from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import BatchSourceType, BatchStatus, BatchType, PackagingType
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.dispatch import Dispatch
    from app.models.finished_goods import FinishedGoods
    from app.models.grn import GRN
    from app.models.inventory_movement import InventoryMovement
    from app.models.product import Product
    from app.models.production_consumption import ProductionConsumption
    from app.models.qr_code import QRCode


class Batch(Base, TimestampMixin):
    """Central traceability unit.

    Every raw-material lot received via a GRN, and every finished-goods lot
    produced by a Production Order, is represented as exactly one Batch.
    The Batch is what a QR code (via its trace_id) ultimately resolves to,
    and it's the node every other module (movements, consumption,
    dispatch) hangs off of for the traceability graph.
    """

    __tablename__ = "batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    batch_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    trace_id: Mapped[str] = mapped_column(String(30), unique=True, index=True)

    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    batch_type: Mapped[BatchType] = mapped_column(Enum(BatchType, native_enum=False))
    source_type: Mapped[BatchSourceType] = mapped_column(
        Enum(BatchSourceType, native_enum=False)
    )
    status: Mapped[BatchStatus] = mapped_column(
        Enum(BatchStatus, native_enum=False), default=BatchStatus.ACTIVE
    )

    lot_number: Mapped[str | None] = mapped_column(String(50))
    quantity: Mapped[float] = mapped_column(Numeric(14, 3))
    remaining_quantity: Mapped[float] = mapped_column(Numeric(14, 3))
    uom: Mapped[str] = mapped_column(String(20), default="EA")

    manufacturing_date: Mapped[date | None] = mapped_column(Date)
    expiry_date: Mapped[date | None] = mapped_column(Date)
    warehouse_location: Mapped[str | None] = mapped_column(String(100))
    packaging_type: Mapped[PackagingType | None] = mapped_column(
        Enum(PackagingType, native_enum=False)
    )

    product: Mapped["Product"] = relationship(back_populates="batches")
    grn: Mapped["GRN | None"] = relationship(back_populates="batch", uselist=False)
    finished_goods: Mapped["FinishedGoods | None"] = relationship(
        back_populates="batch", uselist=False
    )
    qr_code: Mapped["QRCode | None"] = relationship(
        back_populates="batch", uselist=False, cascade="all, delete-orphan"
    )
    movements: Mapped[list["InventoryMovement"]] = relationship(
        back_populates="batch"
    )
    consumptions: Mapped[list["ProductionConsumption"]] = relationship(
        back_populates="raw_batch"
    )
    dispatches: Mapped[list["Dispatch"]] = relationship(back_populates="batch")
