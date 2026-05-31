from typing import Literal

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


class SkillRuntimeRef(BaseModel):
    skill_id: str
    version: str
    section_ids: list[str] = Field(default_factory=list)
    detail_level: Literal["summary", "full", "skipped"]
    summary_digest: str = Field(max_length=240)
