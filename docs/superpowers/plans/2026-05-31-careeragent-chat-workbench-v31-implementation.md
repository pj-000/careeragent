# CareerAgent Chat Workbench v3.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the v3.1 Chat Workbench contract and UI shell so CareerAgent can be driven by free-form chat while preserving an active artifact chain, durable messages, runtime status, strict agent boundaries, memory, compaction, and demo-mode observability.

**Architecture:** Keep `POST /api/runs` as the single LangGraph runtime entry. Add JSON-backed thread repositories for conversation messages, active workspace context, and memory items; enrich run responses with supervisor decisions, run status, active artifact chain, and assistant messages; then replace the fixed demo-loop page with a desktop-first chat workbench shell that reads those contracts. Existing v2.1 graph, artifact repository, producer checks, and thread isolation remain in place.

**Tech Stack:** FastAPI, Pydantic v2, LangGraph `StateGraph`, local JSON repositories, pytest, Vue 3, Vite, TypeScript, Pinia, Element Plus, lucide/Element icons, Browser smoke verification.

---

## File Structure

Create or modify these files only for v3.1:

- `backend/app/schemas/runs.py`: extend run response models, `RunStatus`, `SupervisorDecision`, `ConversationMessage`, `WorkspaceContext`, `WorkspaceDelta`, `WorkspaceResponse`.
- `backend/app/schemas/memory.py`: evolve `MemoryItem`, `CompactionSnapshot`, and add status/scope enums compatible with v3.1.
- `backend/app/schemas/skills.py`: add bounded `SkillRuntimeRef`.
- `backend/app/repositories/interfaces.py`: add typed repository method contracts for messages, workspace context, and memory.
- `backend/app/repositories/json_thread_repository.py`: JSON implementations for `JsonConversationRepository`, `JsonWorkspaceContextRepository`, and `JsonMemoryRepository`.
- `backend/app/services/workspace.py`: active artifact chain resolution, context updates, workspace response assembly.
- `backend/app/services/run_orchestrator.py`: durable user/assistant messages, graph invocation, run status, workspace delta, and response shaping.
- `backend/app/agents/supervisor.py`: produce `SupervisorDecision` and store it in graph state metadata.
- `backend/app/graphs/state.py`: store `supervisor_decision`, `last_business_agent`, `current_runtime_node`, and bounded skill refs.
- `backend/app/graphs/workflow.py`: accept run metadata, preserve checkpointer/thread behavior, and expose enriched state to orchestrator.
- `backend/app/memory/compaction.py`: emit v3.1 compaction snapshot schema and continue excluding hidden reasoning.
- `backend/app/memory/manager.py`: emit memory candidates with v3.1 scopes/status.
- `backend/app/skills/loader.py`: use intent and budget to return `SkillRuntimeRef` plus loaded content for the current run.
- `backend/app/artifacts/markdown.py`: support report building from an explicit active artifact chain.
- `backend/app/api/runs.py`: delegate to `RunOrchestrator`.
- `backend/app/api/threads.py`: expose workspace, messages, artifacts, and memory confirmation endpoints.
- `backend/app/api/reports.py`: export Markdown from the active chain.
- `backend/app/main.py`: include the new threads router.
- `backend/tests/test_chat_workbench_contracts.py`: schema and contract tests.
- `backend/tests/test_thread_repositories.py`: JSON message/workspace/memory repository tests.
- `backend/tests/test_api_e2e.py`: v3.1 API and active-chain E2E tests.
- `backend/tests/test_memory_compaction.py`: v3.1 compaction and hidden reasoning tests.
- `backend/tests/test_skill_loader.py`: intent/budget skill runtime ref tests.
- `frontend/src/api/client.ts`: v3.1 response/request TypeScript types and new API calls.
- `frontend/src/stores/workbench.ts`: Pinia store for thread, messages, workspace, runtime mode, and report export.
- `frontend/src/views/ChatWorkbenchView.vue`: desktop-first chat workbench page.
- `frontend/src/components/ConversationPanel.vue`: durable chat input/history and quick prompt chips.
- `frontend/src/components/WorkspaceTabs.vue`: structured artifact workspace tabs.
- `frontend/src/components/RuntimeDrawer.vue`: student-mode/demo-mode runtime observability.
- `frontend/src/App.vue`: render `ChatWorkbenchView`.
- `docs/demo-script.md`: add the v3.1 chat workbench demo path.

Do not stage or modify the unrelated untracked `/Users/sss/careeragent/agent申报书date20260511.docx`.

---

## Task 1: Backend v3.1 Schema Contracts

**Files:**
- Modify: `backend/app/schemas/runs.py`
- Modify: `backend/app/schemas/memory.py`
- Modify: `backend/app/schemas/skills.py`
- Create: `backend/tests/test_chat_workbench_contracts.py`

- [ ] **Step 1: Write failing schema contract tests**

Create `backend/tests/test_chat_workbench_contracts.py`:

```python
from app.schemas.memory import CompactionSnapshot, MemoryItem, MemoryScope, MemoryStatus
from app.schemas.runs import (
    ActiveArtifactFacts,
    ArtifactChainItem,
    ConversationMessage,
    ConversationRole,
    RunResponse,
    RunStatus,
    SupervisorDecision,
    SupervisorIntent,
    WorkspaceContext,
    WorkspaceDelta,
    WorkspaceResponse,
)
from app.schemas.skills import SkillRuntimeRef


def test_run_response_exposes_v31_chat_workbench_contract() -> None:
    context = WorkspaceContext(
        thread_id="thread-1",
        active_goal="转向 Agent 开发工程师",
        active_profile_id="profile-1",
        active_job_analysis_id="job-1",
        active_match_id="match-1",
        updated_by_run_id="run-1",
    )
    assistant_message = ConversationMessage(
        id="msg-assistant-1",
        thread_id="thread-1",
        role=ConversationRole.ASSISTANT,
        content="我已完成匹配诊断。",
        run_id="run-1",
        artifact_refs=["match-1"],
        last_business_agent="match",
        current_runtime_node="memory_manager",
    )
    response = RunResponse(
        run_id="run-1",
        thread_id="thread-1",
        run_status=RunStatus.COMPLETED,
        active_agent="memory_manager",
        last_business_agent="match",
        current_runtime_node="memory_manager",
        assistant_message=assistant_message,
        supervisor_decision=SupervisorDecision(
            intent=SupervisorIntent.MATCH,
            target_agent="match",
            required_input_artifact_kinds=["profile", "job_analysis"],
            required_capabilities=[],
            expected_output_artifact_kinds=["match"],
            missing_prerequisites=[],
            missing_capabilities=[],
            user_facing_reason="需要根据画像和岗位做匹配。",
            next_actions=["查看能力差距", "生成三个月计划"],
        ),
        workspace_delta=WorkspaceDelta(
            created_artifacts=[
                ArtifactChainItem(
                    id="match-1",
                    kind="match",
                    source_thread_id="thread-1",
                    source_agent="match",
                    parent_artifact_ids=["profile-1", "job-1"],
                )
            ],
            updated_context=context,
        ),
        artifact_chain=[
            ArtifactChainItem(id="profile-1", kind="profile", source_thread_id="thread-1", source_agent="profile"),
            ArtifactChainItem(id="job-1", kind="job_analysis", source_thread_id="thread-1", source_agent="job"),
            ArtifactChainItem(id="match-1", kind="match", source_thread_id="thread-1", source_agent="match"),
        ],
        used_skill_runtime_refs=[
            SkillRuntimeRef(
                skill_id="match/gap_diagnosis",
                version="1",
                section_ids=["rubric", "gaps"],
                detail_level="summary",
                summary_digest="识别岗位要求和学生画像之间的关键差距。",
            )
        ],
        memory_updates=[],
    )

    payload = response.model_dump(mode="json")
    assert payload["run_status"] == "completed"
    assert payload["last_business_agent"] == "match"
    assert payload["current_runtime_node"] == "memory_manager"
    assert payload["assistant_message"]["artifact_refs"] == ["match-1"]
    assert payload["workspace_delta"]["updated_context"]["active_match_id"] == "match-1"


def test_workspace_response_uses_active_context_not_latest_kind() -> None:
    response = WorkspaceResponse(
        thread_id="thread-1",
        active_context=WorkspaceContext(
            thread_id="thread-1",
            active_goal="第一条 Agent 岗位链路",
            active_job_analysis_id="job-first",
            active_match_id="match-first",
            updated_by_run_id="run-first",
        ),
        workspace_artifacts={
            "job_analysis": {"id": "job-first", "kind": "job_analysis"},
            "match": {"id": "match-first", "kind": "match"},
        },
        artifact_chain=[
            ArtifactChainItem(
                id="job-first",
                kind="job_analysis",
                source_thread_id="thread-1",
                source_agent="job",
            ),
            ArtifactChainItem(
                id="match-first",
                kind="match",
                source_thread_id="thread-1",
                source_agent="match",
            ),
        ],
    )

    assert response.workspace_artifacts["match"]["id"] == "match-first"
    assert [item.id for item in response.artifact_chain] == ["job-first", "match-first"]


def test_active_artifact_facts_distinguish_artifact_presence_from_completion() -> None:
    facts = ActiveArtifactFacts(
        has_profile=True,
        has_job_analysis=True,
        has_match=True,
        has_plan=True,
        has_training_result=True,
        training_submitted=False,
        training_scored=False,
        has_interview_summary=True,
        interview_turn_count=2,
        interview_completed=False,
    )

    assert facts.has_training_result is True
    assert facts.training_scored is False
    assert facts.has_interview_summary is True
    assert facts.interview_completed is False


def test_memory_compaction_and_skill_runtime_refs_are_bounded_public_contracts() -> None:
    memory = MemoryItem(
        id="memory-1",
        thread_id="thread-1",
        scope=MemoryScope.GOAL,
        fact="目标是转向 Agent 开发工程师",
        confidence=0.91,
        status=MemoryStatus.PENDING_CONFIRMATION,
    )
    snapshot = CompactionSnapshot(
        id="compact-1",
        thread_id="thread-1",
        source_run_id="run-1",
        current_goal="转向 Agent 开发工程师",
        confirmed_facts=["会 Python 和 FastAPI"],
        decisions_made=["先补 LangGraph 项目证据"],
        active_artifact_refs=["profile-1", "match-1"],
        next_actions=["生成三个月计划"],
        dropped_context_summary="省略已完成的画像追问。",
    )
    skill_ref = SkillRuntimeRef(
        skill_id="match/gap_diagnosis",
        version="1",
        section_ids=["inputs", "rubric"],
        detail_level="summary",
        summary_digest="识别岗位要求和学生画像之间的关键差距。",
    )

    assert memory.status == MemoryStatus.PENDING_CONFIRMATION
    assert "hidden_reasoning" not in str(snapshot.model_dump())
    assert len(skill_ref.summary_digest) <= 240
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd backend && .venv/bin/python -m pytest -q tests/test_chat_workbench_contracts.py
```

Expected: FAIL with import errors for `ActiveArtifactFacts`, `ArtifactChainItem`, `ConversationMessage`, `WorkspaceContext`, `MemoryItem`, or `SkillRuntimeRef`.

- [ ] **Step 3: Implement schemas in `backend/app/schemas/runs.py`**

Replace and extend the file with:

```python
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.memory import MemoryItem, MemoryScope, MemoryStatus
from app.schemas.skills import SkillRuntimeRef


class RunStatus(str, Enum):
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
    active_goal: str = "职业发展规划"
    active_profile_id: str | None = None
    active_job_analysis_id: str | None = None
    active_match_id: str | None = None
    active_plan_id: str | None = None
    active_training_result_id: str | None = None
    active_interview_summary_id: str | None = None
    active_report_id: str | None = None
    active_compaction_snapshot_id: str | None = None
    updated_by_run_id: str
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConversationMessage(BaseModel):
    id: str
    thread_id: str
    role: ConversationRole
    content: str
    run_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    artifact_refs: list[str] = Field(default_factory=list)
    last_business_agent: str | None = None
    current_runtime_node: str | None = None
    warnings: list[str] = Field(default_factory=list)


class SupervisorDecision(BaseModel):
    intent: SupervisorIntent
    target_agent: str
    required_input_artifact_kinds: list[str] = Field(default_factory=list)
    required_capabilities: list[str] = Field(default_factory=list)
    expected_output_artifact_kinds: list[str] = Field(default_factory=list)
    missing_prerequisites: list[str] = Field(default_factory=list)
    missing_capabilities: list[str] = Field(default_factory=list)
    user_facing_reason: str
    next_actions: list[str] = Field(default_factory=list)


class WorkspaceDelta(BaseModel):
    created_artifacts: list[ArtifactChainItem] = Field(default_factory=list)
    updated_context: WorkspaceContext


class WorkspaceResponse(BaseModel):
    thread_id: str
    active_context: WorkspaceContext
    workspace_artifacts: dict[str, dict[str, Any]] = Field(default_factory=dict)
    artifact_chain: list[ArtifactChainItem] = Field(default_factory=list)


class AgentRun(BaseModel):
    id: str
    thread_id: str
    active_agent: str = "supervisor"
    status: RunStatus = RunStatus.COMPLETED
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
    run_status: RunStatus = RunStatus.COMPLETED
    active_agent: str
    last_business_agent: str | None = None
    current_runtime_node: str | None = None
    assistant_message: ConversationMessage | None = None
    supervisor_decision: SupervisorDecision | None = None
    agent_trace_summary: list[AgentTraceItem] = Field(default_factory=list)
    used_skill_refs: list[str] = Field(default_factory=list)
    used_skill_runtime_refs: list[SkillRuntimeRef] = Field(default_factory=list)
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    artifact_chain: list[ArtifactChainItem] = Field(default_factory=list)
    workspace_delta: WorkspaceDelta | None = None
    compaction_snapshot: dict[str, Any] | None = None
    memory_updates: list[MemoryItem] = Field(default_factory=list)
    blocking_reason: str | None = None
    missing_artifacts: list[str] = Field(default_factory=list)
    retryable: bool = False
    next_actions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
```

- [ ] **Step 4: Implement memory and skill schemas**

In `backend/app/schemas/memory.py`, evolve to:

```python
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
```

In `backend/app/schemas/skills.py`, add:

```python
from typing import Literal


class SkillRuntimeRef(BaseModel):
    skill_id: str
    version: str
    section_ids: list[str] = Field(default_factory=list)
    detail_level: Literal["summary", "full", "skipped"]
    summary_digest: str = Field(max_length=240)
```

- [ ] **Step 5: Run schema tests**

Run:

```bash
cd backend && .venv/bin/python -m pytest -q tests/test_chat_workbench_contracts.py
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/schemas/runs.py backend/app/schemas/memory.py backend/app/schemas/skills.py backend/tests/test_chat_workbench_contracts.py
git commit -m "Add chat workbench API schemas"
```

---

## Task 2: JSON Thread Repositories

**Files:**
- Modify: `backend/app/repositories/interfaces.py`
- Create: `backend/app/repositories/json_thread_repository.py`
- Create: `backend/tests/test_thread_repositories.py`

- [ ] **Step 1: Write failing repository tests**

Create `backend/tests/test_thread_repositories.py`:

```python
from app.repositories.json_thread_repository import (
    JsonConversationRepository,
    JsonMemoryRepository,
    JsonWorkspaceContextRepository,
)
from app.schemas.memory import MemoryItem, MemoryScope, MemoryStatus
from app.schemas.runs import ConversationMessage, ConversationRole, WorkspaceContext


def test_conversation_repository_persists_messages_by_thread(tmp_path):
    repo = JsonConversationRepository(tmp_path)
    user_message = ConversationMessage(
        id="msg-user-1",
        thread_id="thread-a",
        role=ConversationRole.USER,
        content="我想转 Agent 开发",
        run_id="run-1",
    )
    assistant_message = ConversationMessage(
        id="msg-assistant-1",
        thread_id="thread-a",
        role=ConversationRole.ASSISTANT,
        content="我会先建立画像。",
        run_id="run-1",
        artifact_refs=["profile-1"],
    )
    other_thread = ConversationMessage(
        id="msg-other-1",
        thread_id="thread-b",
        role=ConversationRole.USER,
        content="另一个线程",
    )

    repo.save(user_message)
    repo.save(assistant_message)
    repo.save(other_thread)

    restored = repo.list_by_thread("thread-a")
    assert [message.id for message in restored] == ["msg-user-1", "msg-assistant-1"]
    assert restored[1].artifact_refs == ["profile-1"]


def test_workspace_context_repository_keeps_active_chain_by_thread(tmp_path):
    repo = JsonWorkspaceContextRepository(tmp_path)
    first = WorkspaceContext(
        thread_id="thread-a",
        active_goal="Agent 开发",
        active_job_analysis_id="job-first",
        active_match_id="match-first",
        updated_by_run_id="run-1",
    )
    second = WorkspaceContext(
        thread_id="thread-b",
        active_goal="产品经理",
        active_job_analysis_id="job-second",
        updated_by_run_id="run-2",
    )

    repo.save(first)
    repo.save(second)

    assert repo.get("thread-a").active_match_id == "match-first"
    assert repo.get("thread-b").active_job_analysis_id == "job-second"


def test_memory_repository_filters_and_updates_status(tmp_path):
    repo = JsonMemoryRepository(tmp_path)
    item = MemoryItem(
        id="memory-1",
        thread_id="thread-a",
        scope=MemoryScope.GOAL,
        fact="目标是 Agent 开发岗位",
        confidence=0.8,
        status=MemoryStatus.PENDING_CONFIRMATION,
    )
    repo.save(item)

    assert repo.list_by_thread("thread-a")[0].status == MemoryStatus.PENDING_CONFIRMATION
    assert repo.list_by_scope("thread-a", MemoryScope.GOAL)[0].fact == "目标是 Agent 开发岗位"
    repo.set_status("thread-a", "memory-1", MemoryStatus.CONFIRMED)
    assert repo.get("thread-a", "memory-1").status == MemoryStatus.CONFIRMED
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd backend && .venv/bin/python -m pytest -q tests/test_thread_repositories.py
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.repositories.json_thread_repository'`.

