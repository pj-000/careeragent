# CareerAgent MVP Implementation Plan V2

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the local CareerAgent MVP demo described in `/Users/sss/careeragent/docs/superpowers/specs/2026-05-30-careeragent-mvp-design.md`, with the external review's P0 architecture corrections applied before business UI/API feature work begins.

**Architecture:** The MVP must prove a real LangGraph strict multi-agent runtime before adding broad page coverage. FastAPI exposes student-facing APIs, but the business loop is driven by `CareerAgentState`, `AgentSpec`, real graph nodes, conditional handoff, JSON persistence, progressive Skill references, memory snapshots, and provider-neutral model requests. Vue 3 presents one strong demo loop: profile -> job -> match -> plan -> training -> interview -> Markdown report, with an Agent panel showing active agent, loaded skills, memory summary, and artifacts.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, pytest, LangGraph, httpx, Vue 3, Vite, TypeScript, Element Plus, Pinia, Vue Router, Vitest, JSON file storage.

---

## Why This V2 Exists

The first implementation plan captured the full product surface, but its task order would let the project become a regular deterministic workflow with multiple agent names. The review correctly identified the blocking risk: `run_supervisor_turn()` and late LangGraph integration cannot prove strict multi-agent behavior.

This V2 supersedes `/Users/sss/careeragent/docs/superpowers/plans/2026-05-30-careeragent-mvp-implementation.md` for implementation. The old plan remains useful as a detailed inventory of pages and schemas, but execution must follow this V2 order.

**V2.1 review patch:** A second review accepted V2 as the main plan but found that several acceptance gates were still too loose. This document now applies the V2.1 patch: LangGraph must be compiled and invoked through the real runtime with `thread_id`, AgentSpec permissions must be enforced at runtime, report generation must be thread-filtered and artifact-backed, and final E2E checks must not be the first place those constraints appear.

## Review Resolution Matrix

| Review item | V2 response |
| --- | --- |
| P0: Task 11 is not real LangGraph | LangGraph vertical slice moves to Task 6, before API and frontend. It defines `CareerAgentState`, nodes, conditional edges, checkpoint contract, `thread_id`, artifacts, and agent snapshots. |
| P0: Agent contracts are not enforced | Task 2 adds `AgentSpec`, `AgentManifest`, `AgentRuntime`, and tests that every agent declares goal, tools, memory scopes, skill policy, schemas, and handoff policy. |
| P0: Provider thinking abstraction is too thin | Task 3 adds provider-neutral `ModelRequest` / `ModelResponse`, `thinking_mode`, `reasoning_effort`, `provider_options`, and provider-specific Qwen/DeepSeek mapping. |
| P0: Memory/Skill/Compression are detached tools | Tasks 4, 5, and 6 connect Skill refs, long-term memory refs, and `CompactionSnapshot` directly to graph state. |
| P0: API/frontend before graph causes rework | API starts at Task 7, frontend starts at Task 9, both consume the graph runtime contract. |
| P1: JSON needs migration boundary | Task 1 adds domain repositories and JSON implementations with `schema_version`, atomic write, and index files. |
| P1: training/interview/report must use artifacts | Tasks 7 and 8 define `Artifact` chain and force report generation from existing artifacts. |
| P2: E2E validation missing | Task 11 adds an end-to-end API test covering the full loop and state restore from JSON. |
| V2.1 P0: LangGraph acceptance too loose | Task 6 now forbids "normal function plus marker" implementations. It requires `StateGraph`, `START`, `END`, `compile(checkpointer=...)`, and `graph.invoke(..., config={"configurable": {"thread_id": thread_id}})`. |
| V2.1 P0: AgentSpec not enforced | Task 6 adds `AgentRuntimeContext` permission checks for tools, memory scopes, and handoff targets. |
| V2.1 P0: Report can mix threads | Tasks 1 and 8 require `source_thread_id`, `source_agent`, `parent_artifact_ids`, `list_by_thread()`, required artifact-chain checks, and a two-thread report isolation test. |
| Execution gate: checkpoint restore | Task 6 adds a `graph.get_state(config)` checkpoint restore test before APIs can be built on top of the graph. |
| Execution gate: training/interview are not static | Task 8 adds a training answer submission and three interview answers before report export. |

## Non-Negotiable MVP Runtime Contract

The implementation is acceptable only if these runtime facts are true:

- All agent-triggering calls use a stable `thread_id`.
- Every graph run returns `run_id`, `thread_id`, `active_agent`, `agent_trace_summary`, `used_skill_refs`, `artifacts`, `next_actions`, and `warnings`.
- Every agent has an `AgentSpec`; direct service functions cannot be presented as agents.
- `CareerAgentState` contains current messages, active agent, artifact IDs, agent snapshots, loaded Skill refs, related long-term memory refs, and optional compaction snapshot ID.
- Skill Loader loads summaries or sections based on agent/task/budget and stores only `SkillRef` in graph state.
- Memory Manager is the only component that writes long-term memory candidates into confirmed memory.
- Context compression writes structured `CompactionSnapshot` records and never stores full hidden reasoning.
- Qwen and DeepSeek providers receive provider-specific thinking parameters only inside provider adapters.
- Markdown reports are assembled from prior artifacts, not from an unrelated one-shot summary.
- `build_graph()` must construct a real LangGraph `StateGraph` with named agent nodes, at least one conditional edge, and a checkpointer. `run_career_graph()` must invoke the compiled graph with `config={"configurable": {"thread_id": thread_id}}`.
- Runtime cannot trust AgentSpec as documentation only. `AgentRuntimeContext` must reject disallowed tool calls, memory writes, and handoff targets.
- Every persisted artifact must include `kind`, `source_thread_id`, `source_agent`, `parent_artifact_ids`, `created_at`, and `updated_at`.
- Report export must query artifacts by `thread_id` and must fail structurally if required artifact kinds are missing.
- Task 6 cannot merge until checkpoint restore is proven with `graph.get_state(config)` for the same `thread_id`.
- Task 8 cannot merge until a submitted training answer creates `training_result` and at least three interview answers create `interview_summary`.

## Planned File Structure

```text
/Users/sss/careeragent/
  README.md
  .gitignore
  Makefile
  backend/
    pyproject.toml
    app/
      main.py
      api/
        profiles.py
        jobs.py
        runs.py
        training.py
        interviews.py
        reports.py
      agents/
        base.py
        runtime.py
        manifests.py
        profile.py
        job.py
        match.py
        planning.py
        training.py
        interview.py
        report.py
        memory.py
        supervisor.py
      artifacts/
        builder.py
        markdown.py
      graphs/
        state.py
        workflow.py
        checkpoints.py
      memory/
        manager.py
        compaction.py
      providers/
        base.py
        mock.py
        qwen.py
        deepseek.py
        router.py
      repositories/
        interfaces.py
        json_repository.py
        paths.py
      schemas/
        agents.py
        artifacts.py
        common.py
        conversations.py
        jobs.py
        memory.py
        model_providers.py
        profiles.py
        reports.py
        runs.py
        skills.py
        training.py
        interviews.py
      skills/
        loader.py
        registry.py
        builtin/
          profile/resume_parsing.md
          profile/evidence_chain.md
          job/jd_analysis.md
          job/agent_developer_role.md
          match/match_scoring_rubric.md
          match/gap_diagnosis.md
          planning/career_path_planning.md
          planning/three_month_plan.md
          training/workplace_task_generation.md
          training/submission_scoring.md
          interview/mock_interview_flow.md
          interview/answer_scoring.md
          report/markdown_report.md
          memory/long_term_write_policy.md
          memory/context_compaction.md
    tests/
      test_repositories.py
      test_agent_contracts.py
      test_model_providers.py
      test_skill_loader.py
      test_memory_compaction.py
      test_graph_vertical_slice.py
      test_api_e2e.py
  frontend/
    index.html
    package.json
    vite.config.ts
    tsconfig.json
    src/
      main.ts
      App.vue
      api/client.ts
      router/index.ts
      stores/demo.ts
      types/api.ts
      views/DemoLoopView.vue
      components/AgentRuntimePanel.vue
      components/ProfileStep.vue
      components/JobStep.vue
      components/MatchStep.vue
      components/PlanStep.vue
      components/TrainingStep.vue
      components/InterviewStep.vue
      components/ReportStep.vue
    tests/demo-loop.spec.ts
  docs/
    demo-script.md
```

## Task 1: Scaffold, Storage Boundaries, And JSON Safety

**Files:**
- Create: `/Users/sss/careeragent/.gitignore`
- Create: `/Users/sss/careeragent/Makefile`
- Create: `/Users/sss/careeragent/backend/pyproject.toml`
- Create: `/Users/sss/careeragent/backend/app/main.py`
- Create: `/Users/sss/careeragent/backend/app/repositories/interfaces.py`
- Create: `/Users/sss/careeragent/backend/app/repositories/json_repository.py`
- Create: `/Users/sss/careeragent/backend/app/repositories/paths.py`
- Create: `/Users/sss/careeragent/backend/tests/test_repositories.py`

