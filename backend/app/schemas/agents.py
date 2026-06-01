from pydantic import BaseModel, Field


JsonSchema = dict[str, object]


class SkillPolicy(BaseModel):
    default_skill_ids: list[str] = Field(default_factory=list)


class HandoffPolicy(BaseModel):
    allowed_targets: list[str] = Field(default_factory=list)


class AgentManifest(BaseModel):
    agent_id: str
    goal: str
    success_criteria: list[str]
    input_schema: JsonSchema
    output_schema: JsonSchema
    allowed_tools: list[str] = Field(default_factory=list)
    skill_policy: SkillPolicy = Field(default_factory=SkillPolicy)
    handoff_policy: HandoffPolicy = Field(default_factory=HandoffPolicy)
    readable_artifact_kinds: list[str] = Field(default_factory=list)
    writable_artifact_kinds: list[str] = Field(default_factory=list)
    readable_memory_scopes: list[str] = Field(default_factory=list)
    writable_memory_scopes: list[str] = Field(default_factory=list)
