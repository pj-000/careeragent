import json
import os
from pathlib import Path

from app.repositories import json_repository
from app.repositories.json_repository import JsonArtifactRepository


def test_json_repository_writes_schema_version_and_index(tmp_path: Path) -> None:
    repo = JsonArtifactRepository(tmp_path)

    saved = repo.save(
        kind="profile",
        artifact_id="profile-1",
        source_thread_id="thread-a",
        source_agent="profile",
        parent_artifact_ids=[],
        payload={"name": "林晨", "skills": ["Python", "FastAPI"]},
    )

    assert saved["schema_version"] == 1
    assert saved["id"] == "profile-1"
    assert saved["kind"] == "profile"
    assert saved["source_thread_id"] == "thread-a"
    assert saved["source_agent"] == "profile"
    assert saved["parent_artifact_ids"] == []
    assert repo.get("profile-1")["payload"]["name"] == "林晨"
    index = repo.list(kind="profile", thread_id="thread-a")
    assert index == [
        {
            "id": "profile-1",
            "kind": "profile",
            "source_thread_id": "thread-a",
            "source_agent": "profile",
        }
    ]
    persisted_index = json.loads((tmp_path / "artifacts-index.json").read_text(encoding="utf-8"))
    assert persisted_index == index


def test_json_repository_filters_by_thread_and_kind(tmp_path: Path) -> None:
    repo = JsonArtifactRepository(tmp_path)
    repo.save("match", "match-a", {"score": 82}, source_thread_id="thread-a", source_agent="match")
    repo.save("match", "match-b", {"score": 61}, source_thread_id="thread-b", source_agent="match")
    repo.save("plan", "plan-a", {"title": "三个月计划"}, source_thread_id="thread-a", source_agent="planning")

    assert [item["id"] for item in repo.list_by_thread("thread-a")] == ["match-a", "plan-a"]
    assert [item["id"] for item in repo.list_by_kind("thread-a", "match")] == ["match-a"]


def test_json_repository_blocks_path_traversal(tmp_path: Path) -> None:
    repo = JsonArtifactRepository(tmp_path)

    try:
        repo.save(kind="profile", artifact_id="../bad", payload={}, source_thread_id="thread-a", source_agent="profile")
    except ValueError as exc:
        assert "Invalid artifact_id" in str(exc)
    else:
        raise AssertionError("path traversal was accepted")


def test_json_repository_uses_unique_temp_files_for_atomic_writes(tmp_path: Path, monkeypatch) -> None:
    replace_sources: list[str] = []
    real_replace = os.replace

    def tracking_replace(src: str | os.PathLike[str], dst: str | os.PathLike[str]) -> None:
        replace_sources.append(str(src))
        real_replace(src, dst)

    monkeypatch.setattr(json_repository.os, "replace", tracking_replace)
    repo = JsonArtifactRepository(tmp_path)

    repo.save("profile", "profile-a", {"name": "林晨"}, source_thread_id="thread-a", source_agent="profile")
    repo.save("profile", "profile-b", {"name": "周然"}, source_thread_id="thread-a", source_agent="profile")

    assert len(replace_sources) == len(set(replace_sources))
