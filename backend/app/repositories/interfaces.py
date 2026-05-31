from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


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
