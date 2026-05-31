from typing import Any, Literal

from pydantic import BaseModel, Field


ThinkingMode = Literal["off", "auto", "on"]
ReasoningEffort = Literal["low", "medium", "high", "max"]


class ModelRequest(BaseModel):
    messages: list[dict[str, Any]]
    response_schema: dict[str, Any] | None = None
    thinking_mode: ThinkingMode = "auto"
    reasoning_effort: ReasoningEffort = "medium"
    tool_policy: dict[str, Any] | None = None
    response_format: dict[str, Any] | None = None
    provider_options: dict[str, Any] = Field(default_factory=dict)


class ModelResponse(BaseModel):
    content: Any
    reasoning_content: str | None = None
    usage: dict[str, Any] = Field(default_factory=dict)
    raw: dict[str, Any] = Field(default_factory=dict)
    model: str
    finish_reason: str
