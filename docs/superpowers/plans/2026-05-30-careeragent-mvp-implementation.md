# CareerAgent MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Superseded for implementation:** This 2026-05-30 plan is kept for history and detailed inventory. External review found that its LangGraph integration came too late and was too shallow to prove strict multi-agent behavior. Use `/Users/sss/careeragent/docs/superpowers/plans/2026-05-31-careeragent-mvp-implementation-v2.md` for implementation.

**Goal:** Build the local CareerAgent MVP demo described in `/Users/sss/careeragent/docs/superpowers/specs/2026-05-30-careeragent-mvp-design.md`.

**Architecture:** The MVP is a local-first FastAPI + Vue application. FastAPI owns JSON persistence, schemas, model providers, progressive Skill loading, memory, and LangGraph multi-agent orchestration. Vue owns the student workflow: profile, job match, plan, training, interview, scenario chat, and Markdown report export.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, pytest, LangGraph, httpx, Vue 3, Vite, TypeScript, Element Plus, Pinia, Vue Router, Vitest, JSON file storage.

---

## Scope Check

The spec spans backend, frontend, data, agents, memory, and model integration. This plan keeps it as one master MVP plan because the deliverable is a single vertical demo loop and the subsystems are tightly connected by shared schemas and API contracts. Execution should still use one subagent per task or small task group when implementation begins.

## Planned File Structure

```text
/Users/sss/careeragent/
  README.md
  .gitignore
  Makefile
  backend/
    pyproject.toml
    app/
      __init__.py
      main.py
      api/
        __init__.py
        profiles.py
        jobs.py
        matches.py
        plans.py
        training.py
        interviews.py
        conversations.py
        reports.py
      schemas/
        __init__.py
        common.py
        profiles.py
        jobs.py
        matches.py
        plans.py
        training.py
        interviews.py
        conversations.py
        reports.py
        memory.py
        skills.py
      repositories/
        __init__.py
        json_repository.py
        paths.py
      skills/
        __init__.py
        registry.py
        loader.py
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
      providers/
        __init__.py
        base.py
        mock.py
        qwen.py
        deepseek.py
        router.py
      memory/
        __init__.py
        manager.py
        compaction.py
      agents/
        __init__.py
        contracts.py
        supervisor.py
        profile.py
        job.py
        match.py
        planning.py
        training.py
        interview.py
        report.py
      graphs/
        __init__.py
        workflow.py
      services/
        __init__.py
        ids.py
        resume_parser.py
        report_builder.py
    tests/
      conftest.py
      test_json_repository.py
      test_skills.py
      test_model_router.py
      test_memory.py
      test_agents.py
      test_api_flow.py
  frontend/
    package.json
    index.html
    tsconfig.json
    vite.config.ts
    src/
      main.ts
      App.vue
      router.ts
      api/client.ts
      stores/profile.ts
      stores/job.ts
      stores/conversation.ts
      stores/report.ts
      views/DashboardView.vue
      views/ProfileView.vue
      views/JobMatchView.vue
      views/PlanView.vue
      views/TrainingView.vue
      views/InterviewView.vue
      views/ReportView.vue
      components/AppShell.vue
      components/AgentChatPanel.vue
      components/ResumeUploader.vue
      components/ProfileEditor.vue
      components/SkillEvidenceList.vue
      components/JobSelector.vue
      components/CustomJobForm.vue
      components/MatchRadar.vue
      components/GapAnalysisCard.vue
      components/PlanTimeline.vue
      components/TrainingTaskCard.vue
      components/InterviewThread.vue
      components/MarkdownReport.vue
      types/api.ts
    tests/
      profile.spec.ts
      job-match.spec.ts
      training.spec.ts
      interview.spec.ts
  data/
    demo/
      students.json
      jobs.json
      training_tasks.json
    runtime/.gitkeep
```

## API Contract Summary

The frontend talks only to FastAPI business endpoints:

```text
POST   /api/profiles/parse-resume
GET    /api/profiles/{profile_id}
PATCH  /api/profiles/{profile_id}
POST   /api/jobs/analyze
POST   /api/matches
POST   /api/plans
POST   /api/training/tasks
POST   /api/training/submissions
POST   /api/interviews/sessions
POST   /api/interviews/{session_id}/messages
POST   /api/conversations/{scope}/messages
POST   /api/reports
GET    /api/reports/{report_id}/markdown
```

## Task 1: Project Scaffold And Tooling

**Files:**
- Create: `/Users/sss/careeragent/.gitignore`
- Create: `/Users/sss/careeragent/Makefile`
- Create: `/Users/sss/careeragent/backend/pyproject.toml`
- Create: `/Users/sss/careeragent/backend/app/main.py`
- Create: `/Users/sss/careeragent/backend/app/__init__.py`
- Create: `/Users/sss/careeragent/backend/tests/conftest.py`
- Create: `/Users/sss/careeragent/frontend/package.json`
- Create: `/Users/sss/careeragent/frontend/index.html`
- Create: `/Users/sss/careeragent/frontend/tsconfig.json`
- Create: `/Users/sss/careeragent/frontend/vite.config.ts`
- Create: `/Users/sss/careeragent/frontend/src/main.ts`
- Create: `/Users/sss/careeragent/frontend/src/App.vue`
- Test: `/Users/sss/careeragent/backend/tests/test_health.py`

- [ ] **Step 1: Create scaffold directories**

Run:

```bash
mkdir -p backend/app backend/tests frontend/src
```

Expected: command exits with code 0.

- [ ] **Step 2: Create backend dependency file**

Create `/Users/sss/careeragent/backend/pyproject.toml`:

```toml
[project]
name = "careeragent-backend"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.115.0",
  "uvicorn[standard]>=0.30.0",
  "pydantic>=2.8.0",
  "httpx>=0.27.0",
  "python-multipart>=0.0.9",
  "langgraph>=0.2.0",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.2.0",
  "pytest-asyncio>=0.23.0",
]

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
asyncio_mode = "auto"
```

- [ ] **Step 3: Create FastAPI health endpoint**

Create `/Users/sss/careeragent/backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="CareerAgent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

Create `/Users/sss/careeragent/backend/app/__init__.py`:

```python
"""CareerAgent backend package."""
```

- [ ] **Step 4: Write backend health test**

Create `/Users/sss/careeragent/backend/tests/test_health.py`:

```python
from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_returns_ok() -> None:
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 5: Run backend test**

Run:

```bash
cd /Users/sss/careeragent/backend
python -m pytest tests/test_health.py -v
```

Expected: `1 passed`.

- [ ] **Step 6: Create frontend scaffold files**

Create `/Users/sss/careeragent/frontend/package.json`:

```json
{
  "name": "careeragent-frontend",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite --host 127.0.0.1",
    "build": "vue-tsc --noEmit && vite build",
    "test": "vitest run"
  },
  "dependencies": {
    "@vitejs/plugin-vue": "^5.2.0",
    "element-plus": "^2.9.0",
    "lucide-vue-next": "^0.468.0",
    "pinia": "^2.2.0",
    "vue": "^3.5.0",
    "vue-router": "^4.4.0"
  },
  "devDependencies": {
    "@vue/test-utils": "^2.4.0",
    "jsdom": "^25.0.0",
    "typescript": "^5.6.0",
    "vite": "^6.0.0",
    "vitest": "^2.1.0",
    "vue-tsc": "^2.1.0"
  }
}
```

Create `/Users/sss/careeragent/frontend/index.html`:

```html
<div id="app"></div>
<script type="module" src="/src/main.ts"></script>
```

Create `/Users/sss/careeragent/frontend/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "strict": true,
    "jsx": "preserve",
    "types": ["vitest/globals"]
  },
  "include": ["src/**/*.ts", "src/**/*.vue", "tests/**/*.ts"]
}
```

Create `/Users/sss/careeragent/frontend/vite.config.ts`:

```ts
import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: "jsdom"
  },
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8000"
    }
  }
});
```

Create `/Users/sss/careeragent/frontend/src/main.ts`:

```ts
import ElementPlus from "element-plus";
import "element-plus/dist/index.css";
import { createPinia } from "pinia";
import { createApp } from "vue";
import App from "./App.vue";

createApp(App).use(createPinia()).use(ElementPlus).mount("#app");
```

Create `/Users/sss/careeragent/frontend/src/App.vue`:

```vue
<template>
  <main class="app-root">
    <h1>CareerAgent</h1>
    <p>职业发展智能体本地演示版</p>
  </main>
</template>

<style scoped>
.app-root {
  min-height: 100vh;
  display: grid;
  place-content: center;
  color: #172337;
  background: #f7f9fb;
  font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
}
</style>
```

- [ ] **Step 7: Create root helper files**

Create `/Users/sss/careeragent/.gitignore`:

```gitignore
.DS_Store
.superpowers/
__pycache__/
.pytest_cache/
.venv/
node_modules/
dist/
data/runtime/*
!data/runtime/.gitkeep
```

Create `/Users/sss/careeragent/Makefile`:

```makefile
.PHONY: backend-test frontend-build

backend-test:
	cd backend && python -m pytest -v

frontend-build:
	cd frontend && npm run build
```

- [ ] **Step 8: Commit scaffold**

Run:

```bash
git add .gitignore Makefile backend frontend
git commit -m "chore: scaffold CareerAgent app"
```

Expected: commit succeeds and includes scaffold files only.

## Task 2: Backend Schemas And JSON Repository

**Files:**
- Create: `/Users/sss/careeragent/backend/app/schemas/common.py`
- Create: `/Users/sss/careeragent/backend/app/schemas/profiles.py`
- Create: `/Users/sss/careeragent/backend/app/schemas/jobs.py`
- Create: `/Users/sss/careeragent/backend/app/schemas/matches.py`
- Create: `/Users/sss/careeragent/backend/app/schemas/plans.py`
- Create: `/Users/sss/careeragent/backend/app/schemas/training.py`
- Create: `/Users/sss/careeragent/backend/app/schemas/interviews.py`
- Create: `/Users/sss/careeragent/backend/app/schemas/conversations.py`
- Create: `/Users/sss/careeragent/backend/app/schemas/reports.py`
- Create: `/Users/sss/careeragent/backend/app/schemas/memory.py`
- Create: `/Users/sss/careeragent/backend/app/schemas/skills.py`
- Create: `/Users/sss/careeragent/backend/app/schemas/__init__.py`
- Create: `/Users/sss/careeragent/backend/app/repositories/paths.py`
- Create: `/Users/sss/careeragent/backend/app/repositories/json_repository.py`
- Create: `/Users/sss/careeragent/backend/app/repositories/__init__.py`
- Test: `/Users/sss/careeragent/backend/tests/test_json_repository.py`

- [ ] **Step 1: Write repository test first**

Create `/Users/sss/careeragent/backend/tests/test_json_repository.py`:

```python
from pathlib import Path

from app.repositories.json_repository import JsonRepository


def test_json_repository_round_trip(tmp_path: Path) -> None:
    repo = JsonRepository(root=tmp_path)

    repo.write("profiles", "student-1", {"name": "林晨", "skills": ["Python"]})
    loaded = repo.read("profiles", "student-1")

    assert loaded == {"name": "林晨", "skills": ["Python"]}
    assert (tmp_path / "profiles" / "student-1.json").exists()


def test_json_repository_lists_saved_objects(tmp_path: Path) -> None:
    repo = JsonRepository(root=tmp_path)
    repo.write("jobs", "agent-dev", {"title": "Agent 开发工程师"})

    assert repo.list_ids("jobs") == ["agent-dev"]
```

