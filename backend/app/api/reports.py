from __future__ import annotations

import re
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Response

from app.api.runs import SAFE_THREAD_ID_PATTERN
from app.artifacts.markdown import (
    MissingArtifactError,
    build_markdown_report,
    required_parent_artifact_ids,
)
from app.repositories.json_repository import JsonArtifactRepository
from app.repositories.paths import RUNTIME_DATA_DIR


router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/{thread_id}/markdown")
def export_markdown_report(
    thread_id: Annotated[str, Path(pattern=SAFE_THREAD_ID_PATTERN)],
) -> Response:
    if not re.match(SAFE_THREAD_ID_PATTERN, thread_id):
        raise HTTPException(status_code=422, detail="Unsafe thread_id")

    repo = JsonArtifactRepository(RUNTIME_DATA_DIR)
    artifact_refs = repo.list_by_thread(thread_id)
    artifacts = [repo.get(artifact["id"]) for artifact in artifact_refs]
    try:
        markdown = build_markdown_report(thread_id, artifacts)
        parent_artifact_ids = required_parent_artifact_ids(thread_id, artifacts)
    except MissingArtifactError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    repo.save(
        kind="report",
        artifact_id=f"report-{thread_id}-latest",
        payload={
            "title": "CareerAgent Markdown report",
            "format": "markdown",
            "content": markdown,
        },
        source_thread_id=thread_id,
        source_agent="report",
        parent_artifact_ids=parent_artifact_ids,
    )
    return Response(content=markdown, media_type="text/markdown; charset=utf-8")