- [ ] **Step 3: Add repository interfaces**

Append these ABCs to `backend/app/repositories/interfaces.py`:

```python
from app.schemas.memory import MemoryItem, MemoryScope, MemoryStatus
from app.schemas.runs import ConversationMessage, WorkspaceContext


class ConversationRepository(ABC):
    @abstractmethod
    def save(self, message: ConversationMessage) -> ConversationMessage:
        raise NotImplementedError

    @abstractmethod
    def list_by_thread(self, thread_id: str) -> list[ConversationMessage]:
        raise NotImplementedError


class WorkspaceContextRepository(ABC):
    @abstractmethod
    def save(self, context: WorkspaceContext) -> WorkspaceContext:
        raise NotImplementedError

    @abstractmethod
    def get(self, thread_id: str) -> WorkspaceContext | None:
        raise NotImplementedError


class MemoryItemRepository(ABC):
    @abstractmethod
    def save(self, item: MemoryItem) -> MemoryItem:
        raise NotImplementedError

    @abstractmethod
    def get(self, thread_id: str, memory_id: str) -> MemoryItem:
        raise NotImplementedError

    @abstractmethod
    def list_by_thread(self, thread_id: str) -> list[MemoryItem]:
        raise NotImplementedError

    @abstractmethod
    def list_by_scope(self, thread_id: str, scope: MemoryScope) -> list[MemoryItem]:
        raise NotImplementedError

    @abstractmethod
    def set_status(self, thread_id: str, memory_id: str, status: MemoryStatus) -> MemoryItem:
        raise NotImplementedError
```

- [ ] **Step 4: Implement JSON repositories**

Create `backend/app/repositories/json_thread_repository.py`:

```python
from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

from app.schemas.memory import MemoryItem, MemoryScope, MemoryStatus
from app.schemas.runs import ConversationMessage, WorkspaceContext


SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,255}$")
ModelT = TypeVar("ModelT", bound=BaseModel)


class JsonConversationRepository:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.message_dir = root / "messages"
        self.message_dir.mkdir(parents=True, exist_ok=True)

    def save(self, message: ConversationMessage) -> ConversationMessage:
        _validate_id(message.id, "message_id")
        path = self.message_dir / f"{message.id}.json"
        _atomic_write(path, message.model_dump(mode="json"))
        return message

    def list_by_thread(self, thread_id: str) -> list[ConversationMessage]:
        messages = _read_models(self.message_dir, ConversationMessage)
        scoped = [message for message in messages if message.thread_id == thread_id]
        return sorted(scoped, key=lambda message: (message.created_at, message.id))


class JsonWorkspaceContextRepository:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.context_dir = root / "workspace-contexts"
        self.context_dir.mkdir(parents=True, exist_ok=True)

    def save(self, context: WorkspaceContext) -> WorkspaceContext:
        path = self.context_dir / f"{_safe_thread_filename(context.thread_id)}.json"
        _atomic_write(path, context.model_dump(mode="json"))
        return context

    def get(self, thread_id: str) -> WorkspaceContext | None:
        path = self.context_dir / f"{_safe_thread_filename(thread_id)}.json"
        if not path.exists():
            return None
        return WorkspaceContext.model_validate(json.loads(path.read_text(encoding="utf-8")))


class JsonMemoryRepository:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.memory_dir = root / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)

    def save(self, item: MemoryItem) -> MemoryItem:
        _validate_id(item.id, "memory_id")
        path = self.memory_dir / f"{item.id}.json"
        _atomic_write(path, item.model_dump(mode="json"))
        return item

    def get(self, thread_id: str, memory_id: str) -> MemoryItem:
        _validate_id(memory_id, "memory_id")
        path = self.memory_dir / f"{memory_id}.json"
        if not path.exists():
            raise KeyError(f"Memory item {memory_id!r} not found")
        item = MemoryItem.model_validate(json.loads(path.read_text(encoding="utf-8")))
        if item.thread_id != thread_id:
            raise KeyError(f"Memory item {memory_id!r} is not in thread {thread_id!r}")
        return item

    def list_by_thread(self, thread_id: str) -> list[MemoryItem]:
        items = _read_models(self.memory_dir, MemoryItem)
        return sorted([item for item in items if item.thread_id == thread_id], key=lambda item: (item.created_at, item.id))

    def list_by_scope(self, thread_id: str, scope: MemoryScope) -> list[MemoryItem]:
        return [item for item in self.list_by_thread(thread_id) if item.scope == scope]

    def set_status(self, thread_id: str, memory_id: str, status: MemoryStatus) -> MemoryItem:
        item = self.get(thread_id, memory_id)
        updated = item.model_copy(update={"status": status, "updated_at": datetime.now(timezone.utc)})
        return self.save(updated)


def _read_models(model_dir: Path, model_type: type[ModelT]) -> list[ModelT]:
    models: list[ModelT] = []
    for path in sorted(model_dir.glob("*.json")):
        models.append(model_type.model_validate(json.loads(path.read_text(encoding="utf-8"))))
    return models


def _safe_thread_filename(thread_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", thread_id).strip("-") or "thread"


def _validate_id(value: str, label: str) -> None:
    if not SAFE_ID.match(value):
        raise ValueError(f"Invalid {label}: {value}")


def _atomic_write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_file = tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        delete=False,
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    tmp_path = Path(tmp_file.name)
    try:
        with tmp_file:
            json.dump(payload, tmp_file, ensure_ascii=False, indent=2)
            tmp_file.flush()
            os.fsync(tmp_file.fileno())
        os.replace(tmp_path, path)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink()
        raise
```

- [ ] **Step 5: Run repository tests**

Run:

```bash
cd backend && .venv/bin/python -m pytest -q tests/test_thread_repositories.py
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/repositories/interfaces.py backend/app/repositories/json_thread_repository.py backend/tests/test_thread_repositories.py
git commit -m "Add JSON thread repositories"
```

---

## Task 3: Supervisor Decision Contract

**Files:**
- Modify: `backend/app/agents/supervisor.py`
- Modify: `backend/app/graphs/state.py`
- Modify: `backend/tests/test_graph_vertical_slice.py`
- Modify: `backend/tests/test_chat_workbench_contracts.py`

- [ ] **Step 1: Write failing tests for supervisor decisions**

Append to `backend/tests/test_chat_workbench_contracts.py`:

```python
from app.agents.supervisor import decide_user_message
from app.schemas.runs import ActiveArtifactFacts, SupervisorIntent


def test_supervisor_decision_maps_training_submission_to_training_agent() -> None:
    decision = decide_user_message(
        "我的训练答案：我会设计 FastAPI + LangGraph demo。",
        available_artifact_kinds={"profile", "job_analysis", "match", "plan", "training_result"},
    )

    assert decision.intent == SupervisorIntent.SUBMIT_TRAINING
    assert decision.target_agent == "training"
    assert decision.required_input_artifact_kinds == ["match", "plan"]
    assert decision.expected_output_artifact_kinds == ["training_result"]
    assert decision.missing_prerequisites == []
    assert "训练" in decision.user_facing_reason


def test_supervisor_decision_reports_missing_prerequisites_for_report() -> None:
    decision = decide_user_message(
        "请导出报告",
        available_artifact_kinds={"profile", "job_analysis", "match", "plan"},
    )

    assert decision.intent == SupervisorIntent.EXPORT_REPORT
    assert decision.target_agent == "report"
    assert decision.missing_prerequisites == ["training_result", "interview_summary"]
    assert decision.missing_capabilities == []
    assert "训练" in decision.next_actions[0]


def test_supervisor_blocks_interview_until_training_is_scored() -> None:
    decision = decide_user_message(
        "开始模拟面试",
        available_artifact_kinds={"profile", "job_analysis", "match", "plan", "training_result"},
        active_facts=ActiveArtifactFacts(
            has_profile=True,
            has_job_analysis=True,
            has_match=True,
            has_plan=True,
            has_training_result=True,
            training_submitted=False,
            training_scored=False,
        ),
    )

    assert decision.intent == SupervisorIntent.START_INTERVIEW
    assert decision.missing_prerequisites == []
    assert decision.required_capabilities == ["training_scored"]
    assert decision.missing_capabilities == ["training_scored"]
    assert "训练答案" in decision.next_actions[0]


def test_supervisor_blocks_report_until_three_interview_turns_are_complete() -> None:
    decision = decide_user_message(
        "请导出报告",
        available_artifact_kinds={
            "profile",
            "job_analysis",
            "match",
            "plan",
            "training_result",
            "interview_summary",
        },
        active_facts=ActiveArtifactFacts(
            has_profile=True,
            has_job_analysis=True,
            has_match=True,
            has_plan=True,
            has_training_result=True,
            training_submitted=True,
            training_scored=True,
            has_interview_summary=True,
            interview_turn_count=2,
            interview_completed=False,
        ),
    )

    assert decision.intent == SupervisorIntent.EXPORT_REPORT
    assert decision.missing_prerequisites == []
    assert decision.required_capabilities == ["training_scored", "interview_completed"]
    assert decision.missing_capabilities == ["interview_completed"]
    assert "三轮模拟面试" in decision.next_actions[0]


def test_supervisor_decision_prefers_profile_for_first_demo_prompt() -> None:
    decision = decide_user_message(
        "我会 Python FastAPI，想匹配 Agent 开发岗位",
        available_artifact_kinds=set(),
    )

    assert decision.intent == SupervisorIntent.BUILD_PROFILE
    assert decision.target_agent == "profile"
    assert decision.missing_prerequisites == []
```

Append to `backend/tests/test_graph_vertical_slice.py`:

```python
def test_graph_state_records_supervisor_decision_and_business_agent(tmp_path: Path) -> None:
    repo = JsonArtifactRepository(tmp_path)
    graph = build_graph(artifact_repo=repo)
    config = {"configurable": {"thread_id": "decision-thread"}}

    state = graph.invoke(
        {
            "thread_id": "decision-thread",
            "user_message": "请做 match 分析",
            "metadata": {"active_artifact_kinds": ["profile", "job_analysis"]},
        },
        config=config,
    )

    decision = state["metadata"]["supervisor_decision"]
    assert decision["intent"] == "match"
    assert decision["target_agent"] == "match"
    assert decision["missing_prerequisites"] == []
    assert state["metadata"]["last_business_agent"] == "match"
    assert state["metadata"]["current_runtime_node"] == "memory_manager"


def test_match_without_prerequisites_is_blocked(tmp_path: Path) -> None:
    repo = JsonArtifactRepository(tmp_path)
    graph = build_graph(artifact_repo=repo)

    state = graph.invoke(
        {"thread_id": "missing-match-thread", "user_message": "请做 match 分析"},
        config={"configurable": {"thread_id": "missing-match-thread"}},
    )

    decision = state["metadata"]["supervisor_decision"]
    assert decision["intent"] == "match"
    assert decision["target_agent"] == "match"
    assert decision["missing_prerequisites"] == ["profile", "job_analysis"]
    assert state["metadata"]["last_business_agent"] is None
    assert repo.list_by_kind("missing-match-thread", "match") == []


def test_missing_prerequisites_do_not_execute_target_agent(tmp_path: Path) -> None:
    repo = JsonArtifactRepository(tmp_path)
    graph = build_graph(artifact_repo=repo)
    state = graph.invoke(
        {"thread_id": "blocked-report-thread", "user_message": "请导出 Markdown 报告"},
        config={"configurable": {"thread_id": "blocked-report-thread"}},
    )
    decision = state["metadata"]["supervisor_decision"]
    assert decision["intent"] == "export_report"
    assert decision["missing_prerequisites"]
    assert state["metadata"]["last_business_agent"] is None
    assert repo.list_by_kind("blocked-report-thread", "report") == []


def test_supervisor_uses_active_chain_kinds_before_thread_history(tmp_path: Path) -> None:
    repo = JsonArtifactRepository(tmp_path)
    repo.save("match", "old-match", {"content": {}}, "active-kind-thread", "match")
    graph = build_graph(artifact_repo=repo)
    state = graph.invoke(
        {
            "thread_id": "active-kind-thread",
            "user_message": "生成三个月路径规划",
            "metadata": {"active_artifact_kinds": ["profile", "job_analysis"]},
        },
        config={"configurable": {"thread_id": "active-kind-thread"}},
    )

    decision = state["metadata"]["supervisor_decision"]
    assert decision["intent"] == "plan"
    assert decision["missing_prerequisites"] == ["match"]
    assert repo.list_by_kind("active-kind-thread", "plan") == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd backend && .venv/bin/python -m pytest -q tests/test_chat_workbench_contracts.py::test_supervisor_decision_maps_training_submission_to_training_agent tests/test_chat_workbench_contracts.py::test_supervisor_decision_reports_missing_prerequisites_for_report tests/test_chat_workbench_contracts.py::test_supervisor_blocks_interview_until_training_is_scored tests/test_chat_workbench_contracts.py::test_supervisor_blocks_report_until_three_interview_turns_are_complete tests/test_chat_workbench_contracts.py::test_supervisor_decision_prefers_profile_for_first_demo_prompt tests/test_graph_vertical_slice.py::test_graph_state_records_supervisor_decision_and_business_agent tests/test_graph_vertical_slice.py::test_match_without_prerequisites_is_blocked tests/test_graph_vertical_slice.py::test_missing_prerequisites_do_not_execute_target_agent tests/test_graph_vertical_slice.py::test_supervisor_uses_active_chain_kinds_before_thread_history
```

Expected: FAIL because `decide_user_message` and graph metadata fields do not exist.

- [ ] **Step 3: Implement `decide_user_message()`**

In `backend/app/agents/supervisor.py`, add:

