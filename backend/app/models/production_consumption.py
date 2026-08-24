from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.batch import Batch
    from app.models.production_order import ProductionOrder


class ProductionConsumption(Base, TimestampMixin):
    """Records that a specific raw-material batch (identified via QR scan)
    was consumed by a specific production order. This join is what lets the
    traceability engine walk backwards from a finished good to every raw
    material lot that went into it.
    """

    __tablename__ = "production_consumption"

    id: Mapped[int] = mapped_column(primary_key=True)
    production_order_id: Mapped[int] = mapped_column(ForeignKey("production_orders.id"))
    raw_batch_id: Mapped[int] = mapped_column(ForeignKey("batches.id"))

    quantity_consumed: Mapped[float] = mapped_column(Numeric(14, 3))
    consumed_by: Mapped[str | None] = mapped_column(String(100))
    consumed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    production_order: Mapped["ProductionOrder"] = relationship(
        back_populates="consumptions"
    )
    raw_batch: Mapped["Batch"] = relationship(back_populates="consumptions")
