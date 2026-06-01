from app.repositories.json_repository import JsonArtifactRepository
from app.repositories.json_thread_repository import JsonWorkspaceContextRepository
from app.schemas.runs import WorkspaceContext
from app.services.workspace import (
    artifact_chain_from_context,
    build_active_artifact_facts,
    build_workspace_response,
    update_context_from_artifacts,
)


def test_workspace_context_tracks_active_chain_not_latest_kind(tmp_path):
    artifact_repo = JsonArtifactRepository(tmp_path)
    context_repo = JsonWorkspaceContextRepository(tmp_path)
    artifact_repo.save("job_analysis", "job-first", {"content": {"summary": "Agent 岗位"}}, "thread-a", "job")
    artifact_repo.save("match", "match-first", {"content": {"score": 80}}, "thread-a", "match", ["job-first"])
    artifact_repo.save("job_analysis", "job-second", {"content": {"summary": "产品岗位"}}, "thread-a", "job")
    context_repo.save(
        WorkspaceContext(
            thread_id="thread-a",
            active_goal="Agent 岗位链路",
            active_job_analysis_id="job-first",
            active_match_id="match-first",
            updated_by_run_id="run-first",
        )
    )

    workspace = build_workspace_response("thread-a", artifact_repo, context_repo)

    assert workspace.workspace_artifacts["job_analysis"]["id"] == "job-first"
    assert workspace.workspace_artifacts["match"]["id"] == "match-first"
    assert [item.id for item in workspace.artifact_chain] == ["job-first", "match-first"]


def test_update_context_from_artifacts_only_updates_created_kinds(tmp_path):
    artifact_repo = JsonArtifactRepository(tmp_path)
    context_repo = JsonWorkspaceContextRepository(tmp_path)
    artifact_repo.save("profile", "profile-1", {"content": {}}, "thread-a", "profile")
    artifact_repo.save("job_analysis", "job-1", {"content": {}}, "thread-a", "job")

    context = update_context_from_artifacts(
        thread_id="thread-a",
        run_id="run-1",
        created_artifact_ids=["profile-1", "job-1"],
        active_goal="Agent 开发",
        artifact_repo=artifact_repo,
        context_repo=context_repo,
    )

    assert context.active_profile_id == "profile-1"
    assert context.active_job_analysis_id == "job-1"
    assert context.updated_by_run_id == "run-1"


def test_update_context_preserves_existing_goal_when_active_goal_is_none(tmp_path):
    artifact_repo = JsonArtifactRepository(tmp_path)
    context_repo = JsonWorkspaceContextRepository(tmp_path)
    artifact_repo.save("profile", "profile-1", {"content": {}}, "thread-a", "profile")
    context_repo.save(
        WorkspaceContext(
            thread_id="thread-a",
            active_goal="Agent 开发工程师",
            active_profile_id="profile-1",
            updated_by_run_id="run-profile",
        )
    )
    artifact_repo.save("training_result", "training-1", {"content": {"has_submission": True}}, "thread-a", "training")

    context = update_context_from_artifacts(
        thread_id="thread-a",
        run_id="run-training",
        created_artifact_ids=["training-1"],
        active_goal=None,
        artifact_repo=artifact_repo,
        context_repo=context_repo,
    )

    assert context.active_goal == "Agent 开发工程师"
    assert context.active_training_result_id == "training-1"


def test_new_job_invalidates_downstream_active_chain(tmp_path):
    artifact_repo = JsonArtifactRepository(tmp_path)
    context_repo = JsonWorkspaceContextRepository(tmp_path)
    artifact_repo.save("job_analysis", "job-first", {"content": {}}, "thread-a", "job")
    artifact_repo.save("match", "match-first", {"content": {}}, "thread-a", "match")
    artifact_repo.save("plan", "plan-first", {"content": {}}, "thread-a", "planning")
    artifact_repo.save("training_result", "training-first", {"content": {}}, "thread-a", "training")
    artifact_repo.save("interview_summary", "interview-first", {"content": {}}, "thread-a", "interview")
    context_repo.save(
        WorkspaceContext(
            thread_id="thread-a",
            active_goal="第一条链",
            active_job_analysis_id="job-first",
            active_match_id="match-first",
            active_plan_id="plan-first",
            active_training_result_id="training-first",
            active_interview_summary_id="interview-first",
            updated_by_run_id="run-first",
        )
    )
    artifact_repo.save("job_analysis", "job-second", {"content": {}}, "thread-a", "job")

    context = update_context_from_artifacts(
        thread_id="thread-a",
        run_id="run-second",
        created_artifact_ids=["job-second"],
        active_goal="第二条链",
        artifact_repo=artifact_repo,
        context_repo=context_repo,
    )

    assert context.active_job_analysis_id == "job-second"
    assert context.active_match_id is None
    assert context.active_plan_id is None
    assert context.active_training_result_id is None
    assert context.active_interview_summary_id is None


