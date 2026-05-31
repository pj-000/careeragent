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


def _seed_report_chain(
    tmp_path: Path,
    thread_id: str,
    training_score: int | None,
    turn_count: int,
    save_context: bool = True,
) -> None:
    from app.repositories.json_thread_repository import JsonWorkspaceContextRepository
    from app.schemas.runs import WorkspaceContext

    artifact_repo = JsonArtifactRepository(tmp_path)
    artifact_repo.save(
        "profile",
        f"profile-{thread_id}",
        {"content": {"summary": "Python/FastAPI backend student", "signals": ["Python", "FastAPI"]}},
        thread_id,
        "profile",
    )
    artifact_repo.save(
        "job_analysis",
        f"job-{thread_id}",
        {"content": {"summary": "Agent 开发工程师"}},
        thread_id,
        "job",
        [f"profile-{thread_id}"],
    )
    artifact_repo.save(
        "match",
        f"match-{thread_id}",
        {"content": {"score": 74, "gaps": ["LangGraph 证据不足"], "strengths": ["FastAPI"]}},
        thread_id,
        "match",
        [f"profile-{thread_id}", f"job-{thread_id}"],
    )
    artifact_repo.save(
        "plan",
        f"plan-{thread_id}",
        {"content": {"milestones": ["补齐 LangGraph 项目证据"]}},
        thread_id,
        "planning",
        [f"match-{thread_id}"],
    )
    has_submission = training_score is not None
    artifact_repo.save(
        "training_result",
        f"training-{thread_id}",
        {
            "content": {
                "task": "写一个 Agent demo",
                "has_submission": has_submission,
                "submission": "FastAPI + LangGraph demo" if has_submission else None,
                "score": training_score,
            }
        },
        thread_id,
        "training",
        [f"plan-{thread_id}"],
    )
    artifact_repo.save(
        "interview_summary",
        f"interview-{thread_id}",
        {
            "content": {
                "turn_count": turn_count,
                "completed": turn_count >= 3,
                "answers": [f"answer-{index}" for index in range(1, turn_count + 1)],
            }
        },
        thread_id,
        "interview",
        [f"training-{thread_id}"],
    )
    if save_context:
        JsonWorkspaceContextRepository(tmp_path).save(
            WorkspaceContext(
                thread_id=thread_id,
                active_goal="Agent 开发工程师",
                active_profile_id=f"profile-{thread_id}",
                active_job_analysis_id=f"job-{thread_id}",
                active_match_id=f"match-{thread_id}",
                active_plan_id=f"plan-{thread_id}",
                active_training_result_id=f"training-{thread_id}",
                active_interview_summary_id=f"interview-{thread_id}",
                updated_by_run_id="seed-report-chain",
            )
        )


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
    assert payload["workspace_delta"]["updated_context"]["thread_id"] == "thread-api-e2e"
    assert payload["workspace_delta"]["updated_context"]["active_profile_id"]
    assert payload["memory_updates"]
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


