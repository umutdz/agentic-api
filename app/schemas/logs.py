from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class LogType(str, Enum):
    request_received = "request_received"
    route_decision = "route_decision"
    agent_started = "agent_started"
    tool_call = "tool_call"
    agent_finished = "agent_finished"
    error = "error"


class LogEvent(BaseModel):
    # Mongo _id <-> event_id mapping is done in the repository layer.
    event_id: Optional[str] = None
    job_id: str
    request_id: str
    type: LogType
    payload: Dict[str, Any] = Field(default_factory=dict)
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(extra="ignore")
