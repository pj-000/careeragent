from pathlib import Path

import pytest

from app.agents.manifests import AGENT_MANIFESTS
from app.agents.runtime import AgentRuntimeContext, PermissionDenied
from app.graphs.workflow import build_graph, run_career_graph
from app.repositories.json_repository import JsonArtifactRepository
from app.schemas.runs import RunStatus


def test_build_graph_uses_real_langgraph_nodes_and_conditional_edges(tmp_path: Path) -> None:
    repo = JsonArtifactRepository(tmp_path)

    graph = build_graph(artifact_repo=repo)
    drawable = graph.get_graph()

    assert hasattr(graph, "invoke")
    assert hasattr(graph, "get_graph")
    assert {
        "supervisor",
        "profile",
        "job",
        "match",
        "planning",
        "training",
        "interview",
        "report",
        "memory_manager",
    }.issubset(drawable.nodes)
    assert any(edge.conditional for edge in drawable.edges)
    assert any(edge.source == "supervisor" and edge.conditional for edge in drawable.edges)


def test_run_career_graph_persists_artifacts_and_supports_same_thread_followup(tmp_path: Path) -> None:
    repo = JsonArtifactRepository(tmp_path)
    thread_id = "thread-vslice"

    first = run_career_graph(thread_id, "请从我的 resume 建立 profile", repo)

    first_records = repo.list_by_thread(thread_id)
    first_kinds = {record["kind"] for record in first_records}
    first_compaction_run_ids = [
        repo.get(record["id"])["payload"]["source_run_id"]
        for record in first_records
        if record["kind"] == "compaction_snapshot"
    ]
    assert first.thread_id == thread_id
    assert first.active_agent == "memory_manager"
    assert "profile" in first_kinds
    assert "compaction_snapshot" in first_kinds
    assert first_compaction_run_ids == [first.run_id]
    assert first.artifacts == first_records
    assert "profile/resume_parsing" in first.used_skill_refs
    assert first.used_skill_runtime_refs
    assert first.used_skill_runtime_refs[0].skill_id
    assert "memory/context_compaction" in first.used_skill_refs

    second = run_career_graph(thread_id, "请分析 Agent 开发岗位 JD", repo)
    third = run_career_graph(thread_id, "请做 match 分析", repo)

    third_records = repo.list_by_thread(thread_id)
    third_kinds = {record["kind"] for record in third_records}
    third_compaction_run_ids = [
        repo.get(record["id"])["payload"]["source_run_id"]
        for record in third_records
        if record["kind"] == "compaction_snapshot"
    ]
    assert second.thread_id == thread_id
    assert third.thread_id == thread_id
    assert second.active_agent == "memory_manager"
    assert third.active_agent == "memory_manager"
    assert "job_analysis" in third_kinds
    assert "match" in third_kinds
    assert second.run_id in third_compaction_run_ids
    assert third.run_id in third_compaction_run_ids
    assert len(third_records) > len(first_records)
    assert set(first.artifacts[0]) == {"id", "kind", "source_thread_id", "source_agent"}
    assert {record["id"] for record in first_records}.issubset({record["id"] for record in third_records})


def test_graph_get_state_restores_checkpoint_for_same_thread(tmp_path: Path) -> None:
    repo = JsonArtifactRepository(tmp_path)
    graph = build_graph(artifact_repo=repo)
    config = {"configurable": {"thread_id": "checkpoint-thread"}}

    graph.invoke(
        {
            "thread_id": "checkpoint-thread",
            "user_message": "请给我一个 plan",
            "metadata": {"active_artifact_kinds": ["profile", "job_analysis", "match"]},
        },
        config=config,
    )
    first_state = graph.get_state(config)
    first_artifact_ids = list(first_state.values["artifact_ids"])

    assert first_artifact_ids
    assert any(repo.get(artifact_id)["kind"] == "plan" for artifact_id in first_artifact_ids)

    graph.invoke(
        {"thread_id": "checkpoint-thread", "user_message": "继续做记忆压缩"},
        config=config,
    )
    restored_state = graph.get_state(config)

    assert set(first_artifact_ids).issubset(set(restored_state.values["artifact_ids"]))
    assert restored_state.values["compaction_snapshot_id"] in restored_state.values["artifact_ids"]


