from app.graphs.state import CareerAgentState
from app.schemas.memory import CompactionSnapshot


def compact_state(state: CareerAgentState) -> CompactionSnapshot:
    return CompactionSnapshot(
        id=f"compact-{state.thread_id}",
        thread_id=state.thread_id,
        message_summary=_latest_public_message(state),
        pending_items=[state.pending_question] if state.pending_question else [],
        agent_summaries={
            agent_id: snapshot.summary
            for agent_id, snapshot in state.agent_snapshots.items()
            if snapshot.summary
        },
        skill_refs=list(state.loaded_skill_refs),
        artifact_ids=list(state.artifact_ids),
    )


def _latest_public_message(state: CareerAgentState) -> str:
    for message in reversed(state.messages):
        if message.get("role") == "assistant" and message.get("content"):
            return message["content"]
    return state.user_message
