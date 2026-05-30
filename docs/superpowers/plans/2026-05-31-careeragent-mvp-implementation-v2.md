# CareerAgent MVP Implementation Plan V2

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the local CareerAgent MVP demo described in `/Users/sss/careeragent/docs/superpowers/specs/2026-05-30-careeragent-mvp-design.md`, with the external review's P0 architecture corrections applied before business UI/API feature work begins.

**Architecture:** The MVP must prove a real LangGraph strict multi-agent runtime before adding broad page coverage. FastAPI exposes student-facing APIs, but the business loop is driven by `CareerAgentState`, `AgentSpec`, real graph nodes, conditional handoff, JSON persistence, progressive Skill references, memory snapshots, and provider-neutral model requests. Vue 3 presents one strong demo loop: profile -> job -> match -> plan -> training -> interview -> Markdown report, with an Agent panel showing active agent, loaded skills, memory summary, and artifacts.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, pytest, LangGraph, httpx, Vue 3, Vite, TypeScript, Element Plus, Pinia, Vue Router, Vitest, JSON file storage.

---

## Why This V2 Exists

The first implementation plan captured the full product surface, but its task order would let the project become a regular deterministic workflow with multiple agent names. The review correctly identified the blocking risk: `run_supervisor_turn()` and late LangGraph integration cannot prove strict multi-agent behavior.

This V2 supersedes `/Users/sss/careeragent/docs/superpowers/plans/2026-05-30-careeragent-mvp-implementation.md` for implementation. The old plan remains useful as a detailed inventory of pages and schemas, but execution must follow this V2 order.

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
        payload={"name": "林晨", "skills": ["Python", "FastAPI"]},
    )

    assert saved["schema_version"] == 1
    assert saved["id"] == "profile-1"
    assert saved["kind"] == "profile"
    assert repo.get("profile-1")["payload"]["name"] == "林晨"
    index = repo.list(kind="profile")
    assert index == [{"id": "profile-1", "kind": "profile"}]


