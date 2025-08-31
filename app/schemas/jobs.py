from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Literal, Optional

from pydantic import AnyUrl, BaseModel, ConfigDict, Field

AgentName = Literal["content", "code"]


class JobStatusEnum(str, Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    canceled = "canceled"


class JobError(BaseModel):
    code: str = Field(..., min_length=2, json_schema_extra={"strip_whitespace": True})
    message: str = Field(..., min_length=2, json_schema_extra={"strip_whitespace": True})
    retryable: bool = False
    detail: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(extra="ignore")


class JobResult(BaseModel):
    agent: AgentName
    # Note: output's a dict; upper layer can validate with ContentOutput/CodeOutput.
    output: Dict[str, Any]

    model_config = ConfigDict(extra="ignore")


class JobDoc(BaseModel):
    # Mongo _id <-> job_id mapping is done in repository layer.
    job_id: str
    request_id: str
    owner_user_id: Optional[str] = None

    task: str = Field(..., min_length=3, json_schema_extra={"strip_whitespace": True})
    task_hash: str
    idempotency_key: Optional[str] = None

    status: JobStatusEnum = JobStatusEnum.queued
    decided_agent: Optional[AgentName] = None
    reason: Optional[str] = None

    result: Optional[JobResult] = None
    error: Optional[JobError] = None

    progress: Optional[float] = Field(None, ge=0.0, le=1.0)
    attempts: int = 0
    metrics: Optional[Dict[str, Any]] = None

    webhook_url: Optional[AnyUrl] = None
    celery_task_id: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=datetime.now(timezone.utc))

    model_config = ConfigDict(extra="ignore")