- [ ] **Step 1: Create the backend and frontend directories**

Run:

```bash
mkdir -p backend/app/{api,agents,artifacts,graphs,memory,providers,repositories,schemas,skills/builtin} backend/tests frontend/src/{api,components,router,stores,types,views} frontend/tests data/runtime
```

Expected: directories exist and `git status --short` shows new project paths.

- [ ] **Step 2: Add local-data git ignore rules**

Write `/Users/sss/careeragent/.gitignore`:

```gitignore
.DS_Store
__pycache__/
.pytest_cache/
.venv/
node_modules/
dist/
.env
.env.local
data/runtime/
*.pyc
```

- [ ] **Step 3: Add backend dependencies**

Write `/Users/sss/careeragent/backend/pyproject.toml`:

```toml
[project]
name = "careeragent-backend"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.111.0",
  "uvicorn[standard]>=0.30.0",
  "pydantic>=2.7.0",
  "httpx>=0.27.0",
  "langgraph>=0.2.0",
  "python-dotenv>=1.0.1"
]

[project.optional-dependencies]
dev = ["pytest>=8.2.0", "pytest-asyncio>=0.23.0"]

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

- [ ] **Step 4: Write repository contract tests first**

Write `/Users/sss/careeragent/backend/tests/test_repositories.py`:

```python
from pathlib import Path

from app.repositories.json_repository import JsonArtifactRepository


def test_json_repository_writes_schema_version_and_index(tmp_path: Path) -> None:
    repo = JsonArtifactRepository(tmp_path)

    saved = repo.save(
        kind="profile",
        artifact_id="profile-1",
        source_thread_id="thread-a",
        source_agent="profile",
        parent_artifact_ids=[],
        payload={"name": "林晨", "skills": ["Python", "FastAPI"]},
    )

    assert saved["schema_version"] == 1
    assert saved["id"] == "profile-1"
    assert saved["kind"] == "profile"
    assert saved["source_thread_id"] == "thread-a"
    assert saved["source_agent"] == "profile"
    assert saved["parent_artifact_ids"] == []
    assert repo.get("profile-1")["payload"]["name"] == "林晨"
    index = repo.list(kind="profile", thread_id="thread-a")
    assert index == [{"id": "profile-1", "kind": "profile", "source_thread_id": "thread-a", "source_agent": "profile"}]


def test_json_repository_filters_by_thread_and_kind(tmp_path: Path) -> None:
    repo = JsonArtifactRepository(tmp_path)
    repo.save("match", "match-a", {"score": 82}, source_thread_id="thread-a", source_agent="match")
    repo.save("match", "match-b", {"score": 61}, source_thread_id="thread-b", source_agent="match")
    repo.save("plan", "plan-a", {"title": "三个月计划"}, source_thread_id="thread-a", source_agent="planning")

    assert [item["id"] for item in repo.list_by_thread("thread-a")] == ["match-a", "plan-a"]
    assert [item["id"] for item in repo.list_by_kind("thread-a", "match")] == ["match-a"]


def test_json_repository_blocks_path_traversal(tmp_path: Path) -> None:
    repo = JsonArtifactRepository(tmp_path)

    try:
        repo.save(kind="profile", artifact_id="../bad", payload={}, source_thread_id="thread-a", source_agent="profile")
    except ValueError as exc:
        assert "Invalid artifact_id" in str(exc)
    else:
        raise AssertionError("path traversal was accepted")
