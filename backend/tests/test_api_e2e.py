from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.repositories.json_repository import JsonArtifactRepository
from app.schemas.runs import RunResponse, RunStatus


def complete_demo_messages(marker: str | None = None) -> list[str]:
    first_message = "我会 Python FastAPI，想匹配 Agent 开发岗位"
    if marker:
        first_message = f"{first_message} {marker}"
    return [
        first_message,
        "请分析目标岗位 JD：Agent 开发工程师，需要 LangGraph、FastAPI、RAG 和测试能力",
        "请做 match 分析",
        "生成三个月路径规划",
        "根据能力差距给我一个训练任务",
        "我的训练答案：我会设计一个简历解析 Agent，使用 FastAPI 暴露接口，用 LangGraph 编排画像抽取和评分节点。",
        "开始模拟面试",
        "回答1：我会用 StateGraph 定义节点和条件边。",
        "回答2：我会用 thread_id 和 checkpointer 保留会话状态。",
        "回答3：我会把评分结果保存为 Artifact 并进入报告。",
        "请导出 Markdown 报告",
    ]


def test_health_endpoint_returns_ok() -> None:
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_runs_endpoint_returns_runtime_fields_and_uses_tmp_runtime_dir(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from app.api import runs

    monkeypatch.setattr(runs, "RUNTIME_DATA_DIR", tmp_path)
    client = TestClient(app)

    response = client.post(
        "/api/runs",
        json={"thread_id": "thread-api-e2e", "message": "请从我的 resume 建立 profile"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == set(RunResponse.model_fields)
    assert payload["run_id"].startswith("run-")
    assert payload["thread_id"] == "thread-api-e2e"
    assert payload["active_agent"] == "memory_manager"
    assert payload["run_status"] == RunStatus.COMPLETED
    assert payload["missing_artifacts"] == []
    assert payload["missing_capabilities"] == []
    assert payload["blocking_reason"] is None
    assert payload["workspace_delta"] is None
    assert payload["memory_updates"] == []
    assert isinstance(payload["agent_trace_summary"], list)
    assert isinstance(payload["used_skill_refs"], list)
    assert isinstance(payload["used_skill_runtime_refs"], list)
    assert isinstance(payload["artifacts"], list)
    assert isinstance(payload["artifact_chain"], list)
    assert isinstance(payload["next_actions"], list)
    assert isinstance(payload["warnings"], list)
    assert {artifact["kind"] for artifact in payload["artifacts"]} >= {
        "profile",
        "compaction_snapshot",
    }
    assert (tmp_path / "artifacts-index.json").exists()


def test_runs_endpoint_reuses_same_thread_checkpoint_between_requests(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from app.api import runs
    from app.graphs.workflow import get_runtime_graph

    monkeypatch.setattr(runs, "RUNTIME_DATA_DIR", tmp_path)
    client = TestClient(app)
    thread_id = "thread-api-checkpoint"

    first = client.post(
        "/api/runs",
        json={"thread_id": thread_id, "message": "请从我的 resume 建立 profile"},
    )
    second = client.post(
        "/api/runs",
        json={"thread_id": thread_id, "message": "请分析 Agent 开发岗位 JD"},
    )
    third = client.post(
        "/api/runs",
        json={"thread_id": thread_id, "message": "请做 match 分析"},
    )
    fourth = client.post(
        "/api/runs",
        json={"thread_id": thread_id, "message": "生成三个月路径规划"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 200
    assert fourth.status_code == 200
    graph = get_runtime_graph(JsonArtifactRepository(tmp_path))
    snapshot = graph.get_state({"configurable": {"thread_id": thread_id}})
    messages = snapshot.values["messages"]
    assert [message["content"] for message in messages if message["role"] == "user"] == [
        "请从我的 resume 建立 profile",
        "请分析 Agent 开发岗位 JD",
        "请做 match 分析",
        "生成三个月路径规划",
    ]
    assert len(snapshot.values["artifact_ids"]) >= len(first.json()["artifacts"])
    assert {"profile", "job_analysis", "match", "plan"} <= {
        artifact["kind"] for artifact in fourth.json()["artifacts"]
    }


def test_runs_endpoint_rejects_unsafe_thread_id() -> None:
    client = TestClient(app)

    response = client.post("/api/runs", json={"thread_id": "../bad", "message": "hello"})

    assert response.status_code == 422


def test_frontend_origin_is_allowed_by_cors() -> None:
    client = TestClient(app)

    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"


def test_profile_and_job_seed_endpoints_create_artifacts_without_running_graph(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from app.api import jobs, profiles

    monkeypatch.setattr(profiles, "RUNTIME_DATA_DIR", tmp_path)
    monkeypatch.setattr(jobs, "RUNTIME_DATA_DIR", tmp_path)
    client = TestClient(app)

    profile_response = client.post("/api/profiles/demo")
    demo_job_response = client.post("/api/jobs/demo")
    custom_job_response = client.post(
        "/api/jobs/custom",
        json={
            "thread_id": "seed-thread",
            "title": "Backend Agent Engineer",
            "company": "CareerAgent",
            "description": "Build agent workflows and backend APIs.",
        },
    )

    assert profile_response.status_code == 200
    assert demo_job_response.status_code == 200
    assert custom_job_response.status_code == 200
    assert profile_response.json()["artifact_id"].startswith("profile-")
    assert demo_job_response.json()["artifact_id"].startswith("job-")
    assert custom_job_response.json()["artifact_id"].startswith("job-")
    assert "run_id" not in profile_response.json()
    assert "run_id" not in demo_job_response.json()
    assert "run_id" not in custom_job_response.json()


def test_complete_backend_loop_exports_isolated_markdown_reports(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from app.api import interviews, reports, runs, training

    monkeypatch.setattr(runs, "RUNTIME_DATA_DIR", tmp_path)
    monkeypatch.setattr(training, "RUNTIME_DATA_DIR", tmp_path)
    monkeypatch.setattr(interviews, "RUNTIME_DATA_DIR", tmp_path)
    monkeypatch.setattr(reports, "RUNTIME_DATA_DIR", tmp_path)
    client = TestClient(app)

    thread_a = "task8-thread-a"
    thread_b = "task8-thread-b"
    marker_a = "MARKER_A_TASK8"
    marker_b = "MARKER_B_TASK8"

    for thread_id, marker in [(thread_a, marker_a), (thread_b, marker_b)]:
        for message in complete_demo_messages(marker):
            response = client.post("/api/runs", json={"thread_id": thread_id, "message": message})
            assert response.status_code == 200

    repo = JsonArtifactRepository(tmp_path)
    artifacts_a = repo.list_by_thread(thread_a)
    kinds_a = {artifact["kind"] for artifact in artifacts_a}
    assert {
        "profile",
        "job_analysis",
        "match",
        "plan",
        "training_result",
        "interview_summary",
        "report",
    } <= kinds_a

    training_records = [
        repo.get(artifact["id"]) for artifact in artifacts_a if artifact["kind"] == "training_result"
    ]
    assert any(
        "简历解析 Agent" in record["payload"].get("content", {}).get("student_submission", "")
        and "feedback" in record["payload"].get("content", {})
        and "score" in record["payload"].get("content", {})
        for record in training_records
    )

    interview_records = [
        repo.get(artifact["id"]) for artifact in artifacts_a if artifact["kind"] == "interview_summary"
    ]
    assert any(len(record["payload"].get("content", {}).get("answers", [])) >= 3 for record in interview_records)

    report_response_a = client.get(f"/api/reports/{thread_a}/markdown")
    report_response_b = client.get(f"/api/reports/{thread_b}/markdown")

    assert report_response_a.status_code == 200
    assert report_response_b.status_code == 200
    assert report_response_a.headers["content-type"] == "text/markdown; charset=utf-8"
    assert report_response_b.headers["content-type"] == "text/markdown; charset=utf-8"

    markdown_a = report_response_a.text
    markdown_b = report_response_b.text
    assert "# CareerAgent 职业发展报告" in markdown_a
    assert "能力差距" in markdown_a
    assert marker_a in markdown_a
    assert marker_b not in markdown_a
    assert marker_b in markdown_b
    assert marker_a not in markdown_b

    latest_report = repo.get(f"report-{thread_a}-latest")
    thread_a_artifact_ids = {artifact["id"] for artifact in artifacts_a}
    assert set(latest_report["parent_artifact_ids"]) <= thread_a_artifact_ids
    assert {
        "profile",
        "job_analysis",
        "match",
        "plan",
        "training_result",
        "interview_summary",
    } <= {
        repo.get(artifact_id)["kind"] for artifact_id in latest_report["parent_artifact_ids"]
    }


def test_report_export_requires_training_submission_and_three_interview_answers(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from app.api import interviews, reports, runs, training

    monkeypatch.setattr(runs, "RUNTIME_DATA_DIR", tmp_path)
    monkeypatch.setattr(training, "RUNTIME_DATA_DIR", tmp_path)
    monkeypatch.setattr(interviews, "RUNTIME_DATA_DIR", tmp_path)
    monkeypatch.setattr(reports, "RUNTIME_DATA_DIR", tmp_path)
    client = TestClient(app)
    thread_id = "task8-incomplete-loop"
    incomplete_messages = [
        "我会 Python FastAPI，想匹配 Agent 开发岗位",
        "请分析目标岗位 JD：Agent 开发工程师，需要 LangGraph、FastAPI、RAG 和测试能力",
        "请做 match 分析",
        "生成三个月路径规划",
        "根据能力差距给我一个训练任务",
        "开始模拟面试",
    ]
    for message in incomplete_messages:
        response = client.post("/api/runs", json={"thread_id": thread_id, "message": message})
        assert response.status_code == 200

    report = client.get(f"/api/reports/{thread_id}/markdown")

    assert report.status_code == 409
    assert "training submission" in report.json()["detail"]


def test_report_export_requires_three_interview_answers_after_training_submission(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from app.api import interviews, reports, runs, training

    monkeypatch.setattr(runs, "RUNTIME_DATA_DIR", tmp_path)
    monkeypatch.setattr(training, "RUNTIME_DATA_DIR", tmp_path)
    monkeypatch.setattr(interviews, "RUNTIME_DATA_DIR", tmp_path)
    monkeypatch.setattr(reports, "RUNTIME_DATA_DIR", tmp_path)
    client = TestClient(app)
    thread_id = "task8-two-interview-answers"
    incomplete_messages = [
        "我会 Python FastAPI，想匹配 Agent 开发岗位",
        "请分析目标岗位 JD：Agent 开发工程师，需要 LangGraph、FastAPI、RAG 和测试能力",
        "请做 match 分析",
        "生成三个月路径规划",
        "根据能力差距给我一个训练任务",
        "我的训练答案：我会设计一个简历解析 Agent，使用 FastAPI 暴露接口，用 LangGraph 编排画像抽取和评分节点。",
        "开始模拟面试",
        "回答1：我会用 StateGraph 定义节点和条件边。",
        "回答2：我会用 thread_id 和 checkpointer 保留会话状态。",
    ]
    for message in incomplete_messages:
        response = client.post("/api/runs", json={"thread_id": thread_id, "message": message})
        assert response.status_code == 200

    report = client.get(f"/api/reports/{thread_id}/markdown")

    assert report.status_code == 409
    assert "three interview answers" in report.json()["detail"]


def test_report_export_accepts_max_length_safe_thread_id(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from app.api import interviews, reports, runs, training

    monkeypatch.setattr(runs, "RUNTIME_DATA_DIR", tmp_path)
    monkeypatch.setattr(training, "RUNTIME_DATA_DIR", tmp_path)
    monkeypatch.setattr(interviews, "RUNTIME_DATA_DIR", tmp_path)
    monkeypatch.setattr(reports, "RUNTIME_DATA_DIR", tmp_path)
    client = TestClient(app)
    thread_id = "t" * 128
    for message in complete_demo_messages("LONG_THREAD"):
        response = client.post("/api/runs", json={"thread_id": thread_id, "message": message})
        assert response.status_code == 200

    report = client.get(f"/api/reports/{thread_id}/markdown")

    assert report.status_code == 200
    repo = JsonArtifactRepository(tmp_path)
    assert repo.get(f"report-{thread_id}-latest")["source_thread_id"] == thread_id


def test_report_agent_does_not_save_placeholder_report_when_required_artifacts_are_missing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from app.api import runs

    monkeypatch.setattr(runs, "RUNTIME_DATA_DIR", tmp_path)
    client = TestClient(app)
    thread_id = "task8-missing-report-chain"

    response = client.post("/api/runs", json={"thread_id": thread_id, "message": "请导出 Markdown 报告"})

    assert response.status_code == 200
    repo = JsonArtifactRepository(tmp_path)
    assert repo.list_by_kind(thread_id, "report") == []
    assert any("Missing required artifact" in warning for warning in response.json()["warnings"])