- [ ] **Step 2: Run repository test and verify it fails**

Run:

```bash
cd /Users/sss/careeragent/backend
python -m pytest tests/test_json_repository.py -v
```

Expected: FAIL with `ModuleNotFoundError` or missing `JsonRepository`.

- [ ] **Step 3: Implement repository**

Create `/Users/sss/careeragent/backend/app/repositories/json_repository.py`:

```python
import json
from pathlib import Path
from typing import Any


class JsonRepository:
    def __init__(self, root: Path) -> None:
        self.root = root

    def write(self, collection: str, object_id: str, payload: dict[str, Any]) -> Path:
        collection_dir = self.root / collection
        collection_dir.mkdir(parents=True, exist_ok=True)
        path = collection_dir / f"{object_id}.json"
        temp_path = path.with_suffix(".json.tmp")
        temp_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp_path.replace(path)
        return path

    def read(self, collection: str, object_id: str) -> dict[str, Any]:
        path = self.root / collection / f"{object_id}.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def list_ids(self, collection: str) -> list[str]:
        collection_dir = self.root / collection
        if not collection_dir.exists():
            return []
        return sorted(path.stem for path in collection_dir.glob("*.json"))
```

Create `/Users/sss/careeragent/backend/app/repositories/paths.py`:

```python
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = PROJECT_ROOT / "data"
DEMO_ROOT = DATA_ROOT / "demo"
RUNTIME_ROOT = DATA_ROOT / "runtime"
```

Create `/Users/sss/careeragent/backend/app/repositories/__init__.py`:

```python
"""Persistence helpers."""
```

- [ ] **Step 4: Add core schema models**

Create `/Users/sss/careeragent/backend/app/schemas/common.py`:

```python
from datetime import datetime, timezone
from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TimestampedModel(BaseModel):
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
```

Create `/Users/sss/careeragent/backend/app/schemas/profiles.py`:

```python
from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    label: str
    source: str
    confidence: float = Field(ge=0, le=1)


class StudentProfile(BaseModel):
    id: str
    name: str
    major: str = ""
    education: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    experiences: list[str] = Field(default_factory=list)
    preferences: list[str] = Field(default_factory=list)
    target_roles: list[str] = Field(default_factory=list)
    evidence_chain: list[EvidenceItem] = Field(default_factory=list)


class ParseResumeRequest(BaseModel):
    resume_text: str


class ProfileResponse(BaseModel):
    profile: StudentProfile
```

Create `/Users/sss/careeragent/backend/app/schemas/jobs.py`:

```python
from pydantic import BaseModel, Field


class JobProfile(BaseModel):
    id: str
    title: str
    source: str = "custom"
    responsibilities: list[str] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    evaluation_dimensions: list[str] = Field(default_factory=list)
    source_jd: str = ""


class AnalyzeJobRequest(BaseModel):
    title: str
    jd_text: str = ""
    source: str = "custom"


class JobProfileResponse(BaseModel):
    job: JobProfile
```

Create `/Users/sss/careeragent/backend/app/schemas/matches.py`:

```python
from pydantic import BaseModel, Field


class MatchResult(BaseModel):
    id: str
    profile_id: str
    job_id: str
    score: int = Field(ge=0, le=100)
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    priorities: list[str] = Field(default_factory=list)
```

Create `/Users/sss/careeragent/backend/app/schemas/plans.py`:

```python
from pydantic import BaseModel, Field


class PlanStage(BaseModel):
    title: str
    duration: str
    actions: list[str] = Field(default_factory=list)


class CareerPlan(BaseModel):
    id: str
    profile_id: str
    job_id: str
    summary: str
    stages: list[PlanStage] = Field(default_factory=list)
```

Create `/Users/sss/careeragent/backend/app/schemas/training.py`:

```python
from pydantic import BaseModel, Field


class TrainingTask(BaseModel):
    id: str
    job_id: str
    title: str
    scenario: str
    rubric: list[str] = Field(default_factory=list)


class TrainingSubmission(BaseModel):
    id: str
    task_id: str
    answer: str
    score: int = Field(ge=0, le=100)
    feedback: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
```

Create `/Users/sss/careeragent/backend/app/schemas/interviews.py`:

```python
from pydantic import BaseModel, Field


class InterviewMessage(BaseModel):
    role: str
    content: str


class InterviewSession(BaseModel):
    id: str
    profile_id: str
    job_id: str
    messages: list[InterviewMessage] = Field(default_factory=list)
    score: int | None = None
    summary: str = ""
```

Create `/Users/sss/careeragent/backend/app/schemas/conversations.py`:

```python
from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):
    role: str
    content: str


class ConversationSession(BaseModel):
    id: str
    scope: str
    related_object_ids: dict[str, str] = Field(default_factory=dict)
    messages: list[ConversationMessage] = Field(default_factory=list)
    snapshot_id: str | None = None
```

Create `/Users/sss/careeragent/backend/app/schemas/reports.py`:

```python
from pydantic import BaseModel


class ReportRecord(BaseModel):
    id: str
    profile_id: str
    markdown: str
```

Create `/Users/sss/careeragent/backend/app/schemas/memory.py`:

```python
from pydantic import BaseModel, Field


class MemoryFact(BaseModel):
    key: str
    value: str
    source: str
    confidence: float = Field(ge=0, le=1)
    confirmed_by_user: bool = False


class CompactionSnapshot(BaseModel):
    id: str
    goal_summary: str
    confirmed_facts: list[MemoryFact] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)
    module_state: dict[str, str] = Field(default_factory=dict)
    agent_notes: dict[str, str] = Field(default_factory=dict)
    skill_refs: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    source_index: list[str] = Field(default_factory=list)
```

Create `/Users/sss/careeragent/backend/app/schemas/skills.py`:

```python
from pydantic import BaseModel, Field


class SkillDocument(BaseModel):
    id: str
    path: str
    title: str
    summary: str
    tags: list[str] = Field(default_factory=list)
    content: str
```

Create `/Users/sss/careeragent/backend/app/schemas/__init__.py`:

```python
"""Pydantic schemas for CareerAgent."""
```

- [ ] **Step 5: Run repository tests**

Run:

```bash
cd /Users/sss/careeragent/backend
python -m pytest tests/test_json_repository.py -v
```

Expected: `2 passed`.

- [ ] **Step 6: Commit schema and repository foundation**

Run:

```bash
git add backend/app/schemas backend/app/repositories backend/tests/test_json_repository.py
git commit -m "feat: add schemas and json repository"
```

Expected: commit succeeds.

## Task 3: Demo Data And Progressive Skill Loading

**Files:**
- Create: `/Users/sss/careeragent/backend/app/skills/registry.py`
- Create: `/Users/sss/careeragent/backend/app/skills/loader.py`
- Create: `/Users/sss/careeragent/backend/app/skills/__init__.py`
- Create: `/Users/sss/careeragent/backend/app/skills/builtin/**/*.md`
- Create: `/Users/sss/careeragent/data/demo/students.json`
- Create: `/Users/sss/careeragent/data/demo/jobs.json`
- Create: `/Users/sss/careeragent/data/demo/training_tasks.json`
- Create: `/Users/sss/careeragent/data/runtime/.gitkeep`
- Test: `/Users/sss/careeragent/backend/tests/test_skills.py`

- [ ] **Step 1: Write skill loader test**

Create `/Users/sss/careeragent/backend/tests/test_skills.py`:

```python
from pathlib import Path

from app.skills.loader import SkillLoader
from app.skills.registry import SkillRegistry


def test_skill_registry_returns_matching_skills(tmp_path: Path) -> None:
    skill_path = tmp_path / "job" / "agent_developer_role.md"
    skill_path.parent.mkdir(parents=True)
    skill_path.write_text(
        "# Agent 开发岗位\n\nSummary: 分析 Agent 开发工程师岗位。\n\nTags: job,agent\n\n## 内容\n岗位能力画像。",
        encoding="utf-8",
    )
    registry = SkillRegistry(root=tmp_path)

    matches = registry.find(tags=["job"], query="Agent 开发")

    assert [match.id for match in matches] == ["job/agent_developer_role"]


def test_skill_loader_loads_content(tmp_path: Path) -> None:
    skill_path = tmp_path / "memory" / "context_compaction.md"
    skill_path.parent.mkdir(parents=True)
    skill_path.write_text("# 上下文压缩\n\nSummary: 保存可恢复任务状态。", encoding="utf-8")
    loader = SkillLoader(root=tmp_path)

    doc = loader.load("memory/context_compaction")

    assert doc.title == "上下文压缩"
    assert "保存可恢复任务状态" in doc.content
```

- [ ] **Step 2: Run skill tests and verify they fail**

Run:

```bash
cd /Users/sss/careeragent/backend
python -m pytest tests/test_skills.py -v
```

Expected: FAIL with missing `app.skills`.

- [ ] **Step 3: Implement Skill Registry and Loader**

Create `/Users/sss/careeragent/backend/app/skills/loader.py`:

```python
from pathlib import Path

from app.schemas.skills import SkillDocument


class SkillLoader:
    def __init__(self, root: Path) -> None:
        self.root = root

    def load(self, skill_id: str) -> SkillDocument:
        path = self.root / f"{skill_id}.md"
        content = path.read_text(encoding="utf-8")
        title = self._title(content)
        return SkillDocument(
            id=skill_id,
            path=str(path),
            title=title,
            summary=self._summary(content),
            tags=self._tags(content),
            content=content,
        )

    def _title(self, content: str) -> str:
        for line in content.splitlines():
            if line.startswith("# "):
                return line[2:].strip()
        return "Untitled Skill"

    def _summary(self, content: str) -> str:
        for line in content.splitlines():
            if line.startswith("Summary:"):
                return line.removeprefix("Summary:").strip()
        return ""

    def _tags(self, content: str) -> list[str]:
        for line in content.splitlines():
            if line.startswith("Tags:"):
                return [part.strip() for part in line.removeprefix("Tags:").split(",") if part.strip()]
        return []
```

Create `/Users/sss/careeragent/backend/app/skills/registry.py`:

```python
from pathlib import Path

from app.schemas.skills import SkillDocument
from app.skills.loader import SkillLoader


class SkillRegistry:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.loader = SkillLoader(root)

    def find(self, tags: list[str], query: str = "", limit: int = 5) -> list[SkillDocument]:
        docs: list[SkillDocument] = []
        for path in sorted(self.root.glob("**/*.md")):
            skill_id = str(path.relative_to(self.root).with_suffix(""))
            doc = self.loader.load(skill_id)
            tag_match = not tags or any(tag in doc.tags for tag in tags)
            query_match = not query or query.lower() in doc.content.lower()
            if tag_match and query_match:
                docs.append(doc)
        return docs[:limit]
```

Create `/Users/sss/careeragent/backend/app/skills/__init__.py`:

```python
"""Progressive Skill loading for agents."""
```

- [ ] **Step 4: Add built-in Skill documents**

Create `/Users/sss/careeragent/backend/app/skills/builtin/job/agent_developer_role.md` with this exact content:

