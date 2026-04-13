"""
Tracker service: background task for monitoring complaint status and triggering escalation.
"""
from datetime import datetime, timezone
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.complaint import Complaint, ComplaintStatus, Reminder
from app.services.complaint_service import update_complaint_status, log_complaint_action
from app.core.logging import get_logger

logger = get_logger(__name__)

ESCALATION_THRESHOLD_DAYS = 30


async def check_pending_complaints(db: AsyncSession) -> List[dict]:
    """Check all submitted complaints for status updates and escalation."""
    result = await db.execute(
        select(Complaint).where(
            Complaint.status.in_([
                ComplaintStatus.SUBMITTED,
                ComplaintStatus.ACKNOWLEDGED,
                ComplaintStatus.IN_PROGRESS,
            ])
        )
    )
    complaints = result.scalars().all()
    updates = []

    for complaint in complaints:
        if not complaint.submitted_at:
            continue

        days_since = (datetime.now(timezone.utc) - complaint.submitted_at).days

        if days_since >= ESCALATION_THRESHOLD_DAYS and complaint.status != ComplaintStatus.ESCALATED:
            await update_complaint_status(
                complaint.id,
                ComplaintStatus.ESCALATED,
                db,
            )
            await log_complaint_action(
                complaint.id,
                "auto_escalated",
                {
                    "days_since_submission": days_since,
                    "threshold": ESCALATION_THRESHOLD_DAYS,
                },
                db,
            )
            updates.append({
                "complaint_id": str(complaint.id),
                "action": "escalated",
                "days_since_submission": days_since,
            })
            logger.info(f"Auto-escalated complaint {complaint.id} after {days_since} days")

    return updates


async def process_reminders(db: AsyncSession) -> int:
    """Send due reminders for tracked complaints."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Reminder).where(
            Reminder.reminded.is_(False),
            Reminder.remind_at <= now,
        )
    )
    reminders = result.scalars().all()
    count = 0

    for reminder in reminders:
        reminder.reminded = True
        await log_complaint_action(
            reminder.complaint_id,
            "reminder_sent",
            {"message": reminder.message},
            db,
        )
        count += 1

    await db.flush()
    logger.info(f"Processed {count} reminders")
    return count
