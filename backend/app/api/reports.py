from __future__ import annotations

import re
from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Path, Response

from app.api.runs import SAFE_THREAD_ID_PATTERN
from app.artifacts.markdown import (
    MissingArtifactError,
    build_markdown_report,
    build_markdown_report_from_chain,
    required_parent_artifact_ids,
    required_parent_artifact_ids_from_chain,
)
from app.repositories.json_repository import JsonArtifactRepository
from app.repositories.json_thread_repository import JsonWorkspaceContextRepository
from app.repositories.paths import RUNTIME_DATA_DIR
from app.services.workspace import artifact_chain_from_context, update_context_from_artifacts


router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/{thread_id}/markdown")
def export_markdown_report(
    thread_id: Annotated[str, Path(pattern=SAFE_THREAD_ID_PATTERN)],
) -> Response:
    if not re.match(SAFE_THREAD_ID_PATTERN, thread_id):
        raise HTTPException(status_code=422, detail="Unsafe thread_id")

    repo = JsonArtifactRepository(RUNTIME_DATA_DIR)
    context_repo = JsonWorkspaceContextRepository(RUNTIME_DATA_DIR)
    current_context = context_repo.get(thread_id)
    try:
        if current_context:
            chain = artifact_chain_from_context(current_context, repo)
            artifacts = [repo.get(item.id) for item in chain]
            markdown = build_markdown_report_from_chain(thread_id, artifacts)
            parent_artifact_ids = required_parent_artifact_ids_from_chain(thread_id, artifacts)
        else:
            artifact_refs = repo.list_by_thread(thread_id)
            artifacts = [repo.get(artifact["id"]) for artifact in artifact_refs]
            markdown = build_markdown_report(thread_id, artifacts)
            parent_artifact_ids = required_parent_artifact_ids(thread_id, artifacts)
    except MissingArtifactError as exc:
        detail = _normalize_active_chain_error(thread_id, current_context, repo, str(exc))
        raise HTTPException(status_code=409, detail=detail) from exc

    report_artifact_id = f"report-{thread_id}-latest"
    repo.save(
        kind="report",
        artifact_id=report_artifact_id,
        payload={
            "title": "CareerAgent Markdown report",
            "format": "markdown",
            "content": markdown,
        },
        source_thread_id=thread_id,
        source_agent="report",
        parent_artifact_ids=parent_artifact_ids,
    )
    update_context_from_artifacts(
        thread_id=thread_id,
        run_id=f"report-export-{thread_id}",
        created_artifact_ids=[report_artifact_id],
        active_goal=current_context.active_goal if current_context else "职业发展报告",
        artifact_repo=repo,
        context_repo=context_repo,
    )
    return Response(content=markdown, media_type="text/markdown; charset=utf-8")


def _normalize_active_chain_error(
    thread_id: str,
    current_context: Any,
    repo: JsonArtifactRepository,
    detail: str,
) -> str:
    if current_context and "Missing required artifact kind: interview_summary" in detail:
        training = _artifact_content(repo, current_context.active_training_result_id)
        if not bool(training.get("has_submission")) or not _training_submission(training):
            return f"Missing training submission for {thread_id}: training answer is not submitted"
    if "fewer than three interview turns" in detail and "three interview answers" not in detail:
        return f"{detail}; requires three interview answers"
    return detail


def _artifact_content(repo: JsonArtifactRepository, artifact_id: str | None) -> dict[str, Any]:
    if not artifact_id:
        return {}
    try:
        artifact = repo.get(artifact_id)
    except (FileNotFoundError, KeyError, ValueError):
        return {}
    payload = artifact.get("payload")
    if not isinstance(payload, dict):
        return {}
    content = payload.get("content")
    return content if isinstance(content, dict) else {}


def _training_submission(training: dict[str, Any]) -> str:
    submission = training.get("submission")
    if isinstance(submission, str) and submission.strip():
        return submission
    return ""
