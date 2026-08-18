from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.schemas.experiment import (
    ExperimentDetail,
    ExperimentIngestRequest,
    ExperimentIngestResponse,
    ExperimentListResponse,
    ExperimentSummary,
    MetricOut,
)
from backend.app.services import experiments as experiment_service

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.post("", response_model=ExperimentIngestResponse, status_code=status.HTTP_200_OK)
def create_experiment(
    payload: ExperimentIngestRequest,
    db: Session = Depends(get_db),
) -> ExperimentIngestResponse:
    experiment, created = experiment_service.ingest_experiment(db, payload)
    return ExperimentIngestResponse(
        created=created,
        experiment=ExperimentDetail.model_validate(experiment),
    )


@router.get("", response_model=ExperimentListResponse)
def list_experiments(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status_filter: str | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
) -> ExperimentListResponse:
    items, total = experiment_service.list_experiments(
        db, limit=limit, offset=offset, status=status_filter
    )
    return ExperimentListResponse(
        items=[ExperimentSummary.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{experiment_id}", response_model=ExperimentDetail)
def get_experiment(experiment_id: str, db: Session = Depends(get_db)) -> ExperimentDetail:
    experiment = experiment_service.get_experiment_by_key(db, experiment_id)
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return ExperimentDetail.model_validate(experiment)


@router.get("/{experiment_id}/metrics", response_model=list[MetricOut])
def get_experiment_metrics(experiment_id: str, db: Session = Depends(get_db)) -> list[MetricOut]:
    experiment = experiment_service.get_experiment_by_key(db, experiment_id)
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return [MetricOut.model_validate(m) for m in experiment.metrics]
