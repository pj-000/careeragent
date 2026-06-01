---
id: profile/evidence_chain
version: 1
agent_scope: profile
tags:
  - evidence
  - profile
summary: Link profile claims to source evidence and flag unsupported assertions.
token_budget: 360
---
# Evidence Chain

## 输入
Parsed profile facts, resume snippets, user messages, and memory records.

## 输出
Return each important claim with evidence references, confidence, and missing evidence notes. Do not invent proof for skills, seniority, impact, or dates.