def test_json_repository_blocks_path_traversal(tmp_path: Path) -> None:
    repo = JsonArtifactRepository(tmp_path)

    try:
        repo.save(kind="profile", artifact_id="../bad", payload={})
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
    def save(self, kind: str, artifact_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get(self, artifact_id: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def list(self, kind: str | None = None) -> list[dict[str, str]]:
        raise NotImplementedError
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

    def save(self, kind: str, artifact_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self._validate_id(artifact_id)
        now = datetime.now(timezone.utc).isoformat()
        current = self.get(artifact_id) if self._path_for(artifact_id).exists() else None
        record = {
            "schema_version": 1,
            "id": artifact_id,
            "kind": kind,
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

    def list(self, kind: str | None = None) -> list[dict[str, str]]:
        records = []
        for path in sorted(self.artifact_dir.glob("*.json")):
            with path.open("r", encoding="utf-8") as f:
                record = json.load(f)
            if kind is None or record["kind"] == kind:
                records.append({"id": record["id"], "kind": record["kind"]})
        return records

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

    def save_artifact(self, kind: str, payload: dict, source_agent: str, parents: list[str]) -> str:
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
    assert payload["reasoning_effort"] == "medium"
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
ReasoningEffort = Literal["low", "medium", "high"]


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
        payload = {
            "model": self.model,
            "messages": request.messages,
            "thinking": {"type": "enabled"} if request.thinking_mode == "on" else {"type": "disabled"},
            "reasoning_effort": request.reasoning_effort,
        }
        payload.update(request.provider_options)
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

- [ ] **Step 5: Commit provider abstraction**

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

from app.graphs.workflow import run_career_graph
from app.repositories.json_repository import JsonArtifactRepository


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
    assert repo.list()


def test_graph_uses_same_thread_for_followup(tmp_path: Path) -> None:
    repo = JsonArtifactRepository(tmp_path)
    first = run_career_graph("thread-graph-2", "分析我的 Agent 开发岗位匹配", repo)
    second = run_career_graph("thread-graph-2", "继续给我训练任务", repo)

    assert first.thread_id == second.thread_id
    assert len(second.agent_trace_summary) >= 1
    assert second.artifacts
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

The implementation must compile a `StateGraph` when LangGraph is available. If local LangGraph API shape differs, wrap the graph creation in `build_graph()` and keep tests focused on the public contract plus a `graph_kind == "langgraph"` marker returned from runtime diagnostics.

- [ ] **Step 4: Add conditional handoff**

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

- [ ] **Step 5: Run graph tests**

Run:

```bash
cd backend && pytest tests/test_graph_vertical_slice.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit graph vertical slice**

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
```

- [ ] **Step 2: Implement `/api/runs` as graph entry**

Write `/Users/sss/careeragent/backend/app/api/runs.py`:

```python
from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter

from app.graphs.workflow import run_career_graph
from app.repositories.json_repository import JsonArtifactRepository
from app.repositories.paths import RUNTIME_DATA_DIR
from app.schemas.runs import RunResponse


router = APIRouter(prefix="/api/runs", tags=["runs"])


class RunRequest(BaseModel):
    thread_id: str
    message: str


@router.post("", response_model=RunResponse)
def create_run(request: RunRequest) -> RunResponse:
    repo = JsonArtifactRepository(RUNTIME_DATA_DIR)
    return run_career_graph(request.thread_id, request.message, repo)
```

Modify `/Users/sss/careeragent/backend/app/main.py`:

```python
from fastapi import FastAPI

from app.api.runs import router as runs_router


app = FastAPI(title="CareerAgent MVP")
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
def test_backend_loop_creates_report_from_artifacts() -> None:
    thread_id = "api-thread-loop"
    for message in [
        "我会 Python FastAPI，想匹配 Agent 开发岗位",
        "生成三个月路径规划",
        "根据能力差距给我一个训练任务",
        "开始模拟面试",
        "请导出 Markdown 报告",
    ]:
        response = client.post("/api/runs", json={"thread_id": thread_id, "message": message})
        assert response.status_code == 200

    report = client.get(f"/api/reports/{thread_id}/markdown")
    assert report.status_code == 200
    assert "# CareerAgent 职业发展报告" in report.text
    assert "能力差距" in report.text
```

- [ ] **Step 2: Implement Markdown report builder**

Write `/Users/sss/careeragent/backend/app/artifacts/markdown.py`:

```python
from __future__ import annotations


def build_markdown_report(thread_id: str, artifacts: list[dict]) -> str:
    sections = [
        "# CareerAgent 职业发展报告",
        f"- Thread ID: `{thread_id}`",
        "## 学生画像摘要",
        "基于当前本地演示数据生成。",
        "## 目标岗位",
        "Agent 开发工程师或学生自定义 JD。",
        "## 匹配结论",
        "系统根据 Profile、JobAnalysis 和 Match Artifact 汇总。",
        "## 能力差距",
        "重点关注 LangGraph、LLM API、测试评估和项目证据链。",
        "## 三阶段路径",
        "基础补齐、项目训练、面试表达。",
        "## 训练表现",
        "引用 TrainingResult Artifact。",
        "## 面试反馈",
        "引用 InterviewSummary Artifact。",
        "## 下一步行动",
        "继续完成一个可展示的 Agent 项目并积累证据。",
    ]
    return "\n\n".join(sections) + "\n"
```

- [ ] **Step 3: Implement report endpoint**

Write `/Users/sss/careeragent/backend/app/api/reports.py`:

```python
from __future__ import annotations

from fastapi import APIRouter, Response

from app.artifacts.markdown import build_markdown_report
from app.repositories.json_repository import JsonArtifactRepository
from app.repositories.paths import RUNTIME_DATA_DIR


router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/{thread_id}/markdown")
def get_markdown_report(thread_id: str) -> Response:
    repo = JsonArtifactRepository(RUNTIME_DATA_DIR)
    artifacts = [repo.get(item["id"]) for item in repo.list()]
    markdown = build_markdown_report(thread_id, artifacts)
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
DEEPSEEK_API_KEY=
CAREERAGENT_MODEL_MODE=mock
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
