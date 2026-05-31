# CareerAgent Chat Workbench v3 Design

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
- No requirement to implement streaming tokens unless it naturally fits after the core workbench is stable.
- No hidden reasoning display. The UI can show summaries, trace, selected skills, artifacts, and compaction summaries, but not private chain-of-thought.

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

## Main Workspace

The workspace renders the latest artifact of each kind for the active thread:

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
    active_agent
    last_business_agent
    current_runtime_node
    assistant_message
    agent_trace_summary
    used_skill_refs
    artifacts
    artifact_chain
    compaction_snapshot
    next_actions
    warnings
```

Add read endpoints only for UI convenience:

- `GET /api/threads/{thread_id}/artifacts`
- `GET /api/threads/{thread_id}/workspace`
- `GET /api/threads/{thread_id}/messages`
- `GET /api/reports/{thread_id}/markdown`

The frontend should not call individual agents directly.

## Memory And Compaction

Short-term memory remains LangGraph checkpoint state plus recent messages.

Long-term memory should become a minimal JSON repository:

- Save confirmed student facts, preferences, goals, and evidence.
- Mark model-inferred facts as pending confirmation when confidence is not high.
- Read only scopes allowed by the active agent manifest.
- Keep memory separate from skill content.

Compaction should follow the existing Codex/Claude Code style: preserve recoverable task state, not a generic chat summary.

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

## Error Handling

The UI should handle:

- Missing prerequisite artifacts: show a recoverable prompt, such as asking the student to run match before training.
- Report export before completion: explain missing training submission or interview turns.
- Provider errors: show retry and allow fallback to mock provider for demo.
- Long context: show that compaction occurred and continue the thread.
- Permission failures: show a demo-safe error and log the denied action in runtime warnings.

## Testing

Backend tests:

- `/api/runs` returns `last_business_agent`, `current_runtime_node`, assistant message, artifact chain, and compaction summary.
- Workspace endpoint returns latest artifacts by kind for one thread only.
- Runtime still rejects unauthorized artifact read/write, memory access, and handoff.
- Memory repository persists confirmed facts and filters by thread/scope.
- Skill loader selects by agent, intent, and budget.

Frontend tests or build checks:

- Workbench renders empty state, chat input, and runtime panel.
- Sending a message updates conversation and workspace artifacts.
- Custom job text flows into job analysis and match.
- Training and interview gates are visible before report export.
- Markdown export still works after a full thread.

Manual browser smoke:

- Start backend and frontend.
- Open the app.
- Send a natural first message.
- Complete profile, job, match, plan, training submission, three interview turns, and report export.
- Confirm the runtime panel shows business agent, memory manager final node, artifact chain, and compaction snapshot.

## Acceptance Criteria

- The user can drive the app from free-form chat, not only by fixed demo buttons.
- The structured workspace updates from persisted artifacts.
- Demo reviewers can see the multi-agent chain, skills, memory, and artifacts.
- Existing v2 strict runtime gates remain intact.
- Full backend pytest and frontend build pass.
- Browser smoke proves the chat workbench flow is usable.
