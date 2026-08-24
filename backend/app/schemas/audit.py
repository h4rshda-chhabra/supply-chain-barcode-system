from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import AuditAction


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    action: AuditAction
    entity_type: str
    entity_id: int | None
    description: str
    performed_by: str
    created_at: datetime
