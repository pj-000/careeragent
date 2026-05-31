from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentRun(BaseModel):
    id: str
    thread_id: str
    active_agent: str = "supervisor"
    status: RunStatus = RunStatus.PENDING
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    artifact_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AgentTraceItem(BaseModel):
    agent_id: str
    summary: str
    artifact_ids: list[str] = Field(default_factory=list)
    used_skill_refs: list[str] = Field(default_factory=list)


class RunResponse(BaseModel):
    run_id: str
    thread_id: str
    active_agent: str
    agent_trace_summary: list[AgentTraceItem] = Field(default_factory=list)
    used_skill_refs: list[str] = Field(default_factory=list)
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
