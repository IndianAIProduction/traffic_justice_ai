from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime


class ComplaintDraftRequest(BaseModel):
    case_id: Optional[uuid.UUID] = None
    complaint_type: str = Field(description="misconduct, overcharge, or general")
    description: Optional[str] = Field(None, description="Brief description for auto-created cases")
    language: str = Field(default="en", description="Response language code")


class ComplaintEditRequest(BaseModel):
    final_text: str


class ComplaintSubmitRequest(BaseModel):
    user_consent: bool = Field(description="Must be true to submit")
    portal_name: Optional[str] = "pgportal"


class ComplaintActionResponse(BaseModel):
    id: uuid.UUID
    action_type: str
    details: Dict[str, Any]
    performed_at: datetime

    model_config = {"from_attributes": True}


class SubmissionDetails(BaseModel):
    """Details of multi-channel complaint submission."""
    state_name: str = ""
    portal_name: str = ""
    portal_url: str = ""
    complaint_form_url: Optional[str] = None

    email_sent: bool = False
    email_recipients: List[str] = []
    email_error: Optional[str] = None

    pdf_generated: bool = False
    pdf_path: Optional[str] = None

    portal_automation_status: str = "skipped"
    portal_screenshot_path: Optional[str] = None

    helplines: Dict[str, str] = {}
    channels_attempted: List[str] = []
    channels_succeeded: List[str] = []
    submitted_at: Optional[str] = None


class ComplaintResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    complaint_type: str
    portal_name: Optional[str]
    status: str
    draft_text: Optional[str]
    final_text: Optional[str]
    portal_complaint_id: Optional[str]
    portal_url: Optional[str] = None
    submission_screenshot_path: Optional[str] = None
    user_consent: bool
    submitted_at: Optional[datetime]
    resolved_at: Optional[datetime]
    created_at: datetime
    submission_details: Optional[SubmissionDetails] = None

    model_config = {"from_attributes": True}


class ComplaintDetailResponse(ComplaintResponse):
    actions: List[ComplaintActionResponse] = []
