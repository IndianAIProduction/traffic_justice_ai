import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey, Boolean, Float, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Challan(Base):
    __tablename__ = "challans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False, index=True
    )
    challan_number: Mapped[str] = mapped_column(String(100), nullable=True)
    sections: Mapped[dict] = mapped_column(JSON, default=dict)
    fines: Mapped[dict] = mapped_column(JSON, default=dict)
    total_fine_charged: Mapped[float] = mapped_column(Float, nullable=True)
    total_fine_valid: Mapped[float] = mapped_column(Float, nullable=True)
    issuing_officer: Mapped[str] = mapped_column(String(255), nullable=True)
    officer_badge_number: Mapped[str] = mapped_column(String(50), nullable=True)
    location: Mapped[str] = mapped_column(String(500), nullable=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    is_valid: Mapped[bool] = mapped_column(Boolean, nullable=True)
    has_overcharge: Mapped[bool] = mapped_column(Boolean, nullable=True)
    validation_result: Mapped[dict] = mapped_column(JSON, default=dict)
    raw_text: Mapped[str] = mapped_column(Text, nullable=True)
    image_path: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    case = relationship("Case", back_populates="challans")