```python
from app.schemas.runs import ActiveArtifactFacts, SupervisorDecision, SupervisorIntent


REQUIRED_BY_INTENT = {
    SupervisorIntent.BUILD_PROFILE: [],
    SupervisorIntent.ANALYZE_JOB: [],
    SupervisorIntent.MATCH: ["profile", "job_analysis"],
    SupervisorIntent.PLAN: ["profile", "job_analysis", "match"],
    SupervisorIntent.CREATE_TRAINING: ["match", "plan"],
    SupervisorIntent.SUBMIT_TRAINING: ["match", "plan"],
    SupervisorIntent.START_INTERVIEW: ["profile", "job_analysis", "match", "plan", "training_result"],
    SupervisorIntent.ANSWER_INTERVIEW: ["profile", "job_analysis", "match", "plan", "training_result"],
    SupervisorIntent.EXPORT_REPORT: ["profile", "job_analysis", "match", "plan", "training_result", "interview_summary"],
    SupervisorIntent.CLARIFY: [],
}


REQUIRED_CAPABILITIES_BY_INTENT = {
    SupervisorIntent.BUILD_PROFILE: [],
    SupervisorIntent.ANALYZE_JOB: [],
    SupervisorIntent.MATCH: [],
    SupervisorIntent.PLAN: [],
    SupervisorIntent.CREATE_TRAINING: [],
    SupervisorIntent.SUBMIT_TRAINING: [],
    SupervisorIntent.START_INTERVIEW: ["training_scored"],
    SupervisorIntent.ANSWER_INTERVIEW: ["training_scored"],
    SupervisorIntent.EXPORT_REPORT: ["training_scored", "interview_completed"],
    SupervisorIntent.CLARIFY: [],
}


EXPECTED_OUTPUT_BY_INTENT = {
    SupervisorIntent.BUILD_PROFILE: ["profile"],
    SupervisorIntent.ANALYZE_JOB: ["job_analysis"],
    SupervisorIntent.MATCH: ["match"],
    SupervisorIntent.PLAN: ["plan"],
    # MVP v3.1 keeps the v2.1 `training_result` artifact for compatibility.
    # Its payload must distinguish task-only, submitted answer, and scored result
    # fields with `has_submission`, `submission`, and `score`.
    SupervisorIntent.CREATE_TRAINING: ["training_result"],
    SupervisorIntent.SUBMIT_TRAINING: ["training_result"],
    SupervisorIntent.START_INTERVIEW: ["interview_summary"],
    SupervisorIntent.ANSWER_INTERVIEW: ["interview_summary"],
    SupervisorIntent.EXPORT_REPORT: ["report"],
    SupervisorIntent.CLARIFY: [],
}


TARGET_BY_INTENT = {
    SupervisorIntent.BUILD_PROFILE: "profile",
    SupervisorIntent.ANALYZE_JOB: "job",
    SupervisorIntent.MATCH: "match",
    SupervisorIntent.PLAN: "planning",
    SupervisorIntent.CREATE_TRAINING: "training",
    SupervisorIntent.SUBMIT_TRAINING: "training",
    SupervisorIntent.START_INTERVIEW: "interview",
    SupervisorIntent.ANSWER_INTERVIEW: "interview",
    SupervisorIntent.EXPORT_REPORT: "report",
    SupervisorIntent.CLARIFY: "memory_manager",
}


def decide_user_message(
    message: str,
    available_artifact_kinds: set[str],
    active_facts: ActiveArtifactFacts | None = None,
) -> SupervisorDecision:
    intent = _detect_intent(message)
    required = REQUIRED_BY_INTENT[intent]
    missing = [kind for kind in required if kind not in available_artifact_kinds]
    required_capabilities = REQUIRED_CAPABILITIES_BY_INTENT[intent]
    missing_capabilities = [] if missing else _missing_capabilities(required_capabilities, active_facts)
    return SupervisorDecision(
        intent=intent,
        target_agent=TARGET_BY_INTENT[intent],
        required_input_artifact_kinds=required,
        required_capabilities=required_capabilities,
        expected_output_artifact_kinds=EXPECTED_OUTPUT_BY_INTENT[intent],
        missing_prerequisites=missing,
        missing_capabilities=missing_capabilities,
        user_facing_reason=_reason_for_intent(intent, missing, missing_capabilities),
        next_actions=_next_actions_for_decision(intent, missing, missing_capabilities),
    )


def _missing_capabilities(required: list[str], active_facts: ActiveArtifactFacts | None) -> list[str]:
    if not required:
        return []
    facts = active_facts or ActiveArtifactFacts()
    return [capability for capability in required if not bool(getattr(facts, capability))]


def _detect_intent(message: str) -> SupervisorIntent:
    normalized = message.lower()
    if message.startswith("回答") or "回答1" in message or "回答2" in message or "回答3" in message:
        return SupervisorIntent.ANSWER_INTERVIEW
    if "训练答案" in message:
        return SupervisorIntent.SUBMIT_TRAINING
    if "我的简历" in message or "简历" in message or "我会" in message or "我有" in message or "resume" in normalized or "profile" in normalized:
        return SupervisorIntent.BUILD_PROFILE
    if "岗位" in message or "jd" in normalized or "job" in normalized:
        return SupervisorIntent.ANALYZE_JOB
    if "训练" in message or "training task" in normalized:
        return SupervisorIntent.CREATE_TRAINING
    if "报告" in message or "report" in normalized:
        return SupervisorIntent.EXPORT_REPORT
    if "面试" in message or "interview" in normalized:
        return SupervisorIntent.START_INTERVIEW
    if "计划" in message or "路径" in message or "plan" in normalized:
        return SupervisorIntent.PLAN
    if "匹配" in message or "match" in normalized:
        return SupervisorIntent.MATCH
    return SupervisorIntent.MATCH


def _reason_for_intent(
    intent: SupervisorIntent,
    missing: list[str],
    missing_capabilities: list[str],
) -> str:
    if missing:
        return f"当前请求需要先补齐：{', '.join(missing)}。"
    if missing_capabilities:
        labels = {
            "training_scored": "提交训练答案并完成评分",
            "interview_completed": "完成三轮模拟面试",
        }
        readable = [labels.get(capability, capability) for capability in missing_capabilities]
        return f"当前请求需要先完成：{', '.join(readable)}。"
    return {
        SupervisorIntent.BUILD_PROFILE: "需要先建立或更新学生职业画像。",
        SupervisorIntent.ANALYZE_JOB: "需要把目标岗位或 JD 拆成结构化岗位画像。",
        SupervisorIntent.MATCH: "需要基于画像和岗位做匹配诊断。",
        SupervisorIntent.PLAN: "需要把匹配差距转成阶段路径。",
        SupervisorIntent.CREATE_TRAINING: "需要根据差距生成训练任务。",
        SupervisorIntent.SUBMIT_TRAINING: "需要评价学生提交的训练答案。",
        SupervisorIntent.START_INTERVIEW: "需要进入模拟面试流程。",
        SupervisorIntent.ANSWER_INTERVIEW: "需要评价当前面试回答并继续追问。",
        SupervisorIntent.EXPORT_REPORT: "需要汇总完整职业发展报告。",
        SupervisorIntent.CLARIFY: "需要先整理上下文或追问。",
    }[intent]


def _next_actions_for_decision(
    intent: SupervisorIntent,
    missing: list[str],
    missing_capabilities: list[str],
) -> list[str]:
    if missing:
        actions = {
            "profile": "补充简历或画像",
            "job_analysis": "分析目标岗位/JD",
            "match": "先做匹配诊断",
            "plan": "生成三个月计划",
            "training_result": "提交训练答案",
            "interview_summary": "完成三轮模拟面试",
        }
        return [actions[kind] for kind in missing if kind in actions]
    if missing_capabilities:
        actions = {
            "training_scored": "提交训练答案并完成评分",
            "interview_completed": "完成三轮模拟面试",
        }
        return [actions[capability] for capability in missing_capabilities if capability in actions]
    return {
        SupervisorIntent.BUILD_PROFILE: ["继续补充目标岗位"],
        SupervisorIntent.ANALYZE_JOB: ["做匹配诊断"],
        SupervisorIntent.MATCH: ["生成三个月计划"],
        SupervisorIntent.PLAN: ["开始训练任务"],
        SupervisorIntent.CREATE_TRAINING: ["提交训练答案"],
        SupervisorIntent.SUBMIT_TRAINING: ["开始模拟面试"],
        SupervisorIntent.START_INTERVIEW: ["回答面试问题"],
        SupervisorIntent.ANSWER_INTERVIEW: ["继续下一轮面试"],
        SupervisorIntent.EXPORT_REPORT: ["预览 Markdown 报告"],
        SupervisorIntent.CLARIFY: ["继续对话"],
    }[intent]
```

- [ ] **Step 4: Wire decision into `supervisor_node()`**

Modify `supervisor_node()`:

```python
def supervisor_node(state: dict[str, Any], artifact_repo: ArtifactRepository) -> dict[str, Any]:
    career_state = coerce_state(state)
    runtime = make_runtime(career_state, "supervisor", artifact_repo)
    active_kinds = career_state.metadata.get("active_artifact_kinds")
    available_kinds = (
        set(active_kinds)
        if isinstance(active_kinds, list)
        else {artifact["kind"] for artifact in artifact_repo.list_by_thread(career_state.thread_id)}
    )
    active_facts_payload = career_state.metadata.get("active_facts")
    active_facts = (
        ActiveArtifactFacts.model_validate(active_facts_payload)
        if isinstance(active_facts_payload, dict)
        else None
    )
    decision = decide_user_message(career_state.user_message, available_kinds, active_facts)
    target = decision.target_agent
    career_state.loaded_skill_refs = _append_unique(
        career_state.loaded_skill_refs,
        AGENT_MANIFESTS["supervisor"].skill_policy.default_skill_ids,
    )
    career_state.agent_snapshots["supervisor"] = AgentSnapshot(
        agent_id="supervisor",
        summary=f"Routed {decision.intent.value} to {target}.",
        private_context={"route": target},
        last_artifact_ids=[],
        used_skill_refs=list(AGENT_MANIFESTS["supervisor"].skill_policy.default_skill_ids),
    )
    career_state.metadata["supervisor_decision"] = decision.model_dump(mode="json")
    career_state.active_agent = "supervisor"
    if decision.missing_prerequisites or decision.missing_capabilities:
        career_state.pending_question = decision.user_facing_reason
        career_state.metadata["last_business_agent"] = None
        career_state.metadata["current_runtime_node"] = "supervisor"
        career_state.next_agent = runtime.handoff_to("memory_manager")
        return career_state.model_dump()

    career_state.metadata["last_business_agent"] = target if target != "memory_manager" else None
    career_state.next_agent = runtime.handoff_to(target)
    return career_state.model_dump()
```

Modify each business node tail centrally in `run_business_agent()` so `metadata["last_business_agent"]` is set:

```python
state.metadata["last_business_agent"] = agent_id
```

Modify `memory_manager_node()` before return:

```python
career_state.metadata["current_runtime_node"] = "memory_manager"
```

- [ ] **Step 5: Add state fields**

In `backend/app/graphs/state.py`, add typed fields to `CareerAgentState`:

```python
supervisor_decision: dict[str, Any] | None = None
last_business_agent: str | None = None
current_runtime_node: str | None = None
```

Also add them to `GraphState` in `backend/app/graphs/workflow.py`:

```python
supervisor_decision: dict[str, Any] | None
last_business_agent: str | None
current_runtime_node: str | None
```

- [ ] **Step 6: Run supervisor tests**

Run:

```bash
cd backend && .venv/bin/python -m pytest -q tests/test_chat_workbench_contracts.py::test_supervisor_decision_maps_training_submission_to_training_agent tests/test_chat_workbench_contracts.py::test_supervisor_decision_reports_missing_prerequisites_for_report tests/test_chat_workbench_contracts.py::test_supervisor_blocks_interview_until_training_is_scored tests/test_chat_workbench_contracts.py::test_supervisor_blocks_report_until_three_interview_turns_are_complete tests/test_chat_workbench_contracts.py::test_supervisor_decision_prefers_profile_for_first_demo_prompt tests/test_graph_vertical_slice.py::test_graph_state_records_supervisor_decision_and_business_agent tests/test_graph_vertical_slice.py::test_match_without_prerequisites_is_blocked tests/test_graph_vertical_slice.py::test_missing_prerequisites_do_not_execute_target_agent tests/test_graph_vertical_slice.py::test_supervisor_uses_active_chain_kinds_before_thread_history
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/app/agents/supervisor.py backend/app/agents/runtime.py backend/app/agents/memory.py backend/app/graphs/state.py backend/app/graphs/workflow.py backend/tests/test_chat_workbench_contracts.py backend/tests/test_graph_vertical_slice.py
git commit -m "Add supervisor decision contract"
```

---

## Task 4: Active Workspace Context And Artifact Chain Service

**Files:**
- Create: `backend/app/services/workspace.py`
- Modify: `backend/app/artifacts/markdown.py`
- Modify: `backend/tests/test_artifact_reporting.py`
- Create: `backend/tests/test_workspace_service.py`
- Modify: `backend/tests/test_api_e2e.py`

- [ ] **Step 1: Write failing service tests**

Create `backend/tests/test_workspace_service.py`:

```python
from app.repositories.json_repository import JsonArtifactRepository
from app.repositories.json_thread_repository import JsonWorkspaceContextRepository
from app.schemas.runs import WorkspaceContext
from app.services.workspace import (
    artifact_chain_from_context,
    build_active_artifact_facts,
    build_workspace_response,
    update_context_from_artifacts,
)


def test_workspace_context_tracks_active_chain_not_latest_kind(tmp_path):
    artifact_repo = JsonArtifactRepository(tmp_path)
    context_repo = JsonWorkspaceContextRepository(tmp_path)
    artifact_repo.save("job_analysis", "job-first", {"content": {"summary": "Agent 岗位"}}, "thread-a", "job")
    artifact_repo.save("match", "match-first", {"content": {"score": 80}}, "thread-a", "match", ["job-first"])
    artifact_repo.save("job_analysis", "job-second", {"content": {"summary": "产品岗位"}}, "thread-a", "job")
    context_repo.save(
        WorkspaceContext(
            thread_id="thread-a",
            active_goal="Agent 岗位链路",
            active_job_analysis_id="job-first",
            active_match_id="match-first",
            updated_by_run_id="run-first",
        )
    )

    workspace = build_workspace_response("thread-a", artifact_repo, context_repo)

    assert workspace.workspace_artifacts["job_analysis"]["id"] == "job-first"
    assert workspace.workspace_artifacts["match"]["id"] == "match-first"
    assert [item.id for item in workspace.artifact_chain] == ["job-first", "match-first"]


def test_update_context_from_artifacts_only_updates_created_kinds(tmp_path):
    artifact_repo = JsonArtifactRepository(tmp_path)
    context_repo = JsonWorkspaceContextRepository(tmp_path)
    artifact_repo.save("profile", "profile-1", {"content": {}}, "thread-a", "profile")
    artifact_repo.save("job_analysis", "job-1", {"content": {}}, "thread-a", "job")

    context = update_context_from_artifacts(
        thread_id="thread-a",
        run_id="run-1",
        created_artifact_ids=["profile-1", "job-1"],
        active_goal="Agent 开发",
        artifact_repo=artifact_repo,
        context_repo=context_repo,
    )

    assert context.active_profile_id == "profile-1"
    assert context.active_job_analysis_id == "job-1"
    assert context.updated_by_run_id == "run-1"


def test_update_context_preserves_existing_goal_when_active_goal_is_none(tmp_path):
    artifact_repo = JsonArtifactRepository(tmp_path)
    context_repo = JsonWorkspaceContextRepository(tmp_path)
    artifact_repo.save("profile", "profile-1", {"content": {}}, "thread-a", "profile")
    context_repo.save(
        WorkspaceContext(
            thread_id="thread-a",
            active_goal="Agent 开发工程师",
            active_profile_id="profile-1",
            updated_by_run_id="run-profile",
        )
    )
    artifact_repo.save("training_result", "training-1", {"content": {"has_submission": True}}, "thread-a", "training")

    context = update_context_from_artifacts(
        thread_id="thread-a",
        run_id="run-training",
        created_artifact_ids=["training-1"],
        active_goal=None,
        artifact_repo=artifact_repo,
        context_repo=context_repo,
    )

    assert context.active_goal == "Agent 开发工程师"
    assert context.active_training_result_id == "training-1"


def test_new_job_invalidates_downstream_active_chain(tmp_path):
    artifact_repo = JsonArtifactRepository(tmp_path)
    context_repo = JsonWorkspaceContextRepository(tmp_path)
    artifact_repo.save("job_analysis", "job-first", {"content": {}}, "thread-a", "job")
    artifact_repo.save("match", "match-first", {"content": {}}, "thread-a", "match")
    artifact_repo.save("plan", "plan-first", {"content": {}}, "thread-a", "planning")
    artifact_repo.save("training_result", "training-first", {"content": {}}, "thread-a", "training")
    context_repo.save(
        WorkspaceContext(
            thread_id="thread-a",
            active_goal="第一条链",
            active_job_analysis_id="job-first",
            active_match_id="match-first",
            active_plan_id="plan-first",
            active_training_result_id="training-first",
            updated_by_run_id="run-first",
        )
    )
    artifact_repo.save("job_analysis", "job-second", {"content": {}}, "thread-a", "job")

    context = update_context_from_artifacts(
        thread_id="thread-a",
        run_id="run-second",
        created_artifact_ids=["job-second"],
        active_goal="第二条链",
        artifact_repo=artifact_repo,
        context_repo=context_repo,
    )

    assert context.active_job_analysis_id == "job-second"
    assert context.active_match_id is None
    assert context.active_plan_id is None
    assert context.active_training_result_id is None


def test_active_artifact_facts_require_submitted_training_and_three_interview_turns(tmp_path):
    artifact_repo = JsonArtifactRepository(tmp_path)
    artifact_repo.save("profile", "profile-1", {"content": {}}, "thread-a", "profile")
    artifact_repo.save("job_analysis", "job-1", {"content": {}}, "thread-a", "job")
    artifact_repo.save("match", "match-1", {"content": {}}, "thread-a", "match")
    artifact_repo.save("plan", "plan-1", {"content": {}}, "thread-a", "planning")
    artifact_repo.save(
        "training_result",
        "training-1",
        {"content": {"task": "写一个 Agent demo", "has_submission": False, "score": None}},
        "thread-a",
        "training",
    )
    artifact_repo.save(
        "interview_summary",
        "interview-1",
        {"content": {"turn_count": 2, "completed": False}},
        "thread-a",
        "interview",
    )
    context = WorkspaceContext(
        thread_id="thread-a",
        active_goal="Agent 开发",
        active_profile_id="profile-1",
        active_job_analysis_id="job-1",
        active_match_id="match-1",
        active_plan_id="plan-1",
        active_training_result_id="training-1",
        active_interview_summary_id="interview-1",
        updated_by_run_id="run-1",
    )

    facts = build_active_artifact_facts(context, artifact_repo)

    assert facts.has_training_result is True
    assert facts.training_submitted is False
    assert facts.training_scored is False
    assert facts.has_interview_summary is True
    assert facts.interview_turn_count == 2
    assert facts.interview_completed is False


def test_artifact_chain_from_context_ignores_missing_optional_ids(tmp_path):
    artifact_repo = JsonArtifactRepository(tmp_path)
    artifact_repo.save("profile", "profile-1", {"content": {}}, "thread-a", "profile")
    context = WorkspaceContext(
        thread_id="thread-a",
        active_goal="Agent 开发",
        active_profile_id="profile-1",
        active_report_id=None,
        updated_by_run_id="run-1",
    )

    chain = artifact_chain_from_context(context, artifact_repo)

    assert [item.id for item in chain] == ["profile-1"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd backend && .venv/bin/python -m pytest -q tests/test_workspace_service.py
```

