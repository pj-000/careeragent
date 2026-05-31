from collections.abc import Iterable, Mapping
from hashlib import sha256
from typing import Any

from app.schemas.memory import LongTermMemoryItem, MemoryScope


ALLOWED_MEMORY_SCOPES = set(MemoryScope)


class MemoryManager:
    def evaluate_candidates(self, candidates: Iterable[Mapping[str, Any]]) -> list[LongTermMemoryItem]:
        accepted: list[LongTermMemoryItem] = []
        for candidate in candidates:
            scope = _memory_scope(candidate.get("scope"))
            fact = candidate.get("fact")
            if scope is None or not isinstance(fact, str) or not fact.strip():
                continue
            accepted.append(
                LongTermMemoryItem(
                    id=str(candidate.get("id") or _memory_id(scope.value, fact)),
                    thread_id=str(candidate.get("thread_id") or "thread-unknown"),
                    scope=scope,
                    fact=fact,
                    source_artifact_id=candidate.get("source_artifact_id"),
                    confidence=candidate.get("confidence", 1.0),
                )
            )
        return accepted


def _memory_id(scope: str, fact: str) -> str:
    digest = sha256(f"{scope}:{fact}".encode("utf-8")).hexdigest()[:12]
    return f"memory-{digest}"


def _memory_scope(value: object) -> MemoryScope | None:
    try:
        scope = MemoryScope(value)
    except (TypeError, ValueError):
        return None
    return scope if scope in ALLOWED_MEMORY_SCOPES else None
