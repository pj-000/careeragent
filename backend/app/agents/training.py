from typing import Any

from app.agents.runtime import coerce_state, run_business_agent
from app.repositories.interfaces import ArtifactRepository


def training_node(state: dict[str, Any], artifact_repo: ArtifactRepository) -> dict[str, Any]:
    career_state = coerce_state(state)
    if not artifact_repo.list_by_kind(career_state.thread_id, "match"):
        career_state.warnings = _append_unique(
            career_state.warnings,
            ["Missing match artifact before training; ask Match Agent to complete gap diagnosis first."],
        )
    message = career_state.user_message
    payload = {
        "task": "围绕 Agent 开发岗位能力差距，设计一个可交付的小型项目练习。",
        "rubric": ["LangGraph 编排清晰", "FastAPI 接口可演示", "RAG/测试证据可验证"],
        "has_submission": False,
        "submission": None,
        "score": None,
    }
    if "训练答案" in message:
        submission = message.split("训练答案", 1)[-1].lstrip("：: ")
        payload.update(
            {
                "has_submission": True,
                "submission": submission,
                "student_submission": submission,
                "feedback": "答案覆盖 FastAPI 与 LangGraph 编排，下一步补充 RAG 检索链路和自动化测试证据。",
                "score": 82,
            }
        )
    return run_business_agent(
        career_state.model_dump(),
        artifact_repo,
        agent_id="training",
        artifact_kind="training_result",
        title="Training task",
        payload=payload,
    )


def _append_unique(existing: list[str], additions: list[str]) -> list[str]:
    values = list(existing)
    for item in additions:
        if item not in values:
            values.append(item)
    return values
