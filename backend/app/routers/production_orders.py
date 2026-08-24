from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.batch import Batch
from app.models.enums import AuditAction, ProductionOrderStatus
from app.models.product import Product
from app.models.production_consumption import ProductionConsumption
from app.models.production_order import ProductionOrder
from app.schemas.production import (
    ConsumeBatchRequest,
    ProductionConsumptionOut,
    ProductionOrderCreate,
    ProductionOrderDetailOut,
    ProductionOrderOut,
)
from app.services.audit_service import log_action
from app.services.id_generator import generate_production_order_no
from app.services.production_service import consume_raw_batch

router = APIRouter(prefix="/production-orders", tags=["Production"])


def _to_detail(po: ProductionOrder) -> ProductionOrderDetailOut:
    return ProductionOrderDetailOut(
        id=po.id,
        production_order_no=po.production_order_no,
        product_id=po.product_id,
        planned_quantity=float(po.planned_quantity),
        produced_quantity=float(po.produced_quantity),
        status=po.status,
        start_date=po.start_date,
        end_date=po.end_date,
        created_at=po.created_at,
        product_name=po.product.name if po.product else None,
    )


@router.get("", response_model=list[ProductionOrderDetailOut])
def list_production_orders(db: Session = Depends(get_db)):
    pos = db.query(ProductionOrder).options(joinedload(ProductionOrder.product)).order_by(
        ProductionOrder.created_at.desc()
    ).all()
    return [_to_detail(p) for p in pos]


@router.post("", response_model=ProductionOrderDetailOut, status_code=201)
def create_production_order(payload: ProductionOrderCreate, db: Session = Depends(get_db)):
    product = db.get(Product, payload.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    po = ProductionOrder(
        production_order_no=generate_production_order_no(db),
        product_id=product.id,
        planned_quantity=payload.planned_quantity,
        produced_quantity=0,
        status=ProductionOrderStatus.PLANNED,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )
    db.add(po)
    db.flush()

    log_action(
        db,
        AuditAction.PRODUCTION_ORDER_CREATED,
        "ProductionOrder",
        po.id,
        f"Production order {po.production_order_no} created for {payload.planned_quantity} "
        f"{product.uom} of {product.name}",
    )

    db.commit()
    db.refresh(po)
    return _to_detail(po)


@router.get("/{po_id}", response_model=ProductionOrderDetailOut)
def get_production_order(po_id: int, db: Session = Depends(get_db)):
    po = db.get(ProductionOrder, po_id)
    if not po:
        raise HTTPException(status_code=404, detail="Production order not found")
    return _to_detail(po)


@router.get("/{po_id}/consumption", response_model=list[ProductionConsumptionOut])
def list_consumption(po_id: int, db: Session = Depends(get_db)):
    return (
        db.query(ProductionConsumption)
        .filter(ProductionConsumption.production_order_id == po_id)
        .order_by(ProductionConsumption.consumed_at.desc())
        .all()
    )


@router.post("/{po_id}/consume", response_model=ProductionConsumptionOut, status_code=201)
def consume_batch(po_id: int, payload: ConsumeBatchRequest, db: Session = Depends(get_db)):
    """Operator scans a raw-material QR during production; the batch is
    looked up by trace_id and the consumed quantity is recorded and
    deducted from what remains of that batch."""
    po = db.get(ProductionOrder, po_id)
    if not po:
        raise HTTPException(status_code=404, detail="Production order not found")

    batch = db.scalar(select(Batch).where(Batch.trace_id == payload.trace_id))
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found for scanned trace ID")

    consumption = consume_raw_batch(
        db, po, batch, payload.quantity_consumed, payload.consumed_by
    )

    db.commit()
    db.refresh(consumption)
    return consumption