Expected: FAIL with missing `app.services.workspace`.

- [ ] **Step 3: Implement workspace service**

Create `backend/app/services/workspace.py`:

```python
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.repositories.interfaces import ArtifactRepository
from app.repositories.json_thread_repository import JsonWorkspaceContextRepository
from app.schemas.runs import ActiveArtifactFacts, ArtifactChainItem, WorkspaceContext, WorkspaceResponse


CONTEXT_FIELD_BY_KIND = {
    "profile": "active_profile_id",
    "job_analysis": "active_job_analysis_id",
    "match": "active_match_id",
    "plan": "active_plan_id",
    "training_result": "active_training_result_id",
    "interview_summary": "active_interview_summary_id",
    "report": "active_report_id",
    "compaction_snapshot": "active_compaction_snapshot_id",
}


INVALIDATE_DOWNSTREAM = {
    "profile": [
        "active_job_analysis_id",
        "active_match_id",
        "active_plan_id",
        "active_training_result_id",
        "active_interview_summary_id",
        "active_report_id",
    ],
    "job_analysis": [
        "active_match_id",
        "active_plan_id",
        "active_training_result_id",
        "active_interview_summary_id",
        "active_report_id",
    ],
    "match": [
        "active_plan_id",
        "active_training_result_id",
        "active_interview_summary_id",
        "active_report_id",
    ],
    "plan": [
        "active_training_result_id",
        "active_interview_summary_id",
        "active_report_id",
    ],
    "training_result": ["active_interview_summary_id", "active_report_id"],
    "interview_summary": ["active_report_id"],
}


def update_context_from_artifacts(
    thread_id: str,
    run_id: str,
    created_artifact_ids: list[str],
    active_goal: str | None,
    artifact_repo: ArtifactRepository,
    context_repo: JsonWorkspaceContextRepository,
) -> WorkspaceContext:
    current = context_repo.get(thread_id)
    values = current.model_dump() if current else {
        "thread_id": thread_id,
        "active_goal": active_goal,
        "updated_by_run_id": run_id,
    }
    if active_goal:
        values["active_goal"] = active_goal
    else:
        values["active_goal"] = values.get("active_goal") or "职业发展规划"
    values["updated_by_run_id"] = run_id
    values["updated_at"] = datetime.now(timezone.utc)
    for artifact_id in created_artifact_ids:
        artifact = artifact_repo.get(artifact_id)
        if artifact.get("source_thread_id") != thread_id:
            continue
        for downstream_field in INVALIDATE_DOWNSTREAM.get(str(artifact.get("kind")), []):
            values[downstream_field] = None
        field_name = CONTEXT_FIELD_BY_KIND.get(artifact.get("kind"))
        if field_name:
            values[field_name] = artifact_id
    context = WorkspaceContext.model_validate(values)
    return context_repo.save(context)


def artifact_chain_from_context(
    context: WorkspaceContext,
    artifact_repo: ArtifactRepository,
) -> list[ArtifactChainItem]:
    ordered_fields = [
        "active_profile_id",
        "active_job_analysis_id",
        "active_match_id",
        "active_plan_id",
        "active_training_result_id",
        "active_interview_summary_id",
        "active_report_id",
        "active_compaction_snapshot_id",
    ]
    chain: list[ArtifactChainItem] = []
    for field_name in ordered_fields:
        artifact_id = getattr(context, field_name)
        if not artifact_id:
            continue
        artifact = artifact_repo.get(artifact_id)
        if artifact.get("source_thread_id") != context.thread_id:
            continue
        chain.append(_to_chain_item(artifact))
    return chain


def build_workspace_response(
    thread_id: str,
    artifact_repo: ArtifactRepository,
    context_repo: JsonWorkspaceContextRepository,
) -> WorkspaceResponse:
    context = context_repo.get(thread_id) or context_repo.save(
        WorkspaceContext(thread_id=thread_id, active_goal="职业发展规划", updated_by_run_id="initial")
    )
    artifacts: dict[str, dict[str, Any]] = {}
    for item in artifact_chain_from_context(context, artifact_repo):
        artifacts[item.kind] = artifact_repo.get(item.id)
    return WorkspaceResponse(
        thread_id=thread_id,
        active_context=context,
        workspace_artifacts=artifacts,
        artifact_chain=artifact_chain_from_context(context, artifact_repo),
    )


def build_active_artifact_facts(
    context: WorkspaceContext,
    artifact_repo: ArtifactRepository,
) -> ActiveArtifactFacts:
    training_payload = _artifact_content(context.active_training_result_id, context.thread_id, artifact_repo)
    interview_payload = _artifact_content(context.active_interview_summary_id, context.thread_id, artifact_repo)
    training_submitted = bool(training_payload.get("has_submission") or training_payload.get("submission"))
    training_scored = training_submitted and training_payload.get("score") is not None
    interview_turn_count = int(interview_payload.get("turn_count") or len(interview_payload.get("turns") or []))
    interview_completed = bool(interview_payload.get("completed")) or interview_turn_count >= 3
    return ActiveArtifactFacts(
        has_profile=bool(context.active_profile_id),
        has_job_analysis=bool(context.active_job_analysis_id),
        has_match=bool(context.active_match_id),
        has_plan=bool(context.active_plan_id),
        has_training_result=bool(context.active_training_result_id),
        training_submitted=training_submitted,
        training_scored=training_scored,
        has_interview_summary=bool(context.active_interview_summary_id),
        interview_turn_count=interview_turn_count,
        interview_completed=interview_completed,
    )


def _artifact_content(artifact_id: str | None, thread_id: str, artifact_repo: ArtifactRepository) -> dict[str, Any]:
    if not artifact_id:
        return {}
    artifact = artifact_repo.get(artifact_id)
    if artifact.get("source_thread_id") != thread_id:
        return {}
    payload = artifact.get("payload") or {}
    content = payload.get("content") if isinstance(payload, dict) else {}
    return content if isinstance(content, dict) else {}


def _to_chain_item(artifact: dict[str, Any]) -> ArtifactChainItem:
    return ArtifactChainItem(
        id=artifact["id"],
        kind=artifact["kind"],
        source_thread_id=artifact["source_thread_id"],
        source_agent=artifact["source_agent"],
        parent_artifact_ids=artifact.get("parent_artifact_ids", []),
        updated_at=artifact.get("updated_at"),
    )
```

- [ ] **Step 4: Add active-chain report helpers**

In `backend/app/artifacts/markdown.py`, add:

```python
def build_markdown_report_from_chain(thread_id: str, artifacts: list[dict[str, Any]]) -> str:
    by_kind = _required_artifacts_from_chain(thread_id, artifacts)
    _validate_required_report_content(thread_id, by_kind)
    return build_markdown_report(thread_id, list(by_kind.values()))


def required_parent_artifact_ids_from_chain(thread_id: str, artifacts: list[dict[str, Any]]) -> list[str]:
    by_kind = _required_artifacts_from_chain(thread_id, artifacts)
    _validate_required_report_content(thread_id, by_kind)
    return [by_kind[kind]["id"] for kind in REQUIRED_REPORT_KINDS]


def _required_artifacts_from_chain(thread_id: str, artifacts: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_kind: dict[str, dict[str, Any]] = {}
    for artifact in artifacts:
        if artifact.get("source_thread_id") != thread_id:
            continue
        kind = artifact.get("kind")
        if kind in REQUIRED_REPORT_KINDS:
            expected_producer = EXPECTED_REPORT_PRODUCERS[kind]
            actual_producer = artifact.get("source_agent")
            if actual_producer != expected_producer:
                raise MissingArtifactError(
                    f"Invalid producer for {kind}: expected {expected_producer}, got {actual_producer}"
                )
            by_kind[kind] = artifact
    for kind in REQUIRED_REPORT_KINDS:
        if kind not in by_kind:
            raise MissingArtifactError(f"Missing required artifact kind: {kind}")
    return by_kind


def _validate_required_report_content(thread_id: str, by_kind: dict[str, dict[str, Any]]) -> None:
    training_content = _payload_content(by_kind["training_result"])
    if not training_content.get("has_submission") or training_content.get("score") is None:
        raise MissingArtifactError(
            f"Thread {thread_id!r} has a training_result artifact, but the training answer is not submitted and scored"
        )
    interview_content = _payload_content(by_kind["interview_summary"])
    turn_count = int(interview_content.get("turn_count") or len(interview_content.get("turns") or []))
    if turn_count < 3:
        raise MissingArtifactError(
            f"Thread {thread_id!r} has an interview_summary artifact, but fewer than three interview turns are complete"
        )


def _payload_content(artifact: dict[str, Any]) -> dict[str, Any]:
    payload = artifact.get("payload") or {}
    content = payload.get("content") if isinstance(payload, dict) else {}
    return content if isinstance(content, dict) else {}
```

Append these report gating regressions to `backend/tests/test_artifact_reporting.py`:

```python
from app.artifacts.markdown import build_markdown_report_from_chain


def test_markdown_report_from_chain_rejects_task_only_training_result() -> None:
    artifacts = [
        _artifact("profile", "profile", {"summary": "Python/FastAPI backend student"}),
        _artifact("job_analysis", "job", {"summary": "Agent 开发工程师"}),
        _artifact("match", "match", {"score": 74, "gaps": ["LangGraph 证据不足"]}),
        _artifact("plan", "planning", {"milestones": ["补齐 LangGraph 项目证据"]}),
        _artifact(
            "training_result",
            "training",
            {"task": "写一个 Agent demo", "has_submission": False, "submission": None, "score": None},
        ),
        _artifact("interview_summary", "interview", {"turn_count": 3, "completed": True}),
    ]

    with pytest.raises(MissingArtifactError, match="training answer"):
        build_markdown_report_from_chain("thread-report-producer", artifacts)


def test_markdown_report_from_chain_rejects_interview_under_three_turns() -> None:
    artifacts = [
        _artifact("profile", "profile", {"summary": "Python/FastAPI backend student"}),
        _artifact("job_analysis", "job", {"summary": "Agent 开发工程师"}),
        _artifact("match", "match", {"score": 74, "gaps": ["LangGraph 证据不足"]}),
        _artifact("plan", "planning", {"milestones": ["补齐 LangGraph 项目证据"]}),
        _artifact(
            "training_result",
            "training",
            {"has_submission": True, "submission": "demo", "score": 82},
        ),
        _artifact("interview_summary", "interview", {"turn_count": 2, "completed": False}),
    ]

    with pytest.raises(MissingArtifactError, match="fewer than three interview turns"):
        build_markdown_report_from_chain("thread-report-producer", artifacts)
```

- [ ] **Step 5: Run workspace service tests**

Run:

```bash
cd backend && .venv/bin/python -m pytest -q tests/test_workspace_service.py tests/test_artifact_reporting.py
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/workspace.py backend/app/artifacts/markdown.py backend/tests/test_workspace_service.py backend/tests/test_artifact_reporting.py
git commit -m "Add active workspace context service"
```

---

## Task 5: Run Orchestrator And `/api/runs` v3.1 Response

**Files:**
- Create: `backend/app/services/run_orchestrator.py`
- Modify: `backend/app/graphs/workflow.py`
- Modify: `backend/app/api/runs.py`
- Modify: `backend/app/providers/base.py`
- Modify: `backend/tests/test_api_e2e.py`

- [ ] **Step 1: Write failing `/api/runs` E2E test**

Add to `backend/tests/test_api_e2e.py`:

```python
def test_runs_endpoint_persists_messages_and_returns_v31_runtime_contract(tmp_path: Path, monkeypatch) -> None:
    from app.api import runs
    from app.repositories.json_thread_repository import JsonConversationRepository, JsonWorkspaceContextRepository

    monkeypatch.setattr(runs, "RUNTIME_DATA_DIR", tmp_path)
    client = TestClient(app)

    response = client.post(
        "/api/runs",
        json={"thread_id": "thread-v31-run", "message": "我会 Python FastAPI，想匹配 Agent 开发岗位"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_status"] == "completed"
    assert payload["last_business_agent"] == "profile"
    assert payload["current_runtime_node"] == "memory_manager"
    assert payload["assistant_message"]["role"] == "assistant"
    assert payload["assistant_message"]["run_id"] == payload["run_id"]
    assert payload["supervisor_decision"]["intent"] == "build_profile"
    assert payload["workspace_delta"]["updated_context"]["active_profile_id"]
    assert payload["artifact_chain"][0]["kind"] == "profile"
    assert payload["memory_updates"]
    assert len(payload["memory_updates"]) == 1

    messages = JsonConversationRepository(tmp_path).list_by_thread("thread-v31-run")
    assert [message.role.value for message in messages] == ["user", "assistant"]
    assert messages[1].artifact_refs == payload["assistant_message"]["artifact_refs"]
    assert payload["memory_updates"][0]["source_message_id"] == messages[0].id
    assert JsonWorkspaceContextRepository(tmp_path).get("thread-v31-run").active_profile_id


def test_runs_endpoint_persists_assistant_error_message_on_permission_denied(tmp_path: Path, monkeypatch) -> None:
    from app.api import runs
    from app.agents.runtime import PermissionDenied
    from app.repositories.json_thread_repository import JsonConversationRepository
    from app.services import run_orchestrator

    def deny(*args, **kwargs):
        raise PermissionDenied("training cannot write match")

    monkeypatch.setattr(runs, "RUNTIME_DATA_DIR", tmp_path)
    monkeypatch.setattr(run_orchestrator, "run_career_graph", deny)
    client = TestClient(app)

    response = client.post(
        "/api/runs",
        json={"thread_id": "thread-permission-error", "message": "请做 match 分析"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_status"] == "permission_denied"
    assert payload["assistant_message"]["role"] == "assistant"
    assert payload["retryable"] is False
    messages = JsonConversationRepository(tmp_path).list_by_thread("thread-permission-error")
    assert [message.role.value for message in messages] == ["user", "assistant"]


def test_runs_endpoint_marks_provider_error_retryable(tmp_path: Path, monkeypatch) -> None:
    from app.api import runs
    from app.providers.base import ProviderError
    from app.repositories.json_thread_repository import JsonConversationRepository
    from app.services import run_orchestrator

    def fail_provider(*args, **kwargs):
        raise ProviderError("qwen upstream timeout")

    monkeypatch.setattr(runs, "RUNTIME_DATA_DIR", tmp_path)
    monkeypatch.setattr(run_orchestrator, "run_career_graph", fail_provider)
    client = TestClient(app)

    response = client.post(
        "/api/runs",
        json={"thread_id": "thread-provider-error", "message": "请分析岗位"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_status"] == "provider_error"
    assert payload["retryable"] is True
    assert "模型服务" in payload["assistant_message"]["content"]
    messages = JsonConversationRepository(tmp_path).list_by_thread("thread-provider-error")
    assert [message.role.value for message in messages] == ["user", "assistant"]


def test_start_interview_requires_submitted_training_result(tmp_path: Path, monkeypatch) -> None:
    from app.api import runs
    from app.repositories.json_repository import JsonArtifactRepository
    from app.repositories.json_thread_repository import JsonWorkspaceContextRepository
    from app.schemas.runs import WorkspaceContext

    monkeypatch.setattr(runs, "RUNTIME_DATA_DIR", tmp_path)
    artifact_repo = JsonArtifactRepository(tmp_path)
    context_repo = JsonWorkspaceContextRepository(tmp_path)
    artifact_repo.save("profile", "profile-1", {"content": {}}, "thread-training-gate", "profile")
    artifact_repo.save("job_analysis", "job-1", {"content": {}}, "thread-training-gate", "job")
    artifact_repo.save("match", "match-1", {"content": {}}, "thread-training-gate", "match")
    artifact_repo.save("plan", "plan-1", {"content": {}}, "thread-training-gate", "planning")
    artifact_repo.save(
        "training_result",
        "training-1",
        {"content": {"task": "写一个 Agent demo", "has_submission": False, "score": None}},
        "thread-training-gate",
        "training",
    )
    context_repo.save(
        WorkspaceContext(
            thread_id="thread-training-gate",
            active_goal="Agent 开发工程师",
            active_profile_id="profile-1",
            active_job_analysis_id="job-1",
            active_match_id="match-1",
            active_plan_id="plan-1",
            active_training_result_id="training-1",
            updated_by_run_id="seed",
        )
    )
    client = TestClient(app)

    response = client.post("/api/runs", json={"thread_id": "thread-training-gate", "message": "开始模拟面试"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_status"] == "blocked_by_prerequisite"
    assert payload["supervisor_decision"]["missing_capabilities"] == ["training_scored"]
    assert JsonArtifactRepository(tmp_path).list_by_kind("thread-training-gate", "interview_summary") == []


def test_blocked_match_request_does_not_create_memory_candidate(tmp_path: Path, monkeypatch) -> None:
    from app.api import runs
    from app.repositories.json_thread_repository import JsonMemoryRepository

    monkeypatch.setattr(runs, "RUNTIME_DATA_DIR", tmp_path)
    client = TestClient(app)

    response = client.post("/api/runs", json={"thread_id": "thread-blocked-memory", "message": "请做 match 分析"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_status"] == "blocked_by_prerequisite"
    assert payload["memory_updates"] == []
    assert JsonMemoryRepository(tmp_path).list_by_thread("thread-blocked-memory") == []


def test_training_submission_does_not_reset_active_goal(tmp_path: Path, monkeypatch) -> None:
    from app.api import runs
    from app.repositories.json_repository import JsonArtifactRepository
    from app.repositories.json_thread_repository import JsonWorkspaceContextRepository
    from app.schemas.runs import WorkspaceContext

    monkeypatch.setattr(runs, "RUNTIME_DATA_DIR", tmp_path)
    artifact_repo = JsonArtifactRepository(tmp_path)
    context_repo = JsonWorkspaceContextRepository(tmp_path)
    artifact_repo.save("profile", "profile-1", {"content": {}}, "thread-goal-preserve", "profile")
    artifact_repo.save("job_analysis", "job-1", {"content": {}}, "thread-goal-preserve", "job")
    artifact_repo.save("match", "match-1", {"content": {}}, "thread-goal-preserve", "match")
    artifact_repo.save("plan", "plan-1", {"content": {}}, "thread-goal-preserve", "planning")
    context_repo.save(
        WorkspaceContext(
            thread_id="thread-goal-preserve",
            active_goal="Agent 开发工程师",
            active_profile_id="profile-1",
            active_job_analysis_id="job-1",
            active_match_id="match-1",
            active_plan_id="plan-1",
            updated_by_run_id="seed",
        )
    )
    client = TestClient(app)

    response = client.post(
        "/api/runs",
        json={"thread_id": "thread-goal-preserve", "message": "我的训练答案：我会设计 FastAPI + LangGraph demo。"},
    )

    assert response.status_code == 200
    context = JsonWorkspaceContextRepository(tmp_path).get("thread-goal-preserve")
    assert context.active_goal == "Agent 开发工程师"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd backend && .venv/bin/python -m pytest -q tests/test_api_e2e.py::test_runs_endpoint_persists_messages_and_returns_v31_runtime_contract tests/test_api_e2e.py::test_runs_endpoint_persists_assistant_error_message_on_permission_denied tests/test_api_e2e.py::test_runs_endpoint_marks_provider_error_retryable tests/test_api_e2e.py::test_start_interview_requires_submitted_training_result tests/test_api_e2e.py::test_blocked_match_request_does_not_create_memory_candidate tests/test_api_e2e.py::test_training_submission_does_not_reset_active_goal
```

