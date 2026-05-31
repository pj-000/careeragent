import inspect

from app.agents.base import AgentRuntime
from app.agents.manifests import AGENT_MANIFESTS
from app.graphs.state import AgentSnapshot, CareerAgentState
from app.schemas.artifacts import Artifact, ArtifactKind
from app.schemas.runs import AgentTraceItem, RunResponse


EXPECTED_SKILL_REFS = {
    "supervisor": ["memory/context_compaction"],
    "memory_manager": ["memory/long_term_write_policy", "memory/context_compaction"],
    "profile": ["profile/resume_parsing", "profile/evidence_chain"],
    "job": ["job/jd_analysis", "job/agent_developer_role"],
    "match": ["match/match_scoring_rubric", "match/gap_diagnosis"],
    "planning": ["planning/career_path_planning", "planning/three_month_plan"],
    "training": ["training/workplace_task_generation", "training/submission_scoring"],
    "interview": ["interview/mock_interview_flow", "interview/answer_scoring"],
    "report": ["report/markdown_report"],
}


def test_agent_manifests_include_expected_agents_with_required_contract_fields() -> None:
    assert set(AGENT_MANIFESTS) == {
        "supervisor",
        "memory_manager",
        "profile",
        "job",
        "match",
        "planning",
        "training",
        "interview",
        "report",
    }

    for agent_id, manifest in AGENT_MANIFESTS.items():
        assert manifest.agent_id == agent_id
        assert manifest.goal
        assert manifest.success_criteria
        assert isinstance(manifest.input_schema, dict)
        assert isinstance(manifest.output_schema, dict)
        assert isinstance(manifest.allowed_tools, list)
        assert manifest.skill_policy.default_skill_ids == EXPECTED_SKILL_REFS[agent_id]
        assert isinstance(manifest.handoff_policy.allowed_targets, list)
        assert isinstance(manifest.readable_memory_scopes, list)
        assert isinstance(manifest.writable_memory_scopes, list)


def test_manifest_permissions_align_with_runtime_gate_expectations() -> None:
    for agent_id, manifest in AGENT_MANIFESTS.items():
        if manifest.writable_memory_scopes:
            assert "memory_write" in manifest.allowed_tools, agent_id

    memory_manager = AGENT_MANIFESTS["memory_manager"]
    assert "artifact_write" in memory_manager.allowed_tools
    assert "memory_write" in memory_manager.allowed_tools

    assert "report" not in AGENT_MANIFESTS["match"].handoff_policy.allowed_targets
    for agent_id in {"profile", "job", "match", "planning", "training", "interview", "report"}:
        assert "memory_manager" in AGENT_MANIFESTS[agent_id].handoff_policy.allowed_targets


def test_career_agent_state_defaults_to_supervisor_and_tracks_user_message() -> None:
    state = CareerAgentState(thread_id="thread-1", user_message="帮我准备面试")

    assert state.thread_id == "thread-1"
    assert state.active_agent == "supervisor"
    assert state.messages[-1] == {"role": "user", "content": "帮我准备面试"}
    assert state.loaded_skill_refs == []
    assert state.related_long_term_memory_refs == []
    assert state.artifact_ids == []
    assert state.agent_snapshots == {}
    assert state.pending_question is None
    assert state.compaction_snapshot_id is None
    assert state.next_agent is None
    assert state.warnings == []


def test_agent_snapshot_schema_tracks_private_agent_context() -> None:
    snapshot = AgentSnapshot(
        agent_id="profile",
        summary="Parsed resume and extracted evidence.",
        private_context={"resume_sections": ["experience"]},
        last_artifact_ids=["profile-1"],
    )

    assert snapshot.agent_id == "profile"
    assert snapshot.summary == "Parsed resume and extracted evidence."
    assert snapshot.private_context == {"resume_sections": ["experience"]}
    assert snapshot.last_artifact_ids == ["profile-1"]


def test_run_response_schema_exposes_agent_trace_and_next_actions() -> None:
    response = RunResponse(
        run_id="run-1",
        thread_id="thread-1",
        active_agent="supervisor",
        agent_trace_summary=[
            AgentTraceItem(
                agent_id="profile",
                summary="Created a profile artifact.",
                artifact_ids=["profile-1"],
                used_skill_refs=["profile/resume_parsing"],
            )
        ],
        used_skill_refs=["profile/resume_parsing"],
        artifacts=[{"id": "profile-1", "kind": "profile"}],
        next_actions=["Review extracted profile"],
        warnings=["Low confidence on dates"],
    )

    assert response.run_id == "run-1"
    assert response.thread_id == "thread-1"
    assert response.active_agent == "supervisor"
    assert response.agent_trace_summary[0].agent_id == "profile"
    assert response.agent_trace_summary[0].used_skill_refs == ["profile/resume_parsing"]
    assert response.used_skill_refs == ["profile/resume_parsing"]
    assert response.artifacts == [{"id": "profile-1", "kind": "profile"}]
    assert response.next_actions == ["Review extracted profile"]
    assert response.warnings == ["Low confidence on dates"]


def test_artifact_schema_has_v2_fields_and_expected_kinds() -> None:
    assert {kind.value for kind in ArtifactKind} == {
        "profile",
        "job_analysis",
        "match",
        "plan",
        "training_result",
        "interview_summary",
        "report",
        "compaction_snapshot",
    }

    artifact = Artifact(
        id="artifact-1",
        kind=ArtifactKind.PROFILE,
        source_thread_id="thread-1",
        source_agent="profile",
        payload={"name": "林晨"},
    )

    assert artifact.kind == ArtifactKind.PROFILE
    assert artifact.source_thread_id == "thread-1"
    assert artifact.source_agent == "profile"
    assert artifact.parent_artifact_ids == []
    assert artifact.created_at is not None
    assert artifact.updated_at is not None


def test_agent_runtime_save_artifact_protocol_signature_matches_v21_plan() -> None:
    signature = inspect.signature(AgentRuntime.save_artifact)

    assert list(signature.parameters) == [
        "self",
        "kind",
        "artifact_id",
        "payload",
        "parent_artifact_ids",
    ]
    assert signature.parameters["kind"].annotation is str
    assert signature.parameters["artifact_id"].annotation is str
    assert signature.parameters["payload"].annotation is dict
    assert signature.parameters["parent_artifact_ids"].default is None
    assert signature.return_annotation is str
