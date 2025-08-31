from typing import Optional

from fastapi import APIRouter, Depends, Header, Request, Response, status

from app.api.deps import depends_orchestrator, require_authenticated_user
from app.core.error_codes import ErrorCode
from app.core.exceptions import ExceptionBase, QueueUnavailable
from app.schemas.api import ExecuteRequest, JobAccepted
from app.schemas.api import JobStatus as JobStatusDTO
from app.schemas.auth import ActorSchema
from app.services.jobs_orchestrator import JobsOrchestrator

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/execute", response_model=JobAccepted, status_code=status.HTTP_202_ACCEPTED)
async def execute_job(
    payload: ExecuteRequest,
    response: Response,
    request: Request,
    actor: ActorSchema = Depends(require_authenticated_user),
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key", description="Idempotency key for the job"),
    orchestrator: JobsOrchestrator = Depends(depends_orchestrator),
):
    """
    Create and enqueue a job.
    Returns:
        JobAccepted: The job accepted response.
        str: The location header value.
    """
    http_request_id = getattr(request.state, "request_id", None)
    try:
        accepted, location = await orchestrator.create_and_enqueue(
            payload=payload,
            actor=actor,
            http_request_id=http_request_id,
            idempotency_key=idempotency_key,
        )
    except QueueUnavailable:
        raise ExceptionBase(ErrorCode.SERVICE_UNAVAILABLE)
    response.headers["Location"] = location
    response.headers["Retry-After"] = "2"
    return accepted


@router.get("/jobs/{job_id}", response_model=JobStatusDTO)
async def get_job_status(
    job_id: str,
    actor: ActorSchema = Depends(require_authenticated_user),
    orchestrator: JobsOrchestrator = Depends(depends_orchestrator),
):
    return await orchestrator.get_status_owner_guard(job_id, actor)
