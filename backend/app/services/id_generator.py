"""Sequential, human-readable document number generation.

MVP uses a simple "count rows this year + 1" strategy per entity type. This
is adequate for demo/pilot volumes; a production rollout with concurrent
writers should switch this to a DB sequence or a SELECT ... FOR UPDATE
counter table, which is a drop-in change confined to this module.
"""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.batch import Batch
from app.models.dispatch import Dispatch
from app.models.enums import BatchType
from app.models.grn import GRN
from app.models.inventory_movement import InventoryMovement
from app.models.production_order import ProductionOrder


def _next_sequence(db: Session, model, number_column, prefix: str, extra_filter=None) -> int:
    """Counts existing rows whose number starts with `prefix` (e.g. "GRN-2026-")
    and returns the next 1-based sequence value. Uses an exact prefix match
    (not a bare substring) so it can never be thrown off by an unrelated
    value that happens to contain the same year, e.g. a free-text
    raw-material batch number."""
    query = select(func.count()).select_from(model).where(number_column.like(f"{prefix}%"))
    if extra_filter is not None:
        query = query.where(extra_filter)
    count = db.scalar(query)
    return (count or 0) + 1


def generate_trace_id(db: Session) -> str:
    year = datetime.utcnow().year
    prefix = f"{settings.TRACE_ID_PREFIX}-{year}-"
    seq = _next_sequence(db, Batch, Batch.trace_id, prefix)
    return f"{prefix}{seq:06d}"


def generate_grn_number(db: Session) -> str:
    year = datetime.utcnow().year
    prefix = f"GRN-{year}-"
    seq = _next_sequence(db, GRN, GRN.grn_number, prefix)
    return f"{prefix}{seq:06d}"


def generate_production_order_no(db: Session) -> str:
    year = datetime.utcnow().year
    prefix = f"PO-{year}-"
    seq = _next_sequence(db, ProductionOrder, ProductionOrder.production_order_no, prefix)
    return f"{prefix}{seq:06d}"


def generate_fg_batch_number(db: Session) -> str:
    """FG batch numbers share the `batches.batch_number` column with
    raw-material batch numbers (which are arbitrary, user/GRN-supplied
    text), so the sequence count must be scoped to FINISHED_GOOD rows only
    - otherwise an unrelated raw-material batch number can inflate the
    count and produce a duplicate FG batch number (unique constraint
    violation -> 500)."""
    year = datetime.utcnow().year
    prefix = f"FG-{year}-"
    seq = _next_sequence(
        db, Batch, Batch.batch_number, prefix, extra_filter=(Batch.batch_type == BatchType.FINISHED_GOOD)
    )
    return f"{prefix}{seq:06d}"


def generate_dispatch_number(db: Session) -> str:
    year = datetime.utcnow().year
    prefix = f"DIS-{year}-"
    seq = _next_sequence(db, Dispatch, Dispatch.dispatch_number, prefix)
    return f"{prefix}{seq:06d}"


def generate_request_number(db: Session) -> str:
    year = datetime.utcnow().year
    prefix_like = f"REQ-{year}-%"
    count = db.scalar(
        select(func.count())
        .select_from(InventoryMovement)
        .where(InventoryMovement.request_number.like(prefix_like))
    )
    seq = (count or 0) + 1
    return f"REQ-{year}-{seq:06d}"
