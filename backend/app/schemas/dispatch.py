from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DispatchStatus


class DispatchCreate(BaseModel):
    customer_id: int
    trace_id: str  # scanned FG batch QR
    quantity: float = Field(gt=0)
    dispatch_date: date


class DispatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    dispatch_number: str
    customer_id: int
    batch_id: int
    quantity: float
    dispatch_date: date
    status: DispatchStatus
    created_at: datetime


class DispatchDetailOut(DispatchOut):
    customer_name: str | None = None
    product_name: str | None = None
    trace_id: str | None = None
