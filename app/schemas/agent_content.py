from typing import List

from pydantic import AnyUrl, BaseModel, ConfigDict, Field


class Source(BaseModel):
    title: str = Field(..., min_length=2, json_schema_extra={"strip_whitespace": True})
    url: AnyUrl

    model_config = ConfigDict(extra="ignore")


class ContentOutput(BaseModel):
    answer: str = Field(..., min_length=10, json_schema_extra={"strip_whitespace": True})
    # Görev required: at least 2 reliable sources
    sources: List[Source] = Field(..., min_length=2)

    model_config = ConfigDict(extra="ignore")
