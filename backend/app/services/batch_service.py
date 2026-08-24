from datetime import date

from sqlalchemy.orm import Session

from app.models.batch import Batch
from app.models.enums import (
    AuditAction,
    BatchSourceType,
    BatchStatus,
    BatchType,
    PackagingType,
)
from app.models.qr_code import QRCode
from app.services.audit_service import log_action
from app.services.id_generator import generate_trace_id
from app.services.qr_service import build_qr_assets


def create_batch_with_qr(
    db: Session,
    *,
    product_id: int,
    batch_number: str,
    batch_type: BatchType,
    source_type: BatchSourceType,
    quantity: float,
    uom: str = "EA",
    lot_number: str | None = None,
    manufacturing_date: date | None = None,
    expiry_date: date | None = None,
    warehouse_location: str | None = None,
    packaging_type: PackagingType | None = None,
    performed_by: str = "system",
) -> Batch:
    """Creates a Batch, generates its Trace ID, and renders + attaches its
    QR code. Does not commit - caller owns the transaction so batch creation
    stays atomic with the GRN / FinishedGoods row that triggered it.
    """
    trace_id = generate_trace_id(db)

    batch = Batch(
        batch_number=batch_number,
        trace_id=trace_id,
        product_id=product_id,
        batch_type=batch_type,
        source_type=source_type,
        status=BatchStatus.ACTIVE,
        lot_number=lot_number,
        quantity=quantity,
        remaining_quantity=quantity,
        uom=uom,
        manufacturing_date=manufacturing_date,
        expiry_date=expiry_date,
        warehouse_location=warehouse_location,
        packaging_type=packaging_type,
    )
    db.add(batch)
    db.flush()  # need batch.id for the QR row and audit log

    assets = build_qr_assets(trace_id)
    qr_code = QRCode(
        batch_id=batch.id,
        trace_id=trace_id,
        qr_payload=assets.payload,
        target_url=assets.target_url,
        png_path=assets.png_path,
        svg_path=assets.svg_path,
    )
    db.add(qr_code)
    db.flush()

    log_action(
        db,
        AuditAction.BATCH_CREATED,
        "Batch",
        batch.id,
        f"Batch {batch_number} ({trace_id}) created",
        performed_by=performed_by,
    )
    log_action(
        db,
        AuditAction.QR_GENERATED,
        "QRCode",
        qr_code.id,
        f"QR generated for trace ID {trace_id}",
        performed_by=performed_by,
    )

    return batch
