from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.traceability_service import build_traceability

router = APIRouter(prefix="/trace", tags=["Traceability"])


@router.get("/{trace_id}")
def get_traceability(trace_id: str, db: Session = Depends(get_db)):
    return build_traceability(db, trace_id)
