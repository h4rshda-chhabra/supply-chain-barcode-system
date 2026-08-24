from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.enums import AuditAction
from app.models.qr_code import QRCode
from app.schemas.batch import QRCodeOut
from app.services.audit_service import log_action
from app.services.qr_service import render_qr_image

router = APIRouter(prefix="/qr-codes", tags=["QR Codes"])


def _get_qr(db: Session, trace_id: str) -> QRCode:
    qr = db.scalar(select(QRCode).where(QRCode.trace_id == trace_id))
    if not qr:
        raise HTTPException(status_code=404, detail="QR code not found for trace ID")
    return qr


def _media_type(format: str) -> str:
    return "image/png" if format == "png" else "image/svg+xml"


@router.get("/{trace_id}", response_model=QRCodeOut)
def get_qr_code(trace_id: str, db: Session = Depends(get_db)):
    return _get_qr(db, trace_id)


@router.get("/{trace_id}/image")
def get_qr_image(
    trace_id: str,
    format: str = Query(default="png", pattern="^(png|svg)$"),
    db: Session = Depends(get_db),
):
    """Renders the QR code image on demand from the stored target URL - no
    file is stored on disk, so this works the same whether the batch was
    created a second ago or a year ago, and needs no durable storage."""
    qr = _get_qr(db, trace_id)
    image_bytes = render_qr_image(qr.target_url, format)
    return Response(content=image_bytes, media_type=_media_type(format))


@router.post("/{trace_id}/print", response_model=QRCodeOut)
def reprint_qr_code(trace_id: str, db: Session = Depends(get_db)):
    """Records a reprint. The actual print job is handled client-side
    (browser print dialog on the PNG); this just tracks it for audit."""
    qr = _get_qr(db, trace_id)
    qr.print_count += 1
    log_action(
        db, AuditAction.QR_PRINTED, "QRCode", qr.id, f"QR reprinted for trace ID {trace_id}"
    )
    db.commit()
    db.refresh(qr)
    return qr


@router.get("/{trace_id}/download")
def download_qr_code(
    trace_id: str,
    format: str = Query(default="png", pattern="^(png|svg)$"),
    db: Session = Depends(get_db),
):
    qr = _get_qr(db, trace_id)
    image_bytes = render_qr_image(qr.target_url, format)

    qr.download_count += 1
    log_action(
        db,
        AuditAction.QR_DOWNLOADED,
        "QRCode",
        qr.id,
        f"QR ({format.upper()}) downloaded for trace ID {trace_id}",
    )
    db.commit()

    return Response(
        content=image_bytes,
        media_type=_media_type(format),
        headers={"Content-Disposition": f'attachment; filename="{trace_id}.{format}"'},
    )
