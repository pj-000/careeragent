from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ArtifactKind(str, Enum):
    PROFILE = "profile"
    JOB_ANALYSIS = "job_analysis"
    MATCH = "match"
    PLAN = "plan"
    TRAINING_RESULT = "training_result"
    INTERVIEW_SUMMARY = "interview_summary"
    REPORT = "report"
    COMPACTION_SNAPSHOT = "compaction_snapshot"


class Artifact(BaseModel):
    id: str
    kind: ArtifactKind
    source_thread_id: str
    source_agent: str
    payload: dict[str, Any] = Field(default_factory=dict)
    parent_artifact_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