```markdown
# Agent 开发岗位画像

Summary: 分析 Agent 开发工程师岗位的能力要求、工具栈和评价维度。

Tags: job,agent,role

## 使用条件

当学生选择 Agent 开发工程师，或自定义岗位/JD 与 AI Agent、智能体开发、工具调用、工作流编排相关时使用。

## 操作规则

- 提取岗位职责、核心能力、常用工具、项目经验要求。
- 区分必备能力和加分能力。
- 评价维度至少包含：Python 后端能力、LLM API 调用、工具调用设计、Agent 工作流编排、RAG/记忆设计、测试与评估、表达与文档能力。

## 输出要求

输出岗位画像时包含 responsibilities、required_skills、tools、evaluation_dimensions 和 source_jd。
```

Create the remaining Skill files with these exact contents:

```markdown
<!-- backend/app/skills/builtin/profile/resume_parsing.md -->
# 简历解析

Summary: 将学生简历文本解析为结构化职业画像草稿。

Tags: profile,resume

## 使用条件

当学生上传简历、粘贴简历文本或要求系统根据经历生成画像时使用。

## 操作规则

- 抽取教育背景、课程、技能、项目、实习、竞赛和职业偏好。
- 明确事实写入画像草稿，模型推断只作为待确认信息。
- 为每个技能或经历保留来源说明。

## 输出要求

输出 StudentProfile 字段，并为 evidence_chain 提供 label、source 和 confidence。
```

```markdown
<!-- backend/app/skills/builtin/profile/evidence_chain.md -->
# 能力证据链

Summary: 将技能、项目和经历整理为可解释的能力证据链。

Tags: profile,evidence

## 使用条件

当系统需要解释学生为什么具备某项能力，或需要支撑人岗匹配结论时使用。

## 操作规则

- 每条能力必须关联一个课程、项目、实习、竞赛或学生确认事实。
- 区分强证据、弱证据和待确认推断。
- 不把无来源的模型猜测写成事实。

## 输出要求

输出 EvidenceItem 列表，每项包含 label、source 和 confidence。
```

```markdown
<!-- backend/app/skills/builtin/job/jd_analysis.md -->
# JD 分析

Summary: 将自定义岗位描述解析为岗位能力画像。

Tags: job,jd

## 使用条件

当学生输入自定义岗位名称或粘贴 JD 时使用。

## 操作规则

- 抽取岗位职责、必备能力、加分能力、工具栈和评价维度。
- 如果 JD 信息不足，生成合理画像并标记 source 为 custom。
- 保留原始 JD 作为 source_jd。

## 输出要求

输出 JobProfile 字段，包括 title、responsibilities、required_skills、tools、evaluation_dimensions 和 source_jd。
```

```markdown
<!-- backend/app/skills/builtin/match/match_scoring_rubric.md -->
# 匹配评分标准

Summary: 根据学生画像和岗位画像计算人岗匹配分。

Tags: match,scoring

## 使用条件

当系统需要计算匹配分、展示优势和短板时使用。

## 操作规则

- 匹配分范围为 0 到 100。
- 分数由必备技能、项目证据、岗位偏好和表达准备共同决定。
- 每个优势和短板都要引用 evidence 或岗位要求。

## 输出要求

输出 MatchResult，包括 score、strengths、gaps、evidence 和 priorities。
```

```markdown
<!-- backend/app/skills/builtin/match/gap_diagnosis.md -->
# 能力差距诊断

Summary: 将岗位要求和学生画像之间的差距转化为优先提升项。

Tags: match,gap

## 使用条件

当匹配分生成后，需要解释能力短板和下一步提升顺序时使用。

## 操作规则

- 优先处理影响岗位入门的核心差距。
- 将差距表达成可行动任务，而不是泛泛建议。
- 标记每个差距对应的岗位能力维度。

## 输出要求

输出 priorities，并为每个优先项给出原因。
```

```markdown
<!-- backend/app/skills/builtin/planning/career_path_planning.md -->
# 职业路径规划

Summary: 基于目标岗位和能力差距生成阶段化职业发展路线。

Tags: planning,path

## 使用条件

当学生需要从当前能力状态走向目标岗位时使用。

## 操作规则

- 路线必须分阶段。
- 每个阶段包含目标、行动、项目产出和可验证证据。
- 路线要和学生当前基础匹配。

## 输出要求

输出 CareerPlan，包含 summary 和 stages。
```

```markdown
<!-- backend/app/skills/builtin/planning/three_month_plan.md -->
# 三个月提升计划

Summary: 将职业路径压缩为三个月可执行计划。

Tags: planning,three-month

## 使用条件

当学生明确提出三个月、十二周或短期冲刺目标时使用。

## 操作规则

- 分为 1-4 周、5-8 周、9-12 周。
- 第一阶段补基础，第二阶段做项目，第三阶段求职训练。
- 每个阶段最多三个核心行动。

## 输出要求

输出三段 PlanStage，每段包含 duration 和 actions。
```

```markdown
<!-- backend/app/skills/builtin/training/workplace_task_generation.md -->
# 虚拟职场任务生成

Summary: 根据目标岗位生成可提交、可评分的训练任务。

Tags: training,task

## 使用条件

当学生进入任务舱，或需要围绕岗位能力训练时使用。

## 操作规则

- 任务应模拟真实工作场景。
- 任务必须要求学生产出文字方案。
- 任务评分维度与岗位能力画像一致。

## 输出要求

输出 TrainingTask，包括 title、scenario 和 rubric。
```

```markdown
<!-- backend/app/skills/builtin/training/submission_scoring.md -->
# 任务提交评分

Summary: 对学生提交的训练答案进行评分和反馈。

Tags: training,scoring

## 使用条件

当学生提交虚拟职场任务答案后使用。

## 操作规则

- 评分范围 0 到 100。
- 反馈必须包含优点、不足和下一步修改建议。
- 不能只给鼓励性评价。

## 输出要求

输出 TrainingSubmission，包括 score、feedback 和 next_steps。
```

```markdown
<!-- backend/app/skills/builtin/interview/mock_interview_flow.md -->
# 模拟面试流程

Summary: 组织面向目标岗位的文字模拟面试。

Tags: interview,flow

## 使用条件

当学生开始模拟面试或继续回答面试问题时使用。

## 操作规则

- 每次只问一个问题。
- 根据学生回答进行追问。
- 面试结束时总结技术能力、表达能力和改进建议。

## 输出要求

输出 InterviewSession 消息列表，并在结束时提供 score 和 summary。
```

```markdown
<!-- backend/app/skills/builtin/interview/answer_scoring.md -->
# 面试回答评分

Summary: 对学生面试回答进行结构化评价。

Tags: interview,scoring

## 使用条件

当学生回答面试问题后需要评分或追问时使用。

## 操作规则

- 评价回答的完整性、逻辑性、专业性和岗位相关性。
- 追问要针对缺失信息。
- 不泄露模型隐藏思考过程。

## 输出要求

输出分数、追问问题和反馈总结。
```

```markdown
<!-- backend/app/skills/builtin/report/markdown_report.md -->
# Markdown 职业发展报告

Summary: 将画像、匹配、路径、训练和面试结果整理为 Markdown 报告。

Tags: report,markdown

## 使用条件

当学生请求导出个人职业发展报告时使用。

## 操作规则

- 报告使用清晰标题层级。
- 包含职业画像、目标岗位、匹配诊断、提升路径、训练记录和面试反馈。
- 保留下一步行动建议。

## 输出要求

输出 Markdown 字符串。
```

```markdown
<!-- backend/app/skills/builtin/memory/long_term_write_policy.md -->
# 长期记忆写入规则

Summary: 判断哪些信息可以进入学生长期职业数字孪生。

Tags: memory,long-term

## 使用条件

当 Agent 产生新事实、新推断或训练反馈时使用。

## 操作规则

- 学生确认事实可以写入。
- 模型推断必须带置信度。
- 低置信度猜测不写入长期记忆。

## 输出要求

输出是否写入、原因、source、confidence 和 confirmed_by_user。
```

```markdown
<!-- backend/app/skills/builtin/memory/context_compaction.md -->
# 上下文压缩

Summary: 将长对话压缩为可恢复任务状态。

Tags: memory,compaction

## 使用条件

当上下文过长、模块切换或任务完成时使用。

## 操作规则

- 保留目标、约束、决策、当前状态、Skill 引用和下一步。
- 不保存完整模型 thinking 内容。
- 不复制完整 Skill 正文。

## 输出要求

输出 CompactionSnapshot。
```

- [ ] **Step 5: Add demo data**

Create `/Users/sss/careeragent/data/demo/students.json`:

```json
[
  {
    "id": "student-cs-agent",
    "name": "林晨",
    "major": "计算机科学与技术",
    "education": ["本科三年级"],
    "skills": ["Python", "FastAPI", "Vue", "基础机器学习"],
    "projects": ["校园问答机器人", "课程推荐系统"],
    "experiences": ["校内软件开发实训"],
    "preferences": ["AI 应用开发", "后端工程"],
    "target_roles": ["Agent 开发工程师"],
    "evidence_chain": []
  },
  {
    "id": "student-cross-ai",
    "name": "周雨",
    "major": "工商管理",
    "education": ["本科三年级"],
    "skills": ["数据分析基础", "Excel", "用户调研", "Python 入门"],
    "projects": ["校园活动数据分析", "用户访谈报告"],
    "experiences": ["社团运营"],
    "preferences": ["AI 产品", "智能体应用"],
    "target_roles": ["Agent 开发工程师"],
    "evidence_chain": []
  }
]
```

Create `/Users/sss/careeragent/data/demo/jobs.json`:

```json
[
  {
    "id": "agent-developer",
    "title": "Agent 开发工程师",
    "source": "preset",
    "responsibilities": ["设计智能体工作流", "接入大模型 API", "实现工具调用和记忆模块"],
    "required_skills": ["Python", "FastAPI", "LLM API", "LangGraph", "Prompt Engineering", "测试评估"],
    "tools": ["Qwen", "DeepSeek", "LangGraph", "FastAPI", "JSON"],
    "evaluation_dimensions": ["后端能力", "模型调用", "工作流编排", "记忆设计", "测试能力"],
    "source_jd": "预置 Agent 开发工程师岗位"
  }
]
```

Create `/Users/sss/careeragent/data/demo/training_tasks.json`:

```json
[
  {
    "id": "task-agent-workflow-design",
    "job_id": "agent-developer",
    "title": "设计职业规划 Agent 工作流",
    "scenario": "为高校学生职业规划系统设计一个多 Agent 工作流，说明每个 Agent 的职责、输入、输出和交接条件。",
    "rubric": ["需求理解", "Agent 边界", "记忆设计", "工具调用", "可测试性"]
  }
]
```

Create `/Users/sss/careeragent/data/runtime/.gitkeep` as an empty file.

- [ ] **Step 6: Run skill tests**

Run:

```bash
cd /Users/sss/careeragent/backend
python -m pytest tests/test_skills.py -v
```

Expected: `2 passed`.

- [ ] **Step 7: Commit skills and demo data**

Run:

```bash
git add backend/app/skills backend/tests/test_skills.py data/demo data/runtime/.gitkeep
git commit -m "feat: add progressive skills and demo data"
```

Expected: commit succeeds.

## Task 4: Model Providers And Router

