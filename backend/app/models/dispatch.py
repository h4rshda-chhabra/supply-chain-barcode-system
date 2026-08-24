from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import DispatchStatus
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.batch import Batch
    from app.models.customer import Customer


class Dispatch(Base, TimestampMixin):
    __tablename__ = "dispatches"

    id: Mapped[int] = mapped_column(primary_key=True)
    dispatch_number: Mapped[str] = mapped_column(String(30), unique=True, index=True)

    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    batch_id: Mapped[int] = mapped_column(ForeignKey("batches.id"))

    quantity: Mapped[float] = mapped_column(Numeric(14, 3))
    dispatch_date: Mapped[date]
    status: Mapped[DispatchStatus] = mapped_column(
        Enum(DispatchStatus, native_enum=False), default=DispatchStatus.DISPATCHED
    )

    customer: Mapped["Customer"] = relationship(back_populates="dispatches")
    batch: Mapped["Batch"] = relationship(back_populates="dispatches")