Expected: FAIL because `/api/runs` does not return v3.1 fields or persist messages.

- [ ] **Step 3: Allow workflow to accept a run id**

Define the provider exception used by the orchestrator in `backend/app/providers/base.py`:

```python
class ProviderError(RuntimeError):
    pass
```

Modify `run_career_graph()` in `backend/app/graphs/workflow.py`:

```python
def run_career_graph(
    thread_id: str,
    message: str,
    artifact_repo: ArtifactRepository,
    run_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], list[AgentTraceItem]]:
    graph = get_runtime_graph(artifact_repo)
    config = {"configurable": {"thread_id": thread_id}}
    initial_metadata = dict(metadata or {})
    initial_metadata["run_id"] = run_id
    state = graph.invoke(
        {"thread_id": thread_id, "user_message": message, "metadata": initial_metadata},
        config=config,
    )
    snapshots = state.get("agent_snapshots", {})
    trace = [
        AgentTraceItem(
            agent_id=agent_id,
            summary=snapshot.get("summary", ""),
            artifact_ids=snapshot.get("last_artifact_ids", []),
            used_skill_refs=snapshot.get("used_skill_refs", []),
        )
        for agent_id, snapshot in snapshots.items()
    ]
    return state, trace
```

Keep `build_graph()`, `get_runtime_graph()`, and the `config={"configurable": {"thread_id": thread_id}}` behavior unchanged.

- [ ] **Step 4: Implement run orchestrator**

Create `backend/app/services/run_orchestrator.py`:

```python
from __future__ import annotations

from uuid import uuid4

from app.agents.runtime import PermissionDenied
from app.graphs.workflow import run_career_graph
from app.providers.base import ProviderError
from app.repositories.json_repository import JsonArtifactRepository
from app.repositories.json_thread_repository import JsonConversationRepository, JsonMemoryRepository, JsonWorkspaceContextRepository
from app.schemas.memory import MemoryItem, MemoryScope, MemoryStatus
from app.schemas.runs import (
    ArtifactChainItem,
    ConversationMessage,
    ConversationRole,
    RunResponse,
    RunStatus,
    SupervisorDecision,
    WorkspaceContext,
    WorkspaceDelta,
)
from app.services.workspace import artifact_chain_from_context, build_active_artifact_facts, update_context_from_artifacts


class RunOrchestrator:
    def __init__(self, root):
        self.artifact_repo = JsonArtifactRepository(root)
        self.message_repo = JsonConversationRepository(root)
        self.context_repo = JsonWorkspaceContextRepository(root)
        self.memory_repo = JsonMemoryRepository(root)

    def run(self, thread_id: str, message: str) -> RunResponse:
        run_id = f"run-{uuid4().hex[:12]}"
        user_message = ConversationMessage(
            id=f"msg-{uuid4().hex[:12]}",
            thread_id=thread_id,
            role=ConversationRole.USER,
            content=message,
            run_id=run_id,
        )
        self.message_repo.save(user_message)

        before_ids = {artifact["id"] for artifact in self.artifact_repo.list_by_thread(thread_id)}
        current_context = self.context_repo.get(thread_id)
        current_chain = artifact_chain_from_context(current_context, self.artifact_repo) if current_context else []
        run_metadata = {}
        if current_context:
            run_metadata = {
                "active_artifact_kinds": [item.kind for item in current_chain],
                "active_facts": build_active_artifact_facts(current_context, self.artifact_repo).model_dump(mode="json"),
                "active_context": current_context.model_dump(mode="json"),
            }
        try:
            state, trace = run_career_graph(
                thread_id,
                message,
                self.artifact_repo,
                run_id=run_id,
                metadata=run_metadata,
            )
        except PermissionDenied as exc:
            return self._error_response(
                thread_id=thread_id,
                run_id=run_id,
                content="当前 Agent 没有权限执行该操作。",
                run_status=RunStatus.PERMISSION_DENIED,
                retryable=False,
                warning=str(exc),
            )
        except ProviderError as exc:
            return self._error_response(
                thread_id=thread_id,
                run_id=run_id,
                content="模型服务暂时不可用，可以稍后重试或切换 Mock Provider。",
                run_status=RunStatus.PROVIDER_ERROR,
                retryable=True,
                warning=str(exc),
            )
        except Exception as exc:
            return self._error_response(
                thread_id=thread_id,
                run_id=run_id,
                content="本轮处理失败，请稍后重试。",
                run_status=RunStatus.FAILED,
                retryable=True,
                warning=str(exc),
            )
        after_refs = self.artifact_repo.list_by_thread(thread_id)
        created_ids = [artifact["id"] for artifact in after_refs if artifact["id"] not in before_ids]
        decision_payload = state.get("metadata", {}).get("supervisor_decision") or state.get("supervisor_decision")
        supervisor_decision = (
            SupervisorDecision.model_validate(decision_payload)
            if decision_payload
            else None
        )
        last_business_agent = state.get("metadata", {}).get("last_business_agent") or state.get("last_business_agent")
        current_runtime_node = state.get("metadata", {}).get("current_runtime_node") or state.get("active_agent")
        active_goal = _active_goal(message, supervisor_decision)
        context = update_context_from_artifacts(
            thread_id=thread_id,
            run_id=run_id,
            created_artifact_ids=created_ids,
            active_goal=active_goal,
            artifact_repo=self.artifact_repo,
            context_repo=self.context_repo,
        )
        chain = artifact_chain_from_context(context, self.artifact_repo)
        assistant_message = ConversationMessage(
            id=f"msg-{uuid4().hex[:12]}",
            thread_id=thread_id,
            role=ConversationRole.ASSISTANT,
            content=_assistant_summary(supervisor_decision, created_ids),
            run_id=run_id,
            artifact_refs=created_ids,
            last_business_agent=last_business_agent,
            current_runtime_node=current_runtime_node,
            warnings=state.get("warnings", []),
        )
        self.message_repo.save(assistant_message)
        memory_updates = self._save_memory_candidates(
            thread_id=thread_id,
            run_id=run_id,
            source_message_id=user_message.id,
            message=message,
            supervisor_decision=supervisor_decision,
        )
        compaction_snapshot = _latest_compaction(chain, self.artifact_repo)

        return RunResponse(
            run_id=run_id,
            thread_id=thread_id,
            run_status=_status_from_state(state, supervisor_decision),
            active_agent=state.get("active_agent", "supervisor"),
            last_business_agent=last_business_agent,
            current_runtime_node=current_runtime_node,
            assistant_message=assistant_message,
            supervisor_decision=supervisor_decision,
            agent_trace_summary=trace,
            used_skill_refs=state.get("loaded_skill_refs", []),
            used_skill_runtime_refs=state.get("loaded_skill_runtime_refs", []),
            artifacts=after_refs,
            artifact_chain=chain,
            workspace_delta=WorkspaceDelta(
                created_artifacts=[
                    _chain_item(self.artifact_repo.get(artifact_id)) for artifact_id in created_ids
                ],
                updated_context=context,
            ),
            compaction_snapshot=compaction_snapshot,
            memory_updates=memory_updates,
            blocking_reason=_blocking_reason(supervisor_decision),
            missing_artifacts=supervisor_decision.missing_prerequisites if supervisor_decision else [],
            retryable=False,
            next_actions=supervisor_decision.next_actions if supervisor_decision else ["继续职业工作流"],
            warnings=state.get("warnings", []),
        )

    def _save_memory_candidates(
        self,
        thread_id: str,
        run_id: str,
        source_message_id: str,
        message: str,
        supervisor_decision: SupervisorDecision | None,
    ) -> list[MemoryItem]:
        if supervisor_decision is None or supervisor_decision.missing_prerequisites or supervisor_decision.missing_capabilities:
            return []
        candidates: list[MemoryItem] = []
        if supervisor_decision.intent.value in {"build_profile", "analyze_job", "plan"}:
            memory = MemoryItem(
                id=f"memory-{uuid4().hex[:12]}",
                thread_id=thread_id,
                scope=MemoryScope.GOAL,
                fact=message[:160],
                source_message_id=source_message_id,
                confidence=0.72,
                status=MemoryStatus.PENDING_CONFIRMATION,
            )
            candidates.append(self.memory_repo.save(memory))
        return candidates

    def _error_response(
        self,
        thread_id: str,
        run_id: str,
        content: str,
        run_status: RunStatus,
        retryable: bool,
        warning: str,
    ) -> RunResponse:
        context = self.context_repo.get(thread_id) or self.context_repo.save(
            WorkspaceContext(thread_id=thread_id, active_goal="职业发展规划", updated_by_run_id=run_id)
        )
        chain = artifact_chain_from_context(context, self.artifact_repo)
        assistant_message = ConversationMessage(
            id=f"msg-{uuid4().hex[:12]}",
            thread_id=thread_id,
            role=ConversationRole.ASSISTANT,
            content=content,
            run_id=run_id,
            artifact_refs=[],
            current_runtime_node="error",
            warnings=[warning],
        )
        self.message_repo.save(assistant_message)
        return RunResponse(
            run_id=run_id,
            thread_id=thread_id,
            run_status=run_status,
            active_agent="supervisor",
            current_runtime_node="error",
            assistant_message=assistant_message,
            artifacts=self.artifact_repo.list_by_thread(thread_id),
            artifact_chain=chain,
            workspace_delta=WorkspaceDelta(created_artifacts=[], updated_context=context),
            memory_updates=[],
            retryable=retryable,
            next_actions=["重试本轮请求"] if retryable else ["调整请求后继续"],
            warnings=[warning],
        )


def _active_goal(message: str, decision: SupervisorDecision | None) -> str | None:
    if decision and decision.intent.value in {"analyze_job", "match", "plan"}:
        return message[:80]
    return None


def _assistant_summary(decision: SupervisorDecision | None, artifact_ids: list[str]) -> str:
    if decision and decision.missing_prerequisites:
        return decision.user_facing_reason
    if artifact_ids:
        return f"已完成本轮处理，并生成 {len(artifact_ids)} 个运行产物。"
    return "本轮已处理完成，可以继续输入下一步。"


def _status_from_state(state: dict, decision: SupervisorDecision | None) -> RunStatus:
    if decision and (decision.missing_prerequisites or decision.missing_capabilities):
        return RunStatus.BLOCKED_BY_PREREQUISITE
    if state.get("pending_question"):
        return RunStatus.NEEDS_INPUT
    return RunStatus.COMPLETED


def _blocking_reason(decision: SupervisorDecision | None) -> str | None:
    if decision and (decision.missing_prerequisites or decision.missing_capabilities):
        return decision.user_facing_reason
    return None


def _chain_item(artifact: dict) -> ArtifactChainItem:
    return ArtifactChainItem(
        id=artifact["id"],
        kind=artifact["kind"],
        source_thread_id=artifact["source_thread_id"],
        source_agent=artifact["source_agent"],
        parent_artifact_ids=artifact.get("parent_artifact_ids", []),
        updated_at=artifact.get("updated_at"),
    )


def _latest_compaction(chain: list[ArtifactChainItem], artifact_repo: JsonArtifactRepository) -> dict | None:
    for item in reversed(chain):
        if item.kind == "compaction_snapshot":
            return artifact_repo.get(item.id).get("payload")
    return None
```

- [ ] **Step 5: Update `/api/runs`**

Modify `backend/app/api/runs.py`:

```python
from app.services.run_orchestrator import RunOrchestrator


@router.post("", response_model=RunResponse)
def create_run(request: RunRequest) -> RunResponse:
    return RunOrchestrator(RUNTIME_DATA_DIR).run(request.thread_id, request.message)
```

- [ ] **Step 6: Run the E2E test**

Run:

```bash
cd backend && .venv/bin/python -m pytest -q tests/test_api_e2e.py::test_runs_endpoint_persists_messages_and_returns_v31_runtime_contract tests/test_api_e2e.py::test_runs_endpoint_persists_assistant_error_message_on_permission_denied tests/test_api_e2e.py::test_runs_endpoint_marks_provider_error_retryable tests/test_api_e2e.py::test_start_interview_requires_submitted_training_result tests/test_api_e2e.py::test_blocked_match_request_does_not_create_memory_candidate tests/test_api_e2e.py::test_training_submission_does_not_reset_active_goal
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/app/services/run_orchestrator.py backend/app/graphs/workflow.py backend/app/api/runs.py backend/app/providers/base.py backend/tests/test_api_e2e.py
git commit -m "Orchestrate v31 chat runs"
```

---

## Task 6: Threads API, Active-Chain Report Export, And Memory Confirmation

**Files:**
- Create: `backend/app/api/threads.py`
- Modify: `backend/app/api/reports.py`
- Modify: `backend/app/main.py`
- Modify: `backend/tests/test_api_e2e.py`

- [ ] **Step 1: Write failing API tests**

Add to `backend/tests/test_api_e2e.py`:

```python
def test_threads_workspace_and_messages_restore_chat_state(tmp_path: Path, monkeypatch) -> None:
    from app.api import reports, runs, threads

    monkeypatch.setattr(runs, "RUNTIME_DATA_DIR", tmp_path)
    monkeypatch.setattr(threads, "RUNTIME_DATA_DIR", tmp_path)
    monkeypatch.setattr(reports, "RUNTIME_DATA_DIR", tmp_path)
    client = TestClient(app)

    run = client.post(
        "/api/runs",
        json={"thread_id": "thread-workspace-api", "message": "我会 Python FastAPI，想匹配 Agent 开发岗位"},
    )
    assert run.status_code == 200

    workspace = client.get("/api/threads/thread-workspace-api/workspace")
    messages = client.get("/api/threads/thread-workspace-api/messages")
    artifacts = client.get("/api/threads/thread-workspace-api/artifacts")
    memory = client.get("/api/threads/thread-workspace-api/memory")

    assert workspace.status_code == 200
    assert workspace.json()["active_context"]["active_profile_id"]
    assert messages.status_code == 200
    assert [message["role"] for message in messages.json()] == ["user", "assistant"]
    assert artifacts.status_code == 200
    assert any(artifact["kind"] == "profile" for artifact in artifacts.json())
    assert memory.status_code == 200
    assert isinstance(memory.json(), list)


def test_memory_confirm_and_reject_endpoints_update_status(tmp_path: Path, monkeypatch) -> None:
    from app.api import threads
    from app.repositories.json_thread_repository import JsonMemoryRepository
    from app.schemas.memory import MemoryItem, MemoryScope, MemoryStatus

    monkeypatch.setattr(threads, "RUNTIME_DATA_DIR", tmp_path)
    repo = JsonMemoryRepository(tmp_path)
    repo.save(
        MemoryItem(
            id="memory-api-1",
            thread_id="thread-memory-api",
            scope=MemoryScope.GOAL,
            fact="想做 Agent 开发",
            status=MemoryStatus.PENDING_CONFIRMATION,
        )
    )
    client = TestClient(app)

    confirmed = client.post("/api/threads/thread-memory-api/memory/memory-api-1/confirm")
    rejected = client.post("/api/threads/thread-memory-api/memory/memory-api-1/reject")

    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "confirmed"
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"


def test_memory_confirm_missing_item_returns_404(tmp_path: Path, monkeypatch) -> None:
    from app.api import threads

    monkeypatch.setattr(threads, "RUNTIME_DATA_DIR", tmp_path)
    client = TestClient(app)

    response = client.post("/api/threads/thread-memory-api/memory/not-found/confirm")

    assert response.status_code == 404


def test_report_export_updates_active_report_context(tmp_path: Path, monkeypatch) -> None:
    from app.api import reports, runs, threads
    from app.repositories.json_thread_repository import JsonWorkspaceContextRepository

    monkeypatch.setattr(runs, "RUNTIME_DATA_DIR", tmp_path)
    monkeypatch.setattr(threads, "RUNTIME_DATA_DIR", tmp_path)
    monkeypatch.setattr(reports, "RUNTIME_DATA_DIR", tmp_path)
    client = TestClient(app)
    thread_id = "thread-report-context"

    for message in complete_demo_messages("REPORT_CONTEXT"):
        response = client.post("/api/runs", json={"thread_id": thread_id, "message": message})
        assert response.status_code == 200

    report = client.get(f"/api/reports/{thread_id}/markdown")

    assert report.status_code == 200
    context = JsonWorkspaceContextRepository(tmp_path).get(thread_id)
    assert context.active_report_id == f"report-{thread_id}-latest"


def test_report_export_rejects_task_only_training_result(tmp_path: Path, monkeypatch) -> None:
    from app.api import reports
    from app.repositories.json_repository import JsonArtifactRepository
    from app.repositories.json_thread_repository import JsonWorkspaceContextRepository
    from app.schemas.runs import WorkspaceContext

    monkeypatch.setattr(reports, "RUNTIME_DATA_DIR", tmp_path)
    artifact_repo = JsonArtifactRepository(tmp_path)
    context_repo = JsonWorkspaceContextRepository(tmp_path)
    _seed_report_chain(artifact_repo, context_repo, "thread-report-training-gate", training_score=None, turn_count=3)
    client = TestClient(app)

    response = client.get("/api/reports/thread-report-training-gate/markdown")

    assert response.status_code == 409
    assert "training answer" in response.json()["detail"]


def test_report_export_rejects_interview_summary_under_three_turns(tmp_path: Path, monkeypatch) -> None:
    from app.api import reports
    from app.repositories.json_repository import JsonArtifactRepository
    from app.repositories.json_thread_repository import JsonWorkspaceContextRepository

    monkeypatch.setattr(reports, "RUNTIME_DATA_DIR", tmp_path)
    artifact_repo = JsonArtifactRepository(tmp_path)
    context_repo = JsonWorkspaceContextRepository(tmp_path)
    _seed_report_chain(artifact_repo, context_repo, "thread-report-interview-gate", training_score=82, turn_count=2)
    client = TestClient(app)

    response = client.get("/api/reports/thread-report-interview-gate/markdown")

    assert response.status_code == 409
    assert "fewer than three interview turns" in response.json()["detail"]


def _seed_report_chain(artifact_repo, context_repo, thread_id: str, training_score: int | None, turn_count: int) -> None:
    from app.schemas.runs import WorkspaceContext

    artifact_repo.save("profile", "profile-1", {"content": {}}, thread_id, "profile")
    artifact_repo.save("job_analysis", "job-1", {"content": {}}, thread_id, "job")
    artifact_repo.save("match", "match-1", {"content": {}}, thread_id, "match")
    artifact_repo.save("plan", "plan-1", {"content": {}}, thread_id, "planning")
    artifact_repo.save(
        "training_result",
        "training-1",
        {"content": {"has_submission": training_score is not None, "submission": "demo", "score": training_score}},
        thread_id,
        "training",
    )
    artifact_repo.save(
        "interview_summary",
        "interview-1",
        {"content": {"turn_count": turn_count, "completed": turn_count >= 3}},
        thread_id,
        "interview",
    )
    context_repo.save(
        WorkspaceContext(
            thread_id=thread_id,
            active_goal="Agent 开发工程师",
            active_profile_id="profile-1",
            active_job_analysis_id="job-1",
            active_match_id="match-1",
            active_plan_id="plan-1",
            active_training_result_id="training-1",
            active_interview_summary_id="interview-1",
            updated_by_run_id="seed",
        )
    )
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd backend && .venv/bin/python -m pytest -q tests/test_api_e2e.py::test_threads_workspace_and_messages_restore_chat_state tests/test_api_e2e.py::test_memory_confirm_and_reject_endpoints_update_status tests/test_api_e2e.py::test_memory_confirm_missing_item_returns_404 tests/test_api_e2e.py::test_report_export_updates_active_report_context tests/test_api_e2e.py::test_report_export_rejects_task_only_training_result tests/test_api_e2e.py::test_report_export_rejects_interview_summary_under_three_turns
```

Expected: FAIL with 404 for `/api/threads/thread-workspace-api/workspace` and `/api/threads/thread-memory-api/memory/memory-api-1/confirm`.

- [ ] **Step 3: Create threads router**

Create `backend/app/api/threads.py`:

```python
from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Path

from app.api.runs import SAFE_THREAD_ID_PATTERN
from app.repositories.json_repository import JsonArtifactRepository
from app.repositories.json_thread_repository import (
    JsonConversationRepository,
    JsonMemoryRepository,
    JsonWorkspaceContextRepository,
)
from app.repositories.paths import RUNTIME_DATA_DIR
from app.schemas.memory import MemoryItem, MemoryStatus
from app.schemas.runs import ConversationMessage, WorkspaceResponse
from app.services.workspace import build_workspace_response


router = APIRouter(prefix="/api/threads", tags=["threads"])


@router.get("/{thread_id}/workspace", response_model=WorkspaceResponse)
def get_workspace(thread_id: Annotated[str, Path(pattern=SAFE_THREAD_ID_PATTERN)]) -> WorkspaceResponse:
    return build_workspace_response(
        thread_id,
        JsonArtifactRepository(RUNTIME_DATA_DIR),
        JsonWorkspaceContextRepository(RUNTIME_DATA_DIR),
    )


@router.get("/{thread_id}/messages", response_model=list[ConversationMessage])
def get_messages(thread_id: Annotated[str, Path(pattern=SAFE_THREAD_ID_PATTERN)]) -> list[ConversationMessage]:
    return JsonConversationRepository(RUNTIME_DATA_DIR).list_by_thread(thread_id)


@router.get("/{thread_id}/artifacts", response_model=list[dict[str, Any]])
def get_artifacts(thread_id: Annotated[str, Path(pattern=SAFE_THREAD_ID_PATTERN)]) -> list[dict[str, Any]]:
    return JsonArtifactRepository(RUNTIME_DATA_DIR).list_by_thread(thread_id)


@router.get("/{thread_id}/memory", response_model=list[MemoryItem])
def get_memory(thread_id: Annotated[str, Path(pattern=SAFE_THREAD_ID_PATTERN)]) -> list[MemoryItem]:
    return JsonMemoryRepository(RUNTIME_DATA_DIR).list_by_thread(thread_id)


@router.post("/{thread_id}/memory/{memory_id}/confirm", response_model=MemoryItem)
def confirm_memory(
    thread_id: Annotated[str, Path(pattern=SAFE_THREAD_ID_PATTERN)],
    memory_id: Annotated[str, Path(pattern=SAFE_THREAD_ID_PATTERN)],
) -> MemoryItem:
    try:
        return JsonMemoryRepository(RUNTIME_DATA_DIR).set_status(thread_id, memory_id, MemoryStatus.CONFIRMED)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{thread_id}/memory/{memory_id}/reject", response_model=MemoryItem)
def reject_memory(
    thread_id: Annotated[str, Path(pattern=SAFE_THREAD_ID_PATTERN)],
    memory_id: Annotated[str, Path(pattern=SAFE_THREAD_ID_PATTERN)],
) -> MemoryItem:
    try:
        return JsonMemoryRepository(RUNTIME_DATA_DIR).set_status(thread_id, memory_id, MemoryStatus.REJECTED)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
```

- [ ] **Step 4: Include router in app**

Modify `backend/app/main.py`:

```python
from app.api.threads import router as threads_router

app.include_router(threads_router)
```

- [ ] **Step 5: Update report export to use active chain**

Modify `backend/app/api/reports.py`:

```python
from app.artifacts.markdown import (
    MissingArtifactError,
    build_markdown_report_from_chain,
    required_parent_artifact_ids_from_chain,
)
from app.repositories.json_thread_repository import JsonWorkspaceContextRepository
from app.services.workspace import artifact_chain_from_context, update_context_from_artifacts


context = JsonWorkspaceContextRepository(RUNTIME_DATA_DIR).get(thread_id)
if context is None:
    artifact_refs = repo.list_by_thread(thread_id)
    artifacts = [repo.get(artifact["id"]) for artifact in artifact_refs]
else:
    artifacts = [repo.get(item.id) for item in artifact_chain_from_context(context, repo)]
try:
    markdown = build_markdown_report_from_chain(thread_id, artifacts)
    parent_artifact_ids = required_parent_artifact_ids_from_chain(thread_id, artifacts)
except MissingArtifactError as exc:
    raise HTTPException(status_code=409, detail=str(exc)) from exc
```

Keep saving `report-{thread_id}-latest` with `source_agent="report"` and parent ids from the active chain. After saving the report artifact, update the active context so the workspace report tab and artifact chain include it:

```python
report_artifact_id = f"report-{thread_id}-latest"
repo.save(
    kind="report",
    artifact_id=report_artifact_id,
    payload={
        "title": "CareerAgent Markdown report",
        "format": "markdown",
        "content": markdown,
    },
    source_thread_id=thread_id,
    source_agent="report",
    parent_artifact_ids=parent_artifact_ids,
)
context_repo = JsonWorkspaceContextRepository(RUNTIME_DATA_DIR)
current_context = context_repo.get(thread_id)
update_context_from_artifacts(
    thread_id=thread_id,
    run_id=f"report-export-{thread_id}",
    created_artifact_ids=[report_artifact_id],
    active_goal=current_context.active_goal if current_context else "职业发展报告",
    artifact_repo=repo,
    context_repo=context_repo,
)
```

- [ ] **Step 6: Run API tests**

Run:

```bash
cd backend && .venv/bin/python -m pytest -q tests/test_api_e2e.py::test_threads_workspace_and_messages_restore_chat_state tests/test_api_e2e.py::test_memory_confirm_and_reject_endpoints_update_status tests/test_api_e2e.py::test_memory_confirm_missing_item_returns_404 tests/test_api_e2e.py::test_report_export_updates_active_report_context tests/test_api_e2e.py::test_report_export_rejects_task_only_training_result tests/test_api_e2e.py::test_report_export_rejects_interview_summary_under_three_turns tests/test_api_e2e.py::test_complete_backend_loop_exports_isolated_markdown_reports
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/app/api/threads.py backend/app/api/reports.py backend/app/main.py backend/tests/test_api_e2e.py
git commit -m "Expose chat workspace thread APIs"
```

---

## Task 7: Memory, Compaction, And Progressive Skill Runtime Refs

**Files:**
- Modify: `backend/app/memory/compaction.py`
- Modify: `backend/app/memory/manager.py`
- Modify: `backend/app/skills/loader.py`
- Modify: `backend/app/graphs/state.py`
- Modify: `backend/app/agents/runtime.py`
- Modify: `backend/tests/test_memory_compaction.py`
- Modify: `backend/tests/test_skill_loader.py`
- Modify: `backend/tests/test_api_e2e.py`

- [ ] **Step 1: Write failing memory and skill tests**

Update `backend/tests/test_memory_compaction.py` with:

```python
def test_compact_state_uses_v31_schema_and_excludes_provider_reasoning() -> None:
    state = CareerAgentState(
        thread_id="thread-v31-compact",
        user_message="继续规划",
        artifact_ids=["profile-1", "match-1"],
        messages=[
            {"role": "user", "content": "继续规划"},
            {"role": "assistant", "content": "下一步补齐项目证据。", "reasoning_content": "private"},
        ],
        metadata={
            "run_id": "run-v31",
            "active_goal": "转向 Agent 开发工程师",
            "confirmed_facts": ["会 Python"],
            "decisions_made": ["先补 LangGraph 项目"],
            "next_actions": ["生成计划"],
            "hidden_reasoning": "private",
        },
    )

    snapshot = compact_state(state)
    dumped = snapshot.model_dump()
    dumped_text = str(dumped).lower()

    assert snapshot.source_run_id == "run-v31"
    assert snapshot.current_goal == "转向 Agent 开发工程师"
    assert snapshot.active_artifact_refs == ["profile-1", "match-1"]
    assert "hidden_reasoning" not in dumped_text
    assert "chain_of_thought" not in dumped_text
    assert "reasoning_content" not in dumped_text
```

Update `backend/tests/test_skill_loader.py` with:

```python
def test_loader_returns_bounded_runtime_refs_by_intent_and_budget() -> None:
    loaded = SkillLoader.builtin().resolve_for_agent("match", "gap_analysis", budget=1200)
    refs = [skill.runtime_ref for skill in loaded]

    assert refs[0].skill_id == "match/match_scoring_rubric"
    assert refs[0].detail_level in {"summary", "full"}
    assert len(refs[0].summary_digest) <= 240
    assert all("# " not in ref.summary_digest for ref in refs)


def test_loader_marks_skipped_when_budget_is_zero() -> None:
    loaded = SkillLoader.builtin().resolve_for_agent("match", "gap_analysis", budget=0)

    assert all(skill.runtime_ref.detail_level == "skipped" for skill in loaded)
    assert all(skill.content == "" for skill in loaded)
```

Update `backend/tests/test_api_e2e.py` with an API-level regression proving runtime refs reach `/api/runs` without leaking skill bodies:

```python
def test_runs_endpoint_returns_skill_runtime_refs_without_skill_body(tmp_path: Path, monkeypatch) -> None:
    from app.api import runs

    monkeypatch.setattr(runs, "RUNTIME_DATA_DIR", tmp_path)
    client = TestClient(app)

    response = client.post(
        "/api/runs",
        json={"thread_id": "thread-skill-ref-api", "message": "我会 Python FastAPI，想匹配 Agent 开发岗位"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["used_skill_runtime_refs"]
    first_ref = payload["used_skill_runtime_refs"][0]
    assert first_ref["skill_id"]
    assert first_ref["detail_level"] in {"summary", "full", "skipped"}
    assert "content" not in first_ref


def test_runs_endpoint_returns_public_compaction_snapshot_after_memory_manager(tmp_path: Path, monkeypatch) -> None:
    from app.api import runs

    monkeypatch.setattr(runs, "RUNTIME_DATA_DIR", tmp_path)
    client = TestClient(app)

    response = client.post(
        "/api/runs",
        json={"thread_id": "thread-compaction-api", "message": "我会 Python FastAPI，想匹配 Agent 开发岗位"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["compaction_snapshot"] is not None
    dumped = str(payload["compaction_snapshot"]).lower()
    assert "hidden_reasoning" not in dumped
    assert "reasoning_content" not in dumped
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd backend && .venv/bin/python -m pytest -q tests/test_memory_compaction.py::test_compact_state_uses_v31_schema_and_excludes_provider_reasoning tests/test_skill_loader.py::test_loader_returns_bounded_runtime_refs_by_intent_and_budget tests/test_skill_loader.py::test_loader_marks_skipped_when_budget_is_zero tests/test_api_e2e.py::test_runs_endpoint_returns_skill_runtime_refs_without_skill_body tests/test_api_e2e.py::test_runs_endpoint_returns_public_compaction_snapshot_after_memory_manager
```

