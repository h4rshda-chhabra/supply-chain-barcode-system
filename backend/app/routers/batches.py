from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.batch import Batch
from app.models.enums import BatchStatus, BatchType
from app.schemas.batch import BatchDetailOut

router = APIRouter(prefix="/batches", tags=["Batches"])


def _to_detail(batch: Batch) -> BatchDetailOut:
    return BatchDetailOut(
        id=batch.id,
        batch_number=batch.batch_number,
        trace_id=batch.trace_id,
        product_id=batch.product_id,
        batch_type=batch.batch_type,
        source_type=batch.source_type,
        status=batch.status,
        lot_number=batch.lot_number,
        quantity=float(batch.quantity),
        remaining_quantity=float(batch.remaining_quantity),
        uom=batch.uom,
        manufacturing_date=batch.manufacturing_date,
        expiry_date=batch.expiry_date,
        warehouse_location=batch.warehouse_location,
        packaging_type=batch.packaging_type,
        created_at=batch.created_at,
        product_name=batch.product.name if batch.product else None,
        product_sku=batch.product.sku if batch.product else None,
        qr_code=batch.qr_code,
    )


@router.get("", response_model=list[BatchDetailOut])
def list_batches(
    batch_type: BatchType | None = None,
    status: BatchStatus | None = None,
    product_id: int | None = None,
    search: str | None = Query(default=None, description="Search by trace ID or batch number"),
    db: Session = Depends(get_db),
):
    query = db.query(Batch).options(joinedload(Batch.product), joinedload(Batch.qr_code))
    if batch_type:
        query = query.filter(Batch.batch_type == batch_type)
    if status:
        query = query.filter(Batch.status == status)
    if product_id:
        query = query.filter(Batch.product_id == product_id)
    if search:
        like = f"%{search}%"
        query = query.filter(
            (Batch.trace_id.ilike(like)) | (Batch.batch_number.ilike(like))
        )
    batches = query.order_by(Batch.created_at.desc()).limit(500).all()
    return [_to_detail(b) for b in batches]


@router.get("/{trace_id}", response_model=BatchDetailOut)
def get_batch(trace_id: str, db: Session = Depends(get_db)):
    batch = db.scalar(
        select(Batch)
        .options(joinedload(Batch.product), joinedload(Batch.qr_code))
        .where(Batch.trace_id == trace_id)
    )
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return _to_detail(batch)
