from typing import Any

from app.agents.runtime import run_business_agent
from app.repositories.interfaces import ArtifactRepository


def match_node(state: dict[str, Any], artifact_repo: ArtifactRepository) -> dict[str, Any]:
    return run_business_agent(
        state,
        artifact_repo,
        agent_id="match",
        artifact_kind="match",
        title="Match diagnosis",
        payload={
            "score": 72,
            "strengths": ["transferable backend experience", "clear learning velocity"],
            "gaps": ["add role-specific evidence", "prepare project stories"],
        },
    )