def test_direct_graph_invoke_without_run_id_uses_fresh_compaction_run_id_each_time(tmp_path: Path) -> None:
    repo = JsonArtifactRepository(tmp_path)
    graph = build_graph(artifact_repo=repo)
    thread_id = "direct-run-id-thread"
    config = {"configurable": {"thread_id": thread_id}}

    graph.invoke({"thread_id": thread_id, "user_message": "请从我的 resume 建立 profile"}, config=config)
    graph.invoke({"thread_id": thread_id, "user_message": "生成三个月路径规划"}, config=config)

    compaction_records = [
        repo.get(artifact["id"]) for artifact in repo.list_by_kind(thread_id=thread_id, kind="compaction_snapshot")
    ]
    source_run_ids = [record["payload"]["source_run_id"] for record in compaction_records]

    assert len(source_run_ids) >= 2
    assert len(source_run_ids) == len(set(source_run_ids))
    assert all(source_run_id.startswith("run-") for source_run_id in source_run_ids)
    assert "run-unknown" not in source_run_ids


def test_direct_graph_invoke_with_explicit_metadata_run_id_preserves_it(tmp_path: Path) -> None:
    repo = JsonArtifactRepository(tmp_path)
    graph = build_graph(artifact_repo=repo)
    thread_id = "direct-explicit-run-id-thread"

    graph.invoke(
        {
            "thread_id": thread_id,
            "user_message": "请从我的 resume 建立 profile",
            "metadata": {"run_id": "run-direct-explicit"},
        },
        config={"configurable": {"thread_id": thread_id}},
    )

    compaction_records = [
        repo.get(artifact["id"]) for artifact in repo.list_by_kind(thread_id=thread_id, kind="compaction_snapshot")
    ]

    assert [record["payload"]["source_run_id"] for record in compaction_records] == ["run-direct-explicit"]


def test_graph_state_records_supervisor_decision_and_business_agent(tmp_path: Path) -> None:
    repo = JsonArtifactRepository(tmp_path)
    graph = build_graph(artifact_repo=repo)
    thread_id = "decision-thread"

    state = graph.invoke(
        {
            "thread_id": thread_id,
            "user_message": "请做 match 分析",
            "metadata": {"active_artifact_kinds": ["profile", "job_analysis"]},
        },
        config={"configurable": {"thread_id": thread_id}},
    )

    decision = state["metadata"]["supervisor_decision"]
    assert decision["intent"] == "match"
    assert decision["target_agent"] == "match"
    assert decision["missing_prerequisites"] == []
    assert state["metadata"]["last_business_agent"] == "match"
    assert state["metadata"]["current_runtime_node"] == "memory_manager"


def test_match_without_prerequisites_is_blocked(tmp_path: Path) -> None:
    repo = JsonArtifactRepository(tmp_path)
    graph = build_graph(artifact_repo=repo)
    thread_id = "missing-match-prereqs-thread"

    state = graph.invoke(
        {"thread_id": thread_id, "user_message": "请做 match 分析"},
        config={"configurable": {"thread_id": thread_id}},
    )

    decision = state["metadata"]["supervisor_decision"]
    assert decision["intent"] == "match"
    assert decision["target_agent"] == "match"
    assert decision["missing_prerequisites"] == ["profile", "job_analysis"]
    assert state["metadata"]["last_business_agent"] is None
    assert repo.list_by_kind(thread_id=thread_id, kind="match") == []


def test_run_response_marks_blocked_prerequisite_status(tmp_path: Path) -> None:
    repo = JsonArtifactRepository(tmp_path)

    response = run_career_graph("blocked-run-status-thread", "请做 match 分析", repo)

    assert response.run_status == RunStatus.BLOCKED_BY_PREREQUISITE
    assert response.missing_artifacts == ["profile", "job_analysis"]
    assert response.blocking_reason


