import json

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.enums import AuditAction


def log_action(
    db: Session,
    action: AuditAction,
    entity_type: str,
    entity_id: int | None,
    description: str,
    performed_by: str = "system",
    extra_data: dict | None = None,
) -> AuditLog:
    entry = AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        performed_by=performed_by,
        extra_data=json.dumps(extra_data) if extra_data else None,
    )
    db.add(entry)
    db.flush()
    return entry
