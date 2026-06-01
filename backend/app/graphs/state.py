from typing import Any

from pydantic import BaseModel, Field, model_validator


class AgentSnapshot(BaseModel):
    agent_id: str
    summary: str
    private_context: dict[str, Any] = Field(default_factory=dict)
    last_artifact_ids: list[str] = Field(default_factory=list)
    used_skill_refs: list[str] = Field(default_factory=list)


class CareerAgentState(BaseModel):
    thread_id: str
    user_message: str
    active_agent: str = "supervisor"
    messages: list[dict[str, str]] = Field(default_factory=list)
    loaded_skill_refs: list[str] = Field(default_factory=list)
    loaded_skill_runtime_refs: list[dict[str, Any]] = Field(default_factory=list)
    related_long_term_memory_refs: list[str] = Field(default_factory=list)
    artifact_ids: list[str] = Field(default_factory=list)
    agent_snapshots: dict[str, AgentSnapshot] = Field(default_factory=dict)
    pending_question: str | None = None
    compaction_snapshot_id: str | None = None
    next_agent: str | None = None
    supervisor_decision: dict[str, Any] | None = None
    last_business_agent: str | None = None
    current_runtime_node: str | None = None
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def append_initial_user_message(self) -> "CareerAgentState":
        if not self.messages:
            self.messages.append({"role": "user", "content": self.user_message})
        return self