Expected: FAIL because schemas and loader output do not match v3.1.

- [ ] **Step 3: Update compaction**

Modify `backend/app/memory/compaction.py`:

```python
def compact_state(state: CareerAgentState) -> CompactionSnapshot:
    return CompactionSnapshot(
        id=f"compact-{state.thread_id}",
        thread_id=state.thread_id,
        source_run_id=str(state.metadata.get("run_id") or "run-unknown"),
        current_goal=str(state.metadata.get("active_goal") or "职业发展规划"),
        confirmed_facts=_string_list(state.metadata.get("confirmed_facts")),
        decisions_made=_string_list(state.metadata.get("decisions_made")),
        active_artifact_refs=list(state.artifact_ids),
        next_actions=_string_list(state.metadata.get("next_actions")),
        dropped_context_summary=_latest_public_message(state),
    )


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]
```

Keep `_latest_public_message()` reading only public message `content`.

- [ ] **Step 4: Update skill loader and loaded schema**

Modify `LoadedSkill` in `backend/app/schemas/skills.py`:

```python
class LoadedSkill(BaseModel):
    ref: str
    summary: str
    content: str
    runtime_ref: SkillRuntimeRef
```

Modify `SkillLoader.resolve_for_agent()`:

```python
def resolve_for_agent(self, agent_id: str, intent: str, budget: int) -> list[LoadedSkill]:
    remaining_budget = budget
    loaded: list[LoadedSkill] = []
    for skill_id in self.agent_skills.get(agent_id, []):
        document = self.registry.get(skill_id)
        if remaining_budget <= 0:
            detail_level = "skipped"
            content = ""
        elif document.token_budget <= remaining_budget:
            detail_level = "full"
            content = document.body
            remaining_budget -= document.token_budget
        else:
            detail_level = "summary"
            content = document.summary
            remaining_budget = 0
        loaded.append(
            LoadedSkill(
                ref=f"{document.id}@v{document.version}",
                summary=document.summary,
                content=content,
                runtime_ref=SkillRuntimeRef(
                    skill_id=document.id,
                    version=str(document.version),
                    section_ids=_section_ids_for_intent(intent),
                    detail_level=detail_level,
                    summary_digest=document.summary[:240],
                ),
            )
        )
    return loaded


def _section_ids_for_intent(intent: str) -> list[str]:
    if intent in {"gap_analysis", "match"}:
        return ["rubric", "gaps"]
    if intent in {"submit_training", "answer_interview"}:
        return ["scoring", "feedback"]
    return ["summary"]
```

- [ ] **Step 5: Connect SkillRuntimeRef to business agent runtime**

In `CareerAgentState`, add:

```python
loaded_skill_runtime_refs: list[dict[str, Any]] = Field(default_factory=list)
```

In `backend/app/agents/runtime.py`, import `SkillLoader` and replace the static manifest-only skill selection in `run_business_agent()`:

```python
from app.skills.loader import SkillLoader
```

```python
decision = state.metadata.get("supervisor_decision", {})
intent = decision.get("intent", "default") if isinstance(decision, dict) else "default"
loaded_skills = SkillLoader.builtin().resolve_for_agent(agent_id, str(intent), budget=1200)
skill_refs = [skill.ref for skill in loaded_skills]
append_skill_runtime_refs(
    state,
    [skill.runtime_ref.model_dump(mode="json") for skill in loaded_skills],
)
```

Keep artifact payloads storing `skill_refs`, not full skill bodies. Add the helper:

```python
def append_skill_runtime_refs(state: CareerAgentState, refs: list[dict[str, Any]]) -> None:
    existing_keys = {
        (
            ref.get("skill_id"),
            ref.get("version"),
            tuple(ref.get("section_ids") or []),
            ref.get("detail_level"),
        )
        for ref in state.loaded_skill_runtime_refs
    }
    for ref in refs:
        key = (
            ref.get("skill_id"),
            ref.get("version"),
            tuple(ref.get("section_ids") or []),
            ref.get("detail_level"),
        )
        if key not in existing_keys:
            state.loaded_skill_runtime_refs.append(ref)
            existing_keys.add(key)
```

In `backend/app/services/run_orchestrator.py`, include runtime refs in the response:

```python
used_skill_runtime_refs=state.get("loaded_skill_runtime_refs", []),
```

Keep `memory_manager_node()` saving a `compaction_snapshot` artifact through `AgentRuntimeContext.save_artifact()` on every run, and ensure `update_context_from_artifacts()` receives that created artifact id so `_latest_compaction()` can return the public snapshot in `/api/runs`. The saved payload must come from `compact_state()` and must not include provider `reasoning_content`, hidden reasoning, or chain-of-thought fields.

- [ ] **Step 6: Run memory and skill tests**

Run:

```bash
cd backend && .venv/bin/python -m pytest -q tests/test_memory_compaction.py tests/test_skill_loader.py tests/test_api_e2e.py::test_runs_endpoint_returns_skill_runtime_refs_without_skill_body tests/test_api_e2e.py::test_runs_endpoint_returns_public_compaction_snapshot_after_memory_manager
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/app/memory/compaction.py backend/app/memory/manager.py backend/app/skills/loader.py backend/app/schemas/skills.py backend/app/graphs/state.py backend/app/agents/runtime.py backend/tests/test_memory_compaction.py backend/tests/test_skill_loader.py backend/tests/test_api_e2e.py
git commit -m "Bound memory compaction and skill refs"
```

---

## Task 8: Backend Regression Pass And Compatibility Fixes

**Files:**
- Modify only files required by failing tests from this task.

- [ ] **Step 1: Run full backend tests**

Run:

```bash
cd backend && .venv/bin/python -m pytest -q
```

Expected before fixes: existing tests may fail because `RunResponse` now has additional fields and compaction schema changed.

- [ ] **Step 2: Update old tests to the new response shape**

In `backend/tests/test_agent_contracts.py`, update `RunResponse(...)` construction:

```python
response = RunResponse(
    run_id="run-1",
    thread_id="thread-1",
    run_status=RunStatus.COMPLETED,
    active_agent="supervisor",
    agent_trace_summary=[
        AgentTraceItem(
            agent_id="profile",
            summary="Created a profile artifact.",
            artifact_ids=["profile-1"],
            used_skill_refs=["profile/resume_parsing"],
        )
    ],
    used_skill_refs=["profile/resume_parsing"],
    artifacts=[{"id": "profile-1", "kind": "profile"}],
    next_actions=["Review extracted profile"],
    warnings=["Low confidence on dates"],
)
```

Assert existing fields and add:

```python
assert response.run_status == RunStatus.COMPLETED
assert response.assistant_message is None
```

- [ ] **Step 3: Keep graph vertical slice assertions meaningful**

Where tests previously expected exact response keys, update them to assert required v3.1 keys are present:

```python
assert {
    "run_id",
    "thread_id",
    "run_status",
    "active_agent",
    "last_business_agent",
    "current_runtime_node",
    "assistant_message",
    "supervisor_decision",
    "workspace_delta",
    "artifact_chain",
}.issubset(payload)
```

- [ ] **Step 4: Run full backend tests again**

Run:

```bash
cd backend && .venv/bin/python -m pytest -q
```

Expected: all tests pass with only the existing FastAPI/TestClient deprecation warning.

- [ ] **Step 5: Commit**

```bash
git add backend
git commit -m "Keep backend tests aligned with v31 contracts"
```

---

## Task 9: Frontend API Types And Workbench Store

**Files:**
- Modify: `frontend/src/api/client.ts`
- Create: `frontend/src/stores/workbench.ts`
- Keep: `frontend/src/stores/demo.ts` until the new view fully replaces it.

- [ ] **Step 1: Add TypeScript contracts**

Modify `frontend/src/api/client.ts`:

```ts
export type RunStatus =
  | "completed"
  | "needs_input"
  | "blocked_by_prerequisite"
  | "provider_error"
  | "permission_denied"
  | "failed";

export interface ConversationMessage {
  id: string;
  thread_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  run_id?: string;
  created_at: string;
  artifact_refs: string[];
  last_business_agent?: string;
  current_runtime_node?: string;
  warnings?: string[];
}

export interface SupervisorDecision {
  intent: string;
  target_agent: string;
  required_input_artifact_kinds: string[];
  required_capabilities: string[];
  expected_output_artifact_kinds: string[];
  missing_prerequisites: string[];
  missing_capabilities: string[];
  user_facing_reason: string;
  next_actions: string[];
}

export interface WorkspaceContext {
  thread_id: string;
  active_goal: string;
  active_profile_id?: string;
  active_job_analysis_id?: string;
  active_match_id?: string;
  active_plan_id?: string;
  active_training_result_id?: string;
  active_interview_summary_id?: string;
  active_report_id?: string;
  active_compaction_snapshot_id?: string;
  updated_by_run_id: string;
  updated_at: string;
}

export interface ArtifactChainItem extends ArtifactRef {
  parent_artifact_ids: string[];
  updated_at?: string;
}

export interface WorkspaceResponse {
  thread_id: string;
  active_context: WorkspaceContext;
  workspace_artifacts: Record<string, Record<string, unknown>>;
  artifact_chain: ArtifactChainItem[];
}

export interface SkillRuntimeRef {
  skill_id: string;
  version: string;
  section_ids: string[];
  detail_level: "summary" | "full" | "skipped";
  summary_digest: string;
}

export interface MemoryItem {
  id: string;
  thread_id: string;
  scope: "profile" | "preference" | "goal" | "skill" | "evidence";
  fact: string;
  confidence: number;
  status: "confirmed" | "pending_confirmation" | "rejected";
  source_artifact_id?: string;
  source_message_id?: string;
}
```

Extend `RunResponse`:

```ts
export interface RunResponse {
  run_id: string;
  thread_id: string;
  run_status: RunStatus;
  active_agent: string;
  last_business_agent?: string;
  current_runtime_node?: string;
  assistant_message?: ConversationMessage;
  supervisor_decision?: SupervisorDecision;
  agent_trace_summary: AgentTraceItem[];
  used_skill_refs: string[];
  used_skill_runtime_refs: SkillRuntimeRef[];
  artifacts: ArtifactRef[];
  artifact_chain: ArtifactChainItem[];
  workspace_delta?: {
    created_artifacts: ArtifactChainItem[];
    updated_context: WorkspaceContext;
  };
  compaction_snapshot?: Record<string, unknown>;
  memory_updates: MemoryItem[];
  blocking_reason?: string;
  missing_artifacts: string[];
  retryable: boolean;
  next_actions: string[];
  warnings: string[];
}
```

Add API functions:

```ts
export async function getWorkspace(threadId: string): Promise<WorkspaceResponse> {
  const response = await fetch(`${API_BASE_URL}/api/threads/${encodeURIComponent(threadId)}/workspace`);
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return response.json() as Promise<WorkspaceResponse>;
}

export async function getMessages(threadId: string): Promise<ConversationMessage[]> {
  const response = await fetch(`${API_BASE_URL}/api/threads/${encodeURIComponent(threadId)}/messages`);
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return response.json() as Promise<ConversationMessage[]>;
}
```

- [ ] **Step 2: Create workbench store**

Create `frontend/src/stores/workbench.ts`:

```ts
import { defineStore } from "pinia";

import {
  createRun,
  downloadReport,
  getMessages,
  getWorkspace,
  type ArtifactChainItem,
  type ConversationMessage,
  type RunResponse,
  type WorkspaceResponse,
} from "../api/client";

function makeThreadId(): string {
  return `chat-${Date.now().toString(36)}`;
}

export const quickPrompts = [
  "我会 Python FastAPI，想匹配 Agent 开发岗位",
  "请分析目标岗位 JD：Agent 开发工程师，需要 LangGraph、FastAPI、RAG 和测试能力",
  "请做 match 分析",
  "生成三个月路径规划",
  "根据能力差距给我一个训练任务",
  "我的训练答案：我会设计一个简历解析 Agent，使用 FastAPI 暴露接口，用 LangGraph 编排画像抽取和评分节点。",
  "开始模拟面试",
  "回答1：我会用 StateGraph 定义节点和条件边。",
  "回答2：我会用 thread_id 和 checkpointer 保留会话状态。",
  "回答3：我会把评分结果保存为 Artifact 并进入报告。",
  "请导出 Markdown 报告",
];

export const useWorkbenchStore = defineStore("workbench", {
  state: () => ({
    threadId: makeThreadId(),
    input: "",
    isRunning: false,
    demoMode: new URLSearchParams(window.location.search).get("demo") === "1",
    error: "",
    lastRun: null as RunResponse | null,
    messages: [] as ConversationMessage[],
    workspace: null as WorkspaceResponse | null,
    artifactChain: [] as ArtifactChainItem[],
    reportMarkdown: "",
  }),

  actions: {
    async sendMessage(message?: string) {
      const content = (message ?? this.input).trim();
      if (!content) return;
      this.input = "";
      this.error = "";
      this.isRunning = true;
      try {
        const run = await createRun(this.threadId, content);
        this.lastRun = run;
        this.artifactChain = run.artifact_chain ?? [];
        await this.refreshThread();
      } catch (error) {
        this.error = error instanceof Error ? error.message : "请求失败";
      } finally {
        this.isRunning = false;
      }
    },

    async refreshThread() {
      this.messages = await getMessages(this.threadId);
      this.workspace = await getWorkspace(this.threadId);
      this.artifactChain = this.workspace.artifact_chain;
    },

    resetThread() {
      this.threadId = makeThreadId();
      this.input = "";
      this.error = "";
      this.lastRun = null;
      this.messages = [];
      this.workspace = null;
      this.artifactChain = [];
      this.reportMarkdown = "";
    },

    async exportMarkdownReport() {
      this.error = "";
      try {
        this.reportMarkdown = await downloadReport(this.threadId);
        await this.refreshThread();
      } catch (error) {
        this.error = error instanceof Error ? error.message : "报告导出失败";
      }
    },
  },
});
```

- [ ] **Step 3: Run frontend type check/build**

Run:

```bash
cd frontend && npm run build
```

Expected: PASS. Rollup may warn about chunk size and annotations; no TypeScript errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/api/client.ts frontend/src/stores/workbench.ts
git commit -m "Add chat workbench frontend contracts"
```

---

## Task 10: Chat Workbench UI Shell

**Files:**
- Create: `frontend/src/components/ConversationPanel.vue`
- Create: `frontend/src/components/WorkspaceTabs.vue`
- Create: `frontend/src/components/RuntimeDrawer.vue`
- Create: `frontend/src/views/ChatWorkbenchView.vue`
- Modify: `frontend/src/App.vue`

- [ ] **Step 1: Create conversation panel**

Create `frontend/src/components/ConversationPanel.vue`:

```vue
<script setup lang="ts">
import { Send, RotateCcw } from "@element-plus/icons-vue";
import type { ConversationMessage } from "../api/client";
import { quickPrompts } from "../stores/workbench";

defineProps<{
  messages: ConversationMessage[];
  running: boolean;
}>();

const model = defineModel<string>({ required: true });
const emit = defineEmits<{
  send: [message?: string];
  reset: [];
}>();

function submit() {
  emit("send");
}
</script>

<template>
  <aside class="conversation-panel">
    <header class="panel-head">
      <div>
        <span>CareerAgent</span>
        <h2>对话助手</h2>
      </div>
      <el-button :icon="RotateCcw" text @click="emit('reset')" />
    </header>

    <section class="quick-prompts">
      <el-button
        v-for="prompt in quickPrompts"
        :key="prompt"
        size="small"
        :disabled="running"
        @click="emit('send', prompt)"
      >
        {{ prompt }}
      </el-button>
    </section>

    <section class="messages">
      <div v-if="!messages.length" class="empty-chat">
        输入你的简历、目标岗位或下一步问题。
      </div>
      <article
        v-for="message in messages"
        :key="message.id"
        class="message"
        :class="message.role"
      >
        <span>{{ message.role === "user" ? "你" : "CareerAgent" }}</span>
        <p>{{ message.content }}</p>
      </article>
    </section>

    <footer class="composer">
      <el-input
        v-model="model"
        type="textarea"
        :autosize="{ minRows: 2, maxRows: 5 }"
        resize="none"
        placeholder="输入你的问题、简历文本或 JD..."
        @keydown.enter.exact.prevent="submit"
      />
      <el-button type="primary" :icon="Send" :loading="running" @click="submit">
        发送
      </el-button>
    </footer>
  </aside>
