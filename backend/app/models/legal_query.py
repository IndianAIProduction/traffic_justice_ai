import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class LegalQuery(Base):
    __tablename__ = "legal_queries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id"), nullable=True, index=True
    )
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    response_text: Mapped[str] = mapped_column(Text, nullable=True)
    sections_cited: Mapped[dict] = mapped_column(JSON, default=list)
    state: Mapped[str] = mapped_column(String(100), nullable=True)
    extra_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    case = relationship("Case", back_populates="legal_queries")