**Files:**
- Create: `/Users/sss/careeragent/backend/app/providers/base.py`
- Create: `/Users/sss/careeragent/backend/app/providers/mock.py`
- Create: `/Users/sss/careeragent/backend/app/providers/qwen.py`
- Create: `/Users/sss/careeragent/backend/app/providers/deepseek.py`
- Create: `/Users/sss/careeragent/backend/app/providers/router.py`
- Create: `/Users/sss/careeragent/backend/app/providers/__init__.py`
- Test: `/Users/sss/careeragent/backend/tests/test_model_router.py`

- [ ] **Step 1: Write model router tests**

Create `/Users/sss/careeragent/backend/tests/test_model_router.py`:

```python
import pytest

from app.providers.mock import MockProvider
from app.providers.router import ModelRouter


@pytest.mark.asyncio
async def test_router_selects_qwen_for_report() -> None:
    router = ModelRouter(qwen=MockProvider("qwen"), deepseek=MockProvider("deepseek"))

    result = await router.generate(task="report", messages=[{"role": "user", "content": "生成报告"}])

    assert result.model == "qwen"
    assert "生成报告" in result.content


@pytest.mark.asyncio
async def test_router_selects_deepseek_for_match() -> None:
    router = ModelRouter(qwen=MockProvider("qwen"), deepseek=MockProvider("deepseek"))

    result = await router.generate(task="match", messages=[{"role": "user", "content": "诊断差距"}])

    assert result.model == "deepseek"
    assert "诊断差距" in result.content
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```bash
cd /Users/sss/careeragent/backend
python -m pytest tests/test_model_router.py -v
```

Expected: FAIL with missing provider modules.

- [ ] **Step 3: Implement providers**

Create `/Users/sss/careeragent/backend/app/providers/base.py`:

```python
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ModelResult:
    model: str
    content: str


class ModelProvider(Protocol):
    async def generate(
        self,
        messages: list[dict[str, str]],
        schema: type | None = None,
        thinking: bool = True,
        model: str | None = None,
    ) -> ModelResult:
        raise NotImplementedError
```

Create `/Users/sss/careeragent/backend/app/providers/mock.py`:

```python
from app.providers.base import ModelResult


class MockProvider:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    async def generate(
        self,
        messages: list[dict[str, str]],
        schema: type | None = None,
        thinking: bool = True,
        model: str | None = None,
    ) -> ModelResult:
        content = "\n".join(message["content"] for message in messages)
        return ModelResult(model=model or self.model_name, content=f"[{self.model_name}] {content}")
```

Create `/Users/sss/careeragent/backend/app/providers/router.py`:

```python
from app.providers.base import ModelProvider, ModelResult


class ModelRouter:
    def __init__(self, qwen: ModelProvider, deepseek: ModelProvider) -> None:
        self.qwen = qwen
        self.deepseek = deepseek

    async def generate(
        self,
        task: str,
        messages: list[dict[str, str]],
        schema: type | None = None,
        thinking: bool = True,
    ) -> ModelResult:
        provider = self._select(task)
        return await provider.generate(messages=messages, schema=schema, thinking=thinking)

    def _select(self, task: str) -> ModelProvider:
        if task in {"match", "job", "interview", "critique", "score"}:
            return self.deepseek
        return self.qwen
```

Create `/Users/sss/careeragent/backend/app/providers/qwen.py`:

```python
import os

import httpx

from app.providers.base import ModelResult


class QwenProvider:
    def __init__(self, api_key: str | None = None, base_url: str | None = None, model: str = "qwen3.6-plus") -> None:
        self.api_key = api_key or os.getenv("QWEN_API_KEY", "")
        self.base_url = base_url or os.getenv("QWEN_BASE_URL", "")
        self.model = model

    async def generate(self, messages: list[dict[str, str]], schema: type | None = None, thinking: bool = True, model: str | None = None) -> ModelResult:
        if not self.api_key or not self.base_url:
            raise RuntimeError("Qwen provider requires QWEN_API_KEY and QWEN_BASE_URL")
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": model or self.model, "messages": messages, "thinking": thinking},
            )
            response.raise_for_status()
            payload = response.json()
        content = payload.get("choices", [{}])[0].get("message", {}).get("content", "")
        return ModelResult(model=model or self.model, content=content)
```

Create `/Users/sss/careeragent/backend/app/providers/deepseek.py`:

```python
import os

import httpx

from app.providers.base import ModelResult


class DeepSeekProvider:
    def __init__(self, api_key: str | None = None, base_url: str | None = None, model: str = "deepseek-v4-flash") -> None:
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        self.base_url = base_url or os.getenv("DEEPSEEK_BASE_URL", "")
        self.model = model

    async def generate(self, messages: list[dict[str, str]], schema: type | None = None, thinking: bool = True, model: str | None = None) -> ModelResult:
        if not self.api_key or not self.base_url:
            raise RuntimeError("DeepSeek provider requires DEEPSEEK_API_KEY and DEEPSEEK_BASE_URL")
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": model or self.model, "messages": messages, "thinking": thinking},
            )
            response.raise_for_status()
            payload = response.json()
        content = payload.get("choices", [{}])[0].get("message", {}).get("content", "")
        return ModelResult(model=model or self.model, content=content)
```

Create `/Users/sss/careeragent/backend/app/providers/__init__.py`:

```python
"""Model provider abstractions."""
```

- [ ] **Step 4: Run model router tests**

Run:

```bash
cd /Users/sss/careeragent/backend
python -m pytest tests/test_model_router.py -v
```

Expected: `2 passed`.

- [ ] **Step 5: Commit model provider layer**

Run:

```bash
git add backend/app/providers backend/tests/test_model_router.py
git commit -m "feat: add model provider router"
```

Expected: commit succeeds.

## Task 5: Memory Manager And Context Compaction

**Files:**
- Create: `/Users/sss/careeragent/backend/app/memory/manager.py`
- Create: `/Users/sss/careeragent/backend/app/memory/compaction.py`
- Create: `/Users/sss/careeragent/backend/app/memory/__init__.py`
- Test: `/Users/sss/careeragent/backend/tests/test_memory.py`

- [ ] **Step 1: Write memory tests**

Create `/Users/sss/careeragent/backend/tests/test_memory.py`:

```python
from app.memory.compaction import compact_conversation
from app.memory.manager import should_write_long_term
from app.schemas.conversations import ConversationMessage
from app.schemas.memory import MemoryFact


def test_unconfirmed_low_confidence_fact_is_not_written() -> None:
    fact = MemoryFact(key="career_interest", value="Agent 开发", source="model_inference", confidence=0.4)

    assert should_write_long_term(fact) is False


def test_confirmed_fact_is_written() -> None:
    fact = MemoryFact(key="target_role", value="Agent 开发工程师", source="student", confidence=1.0, confirmed_by_user=True)

    assert should_write_long_term(fact) is True


def test_compaction_snapshot_keeps_goal_and_skill_refs() -> None:
    messages = [
        ConversationMessage(role="user", content="我想三个月转 Agent 开发"),
        ConversationMessage(role="assistant", content="需要诊断画像、岗位和路径"),
    ]

    snapshot = compact_conversation(
        conversation_id="conv-1",
        goal_summary="三个月转 Agent 开发",
        messages=messages,
        skill_refs=["planning/three_month_plan"],
    )

    assert snapshot.goal_summary == "三个月转 Agent 开发"
    assert snapshot.skill_refs == ["planning/three_month_plan"]
    assert snapshot.source_index == ["conv-1:0-1"]
```

- [ ] **Step 2: Run memory tests and verify they fail**

Run:

```bash
cd /Users/sss/careeragent/backend
python -m pytest tests/test_memory.py -v
```

Expected: FAIL with missing memory modules.

- [ ] **Step 3: Implement memory manager**

Create `/Users/sss/careeragent/backend/app/memory/manager.py`:

```python
from app.schemas.memory import MemoryFact


def should_write_long_term(fact: MemoryFact) -> bool:
    if fact.confirmed_by_user:
        return True
    if fact.source in {"student", "resume"} and fact.confidence >= 0.75:
        return True
    return False
```

Create `/Users/sss/careeragent/backend/app/memory/compaction.py`:

```python
from app.schemas.conversations import ConversationMessage
from app.schemas.memory import CompactionSnapshot


def compact_conversation(
    conversation_id: str,
    goal_summary: str,
    messages: list[ConversationMessage],
    skill_refs: list[str],
) -> CompactionSnapshot:
    last_index = max(len(messages) - 1, 0)
    return CompactionSnapshot(
        id=f"{conversation_id}-snapshot",
        goal_summary=goal_summary,
        decisions=[],
        module_state={"conversation_id": conversation_id},
        agent_notes={"summary": "保留当前目标、最近对话和下一步任务状态"},
        skill_refs=skill_refs,
        open_questions=[],
        next_actions=["继续当前场景对话"],
        source_index=[f"{conversation_id}:0-{last_index}"],
    )
```

Create `/Users/sss/careeragent/backend/app/memory/__init__.py`:

```python
"""Memory and context compaction helpers."""
```

- [ ] **Step 4: Run memory tests**

Run:

```bash
cd /Users/sss/careeragent/backend
python -m pytest tests/test_memory.py -v
```

Expected: `3 passed`.

- [ ] **Step 5: Commit memory layer**

Run:

```bash
git add backend/app/memory backend/tests/test_memory.py
git commit -m "feat: add memory and context compaction"
```

Expected: commit succeeds.

## Task 6: Agent Contracts And Deterministic Agent Implementations

**Files:**
- Create: `/Users/sss/careeragent/backend/app/agents/contracts.py`
- Create: `/Users/sss/careeragent/backend/app/agents/profile.py`
- Create: `/Users/sss/careeragent/backend/app/agents/job.py`
- Create: `/Users/sss/careeragent/backend/app/agents/match.py`
- Create: `/Users/sss/careeragent/backend/app/agents/planning.py`
- Create: `/Users/sss/careeragent/backend/app/agents/training.py`
- Create: `/Users/sss/careeragent/backend/app/agents/interview.py`
- Create: `/Users/sss/careeragent/backend/app/agents/report.py`
- Create: `/Users/sss/careeragent/backend/app/agents/supervisor.py`
- Create: `/Users/sss/careeragent/backend/app/agents/__init__.py`
- Test: `/Users/sss/careeragent/backend/tests/test_agents.py`

- [ ] **Step 1: Write agent behavior tests**

Create `/Users/sss/careeragent/backend/tests/test_agents.py`:

```python
from app.agents.job import analyze_job_deterministic
from app.agents.match import match_profile_to_job
from app.agents.planning import build_plan
from app.schemas.jobs import JobProfile
from app.schemas.profiles import StudentProfile


def test_job_agent_creates_agent_developer_profile() -> None:
    job = analyze_job_deterministic(title="Agent 开发工程师", jd_text="")

    assert job.id == "agent-developer"
    assert "LangGraph" in job.tools
    assert "工作流编排" in "".join(job.evaluation_dimensions)


def test_match_agent_scores_profile_against_job() -> None:
    profile = StudentProfile(id="p1", name="林晨", skills=["Python", "FastAPI", "LangGraph"])
    job = JobProfile(id="j1", title="Agent 开发工程师", required_skills=["Python", "FastAPI", "LangGraph", "测试评估"])

    result = match_profile_to_job(profile=profile, job=job)

    assert result.score == 75
    assert "测试评估" in result.gaps


def test_planning_agent_generates_stages() -> None:
    plan = build_plan(profile_id="p1", job_id="j1", gaps=["测试评估", "记忆设计"])

    assert len(plan.stages) == 3
    assert "测试评估" in plan.stages[0].actions[0]
