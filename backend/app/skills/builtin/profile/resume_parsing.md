---
id: profile/resume_parsing
version: 1
agent_scope: profile
tags:
  - profile
  - resume
summary: Extract structured career facts from resume text while preserving evidence.
token_budget: 420
---
# Resume Parsing

## 输入
Resume text, uploaded document excerpts, or user-provided career history.

## 输出
Return structured profile fields for roles, companies, dates, skills, education, achievements, goals, and constraints. Preserve source snippets for claims that may be reused downstream.
