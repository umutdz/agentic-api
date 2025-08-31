from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CodeOutput(BaseModel):
    language: str = Field(..., min_length=1, json_schema_extra={"strip_whitespace": True})
    code: str
    explanation: Optional[str] = None

    model_config = ConfigDict(extra="ignore")