```

- [ ] **Step 2: Run agent tests and verify they fail**

Run:

```bash
cd /Users/sss/careeragent/backend
python -m pytest tests/test_agents.py -v
```

Expected: FAIL with missing agent modules.

- [ ] **Step 3: Implement deterministic agents**

Create `/Users/sss/careeragent/backend/app/agents/job.py`:

```python
import re

from app.schemas.jobs import JobProfile


def slugify_title(title: str) -> str:
    if "Agent" in title or "智能体" in title:
        return "agent-developer"
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "custom-job"


def analyze_job_deterministic(title: str, jd_text: str = "") -> JobProfile:
    if "Agent" in title or "智能体" in title:
        return JobProfile(
            id="agent-developer",
            title="Agent 开发工程师",
            source="preset" if not jd_text else "custom",
            responsibilities=["设计智能体工作流", "接入大模型 API", "实现工具调用和记忆模块"],
            required_skills=["Python", "FastAPI", "LLM API", "LangGraph", "Prompt Engineering", "测试评估"],
            tools=["Qwen", "DeepSeek", "LangGraph", "FastAPI", "JSON"],
            evaluation_dimensions=["后端能力", "模型调用", "工作流编排", "记忆设计", "测试能力"],
            source_jd=jd_text or "预置 Agent 开发工程师岗位",
        )
    return JobProfile(id=slugify_title(title), title=title, source="custom", source_jd=jd_text)
```

Create `/Users/sss/careeragent/backend/app/agents/match.py`:

```python
from app.schemas.jobs import JobProfile
from app.schemas.matches import MatchResult
from app.schemas.profiles import StudentProfile


def match_profile_to_job(profile: StudentProfile, job: JobProfile) -> MatchResult:
    required = set(job.required_skills)
    owned = set(profile.skills)
    matched = sorted(required & owned)
    gaps = sorted(required - owned)
    score = int((len(matched) / len(required)) * 100) if required else 0
    return MatchResult(
        id=f"match-{profile.id}-{job.id}",
        profile_id=profile.id,
        job_id=job.id,
        score=score,
        strengths=matched,
        gaps=gaps,
        evidence=[f"技能匹配：{skill}" for skill in matched],
        priorities=gaps[:3],
    )
```

Create `/Users/sss/careeragent/backend/app/agents/planning.py`:

```python
from app.schemas.plans import CareerPlan, PlanStage


def build_plan(profile_id: str, job_id: str, gaps: list[str]) -> CareerPlan:
    first_gap = gaps[0] if gaps else "Agent 项目实践"
    second_gap = gaps[1] if len(gaps) > 1 else "工具调用设计"
    return CareerPlan(
        id=f"plan-{profile_id}-{job_id}",
        profile_id=profile_id,
        job_id=job_id,
        summary="围绕目标岗位补齐关键能力，并通过项目和面试训练形成证据链。",
        stages=[
            PlanStage(title="第 1 阶段：补齐基础", duration="第 1-4 周", actions=[f"学习并练习：{first_gap}"]),
            PlanStage(title="第 2 阶段：完成项目", duration="第 5-8 周", actions=[f"围绕 {second_gap} 完成一个可展示项目"]),
            PlanStage(title="第 3 阶段：求职训练", duration="第 9-12 周", actions=["完善简历、模拟面试、整理项目报告"]),
        ],
    )
```

Create minimal modules for profile, training, interview, report, supervisor, contracts, and init:

```python
# backend/app/agents/contracts.py
from pydantic import BaseModel


class AgentDecision(BaseModel):
    next_agent: str
    reason: str
```

```python
# backend/app/agents/supervisor.py
from app.agents.contracts import AgentDecision


def route_intent(message: str) -> AgentDecision:
    if "面试" in message:
        return AgentDecision(next_agent="interview", reason="用户请求模拟面试")
    if "任务" in message or "训练" in message:
        return AgentDecision(next_agent="training", reason="用户请求任务训练")
    if "岗位" in message or "匹配" in message:
        return AgentDecision(next_agent="match", reason="用户请求岗位匹配")
    return AgentDecision(next_agent="planning", reason="默认进入规划对话")
```

```python
# backend/app/agents/profile.py
from app.schemas.profiles import EvidenceItem, StudentProfile


def parse_resume_text(profile_id: str, resume_text: str) -> StudentProfile:
    skills = [skill for skill in ["Python", "FastAPI", "Vue", "LangGraph"] if skill.lower() in resume_text.lower()]
    return StudentProfile(
        id=profile_id,
        name="待确认学生",
        skills=skills,
        evidence_chain=[EvidenceItem(label=skill, source="resume", confidence=0.8) for skill in skills],
    )
```

```python
# backend/app/agents/training.py
from app.schemas.training import TrainingSubmission, TrainingTask


def score_submission(task: TrainingTask, answer: str) -> TrainingSubmission:
    score = 80 if len(answer) >= 80 else 60
    return TrainingSubmission(
        id=f"submission-{task.id}",
        task_id=task.id,
        answer=answer,
        score=score,
        feedback=["结构清晰" if score >= 80 else "答案需要更具体"],
        next_steps=["补充 Agent 分工、记忆设计和评估方法"],
    )
```

```python
# backend/app/agents/interview.py
from app.schemas.interviews import InterviewMessage, InterviewSession


def start_interview(session_id: str, profile_id: str, job_id: str) -> InterviewSession:
    return InterviewSession(
        id=session_id,
        profile_id=profile_id,
        job_id=job_id,
        messages=[InterviewMessage(role="assistant", content="请介绍一个你做过的 Agent 或 AI 应用项目。")],
    )
```

```python
# backend/app/agents/report.py
def build_markdown_report(title: str, sections: dict[str, str]) -> str:
    body = "\n\n".join(f"## {name}\n\n{content}" for name, content in sections.items())
    return f"# {title}\n\n{body}\n"
