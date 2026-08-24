"""Builds the end-to-end traceability graph + timeline for a Trace ID.

This is the heart of the platform: given any trace_id printed on a QR code
(raw material batch OR finished goods batch), reconstruct

    GRN Received -> Warehouse -> Material Issued -> Production Consumed
        -> Finished Goods Created -> Dispatched

by walking the relationships between Batch, GRN, InventoryMovement,
ProductionConsumption, ProductionOrder, FinishedGoods and Dispatch.
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.models.batch import Batch
from app.models.enums import BatchType, MovementType
from app.models.finished_goods import FinishedGoods
from app.models.production_consumption import ProductionConsumption


def _batch_summary(batch: Batch) -> dict[str, Any]:
    return {
        "traceId": batch.trace_id,
        "batchNumber": batch.batch_number,
        "batchType": batch.batch_type.value,
        "status": batch.status.value,
        "productId": batch.product_id,
        "productName": batch.product.name,
        "productSku": batch.product.sku,
        "quantity": float(batch.quantity),
        "remainingQuantity": float(batch.remaining_quantity),
        "uom": batch.uom,
        "warehouseLocation": batch.warehouse_location,
        "manufacturingDate": batch.manufacturing_date,
        "expiryDate": batch.expiry_date,
        "packagingType": batch.packaging_type.value if batch.packaging_type else None,
        "lotNumber": batch.lot_number,
    }


def _downstream_from_raw_batch(db: Session, batch: Batch) -> list[dict[str, Any]]:
    """Every finished-goods batch that this raw material batch fed into."""
    downstream = []
    for consumption in batch.consumptions:
        po = consumption.production_order
        for fg in po.finished_goods:
            downstream.append(
                {
                    "traceId": fg.batch.trace_id,
                    "fgBatchNumber": fg.fg_batch_number,
                    "productName": fg.product.name,
                    "quantity": float(fg.quantity),
                    "productionOrderNo": po.production_order_no,
                    "productionDate": fg.production_date,
                    "quantityConsumedFromThisBatch": float(consumption.quantity_consumed),
                }
            )
    return downstream


def _upstream_from_fg_batch(db: Session, fg: FinishedGoods) -> list[dict[str, Any]]:
    """Every raw-material batch consumed by the production order that made
    this finished-goods batch."""
    upstream = []
    for consumption in fg.production_order.consumptions:
        raw_batch = consumption.raw_batch
        grn = raw_batch.grn
        upstream.append(
            {
                "traceId": raw_batch.trace_id,
                "batchNumber": raw_batch.batch_number,
                "productName": raw_batch.product.name,
                "quantityConsumed": float(consumption.quantity_consumed),
                "supplierName": grn.supplier.name if grn else None,
                "grnNumber": grn.grn_number if grn else None,
                "consumedAt": consumption.consumed_at,
            }
        )
    return upstream


def _dispatch_events(batch: Batch) -> list[dict[str, Any]]:
    events = []
    for d in batch.dispatches:
        events.append(
            {
                "stage": "DISPATCHED",
                "title": "Dispatched",
                # dispatch_date is a plain Date (no time-of-day), but every
                # other event's timestamp comes from a DateTime(timezone=True)
                # column - attach UTC explicitly so this stays comparable to
                # those when the full timeline is sorted below (mixing naive
                # and aware datetimes raises TypeError on sort/comparison).
                "timestamp": datetime.combine(d.dispatch_date, datetime.min.time(), tzinfo=timezone.utc),
                "description": f"{d.quantity} {batch.uom} dispatched to {d.customer.name}",
                "details": {
                    "dispatchNumber": d.dispatch_number,
                    "customer": d.customer.name,
                    "quantity": float(d.quantity),
                    "status": d.status.value,
                },
            }
        )
    return events


def build_traceability(db: Session, trace_id: str) -> dict[str, Any]:
    batch = (
        db.query(Batch)
        .options(
            joinedload(Batch.product),
            joinedload(Batch.grn),
            joinedload(Batch.finished_goods),
            joinedload(Batch.qr_code),
            joinedload(Batch.dispatches),
            joinedload(Batch.movements),
            joinedload(Batch.consumptions),
        )
        .filter(Batch.trace_id == trace_id)
        .first()
    )
    if batch is None:
        raise HTTPException(status_code=404, detail=f"No batch found for trace ID {trace_id}")

    timeline: list[dict[str, Any]] = []
    upstream: list[dict[str, Any]] = []
    downstream: list[dict[str, Any]] = []

    if batch.batch_type == BatchType.RAW_MATERIAL:
        grn = batch.grn
        if grn:
            timeline.append(
                {
                    "stage": "GRN_RECEIVED",
                    "title": "GRN Received",
                    "timestamp": grn.received_date,
                    "description": (
                        f"{grn.quantity} {batch.uom} received from {grn.supplier.name} "
                        f"(GRN {grn.grn_number})"
                    ),
                    "details": {
                        "grnNumber": grn.grn_number,
                        "supplier": grn.supplier.name,
                        "quantity": float(grn.quantity),
                        "lotNumber": grn.lot_number,
                    },
                }
            )
            timeline.append(
                {
                    "stage": "WAREHOUSE",
                    "title": "Warehouse",
                    "timestamp": grn.received_date,
                    "description": f"Stored at {batch.warehouse_location}",
                    "details": {"warehouseLocation": batch.warehouse_location},
                }
            )

        for m in sorted(batch.movements, key=lambda x: x.movement_date):
            if m.movement_type == MovementType.ISSUE:
                timeline.append(
                    {
                        "stage": "MATERIAL_ISSUED",
                        "title": "Material Issued",
                        "timestamp": m.movement_date,
                        "description": (
                            f"{m.quantity} {batch.uom} issued to {m.department} "
                            f"(Req# {m.request_number})"
                        ),
                        "details": {
                            "requestNumber": m.request_number,
                            "department": m.department,
                            "requestedBy": m.requested_by,
                            "quantity": float(m.quantity),
                        },
                    }
                )

        for c in sorted(batch.consumptions, key=lambda x: x.consumed_at):
            po = c.production_order
            timeline.append(
                {
                    "stage": "PRODUCTION_CONSUMED",
                    "title": "Production Consumed",
                    "timestamp": c.consumed_at,
                    "description": (
                        f"{c.quantity_consumed} {batch.uom} consumed by production "
                        f"order {po.production_order_no}"
                    ),
                    "details": {
                        "productionOrderNo": po.production_order_no,
                        "quantityConsumed": float(c.quantity_consumed),
                    },
                }
            )
            for fg in po.finished_goods:
                timeline.append(
                    {
                        "stage": "FINISHED_GOODS_CREATED",
                        "title": "Finished Goods Created",
                        "timestamp": fg.created_at,
                        "description": (
                            f"FG batch {fg.fg_batch_number} ({fg.batch.trace_id}) created"
                        ),
                        "details": {
                            "fgBatchNumber": fg.fg_batch_number,
                            "traceId": fg.batch.trace_id,
                            "quantity": float(fg.quantity),
                        },
                    }
                )
                timeline.extend(_dispatch_events(fg.batch))

        downstream = _downstream_from_raw_batch(db, batch)

    else:  # FINISHED_GOOD
        fg = batch.finished_goods
        if fg:
            for c in fg.production_order.consumptions:
                rb = c.raw_batch
                timeline.append(
                    {
                        "stage": "PRODUCTION_CONSUMED",
                        "title": "Raw Material Consumed",
                        "timestamp": c.consumed_at,
                        "description": (
                            f"{c.quantity_consumed} {rb.uom} of {rb.product.name} "
                            f"({rb.trace_id}) consumed"
                        ),
                        "details": {
                            "traceId": rb.trace_id,
                            "batchNumber": rb.batch_number,
                            "productName": rb.product.name,
                            "quantityConsumed": float(c.quantity_consumed),
                        },
                    }
                )

            timeline.append(
                {
                    "stage": "FINISHED_GOODS_CREATED",
                    "title": "Finished Goods Created",
                    "timestamp": fg.created_at,
                    "description": (
                        f"FG batch {fg.fg_batch_number} created from production order "
                        f"{fg.production_order.production_order_no}"
                    ),
                    "details": {
                        "fgBatchNumber": fg.fg_batch_number,
                        "productionOrderNo": fg.production_order.production_order_no,
                        "quantity": float(fg.quantity),
                    },
                }
            )
            upstream = _upstream_from_fg_batch(db, fg)

        timeline.extend(_dispatch_events(batch))

    timeline.sort(key=lambda e: e["timestamp"])

    return {
        "batch": _batch_summary(batch),
        "qrCode": {
            "pngUrl": batch.qr_code.png_path if batch.qr_code else None,
            "svgUrl": batch.qr_code.svg_path if batch.qr_code else None,
            "targetUrl": batch.qr_code.target_url if batch.qr_code else None,
        }
        if batch.qr_code
        else None,
        "timeline": timeline,
        "upstreamRawMaterials": upstream,
        "downstreamFinishedGoods": downstream,
    }
