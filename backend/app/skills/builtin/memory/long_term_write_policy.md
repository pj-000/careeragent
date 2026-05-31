---
id: memory/long_term_write_policy
version: 1
agent_scope: memory_manager
tags:
  - memory
  - policy
summary: Decide what career information is durable enough to write to long-term memory.
token_budget: 360
---
# Long Term Write Policy

## 输入
Recent conversation, artifacts, user corrections, and candidate memory updates.

## 输出
Return memory writes only for stable preferences, career history, durable goals, and reusable facts. Avoid saving transient tasks, sensitive guesses, or unsupported claims.
