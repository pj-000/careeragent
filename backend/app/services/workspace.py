from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.repositories.interfaces import ArtifactRepository, WorkspaceContextRepository
from app.schemas.runs import ActiveArtifactFacts, ArtifactChainItem, WorkspaceContext, WorkspaceResponse


CONTEXT_FIELD_BY_KIND = {
    "profile": "active_profile_id",
    "job_analysis": "active_job_analysis_id",
    "match": "active_match_id",
    "plan": "active_plan_id",
    "training_result": "active_training_result_id",
    "interview_summary": "active_interview_summary_id",
    "report": "active_report_id",
    "compaction_snapshot": "active_compaction_snapshot_id",
}

INVALIDATE_DOWNSTREAM = {
    "profile": [
        "active_job_analysis_id",
        "active_match_id",
        "active_plan_id",
        "active_training_result_id",
        "active_interview_summary_id",
        "active_report_id",
    ],
    "job_analysis": [
        "active_match_id",
        "active_plan_id",
        "active_training_result_id",
        "active_interview_summary_id",
        "active_report_id",
    ],
    "match": [
        "active_plan_id",
        "active_training_result_id",
        "active_interview_summary_id",
        "active_report_id",
    ],
    "plan": [
        "active_training_result_id",
        "active_interview_summary_id",
        "active_report_id",
    ],
    "training_result": ["active_interview_summary_id", "active_report_id"],
    "interview_summary": ["active_report_id"],
}

ORDERED_CONTEXT_FIELDS = [
    "active_profile_id",
    "active_job_analysis_id",
    "active_match_id",
    "active_plan_id",
    "active_training_result_id",
    "active_interview_summary_id",
    "active_report_id",
    "active_compaction_snapshot_id",
]


def update_context_from_artifacts(
    thread_id: str,
    run_id: str,
    created_artifact_ids: list[str],
    active_goal: str | None,
    artifact_repo: ArtifactRepository,
    context_repo: WorkspaceContextRepository,
) -> WorkspaceContext:
    current = context_repo.get(thread_id)
    values = (
        current.model_dump()
        if current
        else {
            "thread_id": thread_id,
            "active_goal": active_goal or "职业发展规划",
            "updated_by_run_id": run_id,
        }
    )
    if active_goal is not None:
        values["active_goal"] = active_goal
    values["updated_by_run_id"] = run_id
    values["updated_at"] = datetime.now(timezone.utc)

    for artifact_id in created_artifact_ids:
        artifact = _get_artifact_or_none(artifact_id, artifact_repo)
        if not artifact or artifact.get("source_thread_id") != thread_id:
            continue
        kind = str(artifact.get("kind"))
        for field_name in INVALIDATE_DOWNSTREAM.get(kind, []):
            values[field_name] = None
        active_field = CONTEXT_FIELD_BY_KIND.get(kind)
        if active_field:
            values[active_field] = artifact_id

    context = WorkspaceContext.model_validate(values)
    return context_repo.save(context)


def artifact_chain_from_context(
    context: WorkspaceContext,
    artifact_repo: ArtifactRepository,
) -> list[ArtifactChainItem]:
    chain: list[ArtifactChainItem] = []
    for field_name in ORDERED_CONTEXT_FIELDS:
        artifact_id = getattr(context, field_name)
        if not artifact_id:
            continue
        artifact = _get_artifact_or_none(artifact_id, artifact_repo)
        if not artifact or artifact.get("source_thread_id") != context.thread_id:
            continue
        chain.append(_to_chain_item(artifact))
    return chain


def build_workspace_response(
    thread_id: str,
    artifact_repo: ArtifactRepository,
    context_repo: WorkspaceContextRepository,
) -> WorkspaceResponse:
    context = context_repo.get(thread_id)
    if context is None:
        context = context_repo.save(
            WorkspaceContext(thread_id=thread_id, active_goal="职业发展规划", updated_by_run_id="initial")
        )
    artifact_chain = artifact_chain_from_context(context, artifact_repo)
    workspace_artifacts = {item.kind: artifact_repo.get(item.id) for item in artifact_chain}
    return WorkspaceResponse(
        thread_id=thread_id,
        active_context=context,
        workspace_artifacts=workspace_artifacts,
        artifact_chain=artifact_chain,
    )


def build_active_artifact_facts(
    context: WorkspaceContext,
    artifact_repo: ArtifactRepository,
) -> ActiveArtifactFacts:
    training_content = _artifact_content(context.active_training_result_id, context.thread_id, artifact_repo)
    submission = training_content.get("submission")
    training_submitted = bool(training_content.get("has_submission")) and isinstance(submission, str) and bool(
        submission.strip()
    )
    training_scored = training_submitted and training_content.get("score") is not None

    interview_content = _artifact_content(context.active_interview_summary_id, context.thread_id, artifact_repo)
    interview_turn_count = _interview_turn_count(interview_content)

    return ActiveArtifactFacts(
        has_profile=bool(context.active_profile_id),
        has_job_analysis=bool(context.active_job_analysis_id),
        has_match=bool(context.active_match_id),
        has_plan=bool(context.active_plan_id),
        has_training_result=bool(context.active_training_result_id),
        training_submitted=training_submitted,
        training_scored=training_scored,
        has_interview_summary=bool(context.active_interview_summary_id),
        interview_turn_count=interview_turn_count,
        interview_completed=interview_turn_count >= 3,
    )


def _artifact_content(
    artifact_id: str | None,
    thread_id: str,
    artifact_repo: ArtifactRepository,
) -> dict[str, Any]:
    if not artifact_id:
        return {}
    artifact = _get_artifact_or_none(artifact_id, artifact_repo)
    if not artifact or artifact.get("source_thread_id") != thread_id:
        return {}
    payload = artifact.get("payload")
    if not isinstance(payload, dict):
        return {}
    content = payload.get("content")
    return content if isinstance(content, dict) else {}


def _to_chain_item(artifact: dict[str, Any]) -> ArtifactChainItem:
    return ArtifactChainItem(
        id=artifact["id"],
        kind=artifact["kind"],
        source_thread_id=artifact["source_thread_id"],
        source_agent=artifact["source_agent"],
        parent_artifact_ids=artifact.get("parent_artifact_ids", []),
        updated_at=artifact.get("updated_at"),
    )


def _get_artifact_or_none(artifact_id: str, artifact_repo: ArtifactRepository) -> dict[str, Any] | None:
    try:
        return artifact_repo.get(artifact_id)
    except (FileNotFoundError, KeyError, ValueError):
        return None


def _interview_turn_count(content: dict[str, Any]) -> int:
    turn_count = content.get("turn_count")
    if isinstance(turn_count, int):
        return turn_count
    answers = content.get("answers")
    if isinstance(answers, list):
        return len(answers)
    turns = content.get("turns")
    if isinstance(turns, list):
        return len(turns)
    return 0
