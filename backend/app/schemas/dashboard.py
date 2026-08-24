from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_grns: int
    active_batches: int
    production_orders: int
    finished_goods_batches: int
    dispatches: int
    total_suppliers: int
    total_products: int
    total_customers: int


class TrendPoint(BaseModel):
    label: str
    value: float


class DashboardTrends(BaseModel):
    batch_movement_trend: list[TrendPoint]
    production_trend: list[TrendPoint]
    dispatch_trend: list[TrendPoint]
