from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.grn import GRN


class Supplier(Base, TimestampMixin):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(150), index=True)
    contact_email: Mapped[str | None] = mapped_column(String(150))
    contact_phone: Mapped[str | None] = mapped_column(String(30))
    address: Mapped[str | None] = mapped_column(String(300))

    # Reserved for future Microsoft Dynamics NAV 2016 vendor sync
    # (maps to NAV's Vendor "No.").
    erp_reference_no: Mapped[str | None] = mapped_column(String(20), index=True)

    grns: Mapped[list["GRN"]] = relationship(back_populates="supplier")
