import asyncio
from typing import List

import httpx
from celery import Task

from app.peer.peer_agent import PeerAgent
from app.peer.registry import AgentRegistry
from app.repositories.mongodb.jobs import JobsRepository
from app.repositories.mongodb.log_events import LogEventsRepository
from app.schemas.jobs import JobError, JobResult, JobStatusEnum
from app.schemas.logs import LogEvent, LogType
from app.workers.celery_config import celery_app

_LOOP = None


def _get_loop():
    global _LOOP
    if _LOOP is None or _LOOP.is_closed():
        _LOOP = asyncio.new_event_loop()
        asyncio.set_event_loop(_LOOP)
    return _LOOP


@celery_app.task(
    bind=True,
    name="run_agent_task",
    autoretry_for=(
        httpx.HTTPError,
        TimeoutError,
    ),
    retry_backoff=True,
    retry_backoff_max=30,
    retry_kwargs={"max_retries": 3},
)
def run_agent_task(self: Task, *, job_id: str, request_id: str) -> None:
    """
    Flow:
      1) queued -> running
      2) Peer decision -> set_decision + log
      3) Agent.run(...) (async) -> JobResult
      4) succeed | fail (+ progress & logs)
    """

    async def _run() -> None:
        jobs = JobsRepository()
        logs = LogEventsRepository()

        # Attempt counter (for retry observation by APM, etc.)
        await jobs.set_attempts_inc(job_id, by=1)

        # 1) queued -> running (atomic)
        transitioned = await jobs.transition(
            job_id,
            to=JobStatusEnum.running,
            expected_from=JobStatusEnum.queued,
        )
        if not transitioned:
            # State race condition (already transitioned)
            await logs.push(
                LogEvent(
                    job_id=job_id,
                    request_id=request_id,
                    type=LogType.error,
                    payload={"stage": "transition", "msg": "state_not_queued_or_already_taken"},
                )
            )
            return

        await logs.push(LogEvent(job_id=job_id, request_id=request_id, type=LogType.agent_started, payload={}))

        # Job document from task text
        job = await jobs.get(job_id)
        if not job:
            await jobs.fail(job_id, JobError(code="job_not_found", message="Job not found", retryable=False))
            await logs.push(
                LogEvent(job_id=job_id, request_id=request_id, type=LogType.error, payload={"stage": "load_job", "err": "job_not_found"})
            )
            return

        task_text: str = job.task

        # progress tasks to collect and flush before loop ends
        pending_progress: List[asyncio.Task] = []

        def progress_cb(value: float) -> None:
            try:
                t1 = asyncio.create_task(jobs.progress(job_id, float(value)))
                t2 = asyncio.create_task(
                    logs.push(LogEvent(job_id=job_id, request_id=request_id, type=LogType.tool_call, payload={"progress": float(value)}))
                )
                pending_progress.extend([t1, t2])
            except Exception:
                # best-effort
                pass

        try:
            # 2) routing
            decision = PeerAgent.decide(task_text)
            await jobs.set_decision(job_id, agent=decision["agent"], reason=decision.get("reason", ""))
            await logs.push(LogEvent(job_id=job_id, request_id=request_id, type=LogType.route_decision, payload=decision))

            # 3) agent run
            agent = AgentRegistry.get(decision["agent"])
            await logs.push(
                LogEvent(job_id=job_id, request_id=request_id, type=LogType.agent_started, payload={"agent": decision["agent"]})
            )

            result_obj = await agent.run(
                task_text,
                job_id=job_id,
                request_id=request_id,
                progress_cb=progress_cb,
            )

            job_result = JobResult(agent=decision["agent"], output=result_obj.model_dump(mode="json"))

            # 4) succeed
            ok = await jobs.succeed(job_id, job_result)
            if ok:
                await logs.push(
                    LogEvent(job_id=job_id, request_id=request_id, type=LogType.agent_finished, payload={"agent": decision["agent"]})
                )
                await jobs.progress(job_id, 1.0)
            else:
                await logs.push(
                    LogEvent(
                        job_id=job_id, request_id=request_id, type=LogType.error, payload={"stage": "succeed", "msg": "state_not_modified"}
                    )
                )

            # pending progress/log tasks flush
            if pending_progress:
                await asyncio.gather(*pending_progress, return_exceptions=True)

        except Exception as e:
            err = JobError(
                code=getattr(e, "code", "agent_run_error"),
                message=str(e),
                retryable=isinstance(e, (httpx.HTTPError, TimeoutError)),
            )
            await jobs.fail(job_id, err)
            await logs.push(
                LogEvent(job_id=job_id, request_id=request_id, type=LogType.error, payload={"stage": "agent_run", "err": str(e)})
            )
            # pending progress/log tasks flush (even on error)
            if pending_progress:
                await asyncio.gather(*pending_progress, return_exceptions=True)
            raise

    loop = _get_loop()
    loop.run_until_complete(_run())
