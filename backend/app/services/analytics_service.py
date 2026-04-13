"""
Analytics service: anonymized event logging and aggregation for the transparency dashboard.
"""
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AnalyticsEvent, AuditLog
from app.core.logging import get_logger

logger = get_logger(__name__)


async def log_analytics_event(
    event_type: str,
    db: AsyncSession,
    state: Optional[str] = None,
    city: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    data: Optional[dict] = None,
) -> AnalyticsEvent:
    """Log an anonymized analytics event (no user_id stored)."""
    event = AnalyticsEvent(
        event_type=event_type,
        state=state,
        city=city,
        latitude=latitude,
        longitude=longitude,
        data=data or {},
    )
    db.add(event)
    await db.flush()
    return event


async def log_audit(
    action: str,
    db: AsyncSession,
    user_id=None,
    entity_type: str = None,
    entity_id: str = None,
    agent_name: str = None,
    model_used: str = None,
    input_hash: str = None,
    output_summary: str = None,
    latency_ms: int = None,
    token_count: int = None,
    extra_metadata: dict = None,
) -> AuditLog:
    """Log an audit entry for traceability."""
    log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        agent_name=agent_name,
        model_used=model_used,
        input_hash=input_hash,
        output_summary=output_summary,
        latency_ms=latency_ms,
        token_count=token_count,
        extra_metadata=extra_metadata or {},
    )
    db.add(log)
    await db.flush()
    return log
