---
id: memory/context_compaction
version: 1
agent_scope: supervisor,memory_manager
tags:
  - memory
  - compaction
summary: Compact working context into a short state snapshot for future agent handoffs.
token_budget: 360
---
# Context Compaction

## 输入
Conversation history, active agent state, artifacts, loaded skills, and unresolved questions.

## 输出
Return a compact snapshot containing user objective, confirmed facts, decisions made, artifact references, active risks, and recommended next agent.
