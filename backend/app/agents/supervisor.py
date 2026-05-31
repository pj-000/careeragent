from __future__ import annotations

from typing import Any

from app.agents.manifests import AGENT_MANIFESTS
from app.agents.runtime import coerce_state, make_runtime
from app.graphs.state import AgentSnapshot
from app.repositories.interfaces import ArtifactRepository


def supervisor_node(state: dict[str, Any], artifact_repo: ArtifactRepository) -> dict[str, Any]:
    career_state = coerce_state(state)
    runtime = make_runtime(career_state, "supervisor", artifact_repo)
    target = route_user_message(career_state.user_message)
    career_state.loaded_skill_refs = _append_unique(
        career_state.loaded_skill_refs,
        AGENT_MANIFESTS["supervisor"].skill_policy.default_skill_ids,
    )
    career_state.agent_snapshots["supervisor"] = AgentSnapshot(
        agent_id="supervisor",
        summary=f"Routed current message to {target}.",
        private_context={"route": target},
        last_artifact_ids=[],
        used_skill_refs=list(AGENT_MANIFESTS["supervisor"].skill_policy.default_skill_ids),
    )
    career_state.active_agent = "supervisor"
    career_state.next_agent = runtime.handoff_to(target)
    return career_state.model_dump()


def route_user_message(message: str) -> str:
    normalized = message.lower()
    if "继续" in message or "记忆" in message or "压缩" in message:
        return "memory_manager"
    if message.startswith("回答") or "回答1" in message or "回答2" in message or "回答3" in message:
        return "interview"
    if "训练" in message or "training task" in normalized:
        return "training"
    if "我会" in message or "我有" in message or "resume" in normalized or "profile" in normalized:
        return "profile"
    if "岗位" in message or "jd" in normalized or "job" in normalized:
        return "job"
    if "匹配" in message or "match" in normalized:
        return "match"
    if "计划" in message or "路径" in message or "plan" in normalized:
        return "planning"
    if "面试" in message or "interview" in normalized:
        return "interview"
    if "报告" in message or "report" in normalized:
        return "report"
    return "match"


def _append_unique(existing: list[str], additions: list[str]) -> list[str]:
    values = list(existing)
    for item in additions:
        if item not in values:
            values.append(item)
    return values
