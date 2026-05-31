from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.repositories.interfaces import ArtifactRepository


SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,255}$")


class JsonArtifactRepository(ArtifactRepository):
    def __init__(self, root: Path) -> None:
        self.root = root
        self.artifact_dir = root / "artifacts"
        self.index_path = root / "artifacts-index.json"
        self.artifact_dir.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        kind: str,
        artifact_id: str,
        payload: dict[str, Any],
        source_thread_id: str,
        source_agent: str,
        parent_artifact_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        self._validate_id(artifact_id)
        now = datetime.now(timezone.utc).isoformat()
        current = self.get(artifact_id) if self._path_for(artifact_id).exists() else None
        record = {
            "schema_version": 1,
            "id": artifact_id,
            "kind": kind,
            "source_thread_id": source_thread_id,
            "source_agent": source_agent,
            "parent_artifact_ids": parent_artifact_ids or [],
            "payload": payload,
            "created_at": current["created_at"] if current else now,
            "updated_at": now,
        }
        self._atomic_write(self._path_for(artifact_id), record)
        self._write_index()
        return record

    def get(self, artifact_id: str) -> dict[str, Any]:
        self._validate_id(artifact_id)
        with self._path_for(artifact_id).open("r", encoding="utf-8") as f:
            return json.load(f)

    def list(self, kind: str | None = None, thread_id: str | None = None) -> list[dict[str, str]]:
        records = []
        for path in sorted(self.artifact_dir.glob("*.json")):
            with path.open("r", encoding="utf-8") as f:
                record = json.load(f)
            if kind is not None and record["kind"] != kind:
                continue
            if thread_id is not None and record["source_thread_id"] != thread_id:
                continue
            records.append(
                {
                    "id": record["id"],
                    "kind": record["kind"],
                    "source_thread_id": record["source_thread_id"],
                    "source_agent": record["source_agent"],
                }
            )
        return records

    def list_by_thread(self, thread_id: str) -> list[dict[str, str]]:
        return self.list(thread_id=thread_id)

    def list_by_kind(self, thread_id: str, kind: str) -> list[dict[str, str]]:
        return self.list(kind=kind, thread_id=thread_id)

    def _path_for(self, artifact_id: str) -> Path:
        return self.artifact_dir / f"{artifact_id}.json"

    def _validate_id(self, artifact_id: str) -> None:
        if not SAFE_ID.match(artifact_id):
            raise ValueError(f"Invalid artifact_id: {artifact_id}")

    def _write_index(self) -> None:
        self._atomic_write(self.index_path, self.list())

    def _atomic_write(self, path: Path, payload: Any) -> None:
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
