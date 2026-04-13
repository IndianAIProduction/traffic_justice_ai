import uuid
from datetime import datetime, timezone
import enum

from sqlalchemy import String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CaseType(str, enum.Enum):
    TRAFFIC_STOP = "traffic_stop"
    CHALLAN = "challan"
    MISCONDUCT = "misconduct"


class CaseStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    case_type: Mapped[CaseType] = mapped_column(
        Enum(CaseType, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    status: Mapped[CaseStatus] = mapped_column(
        Enum(CaseStatus, values_callable=lambda e: [m.value for m in e]),
        default=CaseStatus.OPEN,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    state: Mapped[str] = mapped_column(String(100), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=True)
    location: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User", back_populates="cases")
    challans = relationship("Challan", back_populates="case", lazy="selectin")
    evidence_items = relationship("Evidence", back_populates="case", lazy="selectin")
    complaints = relationship("Complaint", back_populates="case", lazy="selectin")
    legal_queries = relationship("LegalQuery", back_populates="case", lazy="selectin")
