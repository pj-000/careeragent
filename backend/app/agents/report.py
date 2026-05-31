from typing import Any

from app.agents.manifests import AGENT_MANIFESTS
from app.agents.runtime import coerce_state, make_runtime, next_artifact_id
from app.artifacts.markdown import MissingArtifactError, build_markdown_report, required_parent_artifact_ids
from app.graphs.state import AgentSnapshot
from app.repositories.interfaces import ArtifactRepository


def report_node(state: dict[str, Any], artifact_repo: ArtifactRepository) -> dict[str, Any]:
    career_state = coerce_state(state)
    runtime = make_runtime(career_state, "report", artifact_repo)
    skill_refs = AGENT_MANIFESTS["report"].skill_policy.default_skill_ids
    artifacts = [runtime.get_artifact(artifact["id"]) for artifact in runtime.list_artifacts()]
    try:
        content = build_markdown_report(career_state.thread_id, artifacts)
        parent_artifact_ids = required_parent_artifact_ids(career_state.thread_id, artifacts)
    except MissingArtifactError as exc:
        career_state.loaded_skill_refs = _append_unique(career_state.loaded_skill_refs, skill_refs)
        career_state.agent_snapshots["report"] = AgentSnapshot(
            agent_id="report",
            summary=f"Report blocked: {exc}",
            private_context={"mode": "deterministic_mvp"},
            last_artifact_ids=[],
            used_skill_refs=list(skill_refs),
        )
        career_state.messages.append({"role": "assistant", "content": f"Career report blocked: {exc}."})
        career_state.warnings = _append_unique(career_state.warnings, [f"Missing required artifact chain: {exc}"])
        career_state.active_agent = "report"
        career_state.next_agent = runtime.handoff_to("memory_manager")
        return career_state.model_dump()

    artifact_id = runtime.save_artifact(
        kind="report",
        artifact_id=next_artifact_id(artifact_repo, career_state.thread_id, "report"),
        payload={
            "title": "Career report",
            "format": "markdown",
            "content": content,
            "skill_refs": skill_refs,
        },
        parent_artifact_ids=parent_artifact_ids,
    )
    career_state.artifact_ids.append(artifact_id)
    career_state.loaded_skill_refs = _append_unique(career_state.loaded_skill_refs, skill_refs)
    career_state.agent_snapshots["report"] = AgentSnapshot(
        agent_id="report",
        summary=f"report saved report artifact {artifact_id}.",
        private_context={"mode": "deterministic_mvp"},
        last_artifact_ids=[artifact_id],
        used_skill_refs=list(skill_refs),
    )
    career_state.messages.append({"role": "assistant", "content": f"Career report: saved {artifact_id}."})
    career_state.active_agent = "report"
    career_state.next_agent = runtime.handoff_to("memory_manager")
    return career_state.model_dump()


def _append_unique(existing: list[str], additions: list[str]) -> list[str]:
    values = list(existing)
    for item in additions:
        if item not in values:
            values.append(item)
    return values
