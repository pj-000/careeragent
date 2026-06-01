from typing import Protocol


class AgentRuntime(Protocol):
    def save_artifact(
        self,
        kind: str,
        artifact_id: str,
        payload: dict,
        parent_artifact_ids: list[str] | None = None,
    ) -> str:
        ...
