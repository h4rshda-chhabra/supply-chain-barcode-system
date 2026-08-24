from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.batch import Batch
from app.models.enums import MovementType
from app.models.inventory_movement import InventoryMovement
from app.schemas.movement import IssueRequestCreate, MovementOut
from app.services.movement_service import issue_material as issue_material_service

router = APIRouter(prefix="/movements", tags=["Request & Issue"])


@router.get("", response_model=list[MovementOut])
def list_movements(movement_type: MovementType | None = None, db: Session = Depends(get_db)):
    query = db.query(InventoryMovement)
    if movement_type:
        query = query.filter(InventoryMovement.movement_type == movement_type)
    return query.order_by(InventoryMovement.movement_date.desc()).limit(500).all()


@router.post("/issue", response_model=MovementOut, status_code=201)
def issue_material(payload: IssueRequestCreate, db: Session = Depends(get_db)):
    """Request & Issue flow: operator scans a batch's QR (trace_id), the
    system looks the batch up, and the issued quantity is recorded against
    it, decrementing what remains in the warehouse."""
    batch = db.scalar(
        select(Batch).options(joinedload(Batch.product)).where(Batch.trace_id == payload.trace_id)
    )
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found for scanned trace ID")

    movement = issue_material_service(
        db, batch, payload.quantity, payload.department, payload.requested_by, payload.notes
    )

    db.commit()
    db.refresh(movement)
    return movement
