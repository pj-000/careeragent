from __future__ import annotations

from typing import Any


REQUIRED_REPORT_KINDS = [
    "profile",
    "job_analysis",
    "match",
    "plan",
    "training_result",
    "interview_summary",
]


class MissingArtifactError(ValueError):
    pass


def build_markdown_report(thread_id: str, artifacts: list[dict[str, Any]]) -> str:
    by_kind = _latest_required_artifacts(thread_id, artifacts)
    _validate_required_report_content(thread_id, by_kind)

    profile = _content(by_kind["profile"])
    job = _content(by_kind["job_analysis"])
    match = _content(by_kind["match"])
    plan = _content(by_kind["plan"])
    training = _content(by_kind["training_result"])
    interview = _content(by_kind["interview_summary"])

    gaps = match.get("gaps") or ["补齐目标岗位所需的可验证项目证据"]
    strengths = match.get("strengths") or profile.get("signals") or ["Python", "FastAPI"]
    milestones = plan.get("milestones") or []
    answers = interview.get("answers") or []

    lines = [
        "# CareerAgent 职业发展报告",
        "",
        f"- 线程：{thread_id}",
        f"- 画像摘要：{profile.get('summary', '已建立候选人画像')}",
        f"- 画像输入：{profile.get('source_message', '未记录')}",
        f"- 目标岗位：{job.get('summary') or job.get('description') or 'Agent 开发工程师'}",
        "",
        "## 匹配结论",
        f"- 匹配分：{match.get('score', '待评估')}",
        f"- 优势：{_join_items(strengths)}",
        "",
        "## 能力差距",
        *_bullet_lines(gaps),
        "",
        "## 三个月路径规划",
        *_bullet_lines(milestones or ["完善 Agent 项目证据", "补齐 RAG 与测试实践", "完成模拟面试复盘"]),
        "",
        "## 训练结果",
        f"- 任务：{training.get('task', '围绕能力差距完成一次项目化练习')}",
        f"- 提交：{training.get('student_submission', '尚未提交')}",
        f"- 反馈：{training.get('feedback', '继续补充可验证证据')}",
        f"- 分数：{training.get('score', '待评分')}",
        "",
        "## 面试总结",
        *_bullet_lines(answers or interview.get("turns") or ["已启动模拟面试"]),
    ]
    return "\n".join(str(line) for line in lines).strip() + "\n"


def required_parent_artifact_ids(thread_id: str, artifacts: list[dict[str, Any]]) -> list[str]:
    by_kind = _latest_required_artifacts(thread_id, artifacts)
    _validate_required_report_content(thread_id, by_kind)
    return [by_kind[kind]["id"] for kind in REQUIRED_REPORT_KINDS]


def _latest_required_artifacts(
    thread_id: str, artifacts: list[dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    scoped = [artifact for artifact in artifacts if artifact.get("source_thread_id") == thread_id]
    by_kind: dict[str, dict[str, Any]] = {}
    for kind in REQUIRED_REPORT_KINDS:
        matches = [artifact for artifact in scoped if artifact.get("kind") == kind]
        if not matches:
            raise MissingArtifactError(f"Missing required artifact kind: {kind}")
        by_kind[kind] = sorted(
            matches,
            key=lambda artifact: (
                str(artifact.get("updated_at", "")),
                str(artifact.get("created_at", "")),
                str(artifact.get("id", "")),
            ),
        )[-1]
    return by_kind


def _content(artifact: dict[str, Any]) -> dict[str, Any]:
    payload = artifact.get("payload", {})
    content = payload.get("content")
    if isinstance(content, dict):
        values = dict(content)
        if "user_message" in payload:
            values["source_message"] = payload["user_message"]
        return values
    if isinstance(payload, dict):
        return payload
    return {}


def _validate_required_report_content(thread_id: str, by_kind: dict[str, dict[str, Any]]) -> None:
    training = _content(by_kind["training_result"])
    if not training.get("student_submission"):
        raise MissingArtifactError(f"Missing training submission for {thread_id}")

    interview = _content(by_kind["interview_summary"])
    answers = interview.get("answers")
    if not isinstance(answers, list) or len(answers) < 3:
        raise MissingArtifactError(f"Missing three interview answers for {thread_id}")


def _join_items(value: Any) -> str:
    if isinstance(value, list):
        return "、".join(str(item) for item in value)
    return str(value)


def _bullet_lines(items: Any) -> list[str]:
    if not isinstance(items, list):
        items = [items]
    return [f"- {item}" for item in items]
