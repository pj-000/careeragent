from pathlib import Path

import pytest

from app.agents.manifests import AGENT_MANIFESTS
from app.agents.runtime import AgentRuntimeContext, PermissionDenied
from app.graphs.workflow import build_graph, run_career_graph
from app.repositories.json_repository import JsonArtifactRepository


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
    assert first.thread_id == thread_id
    assert first.active_agent == "memory_manager"
    assert "profile" in first_kinds
    assert "compaction_snapshot" in first_kinds
    assert first.artifacts == first_records
    assert "profile/resume_parsing" in first.used_skill_refs
    assert "memory/context_compaction" in first.used_skill_refs

    second = run_career_graph(thread_id, "请做 match 分析", repo)

    second_records = repo.list_by_thread(thread_id)
    second_kinds = {record["kind"] for record in second_records}
    assert second.thread_id == thread_id
    assert second.active_agent == "memory_manager"
    assert "match" in second_kinds
    assert len(second_records) > len(first_records)
    assert set(first.artifacts[0]) == {"id", "kind", "source_thread_id", "source_agent"}
    assert {record["id"] for record in first_records}.issubset({record["id"] for record in second_records})


def test_graph_get_state_restores_checkpoint_for_same_thread(tmp_path: Path) -> None:
    repo = JsonArtifactRepository(tmp_path)
    graph = build_graph(artifact_repo=repo)
    config = {"configurable": {"thread_id": "checkpoint-thread"}}

    graph.invoke(
        {"thread_id": "checkpoint-thread", "user_message": "请给我一个 plan"},
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
