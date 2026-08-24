from datetime import date, datetime

from sqlalchemy.orm import Session

from app.models.enums import (
    AuditAction,
    BatchSourceType,
    BatchType,
    MovementType,
    PackagingType,
)
from app.models.grn import GRN
from app.models.inventory_movement import InventoryMovement
from app.models.product import Product
from app.models.supplier import Supplier
from app.services.audit_service import log_action
from app.services.batch_service import create_batch_with_qr
from app.services.id_generator import generate_grn_number


def create_grn(
    db: Session,
    supplier: Supplier,
    product: Product,
    quantity: float,
    batch_number: str,
    warehouse_location: str,
    uom: str = "EA",
    lot_number: str | None = None,
    manufacturing_date: date | None = None,
    expiry_date: date | None = None,
    packaging_type: PackagingType | None = None,
    received_date: datetime | None = None,
) -> GRN:
    """Goods receipt: creates the traceable raw-material Batch (+ QR),
    the GRN record, and the RECEIPT movement that opens its timeline."""
    received_date = received_date or datetime.utcnow()

    batch = create_batch_with_qr(
        db,
        product_id=product.id,
        batch_number=batch_number,
        batch_type=BatchType.RAW_MATERIAL,
        source_type=BatchSourceType.GRN,
        quantity=quantity,
        uom=uom,
        lot_number=lot_number,
        manufacturing_date=manufacturing_date,
        expiry_date=expiry_date,
        warehouse_location=warehouse_location,
        packaging_type=packaging_type,
    )

    grn = GRN(
        grn_number=generate_grn_number(db),
        supplier_id=supplier.id,
        product_id=product.id,
        batch_id=batch.id,
        quantity=quantity,
        batch_number=batch_number,
        lot_number=lot_number,
        manufacturing_date=manufacturing_date,
        expiry_date=expiry_date,
        warehouse_location=warehouse_location,
        received_date=received_date,
    )
    db.add(grn)
    db.flush()

    db.add(
        InventoryMovement(
            movement_type=MovementType.RECEIPT,
            batch_id=batch.id,
            quantity=quantity,
            reference_type="GRN",
            reference_id=grn.id,
            movement_date=received_date,
        )
    )

    log_action(
        db,
        AuditAction.GRN_CREATED,
        "GRN",
        grn.id,
        f"GRN {grn.grn_number} created for {quantity} {uom} of {product.name}",
    )
    db.flush()
    return grn
