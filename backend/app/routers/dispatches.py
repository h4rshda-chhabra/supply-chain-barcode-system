from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.batch import Batch
from app.models.customer import Customer
from app.models.dispatch import Dispatch
from app.schemas.dispatch import DispatchCreate, DispatchDetailOut
from app.services.dispatch_service import create_dispatch as create_dispatch_service

router = APIRouter(prefix="/dispatches", tags=["Dispatch"])


def _to_detail(dispatch: Dispatch) -> DispatchDetailOut:
    return DispatchDetailOut(
        id=dispatch.id,
        dispatch_number=dispatch.dispatch_number,
        customer_id=dispatch.customer_id,
        batch_id=dispatch.batch_id,
        quantity=float(dispatch.quantity),
        dispatch_date=dispatch.dispatch_date,
        status=dispatch.status,
        created_at=dispatch.created_at,
        customer_name=dispatch.customer.name if dispatch.customer else None,
        product_name=dispatch.batch.product.name if dispatch.batch else None,
        trace_id=dispatch.batch.trace_id if dispatch.batch else None,
    )


@router.get("", response_model=list[DispatchDetailOut])
def list_dispatches(db: Session = Depends(get_db)):
    dispatches = (
        db.query(Dispatch)
        .options(
            joinedload(Dispatch.customer),
            joinedload(Dispatch.batch).joinedload(Batch.product),
        )
        .order_by(Dispatch.created_at.desc())
        .all()
    )
    return [_to_detail(d) for d in dispatches]


@router.post("", response_model=DispatchDetailOut, status_code=201)
def create_dispatch(payload: DispatchCreate, db: Session = Depends(get_db)):
    customer = db.get(Customer, payload.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    batch = db.scalar(select(Batch).where(Batch.trace_id == payload.trace_id))
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found for scanned trace ID")

    dispatch = create_dispatch_service(
        db, customer, batch, payload.quantity, payload.dispatch_date
    )

    db.commit()
    db.refresh(dispatch)
    return _to_detail(dispatch)


@router.get("/{dispatch_id}", response_model=DispatchDetailOut)
def get_dispatch(dispatch_id: int, db: Session = Depends(get_db)):
    dispatch = db.get(Dispatch, dispatch_id)
    if not dispatch:
        raise HTTPException(status_code=404, detail="Dispatch not found")
    return _to_detail(dispatch)
