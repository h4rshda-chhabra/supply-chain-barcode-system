from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.batch import Batch
    from app.models.product import Product
    from app.models.production_order import ProductionOrder


class FinishedGoods(Base, TimestampMixin):
    __tablename__ = "finished_goods"

    id: Mapped[int] = mapped_column(primary_key=True)
    fg_batch_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)

    batch_id: Mapped[int] = mapped_column(ForeignKey("batches.id"), unique=True)
    production_order_id: Mapped[int] = mapped_column(ForeignKey("production_orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))

    quantity: Mapped[float] = mapped_column(Numeric(14, 3))
    production_date: Mapped[date]

    batch: Mapped["Batch"] = relationship(back_populates="finished_goods")
    production_order: Mapped["ProductionOrder"] = relationship(
        back_populates="finished_goods"
    )
    product: Mapped["Product"] = relationship()
