from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.services import experiments as experiment_service

router = APIRouter(prefix="/checkpoints", tags=["checkpoints"])


class CheckpointListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    checkpoint_path: str
    metadata: dict | None = Field(
        default=None,
        validation_alias="metadata_json",
        serialization_alias="metadata",
    )
    created_at: object
    experiment_uuid: UUID


class CheckpointListResponse(BaseModel):
    items: list[CheckpointListItem]
    total: int
    limit: int
    offset: int


@router.get("", response_model=CheckpointListResponse)
def list_checkpoints(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> CheckpointListResponse:
    items, total = experiment_service.list_checkpoints(db, limit=limit, offset=offset)
    return CheckpointListResponse(
        items=[CheckpointListItem.model_validate(i) for i in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{checkpoint_id}", response_model=CheckpointListItem)
def get_checkpoint(checkpoint_id: UUID, db: Session = Depends(get_db)) -> CheckpointListItem:
    checkpoint = experiment_service.get_checkpoint(db, checkpoint_id)
    if checkpoint is None:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    return CheckpointListItem.model_validate(checkpoint)
