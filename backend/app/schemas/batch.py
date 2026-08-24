from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import BatchSourceType, BatchStatus, BatchType, PackagingType


class QRCodeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    trace_id: str
    target_url: str
    png_path: str
    svg_path: str
    print_count: int
    download_count: int


class BatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    batch_number: str
    trace_id: str
    product_id: int
    batch_type: BatchType
    source_type: BatchSourceType
    status: BatchStatus
    lot_number: str | None
    quantity: float
    remaining_quantity: float
    uom: str
    manufacturing_date: date | None
    expiry_date: date | None
    warehouse_location: str | None
    packaging_type: PackagingType | None
    created_at: datetime


class BatchDetailOut(BatchOut):
    product_name: str | None = None
    product_sku: str | None = None
    qr_code: QRCodeOut | None = None
