import json
import uuid
from typing import List, Any
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.complaint import Complaint, ComplaintAction, ComplaintStatus
from app.models.case import Case
from app.schemas.complaint import (
    ComplaintDraftRequest,
    ComplaintEditRequest,
    ComplaintSubmitRequest,
    ComplaintResponse,
    ComplaintDetailResponse,
    ComplaintActionResponse,
)
from app.core.exceptions import NotFoundException, ValidationException
from app.agents.orchestrator import run_orchestrator
from app.services.portal_submission import submit_complaint_to_authorities
from app.schemas.complaint import SubmissionDetails
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


def _extract_body(response: Any) -> str:
    """Robustly extract the complaint body from the agent response,
    whether it arrives as a dict, a JSON string, or plain text."""
    if isinstance(response, str):
        try:
            response = json.loads(response)
        except (json.JSONDecodeError, TypeError):
            return response

    if isinstance(response, dict):
        if "body" in response:
            return response["body"]
        if "answer" in response:
            return response["answer"]
        cleaned = {k: v for k, v in response.items() if k != "disclaimer"}
        return json.dumps(cleaned, ensure_ascii=False, indent=2)

    return str(response)


async def _get_owned_complaint(
    complaint_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession
) -> Complaint:
    result = await db.execute(
        select(Complaint)
        .join(Complaint.case)
        .where(Complaint.id == complaint_id, Case.user_id == user_id)
    )
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise NotFoundException("Complaint")
    return complaint


