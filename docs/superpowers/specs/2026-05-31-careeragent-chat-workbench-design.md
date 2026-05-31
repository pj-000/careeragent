# CareerAgent Chat Workbench v3.1 Design

## Purpose

CareerAgent v3 turns the current fixed-step local demo into a conversational student career workbench. The user should feel they are talking with a career planning AI, similar to a ChatGPT-style web app, while the page makes the underlying multi-agent workflow visible through structured panels, artifacts, memory, and report outputs.

This phase does not replace the strict LangGraph runtime built in v2.1. It wraps that runtime in a more natural student-facing interaction model.

## Product Shape

The final page should not be a pure chat clone. It should be a split workbench:

- Main workspace: structured career outputs and task state.
- Right conversation panel: natural multi-turn dialogue with the student.
- Runtime drawer or panel: agent trace, artifacts, skills, memory, and compaction snapshots for demo and review.

The student can type natural requests such as:

- "我想转 Agent 开发，帮我规划一下。"
- "这是我的简历，帮我看看差距。"
- "我想用自己的 JD 做匹配。"
- "给我一个训练任务。"
- "继续模拟面试。"
- "导出报告。"

The system routes those messages through Supervisor and the specialist agents. The UI then updates the relevant workspace section from artifacts instead of treating the response as disposable chat text.

## Non-Goals

- No teacher dashboard, class management, or student list.
- No public cloud deployment requirement in this phase.
- No database migration; JSON remains the persistence layer.
- No PDF, Word, or OCR resume parsing in this phase. v3.1 supports pasted resume text and pasted JD text only.
- No requirement to implement streaming tokens unless it naturally fits after the core workbench is stable.
- No hidden reasoning display. The UI can show summaries, trace, selected skills, artifacts, and compaction summaries, but not private chain-of-thought.
- No mobile-first layout requirement. This phase is desktop-first for local demo and review.

## User Experience

The app opens directly into the workbench. It should not open with a marketing landing page.

The first screen contains:

- A compact thread header with student name or current thread id.
- A main workspace with tabs or segmented navigation:
  - 总览
  - 画像
  - 岗位
  - 匹配
  - 规划
  - 训练
  - 面试
  - 报告
- A persistent conversation panel where the student can type messages.
- A runtime visibility panel or drawer for demo mode.

The workbench starts with sample prompts and optional sample student/job presets. After the first user message, the conversation and workspace are driven by `/api/runs`.

## Active Workspace Context

Free-form chat can create multiple job, match, plan, training, interview, and report artifacts inside one thread. The workbench must not simply render the latest artifact by kind. It must render the active artifact chain selected by an explicit workspace context.

Minimum schema:

```text
WorkspaceContext {
  thread_id: string
  active_goal: string
  active_profile_id?: string
  active_job_analysis_id?: string
  active_match_id?: string
  active_plan_id?: string
  active_training_result_id?: string
  active_interview_summary_id?: string
  active_report_id?: string
  active_compaction_snapshot_id?: string
  updated_by_run_id: string
  updated_at: string
}
```

The Supervisor and business agents update this context after each run. If the student switches target roles, the system can start a new active chain without deleting historical artifacts. The report builder reads the active chain, not the latest artifact of each kind.

## Main Workspace

The workspace renders the artifacts referenced by the active workspace context:

- `profile`: student summary, skills, experience signals, evidence notes.
- `job_analysis`: target role, responsibilities, required skills, risks.
- `match`: match score, strengths, gaps, priority gaps.
- `plan`: milestones, timeline, next actions.
- `training_result`: task, rubric, student submission, feedback, score.
- `interview_summary`: current question, answers, feedback, three-turn progress.
- `report`: Markdown preview and export action.
- `compaction_snapshot`: summarized goal, confirmed facts, artifact refs, next actions.

Empty states should invite the student to ask the assistant, not explain implementation details.

## Conversation Panel

The conversation panel is the primary input surface. It should support:

- Free-form student message input.
- Enter-to-send and button-to-send.
- Visible user and assistant messages.
- Quick prompt chips for common actions:
  - 生成画像
  - 分析自定义岗位
  - 做匹配诊断
  - 生成三个月计划
  - 开始训练任务
  - 继续面试
  - 导出报告
- A small indicator for the last business agent, separate from the final runtime node.

The assistant response should be a user-facing summary derived from the latest run. It can reference created artifacts and next actions. It should not simply expose raw JSON.

Messages are durable JSON records, not frontend-only state:

```text
ConversationMessage {
  id: string
  thread_id: string
  role: "user" | "assistant" | "system"
  content: string
  run_id?: string
  created_at: string
  artifact_refs: string[]
  last_business_agent?: string
  current_runtime_node?: string
  warnings?: string[]
}
```