def test_active_artifact_facts_require_submitted_training_and_three_interview_turns(tmp_path):
    artifact_repo = JsonArtifactRepository(tmp_path)
    artifact_repo.save("profile", "profile-1", {"content": {}}, "thread-a", "profile")
    artifact_repo.save("job_analysis", "job-1", {"content": {}}, "thread-a", "job")
    artifact_repo.save("match", "match-1", {"content": {}}, "thread-a", "match")
    artifact_repo.save("plan", "plan-1", {"content": {}}, "thread-a", "planning")
    artifact_repo.save(
        "training_result",
        "training-1",
        {"content": {"task": "写一个 Agent demo", "has_submission": False, "score": None}},
        "thread-a",
        "training",
    )
    artifact_repo.save(
        "interview_summary",
        "interview-1",
        {"content": {"turn_count": 2, "completed": False}},
        "thread-a",
        "interview",
    )
    context = WorkspaceContext(
        thread_id="thread-a",
        active_goal="Agent 开发",
        active_profile_id="profile-1",
        active_job_analysis_id="job-1",
        active_match_id="match-1",
        active_plan_id="plan-1",
        active_training_result_id="training-1",
        active_interview_summary_id="interview-1",
        updated_by_run_id="run-1",
    )

    facts = build_active_artifact_facts(context, artifact_repo)

    assert facts.has_training_result is True
    assert facts.training_submitted is False
    assert facts.training_scored is False
    assert facts.has_interview_summary is True
    assert facts.interview_turn_count == 2
    assert facts.interview_completed is False


def test_active_artifact_facts_does_not_trust_completed_flag_without_three_turns(tmp_path):
    artifact_repo = JsonArtifactRepository(tmp_path)
    artifact_repo.save("profile", "profile-1", {"content": {}}, "thread-a", "profile")
    artifact_repo.save("job_analysis", "job-1", {"content": {}}, "thread-a", "job")
    artifact_repo.save("match", "match-1", {"content": {}}, "thread-a", "match")
    artifact_repo.save("plan", "plan-1", {"content": {}}, "thread-a", "planning")
    artifact_repo.save(
        "training_result",
        "training-1",
        {"content": {"has_submission": True, "submission": "demo", "score": 82}},
        "thread-a",
        "training",
    )
    artifact_repo.save(
        "interview_summary",
        "interview-1",
        {"content": {"turn_count": 2, "completed": True}},
        "thread-a",
        "interview",
    )
    context = WorkspaceContext(
        thread_id="thread-a",
        active_goal="Agent 开发",
        active_profile_id="profile-1",
        active_job_analysis_id="job-1",
        active_match_id="match-1",
        active_plan_id="plan-1",
        active_training_result_id="training-1",
        active_interview_summary_id="interview-1",
        updated_by_run_id="run-1",
    )

    facts = build_active_artifact_facts(context, artifact_repo)

    assert facts.interview_turn_count == 2
    assert facts.interview_completed is False


def test_active_artifact_facts_ignores_missing_and_cross_thread_active_ids(tmp_path):
    artifact_repo = JsonArtifactRepository(tmp_path)
    artifact_repo.save(
        "training_result",
        "training-other-thread",
        {"content": {"has_submission": True, "submission": "demo", "score": 82}},
        "thread-b",
        "training",
    )
    artifact_repo.save(
        "interview_summary",
        "interview-other-thread",
        {"content": {"turn_count": 3, "completed": True}},
        "thread-b",
        "interview",
    )
    context = WorkspaceContext(
        thread_id="thread-a",
        active_goal="Agent 开发",
        active_profile_id="missing-profile",
        active_training_result_id="training-other-thread",
        active_interview_summary_id="interview-other-thread",
        updated_by_run_id="run-1",
    )

    facts = build_active_artifact_facts(context, artifact_repo)

    assert facts.has_profile is False
    assert facts.has_training_result is False
    assert facts.training_submitted is False
    assert facts.training_scored is False
    assert facts.has_interview_summary is False
    assert facts.interview_turn_count == 0
    assert facts.interview_completed is False


def test_artifact_chain_from_context_ignores_missing_optional_ids(tmp_path):
    artifact_repo = JsonArtifactRepository(tmp_path)
    artifact_repo.save("profile", "profile-1", {"content": {}}, "thread-a", "profile")
    context = WorkspaceContext(
        thread_id="thread-a",
        active_goal="Agent 开发",
        active_profile_id="profile-1",
        active_report_id=None,
        updated_by_run_id="run-1",
    )

    chain = artifact_chain_from_context(context, artifact_repo)

    assert [item.id for item in chain] == ["profile-1"]
