from typing import Any

from app.agents.runtime import run_business_agent
from app.repositories.interfaces import ArtifactRepository


def planning_node(state: dict[str, Any], artifact_repo: ArtifactRepository) -> dict[str, Any]:
    return run_business_agent(
        state,
        artifact_repo,
        agent_id="planning",
        artifact_kind="plan",
        title="Career plan",
        payload={
            "milestones": ["profile cleanup", "targeted applications", "interview practice"],
            "horizon": "3 months",
        },
    )
