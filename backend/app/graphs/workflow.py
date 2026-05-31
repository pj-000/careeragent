from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import Any, TypedDict
from uuid import uuid4

from langgraph.graph import END, START, StateGraph

from app.agents.interview import interview_node
from app.agents.job import job_node
from app.agents.match import match_node
from app.agents.memory import memory_manager_node
from app.agents.planning import planning_node
from app.agents.profile import profile_node
from app.agents.report import report_node
from app.agents.supervisor import supervisor_node
from app.agents.training import training_node
from app.graphs.checkpoints import create_checkpointer
from app.repositories.interfaces import ArtifactRepository
from app.schemas.runs import AgentTraceItem, RunResponse


class GraphState(TypedDict, total=False):
    thread_id: str
    user_message: str
    active_agent: str
    messages: list[dict[str, str]]
    loaded_skill_refs: list[str]
    related_long_term_memory_refs: list[str]
    artifact_ids: list[str]
    agent_snapshots: dict[str, dict[str, Any]]
    pending_question: str | None
    compaction_snapshot_id: str | None
    next_agent: str | None
    warnings: list[str]
    metadata: dict[str, Any]


_GRAPH_CACHE: dict[tuple[str, str], Any] = {}


def build_graph(artifact_repo: ArtifactRepository):
    checkpointer = create_checkpointer()
    graph = StateGraph(GraphState)
    graph.add_node("supervisor", partial(supervisor_node, artifact_repo=artifact_repo))
    graph.add_node("profile", partial(profile_node, artifact_repo=artifact_repo))
    graph.add_node("job", partial(job_node, artifact_repo=artifact_repo))
    graph.add_node("match", partial(match_node, artifact_repo=artifact_repo))
    graph.add_node("planning", partial(planning_node, artifact_repo=artifact_repo))
    graph.add_node("training", partial(training_node, artifact_repo=artifact_repo))
    graph.add_node("interview", partial(interview_node, artifact_repo=artifact_repo))
    graph.add_node("report", partial(report_node, artifact_repo=artifact_repo))
    graph.add_node("memory_manager", partial(memory_manager_node, artifact_repo=artifact_repo))

    graph.add_edge(START, "supervisor")
    graph.add_conditional_edges(
        "supervisor",
        _route_from_supervisor,
        {
            "profile": "profile",
            "job": "job",
            "match": "match",
            "planning": "planning",
            "training": "training",
            "interview": "interview",
            "report": "report",
            "memory_manager": "memory_manager",
        },
    )
    for agent_id in ["profile", "job", "match", "planning", "training", "interview", "report"]:
        graph.add_edge(agent_id, "memory_manager")
    graph.add_edge("memory_manager", END)
    return graph.compile(checkpointer=checkpointer)


def run_career_graph(thread_id: str, message: str, artifact_repo: ArtifactRepository) -> RunResponse:
    graph = get_runtime_graph(artifact_repo)
    config = {"configurable": {"thread_id": thread_id}}
    state = graph.invoke({"thread_id": thread_id, "user_message": message}, config=config)
    artifacts = artifact_repo.list_by_thread(thread_id)
    snapshots = state.get("agent_snapshots", {})
    trace = [
        AgentTraceItem(
            agent_id=agent_id,
            summary=snapshot.get("summary", ""),
            artifact_ids=snapshot.get("last_artifact_ids", []),
            used_skill_refs=snapshot.get("used_skill_refs", []),
        )
        for agent_id, snapshot in snapshots.items()
    ]
    return RunResponse(
        run_id=f"run-{uuid4().hex[:12]}",
        thread_id=thread_id,
        active_agent=state.get("active_agent", "supervisor"),
        agent_trace_summary=trace,
        used_skill_refs=state.get("loaded_skill_refs", []),
        artifacts=artifacts,
        next_actions=_next_actions(state),
        warnings=state.get("warnings", []),
    )


def get_runtime_graph(artifact_repo: ArtifactRepository):
    return _cached_graph(artifact_repo)


def _cached_graph(artifact_repo: ArtifactRepository):
    key = _graph_cache_key(artifact_repo)
    if key not in _GRAPH_CACHE:
        _GRAPH_CACHE[key] = build_graph(artifact_repo=artifact_repo)
    return _GRAPH_CACHE[key]


def _graph_cache_key(artifact_repo: ArtifactRepository) -> tuple[str, str]:
    root = getattr(artifact_repo, "root", None)
    if root is not None:
        return ("root", str(Path(root).resolve()))
    return ("object", str(id(artifact_repo)))


def _route_from_supervisor(state: GraphState) -> str:
    return state.get("next_agent") or "match"


def _next_actions(state: dict[str, Any]) -> list[str]:
    if state.get("active_agent") == "memory_manager":
        return ["Review saved artifacts", "Send a follow-up message to continue the workflow"]
    return ["Continue the career workflow"]