</template>

<style scoped>
.conversation-panel {
  display: grid;
  min-height: 100vh;
  grid-template-rows: auto auto minmax(0, 1fr) auto;
  border-left: 1px solid #d8dee8;
  background: #ffffff;
}
.panel-head,
.composer {
  padding: 16px;
}
.panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}
.panel-head span {
  color: #667085;
  font-size: 12px;
}
.panel-head h2 {
  margin: 2px 0 0;
  font-size: 20px;
}
.quick-prompts {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 0 16px 12px;
}
.quick-prompts .el-button {
  max-width: 100%;
  white-space: normal;
}
.messages {
  display: grid;
  align-content: start;
  gap: 10px;
  overflow: auto;
  padding: 16px;
}
.message {
  border-radius: 8px;
  padding: 10px 12px;
}
.message.user {
  background: #eaf2ff;
}
.message.assistant {
  background: #f3f6fb;
}
.message span {
  color: #667085;
  font-size: 12px;
}
.message p,
.empty-chat {
  margin: 4px 0 0;
  overflow-wrap: anywhere;
  line-height: 1.5;
}
.empty-chat {
  color: #667085;
}
.composer {
  display: grid;
  gap: 10px;
  border-top: 1px solid #e4e9f2;
}
</style>
```

- [ ] **Step 2: Create workspace tabs**

Create `frontend/src/components/WorkspaceTabs.vue`:

```vue
<script setup lang="ts">
import type { WorkspaceResponse } from "../api/client";

const props = defineProps<{
  workspace: WorkspaceResponse | null;
}>();

const tabs = [
  ["overview", "总览"],
  ["profile", "画像"],
  ["job_analysis", "岗位"],
  ["match", "匹配"],
  ["plan", "规划"],
  ["training_result", "训练"],
  ["interview_summary", "面试"],
  ["report", "报告"],
] as const;

function artifact(kind: string): Record<string, unknown> | undefined {
  return props.workspace?.workspace_artifacts?.[kind];
}

function content(kind: string): Record<string, unknown> {
  const payload = artifact(kind)?.payload as Record<string, unknown> | undefined;
  return (payload?.content as Record<string, unknown>) ?? payload ?? {};
}

function pretty(value: unknown): string {
  return JSON.stringify(value ?? {}, null, 2);
}
</script>

<template>
  <section class="workspace-tabs">
    <el-tabs>
      <el-tab-pane v-for="[kind, label] in tabs" :key="kind" :label="label">
        <div v-if="kind === 'overview'" class="overview-grid">
          <article class="summary-card">
            <span>当前目标</span>
            <strong>{{ workspace?.active_context.active_goal ?? "等待输入" }}</strong>
          </article>
          <article class="summary-card">
            <span>Artifact Chain</span>
            <strong>{{ workspace?.artifact_chain.length ?? 0 }} 个产物</strong>
          </article>
        </div>
        <pre v-else-if="artifact(kind)" class="artifact-json">{{ pretty(content(kind)) }}</pre>
        <el-empty v-else description="还没有该模块产物，可以在右侧对话中请求生成" :image-size="64" />
      </el-tab-pane>
    </el-tabs>
  </section>
</template>

<style scoped>
.workspace-tabs {
  min-width: 0;
  border: 1px solid #d9e0eb;
  border-radius: 8px;
  background: #ffffff;
  padding: 16px;
}
.overview-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.summary-card {
  display: grid;
  gap: 8px;
  border: 1px solid #e4e9f2;
  border-radius: 8px;
  padding: 14px;
}
.summary-card span {
  color: #667085;
  font-size: 12px;
}
.summary-card strong {
  overflow-wrap: anywhere;
}
.artifact-json {
  max-height: 420px;
  overflow: auto;
  border-radius: 8px;
  background: #f5f7fb;
  padding: 12px;
  white-space: pre-wrap;
}
</style>
```

- [ ] **Step 3: Create runtime drawer**

Create `frontend/src/components/RuntimeDrawer.vue`:

```vue
<script setup lang="ts">
import type { RunResponse, WorkspaceResponse } from "../api/client";

defineProps<{
  lastRun: RunResponse | null;
  workspace: WorkspaceResponse | null;
  demoMode: boolean;
}>();

function pretty(value: unknown): string {
  return JSON.stringify(value ?? {}, null, 2);
}
</script>

<template>
  <section class="runtime-drawer">
    <div class="runtime-head">
      <div>
        <span>Runtime</span>
        <h2>{{ demoMode ? "演示模式" : "学生模式" }}</h2>
      </div>
      <el-tag :type="lastRun?.run_status === 'completed' ? 'success' : 'info'" effect="plain">
        {{ lastRun?.run_status ?? "idle" }}
      </el-tag>
    </div>

    <div class="simple-status">
      <p>业务 Agent：{{ lastRun?.last_business_agent ?? "等待输入" }}</p>
      <p>Runtime 节点：{{ lastRun?.current_runtime_node ?? "等待运行" }}</p>
    </div>

    <template v-if="demoMode">
      <el-divider />
      <h3>Skill Runtime Refs</h3>
      <div v-if="lastRun?.used_skill_runtime_refs?.length" class="chain-list">
        <div v-for="skill in lastRun.used_skill_runtime_refs" :key="skill.skill_id" class="chain-row">
          <el-tag size="small">{{ skill.detail_level }}</el-tag>
          <span>{{ skill.skill_id }} · {{ skill.summary_digest }}</span>
        </div>
      </div>

      <h3>Artifact Chain</h3>
      <div v-if="workspace?.artifact_chain.length" class="chain-list">
        <div v-for="item in workspace.artifact_chain" :key="item.id" class="chain-row">
          <el-tag size="small">{{ item.kind }}</el-tag>
          <span>{{ item.id }} ← {{ item.parent_artifact_ids.join(", ") || "root" }}</span>
        </div>
      </div>
      <el-empty v-else description="暂无链路" :image-size="48" />

      <h3>Compaction</h3>
      <pre v-if="lastRun?.compaction_snapshot" class="runtime-json">{{ pretty(lastRun.compaction_snapshot) }}</pre>

      <h3>Memory Updates</h3>
      <div v-if="lastRun?.memory_updates?.length" class="chain-list">
        <div v-for="memory in lastRun.memory_updates" :key="memory.id" class="chain-row">
          <el-tag size="small">{{ memory.status }}</el-tag>
          <span>{{ memory.fact }}</span>
        </div>
      </div>

      <h3>Warnings</h3>
      <el-alert
        v-for="warning in lastRun?.warnings ?? []"
        :key="warning"
        :title="warning"
        type="warning"
        :closable="false"
      />
    </template>
  </section>
</template>

<style scoped>
.runtime-drawer {
  border: 1px solid #d9e0eb;
  border-radius: 8px;
  background: #ffffff;
  padding: 16px;
}
.runtime-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}
.runtime-head span,
.simple-status {
  color: #667085;
  font-size: 13px;
}
.runtime-head h2 {
  margin: 2px 0 0;
  font-size: 18px;
}
.chain-list {
  display: grid;
  gap: 8px;
}
.chain-row {
  display: grid;
  grid-template-columns: max-content minmax(0, 1fr);
  gap: 8px;
}
.chain-row span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.runtime-json {
  max-height: 160px;
  overflow: auto;
  border-radius: 8px;
  background: #f5f7fb;
  padding: 10px;
  white-space: pre-wrap;
}
</style>
```

- [ ] **Step 4: Create chat workbench view**

Create `frontend/src/views/ChatWorkbenchView.vue`:

```vue
<script setup lang="ts">
import { Download, Refresh } from "@element-plus/icons-vue";

import ConversationPanel from "../components/ConversationPanel.vue";
import RuntimeDrawer from "../components/RuntimeDrawer.vue";
import WorkspaceTabs from "../components/WorkspaceTabs.vue";
import { API_BASE_URL } from "../api/client";
import { useWorkbenchStore } from "../stores/workbench";

const workbench = useWorkbenchStore();
</script>

<template>
  <div class="chat-workbench">
    <main class="workspace">
      <header class="topbar">
        <div>
          <span>CareerAgent MVP</span>
          <h1>职业规划工作台</h1>
        </div>
        <div class="header-actions">
          <el-tag effect="plain">{{ workbench.threadId }}</el-tag>
          <el-tag effect="plain">{{ API_BASE_URL }}</el-tag>
          <el-switch v-model="workbench.demoMode" active-text="演示模式" inactive-text="学生模式" />
          <el-button :icon="Download" :disabled="workbench.isRunning" @click="workbench.exportMarkdownReport()">
            导出报告
          </el-button>
          <el-button :icon="Refresh" :disabled="workbench.isRunning" @click="workbench.resetThread()">
            新线程
          </el-button>
        </div>
      </header>

      <el-alert
        v-if="workbench.error"
        class="error-alert"
        :title="workbench.error"
        type="error"
        show-icon
        :closable="false"
      />

      <WorkspaceTabs :workspace="workbench.workspace" />
      <RuntimeDrawer
        :last-run="workbench.lastRun"
        :workspace="workbench.workspace"
        :demo-mode="workbench.demoMode"
      />
    </main>

    <ConversationPanel
      v-model="workbench.input"
      :messages="workbench.messages"
      :running="workbench.isRunning"
      @send="workbench.sendMessage"
      @reset="workbench.resetThread"
    />
  </div>
</template>

<style scoped>
.chat-workbench {
  display: grid;
  min-height: 100vh;
  grid-template-columns: minmax(0, 1fr) 420px;
  background: #eef2f7;
  color: #162033;
}
.workspace {
  display: grid;
  align-content: start;
  gap: 16px;
  min-width: 0;
  padding: 22px;
}
.topbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  border: 1px solid #d9e0eb;
  border-radius: 8px;
  background: #ffffff;
  padding: 18px 20px;
}
.topbar span {
  color: #667085;
  font-size: 12px;
}
.topbar h1 {
  margin: 3px 0 0;
  font-size: 28px;
}
.header-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}
.error-alert {
  margin: 0;
}
@media (max-width: 1100px) {
  .chat-workbench {
    grid-template-columns: 1fr;
  }
}
</style>
```

- [ ] **Step 5: Render new view**

Modify `frontend/src/App.vue`:

```vue
<script setup lang="ts">
import ChatWorkbenchView from "./views/ChatWorkbenchView.vue";
</script>

<template>
  <ChatWorkbenchView />
</template>
```

- [ ] **Step 6: Run frontend build**

Run:

```bash
cd frontend && npm run build
```

Expected: PASS. Existing Rollup annotation/chunk warnings are acceptable; TypeScript errors are not.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/ConversationPanel.vue frontend/src/components/WorkspaceTabs.vue frontend/src/components/RuntimeDrawer.vue frontend/src/views/ChatWorkbenchView.vue frontend/src/App.vue
git commit -m "Add chat workbench UI shell"
```

---

## Task 11: Browser Smoke, Docs, And Final Verification

**Files:**
- Modify: `docs/demo-script.md`
- Modify: `README.md` if the frontend description still says fixed demo only.

- [ ] **Step 1: Update demo script**

Add this v3.1 flow to `docs/demo-script.md`:

```markdown
## v3.1 Chat Workbench 演示路径

1. 打开前端工作台，确认页面直接进入职业规划工作区，而不是营销页。
2. 在右侧对话栏输入：“我会 Python FastAPI，想匹配 Agent 开发岗位。”
3. 观察中间画像 tab 出现 profile artifact，演示模式下 Runtime Drawer 显示业务 Agent 和最终 `memory_manager` 节点。
4. 继续输入自定义 JD，请求匹配、规划、训练任务、训练答案、三轮面试和报告。
5. 在只有训练任务、尚未提交训练答案时尝试开始面试，确认系统提示需要先提交训练答案并完成评分。
6. 切换到演示模式，展示 active artifact chain、parent relationships、used skills、compaction snapshot。
7. 导出 Markdown 报告，说明报告读取 active workspace context，不混用同线程其他目标岗位的历史 artifact。
```

- [ ] **Step 2: Run full backend tests**

Run:

```bash
cd backend && .venv/bin/python -m pytest -q
```

Expected: all tests pass; existing FastAPI/TestClient deprecation warning is acceptable.

- [ ] **Step 3: Run frontend build**

Run:

```bash
cd frontend && npm run build
```

Expected: build completes; existing Rollup annotation/chunk warnings are acceptable.

- [ ] **Step 4: Start local servers**

Run backend:

```bash
cd backend && .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Run frontend in another terminal:

```bash
cd frontend && npm run dev -- --host 127.0.0.1 --port 5173
```

Expected: backend listens on `http://127.0.0.1:8000`; frontend listens on `http://127.0.0.1:5173`.

- [ ] **Step 5: Browser smoke**

Use the in-app Browser to open:

```text
http://127.0.0.1:5173/?demo=1
```

Manual smoke script:

```text
1. Send: 我会 Python FastAPI，想匹配 Agent 开发岗位
2. Send: 请分析目标岗位 JD：Agent 开发工程师，需要 LangGraph、FastAPI、RAG 和测试能力
3. Send: 请做 match 分析
4. Send: 生成三个月路径规划
5. Send: 根据能力差距给我一个训练任务
6. Send: 开始模拟面试
7. Expect: 系统返回 blocked_by_prerequisite，提示先提交训练答案并完成评分，且不生成 interview_summary
8. Send: 我的训练答案：我会设计一个简历解析 Agent，使用 FastAPI 暴露接口，用 LangGraph 编排画像抽取和评分节点。
9. Send: 开始模拟面试
10. Send: 回答1：我会用 StateGraph 定义节点和条件边。
11. Send: 回答2：我会用 thread_id 和 checkpointer 保留会话状态。
12. Send: 回答3：我会把评分结果保存为 Artifact 并进入报告。
13. Click: 导出报告
```

Expected:

```text
- Conversation shows user and assistant messages after refresh.
- Workspace tabs show profile/job/match/plan/training/interview/report data.
- Runtime drawer in demo mode shows last business agent, current runtime node, artifact chain, warnings, and compaction summary.
- Runtime drawer and workspace tabs render JSON objects as formatted JSON, not `[object Object]`.
- Exported report succeeds only after training submission and three interview answers.
- Browser console has no app errors.
```

- [ ] **Step 6: Stop local servers**

If servers were started by this implementation session, stop both before final response.

- [ ] **Step 7: Commit docs**

```bash
git add docs/demo-script.md README.md
git commit -m "Document chat workbench demo flow"
```

- [ ] **Step 8: Final status**

Run:

```bash
git status --short --branch
```

Expected: only the unrelated `agent申报书date20260511.docx` remains untracked unless the user asks to handle it.

---

## Self-Review Checklist

- Spec coverage:
  - Active Workspace Context: Tasks 1, 2, 4, 5, 6, 10.
  - Active chain downstream invalidation: Task 4.
  - Supervisor active-chain prerequisite checks and completion-state capabilities: Tasks 1, 3, 4, 5, 6, 11.
  - ConversationMessage persistence: Tasks 1, 2, 5, 6, 9, 10.
  - SupervisorDecision: Tasks 1, 3, 5, 9, 10.
  - run_status: Tasks 1, 5, 8, 9, 10.
  - Permission/failure error messages: Task 5.
  - workspace/messages API: Tasks 2, 4, 5, 6.
  - Runtime student/demo modes and readable JSON rendering: Tasks 9, 10, 11.
  - Memory repository, memory updates, and confirmation: Tasks 1, 2, 5, 6, 7.
  - Compaction safety: Tasks 1, 7, 11.
  - Progressive Skill loading refs: Tasks 1, 7.
  - Training submission, three-turn interview, and report export gates: Tasks 3, 4, 5, 6, 11.
  - v2.1 gates: Tasks 3, 4, 5, 6, 8, 11.
- Placeholder scan:
  - No "TBD", "TODO", or vague "handle edge cases" steps.
  - Every task has concrete tests, implementation snippets, commands, expected results, and commit command.
- Type consistency:
  - `RunStatus`, `SupervisorDecision`, `ActiveArtifactFacts`, `WorkspaceContext`, `ConversationMessage`, `WorkspaceDelta`, `WorkspaceResponse`, `MemoryItem`, `CompactionSnapshot`, and `SkillRuntimeRef` names match across tests, backend code, and frontend types.
  - `artifact_chain` uses `ArtifactChainItem[]` everywhere.
  - `workspace_delta.updated_context` uses `WorkspaceContext`.