def test_missing_prerequisites_do_not_execute_target_agent(tmp_path: Path) -> None:
    repo = JsonArtifactRepository(tmp_path)
    graph = build_graph(artifact_repo=repo)
    thread_id = "missing-report-prereqs-thread"

    state = graph.invoke(
        {"thread_id": thread_id, "user_message": "请导出 Markdown 报告"},
        config={"configurable": {"thread_id": thread_id}},
    )

    decision = state["metadata"]["supervisor_decision"]
    assert decision["intent"] == "export_report"
    assert decision["missing_prerequisites"]
    assert state["metadata"]["last_business_agent"] is None
    assert repo.list_by_kind(thread_id=thread_id, kind="report") == []


def test_supervisor_uses_active_chain_kinds_before_thread_history(tmp_path: Path) -> None:
    repo = JsonArtifactRepository(tmp_path)
    graph = build_graph(artifact_repo=repo)
    thread_id = "active-chain-before-history-thread"
    repo.save(
        kind="match",
        artifact_id="old-match",
        payload={"title": "旧匹配分析"},
        source_thread_id=thread_id,
        source_agent="match",
    )

    state = graph.invoke(
        {
            "thread_id": thread_id,
            "user_message": "生成三个月路径规划",
            "metadata": {"active_artifact_kinds": ["profile", "job_analysis"]},
        },
        config={"configurable": {"thread_id": thread_id}},
    )

    decision = state["metadata"]["supervisor_decision"]
    assert decision["intent"] == "plan"
    assert decision["missing_prerequisites"] == ["match"]
    assert repo.list_by_kind(thread_id=thread_id, kind="plan") == []


def test_interview_with_training_artifact_but_no_scored_fact_is_blocked(tmp_path: Path) -> None:
    repo = JsonArtifactRepository(tmp_path)
    graph = build_graph(artifact_repo=repo)
    thread_id = "interview-active-facts-thread"

    state = graph.invoke(
        {
            "thread_id": thread_id,
            "user_message": "开始模拟面试",
            "metadata": {"active_artifact_kinds": ["profile", "job_analysis", "match", "plan", "training_result"]},
        },
        config={"configurable": {"thread_id": thread_id}},
    )

    decision = state["metadata"]["supervisor_decision"]
    assert decision["intent"] == "start_interview"
    assert decision["missing_prerequisites"] == []
    assert decision["missing_capabilities"] == ["training_scored"]
    assert state["metadata"]["last_business_agent"] is None
    assert repo.list_by_kind(thread_id=thread_id, kind="interview_summary") == []


def test_training_agent_scores_english_training_answer_route(tmp_path: Path) -> None:
    repo = JsonArtifactRepository(tmp_path)
    graph = build_graph(artifact_repo=repo)
    thread_id = "english-training-answer-thread"

    graph.invoke(
        {
            "thread_id": thread_id,
            "user_message": "training answer: I built a FastAPI and LangGraph demo.",
            "metadata": {"active_artifact_kinds": ["match", "plan", "training_result"]},
        },
        config={"configurable": {"thread_id": thread_id}},
    )

    training_records = [
        repo.get(artifact["id"]) for artifact in repo.list_by_kind(thread_id=thread_id, kind="training_result")
    ]
    latest_content = training_records[-1]["payload"]["content"]
    assert latest_content["has_submission"] is True
    assert latest_content["submission"] == "I built a FastAPI and LangGraph demo."
    assert latest_content["score"] is not None


def test_interview_agent_records_chinese_interview_answer_route(tmp_path: Path) -> None:
    repo = JsonArtifactRepository(tmp_path)
    graph = build_graph(artifact_repo=repo)
    thread_id = "chinese-interview-answer-thread"

    graph.invoke(
        {
            "thread_id": thread_id,
            "user_message": "面试答案：我会用 thread_id 保存会话状态。",
            "metadata": {
                "active_artifact_kinds": ["profile", "job_analysis", "match", "plan", "training_result"],
                "active_facts": {"training_scored": True},
            },
        },
        config={"configurable": {"thread_id": thread_id}},
    )

    interview_records = [
        repo.get(artifact["id"]) for artifact in repo.list_by_kind(thread_id=thread_id, kind="interview_summary")
    ]
    latest_content = interview_records[-1]["payload"]["content"]
    assert latest_content["answers"] == ["我会用 thread_id 保存会话状态。"]
    assert latest_content["turn_count"] == 1


