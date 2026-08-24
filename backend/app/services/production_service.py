from datetime import date, datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.batch import Batch
from app.models.enums import (
    AuditAction,
    BatchSourceType,
    BatchType,
    MovementType,
    PackagingType,
    ProductionOrderStatus,
)
from app.models.finished_goods import FinishedGoods
from app.models.inventory_movement import InventoryMovement
from app.models.production_consumption import ProductionConsumption
from app.models.production_order import ProductionOrder
from app.services.audit_service import log_action
from app.services.batch_service import create_batch_with_qr
from app.services.id_generator import generate_fg_batch_number


def consume_raw_batch(
    db: Session,
    po: ProductionOrder,
    batch: Batch,
    quantity_consumed: float,
    consumed_by: str | None = None,
    event_time: datetime | None = None,
) -> ProductionConsumption:
    """Operator scans a raw-material QR during production: deduct the
    consumed quantity from the batch and link it to the production order."""
    if quantity_consumed > float(batch.remaining_quantity):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Requested {quantity_consumed} exceeds remaining "
                f"{batch.remaining_quantity} in batch {batch.batch_number}"
            ),
        )

    event_time = event_time or datetime.utcnow()

    consumption = ProductionConsumption(
        production_order_id=po.id,
        raw_batch_id=batch.id,
        quantity_consumed=quantity_consumed,
        consumed_by=consumed_by,
        consumed_at=event_time,
    )
    db.add(consumption)

    batch.remaining_quantity = float(batch.remaining_quantity) - quantity_consumed

    db.add(
        InventoryMovement(
            movement_type=MovementType.PRODUCTION_CONSUMPTION,
            batch_id=batch.id,
            quantity=quantity_consumed,
            reference_type="ProductionOrder",
            reference_id=po.id,
            movement_date=event_time,
        )
    )

    if po.status == ProductionOrderStatus.PLANNED:
        po.status = ProductionOrderStatus.IN_PROGRESS

    log_action(
        db,
        AuditAction.PRODUCTION_CONSUMED,
        "Batch",
        batch.id,
        f"{quantity_consumed} {batch.uom} of batch {batch.batch_number} consumed by "
        f"production order {po.production_order_no}",
    )
    db.flush()
    return consumption


def create_finished_goods(
    db: Session,
    po: ProductionOrder,
    quantity: float,
    production_date: date,
    warehouse_location: str | None = None,
    packaging_type: PackagingType | None = None,
    event_time: datetime | None = None,
) -> FinishedGoods:
    """Creates a new traceable finished-goods batch (with its own QR) from a
    production order and rolls the produced quantity up onto the order."""
    fg_batch_number = generate_fg_batch_number(db)
    batch = create_batch_with_qr(
        db,
        product_id=po.product_id,
        batch_number=fg_batch_number,
        batch_type=BatchType.FINISHED_GOOD,
        source_type=BatchSourceType.PRODUCTION,
        quantity=quantity,
        uom=po.product.uom,
        manufacturing_date=production_date,
        warehouse_location=warehouse_location,
        packaging_type=packaging_type,
    )

    event_time = event_time or datetime.utcnow()

    fg = FinishedGoods(
        fg_batch_number=fg_batch_number,
        batch_id=batch.id,
        production_order_id=po.id,
        product_id=po.product_id,
        quantity=quantity,
        production_date=production_date,
        created_at=event_time,
    )
    db.add(fg)

    db.add(
        InventoryMovement(
            movement_type=MovementType.FINISHED_GOODS_CREATION,
            batch_id=batch.id,
            quantity=quantity,
            reference_type="ProductionOrder",
            reference_id=po.id,
            movement_date=event_time,
        )
    )

    po.produced_quantity = float(po.produced_quantity) + quantity
    po.status = (
        ProductionOrderStatus.COMPLETED
        if po.produced_quantity >= float(po.planned_quantity)
        else ProductionOrderStatus.IN_PROGRESS
    )

    log_action(
        db,
        AuditAction.FG_CREATED,
        "FinishedGoods",
        None,
        f"FG batch {fg_batch_number} ({batch.trace_id}) created: {quantity} "
        f"{po.product.uom} from {po.production_order_no}",
    )
    db.flush()
    return fg
