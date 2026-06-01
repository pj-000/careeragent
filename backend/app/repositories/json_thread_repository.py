from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

from app.repositories.interfaces import ConversationRepository, MemoryItemRepository, WorkspaceContextRepository
from app.schemas.memory import MemoryItem, MemoryScope, MemoryStatus
from app.schemas.runs import ConversationMessage, WorkspaceContext


SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,255}$")
ModelT = TypeVar("ModelT", bound=BaseModel)


class JsonConversationRepository(ConversationRepository):
    def __init__(self, root: Path) -> None:
        self.root = root
        self.message_dir = root / "messages"
        self.message_dir.mkdir(parents=True, exist_ok=True)

    def save(self, message: ConversationMessage) -> ConversationMessage:
        _validate_id(message.id, "message_id")
        path = _thread_dir(self.message_dir, message.thread_id) / f"{message.id}.json"
        _atomic_write(path, message.model_dump(mode="json"))
        return message

    def list_by_thread(self, thread_id: str) -> list[ConversationMessage]:
        messages = _read_models(_thread_dir(self.message_dir, thread_id), ConversationMessage)
        scoped = [message for message in messages if message.thread_id == thread_id]
        return sorted(scoped, key=lambda message: (message.created_at, message.id))


class JsonWorkspaceContextRepository(WorkspaceContextRepository):
    def __init__(self, root: Path) -> None:
        self.root = root
        self.context_dir = root / "workspace-contexts"
        self.context_dir.mkdir(parents=True, exist_ok=True)

    def save(self, context: WorkspaceContext) -> WorkspaceContext:
        path = self.context_dir / f"{_thread_key(context.thread_id)}.json"
        _atomic_write(path, context.model_dump(mode="json"))
        return context

    def get(self, thread_id: str) -> WorkspaceContext | None:
        path = self.context_dir / f"{_thread_key(thread_id)}.json"
        if not path.exists():
            return None
        context = WorkspaceContext.model_validate(json.loads(path.read_text(encoding="utf-8")))
        if context.thread_id != thread_id:
            return None
        return context


class JsonMemoryRepository(MemoryItemRepository):
    def __init__(self, root: Path) -> None:
        self.root = root
        self.memory_dir = root / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)

    def save(self, item: MemoryItem) -> MemoryItem:
        _validate_id(item.id, "memory_id")
        path = _thread_dir(self.memory_dir, item.thread_id) / f"{item.id}.json"
        _atomic_write(path, item.model_dump(mode="json"))
        return item

    def get(self, thread_id: str, memory_id: str) -> MemoryItem:
        _validate_id(memory_id, "memory_id")
        path = _thread_dir(self.memory_dir, thread_id) / f"{memory_id}.json"
        if not path.exists():
            raise KeyError(f"Memory item {memory_id!r} not found in thread {thread_id!r}")
        item = MemoryItem.model_validate(json.loads(path.read_text(encoding="utf-8")))
        if item.thread_id != thread_id:
            raise KeyError(f"Memory item {memory_id!r} is not in thread {thread_id!r}")
        return item

    def list_by_thread(self, thread_id: str) -> list[MemoryItem]:
        items = _read_models(_thread_dir(self.memory_dir, thread_id), MemoryItem)
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
    if not model_dir.exists():
        return models
    for path in sorted(model_dir.glob("*.json")):
        models.append(model_type.model_validate(json.loads(path.read_text(encoding="utf-8"))))
    return models


def _thread_dir(parent: Path, thread_id: str) -> Path:
    return parent / _thread_key(thread_id)


def _thread_key(thread_id: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", thread_id).strip("-") or "thread"
    slug = slug[:80].strip(".-") or "thread"
    digest = sha256(thread_id.encode("utf-8")).hexdigest()
    return f"{slug}-{digest}"


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
        _fsync_parent(path)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink()
        raise


def _fsync_parent(path: Path) -> None:
    try:
        dir_fd = os.open(path.parent, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)
