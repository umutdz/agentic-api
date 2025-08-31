import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple

from app.core.error_codes import ErrorCode
from app.core.exceptions import ExceptionBase, QueueUnavailable
from app.repositories.mongodb.jobs import JobsRepository
from app.repositories.mongodb.log_events import LogEventsRepository
from app.schemas.api import ExecuteRequest, JobAccepted
from app.schemas.api import JobStatus as JobStatusDTO
from app.schemas.auth import ActorSchema
from app.schemas.jobs import JobDoc, JobError, JobStatusEnum
from app.schemas.logs import LogEvent, LogType
from app.services.queue import Producer


class JobsOrchestrator:
    """App-level orchestrator for creating/enqueuing jobs and reading status."""

    def __init__(
        self,
        jobs_repo: Optional[JobsRepository] = None,
        logs_repo: Optional[LogEventsRepository] = None,
        producer: Optional[Producer] = None,
    ) -> None:
        """
        Initialize the JobsOrchestrator with optional repositories and producer to make it easier to test.
        If not provided, default repositories and producer will be used.
        """
        self._jobs_repo = jobs_repo or JobsRepository()
        self._logs_repo = logs_repo or LogEventsRepository()
        self._producer = producer or Producer()

    @staticmethod
    def _task_hash(task: str) -> str:
        normalized = " ".join(task.lower().split())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    @staticmethod
    def _new_request_id() -> str:
        return f"req_{uuid.uuid4().hex}"

    @staticmethod
    def _new_job_id() -> str:
        return f"j_{uuid.uuid4().hex}"

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    async def create_and_enqueue(
        self,
        payload: ExecuteRequest,
        actor: ActorSchema,
        http_request_id: Optional[str],
        idempotency_key: Optional[str],
    ) -> Tuple[JobAccepted, str]:
        """
        Job queued, first log pushed, enqueued.
        Returns: (JobAccepted DTO, location_path)
        """
        t_hash = self._task_hash(payload.task)

        # Idempotency
        if idempotency_key:
            existing = await self._jobs_repo.get_by_idempotency(idempotency_key, t_hash)
            if existing:
                accepted = JobAccepted(job_id=existing.job_id, status="queued", request_id=existing.request_id)
                return accepted, f"/api/v1/jobs/{existing.job_id}"

        # New job
        job_id = self._new_job_id()
        request_id = http_request_id or self._new_request_id()

        now = self._now()
        job_doc = JobDoc(
            job_id=job_id,
            request_id=request_id,
            owner_user_id=str(actor.user_id),
            task=payload.task,
            task_hash=t_hash,
            idempotency_key=idempotency_key,
            status=JobStatusEnum.queued,
            progress=0.0,
            webhook_url=str(payload.webhook_url) if payload.webhook_url else None,
            created_at=now,
            updated_at=now,
        )
        await self._jobs_repo.create_job(job_doc)

        # First event
        await self._logs_repo.push(
            LogEvent(
                job_id=job_id,
                request_id=request_id,
                type=LogType.request_received,
                payload={"mode": payload.mode, "owner_user_id": str(actor.user_id)},
            )
        )

        try:
            self._producer.enqueue_execute(job_id=job_id, request_id=request_id, owner_user_id=str(actor.user_id))
        except Exception as e:
            # 1) log_events (best-effort)
            await self._logs_repo.push(
                LogEvent(
                    job_id=job_id,
                    request_id=request_id,
                    type=LogType.error,
                    payload={"stage": "enqueue", "message": "failed to publish to queue", "exc": str(e)},
                )
            )
            # 2) job -> failed (retryable true; you can implement retry mechanism)
            await self._jobs_repo.fail(
                job_id,
                JobError(
                    code="queue_unavailable",
                    message="Queue publish failed",
                    retryable=True,
                    detail={"exc": str(e)},
                ),
            )
            # 3) raise QueueUnavailable (503)
            raise QueueUnavailable(ErrorCode.QUEUE_UNAVAILABLE)

        accepted = JobAccepted(job_id=job_id, status="queued", request_id=request_id)
        return accepted, f"/api/v1/jobs/{job_id}"

    async def get_status_owner_guard(self, job_id: str, actor: ActorSchema) -> JobStatusDTO:
        job = await self._jobs_repo.get(job_id)
        if not job:
            raise ExceptionBase(ErrorCode.RECORD_NOT_FOUND)
        if job.owner_user_id and str(job.owner_user_id) != str(actor.user_id):
            raise ExceptionBase(ErrorCode.UNAUTHORIZED_ACCESS)
        return JobStatusDTO(
            job_id=job.job_id,
            status=job.status,
            decided_agent=job.decided_agent,
            result=job.result.model_dump(mode="json") if job.result else None,
            error=job.error.model_dump(mode="json") if job.error else None,
            progress=job.progress,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )
