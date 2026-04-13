"""Initial schema - all tables

Revision ID: 0001_initial
Revises:
Create Date: 2026-02-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, index=True, nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("role", sa.String(20), nullable=False, server_default="user"),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    casetype_enum = postgresql.ENUM("traffic_stop", "challan", "misconduct", name="casetype", create_type=True)
    casestatus_enum = postgresql.ENUM("open", "in_progress", "resolved", "closed", "escalated", name="casestatus", create_type=True)

    op.create_table(
        "cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("case_type", casetype_enum, nullable=False),
        sa.Column("status", casestatus_enum, nullable=False, server_default="open"),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("location", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "challans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id"), nullable=False, index=True),
        sa.Column("challan_number", sa.String(100), nullable=True),
        sa.Column("sections", postgresql.JSONB(), server_default="{}"),
        sa.Column("fines", postgresql.JSONB(), server_default="{}"),
        sa.Column("total_fine_charged", sa.Float(), nullable=True),
        sa.Column("total_fine_valid", sa.Float(), nullable=True),
        sa.Column("issuing_officer", sa.String(255), nullable=True),
        sa.Column("officer_badge_number", sa.String(50), nullable=True),
        sa.Column("location", sa.String(500), nullable=True),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_valid", sa.Boolean(), nullable=True),
        sa.Column("has_overcharge", sa.Boolean(), nullable=True),
        sa.Column("validation_result", postgresql.JSONB(), server_default="{}"),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("image_path", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "legal_queries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id"), nullable=True, index=True),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("response_text", sa.Text(), nullable=True),
        sa.Column("sections_cited", postgresql.JSONB(), server_default="[]"),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    filetype_enum = postgresql.ENUM("audio", "video", "image", "document", name="filetype", create_type=True)

    op.create_table(
        "evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id"), nullable=False, index=True),
        sa.Column("file_type", filetype_enum, nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_hash", sa.String(128), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("transcription", sa.Text(), nullable=True),
        sa.Column("analysis", postgresql.JSONB(), server_default="{}"),
        sa.Column("is_analyzed", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "misconduct_flags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("evidence_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("evidence.id"), nullable=False, index=True),
        sa.Column("flag_type", sa.String(100), nullable=False),
        sa.Column("severity", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("timestamp_in_media", sa.String(20), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("raw_quote", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    complaintstatus_enum = postgresql.ENUM(
        "drafted", "submitted", "acknowledged", "in_progress", "resolved", "escalated", "rejected",
        name="complaintstatus", create_type=True,
    )

    op.create_table(
        "complaints",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id"), nullable=False, index=True),
        sa.Column("complaint_type", sa.String(100), nullable=False),
        sa.Column("portal_name", sa.String(255), nullable=True),
        sa.Column("draft_text", sa.Text(), nullable=True),
        sa.Column("final_text", sa.Text(), nullable=True),
        sa.Column("status", complaintstatus_enum, nullable=False, server_default="drafted"),
        sa.Column("portal_complaint_id", sa.String(100), nullable=True),
        sa.Column("portal_url", sa.String(500), nullable=True),
        sa.Column("submission_screenshot_path", sa.String(500), nullable=True),
        sa.Column("user_consent", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "complaint_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("complaint_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("complaints.id"), nullable=False, index=True),
        sa.Column("action_type", sa.String(100), nullable=False),
        sa.Column("details", postgresql.JSONB(), server_default="{}"),
        sa.Column("performed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "reminders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("complaint_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("complaints.id"), nullable=False, index=True),
        sa.Column("remind_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reminded", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("action", sa.String(100), nullable=False, index=True),
        sa.Column("entity_type", sa.String(50), nullable=True),
        sa.Column("entity_id", sa.String(100), nullable=True),
        sa.Column("agent_name", sa.String(50), nullable=True),
        sa.Column("model_used", sa.String(50), nullable=True),
        sa.Column("input_hash", sa.String(128), nullable=True),
        sa.Column("output_summary", sa.Text(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "analytics_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_type", sa.String(100), nullable=False, index=True),
        sa.Column("state", sa.String(100), nullable=True, index=True),
        sa.Column("city", sa.String(100), nullable=True, index=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("data", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("analytics_events")
    op.drop_table("audit_logs")
    op.drop_table("reminders")
    op.drop_table("complaint_actions")
    op.drop_table("complaints")
    op.drop_table("misconduct_flags")
    op.drop_table("evidence")
    op.drop_table("legal_queries")
    op.drop_table("challans")
    op.drop_table("cases")
    op.drop_table("users")
    sa.Enum(name="casetype").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="casestatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="filetype").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="complaintstatus").drop(op.get_bind(), checkfirst=True)