def test_graph_handles_thread_ids_that_are_not_safe_artifact_ids(tmp_path: Path) -> None:
    repo = JsonArtifactRepository(tmp_path)

    response = run_career_graph("student/a b?career", "请做 match 分析", repo)

    assert response.thread_id == "student/a b?career"
    assert response.artifacts
    for artifact in response.artifacts:
        assert "/" not in artifact["id"]
        assert " " not in artifact["id"]
        assert "?" not in artifact["id"]


def test_graph_creates_unique_artifact_ids_for_same_thread_repeated_runs(tmp_path: Path) -> None:
    repo = JsonArtifactRepository(tmp_path)
    thread_id = "repeat-thread"

    run_career_graph(thread_id, "请做 match 分析", repo)
    run_career_graph(thread_id, "请做 match 分析", repo)

    artifact_ids = [artifact["id"] for artifact in repo.list_by_thread(thread_id)]
    assert len(artifact_ids) == len(set(artifact_ids))


def test_agent_trace_reports_skill_refs_for_each_agent_without_cross_attribution(tmp_path: Path) -> None:
    repo = JsonArtifactRepository(tmp_path)

    response = run_career_graph("trace-thread", "请从我的 resume 建立 profile", repo)
    trace_by_agent = {item.agent_id: item for item in response.agent_trace_summary}

    assert trace_by_agent["supervisor"].used_skill_refs == ["memory/context_compaction"]
    assert "memory/long_term_write_policy" not in trace_by_agent["supervisor"].used_skill_refs
    assert trace_by_agent["memory_manager"].used_skill_refs == [
        "memory/long_term_write_policy",
        "memory/context_compaction",
    ]


def test_agent_runtime_context_enforces_permissions_and_thread_scoped_artifact_reads(tmp_path: Path) -> None:
    repo = JsonArtifactRepository(tmp_path)
    profile_runtime = AgentRuntimeContext(
        thread_id="thread-a",
        agent_id="profile",
        artifact_repo=repo,
        manifest=AGENT_MANIFESTS["profile"],
    )
    profile_artifact_id = profile_runtime.save_artifact(
        kind="profile",
        artifact_id="profile-thread-a",
        payload={"name": "林晨"},
    )
    repo.save(
        kind="profile",
        artifact_id="profile-thread-b",
        payload={"name": "周然"},
        source_thread_id="thread-b",
        source_agent="profile",
    )

    assert profile_artifact_id == "profile-thread-a"
    assert [artifact["id"] for artifact in profile_runtime.list_artifacts()] == ["profile-thread-a"]

    with pytest.raises(PermissionDenied, match="memory scope"):
        profile_runtime.read_memory("artifacts")

    with pytest.raises(PermissionDenied, match="memory_write"):
        profile_runtime.write_memory_candidate({"scope": "profile", "fact": "User likes backend roles."})

    memory_runtime = AgentRuntimeContext(
        thread_id="thread-a",
        agent_id="memory_manager",
        artifact_repo=repo,
        manifest=AGENT_MANIFESTS["memory_manager"],
    )
    candidate = {"scope": "profile", "fact": "User likes backend roles."}
    assert memory_runtime.write_memory_candidate(candidate) == candidate

    with pytest.raises(PermissionDenied, match="handoff"):
        AgentRuntimeContext(
            thread_id="thread-a",
            agent_id="match",
            artifact_repo=repo,
            manifest=AGENT_MANIFESTS["match"],
        ).handoff_to("report")

    with pytest.raises(PermissionDenied, match="artifact_read"):
        memory_runtime.list_artifacts()

    with pytest.raises(PermissionDenied, match="tool"):
        profile_runtime._require_tool("external_search")


def test_training_agent_cannot_write_match_artifact(tmp_path: Path) -> None:
    repo = JsonArtifactRepository(tmp_path)
    training_runtime = AgentRuntimeContext(
        thread_id="thread-kind-gate",
        agent_id="training",
        artifact_repo=repo,
        manifest=AGENT_MANIFESTS["training"],
    )

    with pytest.raises(PermissionDenied, match="artifact kind 'match'"):
        training_runtime.save_artifact(
            kind="match",
            artifact_id="match-from-training",
            payload={"content": {"score": 74}},
        )
