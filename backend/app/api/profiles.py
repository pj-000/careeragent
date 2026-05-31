from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel

from app.repositories.json_repository import JsonArtifactRepository
from app.repositories.paths import RUNTIME_DATA_DIR


router = APIRouter(prefix="/api/profiles", tags=["profiles"])


class SeedArtifactResponse(BaseModel):
    artifact_id: str


@router.post("/demo", response_model=SeedArtifactResponse)
def create_demo_profile() -> SeedArtifactResponse:
    repo = JsonArtifactRepository(RUNTIME_DATA_DIR)
    artifact_id = f"profile-{uuid4().hex[:12]}"
    repo.save(
        kind="profile",
        artifact_id=artifact_id,
        payload={
            "name": "Demo Candidate",
            "summary": "Backend-oriented candidate profile seeded for API demos.",
            "skills": ["Python", "FastAPI", "agent workflows"],
            "goals": ["Build production-ready career agent systems"],
        },
        source_thread_id="demo",
        source_agent="seed",
    )
    return SeedArtifactResponse(artifact_id=artifact_id)
