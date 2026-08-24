from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.grn import GRN
from app.models.product import Product
from app.models.supplier import Supplier
from app.schemas.grn import GRNCreate, GRNDetailOut
from app.services.grn_service import create_grn

router = APIRouter(prefix="/grns", tags=["GRN"])


def _to_detail(grn: GRN) -> GRNDetailOut:
    return GRNDetailOut(
        id=grn.id,
        grn_number=grn.grn_number,
        supplier_id=grn.supplier_id,
        product_id=grn.product_id,
        batch_id=grn.batch_id,
        quantity=float(grn.quantity),
        batch_number=grn.batch_number,
        lot_number=grn.lot_number,
        manufacturing_date=grn.manufacturing_date,
        expiry_date=grn.expiry_date,
        warehouse_location=grn.warehouse_location,
        received_date=grn.received_date,
        supplier_name=grn.supplier.name,
        product_name=grn.product.name,
        trace_id=grn.batch.trace_id,
        packaging_type=grn.batch.packaging_type,
    )


@router.get("", response_model=list[GRNDetailOut])
def list_grns(db: Session = Depends(get_db)):
    grns = (
        db.query(GRN)
        .options(joinedload(GRN.supplier), joinedload(GRN.product), joinedload(GRN.batch))
        .order_by(GRN.received_date.desc())
        .all()
    )
    return [_to_detail(g) for g in grns]


@router.post("", response_model=GRNDetailOut, status_code=201)
def create_grn_endpoint(payload: GRNCreate, db: Session = Depends(get_db)):
    supplier = db.get(Supplier, payload.supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    product = db.get(Product, payload.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    grn = create_grn(
        db,
        supplier,
        product,
        payload.quantity,
        payload.batch_number,
        payload.warehouse_location,
        uom=payload.uom,
        lot_number=payload.lot_number,
        manufacturing_date=payload.manufacturing_date,
        expiry_date=payload.expiry_date,
        packaging_type=payload.packaging_type,
    )

    db.commit()
    db.refresh(grn)
    return _to_detail(grn)


@router.get("/{grn_id}", response_model=GRNDetailOut)
def get_grn(grn_id: int, db: Session = Depends(get_db)):
    grn = db.get(GRN, grn_id)
    if not grn:
        raise HTTPException(status_code=404, detail="GRN not found")
    return _to_detail(grn)
