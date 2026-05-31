from app.graphs.state import CareerAgentState
from app.schemas.memory import CompactionSnapshot


def compact_state(state: CareerAgentState) -> CompactionSnapshot:
    run_id = state.metadata.get("run_id")
    if not run_id:
        raise ValueError("CompactionSnapshot requires metadata.run_id")
    return CompactionSnapshot(
        id=f"compact-{state.thread_id}",
        thread_id=state.thread_id,
        source_run_id=str(run_id),
        current_goal=str(state.metadata.get("active_goal") or "职业发展规划"),
        confirmed_facts=_string_list(state.metadata.get("confirmed_facts")),
        decisions_made=_string_list(state.metadata.get("decisions_made")),
        active_artifact_refs=list(state.artifact_ids),
        next_actions=_string_list(state.metadata.get("next_actions")),
        dropped_context_summary=_latest_public_message(state),
    )


def _latest_public_message(state: CareerAgentState) -> str:
    for message in reversed(state.messages):
        if message.get("role") == "assistant" and message.get("content"):
            return message["content"]
    return state.user_message


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]
