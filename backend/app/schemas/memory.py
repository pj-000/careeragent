from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class MemoryScope(str, Enum):
    PROFILE = "profile"
    PREFERENCE = "preference"
    GOAL = "goal"
    SKILL = "skill"
    EVIDENCE = "evidence"


class MemoryStatus(str, Enum):
    CONFIRMED = "confirmed"
    PENDING_CONFIRMATION = "pending_confirmation"
    REJECTED = "rejected"


class MemoryItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    thread_id: str
    scope: MemoryScope
    fact: str
    source_artifact_id: str | None = None
    source_message_id: str | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    status: MemoryStatus = MemoryStatus.PENDING_CONFIRMATION
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class LongTermMemoryItem(MemoryItem):
    pass


class CompactionSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    thread_id: str
    source_run_id: str
    current_goal: str
    confirmed_facts: list[str] = Field(default_factory=list)
    decisions_made: list[str] = Field(default_factory=list)
    active_artifact_refs: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    dropped_context_summary: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
