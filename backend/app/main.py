from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.interviews import router as interviews_router
from app.api.jobs import router as jobs_router
from app.api.profiles import router as profiles_router
from app.api.reports import router as reports_router
from app.api.runs import router as runs_router
from app.api.threads import router as threads_router
from app.api.training import router as training_router


app = FastAPI(title="CareerAgent MVP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(runs_router)
app.include_router(profiles_router)
app.include_router(jobs_router)
app.include_router(training_router)
app.include_router(interviews_router)
app.include_router(reports_router)
app.include_router(threads_router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
