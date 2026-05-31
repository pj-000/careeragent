from fastapi import APIRouter

from app.api.runs import RunRequest
from app.graphs.workflow import run_career_graph
from app.repositories.json_repository import JsonArtifactRepository
from app.repositories.paths import RUNTIME_DATA_DIR
from app.schemas.runs import RunResponse


router = APIRouter(prefix="/api/training", tags=["training"])


@router.post("", response_model=RunResponse)
def create_training_run(request: RunRequest) -> RunResponse:
    repo = JsonArtifactRepository(RUNTIME_DATA_DIR)
    return run_career_graph(request.thread_id, request.message, repo)
