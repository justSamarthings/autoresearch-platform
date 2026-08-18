from fastapi import FastAPI

from backend.app.api import checkpoints, experiments, health
from backend.app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="AutoResearch Experiment Platform API",
    version="0.1.0",
    description="Ingest and query AutoResearch experiment artifacts.",
)

app.include_router(health.router)
app.include_router(experiments.router, prefix=settings.api_prefix)
app.include_router(checkpoints.router, prefix=settings.api_prefix)
