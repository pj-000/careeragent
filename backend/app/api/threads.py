from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Path

from app.api.runs import SAFE_THREAD_ID_PATTERN
from app.repositories.json_repository import JsonArtifactRepository
from app.repositories.json_thread_repository import (
    JsonConversationRepository,
    JsonMemoryRepository,
    JsonWorkspaceContextRepository,
)
from app.repositories.paths import RUNTIME_DATA_DIR
from app.schemas.memory import MemoryItem, MemoryStatus
from app.schemas.runs import ConversationMessage, WorkspaceResponse
from app.services.workspace import build_workspace_response


router = APIRouter(prefix="/api/threads", tags=["threads"])


@router.get("/{thread_id}/workspace")
def get_workspace(
    thread_id: Annotated[str, Path(pattern=SAFE_THREAD_ID_PATTERN)],
) -> WorkspaceResponse:
    return build_workspace_response(
        thread_id,
        JsonArtifactRepository(RUNTIME_DATA_DIR),
        JsonWorkspaceContextRepository(RUNTIME_DATA_DIR),
    )


@router.get("/{thread_id}/messages")
def list_messages(
    thread_id: Annotated[str, Path(pattern=SAFE_THREAD_ID_PATTERN)],
) -> list[ConversationMessage]:
    return JsonConversationRepository(RUNTIME_DATA_DIR).list_by_thread(thread_id)


@router.get("/{thread_id}/artifacts")
def list_artifacts(
    thread_id: Annotated[str, Path(pattern=SAFE_THREAD_ID_PATTERN)],
) -> list[dict[str, Any]]:
    repo = JsonArtifactRepository(RUNTIME_DATA_DIR)
    return [repo.get(artifact["id"]) for artifact in repo.list_by_thread(thread_id)]


@router.get("/{thread_id}/memory")
def list_memory(
    thread_id: Annotated[str, Path(pattern=SAFE_THREAD_ID_PATTERN)],
) -> list[MemoryItem]:
    return JsonMemoryRepository(RUNTIME_DATA_DIR).list_by_thread(thread_id)


@router.post("/{thread_id}/memory/{memory_id}/confirm")
def confirm_memory(
    thread_id: Annotated[str, Path(pattern=SAFE_THREAD_ID_PATTERN)],
    memory_id: str,
) -> MemoryItem:
    return _set_memory_status(thread_id, memory_id, MemoryStatus.CONFIRMED)


@router.post("/{thread_id}/memory/{memory_id}/reject")
def reject_memory(
    thread_id: Annotated[str, Path(pattern=SAFE_THREAD_ID_PATTERN)],
    memory_id: str,
) -> MemoryItem:
    return _set_memory_status(thread_id, memory_id, MemoryStatus.REJECTED)


def _set_memory_status(thread_id: str, memory_id: str, status: MemoryStatus) -> MemoryItem:
    try:
        return JsonMemoryRepository(RUNTIME_DATA_DIR).set_status(thread_id, memory_id, status)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=404, detail="Memory item not found") from exc
