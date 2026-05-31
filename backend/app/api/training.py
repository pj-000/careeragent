from fastapi import APIRouter, HTTPException, status

from app.api.runs import RunRequest
from app.repositories.paths import RUNTIME_DATA_DIR
from app.schemas.runs import RunResponse


router = APIRouter(prefix="/api/training", tags=["training"])


@router.post("", response_model=RunResponse)
def create_training_run(request: RunRequest) -> RunResponse:
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Agent-specific runtime endpoints are disabled. Use POST /api/runs.",
    )
