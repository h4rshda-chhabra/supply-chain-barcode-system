"""QR code generation for batch traceability.

Design decision: the QR image encodes the *URL* `{TRACE_PUBLIC_BASE_URL}/trace/{traceId}`
so that scanning it with a standard phone camera opens the traceability page
directly. The minimal logical payload `{"traceId": "..."}` is kept alongside
it (qr_payload) as the canonical machine-readable content for any in-app
scanner that wants just the ID. In both cases the QR carries nothing but the
trace ID - no batch, product, or business data - so nothing sensitive leaks
if a code is photographed off a pallet.

Images are rendered on demand (see routers/qr_codes.py's /image and
/download endpoints) rather than pre-rendered and saved to disk: a batch's
QR content is fully determined by its trace_id + target_url, both already
in the database, so there's nothing to persist as a file. This also means
the app has no dependency on durable local disk storage, which matters on
platforms (e.g. Render's standard web services) whose container filesystem
is wiped on every restart/redeploy.
"""

import io
import json
from dataclasses import dataclass

import qrcode
import qrcode.image.svg

from app.core.config import settings


@dataclass
class QRAssets:
    trace_id: str
    payload: str
    target_url: str
    png_path: str  # API endpoint URL, e.g. /api/v1/qr-codes/{traceId}/image?format=png
    svg_path: str


def _image_endpoint(trace_id: str, fmt: str) -> str:
    return f"{settings.API_V1_PREFIX}/qr-codes/{trace_id}/image?format={fmt}"


def build_qr_assets(trace_id: str) -> QRAssets:
    """Computes (but does not render) the QR metadata for a trace ID: the
    target URL it should resolve to, the canonical JSON payload, and the
    endpoint URLs the frontend/consumers can hit to get the actual image
    bytes (rendered on demand, see render_qr_image below)."""
    target_url = f"{settings.TRACE_PUBLIC_BASE_URL}/trace/{trace_id}"
    payload = json.dumps({"traceId": trace_id})

    return QRAssets(
        trace_id=trace_id,
        payload=payload,
        target_url=target_url,
        png_path=_image_endpoint(trace_id, "png"),
        svg_path=_image_endpoint(trace_id, "svg"),
    )


def render_qr_image(target_url: str, fmt: str) -> bytes:
    """Renders a QR code for `target_url` in-memory and returns the raw
    image bytes. Called on every image/download request - cheap (a few ms)
    and avoids needing any persistent storage for QR assets."""
    if fmt == "svg":
        factory = qrcode.image.svg.SvgPathImage
        img = qrcode.make(target_url, image_factory=factory, box_size=10, border=4)
        buf = io.BytesIO()
        img.save(buf)
        return buf.getvalue()

    img = qrcode.make(target_url, box_size=10, border=4)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
