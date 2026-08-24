from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import (
    audit_logs,
    batches,
    customers,
    dashboard,
    dispatches,
    finished_goods,
    grns,
    movements,
    production_orders,
    products,
    qr_codes,
    suppliers,
    traceability,
)

# Import models package so every model class (and its relationship() string
# references) is registered on Base's mapper registry before first use.
# Schema itself is managed by Alembic (see migrations/), not create_all.
import app.models  # noqa: F401

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description=(
        "QR Code Tracking & Traceability Platform for manufacturing - "
        "end-to-end material and product traceability from GRN through dispatch."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


api = settings.API_V1_PREFIX
for router in (
    suppliers.router,
    customers.router,
    products.router,
    grns.router,
    batches.router,
    qr_codes.router,
    movements.router,
    production_orders.router,
    finished_goods.router,
    dispatches.router,
    traceability.router,
    dashboard.router,
    audit_logs.router,
):
    app.include_router(router, prefix=api)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "app": settings.APP_NAME}