@router.post("/draft", response_model=ComplaintResponse, status_code=201)
async def draft_complaint(
    data: ComplaintDraftRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a complaint draft using the AI agent."""
    from app.models.case import CaseType, CaseStatus

    if data.case_id:
        result = await db.execute(
            select(Case).where(Case.id == data.case_id, Case.user_id == current_user.id)
        )
        case = result.scalar_one_or_none()
        if not case:
            raise NotFoundException("Case")
    else:
        type_map = {
            "misconduct": CaseType.MISCONDUCT,
            "overcharge": CaseType.CHALLAN,
            "general": CaseType.TRAFFIC_STOP,
        }
        case = Case(
            user_id=current_user.id,
            case_type=type_map.get(data.complaint_type, CaseType.MISCONDUCT),
            status=CaseStatus.OPEN,
            title=data.description or f"Complaint: {data.complaint_type}",
        )
        db.add(case)
        await db.flush()

    agent_result = await run_orchestrator(
        query=f"Draft a {data.complaint_type} complaint for case: {case.title}",
        user_id=str(current_user.id),
        state=case.state or "central",
        intent="complaint_draft",
        language=data.language,
        case_details=f"Type: {case.case_type.value}, Title: {case.title}, "
                     f"Description: {case.description or 'N/A'}, "
                     f"Location: {case.location or 'N/A'}",
        evidence_summary="See attached evidence",
    )

    response = agent_result.get("response", {})
    draft_text = _extract_body(response)

    complaint = Complaint(
        case_id=case.id,
        complaint_type=data.complaint_type,
        draft_text=draft_text,
        status=ComplaintStatus.DRAFTED,
    )
    db.add(complaint)
    await db.flush()

    action = ComplaintAction(
        complaint_id=complaint.id,
        action_type="draft_generated",
        details={"agent_response": response},
    )
    db.add(action)
    await db.flush()

    await db.refresh(complaint)
    return ComplaintResponse.model_validate(complaint)


@router.put("/{complaint_id}", response_model=ComplaintResponse)
async def edit_complaint(
    complaint_id: uuid.UUID,
    data: ComplaintEditRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Edit the complaint text before submission."""
    complaint = await _get_owned_complaint(complaint_id, current_user.id, db)

    complaint.final_text = data.final_text

    action = ComplaintAction(
        complaint_id=complaint.id,
        action_type="text_edited",
        details={"edited_by": str(current_user.id)},
    )
    db.add(action)

    await db.flush()
    await db.refresh(complaint)
    return ComplaintResponse.model_validate(complaint)


@router.post("/{complaint_id}/submit", response_model=ComplaintResponse)
async def submit_complaint(
    complaint_id: uuid.UUID,
    data: ComplaintSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit complaint to grievance portal via email + portal automation."""
    if not data.user_consent:
        raise ValidationException("User consent is required for complaint submission")

    complaint = await _get_owned_complaint(complaint_id, current_user.id, db)

    if complaint.status != ComplaintStatus.DRAFTED:
        raise ValidationException("Only drafted complaints can be submitted")

    # Resolve the case state for portal routing
    case_result = await db.execute(select(Case).where(Case.id == complaint.case_id))
    case = case_result.scalar_one_or_none()
    case_state = (case.state if case and case.state else None) or current_user.state or "central"

    complaint_text = complaint.final_text or complaint.draft_text or ""

    # Extract structured fields from the original agent response if stored
    legal_citations = None
    relief_sought = None
    recipient = None
    subject = None
    draft_action = await db.execute(
        select(ComplaintAction)
        .where(
            ComplaintAction.complaint_id == complaint.id,
            ComplaintAction.action_type == "draft_generated",
        )
        .limit(1)
    )
    action_row = draft_action.scalar_one_or_none()
    if action_row and isinstance(action_row.details, dict):
        agent_resp = action_row.details.get("agent_response", {})
        if isinstance(agent_resp, dict):
            legal_citations = agent_resp.get("legal_citations")
            relief_sought = agent_resp.get("relief_sought")
            recipient = agent_resp.get("recipient")
            subject = agent_resp.get("subject")

    # Real multi-channel submission
    submission_result = await submit_complaint_to_authorities(
        complaint_id=str(complaint.id),
        complaint_text=complaint_text,
        complaint_type=complaint.complaint_type,
        state=case_state,
        complainant_name=current_user.full_name or current_user.email,
        complainant_email=current_user.email,
        portal_name=data.portal_name,
        legal_citations=legal_citations,
        relief_sought=relief_sought,
        recipient=recipient,
        subject=subject,
    )

    # Update complaint record
    complaint.user_consent = True
    complaint.portal_name = submission_result.portal_name
    complaint.portal_url = submission_result.portal_url
    complaint.status = ComplaintStatus.SUBMITTED
    complaint.submitted_at = datetime.now(timezone.utc)

    if submission_result.portal_complaint_id:
        complaint.portal_complaint_id = submission_result.portal_complaint_id
    if submission_result.portal_screenshot_path:
        complaint.submission_screenshot_path = submission_result.portal_screenshot_path

    action = ComplaintAction(
        complaint_id=complaint.id,
        action_type="submitted",
        details={
            "portal": submission_result.portal_name,
            "portal_url": submission_result.portal_url,
            "consent_given": True,
            "submitted_by": str(current_user.id),
            "email_sent": submission_result.email_sent,
            "email_recipients": submission_result.email_recipients,
            "pdf_generated": submission_result.pdf_generated,
            "pdf_path": submission_result.pdf_path,
            "portal_automation_status": submission_result.portal_automation_status,
            "channels_attempted": submission_result.channels_attempted,
            "channels_succeeded": submission_result.channels_succeeded,
            "complaint_form_url": submission_result.complaint_form_url,
        },
    )
    db.add(action)

    await db.flush()
    await db.refresh(complaint)

    logger.info(
        f"Complaint {complaint.id} submitted: "
        f"channels={submission_result.channels_succeeded}"
    )

    resp = ComplaintResponse.model_validate(complaint)
    resp.submission_details = SubmissionDetails(
        state_name=submission_result.state_name,
        portal_name=submission_result.portal_name,
        portal_url=submission_result.portal_url,
        complaint_form_url=submission_result.complaint_form_url,
        email_sent=submission_result.email_sent,
        email_recipients=submission_result.email_recipients,
        email_error=submission_result.email_error,
        pdf_generated=submission_result.pdf_generated,
        pdf_path=submission_result.pdf_path,
        portal_automation_status=submission_result.portal_automation_status,
        portal_screenshot_path=submission_result.portal_screenshot_path,
        helplines=submission_result.helplines,
        channels_attempted=submission_result.channels_attempted,
        channels_succeeded=submission_result.channels_succeeded,
        submitted_at=submission_result.submitted_at,
    )
    return resp


@router.get("/portal-info/{state}")
async def get_portal_info(state: str):
    """Return the recommended portal and email targets for a given state."""
    from app.services.portal_registry import (
        resolve_submission_target,
        get_supported_portals_for_state,
        get_helplines_for_state,
    )
    target = resolve_submission_target(state)
    portals = get_supported_portals_for_state(state)
    helplines = get_helplines_for_state(state)
    return {
        "state_name": target.state_name,
        "state_code": target.state_code,
        "recommended_portal": {
            "name": target.portal.name,
            "url": target.portal.url,
            "type": target.portal.portal_type,
        },
        "emails": target.emails,
        "cc_emails": target.cc_emails,
        "all_portals": portals,
        "helplines": helplines,
    }


@router.get("/{complaint_id}/download-pdf")
async def download_complaint_pdf(
    complaint_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download the generated complaint PDF."""
    import os

    complaint = await _get_owned_complaint(complaint_id, current_user.id, db)

    # Check for PDF path in the submission action
    action_result = await db.execute(
        select(ComplaintAction)
        .where(
            ComplaintAction.complaint_id == complaint.id,
            ComplaintAction.action_type == "submitted",
        )
        .order_by(ComplaintAction.performed_at.desc())
        .limit(1)
    )
    action = action_result.scalar_one_or_none()

    pdf_path = None
    if action and isinstance(action.details, dict):
        pdf_path = action.details.get("pdf_path")

    if not pdf_path or not os.path.isfile(pdf_path):
        raise NotFoundException("PDF file not found. The complaint may not have been submitted yet.")

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=os.path.basename(pdf_path),
    )


@router.get("/{complaint_id}", response_model=ComplaintDetailResponse)
async def get_complaint(
    complaint_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get complaint details with action history."""
    complaint = await _get_owned_complaint(complaint_id, current_user.id, db)
    return ComplaintDetailResponse.model_validate(complaint)


@router.get("/{complaint_id}/actions", response_model=List[ComplaintActionResponse])
async def get_complaint_actions(
    complaint_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the audit trail for a complaint."""
    await _get_owned_complaint(complaint_id, current_user.id, db)
    result = await db.execute(
        select(ComplaintAction)
        .where(ComplaintAction.complaint_id == complaint_id)
        .order_by(ComplaintAction.performed_at.asc())
    )
    return result.scalars().all()


@router.post("/{complaint_id}/escalate", response_model=ComplaintResponse)
async def escalate_complaint(
    complaint_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually escalate a complaint."""
    complaint = await _get_owned_complaint(complaint_id, current_user.id, db)

    complaint.status = ComplaintStatus.ESCALATED

    action = ComplaintAction(
        complaint_id=complaint.id,
        action_type="escalated",
        details={"escalated_by": str(current_user.id), "reason": "manual_escalation"},
    )
    db.add(action)

    await db.flush()
    await db.refresh(complaint)

    logger.info(f"Complaint {complaint.id} escalated")
    return ComplaintResponse.model_validate(complaint)
