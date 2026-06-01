from typing import Any

from app.agents.runtime import coerce_state
from app.agents.runtime import run_business_agent
from app.repositories.interfaces import ArtifactRepository


def interview_node(state: dict[str, Any], artifact_repo: ArtifactRepository) -> dict[str, Any]:
    career_state = coerce_state(state)
    message = career_state.user_message
    previous_answers = _latest_answers(career_state.thread_id, artifact_repo)
    answers = list(previous_answers)
    answer = _extract_answer(message)
    if answer:
        answers.append(answer)
    turns = [{"role": "candidate", "answer": answer} for answer in answers]
    if "开始" in message or "模拟面试" in message:
        turns.append({"role": "interviewer", "question": "请介绍一个你用 LangGraph 编排 Agent 工作流的项目。"})

    return run_business_agent(
        career_state.model_dump(),
        artifact_repo,
        agent_id="interview",
        artifact_kind="interview_summary",
        title="Interview preparation",
        payload={
            "questions": ["Tell me about a backend project.", "How do you debug production issues?"],
            "focus": "Use evidence from saved profile and match artifacts.",
            "answers": answers,
            "turn_count": len(answers),
            "completed": len(answers) >= 3,
            "turns": turns,
            "feedback": _feedback_for_answers(answers),
        },
    )


def _latest_answers(thread_id: str, artifact_repo: ArtifactRepository) -> list[str]:
    records = []
    for artifact in artifact_repo.list_by_kind(thread_id, "interview_summary"):
        record = artifact_repo.get(artifact["id"])
        content = record.get("payload", {}).get("content", {})
        records.append(
            (
                record.get("updated_at", ""),
                content.get("answers", []) if isinstance(content, dict) else [],
            )
        )
    if not records:
        return []
    return list(sorted(records, key=lambda item: item[0])[-1][1])


def _extract_answer(message: str) -> str:
    if message.startswith("回答") or "面试答案" in message:
        return message.split("：", 1)[-1].split(":", 1)[-1].strip()
    return ""


def _feedback_for_answers(answers: list[str]) -> str:
    if len(answers) >= 3:
        return "三轮回答已覆盖状态图、会话状态和 Artifact 沉淀，可进入报告汇总。"
    if answers:
        return "继续补充实现细节、状态保存和产物复盘。"
    return "模拟面试已启动，请按轮次回答。"
