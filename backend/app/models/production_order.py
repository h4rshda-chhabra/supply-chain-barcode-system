from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ProductionOrderStatus
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.finished_goods import FinishedGoods
    from app.models.product import Product
    from app.models.production_consumption import ProductionConsumption


class ProductionOrder(Base, TimestampMixin):
    __tablename__ = "production_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    production_order_no: Mapped[str] = mapped_column(String(30), unique=True, index=True)

    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    planned_quantity: Mapped[float] = mapped_column(Numeric(14, 3))
    produced_quantity: Mapped[float] = mapped_column(Numeric(14, 3), default=0)

    status: Mapped[ProductionOrderStatus] = mapped_column(
        Enum(ProductionOrderStatus, native_enum=False),
        default=ProductionOrderStatus.PLANNED,
    )

    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)

    product: Mapped["Product"] = relationship()
    consumptions: Mapped[list["ProductionConsumption"]] = relationship(
        back_populates="production_order"
    )
    finished_goods: Mapped[list["FinishedGoods"]] = relationship(
        back_populates="production_order"
    )
