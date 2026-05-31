from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

from app.schemas.memory import MemoryItem, MemoryScope, MemoryStatus
from app.schemas.runs import ConversationMessage, WorkspaceContext


SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,255}$")
ModelT = TypeVar("ModelT", bound=BaseModel)


class JsonConversationRepository:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.message_dir = root / "messages"
        self.message_dir.mkdir(parents=True, exist_ok=True)

    def save(self, message: ConversationMessage) -> ConversationMessage:
        _validate_id(message.id, "message_id")
        path = self.message_dir / f"{message.id}.json"
        _atomic_write(path, message.model_dump(mode="json"))
        return message

    def list_by_thread(self, thread_id: str) -> list[ConversationMessage]:
        messages = _read_models(self.message_dir, ConversationMessage)
        scoped = [message for message in messages if message.thread_id == thread_id]
        return sorted(scoped, key=lambda message: (message.created_at, message.id))


class JsonWorkspaceContextRepository:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.context_dir = root / "workspace-contexts"
        self.context_dir.mkdir(parents=True, exist_ok=True)

    def save(self, context: WorkspaceContext) -> WorkspaceContext:
        path = self.context_dir / f"{_safe_thread_filename(context.thread_id)}.json"
        _atomic_write(path, context.model_dump(mode="json"))
        return context

    def get(self, thread_id: str) -> WorkspaceContext | None:
        path = self.context_dir / f"{_safe_thread_filename(thread_id)}.json"
        if not path.exists():
            return None
        return WorkspaceContext.model_validate(json.loads(path.read_text(encoding="utf-8")))


class JsonMemoryRepository:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.memory_dir = root / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)

    def save(self, item: MemoryItem) -> MemoryItem:
        _validate_id(item.id, "memory_id")
        path = self.memory_dir / f"{item.id}.json"
        _atomic_write(path, item.model_dump(mode="json"))
        return item

    def get(self, thread_id: str, memory_id: str) -> MemoryItem:
        _validate_id(memory_id, "memory_id")
        path = self.memory_dir / f"{memory_id}.json"
        if not path.exists():
            raise KeyError(f"Memory item {memory_id!r} not found")
        item = MemoryItem.model_validate(json.loads(path.read_text(encoding="utf-8")))
        if item.thread_id != thread_id:
            raise KeyError(f"Memory item {memory_id!r} is not in thread {thread_id!r}")
        return item

    def list_by_thread(self, thread_id: str) -> list[MemoryItem]:
        items = _read_models(self.memory_dir, MemoryItem)
        scoped = [item for item in items if item.thread_id == thread_id]
        return sorted(scoped, key=lambda item: (item.created_at, item.id))

    def list_by_scope(self, thread_id: str, scope: MemoryScope) -> list[MemoryItem]:
        return [item for item in self.list_by_thread(thread_id) if item.scope == scope]

    def set_status(self, thread_id: str, memory_id: str, status: MemoryStatus) -> MemoryItem:
        item = self.get(thread_id, memory_id)
        updated = item.model_copy(update={"status": status, "updated_at": datetime.now(timezone.utc)})
        return self.save(updated)


def _read_models(model_dir: Path, model_type: type[ModelT]) -> list[ModelT]:
    models: list[ModelT] = []
    for path in sorted(model_dir.glob("*.json")):
        models.append(model_type.model_validate(json.loads(path.read_text(encoding="utf-8"))))
    return models


def _safe_thread_filename(thread_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", thread_id).strip("-") or "thread"


def _validate_id(value: str, label: str) -> None:
    if not SAFE_ID.match(value):
        raise ValueError(f"Invalid {label}: {value}")


def _atomic_write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_file = tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        delete=False,
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    tmp_path = Path(tmp_file.name)
    try:
        with tmp_file:
            json.dump(payload, tmp_file, ensure_ascii=False, indent=2)
            tmp_file.flush()
            os.fsync(tmp_file.fileno())
        os.replace(tmp_path, path)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink()
        raise
