from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.dispatch import Dispatch


class Customer(Base, TimestampMixin):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(150), index=True)
    contact_email: Mapped[str | None] = mapped_column(String(150))
    contact_phone: Mapped[str | None] = mapped_column(String(30))
    address: Mapped[str | None] = mapped_column(String(300))

    # Reserved for future Microsoft Dynamics NAV 2016 customer sync
    # (maps to NAV's Customer "No.").
    erp_reference_no: Mapped[str | None] = mapped_column(String(20), index=True)

    dispatches: Mapped[list["Dispatch"]] = relationship(back_populates="customer")
