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

EXPECTED_REPORT_PRODUCERS = {
    "profile": "profile",
    "job_analysis": "job",
    "match": "match",
    "plan": "planning",
    "training_result": "training",
    "interview_summary": "interview",
}


class MissingArtifactError(ValueError):
    pass


def build_markdown_report(thread_id: str, artifacts: list[dict[str, Any]]) -> str:
    by_kind = _latest_required_artifacts(thread_id, artifacts)
    _validate_required_report_content(thread_id, by_kind)
    return _render_markdown_report(thread_id, by_kind)


def build_markdown_report_from_chain(thread_id: str, artifacts: list[dict[str, Any]]) -> str:
    by_kind = _required_artifacts_from_chain(thread_id, artifacts)
    _validate_required_chain_report_content(thread_id, by_kind)
    return _render_markdown_report(thread_id, by_kind)


def _render_markdown_report(thread_id: str, by_kind: dict[str, dict[str, Any]]) -> str:
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
        f"- 提交：{_training_submission(training) or '尚未提交'}",
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


def required_parent_artifact_ids_from_chain(thread_id: str, artifacts: list[dict[str, Any]]) -> list[str]:
    by_kind = _required_artifacts_from_chain(thread_id, artifacts)
    _validate_required_chain_report_content(thread_id, by_kind)
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
        expected_producer = EXPECTED_REPORT_PRODUCERS[kind]
        actual_producer = by_kind[kind].get("source_agent")
        if actual_producer != expected_producer:
            raise MissingArtifactError(
                f"Invalid producer for {kind}: expected {expected_producer}, got {actual_producer}"
            )
        if kind == "training_result":
            _validate_training_submission(thread_id, by_kind[kind])
    return by_kind


def _required_artifacts_from_chain(thread_id: str, artifacts: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_kind: dict[str, dict[str, Any]] = {}
    for artifact in artifacts:
        if artifact.get("source_thread_id") != thread_id:
            continue
        kind = artifact.get("kind")
        if kind not in REQUIRED_REPORT_KINDS:
            continue
        expected_producer = EXPECTED_REPORT_PRODUCERS[kind]
        actual_producer = artifact.get("source_agent")
        if actual_producer != expected_producer:
            raise MissingArtifactError(
                f"Invalid producer for {kind}: expected {expected_producer}, got {actual_producer}"
            )
        by_kind[kind] = artifact
    for kind in REQUIRED_REPORT_KINDS:
        if kind not in by_kind:
            raise MissingArtifactError(f"Missing required artifact kind: {kind}")
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
    _validate_training_submission(thread_id, by_kind["training_result"])

    interview = _content(by_kind["interview_summary"])
    answers = interview.get("answers")
    if not isinstance(answers, list) or len(answers) < 3:
        raise MissingArtifactError(f"Missing three interview answers for {thread_id}")


def _validate_required_chain_report_content(thread_id: str, by_kind: dict[str, dict[str, Any]]) -> None:
    training = _content(by_kind["training_result"])
    if not bool(training.get("has_submission")) or not _training_submission(training):
        raise MissingArtifactError(
            f"Thread {thread_id!r} has a training_result artifact, but the training answer is not submitted"
        )
    if training.get("score") is None:
        raise MissingArtifactError(
            f"Thread {thread_id!r} has a training_result artifact, but the training answer is not scored"
        )

    interview = _content(by_kind["interview_summary"])
    turn_count = _chain_interview_turn_count(interview)
    if turn_count < 3:
        raise MissingArtifactError(
            f"Thread {thread_id!r} has an interview_summary artifact, but fewer than three interview turns are complete"
        )


def _validate_training_submission(thread_id: str, artifact: dict[str, Any]) -> None:
    training = _content(artifact)
    if not bool(training.get("has_submission")) or not _training_submission(training):
        raise MissingArtifactError(f"Missing training submission for {thread_id}")
    if training.get("score") is None:
        raise MissingArtifactError(f"Missing training score for {thread_id}")


def _training_submission(training: dict[str, Any]) -> str:
    submission = training.get("submission")
    if isinstance(submission, str) and submission.strip():
        return submission
    return ""


def _chain_interview_turn_count(interview: dict[str, Any]) -> int:
    turn_count = interview.get("turn_count")
    if isinstance(turn_count, int):
        return turn_count
    answers = interview.get("answers")
    if isinstance(answers, list):
        return len(answers)
    turns = interview.get("turns")
    if isinstance(turns, list):
        return len(turns)
    return 0


def _join_items(value: Any) -> str:
    if isinstance(value, list):
        return "、".join(str(item) for item in value)
    return str(value)


def _bullet_lines(items: Any) -> list[str]:
    if not isinstance(items, list):
        items = [items]
    return [f"- {item}" for item in items]
