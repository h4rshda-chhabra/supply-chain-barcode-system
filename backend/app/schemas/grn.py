from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import PackagingType


class GRNCreate(BaseModel):
    supplier_id: int
    product_id: int
    quantity: float = Field(gt=0)
    batch_number: str
    lot_number: str | None = None
    manufacturing_date: date | None = None
    expiry_date: date | None = None
    warehouse_location: str
    uom: str = "EA"
    packaging_type: PackagingType | None = None


class GRNOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    grn_number: str
    supplier_id: int
    product_id: int
    batch_id: int
    quantity: float
    batch_number: str
    lot_number: str | None
    manufacturing_date: date | None
    expiry_date: date | None
    warehouse_location: str
    received_date: datetime
    packaging_type: PackagingType | None = None


class GRNDetailOut(GRNOut):
    supplier_name: str | None = None
    product_name: str | None = None
    trace_id: str | None = None
