from datetime import date, datetime, time

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.batch import Batch
from app.models.customer import Customer
from app.models.dispatch import Dispatch
from app.models.enums import AuditAction, BatchStatus, DispatchStatus, MovementType
from app.models.inventory_movement import InventoryMovement
from app.services.audit_service import log_action
from app.services.id_generator import generate_dispatch_number


def create_dispatch(
    db: Session,
    customer: Customer,
    batch: Batch,
    quantity: float,
    dispatch_date: date,
) -> Dispatch:
    """Ship `quantity` of a finished-goods batch (scanned via QR) to a
    customer, deducting from what remains of that batch."""
    if quantity > float(batch.remaining_quantity):
        raise HTTPException(
            status_code=400,
            detail=f"Requested {quantity} exceeds remaining {batch.remaining_quantity}",
        )

    dispatch = Dispatch(
        dispatch_number=generate_dispatch_number(db),
        customer_id=customer.id,
        batch_id=batch.id,
        quantity=quantity,
        dispatch_date=dispatch_date,
        status=DispatchStatus.DISPATCHED,
    )
    db.add(dispatch)

    batch.remaining_quantity = float(batch.remaining_quantity) - quantity
    if batch.remaining_quantity <= 0:
        batch.status = BatchStatus.DISPATCHED

    db.add(
        InventoryMovement(
            movement_type=MovementType.DISPATCH,
            batch_id=batch.id,
            quantity=quantity,
            reference_type="Dispatch",
            movement_date=datetime.combine(dispatch_date, time(12, 0)),
        )
    )

    log_action(
        db,
        AuditAction.DISPATCH_COMPLETED,
        "Dispatch",
        None,
        f"{quantity} {batch.uom} of batch {batch.batch_number} dispatched to {customer.name}",
    )
    db.flush()
    return dispatch
