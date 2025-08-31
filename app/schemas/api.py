from datetime import datetime
from typing import Any, Dict, Literal, Optional

from pydantic import AnyUrl, BaseModel, ConfigDict, Field

from app.schemas.jobs import AgentName, JobStatusEnum


class ExecuteRequest(BaseModel):
    task: str = Field(..., min_length=3, json_schema_extra={"strip_whitespace": True})
    mode: Literal["async"] = "async"
    webhook_url: Optional[AnyUrl] = None

    model_config = ConfigDict(extra="ignore")


class JobAccepted(BaseModel):
    job_id: str
    status: Literal["queued"]
    request_id: str

    model_config = ConfigDict(extra="ignore")


class ErrorResponse(BaseModel):
    code: str
    message: str

    model_config = ConfigDict(extra="ignore")


class JobStatus(BaseModel):
    job_id: str
    status: JobStatusEnum
    decided_agent: Optional[AgentName] = None
    result: Optional[Dict[str, Any]] = None  # (ContentOutput|CodeOutput) serialized dict
    error: Optional[Dict[str, Any]] = None  # JobError serialized dict
    progress: Optional[float] = Field(None, ge=0.0, le=1.0)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(extra="ignore")
