"""
Complaint service: handles complaint lifecycle management.
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.complaint import Complaint, ComplaintAction, ComplaintStatus
from app.core.logging import get_logger

logger = get_logger(__name__)


async def log_complaint_action(
    complaint_id,
    action_type: str,
    details: dict,
    db: AsyncSession,
) -> ComplaintAction:
    """Log an action on a complaint for audit trail."""
    action = ComplaintAction(
        complaint_id=complaint_id,
        action_type=action_type,
        details=details,
    )
    db.add(action)
    await db.flush()
    return action


async def update_complaint_status(
    complaint_id,
    new_status: ComplaintStatus,
    db: AsyncSession,
    portal_complaint_id: Optional[str] = None,
) -> Complaint:
    """Update complaint status and log the transition."""
    result = await db.execute(select(Complaint).where(Complaint.id == complaint_id))
    complaint = result.scalar_one_or_none()
    if not complaint:
        return None

    old_status = complaint.status
    complaint.status = new_status

    if portal_complaint_id:
        complaint.portal_complaint_id = portal_complaint_id

    if new_status == ComplaintStatus.RESOLVED:
        complaint.resolved_at = datetime.now(timezone.utc)

    await log_complaint_action(
        complaint_id=complaint.id,
        action_type="status_change",
        details={
            "old_status": old_status.value,
            "new_status": new_status.value,
        },
        db=db,
    )

    await db.flush()
    await db.refresh(complaint)

    logger.info(f"Complaint {complaint_id}: {old_status.value} -> {new_status.value}")
    return complaint