```

```python
# backend/app/agents/__init__.py
"""CareerAgent role-specific agents."""
```

- [ ] **Step 4: Run agent tests**

Run:

```bash
cd /Users/sss/careeragent/backend
python -m pytest tests/test_agents.py -v
```

Expected: `3 passed`.

- [ ] **Step 5: Commit deterministic agents**

Run:

```bash
git add backend/app/agents backend/tests/test_agents.py
git commit -m "feat: add deterministic agent foundations"
```

Expected: commit succeeds.

## Task 7: FastAPI Business Endpoints

**Files:**
- Create: `/Users/sss/careeragent/backend/app/api/*.py`
- Modify: `/Users/sss/careeragent/backend/app/main.py`
- Test: `/Users/sss/careeragent/backend/tests/test_api_flow.py`

- [ ] **Step 1: Write API flow test**

Create `/Users/sss/careeragent/backend/tests/test_api_flow.py`:

```python
from fastapi.testclient import TestClient

from app.main import app


def test_profile_job_match_plan_report_flow() -> None:
    client = TestClient(app)

    profile_response = client.post("/api/profiles/parse-resume", json={"resume_text": "我会 Python FastAPI LangGraph"})
    assert profile_response.status_code == 200
    profile_id = profile_response.json()["profile"]["id"]

    job_response = client.post("/api/jobs/analyze", json={"title": "Agent 开发工程师", "jd_text": "", "source": "preset"})
    assert job_response.status_code == 200
    job_id = job_response.json()["job"]["id"]

    match_response = client.post("/api/matches", json={"profile_id": profile_id, "job_id": job_id})
    assert match_response.status_code == 200
    assert match_response.json()["score"] >= 50

    plan_response = client.post("/api/plans", json={"profile_id": profile_id, "job_id": job_id})
    assert plan_response.status_code == 200
    assert len(plan_response.json()["stages"]) == 3

    report_response = client.post("/api/reports", json={"profile_id": profile_id, "job_id": job_id})
    assert report_response.status_code == 200
    assert "Markdown" in report_response.json()["markdown"]
```

- [ ] **Step 2: Run API test and verify it fails**

Run:

```bash
cd /Users/sss/careeragent/backend
python -m pytest tests/test_api_flow.py -v
```

Expected: FAIL with route not found.

- [ ] **Step 3: Implement profile, job, match, plan, report routers**

Create `/Users/sss/careeragent/backend/app/api/profiles.py`:

```python
from fastapi import APIRouter

from app.agents.profile import parse_resume_text
from app.schemas.profiles import ParseResumeRequest, ProfileResponse

router = APIRouter(prefix="/api/profiles", tags=["profiles"])


@router.post("/parse-resume", response_model=ProfileResponse)
def parse_resume(request: ParseResumeRequest) -> ProfileResponse:
    profile = parse_resume_text(profile_id="runtime-profile", resume_text=request.resume_text)
    return ProfileResponse(profile=profile)
```

Create `/Users/sss/careeragent/backend/app/api/jobs.py`:

```python
from fastapi import APIRouter

from app.agents.job import analyze_job_deterministic
from app.schemas.jobs import AnalyzeJobRequest, JobProfileResponse

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("/analyze", response_model=JobProfileResponse)
def analyze_job(request: AnalyzeJobRequest) -> JobProfileResponse:
    return JobProfileResponse(job=analyze_job_deterministic(title=request.title, jd_text=request.jd_text))
```

Create `/Users/sss/careeragent/backend/app/api/matches.py`:

```python
from fastapi import APIRouter
from pydantic import BaseModel

from app.agents.job import analyze_job_deterministic
from app.agents.match import match_profile_to_job
from app.agents.profile import parse_resume_text
from app.schemas.matches import MatchResult

router = APIRouter(prefix="/api/matches", tags=["matches"])


class MatchRequest(BaseModel):
    profile_id: str
    job_id: str


@router.post("", response_model=MatchResult)
def create_match(request: MatchRequest) -> MatchResult:
    profile = parse_resume_text(profile_id=request.profile_id, resume_text="Python FastAPI LangGraph")
    job = analyze_job_deterministic(title="Agent 开发工程师")
    return match_profile_to_job(profile=profile, job=job)
```

Create `/Users/sss/careeragent/backend/app/api/plans.py`:

```python
from fastapi import APIRouter
from pydantic import BaseModel

from app.agents.planning import build_plan
from app.schemas.plans import CareerPlan

router = APIRouter(prefix="/api/plans", tags=["plans"])


class PlanRequest(BaseModel):
    profile_id: str
    job_id: str


@router.post("", response_model=CareerPlan)
def create_plan(request: PlanRequest) -> CareerPlan:
    return build_plan(profile_id=request.profile_id, job_id=request.job_id, gaps=["测试评估", "记忆设计"])
```

Create `/Users/sss/careeragent/backend/app/api/reports.py`:

```python
from fastapi import APIRouter
from pydantic import BaseModel

from app.agents.report import build_markdown_report
from app.schemas.reports import ReportRecord

router = APIRouter(prefix="/api/reports", tags=["reports"])


class ReportRequest(BaseModel):
    profile_id: str
    job_id: str


@router.post("", response_model=ReportRecord)
def create_report(request: ReportRequest) -> ReportRecord:
    markdown = build_markdown_report(
        title="Markdown 职业发展报告",
        sections={
            "职业画像": f"Profile: {request.profile_id}",
            "目标岗位": f"Job: {request.job_id}",
            "下一步": "完成任务训练和模拟面试。",
        },
    )
    return ReportRecord(id=f"report-{request.profile_id}-{request.job_id}", profile_id=request.profile_id, markdown=markdown)
```

Create empty routers with valid prefixes for training, interviews, conversations:

```python
# backend/app/api/training.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/training", tags=["training"])
```

```python
# backend/app/api/interviews.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/interviews", tags=["interviews"])
```

```python
# backend/app/api/conversations.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/conversations", tags=["conversations"])
```

Create `/Users/sss/careeragent/backend/app/api/__init__.py`:

```python
"""FastAPI routers."""
```

- [ ] **Step 4: Include routers in app**

Modify `/Users/sss/careeragent/backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import conversations, interviews, jobs, matches, plans, profiles, reports, training

app = FastAPI(title="CareerAgent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profiles.router)
app.include_router(jobs.router)
app.include_router(matches.router)
app.include_router(plans.router)
app.include_router(training.router)
app.include_router(interviews.router)
app.include_router(conversations.router)
app.include_router(reports.router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 5: Run API tests**

Run:

```bash
cd /Users/sss/careeragent/backend
python -m pytest tests/test_api_flow.py tests/test_health.py -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit API flow**

Run:

```bash
git add backend/app/api backend/app/main.py backend/tests/test_api_flow.py
git commit -m "feat: add core API flow"
```

Expected: commit succeeds.

## Task 8: Training, Interview, Conversation, And Markdown Export Endpoints

**Files:**
- Modify: `/Users/sss/careeragent/backend/app/api/training.py`
- Modify: `/Users/sss/careeragent/backend/app/api/interviews.py`
- Modify: `/Users/sss/careeragent/backend/app/api/conversations.py`
- Modify: `/Users/sss/careeragent/backend/app/api/reports.py`
- Test: `/Users/sss/careeragent/backend/tests/test_api_flow.py`

- [ ] **Step 1: Extend API test with training and interview**

Append to `/Users/sss/careeragent/backend/tests/test_api_flow.py`:

```python

def test_training_interview_conversation_and_markdown_export() -> None:
    client = TestClient(app)

    task_response = client.post("/api/training/tasks", json={"job_id": "agent-developer"})
    assert task_response.status_code == 200
    task_id = task_response.json()["id"]

    submission_response = client.post(
        "/api/training/submissions",
        json={"task_id": task_id, "answer": "我会设计 Supervisor、Memory、Profile、Job、Match 多 Agent 协作，并说明 handoff 条件。"},
    )
    assert submission_response.status_code == 200
    assert submission_response.json()["score"] >= 60

    interview_response = client.post("/api/interviews/sessions", json={"profile_id": "p1", "job_id": "agent-developer"})
    assert interview_response.status_code == 200
    session_id = interview_response.json()["id"]

    message_response = client.post(f"/api/interviews/{session_id}/messages", json={"content": "我做过校园问答机器人。"})
    assert message_response.status_code == 200
    assert len(message_response.json()["messages"]) >= 3

    conversation_response = client.post("/api/conversations/match/messages", json={"content": "为什么我还需要补测试评估？"})
    assert conversation_response.status_code == 200
    assert conversation_response.json()["scope"] == "match"

    markdown_response = client.get("/api/reports/report-runtime-profile-agent-developer/markdown")
    assert markdown_response.status_code == 200
    assert markdown_response.text.startswith("#")
```

- [ ] **Step 2: Run extended API test and verify it fails**

Run:

```bash
cd /Users/sss/careeragent/backend
python -m pytest tests/test_api_flow.py::test_training_interview_conversation_and_markdown_export -v
```

Expected: FAIL with route not found.

- [ ] **Step 3: Implement training endpoints**

Modify `/Users/sss/careeragent/backend/app/api/training.py`:

```python
from fastapi import APIRouter
from pydantic import BaseModel

from app.agents.training import score_submission
from app.schemas.training import TrainingSubmission, TrainingTask

router = APIRouter(prefix="/api/training", tags=["training"])


class TaskRequest(BaseModel):
    job_id: str


class SubmissionRequest(BaseModel):
    task_id: str
    answer: str


@router.post("/tasks", response_model=TrainingTask)
def create_task(request: TaskRequest) -> TrainingTask:
    return TrainingTask(
        id="task-agent-workflow-design",
        job_id=request.job_id,
        title="设计职业规划 Agent 工作流",
        scenario="为学生职业规划系统设计多 Agent 工作流。",
        rubric=["需求理解", "Agent 边界", "记忆设计", "工具调用", "可测试性"],
    )


@router.post("/submissions", response_model=TrainingSubmission)
def submit_answer(request: SubmissionRequest) -> TrainingSubmission:
    task = TrainingTask(id=request.task_id, job_id="agent-developer", title="设计职业规划 Agent 工作流", scenario="", rubric=[])
    return score_submission(task=task, answer=request.answer)
```

- [ ] **Step 4: Implement interview and conversation endpoints**

Modify `/Users/sss/careeragent/backend/app/api/interviews.py`:

```python
from fastapi import APIRouter
from pydantic import BaseModel

from app.agents.interview import start_interview
from app.schemas.interviews import InterviewMessage, InterviewSession

router = APIRouter(prefix="/api/interviews", tags=["interviews"])

SESSIONS: dict[str, InterviewSession] = {}


class StartInterviewRequest(BaseModel):
    profile_id: str
    job_id: str


class InterviewAnswerRequest(BaseModel):
    content: str


@router.post("/sessions", response_model=InterviewSession)
def create_session(request: StartInterviewRequest) -> InterviewSession:
    session = start_interview(session_id=f"interview-{request.profile_id}-{request.job_id}", profile_id=request.profile_id, job_id=request.job_id)
    SESSIONS[session.id] = session
    return session


@router.post("/{session_id}/messages", response_model=InterviewSession)
def add_message(session_id: str, request: InterviewAnswerRequest) -> InterviewSession:
    session = SESSIONS[session_id]
    session.messages.append(InterviewMessage(role="user", content=request.content))
    session.messages.append(InterviewMessage(role="assistant", content="请补充你在项目中的技术选型、工具调用和评估方式。"))
    return session
```

Modify `/Users/sss/careeragent/backend/app/api/conversations.py`:

```python
from fastapi import APIRouter
from pydantic import BaseModel

from app.schemas.conversations import ConversationMessage, ConversationSession

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


class ConversationRequest(BaseModel):
    content: str


@router.post("/{scope}/messages", response_model=ConversationSession)
def send_message(scope: str, request: ConversationRequest) -> ConversationSession:
    return ConversationSession(
        id=f"conversation-{scope}",
        scope=scope,
        messages=[
            ConversationMessage(role="user", content=request.content),
            ConversationMessage(role="assistant", content="我会结合当前画像、岗位和记忆给出场景化回答。"),
        ],
    )
```

- [ ] **Step 5: Implement Markdown export endpoint**

Modify `/Users/sss/careeragent/backend/app/api/reports.py` by adding:

```python
from fastapi.responses import PlainTextResponse


@router.get("/{report_id}/markdown", response_class=PlainTextResponse)
def export_markdown(report_id: str) -> str:
    return "# CareerAgent 职业发展报告\n\n这是本地演示版 Markdown 报告。\n"
```

- [ ] **Step 6: Run extended API test**

Run:

```bash
cd /Users/sss/careeragent/backend
python -m pytest tests/test_api_flow.py -v
```

Expected: all API tests pass.

- [ ] **Step 7: Commit training/interview/conversation endpoints**

Run:

```bash
git add backend/app/api backend/tests/test_api_flow.py
git commit -m "feat: add training interview and conversation APIs"
```

Expected: commit succeeds.

## Task 9: Frontend Shell, Routing, Stores, And API Client

**Files:**
- Create: `/Users/sss/careeragent/frontend/src/types/api.ts`
- Create: `/Users/sss/careeragent/frontend/src/api/client.ts`
- Create: `/Users/sss/careeragent/frontend/src/router.ts`
- Create: `/Users/sss/careeragent/frontend/src/components/AppShell.vue`
- Create: `/Users/sss/careeragent/frontend/src/components/AgentChatPanel.vue`
- Create: `/Users/sss/careeragent/frontend/src/stores/profile.ts`
- Create: `/Users/sss/careeragent/frontend/src/stores/job.ts`
- Create: `/Users/sss/careeragent/frontend/src/stores/conversation.ts`
- Create: `/Users/sss/careeragent/frontend/src/stores/report.ts`
- Modify: `/Users/sss/careeragent/frontend/src/main.ts`
- Modify: `/Users/sss/careeragent/frontend/src/App.vue`

- [ ] **Step 1: Add frontend shared types**

Create `/Users/sss/careeragent/frontend/src/types/api.ts`:

```ts
export interface StudentProfile {
  id: string;
  name: string;
  major: string;
  skills: string[];
  projects: string[];
  preferences: string[];
  target_roles: string[];
}

export interface JobProfile {
  id: string;
  title: string;
  responsibilities: string[];
  required_skills: string[];
  tools: string[];
  evaluation_dimensions: string[];
}

export interface MatchResult {
  id: string;
  score: number;
  strengths: string[];
  gaps: string[];
  evidence: string[];
  priorities: string[];
}
```

- [ ] **Step 2: Add API client**

Create `/Users/sss/careeragent/frontend/src/api/client.ts`:

```ts
export async function apiPost<TResponse, TBody>(path: string, body: TBody): Promise<TResponse> {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }
  return response.json() as Promise<TResponse>;
}

export async function apiGetText(path: string): Promise<string> {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }
  return response.text();
}
```

- [ ] **Step 3: Add stores**

Create `/Users/sss/careeragent/frontend/src/stores/profile.ts`:

```ts
import { defineStore } from "pinia";
import type { StudentProfile } from "../types/api";

export const useProfileStore = defineStore("profile", {
  state: () => ({ current: null as StudentProfile | null }),
  actions: {
    setProfile(profile: StudentProfile) {
      this.current = profile;
    }
  }
});
```

Create job, conversation, and report stores with these exact contents:

```ts
// frontend/src/stores/job.ts
import { defineStore } from "pinia";
import type { JobProfile, MatchResult } from "../types/api";

export const useJobStore = defineStore("job", {
  state: () => ({ current: null as JobProfile | null, match: null as MatchResult | null }),
  actions: {
    setJob(job: JobProfile) { this.current = job; },
    setMatch(match: MatchResult) { this.match = match; }
  }
});
```

```ts
// frontend/src/stores/conversation.ts
import { defineStore } from "pinia";

export const useConversationStore = defineStore("conversation", {
  state: () => ({ messages: [] as Array<{ role: string; content: string }> }),
  actions: {
    setMessages(messages: Array<{ role: string; content: string }>) { this.messages = messages; }
  }
});
```

```ts
// frontend/src/stores/report.ts
import { defineStore } from "pinia";

export const useReportStore = defineStore("report", {
  state: () => ({ markdown: "" }),
  actions: {
    setMarkdown(markdown: string) { this.markdown = markdown; }
  }
});
```

- [ ] **Step 4: Add shell and router**

Create `/Users/sss/careeragent/frontend/src/router.ts`:

```ts
import { createRouter, createWebHistory } from "vue-router";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", component: () => import("./views/DashboardView.vue") },
    { path: "/profile", component: () => import("./views/ProfileView.vue") },
    { path: "/match", component: () => import("./views/JobMatchView.vue") },
    { path: "/plan", component: () => import("./views/PlanView.vue") },
    { path: "/training", component: () => import("./views/TrainingView.vue") },
    { path: "/interview", component: () => import("./views/InterviewView.vue") },
    { path: "/report", component: () => import("./views/ReportView.vue") }
  ]
});
```

Create `/Users/sss/careeragent/frontend/src/components/AppShell.vue`:

```vue
<template>
  <el-container class="shell">
    <el-aside width="230px" class="side">
      <h1>CareerAgent</h1>
      <router-link to="/">首页总览</router-link>
      <router-link to="/profile">职业画像</router-link>
      <router-link to="/match">岗位匹配</router-link>
      <router-link to="/plan">路径规划</router-link>
      <router-link to="/training">任务舱</router-link>
      <router-link to="/interview">模拟面试</router-link>
      <router-link to="/report">个人报告</router-link>
    </el-aside>
    <el-main class="main">
      <router-view />
    </el-main>
    <el-aside width="340px" class="chat">
      <AgentChatPanel />
    </el-aside>
  </el-container>
</template>

<script setup lang="ts">
import AgentChatPanel from "./AgentChatPanel.vue";
</script>

<style scoped>
.shell { min-height: 100vh; background: #f7f9fb; }
.side { padding: 24px; background: #172337; color: white; }
.side a { display: block; color: #dce7f3; margin: 16px 0; text-decoration: none; }
.main { padding: 24px; }
.chat { border-left: 1px solid #d8e1ea; background: #fff; padding: 20px; }
</style>
```

Create `/Users/sss/careeragent/frontend/src/components/AgentChatPanel.vue`:

```vue
<template>
  <section>
    <h2>场景 Agent</h2>
    <el-input v-model="draft" type="textarea" :rows="4" placeholder="继续追问当前页面内容" />
    <el-button type="primary" class="send" @click="send">发送</el-button>
    <div v-for="(message, index) in store.messages" :key="index" class="message">
      <strong>{{ message.role }}</strong>
      <p>{{ message.content }}</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { apiPost } from "../api/client";
import { useConversationStore } from "../stores/conversation";

const draft = ref("");
const store = useConversationStore();

async function send() {
  const response = await apiPost<{ messages: Array<{ role: string; content: string }> }, { content: string }>(
    "/api/conversations/general/messages",
    { content: draft.value }
  );
  store.setMessages(response.messages);
  draft.value = "";
}
</script>

<style scoped>
.send { margin-top: 12px; width: 100%; }
.message { border-top: 1px solid #edf1f5; padding: 12px 0; }
</style>
```

Modify `/Users/sss/careeragent/frontend/src/main.ts` to use router:

```ts
import ElementPlus from "element-plus";
import "element-plus/dist/index.css";
import { createPinia } from "pinia";
import { createApp } from "vue";
import App from "./App.vue";
import { router } from "./router";

createApp(App).use(createPinia()).use(router).use(ElementPlus).mount("#app");
```

Modify `/Users/sss/careeragent/frontend/src/App.vue`:

```vue
<template>
  <AppShell />
</template>

<script setup lang="ts">
import AppShell from "./components/AppShell.vue";
</script>
```

- [ ] **Step 5: Commit frontend shell**

Run:

```bash
git add frontend/src
git commit -m "feat: add frontend app shell"
```

Expected: commit succeeds.

## Task 10: Frontend Views For The MVP Loop

**Files:**
- Create: `/Users/sss/careeragent/frontend/src/views/*.vue`
- Create: `/Users/sss/careeragent/frontend/src/components/*.vue`
- Test: `/Users/sss/careeragent/frontend/tests/profile.spec.ts`
- Test: `/Users/sss/careeragent/frontend/tests/job-match.spec.ts`
- Test: `/Users/sss/careeragent/frontend/tests/training.spec.ts`
- Test: `/Users/sss/careeragent/frontend/tests/interview.spec.ts`

- [ ] **Step 1: Create Profile view**

Create `/Users/sss/careeragent/frontend/src/views/ProfileView.vue`:

```vue
<template>
  <section>
    <h2>职业画像</h2>
    <el-input v-model="resumeText" type="textarea" :rows="8" placeholder="粘贴简历文本" />
    <el-button type="primary" @click="parseResume">生成画像草稿</el-button>
    <el-card v-if="profile" class="result">
      <h3>{{ profile.name }}</h3>
      <p>技能：{{ profile.skills.join("、") }}</p>
    </el-card>
  </section>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { apiPost } from "../api/client";
import { useProfileStore } from "../stores/profile";
import type { StudentProfile } from "../types/api";

const resumeText = ref("我会 Python FastAPI LangGraph");
const store = useProfileStore();
const profile = ref<StudentProfile | null>(null);

async function parseResume() {
  const response = await apiPost<{ profile: StudentProfile }, { resume_text: string }>(
    "/api/profiles/parse-resume",
    { resume_text: resumeText.value }
  );
  profile.value = response.profile;
  store.setProfile(response.profile);
}
</script>

<style scoped>
.result { margin-top: 16px; }
</style>
```

- [ ] **Step 2: Create Job Match view**

Create `/Users/sss/careeragent/frontend/src/views/JobMatchView.vue`:

```vue
<template>
  <section>
    <h2>岗位匹配</h2>
    <el-input v-model="title" placeholder="目标岗位" />
    <el-input v-model="jdText" type="textarea" :rows="5" placeholder="可选：粘贴 JD" />
    <el-button type="primary" @click="analyze">分析岗位</el-button>
    <el-button @click="match">生成匹配</el-button>
    <el-card v-if="job" class="result"><h3>{{ job.title }}</h3><p>{{ job.required_skills.join("、") }}</p></el-card>
    <el-card v-if="matchResult" class="result"><h3>匹配度 {{ matchResult.score }}</h3><p>短板：{{ matchResult.gaps.join("、") }}</p></el-card>
  </section>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { apiPost } from "../api/client";
import { useJobStore } from "../stores/job";
import { useProfileStore } from "../stores/profile";
import type { JobProfile, MatchResult } from "../types/api";

const title = ref("Agent 开发工程师");
const jdText = ref("");
const job = ref<JobProfile | null>(null);
const matchResult = ref<MatchResult | null>(null);
const jobStore = useJobStore();
const profileStore = useProfileStore();

async function analyze() {
  const response = await apiPost<{ job: JobProfile }, { title: string; jd_text: string; source: string }>("/api/jobs/analyze", {
    title: title.value,
    jd_text: jdText.value,
    source: "custom"
  });
  job.value = response.job;
  jobStore.setJob(response.job);
}

async function match() {
  const response = await apiPost<MatchResult, { profile_id: string; job_id: string }>("/api/matches", {
    profile_id: profileStore.current?.id || "runtime-profile",
    job_id: job.value?.id || "agent-developer"
  });
  matchResult.value = response;
  jobStore.setMatch(response);
}
</script>

<style scoped>
.result { margin-top: 16px; }
</style>
```

- [ ] **Step 3: Create reusable workflow components**

Create `/Users/sss/careeragent/frontend/src/components/ResumeUploader.vue`:

```vue
<template>
  <el-input :model-value="modelValue" type="textarea" :rows="6" placeholder="粘贴简历文本" @update:model-value="$emit('update:modelValue', String($event))" />
</template>

<script setup lang="ts">
defineProps<{ modelValue: string }>();
defineEmits<{ "update:modelValue": [value: string] }>();
</script>
```

Create `/Users/sss/careeragent/frontend/src/components/ProfileEditor.vue`:

```vue
<template>
  <el-card>
    <h3>{{ name }}</h3>
    <p>专业：{{ major || "待补充" }}</p>
    <p>技能：{{ skills.join("、") || "待补充" }}</p>
  </el-card>
</template>

<script setup lang="ts">
defineProps<{ name: string; major: string; skills: string[] }>();
</script>
```

Create `/Users/sss/careeragent/frontend/src/components/SkillEvidenceList.vue`:

```vue
<template>
  <el-card>
    <h3>能力证据链</h3>
    <el-empty v-if="items.length === 0" description="暂无证据" />
    <el-tag v-for="item in items" v-else :key="item" class="tag">{{ item }}</el-tag>
  </el-card>
</template>

<script setup lang="ts">
defineProps<{ items: string[] }>();
</script>

<style scoped>
.tag { margin: 4px; }
</style>
```

Create `/Users/sss/careeragent/frontend/src/components/JobSelector.vue`:

```vue
<template>
  <el-select :model-value="modelValue" @update:model-value="$emit('update:modelValue', String($event))">
    <el-option label="Agent 开发工程师" value="Agent 开发工程师" />
    <el-option label="AI 应用开发工程师" value="AI 应用开发工程师" />
    <el-option label="Python 后端开发工程师" value="Python 后端开发工程师" />
  </el-select>
</template>

<script setup lang="ts">
defineProps<{ modelValue: string }>();
defineEmits<{ "update:modelValue": [value: string] }>();
</script>
```

Create `/Users/sss/careeragent/frontend/src/components/CustomJobForm.vue`:

```vue
<template>
  <div class="custom-job">
    <el-input :model-value="title" placeholder="岗位名称" @update:model-value="$emit('update:title', String($event))" />
    <el-input :model-value="jdText" type="textarea" :rows="5" placeholder="粘贴岗位 JD" @update:model-value="$emit('update:jdText', String($event))" />
  </div>
</template>

<script setup lang="ts">
defineProps<{ title: string; jdText: string }>();
defineEmits<{ "update:title": [value: string]; "update:jdText": [value: string] }>();
</script>

<style scoped>
.custom-job { display: grid; gap: 12px; }
</style>
```

Create `/Users/sss/careeragent/frontend/src/components/MatchRadar.vue`:

```vue
<template>
  <el-card>
    <h3>匹配度</h3>
    <el-progress :percentage="score" />
  </el-card>
</template>

<script setup lang="ts">
defineProps<{ score: number }>();
</script>
```

Create `/Users/sss/careeragent/frontend/src/components/GapAnalysisCard.vue`:

```vue
<template>
  <el-card>
    <h3>能力短板</h3>
    <el-tag v-for="gap in gaps" :key="gap" type="warning" class="tag">{{ gap }}</el-tag>
  </el-card>
</template>

<script setup lang="ts">
defineProps<{ gaps: string[] }>();
</script>

<style scoped>
.tag { margin: 4px; }
</style>
```

Create `/Users/sss/careeragent/frontend/src/components/PlanTimeline.vue`:

```vue
<template>
  <el-timeline>
    <el-timeline-item v-for="stage in stages" :key="stage.title" :timestamp="stage.duration">
      <strong>{{ stage.title }}</strong>
      <p>{{ stage.actions.join("；") }}</p>
    </el-timeline-item>
  </el-timeline>
</template>

<script setup lang="ts">
defineProps<{ stages: Array<{ title: string; duration: string; actions: string[] }> }>();
</script>
```

Create `/Users/sss/careeragent/frontend/src/components/TrainingTaskCard.vue`:

```vue
<template>
  <el-card>
    <h3>{{ title }}</h3>
    <p>{{ scenario }}</p>
    <el-tag v-for="item in rubric" :key="item" class="tag">{{ item }}</el-tag>
  </el-card>
</template>

<script setup lang="ts">
defineProps<{ title: string; scenario: string; rubric: string[] }>();
</script>

<style scoped>
.tag { margin: 4px; }
</style>
```

Create `/Users/sss/careeragent/frontend/src/components/InterviewThread.vue`:

```vue
<template>
  <el-card>
    <h3>面试对话</h3>
    <div v-for="(message, index) in messages" :key="index">
      <strong>{{ message.role }}</strong>
      <p>{{ message.content }}</p>
    </div>
  </el-card>
</template>

<script setup lang="ts">
defineProps<{ messages: Array<{ role: string; content: string }> }>();
</script>
```

Create `/Users/sss/careeragent/frontend/src/components/MarkdownReport.vue`:

```vue
<template>
  <el-card>
    <h3>Markdown 报告</h3>
    <pre>{{ markdown }}</pre>
  </el-card>
</template>

<script setup lang="ts">
defineProps<{ markdown: string }>();
</script>
```

- [ ] **Step 4: Create remaining views**

Create Dashboard, Plan, Training, Interview, and Report views with these exact contents:

```vue
<!-- frontend/src/views/DashboardView.vue -->
<template><section><h2>首页总览</h2><p>当前目标：Agent 开发工程师。请从职业画像开始。</p></section></template>
```

```vue
<!-- frontend/src/views/PlanView.vue -->
<template><section><h2>路径规划</h2><el-button @click="createPlan">生成三阶段路线</el-button><pre>{{ plan }}</pre></section></template>
<script setup lang="ts">
import { ref } from "vue";
import { apiPost } from "../api/client";
const plan = ref("");
async function createPlan() {
  const response = await apiPost<unknown, { profile_id: string; job_id: string }>("/api/plans", { profile_id: "runtime-profile", job_id: "agent-developer" });
  plan.value = JSON.stringify(response, null, 2);
}
</script>
```

```vue
<!-- frontend/src/views/TrainingView.vue -->
<template><section><h2>虚拟职场任务舱</h2><el-button @click="loadTask">生成任务</el-button><el-input v-model="answer" type="textarea" :rows="6" /><el-button @click="submit">提交评分</el-button><pre>{{ result }}</pre></section></template>
<script setup lang="ts">
import { ref } from "vue";
import { apiPost } from "../api/client";
const taskId = ref("");
const answer = ref("我会设计 Supervisor、Memory、Profile、Job、Match 多 Agent 协作。");
const result = ref("");
async function loadTask() {
  const task = await apiPost<{ id: string }, { job_id: string }>("/api/training/tasks", { job_id: "agent-developer" });
  taskId.value = task.id;
  result.value = JSON.stringify(task, null, 2);
}
async function submit() {
  const response = await apiPost<unknown, { task_id: string; answer: string }>("/api/training/submissions", { task_id: taskId.value || "task-agent-workflow-design", answer: answer.value });
  result.value = JSON.stringify(response, null, 2);
}
</script>
```

```vue
<!-- frontend/src/views/InterviewView.vue -->
<template><section><h2>模拟面试</h2><el-button @click="start">开始面试</el-button><el-input v-model="answer" /><el-button @click="send">回答</el-button><pre>{{ session }}</pre></section></template>
<script setup lang="ts">
import { ref } from "vue";
import { apiPost } from "../api/client";
const sessionId = ref("");
const answer = ref("我做过校园问答机器人。");
const session = ref("");
async function start() {
  const response = await apiPost<{ id: string }, { profile_id: string; job_id: string }>("/api/interviews/sessions", { profile_id: "runtime-profile", job_id: "agent-developer" });
  sessionId.value = response.id;
  session.value = JSON.stringify(response, null, 2);
}
async function send() {
  const response = await apiPost<unknown, { content: string }>(`/api/interviews/${sessionId.value}/messages`, { content: answer.value });
  session.value = JSON.stringify(response, null, 2);
}
</script>
```

```vue
<!-- frontend/src/views/ReportView.vue -->
<template><section><h2>个人报告</h2><el-button @click="load">生成 Markdown</el-button><pre>{{ markdown }}</pre></section></template>
<script setup lang="ts">
import { ref } from "vue";
import { apiGetText } from "../api/client";
const markdown = ref("");
async function load() {
  markdown.value = await apiGetText("/api/reports/report-runtime-profile-agent-developer/markdown");
}
</script>
```

- [ ] **Step 5: Add frontend smoke tests**

Create `/Users/sss/careeragent/frontend/tests/profile.spec.ts`:

```ts
import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import ProfileView from "../src/views/ProfileView.vue";

describe("ProfileView", () => {
  it("renders profile heading", () => {
    const wrapper = mount(ProfileView);
    expect(wrapper.text()).toContain("职业画像");
  });
});
```

Create `/Users/sss/careeragent/frontend/tests/job-match.spec.ts`:

```ts
import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import JobMatchView from "../src/views/JobMatchView.vue";

describe("JobMatchView", () => {
  it("renders job match heading", () => {
    const wrapper = mount(JobMatchView);
    expect(wrapper.text()).toContain("岗位匹配");
  });
});
```

Create `/Users/sss/careeragent/frontend/tests/training.spec.ts`:

```ts
import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import TrainingView from "../src/views/TrainingView.vue";

describe("TrainingView", () => {
  it("renders training heading", () => {
    const wrapper = mount(TrainingView);
    expect(wrapper.text()).toContain("虚拟职场任务舱");
  });
});
```

Create `/Users/sss/careeragent/frontend/tests/interview.spec.ts`:

```ts
import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import InterviewView from "../src/views/InterviewView.vue";

describe("InterviewView", () => {
  it("renders interview heading", () => {
    const wrapper = mount(InterviewView);
    expect(wrapper.text()).toContain("模拟面试");
  });
});
```

- [ ] **Step 6: Run frontend build and test**

Run:

```bash
cd /Users/sss/careeragent/frontend
npm install
npm run build
npm run test
```

Expected: build succeeds and tests pass.

- [ ] **Step 7: Commit frontend MVP views**

Run:

```bash
git add frontend
git commit -m "feat: add student MVP frontend views"
```

Expected: commit succeeds.

## Task 11: LangGraph Workflow Integration

**Files:**
- Create: `/Users/sss/careeragent/backend/app/graphs/workflow.py`
- Create: `/Users/sss/careeragent/backend/app/graphs/__init__.py`
- Modify: `/Users/sss/careeragent/backend/app/api/conversations.py`
- Test: `/Users/sss/careeragent/backend/tests/test_agents.py`

- [ ] **Step 1: Add workflow routing test**

Append to `/Users/sss/careeragent/backend/tests/test_agents.py`:

```python

def test_workflow_routes_match_message() -> None:
    from app.graphs.workflow import run_supervisor_turn

    result = run_supervisor_turn("我为什么和 Agent 开发岗位不匹配？")

    assert result["next_agent"] == "match"
```

- [ ] **Step 2: Run workflow test and verify it fails**

Run:

```bash
cd /Users/sss/careeragent/backend
python -m pytest tests/test_agents.py::test_workflow_routes_match_message -v
```

Expected: FAIL with missing `app.graphs.workflow`.

- [ ] **Step 3: Implement workflow wrapper**

Create `/Users/sss/careeragent/backend/app/graphs/workflow.py`:

```python
from app.agents.supervisor import route_intent


def run_supervisor_turn(message: str) -> dict[str, str]:
    decision = route_intent(message)
    return {"next_agent": decision.next_agent, "reason": decision.reason}
```

Create `/Users/sss/careeragent/backend/app/graphs/__init__.py`:

```python
"""LangGraph workflow entry points."""
```

This task keeps `run_supervisor_turn()` as the public workflow entry point. The implementation is deterministic for the MVP plan so tests and API behavior are stable before real model calls are enabled.

- [ ] **Step 4: Route scenario conversation through workflow**

Modify `/Users/sss/careeragent/backend/app/api/conversations.py`:

```python
from fastapi import APIRouter
from pydantic import BaseModel

from app.graphs.workflow import run_supervisor_turn
from app.schemas.conversations import ConversationMessage, ConversationSession

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


class ConversationRequest(BaseModel):
    content: str


@router.post("/{scope}/messages", response_model=ConversationSession)
def send_message(scope: str, request: ConversationRequest) -> ConversationSession:
    decision = run_supervisor_turn(request.content)
    return ConversationSession(
        id=f"conversation-{scope}",
        scope=scope,
        messages=[
            ConversationMessage(role="user", content=request.content),
            ConversationMessage(role="assistant", content=f"已交给 {decision['next_agent']} Agent：{decision['reason']}"),
        ],
    )
```

- [ ] **Step 5: Run workflow tests**

Run:

```bash
cd /Users/sss/careeragent/backend
python -m pytest tests/test_agents.py tests/test_api_flow.py -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit workflow integration**

Run:

```bash
git add backend/app/graphs backend/app/api/conversations.py backend/tests/test_agents.py
git commit -m "feat: add supervisor workflow entry point"
```

Expected: commit succeeds.

## Task 12: Full Local Verification And Documentation

**Files:**
- Modify: `/Users/sss/careeragent/README.md`
- Test commands: backend pytest, frontend build, frontend tests, manual browser smoke test.

- [ ] **Step 1: Update README with run instructions**

Modify `/Users/sss/careeragent/README.md`:

```markdown
# careeragent

CareerAgent 是一个面向学生个人职业发展的多智能体 MVP。本地演示版使用 FastAPI + Vue 3 + LangGraph 思路，支持职业画像、岗位匹配、路径规划、任务训练、模拟面试和 Markdown 报告。

## Backend

```bash
cd backend
python -m pytest -v
uvicorn app.main:app --reload
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

浏览器打开 http://localhost:5173。

## Demo Flow

1. 职业画像：粘贴简历文本并生成画像。
2. 岗位匹配：选择或输入 Agent 开发工程师岗位。
3. 路径规划：生成三阶段路线。
4. 任务舱：生成任务并提交答案评分。
5. 模拟面试：开始文字面试并回答追问。
6. 个人报告：导出 Markdown 报告。
```

- [ ] **Step 2: Run backend verification**

Run:

```bash
cd /Users/sss/careeragent/backend
python -m pytest -v
```

Expected: all backend tests pass.

- [ ] **Step 3: Run frontend verification**

Run:

```bash
cd /Users/sss/careeragent/frontend
npm run build
npm run test
```

Expected: build succeeds and tests pass.

- [ ] **Step 4: Manual browser smoke test**

Run two servers:

```bash
cd /Users/sss/careeragent/backend
uvicorn app.main:app --reload
```

```bash
cd /Users/sss/careeragent/frontend
npm run dev
```

Open `http://localhost:5173` and verify:

- Left navigation shows all seven pages.
- Profile page can generate a profile draft.
- Job match page can analyze Agent developer and generate match score.
- Plan page can generate stages.
- Training page can generate a task and score an answer.
- Interview page can start a session and add one answer.
- Report page can load Markdown.
- Right-side Agent panel can send a message and receive a scoped response.

- [ ] **Step 5: Commit documentation**

Run:

```bash
git add README.md
git commit -m "docs: add local demo instructions"
```

Expected: commit succeeds.

## Self-Review Checklist

- [ ] Spec coverage: Tasks cover project scaffold, JSON storage, skills, model providers, memory, agents, APIs, frontend pages, workflow, report export, and verification.
- [ ] Placeholder scan: The plan contains no placeholder tokens or unbounded error-handling instructions.
- [ ] Type consistency: Backend schema names in tests match implementation snippets.
- [ ] Execution boundary: This plan does not start implementation; it prepares the next phase.
