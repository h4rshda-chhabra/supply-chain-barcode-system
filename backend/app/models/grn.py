from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.batch import Batch
    from app.models.product import Product
    from app.models.supplier import Supplier


class GRN(Base, TimestampMixin):
    """Goods Receipt Note - the entry point of raw material into the plant."""

    __tablename__ = "grns"

    id: Mapped[int] = mapped_column(primary_key=True)
    grn_number: Mapped[str] = mapped_column(String(30), unique=True, index=True)

    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    batch_id: Mapped[int] = mapped_column(ForeignKey("batches.id"), unique=True)

    quantity: Mapped[float] = mapped_column(Numeric(14, 3))
    batch_number: Mapped[str] = mapped_column(String(50))
    lot_number: Mapped[str | None] = mapped_column(String(50))
    manufacturing_date: Mapped[date | None] = mapped_column(Date)
    expiry_date: Mapped[date | None] = mapped_column(Date)
    warehouse_location: Mapped[str] = mapped_column(String(100))
    received_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    supplier: Mapped["Supplier"] = relationship(back_populates="grns")
    product: Mapped["Product"] = relationship(back_populates="grns")
    batch: Mapped["Batch"] = relationship(back_populates="grn")
