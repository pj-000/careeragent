from __future__ import annotations

from typing import Any

from app.agents.manifests import AGENT_MANIFESTS
from app.agents.runtime import coerce_state, make_runtime, next_artifact_id
from app.graphs.state import AgentSnapshot
from app.memory.compaction import compact_state
from app.repositories.interfaces import ArtifactRepository


def memory_manager_node(state: dict[str, Any], artifact_repo: ArtifactRepository) -> dict[str, Any]:
    career_state = coerce_state(state)
    runtime = make_runtime(career_state, "memory_manager", artifact_repo)
    for scope in AGENT_MANIFESTS["memory_manager"].readable_memory_scopes:
        runtime.read_memory(scope)

    career_state.loaded_skill_refs = _append_unique(
        career_state.loaded_skill_refs,
        AGENT_MANIFESTS["memory_manager"].skill_policy.default_skill_ids,
    )
    snapshot = compact_state(career_state)
    artifact_id = next_artifact_id(artifact_repo, career_state.thread_id, "compaction")
    runtime.save_artifact(
        kind="compaction_snapshot",
        artifact_id=artifact_id,
        payload=snapshot.model_dump(),
        parent_artifact_ids=list(career_state.artifact_ids),
    )
    career_state.artifact_ids.append(artifact_id)
    career_state.compaction_snapshot_id = artifact_id
    career_state.agent_snapshots["memory_manager"] = AgentSnapshot(
        agent_id="memory_manager",
        summary=f"Compacted state into {artifact_id}.",
        private_context={},
        last_artifact_ids=[artifact_id],
        used_skill_refs=list(AGENT_MANIFESTS["memory_manager"].skill_policy.default_skill_ids),
    )
    career_state.messages.append(
        {"role": "assistant", "content": f"Memory compaction snapshot saved as {artifact_id}."}
    )
    career_state.active_agent = "memory_manager"
    career_state.next_agent = None
    return career_state.model_dump()


def _append_unique(existing: list[str], additions: list[str]) -> list[str]:
    values = list(existing)
    for item in additions:
        if item not in values:
            values.append(item)
    return values
