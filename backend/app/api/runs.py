from typing import Annotated

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.graphs.workflow import run_career_graph
from app.repositories.json_repository import JsonArtifactRepository
from app.repositories.paths import RUNTIME_DATA_DIR
from app.schemas.runs import RunResponse


SAFE_THREAD_ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$"

router = APIRouter(prefix="/api/runs", tags=["runs"])


class RunRequest(BaseModel):
    thread_id: Annotated[str, Field(pattern=SAFE_THREAD_ID_PATTERN)]
    message: str


@router.post("", response_model=RunResponse)
def create_run(request: RunRequest) -> RunResponse:
    repo = JsonArtifactRepository(RUNTIME_DATA_DIR)
    return run_career_graph(request.thread_id, request.message, repo)