`POST /api/runs` saves the user message, executes the LangGraph run, updates the active workspace context, then saves an assistant message tied to the run and created artifacts. `GET /api/threads/{thread_id}/messages` restores the visible conversation after refresh.

## Runtime Visibility

For project demonstration, the UI should make the runtime auditable without overwhelming the student view.

Add or enhance fields in API responses:

- `last_business_agent`: the specialist agent that handled the user intent.
- `current_runtime_node`: the final node reached by LangGraph, often `memory_manager`.
- `artifact_chain`: artifact summaries with `id`, `kind`, `source_agent`, `source_thread_id`, `parent_artifact_ids`, and `updated_at`.
- `compaction_snapshot`: compact public summary of the latest snapshot artifact.
- `memory_updates`: accepted, pending confirmation, and rejected memory candidates when available.

The runtime panel should show:

- 当前业务 Agent
- Runtime 节点
- Used Skills
- Artifact Chain
- Parent relationships
- Warnings
- Compaction Snapshot summary

This panel is a demo and review aid. It should be visually secondary to the student workbench.

Runtime visibility has two modes:

- Student mode: default mode. Hide the runtime drawer and show only simple progress, next actions, and recoverable errors.
- Demo mode: enabled by a local toggle or `?demo=1`. Show agent trace, artifact chain, parent relationships, skill refs, memory updates, and compaction snapshot summary.

## Backend API Direction

Keep `POST /api/runs` as the single runtime entry for messages that can trigger agent work.

Extend the response shape rather than creating separate agent-specific chat endpoints:

```text
POST /api/runs
  input:
    thread_id
    message
    optional scope

  output:
    run_id
    thread_id
    run_status
    active_agent
    last_business_agent
    current_runtime_node
    assistant_message
    supervisor_decision
    agent_trace_summary
    used_skill_refs
    artifacts
    artifact_chain
    workspace_delta
    compaction_snapshot
    blocking_reason
    missing_artifacts
    retryable
    next_actions
    warnings
```

Run status values:

```text
run_status:
  | "completed"
  | "needs_input"
  | "blocked_by_prerequisite"
  | "provider_error"
  | "permission_denied"
  | "failed"
```

`assistant_message` uses the durable `ConversationMessage` shape. `workspace_delta` describes created artifacts and the updated active workspace context:

```text
workspace_delta {
  created_artifacts: ArtifactRef[]
  updated_context: WorkspaceContext
}
```

Add read endpoints only for UI convenience:

- `GET /api/threads/{thread_id}/artifacts`
- `GET /api/threads/{thread_id}/workspace`
- `GET /api/threads/{thread_id}/messages`
- `GET /api/reports/{thread_id}/markdown`

The frontend should not call individual agents directly.

`GET /api/threads/{thread_id}/workspace` returns active-context artifacts, not latest-by-kind artifacts:

```text
{
  thread_id: string
  active_context: WorkspaceContext
  workspace_artifacts: {
    profile?: Artifact
    job_analysis?: Artifact
    match?: Artifact
    plan?: Artifact
    training_result?: Artifact
    interview_summary?: Artifact
    report?: Artifact
    compaction_snapshot?: Artifact
  }
  artifact_chain: ArtifactRef[]
}
```

## Supervisor Decision Contract

The natural-language entrypoint depends on Supervisor producing a stable routing contract:

```text
SupervisorDecision {
  intent:
    | "build_profile"
    | "analyze_job"
    | "match"
    | "plan"
    | "create_training"
    | "submit_training"
    | "start_interview"
    | "answer_interview"
    | "export_report"
    | "clarify"
  target_agent: string
  required_artifact_kinds: string[]
  missing_prerequisites: string[]
  user_facing_reason: string
  next_actions: string[]
}
```

The UI uses this contract to explain why a run was routed, which agent acted, which prerequisites are missing, and what the student can do next.

## Memory And Compaction

Short-term memory remains LangGraph checkpoint state plus recent messages.

Long-term memory should become a minimal JSON repository:

- Save confirmed student facts, preferences, goals, and evidence.
- Mark model-inferred facts as pending confirmation when confidence is not high.
- Read only scopes allowed by the active agent manifest.
- Keep memory separate from skill content.

Minimum memory schema:

```text
MemoryItem {
  id: string
  thread_id: string
  scope: "profile" | "preference" | "goal" | "skill" | "evidence"
  fact: string
  source_artifact_id?: string
  source_message_id?: string
  confidence: number
  status: "confirmed" | "pending_confirmation" | "rejected"
  created_at: string
  updated_at: string
}
```

