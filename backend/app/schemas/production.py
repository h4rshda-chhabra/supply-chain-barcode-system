from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import PackagingType, ProductionOrderStatus


class ProductionOrderCreate(BaseModel):
    product_id: int
    planned_quantity: float = Field(gt=0)
    start_date: date | None = None
    end_date: date | None = None


class ProductionOrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    production_order_no: str
    product_id: int
    planned_quantity: float
    produced_quantity: float
    status: ProductionOrderStatus
    start_date: date | None
    end_date: date | None
    created_at: datetime


class ProductionOrderDetailOut(ProductionOrderOut):
    product_name: str | None = None


class ConsumeBatchRequest(BaseModel):
    """Operator scans a raw-material QR and records how much was consumed."""

    trace_id: str
    quantity_consumed: float = Field(gt=0)
    consumed_by: str | None = None


class ProductionConsumptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    production_order_id: int
    raw_batch_id: int
    quantity_consumed: float
    consumed_by: str | None
    consumed_at: datetime


class FinishedGoodsCreate(BaseModel):
    production_order_id: int
    quantity: float = Field(gt=0)
    production_date: date
    warehouse_location: str | None = None
    packaging_type: PackagingType | None = None


class FinishedGoodsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    fg_batch_number: str
    batch_id: int
    production_order_id: int
    product_id: int
    quantity: float
    production_date: date
    created_at: datetime
    packaging_type: PackagingType | None = None


class FinishedGoodsDetailOut(FinishedGoodsOut):
    product_name: str | None = None
    trace_id: str | None = None
