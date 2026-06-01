from typing import Any

from app.agents.runtime import run_business_agent
from app.repositories.interfaces import ArtifactRepository


def profile_node(state: dict[str, Any], artifact_repo: ArtifactRepository) -> dict[str, Any]:
    return run_business_agent(
        state,
        artifact_repo,
        agent_id="profile",
        artifact_kind="profile",
        title="Profile summary",
        payload={
            "summary": "Structured profile extracted from the current resume or career message.",
            "signals": ["experience", "skills", "career goals"],
        },
    )
