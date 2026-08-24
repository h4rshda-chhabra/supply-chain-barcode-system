from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.batch import Batch
from app.models.enums import AuditAction, BatchStatus, MovementType
from app.models.inventory_movement import InventoryMovement
from app.services.audit_service import log_action
from app.services.id_generator import generate_request_number


def issue_material(
    db: Session,
    batch: Batch,
    quantity: float,
    department: str,
    requested_by: str,
    notes: str | None = None,
    movement_date: datetime | None = None,
) -> InventoryMovement:
    """Request & Issue: deduct `quantity` from `batch` and record the
    movement. Raises HTTPException(400) if the batch doesn't have enough
    remaining quantity."""
    if quantity > float(batch.remaining_quantity):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Requested quantity {quantity} exceeds remaining "
                f"{batch.remaining_quantity} in batch {batch.batch_number}"
            ),
        )

    movement = InventoryMovement(
        movement_type=MovementType.ISSUE,
        batch_id=batch.id,
        quantity=quantity,
        request_number=generate_request_number(db),
        department=department,
        requested_by=requested_by,
        notes=notes,
        movement_date=movement_date or datetime.utcnow(),
    )
    db.add(movement)

    batch.remaining_quantity = float(batch.remaining_quantity) - quantity
    if batch.remaining_quantity <= 0:
        batch.status = BatchStatus.ISSUED_OUT

    log_action(
        db,
        AuditAction.BATCH_ISSUED,
        "Batch",
        batch.id,
        f"{quantity} {batch.uom} issued from batch {batch.batch_number} to "
        f"{department} (req by {requested_by})",
    )
    db.flush()
    return movement
