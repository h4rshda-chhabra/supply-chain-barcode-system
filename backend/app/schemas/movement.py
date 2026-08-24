from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import MovementType


class IssueRequestCreate(BaseModel):
    """Request & Issue module: create a request + fulfil it against a scanned batch."""

    trace_id: str
    department: str
    requested_by: str
    quantity: float = Field(gt=0)
    notes: str | None = None


class MovementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    movement_type: MovementType
    batch_id: int
    quantity: float
    request_number: str | None
    department: str | None
    requested_by: str | None
    reference_type: str | None
    reference_id: int | None
    notes: str | None
    movement_date: datetime
