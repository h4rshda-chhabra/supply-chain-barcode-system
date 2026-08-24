from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import MovementType
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.batch import Batch


class InventoryMovement(Base, TimestampMixin):
    """Every quantity movement of a batch: issue, production consumption,
    FG creation, or dispatch. This is the ledger the traceability engine
    and dashboards read from.
    """

    __tablename__ = "inventory_movements"

    id: Mapped[int] = mapped_column(primary_key=True)
    movement_type: Mapped[MovementType] = mapped_column(
        Enum(MovementType, native_enum=False)
    )
    batch_id: Mapped[int] = mapped_column(ForeignKey("batches.id"))
    quantity: Mapped[float] = mapped_column(Numeric(14, 3))

    request_number: Mapped[str | None] = mapped_column(String(30), index=True)
    department: Mapped[str | None] = mapped_column(String(100))
    requested_by: Mapped[str | None] = mapped_column(String(100))

    reference_type: Mapped[str | None] = mapped_column(String(50))
    reference_id: Mapped[int | None] = mapped_column(Integer)

    notes: Mapped[str | None] = mapped_column(String(300))
    movement_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    batch: Mapped["Batch"] = relationship(back_populates="movements")
