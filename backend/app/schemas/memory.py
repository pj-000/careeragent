from pydantic import BaseModel, ConfigDict, Field


class LongTermMemoryItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    scope: str
    fact: str
    source_artifact_id: str | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class CompactionSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    thread_id: str
    message_summary: str
    facts: list[str] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)
    pending_items: list[str] = Field(default_factory=list)
    agent_summaries: dict[str, str] = Field(default_factory=dict)
    skill_refs: list[str] = Field(default_factory=list)
    artifact_ids: list[str] = Field(default_factory=list)
