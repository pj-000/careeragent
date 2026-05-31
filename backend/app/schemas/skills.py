from pydantic import BaseModel, Field


class SkillDocument(BaseModel):
    id: str
    version: int
    agent_scope: str
    tags: list[str] = Field(default_factory=list)
    summary: str
    token_budget: int
    body: str


class LoadedSkill(BaseModel):
    ref: str
    summary: str
    content: str
