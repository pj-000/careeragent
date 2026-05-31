from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class MemoryScope(str, Enum):
    PROFILE = "profile"
    PREFERENCE = "preference"
    GOAL = "goal"
    SKILL = "skill"
    EVIDENCE = "evidence"
    HISTORY = "history"
    PREFERENCES = "preferences"


class MemoryStatus(str, Enum):
    CONFIRMED = "confirmed"
    PENDING_CONFIRMATION = "pending_confirmation"
    REJECTED = "rejected"


class MemoryItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    thread_id: str | None = None
    scope: MemoryScope | str
    fact: str
    source_artifact_id: str | None = None
    source_message_id: str | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    status: MemoryStatus = MemoryStatus.CONFIRMED
    created_at: str | None = None
    updated_at: str | None = None


class LongTermMemoryItem(MemoryItem):
    pass


class CompactionSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    thread_id: str
    source_run_id: str | None = None
    current_goal: str | None = None
    confirmed_facts: list[str] = Field(default_factory=list)
    decisions_made: list[str] = Field(default_factory=list)
    active_artifact_refs: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    dropped_context_summary: str | None = None
    created_at: str | None = None
    message_summary: str = ""
    facts: list[str] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)
    pending_items: list[str] = Field(default_factory=list)
    agent_summaries: dict[str, str] = Field(default_factory=dict)
    skill_refs: list[str] = Field(default_factory=list)
    artifact_ids: list[str] = Field(default_factory=list)
