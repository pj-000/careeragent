from __future__ import annotations

from langgraph.checkpoint.memory import InMemorySaver


def create_checkpointer() -> InMemorySaver:
    return InMemorySaver()
