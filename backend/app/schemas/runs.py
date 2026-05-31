from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.memory import MemoryItem
from app.schemas.skills import SkillRuntimeRef


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    NEEDS_INPUT = "needs_input"
    BLOCKED_BY_PREREQUISITE = "blocked_by_prerequisite"
    PROVIDER_ERROR = "provider_error"
    PERMISSION_DENIED = "permission_denied"
    FAILED = "failed"


class SupervisorIntent(str, Enum):
    BUILD_PROFILE = "build_profile"
    ANALYZE_JOB = "analyze_job"
    MATCH = "match"
    PLAN = "plan"
    CREATE_TRAINING = "create_training"
    SUBMIT_TRAINING = "submit_training"
    START_INTERVIEW = "start_interview"
    ANSWER_INTERVIEW = "answer_interview"
    EXPORT_REPORT = "export_report"
    CLARIFY = "clarify"


class ConversationRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ArtifactChainItem(BaseModel):
    id: str
    kind: str
    source_thread_id: str
    source_agent: str
    parent_artifact_ids: list[str] = Field(default_factory=list)
    updated_at: str | None = None


class ActiveArtifactFacts(BaseModel):
    has_profile: bool = False
    has_job_analysis: bool = False
    has_match: bool = False
    has_plan: bool = False
    has_training_result: bool = False
    training_submitted: bool = False
    training_scored: bool = False
    has_interview_summary: bool = False
    interview_turn_count: int = 0
    interview_completed: bool = False


class WorkspaceContext(BaseModel):
    thread_id: str
    updated_by_run_id: str
    active_goal: str = "职业发展规划"
    active_profile_id: str | None = None
    active_job_analysis_id: str | None = None
    active_match_id: str | None = None
    active_plan_id: str | None = None
    active_training_result_id: str | None = None
    active_interview_summary_id: str | None = None
    active_report_id: str | None = None
    active_compaction_snapshot_id: str | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConversationMessage(BaseModel):
    id: str
    thread_id: str
    role: ConversationRole
    content: str
    run_id: str | None = None
    artifact_refs: list[str] = Field(default_factory=list)
    last_business_agent: str | None = None
    current_runtime_node: str | None = None
    warnings: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SupervisorDecision(BaseModel):
    intent: SupervisorIntent
    target_agent: str | None = None
    required_input_artifact_kinds: list[str] = Field(default_factory=list)
    required_capabilities: list[str] = Field(default_factory=list)
    expected_output_artifact_kinds: list[str] = Field(default_factory=list)
    missing_prerequisites: list[str] = Field(default_factory=list)
    missing_capabilities: list[str] = Field(default_factory=list)
    user_facing_reason: str | None = None
    next_actions: list[str] = Field(default_factory=list)


class WorkspaceDelta(BaseModel):
    created_artifacts: list[ArtifactChainItem] = Field(default_factory=list)
    updated_context: WorkspaceContext


class WorkspaceResponse(BaseModel):
    thread_id: str
    active_context: WorkspaceContext
    workspace_artifacts: dict[str, dict[str, Any]] = Field(default_factory=dict)
    artifact_chain: list[ArtifactChainItem] = Field(default_factory=list)
    active_artifact_facts: ActiveArtifactFacts | None = None


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
    run_status: RunStatus = RunStatus.COMPLETED
    last_business_agent: str | None = None
    current_runtime_node: str | None = None
    assistant_message: ConversationMessage | None = None
    supervisor_decision: SupervisorDecision | None = None
    workspace_delta: WorkspaceDelta | None = None
    artifact_chain: list[ArtifactChainItem] = Field(default_factory=list)
    used_skill_runtime_refs: list[SkillRuntimeRef] = Field(default_factory=list)
    compaction_snapshot: dict[str, Any] | None = None
    memory_updates: list[MemoryItem] = Field(default_factory=list)
    blocking_reason: str | None = None
    missing_artifacts: list[str] = Field(default_factory=list)
    missing_capabilities: list[str] = Field(default_factory=list)
    retryable: bool = False
    agent_trace_summary: list[AgentTraceItem] = Field(default_factory=list)
    used_skill_refs: list[str] = Field(default_factory=list)
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
