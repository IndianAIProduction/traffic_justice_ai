"""
Portal Submission Orchestrator: Coordinates multi-channel complaint submission.

Channels (in order of reliability):
1. Email to government authority addresses (most reliable)
2. PDF generation for user records and manual submission
3. Playwright browser automation for portal submission (best-effort)
"""
import asyncio
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone

from app.services.portal_registry import (
    resolve_submission_target,
    SubmissionTarget,
)
from app.services.email_service import send_complaint_email, EmailResult
from app.services.pdf_service import generate_complaint_pdf
from app.agents.tools.portal_tools import submit_to_portal
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SubmissionResult:
    """Aggregated result of multi-channel complaint submission."""
    success: bool
    state_name: str
    portal_name: str
    portal_url: str
    complaint_form_url: Optional[str] = None

    # Email channel
    email_sent: bool = False
    email_recipients: List[str] = field(default_factory=list)
    email_error: Optional[str] = None

    # PDF channel
    pdf_generated: bool = False
    pdf_path: Optional[str] = None

    # Portal automation channel
    portal_automation_status: str = "skipped"
    portal_screenshot_path: Optional[str] = None
    portal_complaint_id: Optional[str] = None

    # Summary
    helplines: Dict[str, str] = field(default_factory=dict)
    submitted_at: Optional[str] = None
    channels_attempted: List[str] = field(default_factory=list)
    channels_succeeded: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


async def submit_complaint_to_authorities(
    complaint_id: str,
    complaint_text: str,
    complaint_type: str,
    state: str,
    complainant_name: str,
    complainant_email: str,
    portal_name: Optional[str] = None,
    legal_citations: Optional[List[str]] = None,
    relief_sought: Optional[str] = None,
    evidence_paths: Optional[List[str]] = None,
    recipient: Optional[str] = None,
    subject: Optional[str] = None,
) -> SubmissionResult:
    """
    Submit a complaint through all available channels.
    Returns an aggregated SubmissionResult with details per channel.
    """
    target: SubmissionTarget = resolve_submission_target(state, complaint_type)
    now = datetime.now(timezone.utc)

    email_subject = subject or (
        f"[Grievance] Traffic {complaint_type.replace('_', ' ').title()} "
        f"Complaint - {target.state_name} - {now.strftime('%d/%m/%Y')}"
    )

    result = SubmissionResult(
        success=False,
        state_name=target.state_name,
        portal_name=target.portal.name,
        portal_url=target.portal.url,
        complaint_form_url=target.portal.complaint_form_url,
        helplines=target.helplines,
        submitted_at=now.isoformat(),
        email_recipients=target.emails + target.cc_emails,
    )

    # -- Channel 1: Email submission (most reliable) --
    result.channels_attempted.append("email")
    try:
        email_result: EmailResult = await send_complaint_email(
            to_emails=target.emails,
            cc_emails=target.cc_emails,
            subject=email_subject,
            complainant_name=complainant_name,
            complainant_email=complainant_email,
            complaint_type=complaint_type,
            state_name=target.state_name,
            complaint_text=complaint_text,
            legal_citations=legal_citations,
            attachment_paths=evidence_paths,
        )
        result.email_sent = email_result.success
        result.email_recipients = email_result.recipients
        result.email_error = email_result.error
        if email_result.success:
            result.channels_succeeded.append("email")
    except Exception as e:
        logger.error(f"Email channel failed: {e}")
        result.email_error = str(e)

    # -- Channel 2: PDF generation --
    result.channels_attempted.append("pdf")
    try:
        pdf_path = generate_complaint_pdf(
            complaint_id=complaint_id,
            complainant_name=complainant_name,
            complainant_email=complainant_email,
            complaint_type=complaint_type,
            state_name=target.state_name,
            portal_name=target.portal.name,
            complaint_text=complaint_text,
            recipient=recipient,
            subject=email_subject,
            legal_citations=legal_citations,
            relief_sought=relief_sought,
            emails_sent_to=target.emails if result.email_sent else None,
            portal_url=target.portal.url,
        )
        if pdf_path:
            result.pdf_generated = True
            result.pdf_path = pdf_path
            result.channels_succeeded.append("pdf")
    except Exception as e:
        logger.error(f"PDF channel failed: {e}")

    # -- Channel 3: Playwright portal automation (best-effort, non-blocking) --
    result.channels_attempted.append("portal_automation")
    try:
        portal_result = await asyncio.wait_for(
            submit_to_portal(
                portal_type=target.portal.portal_type,
                portal_url=target.portal.url,
                complaint_data={
                    "name": complainant_name,
                    "email": complainant_email,
                    "subject": email_subject,
                    "body": complaint_text,
                    "category": f"Traffic / {complaint_type.title()}",
                },
            ),
            timeout=45.0,
        )
        result.portal_automation_status = portal_result.get("status", "unknown")
        result.portal_screenshot_path = portal_result.get("screenshot_path")
        result.portal_complaint_id = portal_result.get("portal_complaint_id")
        if portal_result.get("complaint_form_url"):
            result.complaint_form_url = portal_result["complaint_form_url"]
        if portal_result.get("status") in ("portal_opened", "submitted"):
            result.channels_succeeded.append("portal_automation")
    except asyncio.TimeoutError:
        logger.warning("Portal automation timed out after 45s")
        result.portal_automation_status = "timeout"
    except Exception as e:
        logger.error(f"Portal automation channel failed: {e}")
        result.portal_automation_status = "error"

    # Success if at least one channel worked, or we have portal/email info for user
    result.success = len(result.channels_succeeded) > 0 or len(result.email_recipients) > 0

    logger.info(
        f"Complaint {complaint_id} submission: "
        f"channels={result.channels_succeeded}/{result.channels_attempted}, "
        f"state={target.state_name}"
    )

    return result
