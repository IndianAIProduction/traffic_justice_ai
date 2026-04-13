import uuid
from datetime import datetime, timezone
import enum

from sqlalchemy import String, DateTime, ForeignKey, Text, Boolean, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ComplaintStatus(str, enum.Enum):
    DRAFTED = "drafted"
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    REJECTED = "rejected"


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False, index=True
    )
    complaint_type: Mapped[str] = mapped_column(String(100), nullable=False)
    portal_name: Mapped[str] = mapped_column(String(255), nullable=True)
    draft_text: Mapped[str] = mapped_column(Text, nullable=True)
    final_text: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[ComplaintStatus] = mapped_column(
        Enum(ComplaintStatus, values_callable=lambda e: [m.value for m in e]),
        default=ComplaintStatus.DRAFTED, nullable=False,
    )
    portal_complaint_id: Mapped[str] = mapped_column(String(100), nullable=True)
    portal_url: Mapped[str] = mapped_column(String(500), nullable=True)
    submission_screenshot_path: Mapped[str] = mapped_column(String(500), nullable=True)
    user_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    case = relationship("Case", back_populates="complaints")
    actions = relationship("ComplaintAction", back_populates="complaint", lazy="selectin")
    reminders = relationship("Reminder", back_populates="complaint", lazy="selectin")


class ComplaintAction(Base):
    __tablename__ = "complaint_actions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    complaint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("complaints.id"), nullable=False, index=True
    )
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    performed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    complaint = relationship("Complaint", back_populates="actions")


class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    complaint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("complaints.id"), nullable=False, index=True
    )
    remind_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reminded: Mapped[bool] = mapped_column(Boolean, default=False)
    message: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    complaint = relationship("Complaint", back_populates="reminders")
