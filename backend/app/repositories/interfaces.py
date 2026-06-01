from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.schemas.memory import MemoryItem, MemoryScope, MemoryStatus
from app.schemas.runs import ConversationMessage, WorkspaceContext


class ArtifactRepository(ABC):
    @abstractmethod
    def save(
        self,
        kind: str,
        artifact_id: str,
        payload: dict[str, Any],
        source_thread_id: str,
        source_agent: str,
        parent_artifact_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get(self, artifact_id: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def list(self, kind: str | None = None, thread_id: str | None = None) -> list[dict[str, str]]:
        raise NotImplementedError

    @abstractmethod
    def list_by_thread(self, thread_id: str) -> list[dict[str, str]]:
        raise NotImplementedError

    @abstractmethod
    def list_by_kind(self, thread_id: str, kind: str) -> list[dict[str, str]]:
        raise NotImplementedError


class ThreadRepository(ABC):
    """Boundary for future database-backed thread state persistence."""


class MemoryRepository(ABC):
    """Boundary for future database-backed long-term memory persistence."""


class ReportRepository(ABC):
    """Boundary for future database-backed report persistence."""


class ConversationRepository(ABC):
    @abstractmethod
    def save(self, message: ConversationMessage) -> ConversationMessage:
        raise NotImplementedError

    @abstractmethod
    def list_by_thread(self, thread_id: str) -> list[ConversationMessage]:
        raise NotImplementedError


class WorkspaceContextRepository(ABC):
    @abstractmethod
    def save(self, context: WorkspaceContext) -> WorkspaceContext:
        raise NotImplementedError

    @abstractmethod
    def get(self, thread_id: str) -> WorkspaceContext | None:
        raise NotImplementedError


class MemoryItemRepository(ABC):
    @abstractmethod
    def save(self, item: MemoryItem) -> MemoryItem:
        raise NotImplementedError

    @abstractmethod
    def get(self, thread_id: str, memory_id: str) -> MemoryItem:
        raise NotImplementedError

    @abstractmethod
    def list_by_thread(self, thread_id: str) -> list[MemoryItem]:
        raise NotImplementedError

    @abstractmethod
    def list_by_scope(self, thread_id: str, scope: MemoryScope) -> list[MemoryItem]:
        raise NotImplementedError

    @abstractmethod
    def set_status(self, thread_id: str, memory_id: str, status: MemoryStatus) -> MemoryItem:
        raise NotImplementedError
