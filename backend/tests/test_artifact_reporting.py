import pytest

from app.artifacts.markdown import MissingArtifactError, build_markdown_report


def _artifact(kind: str, source_agent: str, content: dict) -> dict:
    return {
        "id": f"{source_agent}-{kind}-1",
        "kind": kind,
        "source_thread_id": "thread-report-producer",
        "source_agent": source_agent,
        "payload": {"content": content},
        "created_at": "2026-05-31T00:00:00Z",
        "updated_at": "2026-05-31T00:00:00Z",
    }


def test_report_rejects_match_artifact_from_training_agent() -> None:
    artifacts = [
        _artifact("profile", "profile", {"summary": "Python/FastAPI backend student"}),
        _artifact("job_analysis", "job", {"summary": "Agent 开发工程师"}),
        _artifact("match", "training", {"score": 74, "gaps": ["LangGraph 证据不足"]}),
        _artifact("plan", "planning", {"milestones": ["补齐 LangGraph 项目证据"]}),
        _artifact(
            "training_result",
            "training",
            {
                "task": "实现一个 Agent 练习项目",
                "student_submission": "我提交了 FastAPI + LangGraph demo。",
            },
        ),
        _artifact("interview_summary", "interview", {"answers": ["a1", "a2", "a3"]}),
    ]

    with pytest.raises(MissingArtifactError, match="producer"):
        build_markdown_report("thread-report-producer", artifacts)
