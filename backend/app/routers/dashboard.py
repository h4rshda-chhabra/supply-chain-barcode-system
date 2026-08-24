from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.batch import Batch
from app.models.customer import Customer
from app.models.dispatch import Dispatch
from app.models.enums import BatchStatus
from app.models.finished_goods import FinishedGoods
from app.models.grn import GRN
from app.models.inventory_movement import InventoryMovement
from app.models.product import Product
from app.models.production_order import ProductionOrder
from app.models.supplier import Supplier
from app.schemas.dashboard import DashboardSummary, DashboardTrends, TrendPoint

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

TREND_WINDOW_DAYS = 30


@router.get("/summary", response_model=DashboardSummary)
def get_summary(db: Session = Depends(get_db)):
    return DashboardSummary(
        total_grns=db.scalar(select(func.count()).select_from(GRN)) or 0,
        active_batches=db.scalar(
            select(func.count()).select_from(Batch).where(Batch.status == BatchStatus.ACTIVE)
        )
        or 0,
        production_orders=db.scalar(select(func.count()).select_from(ProductionOrder)) or 0,
        finished_goods_batches=db.scalar(select(func.count()).select_from(FinishedGoods)) or 0,
        dispatches=db.scalar(select(func.count()).select_from(Dispatch)) or 0,
        total_suppliers=db.scalar(select(func.count()).select_from(Supplier)) or 0,
        total_products=db.scalar(select(func.count()).select_from(Product)) or 0,
        total_customers=db.scalar(select(func.count()).select_from(Customer)) or 0,
    )


def _daily_counts(db: Session, model, date_column, since_date=None) -> dict[str, int]:
    since = since_date or (datetime.utcnow() - timedelta(days=TREND_WINDOW_DAYS))
    rows = (
        db.query(func.date(date_column).label("day"), func.count().label("cnt"))
        .filter(date_column >= since)
        .group_by(func.date(date_column))
        .all()
    )
    return {str(r.day): r.cnt for r in rows}


def _fill_series(counts: dict[str, int]) -> list[TrendPoint]:
    points = []
    for i in range(TREND_WINDOW_DAYS, -1, -1):
        day = (datetime.utcnow() - timedelta(days=i)).date()
        points.append(TrendPoint(label=str(day), value=counts.get(str(day), 0)))
    return points


@router.get("/trends", response_model=DashboardTrends)
def get_trends(db: Session = Depends(get_db)):
    since_date = (datetime.utcnow() - timedelta(days=TREND_WINDOW_DAYS)).date()
    movement_counts = _daily_counts(db, InventoryMovement, InventoryMovement.movement_date)
    production_counts = _daily_counts(db, ProductionOrder, ProductionOrder.created_at)
    dispatch_counts = _daily_counts(db, Dispatch, Dispatch.dispatch_date, since_date=since_date)

    return DashboardTrends(
        batch_movement_trend=_fill_series(movement_counts),
        production_trend=_fill_series(production_counts),
        dispatch_trend=_fill_series(dispatch_counts),
    )
