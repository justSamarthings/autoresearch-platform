from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api import checkpoints, experiments, health
from backend.app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="AutoResearch Experiment Platform API",
    version="0.1.0",
    description="Ingest and query AutoResearch experiment artifacts.",
)

# Permit browser / notebook clients calling a tunneled API URL.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(experiments.router, prefix=settings.api_prefix)
app.include_router(checkpoints.router, prefix=settings.api_prefix)
