from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.finished_goods import FinishedGoods
from app.models.production_order import ProductionOrder
from app.schemas.production import FinishedGoodsCreate, FinishedGoodsDetailOut
from app.services.production_service import create_finished_goods as create_finished_goods_service

router = APIRouter(prefix="/finished-goods", tags=["Finished Goods"])


def _to_detail(fg: FinishedGoods) -> FinishedGoodsDetailOut:
    return FinishedGoodsDetailOut(
        id=fg.id,
        fg_batch_number=fg.fg_batch_number,
        batch_id=fg.batch_id,
        production_order_id=fg.production_order_id,
        product_id=fg.product_id,
        quantity=float(fg.quantity),
        production_date=fg.production_date,
        created_at=fg.created_at,
        product_name=fg.product.name if fg.product else None,
        trace_id=fg.batch.trace_id if fg.batch else None,
        packaging_type=fg.batch.packaging_type if fg.batch else None,
    )


@router.get("", response_model=list[FinishedGoodsDetailOut])
def list_finished_goods(db: Session = Depends(get_db)):
    items = (
        db.query(FinishedGoods)
        .options(joinedload(FinishedGoods.product), joinedload(FinishedGoods.batch))
        .order_by(FinishedGoods.created_at.desc())
        .all()
    )
    return [_to_detail(f) for f in items]


@router.post("", response_model=FinishedGoodsDetailOut, status_code=201)
def create_finished_goods(payload: FinishedGoodsCreate, db: Session = Depends(get_db)):
    po = db.get(ProductionOrder, payload.production_order_id)
    if not po:
        raise HTTPException(status_code=404, detail="Production order not found")

    fg = create_finished_goods_service(
        db,
        po,
        payload.quantity,
        payload.production_date,
        payload.warehouse_location,
        packaging_type=payload.packaging_type,
    )

    db.commit()
    db.refresh(fg)
    return _to_detail(fg)


@router.get("/{fg_id}", response_model=FinishedGoodsDetailOut)
def get_finished_goods(fg_id: int, db: Session = Depends(get_db)):
    fg = db.get(FinishedGoods, fg_id)
    if not fg:
        raise HTTPException(status_code=404, detail="Finished goods batch not found")
    return _to_detail(fg)
