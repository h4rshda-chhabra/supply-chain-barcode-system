from typing import TYPE_CHECKING

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ProductType
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.batch import Batch
    from app.models.grn import GRN


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    category: Mapped[str | None] = mapped_column(String(100))
    uom: Mapped[str] = mapped_column(String(20), default="EA")
    product_type: Mapped[ProductType] = mapped_column(
        Enum(ProductType, native_enum=False), default=ProductType.RAW_MATERIAL
    )
    description: Mapped[str | None] = mapped_column(String(500))

    # Reserved for future Microsoft Dynamics NAV 2016 item sync
    # (maps to NAV's Item "No.").
    erp_reference_no: Mapped[str | None] = mapped_column(String(20), index=True)

    grns: Mapped[list["GRN"]] = relationship(back_populates="product")
    batches: Mapped[list["Batch"]] = relationship(back_populates="product")