Pending memory candidates appear in student mode as short confirmation prompts, such as "你似乎更倾向 AI Agent 开发岗位". The student can confirm or ignore them. Minimal APIs:

- `POST /api/threads/{thread_id}/memory/{memory_id}/confirm`
- `POST /api/threads/{thread_id}/memory/{memory_id}/reject`

Compaction should follow the existing Codex/Claude Code style: preserve recoverable task state, not a generic chat summary.

Minimum compaction snapshot schema:

```text
CompactionSnapshot {
  id: string
  thread_id: string
  source_run_id: string
  current_goal: string
  confirmed_facts: string[]
  decisions_made: string[]
  active_artifact_refs: string[]
  next_actions: string[]
  dropped_context_summary: string
  created_at: string
}
```

Trigger compaction when any of these conditions is true:

- Every six conversation turns by default.
- Before report generation.
- The context budget exceeds a configured threshold.
- The student switches target role or active goal.

Tests must prove snapshots do not contain `hidden_reasoning`, `chain_of_thought`, or raw provider `reasoning_content`.

The UI should show compaction as:

- Current goal
- Confirmed facts
- Active artifact refs
- Decisions made
- Next actions

## Progressive Skill Loading

The current implementation stores only skill refs in graph state. v3 should make loading more dynamic:

- The runtime chooses skills by `agent_id`, detected intent, and token budget.
- The graph state stores refs and summaries, not full skill bodies.
- The loader can choose full body, summary, or skip based on budget.
- Tests should prove different intents or budgets produce different loaded skill sets or detail levels.

Runtime state stores bounded skill refs:

```text
SkillRuntimeRef {
  skill_id: string
  version: string
  section_ids: string[]
  detail_level: "summary" | "full" | "skipped"
  summary_digest: string
}
```

`summary_digest` is a short digest capped at 240 characters. It must not become a hidden copy of the skill body.

## Error Handling

The UI should handle:

- Missing prerequisite artifacts: show a recoverable prompt, such as asking the student to run match before training.
- Report export before completion: explain missing training submission or interview turns.
- Provider errors: show retry and allow fallback to mock provider for demo.
- Long context: show that compaction occurred and continue the thread.
- Permission failures: show a demo-safe error and log the denied action in runtime warnings.
- Markdown preview sanitizes user-provided content, disables raw HTML, and avoids rendering untrusted markup directly.

## Testing

Backend tests:

- `/api/runs` returns `last_business_agent`, `current_runtime_node`, assistant message, artifact chain, and compaction summary.
- `/api/runs` persists user and assistant `ConversationMessage` records with run ids and artifact refs.
- `/api/runs` returns `run_status`, `SupervisorDecision`, and `workspace_delta`.
- Workspace endpoint returns active-context artifacts for one thread only.
- Report export reads the active artifact chain and does not mix artifacts from different goals or jobs.
- Runtime still rejects unauthorized artifact read/write, memory access, and handoff.
- Memory repository persists confirmed facts and filters by thread/scope.
- Memory confirmation and rejection endpoints update memory item status.
- Compaction snapshot tests prove no hidden reasoning, chain-of-thought, or raw reasoning content is stored.
- Skill loader selects by agent, intent, and budget.
- Graph state stores bounded `SkillRuntimeRef` records, not full skill bodies.

Frontend tests or build checks:

- Workbench renders empty state, chat input, and runtime panel.
- Sending a message updates conversation and workspace artifacts.
- Custom job text flows into job analysis and match.
- Training and interview gates are visible before report export.
- Student mode hides runtime internals; demo mode exposes trace, artifact chain, memory, and compaction.
- Markdown export still works after a full thread.

Manual browser smoke:

- Start backend and frontend.
- Open the app.
- Send a natural first message.
- Complete profile, job, match, plan, training submission, three interview turns, and report export.
- Confirm the runtime panel shows business agent, memory manager final node, artifact chain, and compaction snapshot.
- Switch or mention a second target role, then return to the first active chain and confirm the workspace does not mix artifacts across goals.

## Acceptance Criteria

- The user can drive the app from free-form chat, not only by fixed demo buttons.
- The structured workspace updates from persisted artifacts.
- The workspace and report use active workspace context, not latest artifacts by kind.
- Conversation messages survive refresh and stay linked to run ids and artifact refs.
- Demo reviewers can see the multi-agent chain, skills, memory, and artifacts.
- Runtime status distinguishes completed, needs-input, prerequisite-blocked, provider-error, permission-denied, and failed runs.
- Existing v2 strict runtime gates remain intact.
- Full backend pytest and frontend build pass.
- Browser smoke proves the chat workbench flow is usable.
