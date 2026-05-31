from typing import Annotated

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.repositories.paths import RUNTIME_DATA_DIR
from app.schemas.runs import RunResponse
from app.services.run_orchestrator import RunOrchestrator


SAFE_THREAD_ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$"

router = APIRouter(prefix="/api/runs", tags=["runs"])


class RunRequest(BaseModel):
    thread_id: Annotated[str, Field(pattern=SAFE_THREAD_ID_PATTERN)]
    message: str


@router.post("", response_model=RunResponse)
def create_run(request: RunRequest) -> RunResponse:
    return RunOrchestrator(RUNTIME_DATA_DIR).run(request.thread_id, request.message)
