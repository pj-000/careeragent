from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.runs import SAFE_THREAD_ID_PATTERN
from app.repositories.json_repository import JsonArtifactRepository
from app.repositories.paths import RUNTIME_DATA_DIR


router = APIRouter(prefix="/api/jobs", tags=["jobs"])


class SeedArtifactResponse(BaseModel):
    artifact_id: str


class CustomJobRequest(BaseModel):
    thread_id: Annotated[str, Field(pattern=SAFE_THREAD_ID_PATTERN)] = "custom"
    title: str
    company: str | None = None
    description: str


@router.post("/demo", response_model=SeedArtifactResponse)
def create_demo_job() -> SeedArtifactResponse:
    repo = JsonArtifactRepository(RUNTIME_DATA_DIR)
    artifact_id = f"job-{uuid4().hex[:12]}"
    repo.save(
        kind="job_analysis",
        artifact_id=artifact_id,
        payload={
            "title": "Backend Agent Engineer",
            "company": "CareerAgent Demo",
            "summary": "Seed job artifact for trying matching and planning flows.",
            "requirements": ["FastAPI", "workflow orchestration", "testing discipline"],
        },
        source_thread_id="demo",
        source_agent="seed",
    )
    return SeedArtifactResponse(artifact_id=artifact_id)


@router.post("/custom", response_model=SeedArtifactResponse)
def create_custom_job(request: CustomJobRequest) -> SeedArtifactResponse:
    repo = JsonArtifactRepository(RUNTIME_DATA_DIR)
    artifact_id = f"job-{uuid4().hex[:12]}"
    repo.save(
        kind="job_analysis",
        artifact_id=artifact_id,
        payload={
            "title": request.title,
            "company": request.company,
            "description": request.description,
        },
        source_thread_id=request.thread_id,
        source_agent="seed",
    )
    return SeedArtifactResponse(artifact_id=artifact_id)
