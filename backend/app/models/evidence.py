import uuid
from datetime import datetime, timezone
import enum

from sqlalchemy import String, DateTime, ForeignKey, Text, Float, Integer, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class FileType(str, enum.Enum):
    AUDIO = "audio"
    VIDEO = "video"
    IMAGE = "image"
    DOCUMENT = "document"


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False, index=True
    )
    file_type: Mapped[FileType] = mapped_column(
        Enum(FileType, values_callable=lambda e: [m.value for m in e]), nullable=False
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=True)
    transcription: Mapped[str] = mapped_column(Text, nullable=True)
    analysis: Mapped[dict] = mapped_column(JSON, default=dict)
    is_analyzed: Mapped[bool] = mapped_column(default=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    case = relationship("Case", back_populates="evidence_items")
    misconduct_flags = relationship("MisconductFlag", back_populates="evidence", lazy="selectin")


class MisconductFlag(Base):
    __tablename__ = "misconduct_flags"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    evidence_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evidence.id"), nullable=False, index=True
    )
    flag_type: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp_in_media: Mapped[str] = mapped_column(String(20), nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=True)
    raw_quote: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    evidence = relationship("Evidence", back_populates="misconduct_flags")