def test_runs_endpoint_persists_messages_and_returns_v31_runtime_contract(tmp_path: Path, monkeypatch) -> None:
    from app.api import runs
    from app.repositories.json_thread_repository import JsonConversationRepository, JsonWorkspaceContextRepository

    monkeypatch.setattr(runs, "RUNTIME_DATA_DIR", tmp_path)
    client = TestClient(app)

    response = client.post(
        "/api/runs",
        json={"thread_id": "thread-v31-run", "message": "我会 Python FastAPI，想匹配 Agent 开发岗位"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_status"] == "completed"
    assert payload["last_business_agent"] == "profile"
    assert payload["current_runtime_node"] == "memory_manager"
    assert payload["assistant_message"]["role"] == "assistant"
    assert payload["assistant_message"]["run_id"] == payload["run_id"]
    assert payload["supervisor_decision"]["intent"] == "build_profile"
    assert payload["workspace_delta"]["updated_context"]["active_profile_id"]
    assert payload["artifact_chain"][0]["kind"] == "profile"
    assert payload["memory_updates"]
    assert len(payload["memory_updates"]) == 1

    messages = JsonConversationRepository(tmp_path).list_by_thread("thread-v31-run")
    assert [message.role.value for message in messages] == ["user", "assistant"]
    assert messages[1].artifact_refs == payload["assistant_message"]["artifact_refs"]
    assert payload["memory_updates"][0]["source_message_id"] == messages[0].id
    assert JsonWorkspaceContextRepository(tmp_path).get("thread-v31-run").active_profile_id


def test_threads_workspace_and_messages_restore_chat_state(tmp_path: Path, monkeypatch) -> None:
    from app.api import reports, runs, threads

    monkeypatch.setattr(runs, "RUNTIME_DATA_DIR", tmp_path)
    monkeypatch.setattr(threads, "RUNTIME_DATA_DIR", tmp_path)
    monkeypatch.setattr(reports, "RUNTIME_DATA_DIR", tmp_path)
    client = TestClient(app)
    thread_id = "thread-workspace-api"

    response = client.post(
        "/api/runs",
        json={"thread_id": thread_id, "message": "我会 Python FastAPI，想匹配 Agent 开发岗位"},
    )

    assert response.status_code == 200
    workspace = client.get(f"/api/threads/{thread_id}/workspace")
    messages = client.get(f"/api/threads/{thread_id}/messages")
    artifacts = client.get(f"/api/threads/{thread_id}/artifacts")
    memory = client.get(f"/api/threads/{thread_id}/memory")
    assert workspace.status_code == 200
    assert messages.status_code == 200
    assert artifacts.status_code == 200
    assert memory.status_code == 200
    assert workspace.json()["active_context"]["active_profile_id"]
    assert [message["role"] for message in messages.json()] == ["user", "assistant"]
    assert any(artifact["kind"] == "profile" for artifact in artifacts.json())
    assert isinstance(memory.json(), list)
    assert memory.json()


def test_memory_confirm_and_reject_endpoints_update_status(tmp_path: Path, monkeypatch) -> None:
    from app.api import threads
    from app.repositories.json_thread_repository import JsonMemoryRepository
    from app.schemas.memory import MemoryItem, MemoryScope, MemoryStatus

    monkeypatch.setattr(threads, "RUNTIME_DATA_DIR", tmp_path)
    JsonMemoryRepository(tmp_path).save(
        MemoryItem(
            id="memory-api-1",
            thread_id="thread-memory-api",
            scope=MemoryScope.GOAL,
            fact="想做 Agent 开发",
            status=MemoryStatus.PENDING_CONFIRMATION,
        )
    )
    client = TestClient(app)

    confirm = client.post("/api/threads/thread-memory-api/memory/memory-api-1/confirm")
    reject = client.post("/api/threads/thread-memory-api/memory/memory-api-1/reject")

    assert confirm.status_code == 200
    assert confirm.json()["status"] == "confirmed"
    assert reject.status_code == 200
    assert reject.json()["status"] == "rejected"


def test_memory_confirm_missing_item_returns_404(tmp_path: Path, monkeypatch) -> None:
    from app.api import threads

    monkeypatch.setattr(threads, "RUNTIME_DATA_DIR", tmp_path)
    client = TestClient(app)

    response = client.post("/api/threads/thread-memory-api/memory/missing-memory/confirm")

    assert response.status_code == 404


def test_runs_endpoint_persists_assistant_error_message_on_permission_denied(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from app.agents.runtime import PermissionDenied
    from app.api import runs
    from app.repositories.json_thread_repository import JsonConversationRepository
    from app.services import run_orchestrator

    def deny(*args, **kwargs):
        raise PermissionDenied("training cannot write match")

    monkeypatch.setattr(runs, "RUNTIME_DATA_DIR", tmp_path)
    monkeypatch.setattr(run_orchestrator, "run_career_graph", deny)
    client = TestClient(app)

    response = client.post(
        "/api/runs",
        json={"thread_id": "thread-permission-error", "message": "请做 match 分析"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_status"] == "permission_denied"
    assert payload["assistant_message"]["role"] == "assistant"
    assert payload["retryable"] is False
    messages = JsonConversationRepository(tmp_path).list_by_thread("thread-permission-error")
    assert [message.role.value for message in messages] == ["user", "assistant"]


def test_runs_endpoint_marks_provider_error_retryable(tmp_path: Path, monkeypatch) -> None:
    from app.api import runs
    from app.providers.base import ProviderError
    from app.repositories.json_thread_repository import JsonConversationRepository
    from app.services import run_orchestrator

    def fail_provider(*args, **kwargs):
        raise ProviderError("qwen upstream timeout")

    monkeypatch.setattr(runs, "RUNTIME_DATA_DIR", tmp_path)
    monkeypatch.setattr(run_orchestrator, "run_career_graph", fail_provider)
    client = TestClient(app)

    response = client.post(
        "/api/runs",
        json={"thread_id": "thread-provider-error", "message": "请分析岗位"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_status"] == "provider_error"
    assert payload["retryable"] is True
    assert "模型服务" in payload["assistant_message"]["content"]
    messages = JsonConversationRepository(tmp_path).list_by_thread("thread-provider-error")
    assert [message.role.value for message in messages] == ["user", "assistant"]


def test_start_interview_requires_submitted_training_result(tmp_path: Path, monkeypatch) -> None:
    from app.api import runs
    from app.repositories.json_repository import JsonArtifactRepository
    from app.repositories.json_thread_repository import JsonWorkspaceContextRepository
    from app.schemas.runs import WorkspaceContext

    monkeypatch.setattr(runs, "RUNTIME_DATA_DIR", tmp_path)
    artifact_repo = JsonArtifactRepository(tmp_path)
    context_repo = JsonWorkspaceContextRepository(tmp_path)
    artifact_repo.save("profile", "profile-1", {"content": {}}, "thread-training-gate", "profile")
    artifact_repo.save("job_analysis", "job-1", {"content": {}}, "thread-training-gate", "job")
    artifact_repo.save("match", "match-1", {"content": {}}, "thread-training-gate", "match")
    artifact_repo.save("plan", "plan-1", {"content": {}}, "thread-training-gate", "planning")
    artifact_repo.save(
        "training_result",
        "training-1",
        {"content": {"task": "写一个 Agent demo", "has_submission": False, "score": None}},
        "thread-training-gate",
        "training",
    )
    context_repo.save(
        WorkspaceContext(
            thread_id="thread-training-gate",
            active_goal="Agent 开发工程师",
            active_profile_id="profile-1",
            active_job_analysis_id="job-1",
            active_match_id="match-1",
            active_plan_id="plan-1",
            active_training_result_id="training-1",
            updated_by_run_id="seed",
        )
    )
    client = TestClient(app)

    response = client.post("/api/runs", json={"thread_id": "thread-training-gate", "message": "开始模拟面试"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_status"] == "blocked_by_prerequisite"
    assert payload["supervisor_decision"]["missing_capabilities"] == ["training_scored"]
    assert payload["missing_capabilities"] == ["training_scored"]
    assert "训练答案" in payload["assistant_message"]["content"]
    assert "完成评分" in payload["assistant_message"]["content"]
    assert JsonArtifactRepository(tmp_path).list_by_kind("thread-training-gate", "interview_summary") == []


def test_blocked_match_request_does_not_create_memory_candidate(tmp_path: Path, monkeypatch) -> None:
    from app.api import runs
    from app.repositories.json_thread_repository import JsonMemoryRepository

    monkeypatch.setattr(runs, "RUNTIME_DATA_DIR", tmp_path)
    client = TestClient(app)

    response = client.post("/api/runs", json={"thread_id": "thread-blocked-memory", "message": "请做 match 分析"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_status"] == "blocked_by_prerequisite"
    assert payload["memory_updates"] == []
    assert JsonMemoryRepository(tmp_path).list_by_thread("thread-blocked-memory") == []


def test_training_submission_does_not_reset_active_goal(tmp_path: Path, monkeypatch) -> None:
    from app.api import runs
    from app.repositories.json_repository import JsonArtifactRepository
    from app.repositories.json_thread_repository import JsonWorkspaceContextRepository
    from app.schemas.runs import WorkspaceContext

    monkeypatch.setattr(runs, "RUNTIME_DATA_DIR", tmp_path)
    artifact_repo = JsonArtifactRepository(tmp_path)
    context_repo = JsonWorkspaceContextRepository(tmp_path)
    artifact_repo.save("profile", "profile-1", {"content": {}}, "thread-goal-preserve", "profile")
    artifact_repo.save("job_analysis", "job-1", {"content": {}}, "thread-goal-preserve", "job")
    artifact_repo.save("match", "match-1", {"content": {}}, "thread-goal-preserve", "match")
    artifact_repo.save("plan", "plan-1", {"content": {}}, "thread-goal-preserve", "planning")
    context_repo.save(
        WorkspaceContext(
            thread_id="thread-goal-preserve",
            active_goal="Agent 开发工程师",
            active_profile_id="profile-1",
            active_job_analysis_id="job-1",
            active_match_id="match-1",
            active_plan_id="plan-1",
            updated_by_run_id="seed",
        )
    )
    client = TestClient(app)

    response = client.post(
        "/api/runs",
        json={"thread_id": "thread-goal-preserve", "message": "我的训练答案：我会设计 FastAPI + LangGraph demo。"},
    )

    assert response.status_code == 200
    context = JsonWorkspaceContextRepository(tmp_path).get("thread-goal-preserve")
    assert context.active_goal == "Agent 开发工程师"


def test_runs_endpoint_backfills_workspace_context_from_existing_thread_artifacts(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from app.api import runs
    from app.repositories.json_repository import JsonArtifactRepository
    from app.repositories.json_thread_repository import JsonWorkspaceContextRepository

    monkeypatch.setattr(runs, "RUNTIME_DATA_DIR", tmp_path)
    artifact_repo = JsonArtifactRepository(tmp_path)
    artifact_repo.save("profile", "profile-seeded", {"content": {}}, "thread-seeded-chain", "profile")
    artifact_repo.save("job_analysis", "job-seeded", {"content": {}}, "thread-seeded-chain", "job")
    client = TestClient(app)

    match_response = client.post(
        "/api/runs",
        json={"thread_id": "thread-seeded-chain", "message": "请做 match 分析"},
    )
    plan_response = client.post(
        "/api/runs",
        json={"thread_id": "thread-seeded-chain", "message": "生成三个月路径规划"},
    )

    assert match_response.status_code == 200
    assert match_response.json()["run_status"] == "completed"
    assert plan_response.status_code == 200
    payload = plan_response.json()
    assert payload["run_status"] == "completed"
    context = JsonWorkspaceContextRepository(tmp_path).get("thread-seeded-chain")
    assert context.active_profile_id == "profile-seeded"
    assert context.active_job_analysis_id == "job-seeded"
    assert context.active_match_id
    assert context.active_plan_id


def test_runs_endpoint_backfill_does_not_mix_artifacts_from_different_chains(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from app.api import runs
    from app.repositories.json_repository import JsonArtifactRepository
    from app.repositories.json_thread_repository import JsonWorkspaceContextRepository

    monkeypatch.setattr(runs, "RUNTIME_DATA_DIR", tmp_path)
    artifact_repo = JsonArtifactRepository(tmp_path)
    artifact_repo.save("profile", "profile-old", {"content": {}}, "thread-multi-chain", "profile")
    artifact_repo.save("job_analysis", "job-old", {"content": {}}, "thread-multi-chain", "job")
    artifact_repo.save(
        "match",
        "match-old",
        {"content": {}},
        "thread-multi-chain",
        "match",
        ["profile-old", "job-old"],
    )
    artifact_repo.save("profile", "profile-new", {"content": {}}, "thread-multi-chain", "profile")
    artifact_repo.save("job_analysis", "job-new", {"content": {}}, "thread-multi-chain", "job")
    client = TestClient(app)

    response = client.post(
        "/api/runs",
        json={"thread_id": "thread-multi-chain", "message": "生成三个月路径规划"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_status"] == "blocked_by_prerequisite"
    assert payload["missing_artifacts"] == ["match"]
    assert JsonArtifactRepository(tmp_path).list_by_kind("thread-multi-chain", "plan") == []
    context = JsonWorkspaceContextRepository(tmp_path).get("thread-multi-chain")
    assert context.active_profile_id == "profile-new"
    assert context.active_job_analysis_id == "job-new"
    assert context.active_match_id is None


def test_runs_endpoint_failed_response_does_not_leak_unexpected_exception_detail(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from app.api import runs
    from app.services import run_orchestrator

    def fail_unexpectedly(*args, **kwargs):
        raise ValueError("secret stack detail")

    monkeypatch.setattr(runs, "RUNTIME_DATA_DIR", tmp_path)
    monkeypatch.setattr(run_orchestrator, "run_career_graph", fail_unexpectedly)
    client = TestClient(app)

    response = client.post(
        "/api/runs",
        json={"thread_id": "thread-unexpected-error", "message": "请分析岗位"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_status"] == "failed"
    assert "secret stack detail" not in payload["assistant_message"]["content"]
    assert payload["warnings"] == ["unexpected_runtime_error"]


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


def test_agent_specific_post_endpoints_do_not_execute_langgraph_runtime(tmp_path: Path, monkeypatch) -> None:
    from app.api import interviews, training

    monkeypatch.setattr(training, "RUNTIME_DATA_DIR", tmp_path)
    monkeypatch.setattr(interviews, "RUNTIME_DATA_DIR", tmp_path)
    client = TestClient(app)

    training_response = client.post(
        "/api/training",
        json={"thread_id": "thread-no-agent-endpoints", "message": "根据能力差距给我一个训练任务"},
    )
    interview_response = client.post(
        "/api/interviews",
        json={"thread_id": "thread-no-agent-endpoints", "message": "开始模拟面试"},
    )

    assert training_response.status_code == 410
    assert interview_response.status_code == 410
    assert "/api/runs" in training_response.json()["detail"]
    assert "/api/runs" in interview_response.json()["detail"]
    assert JsonArtifactRepository(tmp_path).list_by_thread("thread-no-agent-endpoints") == []


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


def test_report_export_updates_active_report_context(tmp_path: Path, monkeypatch) -> None:
    from app.api import interviews, reports, runs, training
    from app.repositories.json_thread_repository import JsonWorkspaceContextRepository

    monkeypatch.setattr(runs, "RUNTIME_DATA_DIR", tmp_path)
    monkeypatch.setattr(training, "RUNTIME_DATA_DIR", tmp_path)
    monkeypatch.setattr(interviews, "RUNTIME_DATA_DIR", tmp_path)
    monkeypatch.setattr(reports, "RUNTIME_DATA_DIR", tmp_path)
    client = TestClient(app)
    thread_id = "thread-report-context"

    for message in complete_demo_messages():
        response = client.post("/api/runs", json={"thread_id": thread_id, "message": message})
        assert response.status_code == 200

    report = client.get(f"/api/reports/{thread_id}/markdown")

    assert report.status_code == 200
    context = JsonWorkspaceContextRepository(tmp_path).get(thread_id)
    assert context.active_report_id == f"report-{thread_id}-latest"


def test_report_export_rejects_task_only_training_result(tmp_path: Path, monkeypatch) -> None:
    from app.api import reports

    monkeypatch.setattr(reports, "RUNTIME_DATA_DIR", tmp_path)
    thread_id = "thread-report-task-only"
    _seed_report_chain(tmp_path, thread_id, training_score=None, turn_count=3)
    client = TestClient(app)

    report = client.get(f"/api/reports/{thread_id}/markdown")

    assert report.status_code == 409
    assert "training answer" in report.json()["detail"]


def test_report_export_rejects_interview_summary_under_three_turns(tmp_path: Path, monkeypatch) -> None:
    from app.api import reports

    monkeypatch.setattr(reports, "RUNTIME_DATA_DIR", tmp_path)
    thread_id = "thread-report-two-turns"
    _seed_report_chain(tmp_path, thread_id, training_score=82, turn_count=2)
    client = TestClient(app)

    report = client.get(f"/api/reports/{thread_id}/markdown")

    assert report.status_code == 409
    assert "fewer than three interview turns" in report.json()["detail"]


def test_report_export_fallback_survives_workspace_restore_for_legacy_thread(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from app.api import reports, threads
    from app.repositories.json_thread_repository import JsonWorkspaceContextRepository

    monkeypatch.setattr(reports, "RUNTIME_DATA_DIR", tmp_path)
    monkeypatch.setattr(threads, "RUNTIME_DATA_DIR", tmp_path)
    thread_id = "thread-report-legacy-workspace"
    _seed_report_chain(tmp_path, thread_id, training_score=82, turn_count=3, save_context=False)
    client = TestClient(app)

    workspace = client.get(f"/api/threads/{thread_id}/workspace")
    report = client.get(f"/api/reports/{thread_id}/markdown")

    assert workspace.status_code == 200
    assert report.status_code == 200
    context = JsonWorkspaceContextRepository(tmp_path).get(thread_id)
    assert context.active_profile_id == f"profile-{thread_id}"
    assert context.active_report_id == f"report-{thread_id}-latest"


def test_report_export_without_context_is_repeatable(tmp_path: Path, monkeypatch) -> None:
    from app.api import reports

    monkeypatch.setattr(reports, "RUNTIME_DATA_DIR", tmp_path)
    thread_id = "thread-report-repeatable-legacy"
    _seed_report_chain(tmp_path, thread_id, training_score=82, turn_count=3, save_context=False)
    client = TestClient(app)

    first = client.get(f"/api/reports/{thread_id}/markdown")
    second = client.get(f"/api/reports/{thread_id}/markdown")

    assert first.status_code == 200
    assert second.status_code == 200
    assert "# CareerAgent 职业发展报告" in second.text


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
