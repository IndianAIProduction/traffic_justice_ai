from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime


class SectionFine(BaseModel):
    section: str
    amount: float


class ScheduleSectionItem(BaseModel):
    """One MV Act section row from the loaded fine schedule for a state."""

    section: str
    offense: str
    max_fine: float


class ChallanValidateRequest(BaseModel):
    case_id: Optional[uuid.UUID] = None
    challan_number: Optional[str] = None
    sections: List[SectionFine]
    state: str = Field(description="Indian state where challan was issued")
    issuing_officer: Optional[str] = None
    officer_badge_number: Optional[str] = None
    location: Optional[str] = None
    issued_at: Optional[datetime] = None
    raw_text: Optional[str] = None


class SectionAnalysis(BaseModel):
    section: str
    offense: str
    charged_amount: float
    valid_range: Dict[str, Optional[float]]
    is_overcharged: bool
    note: str


class ChallanValidationResult(BaseModel):
    is_valid: bool
    has_overcharge: bool
    section_analysis: List[SectionAnalysis]
    total_valid_fine: float
    total_charged: float
    overcharge_amount: float
    recommended_action: str


class ChallanResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    challan_number: Optional[str]
    sections: Dict[str, Any]
    fines: Dict[str, Any]
    total_fine_charged: Optional[float]
    total_fine_valid: Optional[float]
    is_valid: Optional[bool]
    has_overcharge: Optional[bool]
    validation_result: Dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}
