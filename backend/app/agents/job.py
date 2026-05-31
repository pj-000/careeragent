from typing import Any

from app.agents.runtime import run_business_agent
from app.repositories.interfaces import ArtifactRepository


def job_node(state: dict[str, Any], artifact_repo: ArtifactRepository) -> dict[str, Any]:
    return run_business_agent(
        state,
        artifact_repo,
        agent_id="job",
        artifact_kind="job_analysis",
        title="Job analysis",
        payload={
            "summary": "Target role requirements were normalized for matching.",
            "requirements": ["responsibilities", "qualifications", "risk signals"],
        },
    )
