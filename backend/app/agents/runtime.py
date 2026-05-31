from __future__ import annotations

import re
from typing import Any
from uuid import uuid4

from app.agents.manifests import AGENT_MANIFESTS
from app.graphs.state import AgentSnapshot, CareerAgentState
from app.repositories.interfaces import ArtifactRepository
from app.schemas.agents import AgentManifest


class PermissionDenied(PermissionError):
    pass


class AgentRuntimeContext:
    def __init__(
        self,
        thread_id: str,
        agent_id: str,
        artifact_repo: ArtifactRepository,
        manifest: AgentManifest,
    ) -> None:
        self.thread_id = thread_id
        self.agent_id = agent_id
        self.artifact_repo = artifact_repo
        self.manifest = manifest

    def save_artifact(
        self,
        kind: str,
        artifact_id: str,
        payload: dict,
        parent_artifact_ids: list[str] | None = None,
    ) -> str:
        self._require_tool("artifact_write")
        self._require_writable_artifact_kind(kind)
        self.artifact_repo.save(
            kind=kind,
            artifact_id=artifact_id,
            payload=payload,
            source_thread_id=self.thread_id,
            source_agent=self.agent_id,
            parent_artifact_ids=parent_artifact_ids or [],
        )
        return artifact_id

    def list_artifacts(self, kind: str | None = None) -> list[dict[str, str]]:
        self._require_tool("artifact_read")
        if kind is None:
            artifacts = self.artifact_repo.list_by_thread(self.thread_id)
            return [
                artifact
                for artifact in artifacts
                if artifact.get("kind") in set(self.manifest.readable_artifact_kinds)
            ]
        self._require_readable_artifact_kind(kind)
        return self.artifact_repo.list_by_kind(self.thread_id, kind)

    def get_artifact(self, artifact_id: str) -> dict[str, Any]:
        self._require_tool("artifact_read")
        artifact = self.artifact_repo.get(artifact_id)
        if artifact.get("source_thread_id") != self.thread_id:
            raise PermissionDenied(f"{self.agent_id} cannot read artifact outside thread {self.thread_id!r}")
        self._require_readable_artifact_kind(str(artifact.get("kind", "")))
        return artifact

    def read_memory(self, scope: str) -> list[dict[str, Any]]:
        self._require_tool("memory_read")
        if scope not in self.manifest.readable_memory_scopes:
            raise PermissionDenied(f"{self.agent_id} cannot read memory scope {scope!r}")
        return []

    def write_memory_candidate(self, candidate: dict[str, Any]) -> dict[str, Any]:
        self._require_tool("memory_write")
        scope = candidate.get("scope")
        if scope not in self.manifest.writable_memory_scopes:
            raise PermissionDenied(f"{self.agent_id} cannot write memory scope {scope!r}")
        return candidate

    def handoff_to(self, target_agent_id: str) -> str:
        if target_agent_id not in self.manifest.handoff_policy.allowed_targets:
            raise PermissionDenied(f"{self.agent_id} cannot handoff to {target_agent_id}")
        return target_agent_id

    def _require_tool(self, tool_name: str) -> None:
        if tool_name not in self.manifest.allowed_tools:
            raise PermissionDenied(f"{self.agent_id} is not allowed to use tool {tool_name}")

    def _require_readable_artifact_kind(self, kind: str) -> None:
        if kind not in self.manifest.readable_artifact_kinds:
            raise PermissionDenied(f"{self.agent_id} cannot read artifact kind {kind!r}")

    def _require_writable_artifact_kind(self, kind: str) -> None:
        if kind not in self.manifest.writable_artifact_kinds:
            raise PermissionDenied(f"{self.agent_id} cannot write artifact kind {kind!r}")


def coerce_state(raw_state: dict[str, Any]) -> CareerAgentState:
    state = CareerAgentState.model_validate(dict(raw_state))
    latest_user_message = {"role": "user", "content": state.user_message}
    if state.metadata.get("last_user_message") != state.user_message:
        if not state.messages or state.messages[-1] != latest_user_message:
            state.messages.append(latest_user_message)
        state.metadata["last_user_message"] = state.user_message
    return state


def make_runtime(
    state: CareerAgentState,
    agent_id: str,
    artifact_repo: ArtifactRepository,
) -> AgentRuntimeContext:
    return AgentRuntimeContext(
        thread_id=state.thread_id,
        agent_id=agent_id,
        artifact_repo=artifact_repo,
        manifest=AGENT_MANIFESTS[agent_id],
    )


def run_business_agent(
    raw_state: dict[str, Any],
    artifact_repo: ArtifactRepository,
    agent_id: str,
    artifact_kind: str,
    title: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    state = coerce_state(raw_state)
    runtime = make_runtime(state, agent_id, artifact_repo)
    skill_refs = AGENT_MANIFESTS[agent_id].skill_policy.default_skill_ids
    for scope in AGENT_MANIFESTS[agent_id].readable_memory_scopes:
        if "memory_read" in AGENT_MANIFESTS[agent_id].allowed_tools:
            runtime.read_memory(scope)
            break

    artifact_id = _next_artifact_id(artifact_repo, state.thread_id, agent_id)
    artifact_id = runtime.save_artifact(
        kind=artifact_kind,
        artifact_id=artifact_id,
        payload={
            "title": title,
            "user_message": state.user_message,
            "content": payload,
            "skill_refs": skill_refs,
        },
        parent_artifact_ids=list(state.artifact_ids),
    )
    state.artifact_ids.append(artifact_id)
    state.loaded_skill_refs = _append_unique(state.loaded_skill_refs, skill_refs)
    state.agent_snapshots[agent_id] = AgentSnapshot(
        agent_id=agent_id,
        summary=f"{agent_id} saved {artifact_kind} artifact {artifact_id}.",
        private_context={"mode": "deterministic_mvp"},
        last_artifact_ids=[artifact_id],
        used_skill_refs=list(skill_refs),
    )
    state.messages.append({"role": "assistant", "content": f"{title}: saved {artifact_id}."})
    state.active_agent = agent_id
    state.next_agent = runtime.handoff_to("memory_manager")
    state.warnings = _append_unique(
        state.warnings,
        [f"{agent_id} generated deterministic MVP content; validate before use."],
    )
    return state.model_dump()


def _append_unique(existing: list[str], additions: list[str]) -> list[str]:
    values = list(existing)
    for item in additions:
        if item not in values:
            values.append(item)
    return values


def next_artifact_id(artifact_repo: ArtifactRepository, thread_id: str, agent_id: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", thread_id).strip("-") or "thread"
    slug = slug[:48].strip("-") or "thread"
    sequence = len(artifact_repo.list_by_thread(thread_id)) + 1
    return f"{agent_id}-{slug}-{sequence}-{uuid4().hex[:10]}"


def _next_artifact_id(artifact_repo: ArtifactRepository, thread_id: str, agent_id: str) -> str:
    return next_artifact_id(artifact_repo, thread_id, agent_id)
