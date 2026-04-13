import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey, Text, Integer, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[str] = mapped_column(String(100), nullable=True)
    agent_name: Mapped[str] = mapped_column(String(50), nullable=True)
    model_used: Mapped[str] = mapped_column(String(50), nullable=True)
    input_hash: Mapped[str] = mapped_column(String(128), nullable=True)
    output_summary: Mapped[str] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=True)
    token_count: Mapped[int] = mapped_column(Integer, nullable=True)
    extra_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class AnalyticsEvent(Base):
    """Anonymized events for the public transparency dashboard."""
    __tablename__ = "analytics_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    city: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=True)
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
