from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.batch import Batch


class QRCode(Base, TimestampMixin):
    """The physical QR asset for a batch.

    Deliberately stores only a minimal payload ({"traceId": ...}) so the
    printed/scanned code never leaks business data and always resolves
    through the traceability engine, which can apply access rules later.
    """

    __tablename__ = "qr_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("batches.id"), unique=True)
    trace_id: Mapped[str] = mapped_column(String(30), unique=True, index=True)

    qr_payload: Mapped[str] = mapped_column(Text)  # JSON string, e.g. {"traceId": "..."}
    target_url: Mapped[str] = mapped_column(String(300))  # /trace/{trace_id} absolute URL

    png_path: Mapped[str] = mapped_column(String(300))
    svg_path: Mapped[str] = mapped_column(String(300))

    print_count: Mapped[int] = mapped_column(Integer, default=0)
    download_count: Mapped[int] = mapped_column(Integer, default=0)

    batch: Mapped["Batch"] = relationship(back_populates="qr_code")