```

- [ ] **Step 5: Run the failing repository tests**

Run:

```bash
cd backend && pytest tests/test_repositories.py -q
```

Expected: FAIL because `app.repositories.json_repository` does not exist.

- [ ] **Step 6: Implement JSON repository with atomic write and index**

Write `/Users/sss/careeragent/backend/app/repositories/interfaces.py`:

```python
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ArtifactRepository(ABC):
    @abstractmethod
    def save(
        self,
        kind: str,
        artifact_id: str,
        payload: dict[str, Any],
        source_thread_id: str,
        source_agent: str,
        parent_artifact_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get(self, artifact_id: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def list(self, kind: str | None = None, thread_id: str | None = None) -> list[dict[str, str]]:
        raise NotImplementedError

    @abstractmethod
    def list_by_thread(self, thread_id: str) -> list[dict[str, str]]:
        raise NotImplementedError

    @abstractmethod
    def list_by_kind(self, thread_id: str, kind: str) -> list[dict[str, str]]:
        raise NotImplementedError


class ThreadRepository(ABC):
    """Boundary for future database-backed thread state persistence."""


class MemoryRepository(ABC):
    """Boundary for future database-backed long-term memory persistence."""


class ReportRepository(ABC):
    """Boundary for future database-backed report persistence."""
```

Write `/Users/sss/careeragent/backend/app/repositories/paths.py`:

```python
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_DATA_DIR = PROJECT_ROOT / "data" / "runtime"
```

Write `/Users/sss/careeragent/backend/app/repositories/json_repository.py`:

```python
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.repositories.interfaces import ArtifactRepository


SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


class JsonArtifactRepository(ArtifactRepository):
    def __init__(self, root: Path) -> None:
        self.root = root
        self.artifact_dir = root / "artifacts"
        self.index_path = root / "artifacts-index.json"
        self.artifact_dir.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        kind: str,
        artifact_id: str,
        payload: dict[str, Any],
        source_thread_id: str,
        source_agent: str,
        parent_artifact_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        self._validate_id(artifact_id)
        now = datetime.now(timezone.utc).isoformat()
        current = self.get(artifact_id) if self._path_for(artifact_id).exists() else None
        record = {
            "schema_version": 1,
            "id": artifact_id,
            "kind": kind,
            "source_thread_id": source_thread_id,
            "source_agent": source_agent,
            "parent_artifact_ids": parent_artifact_ids or [],
            "payload": payload,
            "created_at": current["created_at"] if current else now,
            "updated_at": now,
        }
        self._atomic_write(self._path_for(artifact_id), record)
        self._write_index()
        return record

    def get(self, artifact_id: str) -> dict[str, Any]:
        self._validate_id(artifact_id)
        with self._path_for(artifact_id).open("r", encoding="utf-8") as f:
            return json.load(f)

    def list(self, kind: str | None = None, thread_id: str | None = None) -> list[dict[str, str]]:
        records = []
        for path in sorted(self.artifact_dir.glob("*.json")):
            with path.open("r", encoding="utf-8") as f:
                record = json.load(f)
            if kind is not None and record["kind"] != kind:
                continue
            if thread_id is not None and record["source_thread_id"] != thread_id:
                continue
            records.append(
                {
                    "id": record["id"],
                    "kind": record["kind"],
                    "source_thread_id": record["source_thread_id"],
                    "source_agent": record["source_agent"],
                }
            )
        return records

    def list_by_thread(self, thread_id: str) -> list[dict[str, str]]:
        return self.list(thread_id=thread_id)

    def list_by_kind(self, thread_id: str, kind: str) -> list[dict[str, str]]:
        return self.list(kind=kind, thread_id=thread_id)

    def _path_for(self, artifact_id: str) -> Path:
        return self.artifact_dir / f"{artifact_id}.json"

    def _validate_id(self, artifact_id: str) -> None:
        if not SAFE_ID.match(artifact_id):
            raise ValueError(f"Invalid artifact_id: {artifact_id}")

    def _write_index(self) -> None:
        self._atomic_write(self.index_path, self.list())

    def _atomic_write(self, path: Path, payload: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
```

- [ ] **Step 7: Add health endpoint**

Write `/Users/sss/careeragent/backend/app/main.py`:

```python
from fastapi import FastAPI


app = FastAPI(title="CareerAgent MVP")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 8: Run repository tests**

Run:

```bash
cd backend && pytest tests/test_repositories.py -q
```

Expected: PASS.

- [ ] **Step 9: Commit storage foundation**

Run:

```bash
git add .gitignore Makefile backend/pyproject.toml backend/app backend/tests/test_repositories.py
git commit -m "Add storage and backend scaffold"
```

## Task 2: AgentSpec, CareerAgentState, And Artifact Schemas

**Files:**
- Create: `/Users/sss/careeragent/backend/app/schemas/agents.py`
- Create: `/Users/sss/careeragent/backend/app/schemas/artifacts.py`
- Create: `/Users/sss/careeragent/backend/app/schemas/runs.py`
- Create: `/Users/sss/careeragent/backend/app/graphs/state.py`
- Create: `/Users/sss/careeragent/backend/app/agents/base.py`
- Create: `/Users/sss/careeragent/backend/app/agents/manifests.py`
- Create: `/Users/sss/careeragent/backend/tests/test_agent_contracts.py`

- [ ] **Step 1: Write Agent contract tests first**

Write `/Users/sss/careeragent/backend/tests/test_agent_contracts.py`:

```python
from app.agents.manifests import AGENT_MANIFESTS
from app.graphs.state import CareerAgentState


def test_every_agent_has_strict_manifest() -> None:
    required = {
        "supervisor",
        "memory_manager",
        "profile",
        "job",
        "match",
        "planning",
        "training",
        "interview",
        "report",
    }
    assert set(AGENT_MANIFESTS) == required

    for manifest in AGENT_MANIFESTS.values():
        assert manifest.agent_id
        assert manifest.goal
        assert manifest.success_criteria
        assert manifest.allowed_tools
        assert manifest.skill_policy.default_skill_ids
        assert manifest.handoff_policy.allowed_targets
        assert manifest.readable_memory_scopes is not None
        assert manifest.writable_memory_scopes is not None


def test_career_agent_state_has_runtime_fields() -> None:
    state = CareerAgentState(thread_id="thread-1", user_message="我想匹配 Agent 开发岗位")

    assert state.thread_id == "thread-1"
    assert state.messages[-1]["content"] == "我想匹配 Agent 开发岗位"
    assert state.active_agent == "supervisor"
    assert state.loaded_skill_refs == []
    assert state.related_long_term_memory_refs == []
    assert state.artifact_ids == []
```

- [ ] **Step 2: Run the failing Agent contract tests**

Run:

```bash
cd backend && pytest tests/test_agent_contracts.py -q
```

Expected: FAIL because agent schema files do not exist.

- [ ] **Step 3: Implement schemas**

Write `/Users/sss/careeragent/backend/app/schemas/agents.py`:

```python
from __future__ import annotations

from pydantic import BaseModel, Field


class SkillPolicy(BaseModel):
    default_skill_ids: list[str]
    max_skill_tokens: int = 1800
    load_strategy: str = "summary_then_sections"


class HandoffPolicy(BaseModel):
    allowed_targets: list[str]
    stop_when: list[str] = Field(default_factory=list)


class AgentManifest(BaseModel):
    agent_id: str
    goal: str
    success_criteria: list[str]
    input_schema: str
    output_schema: str
    allowed_tools: list[str]
    readable_memory_scopes: list[str]
    writable_memory_scopes: list[str]
    skill_policy: SkillPolicy
    handoff_policy: HandoffPolicy


class AgentResult(BaseModel):
    agent_id: str
    summary: str
    artifact_ids: list[str] = Field(default_factory=list)
    memory_write_candidates: list[dict] = Field(default_factory=list)
    used_skill_refs: list[str] = Field(default_factory=list)
    next_agent: str | None = None
    warnings: list[str] = Field(default_factory=list)
```

Write `/Users/sss/careeragent/backend/app/schemas/artifacts.py`:

```python
from __future__ import annotations

from typing import Any, Literal
from datetime import datetime, timezone

from pydantic import BaseModel, Field


ArtifactKind = Literal[
    "profile",
    "job_analysis",
    "match",
    "plan",
    "training_result",
    "interview_summary",
    "report",
    "compaction_snapshot",
]


class Artifact(BaseModel):
    id: str
    kind: ArtifactKind
    title: str
    payload: dict[str, Any]
    source_agent: str
    source_thread_id: str
    parent_artifact_ids: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
```

Write `/Users/sss/careeragent/backend/app/schemas/runs.py`:

```python
from __future__ import annotations

from pydantic import BaseModel, Field


class AgentTraceItem(BaseModel):
    agent_id: str
    summary: str
    used_skill_refs: list[str] = Field(default_factory=list)


class RunResponse(BaseModel):
    run_id: str
    thread_id: str
    active_agent: str
    agent_trace_summary: list[AgentTraceItem]
    used_skill_refs: list[str]
    artifacts: list[str]
    next_actions: list[str]
    warnings: list[str] = Field(default_factory=list)
```

- [ ] **Step 4: Implement graph state**

Write `/Users/sss/careeragent/backend/app/graphs/state.py`:

```python
from __future__ import annotations

from pydantic import BaseModel, Field


class AgentSnapshot(BaseModel):
    agent_id: str
    summary: str
    private_context: dict = Field(default_factory=dict)
    last_artifact_ids: list[str] = Field(default_factory=list)


class CareerAgentState(BaseModel):
    thread_id: str
    user_message: str
    profile_id: str | None = None
    job_id: str | None = None
    current_goal: str | None = None
    active_agent: str = "supervisor"
    messages: list[dict[str, str]] = Field(default_factory=list)
    agent_snapshots: dict[str, AgentSnapshot] = Field(default_factory=dict)
    loaded_skill_refs: list[str] = Field(default_factory=list)
    related_long_term_memory_refs: list[str] = Field(default_factory=list)
    artifact_ids: list[str] = Field(default_factory=list)
    pending_question: str | None = None
    compaction_snapshot_id: str | None = None
    next_agent: str | None = None
    warnings: list[str] = Field(default_factory=list)

    def model_post_init(self, __context: object) -> None:
        if not self.messages and self.user_message:
            self.messages.append({"role": "user", "content": self.user_message})
```

- [ ] **Step 5: Implement Agent base and manifests**

Write `/Users/sss/careeragent/backend/app/agents/base.py`:

```python
from __future__ import annotations

from typing import Protocol

from app.graphs.state import CareerAgentState
from app.schemas.agents import AgentManifest, AgentResult


class AgentRuntime(Protocol):
    def load_skills(self, agent_id: str, task_type: str) -> list[str]:
        ...

    def save_artifact(
        self,
        kind: str,
        artifact_id: str,
        payload: dict,
        parent_artifact_ids: list[str] | None = None,
    ) -> str:
        ...


class CareerAgent(Protocol):
    manifest: AgentManifest

    def run(self, state: CareerAgentState, runtime: AgentRuntime) -> AgentResult:
        ...
```

Write `/Users/sss/careeragent/backend/app/agents/manifests.py`:

```python
from __future__ import annotations

from app.schemas.agents import AgentManifest, HandoffPolicy, SkillPolicy


def manifest(
    agent_id: str,
    goal: str,
    skills: list[str],
    targets: list[str],
    tools: list[str],
    read_scopes: list[str],
    write_scopes: list[str],
) -> AgentManifest:
    return AgentManifest(
        agent_id=agent_id,
        goal=goal,
        success_criteria=["produces structured output", "records skill refs", "respects memory scopes"],
        input_schema="CareerAgentState",
        output_schema="AgentResult",
        allowed_tools=tools,
        readable_memory_scopes=read_scopes,
        writable_memory_scopes=write_scopes,
        skill_policy=SkillPolicy(default_skill_ids=skills),
        handoff_policy=HandoffPolicy(allowed_targets=targets),
    )


AGENT_MANIFESTS = {
    "supervisor": manifest("supervisor", "选择下一位最合适的职业发展 Agent", ["memory/context_compaction"], ["profile", "job", "match", "planning", "training", "interview", "report", "memory_manager"], ["route_intent"], ["session"], [],),
    "memory_manager": manifest("memory_manager", "维护学生职业数字孪生和压缩快照", ["memory/long_term_write_policy", "memory/context_compaction"], ["supervisor"], ["memory_read", "memory_write", "snapshot_write"], ["profile", "history", "preferences"], ["profile", "history", "preferences"],),
    "profile": manifest("profile", "从学生输入中形成职业画像和证据链", ["profile/resume_parsing", "profile/evidence_chain"], ["job", "match", "memory_manager"], ["artifact_write"], ["profile"], ["profile"],),
    "job": manifest("job", "分析目标岗位或自定义 JD 的能力画像", ["job/jd_analysis", "job/agent_developer_role"], ["match", "memory_manager"], ["artifact_write"], ["profile"], [],),
    "match": manifest("match", "计算人岗匹配、证据和差距", ["match/match_scoring_rubric", "match/gap_diagnosis"], ["planning", "training", "memory_manager"], ["artifact_write"], ["profile", "history"], [],),
    "planning": manifest("planning", "生成阶段化职业发展路径", ["planning/career_path_planning", "planning/three_month_plan"], ["training", "interview", "report", "memory_manager"], ["artifact_write"], ["profile", "history"], [],),
    "training": manifest("training", "根据能力缺口生成虚拟职场任务并评分", ["training/workplace_task_generation", "training/submission_scoring"], ["interview", "report", "memory_manager"], ["artifact_write"], ["profile", "history"], ["history"],),
    "interview": manifest("interview", "进行多轮文本模拟面试和反馈", ["interview/mock_interview_flow", "interview/answer_scoring"], ["report", "memory_manager"], ["artifact_write"], ["profile", "history"], ["history"],),
    "report": manifest("report", "基于 Artifact 链路导出 Markdown 职业发展报告", ["report/markdown_report"], ["memory_manager"], ["artifact_read", "markdown_export"], ["profile", "history"], [],),
}
```

- [ ] **Step 6: Run Agent contract tests**

Run:

```bash
cd backend && pytest tests/test_agent_contracts.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit agent contracts**

Run:

```bash
git add backend/app/schemas backend/app/graphs/state.py backend/app/agents backend/tests/test_agent_contracts.py
git commit -m "Add strict agent contracts"
```

## Task 3: Provider-Neutral Model Requests

**Files:**
- Create: `/Users/sss/careeragent/backend/app/schemas/model_providers.py`
- Create: `/Users/sss/careeragent/backend/app/providers/base.py`
- Create: `/Users/sss/careeragent/backend/app/providers/mock.py`
- Create: `/Users/sss/careeragent/backend/app/providers/qwen.py`
- Create: `/Users/sss/careeragent/backend/app/providers/deepseek.py`
- Create: `/Users/sss/careeragent/backend/app/providers/router.py`
- Create: `/Users/sss/careeragent/backend/tests/test_model_providers.py`

- [ ] **Step 1: Write provider tests first**

Write `/Users/sss/careeragent/backend/tests/test_model_providers.py`:

```python
from app.providers.deepseek import DeepSeekProvider
from app.providers.mock import MockProvider
from app.providers.qwen import QwenProvider
from app.schemas.model_providers import ModelRequest


def test_mock_provider_returns_schema_safe_response() -> None:
    provider = MockProvider()
    response = provider.generate(ModelRequest(messages=[{"role": "user", "content": "匹配岗位"}], thinking_mode="on"))

    assert response.model == "mock-careeragent"
    assert response.content
    assert response.reasoning_content is None


def test_qwen_maps_thinking_mode_to_provider_options() -> None:
    provider = QwenProvider(api_key="test", model="qwen3.6-plus")
    payload = provider.build_payload(ModelRequest(messages=[], thinking_mode="on", reasoning_effort="high"))

    assert payload["model"] == "qwen3.6-plus"
    assert payload["enable_thinking"] is True


def test_deepseek_maps_thinking_mode_to_provider_options() -> None:
    provider = DeepSeekProvider(api_key="test", model="deepseek-v4-flash")
    payload = provider.build_payload(ModelRequest(messages=[], thinking_mode="on", reasoning_effort="medium"))

    assert payload["model"] == "deepseek-v4-flash"
    assert payload["thinking"] == {"type": "enabled"}
    assert payload["reasoning_effort"] == "high"


def test_deepseek_internal_effort_option_does_not_leak_to_payload() -> None:
    provider = DeepSeekProvider(api_key="test", model="deepseek-v4-flash")
    payload = provider.build_payload(
        ModelRequest(
            messages=[],
            thinking_mode="on",
            provider_options={"deepseek_effort": "max", "temperature": 0.2},
        )
    )

    assert payload["reasoning_effort"] == "max"
    assert payload["temperature"] == 0.2
    assert "deepseek_effort" not in payload
```

- [ ] **Step 2: Run the failing provider tests**

Run:

```bash
cd backend && pytest tests/test_model_providers.py -q
```

Expected: FAIL because provider files do not exist.

- [ ] **Step 3: Implement provider DTOs and adapters**

Write `/Users/sss/careeragent/backend/app/schemas/model_providers.py`:

```python
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


ThinkingMode = Literal["off", "auto", "on"]
ReasoningEffort = Literal["low", "medium", "high", "max"]


class ModelRequest(BaseModel):
    messages: list[dict[str, str]]
    response_schema: dict[str, Any] | None = None
    thinking_mode: ThinkingMode = "auto"
    reasoning_effort: ReasoningEffort = "medium"
    tool_policy: str = "none"
    response_format: str = "json"
    provider_options: dict[str, Any] = Field(default_factory=dict)


class ModelResponse(BaseModel):
    content: str
    reasoning_content: str | None = None
    usage: dict[str, Any] = Field(default_factory=dict)
    raw: dict[str, Any] = Field(default_factory=dict)
    model: str
    finish_reason: str = "stop"
```

Write `/Users/sss/careeragent/backend/app/providers/base.py`:

```python
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.schemas.model_providers import ModelRequest, ModelResponse


class ModelProvider(ABC):
    @abstractmethod
    def generate(self, request: ModelRequest) -> ModelResponse:
        raise NotImplementedError

    @abstractmethod
    def build_payload(self, request: ModelRequest) -> dict[str, Any]:
        raise NotImplementedError
```

Write `/Users/sss/careeragent/backend/app/providers/mock.py`:

```python
from __future__ import annotations

from app.providers.base import ModelProvider
from app.schemas.model_providers import ModelRequest, ModelResponse


class MockProvider(ModelProvider):
    def build_payload(self, request: ModelRequest) -> dict:
        return request.model_dump()

    def generate(self, request: ModelRequest) -> ModelResponse:
        return ModelResponse(
            model="mock-careeragent",
            content='{"summary":"mock response","confidence":0.82}',
            raw={"provider": "mock", "thinking_mode": request.thinking_mode},
        )
```

Write `/Users/sss/careeragent/backend/app/providers/qwen.py`:

```python
from __future__ import annotations

from app.providers.base import ModelProvider
from app.schemas.model_providers import ModelRequest, ModelResponse


class QwenProvider(ModelProvider):
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def build_payload(self, request: ModelRequest) -> dict:
        payload = {
            "model": self.model,
            "messages": request.messages,
            "enable_thinking": request.thinking_mode == "on",
        }
        payload.update(request.provider_options)
        return payload

    def generate(self, request: ModelRequest) -> ModelResponse:
        payload = self.build_payload(request)
        return ModelResponse(model=self.model, content="", raw={"request_payload": payload})
```

Write `/Users/sss/careeragent/backend/app/providers/deepseek.py`:

```python
from __future__ import annotations

from app.providers.base import ModelProvider
from app.schemas.model_providers import ModelRequest, ModelResponse


class DeepSeekProvider(ModelProvider):
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def build_payload(self, request: ModelRequest) -> dict:
        options = dict(request.provider_options)
        deepseek_effort = options.pop("deepseek_effort", None)
        reasoning_effort = deepseek_effort or ("max" if request.reasoning_effort == "max" else "high")
        payload = {
            "model": self.model,
            "messages": request.messages,
            "thinking": {"type": "enabled"} if request.thinking_mode == "on" else {"type": "disabled"},
            "reasoning_effort": reasoning_effort,
        }
        payload.update(options)
        return payload

    def generate(self, request: ModelRequest) -> ModelResponse:
        payload = self.build_payload(request)
        return ModelResponse(model=self.model, content="", raw={"request_payload": payload})
```

Write `/Users/sss/careeragent/backend/app/providers/router.py`:

```python
from __future__ import annotations

from app.providers.base import ModelProvider
from app.providers.mock import MockProvider


class ModelRouter:
    def __init__(self, default_provider: ModelProvider | None = None) -> None:
        self.default_provider = default_provider or MockProvider()

    def for_agent(self, agent_id: str, task_type: str) -> ModelProvider:
        return self.default_provider
```

- [ ] **Step 4: Run provider tests**

Run:

```bash
cd backend && pytest tests/test_model_providers.py -q
```

Expected: PASS.

- [ ] **Step 5: Add env-gated provider smoke tests**

Append these tests to `/Users/sss/careeragent/backend/tests/test_model_providers.py`. They must skip when keys are absent, so local mock-mode development is not blocked:

```python
import os

import pytest


@pytest.mark.skipif(not os.getenv("QWEN_API_KEY"), reason="QWEN_API_KEY not set")
def test_qwen_provider_smoke() -> None:
    provider = QwenProvider(api_key=os.environ["QWEN_API_KEY"], model=os.getenv("QWEN_MODEL", "qwen3.6-plus"))
    response = provider.generate(ModelRequest(messages=[{"role": "user", "content": "用 JSON 返回 {\"ok\": true}"}], thinking_mode="off"))
    assert response.model
    assert response.content


@pytest.mark.skipif(not os.getenv("DEEPSEEK_API_KEY"), reason="DEEPSEEK_API_KEY not set")
def test_deepseek_provider_smoke() -> None:
    provider = DeepSeekProvider(api_key=os.environ["DEEPSEEK_API_KEY"], model=os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"))
    response = provider.generate(ModelRequest(messages=[{"role": "user", "content": "用 JSON 返回 {\"ok\": true}"}], thinking_mode="off"))
    assert response.model
    assert response.content
```

The first implementation may keep these tests skipped in mock mode, but provider code must be structured so these smoke tests can pass when keys are provided.

- [ ] **Step 6: Commit provider abstraction**

Run:

```bash
git add backend/app/schemas/model_providers.py backend/app/providers backend/tests/test_model_providers.py
git commit -m "Add provider-neutral model interface"
```

## Task 4: Progressive Skill Loading With Metadata

**Files:**
- Create: `/Users/sss/careeragent/backend/app/schemas/skills.py`
- Create: `/Users/sss/careeragent/backend/app/skills/registry.py`
- Create: `/Users/sss/careeragent/backend/app/skills/loader.py`
- Create: `/Users/sss/careeragent/backend/app/skills/builtin/**`
- Create: `/Users/sss/careeragent/backend/tests/test_skill_loader.py`

- [ ] **Step 1: Write skill loader tests first**

Write `/Users/sss/careeragent/backend/tests/test_skill_loader.py`:

```python
from pathlib import Path

from app.skills.loader import SkillLoader
from app.skills.registry import SkillRegistry


def test_skill_registry_reads_frontmatter_and_summary(tmp_path: Path) -> None:
    skill_file = tmp_path / "profile" / "resume_parsing.md"
    skill_file.parent.mkdir()
    skill_file.write_text(
        """---
id: profile/resume_parsing
version: 1
agent_scope: profile
tags: resume, evidence
summary: 从简历文本抽取技能、项目和证据链。
token_budget: 600
---
# 简历解析
## 输入
resume_text
## 输出
ProfileArtifact
""",
        encoding="utf-8",
    )

    registry = SkillRegistry(tmp_path)
    skill = registry.get("profile/resume_parsing")

    assert skill.id == "profile/resume_parsing"
    assert skill.version == 1
    assert skill.summary == "从简历文本抽取技能、项目和证据链。"


def test_loader_resolves_agent_skills_with_refs() -> None:
    loader = SkillLoader.builtin()
    loaded = loader.resolve_for_agent("match", "gap_analysis", budget=1200)

    assert loaded
    assert all(item.ref.startswith("match/") for item in loaded)
    assert all(item.summary for item in loaded)
```

- [ ] **Step 2: Run the failing skill tests**

Run:

```bash
cd backend && pytest tests/test_skill_loader.py -q
```

Expected: FAIL because skill loader files do not exist.

- [ ] **Step 3: Implement Skill schema, registry, and loader**

Write `/Users/sss/careeragent/backend/app/schemas/skills.py`:

```python
from __future__ import annotations

from pydantic import BaseModel


class SkillDocument(BaseModel):
    id: str
    version: int
    agent_scope: str
    tags: list[str]
    summary: str
    token_budget: int
    body: str


class LoadedSkill(BaseModel):
    ref: str
    summary: str
    content: str
```

Write `/Users/sss/careeragent/backend/app/skills/registry.py`:

```python
from __future__ import annotations

from pathlib import Path

from app.schemas.skills import SkillDocument


class SkillRegistry:
    def __init__(self, root: Path) -> None:
        self.root = root

    def get(self, skill_id: str) -> SkillDocument:
        path = self.root / f"{skill_id}.md"
        text = path.read_text(encoding="utf-8")
        meta, body = self._split_frontmatter(text)
        return SkillDocument(
            id=meta["id"],
            version=int(meta["version"]),
            agent_scope=meta["agent_scope"],
            tags=[item.strip() for item in meta["tags"].split(",")],
            summary=meta["summary"],
            token_budget=int(meta["token_budget"]),
            body=body.strip(),
        )

    def _split_frontmatter(self, text: str) -> tuple[dict[str, str], str]:
        if not text.startswith("---"):
            raise ValueError("Skill document missing frontmatter")
        _, raw_meta, body = text.split("---", 2)
        meta: dict[str, str] = {}
        for line in raw_meta.strip().splitlines():
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip()
        return meta, body
```

Write `/Users/sss/careeragent/backend/app/skills/loader.py`:

```python
from __future__ import annotations

from pathlib import Path

from app.schemas.skills import LoadedSkill
from app.skills.registry import SkillRegistry


BUILTIN_ROOT = Path(__file__).resolve().parent / "builtin"


AGENT_SKILLS = {
    "profile": ["profile/resume_parsing", "profile/evidence_chain"],
    "job": ["job/jd_analysis", "job/agent_developer_role"],
    "match": ["match/match_scoring_rubric", "match/gap_diagnosis"],
    "planning": ["planning/career_path_planning", "planning/three_month_plan"],
    "training": ["training/workplace_task_generation", "training/submission_scoring"],
    "interview": ["interview/mock_interview_flow", "interview/answer_scoring"],
    "report": ["report/markdown_report"],
    "memory_manager": ["memory/long_term_write_policy", "memory/context_compaction"],
}


class SkillLoader:
    def __init__(self, registry: SkillRegistry) -> None:
        self.registry = registry

    @classmethod
    def builtin(cls) -> "SkillLoader":
        return cls(SkillRegistry(BUILTIN_ROOT))

    def resolve_for_agent(self, agent_id: str, task_type: str, budget: int) -> list[LoadedSkill]:
        loaded: list[LoadedSkill] = []
        spent = 0
        for skill_id in AGENT_SKILLS.get(agent_id, []):
            doc = self.registry.get(skill_id)
            if spent + doc.token_budget > budget and loaded:
                break
            content = doc.summary if spent + doc.token_budget > budget else doc.body
            loaded.append(LoadedSkill(ref=f"{doc.id}@v{doc.version}", summary=doc.summary, content=content))
            spent += min(doc.token_budget, budget)
        return loaded
```

- [ ] **Step 4: Add built-in Skill documents**

Create each Markdown file listed in `AGENT_SKILLS`. Use this exact frontmatter pattern:

```markdown
---
id: match/gap_diagnosis
version: 1
agent_scope: match
tags: match, gap
summary: 识别人岗匹配中的能力差距并给出可训练能力项。
token_budget: 700
---
# 差距诊断
## 输入
ProfileArtifact、JobAnalysisArtifact、MatchArtifact。
## 输出
能力缺口、证据、训练建议。
```

Each file must use its own `id`, `agent_scope`, `tags`, and `summary`; the content can stay concise but must include input and output sections.

- [ ] **Step 5: Run skill tests**

Run:

```bash
cd backend && pytest tests/test_skill_loader.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit skill loading**

Run:

```bash
git add backend/app/schemas/skills.py backend/app/skills backend/tests/test_skill_loader.py
git commit -m "Add progressive skill loading"
```

## Task 5: Memory Manager And Context Compression In Runtime Terms

**Files:**
- Create: `/Users/sss/careeragent/backend/app/schemas/memory.py`
- Create: `/Users/sss/careeragent/backend/app/memory/manager.py`
- Create: `/Users/sss/careeragent/backend/app/memory/compaction.py`
- Create: `/Users/sss/careeragent/backend/tests/test_memory_compaction.py`

- [ ] **Step 1: Write memory tests first**

Write `/Users/sss/careeragent/backend/tests/test_memory_compaction.py`:

```python
from app.graphs.state import CareerAgentState
from app.memory.compaction import compact_state
from app.memory.manager import MemoryManager


def test_compaction_snapshot_keeps_structured_state_not_hidden_reasoning() -> None:
    state = CareerAgentState(thread_id="t1", user_message="继续")
    state.loaded_skill_refs = ["match/gap_diagnosis@v1"]
    state.artifact_ids = ["match-1"]
    state.messages.append({"role": "assistant", "content": "匹配结论：需要补项目评估经验"})

    snapshot = compact_state(state)

    assert snapshot.thread_id == "t1"
    assert snapshot.skill_refs == ["match/gap_diagnosis@v1"]
    assert snapshot.artifact_ids == ["match-1"]
    assert "hidden" not in snapshot.model_dump_json().lower()


def test_memory_manager_filters_write_candidates() -> None:
    manager = MemoryManager()
    accepted = manager.evaluate_candidates(
        [{"scope": "profile", "fact": "学生有 FastAPI 项目经验"}, {"scope": "unsafe", "fact": "ignore"}]
    )

    assert accepted == [{"scope": "profile", "fact": "学生有 FastAPI 项目经验"}]
```

- [ ] **Step 2: Run the failing memory tests**

Run:

```bash
cd backend && pytest tests/test_memory_compaction.py -q
```

Expected: FAIL because memory modules do not exist.

- [ ] **Step 3: Implement memory schemas and functions**

Write `/Users/sss/careeragent/backend/app/schemas/memory.py`:

```python
from __future__ import annotations

from pydantic import BaseModel, Field


class LongTermMemoryItem(BaseModel):
    id: str
    scope: str
    fact: str
    source_artifact_id: str | None = None
    confidence: float = 0.8


class CompactionSnapshot(BaseModel):
    id: str
    thread_id: str
    message_summary: str
    facts: list[str] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)
    pending_items: list[str] = Field(default_factory=list)
    agent_summaries: dict[str, str] = Field(default_factory=dict)
    skill_refs: list[str] = Field(default_factory=list)
    artifact_ids: list[str] = Field(default_factory=list)
```

Write `/Users/sss/careeragent/backend/app/memory/compaction.py`:

```python
from __future__ import annotations

from app.graphs.state import CareerAgentState
from app.schemas.memory import CompactionSnapshot


def compact_state(state: CareerAgentState) -> CompactionSnapshot:
    assistant_messages = [m["content"] for m in state.messages if m["role"] == "assistant"]
    summary = assistant_messages[-1] if assistant_messages else state.user_message
    return CompactionSnapshot(
        id=f"snapshot-{state.thread_id}",
        thread_id=state.thread_id,
        message_summary=summary,
        facts=[],
        decisions=[],
        pending_items=[state.pending_question] if state.pending_question else [],
        agent_summaries={k: v.summary for k, v in state.agent_snapshots.items()},
        skill_refs=state.loaded_skill_refs,
        artifact_ids=state.artifact_ids,
    )
```

Write `/Users/sss/careeragent/backend/app/memory/manager.py`:

```python
from __future__ import annotations


class MemoryManager:
    writable_scopes = {"profile", "history", "preferences"}

    def evaluate_candidates(self, candidates: list[dict]) -> list[dict]:
        return [item for item in candidates if item.get("scope") in self.writable_scopes and item.get("fact")]
```

- [ ] **Step 4: Run memory tests**

Run:

```bash
cd backend && pytest tests/test_memory_compaction.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit memory layer**

Run:

```bash
git add backend/app/schemas/memory.py backend/app/memory backend/tests/test_memory_compaction.py
git commit -m "Add memory and compaction contracts"
```

## Task 6: Real LangGraph Vertical Slice Before APIs

**Files:**
- Create: `/Users/sss/careeragent/backend/app/graphs/checkpoints.py`
- Create: `/Users/sss/careeragent/backend/app/graphs/workflow.py`
- Create: `/Users/sss/careeragent/backend/app/agents/runtime.py`
- Create: `/Users/sss/careeragent/backend/app/agents/supervisor.py`
- Create: `/Users/sss/careeragent/backend/app/agents/profile.py`
- Create: `/Users/sss/careeragent/backend/app/agents/job.py`
- Create: `/Users/sss/careeragent/backend/app/agents/match.py`
- Create: `/Users/sss/careeragent/backend/app/agents/planning.py`
- Create: `/Users/sss/careeragent/backend/app/agents/training.py`
- Create: `/Users/sss/careeragent/backend/app/agents/interview.py`
- Create: `/Users/sss/careeragent/backend/app/agents/report.py`
- Create: `/Users/sss/careeragent/backend/app/agents/memory.py`
- Create: `/Users/sss/careeragent/backend/tests/test_graph_vertical_slice.py`

- [ ] **Step 1: Write graph vertical slice tests first**

Write `/Users/sss/careeragent/backend/tests/test_graph_vertical_slice.py`:

```python
from pathlib import Path

import pytest

from app.agents.manifests import AGENT_MANIFESTS
from app.agents.runtime import AgentRuntimeContext, PermissionDenied
from app.graphs.workflow import build_graph, run_career_graph
from app.repositories.json_repository import JsonArtifactRepository


def test_build_graph_compiles_real_langgraph_with_required_nodes(tmp_path: Path) -> None:
    repo = JsonArtifactRepository(tmp_path)
    graph = build_graph(artifact_repo=repo)

    assert callable(getattr(graph, "invoke", None))
    graph_view = graph.get_graph()
    node_names = set(graph_view.nodes)
    for required in {"supervisor", "profile", "job", "match", "planning", "training", "interview", "report", "memory_manager"}:
        assert required in node_names
    assert "conditional" in str(graph_view.edges).lower() or "branch" in str(graph_view.edges).lower()


def test_graph_runs_real_handoff_and_persists_artifacts(tmp_path: Path) -> None:
    repo = JsonArtifactRepository(tmp_path)

    response = run_career_graph(
        thread_id="thread-graph-1",
        message="我会 Python FastAPI，想匹配 Agent 开发岗位",
        artifact_repo=repo,
    )

    assert response.thread_id == "thread-graph-1"
    assert response.active_agent in {"match", "planning", "memory_manager"}
    assert response.agent_trace_summary
    assert response.used_skill_refs
    assert response.artifacts
    assert repo.list_by_thread("thread-graph-1")


def test_graph_uses_same_thread_for_followup(tmp_path: Path) -> None:
    repo = JsonArtifactRepository(tmp_path)
    first = run_career_graph("thread-graph-2", "分析我的 Agent 开发岗位匹配", repo)
    second = run_career_graph("thread-graph-2", "继续给我训练任务", repo)

    assert first.thread_id == second.thread_id
    assert len(second.agent_trace_summary) >= 1
    assert second.artifacts
    assert repo.list_by_thread("thread-graph-2")


def test_graph_checkpoint_restores_thread_state(tmp_path: Path) -> None:
    repo = JsonArtifactRepository(tmp_path)
    graph = build_graph(artifact_repo=repo)
    config = {"configurable": {"thread_id": "thread-checkpoint-1"}}

    graph.invoke(
        {"thread_id": "thread-checkpoint-1", "user_message": "我会 FastAPI，先做岗位匹配"},
        config=config,
    )
    snapshot = graph.get_state(config)
    assert snapshot is not None
    assert snapshot.values["thread_id"] == "thread-checkpoint-1"
    assert snapshot.values["artifact_ids"]

    graph.invoke(
        {"thread_id": "thread-checkpoint-1", "user_message": "继续给我训练任务"},
        config=config,
    )
    second_snapshot = graph.get_state(config)
    assert len(second_snapshot.values["artifact_ids"]) >= len(snapshot.values["artifact_ids"])


def test_runtime_enforces_agent_manifest_permissions(tmp_path: Path) -> None:
    repo = JsonArtifactRepository(tmp_path)
    runtime = AgentRuntimeContext(thread_id="t1", manifest=AGENT_MANIFESTS["match"], artifact_repo=repo)

    with pytest.raises(PermissionDenied):
        runtime.write_memory_candidate({"scope": "profile", "fact": "Match Agent 不可直接写长期画像"})

    with pytest.raises(PermissionDenied):
        runtime.handoff_to("report")

    with pytest.raises(PermissionDenied):
        runtime.read_memory("private_notes")

    report_runtime = AgentRuntimeContext(thread_id="t1", manifest=AGENT_MANIFESTS["report"], artifact_repo=repo)
    assert report_runtime.list_artifacts(kind="match") == []
    with pytest.raises(PermissionDenied):
        report_runtime.write_memory_candidate({"scope": "profile", "fact": "Report Agent 不可写长期画像"})
```

- [ ] **Step 2: Run the failing graph tests**

Run:

```bash
cd backend && pytest tests/test_graph_vertical_slice.py -q
```

Expected: FAIL because graph workflow does not exist.

- [ ] **Step 3: Implement deterministic agent nodes behind real graph entry**

Implement each agent node as a small class with `manifest` and `run(state, runtime) -> AgentResult`. The MVP can use deterministic content, but it must update state through graph nodes and produce artifacts through `runtime.save_artifact()`.

The public workflow entry must be:

```python
def run_career_graph(thread_id: str, message: str, artifact_repo: JsonArtifactRepository) -> RunResponse:
    ...
```

The implementation must be a real LangGraph runtime, not a normal function with a marker field. `workflow.py` must import:

```python
from langgraph.graph import END, START, StateGraph
```

`build_graph()` must create named nodes for `supervisor`, every business agent, and `memory_manager`, register at least one conditional edge, and compile with a checkpointer:

```python
compiled = builder.compile(checkpointer=checkpointer)
```

`run_career_graph()` must invoke the compiled graph with thread config:

```python
compiled.invoke(
    initial_state,
    config={"configurable": {"thread_id": thread_id}},
)
```

`run_career_graph()` must not create a fresh isolated in-memory checkpointer per request. For the local MVP, use a module-level cached compiled graph/checkpointer so repeated `/api/runs` calls in the same process share LangGraph thread state. Service restart recovery can rely on the JSON Artifact chain; a JSON or SQLite checkpointer can replace the in-memory checkpointer later.

No `graph_kind == "langgraph"` marker is sufficient evidence by itself.

- [ ] **Step 4: Implement runtime permission enforcement**

Write `/Users/sss/careeragent/backend/app/agents/runtime.py`:

```python
from __future__ import annotations

from app.repositories.json_repository import JsonArtifactRepository
from app.schemas.agents import AgentManifest


class PermissionDenied(RuntimeError):
    pass


class AgentRuntimeContext:
    def __init__(self, thread_id: str, manifest: AgentManifest, artifact_repo: JsonArtifactRepository) -> None:
        self.thread_id = thread_id
        self.manifest = manifest
        self.artifact_repo = artifact_repo

    def save_artifact(self, kind: str, artifact_id: str, payload: dict, parent_artifact_ids: list[str] | None = None) -> str:
        self._require_tool("artifact_write")
        self.artifact_repo.save(
            kind=kind,
            artifact_id=artifact_id,
            payload=payload,
            source_thread_id=self.thread_id,
            source_agent=self.manifest.agent_id,
            parent_artifact_ids=parent_artifact_ids or [],
        )
        return artifact_id

    def list_artifacts(self, kind: str | None = None) -> list[dict[str, str]]:
        self._require_tool("artifact_read")
        if kind:
            return self.artifact_repo.list_by_kind(self.thread_id, kind)
        return self.artifact_repo.list_by_thread(self.thread_id)

    def read_memory(self, scope: str) -> list[dict]:
        if scope not in self.manifest.readable_memory_scopes:
            raise PermissionDenied(f"{self.manifest.agent_id} cannot read memory scope {scope}")
        return []

    def write_memory_candidate(self, candidate: dict) -> dict:
        scope = candidate.get("scope")
        if scope not in self.manifest.writable_memory_scopes:
            raise PermissionDenied(f"{self.manifest.agent_id} cannot write memory scope {scope}")
        return candidate

    def handoff_to(self, target_agent: str) -> str:
        if target_agent not in self.manifest.handoff_policy.allowed_targets:
            raise PermissionDenied(f"{self.manifest.agent_id} cannot hand off to {target_agent}")
        return target_agent

    def _require_tool(self, tool_name: str) -> None:
        if tool_name not in self.manifest.allowed_tools:
            raise PermissionDenied(f"{self.manifest.agent_id} cannot use tool {tool_name}")
```

- [ ] **Step 5: Add conditional handoff**

Supervisor routing rules:

```text
resume/profile -> profile
岗位/JD/job -> job
匹配/match -> match
计划/路径/plan -> planning
训练/task -> training
面试/interview -> interview
报告/report -> report
继续/记忆/压缩 -> memory_manager
default -> match
```

Each business agent must hand off to `memory_manager` before the run ends. `memory_manager` decides whether to compact state and returns final `RunResponse`.

The `memory_manager` node must call `compact_state()` when a module switches or before report generation, then persist the result through `AgentRuntimeContext.save_artifact(kind="compaction_snapshot", ...)`. Task 11 should only re-check this behavior; it must already exist in Task 6.

- [ ] **Step 6: Run graph tests**

Run:

```bash
cd backend && pytest tests/test_graph_vertical_slice.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit graph vertical slice**

Run:

```bash
git add backend/app/graphs backend/app/agents backend/tests/test_graph_vertical_slice.py
git commit -m "Add LangGraph vertical slice"
```

## Task 7: FastAPI APIs Backed By Graph Runs

**Files:**
- Create: `/Users/sss/careeragent/backend/app/api/runs.py`
- Create: `/Users/sss/careeragent/backend/app/api/profiles.py`
- Create: `/Users/sss/careeragent/backend/app/api/jobs.py`
- Modify: `/Users/sss/careeragent/backend/app/main.py`
- Create: `/Users/sss/careeragent/backend/tests/test_api_e2e.py`

- [ ] **Step 1: Write initial API test**

Write `/Users/sss/careeragent/backend/tests/test_api_e2e.py`:

```python
from fastapi.testclient import TestClient

from app.main import app
from app.repositories.json_repository import JsonArtifactRepository
from app.repositories.paths import RUNTIME_DATA_DIR


client = TestClient(app)


def test_run_endpoint_returns_agent_runtime_fields() -> None:
    response = client.post(
        "/api/runs",
        json={"thread_id": "api-thread-1", "message": "我会 Python FastAPI，匹配 Agent 开发岗位"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["thread_id"] == "api-thread-1"
    assert body["active_agent"]
    assert body["agent_trace_summary"]
    assert body["used_skill_refs"]
    assert body["artifacts"]


def test_run_endpoint_rejects_unsafe_thread_id() -> None:
    response = client.post(
        "/api/runs",
        json={"thread_id": "../bad", "message": "hello"},
    )

    assert response.status_code == 422
```

- [ ] **Step 2: Implement `/api/runs` as graph entry**

Write `/Users/sss/careeragent/backend/app/api/runs.py`:

```python
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, constr

from app.graphs.workflow import run_career_graph
from app.repositories.json_repository import JsonArtifactRepository
from app.repositories.paths import RUNTIME_DATA_DIR
from app.schemas.runs import RunResponse


router = APIRouter(prefix="/api/runs", tags=["runs"])


class RunRequest(BaseModel):
    thread_id: constr(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
    message: str


@router.post("", response_model=RunResponse)
def create_run(request: RunRequest) -> RunResponse:
    repo = JsonArtifactRepository(RUNTIME_DATA_DIR)
    return run_career_graph(request.thread_id, request.message, repo)
```

Modify `/Users/sss/careeragent/backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.runs import router as runs_router


app = FastAPI(title="CareerAgent MVP")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(runs_router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 3: Run API test**

Run:

```bash
cd backend && pytest tests/test_api_e2e.py -q
```

Expected: PASS.

- [ ] **Step 4: Add profile and job convenience endpoints**

Add `/api/profiles/demo`, `/api/jobs/demo`, and `/api/jobs/custom` as thin wrappers that create artifacts and return IDs. These endpoints must not bypass the graph for agent-triggering behavior; they only seed user inputs.

- [ ] **Step 5: Commit graph-backed API**

Run:

```bash
git add backend/app/api backend/app/main.py backend/tests/test_api_e2e.py
git commit -m "Add graph-backed API entrypoints"
```

## Task 8: Training, Interview, And Report Artifacts

**Files:**
- Create: `/Users/sss/careeragent/backend/app/api/training.py`
- Create: `/Users/sss/careeragent/backend/app/api/interviews.py`
- Create: `/Users/sss/careeragent/backend/app/api/reports.py`
- Create: `/Users/sss/careeragent/backend/app/artifacts/markdown.py`
- Modify: `/Users/sss/careeragent/backend/tests/test_api_e2e.py`

- [ ] **Step 1: Extend E2E test for the full backend loop**

Append to `/Users/sss/careeragent/backend/tests/test_api_e2e.py`:

```python
def complete_demo_messages(marker: str | None = None) -> list[str]:
    prefix = "我会 Python FastAPI，想匹配 Agent 开发岗位"
    if marker:
        prefix = f"{prefix}，唯一标记 {marker}"
    return [
        prefix,
        "生成三个月路径规划",
        "根据能力差距给我一个训练任务",
        "我的训练答案：我会设计一个简历解析 Agent，使用 FastAPI 暴露接口，用 LangGraph 编排画像抽取和评分节点。",
        "开始模拟面试",
        "回答1：我会用 StateGraph 定义节点和条件边。",
        "回答2：我会用 thread_id 和 checkpointer 保留会话状态。",
        "回答3：我会把评分结果保存为 Artifact 并进入报告。",
        "请导出 Markdown 报告",
    ]


def test_backend_loop_creates_report_from_artifacts() -> None:
    thread_id = "api-thread-loop"
    for message in complete_demo_messages():
        response = client.post("/api/runs", json={"thread_id": thread_id, "message": message})
        assert response.status_code == 200

    report = client.get(f"/api/reports/{thread_id}/markdown")
    assert report.status_code == 200
    assert "# CareerAgent 职业发展报告" in report.text
    assert "能力差距" in report.text


def test_report_is_thread_isolated() -> None:
    thread_a = "api-thread-a"
    thread_b = "api-thread-b"
    for thread_id, marker in [(thread_a, "A-ONLY"), (thread_b, "B-ONLY")]:
        for message in complete_demo_messages(marker):
            response = client.post("/api/runs", json={"thread_id": thread_id, "message": message})
            assert response.status_code == 200

    report_a = client.get(f"/api/reports/{thread_a}/markdown")

    assert report_a.status_code == 200
    assert "A-ONLY" in report_a.text
    assert "B-ONLY" not in report_a.text

    repo = JsonArtifactRepository(RUNTIME_DATA_DIR)
    report_artifact = repo.get(f"report-{thread_a}-latest")
    for parent_id in report_artifact["parent_artifact_ids"]:
        assert repo.get(parent_id)["source_thread_id"] == thread_a


def test_training_submission_and_three_turn_interview_are_artifact_backed() -> None:
    thread_id = "api-thread-training-interview"
    for message in complete_demo_messages():
        response = client.post("/api/runs", json={"thread_id": thread_id, "message": message})
        assert response.status_code == 200

    repo = JsonArtifactRepository(RUNTIME_DATA_DIR)
    assert repo.list_by_kind(thread_id, "training_result")
    assert repo.list_by_kind(thread_id, "interview_summary")
```

- [ ] **Step 2: Implement Markdown report builder**

Write `/Users/sss/careeragent/backend/app/artifacts/markdown.py`:

```python
from __future__ import annotations


class MissingArtifactError(ValueError):
    pass


def build_markdown_report(thread_id: str, artifacts: list[dict]) -> str:
    def latest_by_kind(kind: str) -> dict:
        candidates = [artifact for artifact in artifacts if artifact["kind"] == kind]
        if not candidates:
            raise MissingArtifactError(f"Missing required artifact for {thread_id}: {kind}")
        return sorted(candidates, key=lambda artifact: artifact["updated_at"])[-1]

    profile = latest_by_kind("profile")["payload"]
    job = latest_by_kind("job_analysis")["payload"]
    match = latest_by_kind("match")["payload"]
    plan = latest_by_kind("plan")["payload"]
    training = latest_by_kind("training_result")["payload"]
    interview = latest_by_kind("interview_summary")["payload"]

    sections = [
        "# CareerAgent 职业发展报告",
        f"- Thread ID: `{thread_id}`",
        "## 学生画像摘要",
        profile.get("summary", "画像摘要缺失"),
        "## 目标岗位",
        job.get("title", "目标岗位缺失"),
        "## 匹配结论",
        match.get("summary", "匹配结论缺失"),
        "## 能力差距",
        "\n".join(f"- {gap}" for gap in match.get("gaps", [])),
        "## 三阶段路径",
        plan.get("summary", "路径规划缺失"),
        "## 训练表现",
        training.get("feedback", "训练反馈缺失"),
        "## 面试反馈",
        interview.get("summary", "面试反馈缺失"),
        "## 下一步行动",
        "继续完成一个可展示的 Agent 项目并积累证据。",
    ]
    return "\n\n".join(sections) + "\n"
```

- [ ] **Step 3: Implement report endpoint**

Write `/Users/sss/careeragent/backend/app/api/reports.py`:

```python
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Path, Response

from app.artifacts.markdown import MissingArtifactError, build_markdown_report
from app.repositories.json_repository import JsonArtifactRepository
from app.repositories.paths import RUNTIME_DATA_DIR


router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/{thread_id}/markdown")
def get_markdown_report(thread_id: str = Path(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")) -> Response:
    repo = JsonArtifactRepository(RUNTIME_DATA_DIR)
    required_kinds = {"profile", "job_analysis", "match", "plan", "training_result", "interview_summary"}
    artifacts = [
        repo.get(item["id"])
        for item in repo.list_by_thread(thread_id)
        if item["kind"] in required_kinds
    ]
    if not repo.list_by_kind(thread_id, "compaction_snapshot"):
        repo.save(
            kind="compaction_snapshot",
            artifact_id=f"snapshot-{thread_id}-report",
            payload={"message_summary": "报告导出前的结构化上下文快照"},
            source_thread_id=thread_id,
            source_agent="memory_manager",
            parent_artifact_ids=[artifact["id"] for artifact in artifacts],
        )
    try:
        markdown = build_markdown_report(thread_id, artifacts)
    except MissingArtifactError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    repo.save(
        kind="report",
        artifact_id=f"report-{thread_id}-latest",
        payload={"markdown": markdown},
        source_thread_id=thread_id,
        source_agent="report",
        parent_artifact_ids=[artifact["id"] for artifact in artifacts],
    )
    return Response(markdown, media_type="text/markdown; charset=utf-8")
```

Include `reports_router` in `main.py`.

- [ ] **Step 4: Run full backend tests**

Run:

```bash
cd backend && pytest -q
```

Expected: PASS.

- [ ] **Step 5: Commit training/interview/report artifact loop**

Run:

```bash
git add backend/app/api backend/app/artifacts backend/tests/test_api_e2e.py
git commit -m "Add report artifact loop"
```

## Task 9: Vue 3 Demo Loop UI

**Files:**
- Create: `/Users/sss/careeragent/frontend/package.json`
- Create: `/Users/sss/careeragent/frontend/index.html`
- Create: `/Users/sss/careeragent/frontend/vite.config.ts`
- Create: `/Users/sss/careeragent/frontend/src/main.ts`
- Create: `/Users/sss/careeragent/frontend/src/App.vue`
- Create: `/Users/sss/careeragent/frontend/src/api/client.ts`
- Create: `/Users/sss/careeragent/frontend/src/stores/demo.ts`
- Create: `/Users/sss/careeragent/frontend/src/views/DemoLoopView.vue`
- Create: `/Users/sss/careeragent/frontend/src/components/AgentRuntimePanel.vue`

- [ ] **Step 1: Create frontend dependencies**

Write `/Users/sss/careeragent/frontend/package.json`:

```json
{
  "scripts": {
    "dev": "vite --host 127.0.0.1",
    "build": "vue-tsc --noEmit && vite build",
    "test": "vitest run"
  },
  "dependencies": {
    "@vitejs/plugin-vue": "^5.0.0",
    "element-plus": "^2.7.0",
    "pinia": "^2.1.7",
    "vue": "^3.4.0",
    "vue-router": "^4.3.0"
  },
  "devDependencies": {
    "typescript": "^5.4.0",
    "vite": "^5.2.0",
    "vitest": "^1.6.0",
    "vue-tsc": "^2.0.0"
  }
}
```

- [ ] **Step 2: Implement API client and store**

`client.ts` must expose `createRun(threadId, message)` and `downloadReport(threadId)`. The store must keep `threadId`, `lastRun`, `artifactIds`, `usedSkillRefs`, and `currentStep`.

- [ ] **Step 3: Implement one-page Chinese demo loop**

`DemoLoopView.vue` must show:

- 学生画像输入或样例选择。
- 目标岗位/JD。
- 匹配结果。
- 路径规划。
- 任务训练。
- 模拟面试。
- Markdown 报告导出。
- Right-side `AgentRuntimePanel` with active agent, used skills, artifact IDs, and warnings.

- [ ] **Step 4: Run frontend build**

Run:

```bash
cd frontend && npm install && npm run build
```

Expected: build succeeds.

- [ ] **Step 5: Commit frontend loop**

Run:

```bash
git add frontend
git commit -m "Add Vue demo loop"
```

## Task 10: Local Demo Script And Privacy Boundaries

**Files:**
- Modify: `/Users/sss/careeragent/README.md`
- Create: `/Users/sss/careeragent/docs/demo-script.md`
- Create: `/Users/sss/careeragent/.env.example`

- [ ] **Step 1: Document local environment**

README must include:

````markdown
# CareerAgent

CareerAgent MVP is a local-first student career development multi-agent demo.

## Run Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

## Run Frontend

```bash
cd frontend
npm install
npm run dev
```

## Local Data

Runtime student data is stored under `data/runtime/` and is ignored by git.
````

- [ ] **Step 2: Add demo script**

`docs/demo-script.md` must include a 5-minute flow:

```markdown
# CareerAgent 5 分钟演示脚本

1. 打开前端，选择样例学生或粘贴简历。
2. 输入目标岗位：Agent 开发工程师。
3. 点击匹配，展示 Match Agent、Skill refs 和 Artifact。
4. 点击路径规划，展示 Planning Agent 接手。
5. 触发训练任务并提交一段回答。
6. 进行三轮文本模拟面试。
7. 导出 Markdown 报告。
8. 重启后端，再次打开同一 thread_id，确认 JSON 状态可恢复。
```

- [ ] **Step 3: Add `.env.example`**

Write:

```dotenv
QWEN_API_KEY=
DASHSCOPE_API_KEY=
QWEN_BASE_URL=
QWEN_MODEL=qwen3.6-plus
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=
DEEPSEEK_MODEL=deepseek-v4-flash
CAREERAGENT_MODEL_MODE=mock
CAREERAGENT_DATA_DIR=data/runtime
```

- [ ] **Step 4: Commit docs**

Run:

```bash
git add README.md docs/demo-script.md .env.example
git commit -m "Document local demo workflow"
```

## Task 11: End-To-End Verification Gate

**Files:**
- Modify: `/Users/sss/careeragent/backend/tests/test_api_e2e.py`
- Modify: `/Users/sss/careeragent/frontend/tests/demo-loop.spec.ts`

- [ ] **Step 1: Backend E2E must cover the full artifact chain**

The final backend E2E test must prove:

- `thread_id` remains stable across the flow.
- Profile, job analysis, match, plan, training result, interview summary, and report artifacts are persisted.
- `used_skill_refs` is non-empty.
- A `compaction_snapshot` artifact is created after explicit compression or report generation.
- Recreating the repository object from the same `data/runtime` path can read the artifacts.
- Two different `thread_id` values do not leak artifacts into each other's Markdown reports.
- `build_graph()` returns a compiled LangGraph object with `invoke()` and graph introspection; a marker string is not acceptable evidence.
- Runtime permission tests prove unauthorized memory writes and handoffs raise `PermissionDenied`.
- Training includes at least one submitted student answer and a scored `training_result` artifact.
- Interview includes at least three turns and an `interview_summary` artifact.

- [ ] **Step 2: Frontend build must pass**

Run:

```bash
cd frontend && npm run build
```

Expected: PASS.

- [ ] **Step 3: Backend tests must pass**

Run:

```bash
cd backend && pytest -q
```

Expected: PASS.

- [ ] **Step 4: Run local servers and verify in browser**

Run backend:

```bash
cd backend && uvicorn app.main:app --reload --port 8000
```

Run frontend:

```bash
cd frontend && npm run dev
```

Open the Vite URL in the in-app Browser. Verify the page is Chinese, the right Agent panel updates after each step, and Markdown report download returns text.

- [ ] **Step 5: Commit verification fixes**

Run:

```bash
git status --short
git add backend frontend README.md docs .env.example .gitignore Makefile
git commit -m "Complete CareerAgent MVP verification"
```

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-31-careeragent-mvp-implementation-v2.md`.

Two execution options:

1. **Subagent-Driven (recommended)** - dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** - execute tasks in this session using `superpowers:executing-plans`, with checkpoints for review.

Recommendation: choose **Subagent-Driven** because this MVP has independent backend contracts, graph runtime, frontend, and verification tracks.

## Start-Coding Confirmation Prompt

Use this exact prompt when ready to start implementation:

```text
确认采用 v2 实施计划，选择 1：Subagent-Driven 执行，开始编码。先实现 Task 1-6 的架构骨架和 LangGraph 纵向切片，通过测试后再做 API 和前端。
```
