from typing import Any

from app.agents.runtime import coerce_state, make_runtime, next_artifact_id
from app.agents.runtime import run_business_agent
from app.repositories.interfaces import ArtifactRepository


def training_node(state: dict[str, Any], artifact_repo: ArtifactRepository) -> dict[str, Any]:
    career_state = coerce_state(state)
    _ensure_gap_match_artifact(career_state, artifact_repo)
    message = career_state.user_message
    payload = {
        "task": "围绕 Agent 开发岗位能力差距，设计一个可交付的小型项目练习。",
        "rubric": ["LangGraph 编排清晰", "FastAPI 接口可演示", "RAG/测试证据可验证"],
    }
    if "训练答案" in message:
        submission = message.split("训练答案", 1)[-1].lstrip("：: ")
        payload.update(
            {
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


def _ensure_gap_match_artifact(career_state: Any, artifact_repo: ArtifactRepository) -> None:
    if artifact_repo.list_by_kind(career_state.thread_id, "match"):
        return
    runtime = make_runtime(career_state, "training", artifact_repo)
    artifact_id = next_artifact_id(artifact_repo, career_state.thread_id, "match")
    runtime.save_artifact(
        kind="match",
        artifact_id=artifact_id,
        payload={
            "title": "Match diagnosis",
            "user_message": career_state.user_message,
            "content": {
                "score": 74,
                "strengths": ["Python", "FastAPI", "Agent 项目动机明确"],
                "gaps": ["能力差距：LangGraph 状态编排证据不足", "RAG 项目经验需要补强", "测试能力需要项目化展示"],
            },
            "skill_refs": ["match/match_scoring_rubric", "match/gap_diagnosis"],
        },
        parent_artifact_ids=list(career_state.artifact_ids),
    )
    career_state.artifact_ids.append(artifact_id)
