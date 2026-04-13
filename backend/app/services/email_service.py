"""
Email Service: Sends formal complaint emails to government authorities.
Supports attachments (evidence files, PDF complaint document).
"""
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict
from dataclasses import dataclass
from datetime import datetime, timezone

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

try:
    import aiosmtplib
    HAS_AIOSMTPLIB = True
except ImportError:
    HAS_AIOSMTPLIB = False
    logger.warning("aiosmtplib not installed. Email submission disabled. Run: pip install aiosmtplib")


@dataclass
class EmailResult:
    success: bool
    recipients: List[str]
    message_id: Optional[str] = None
    error: Optional[str] = None


def _build_complaint_email_body(
    complainant_name: str,
    complainant_email: str,
    complaint_type: str,
    state_name: str,
    complaint_text: str,
    legal_citations: Optional[List[str]] = None,
    evidence_summary: Optional[str] = None,
) -> str:
    """Build a formal government complaint email body in text format."""
    date_str = datetime.now(timezone.utc).strftime("%d %B %Y")

    body = f"""Subject: Formal Grievance - Traffic {complaint_type.replace('_', ' ').title()} Complaint

Date: {date_str}

To,
The Competent Authority,
{state_name} Grievance Redressal Department

Respected Sir/Madam,

{complaint_text}

"""
    if legal_citations:
        body += "Relevant Legal Provisions:\n"
        for citation in legal_citations:
            body += f"  - {citation}\n"
        body += "\n"

    if evidence_summary:
        body += f"Supporting Evidence:\n{evidence_summary}\n\n"

    body += f"""I request that this complaint be registered and appropriate action be taken at the earliest.

Yours faithfully,
{complainant_name}
Email: {complainant_email}

---
This complaint was generated and submitted via Traffic Justice AI platform.
For verification, please contact: {complainant_email}
"""
    return body


async def send_complaint_email(
    to_emails: List[str],
    cc_emails: Optional[List[str]],
    subject: str,
    complainant_name: str,
    complainant_email: str,
    complaint_type: str,
    state_name: str,
    complaint_text: str,
    legal_citations: Optional[List[str]] = None,
    evidence_summary: Optional[str] = None,
    attachment_paths: Optional[List[str]] = None,
) -> EmailResult:
    """Send the complaint email to government authority addresses."""

    if not HAS_AIOSMTPLIB:
        return EmailResult(
            success=False,
            recipients=to_emails,
            error="aiosmtplib not installed. Run: pip install aiosmtplib",
        )

    if not settings.smtp_user or not settings.smtp_password:
        logger.warning("SMTP not configured; skipping email submission")
        return EmailResult(
            success=False,
            recipients=to_emails,
            error="SMTP credentials not configured. Set SMTP_USER and SMTP_PASSWORD in .env",
        )

    body_text = _build_complaint_email_body(
        complainant_name=complainant_name,
        complainant_email=complainant_email,
        complaint_type=complaint_type,
        state_name=state_name,
        complaint_text=complaint_text,
        legal_citations=legal_citations,
        evidence_summary=evidence_summary,
    )

    msg = MIMEMultipart()
    msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email or settings.smtp_user}>"
    msg["To"] = ", ".join(to_emails)
    if cc_emails:
        msg["Cc"] = ", ".join(cc_emails)
    msg["Subject"] = subject
    msg["Reply-To"] = complainant_email

    msg.attach(MIMEText(body_text, "plain", "utf-8"))

    if attachment_paths:
        for filepath in attachment_paths:
            if not os.path.isfile(filepath):
                logger.warning(f"Attachment not found, skipping: {filepath}")
                continue
            try:
                with open(filepath, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={os.path.basename(filepath)}",
                )
                msg.attach(part)
            except Exception as e:
                logger.warning(f"Failed to attach {filepath}: {e}")

    all_recipients = list(to_emails)
    if cc_emails:
        all_recipients.extend(cc_emails)

    try:
        smtp_kwargs: Dict = {
            "hostname": settings.smtp_host,
            "port": settings.smtp_port,
            "username": settings.smtp_user,
            "password": settings.smtp_password,
        }
        if settings.smtp_use_tls:
            smtp_kwargs["start_tls"] = True

        await aiosmtplib.send(msg, **smtp_kwargs)

        logger.info(f"Complaint email sent to {all_recipients}")
        return EmailResult(
            success=True,
            recipients=all_recipients,
            message_id=msg.get("Message-ID"),
        )
    except Exception as e:
        logger.error(f"Failed to send complaint email: {e}")
        return EmailResult(
            success=False,
            recipients=all_recipients,
            error=str(e),
        )
