from pydantic import BaseModel, Field
from typing import Optional, List
import uuid
from datetime import datetime


class CaseCreateRequest(BaseModel):
    case_type: str = Field(description="traffic_stop, challan, or misconduct")
    title: str = Field(min_length=1, max_length=500)
    description: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    location: Optional[str] = None


class CaseUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None


class CaseResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    case_type: str
    status: str
    title: str
    description: Optional[str]
    state: Optional[str]
    city: Optional[str]
    location: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChallanSummary(BaseModel):
    id: uuid.UUID
    challan_number: Optional[str] = None
    is_valid: Optional[bool] = None
    has_overcharge: bool = False
    total_fine_charged: Optional[float] = None

    model_config = {"from_attributes": True}


class EvidenceSummary(BaseModel):
    id: uuid.UUID
    file_type: str
    file_name: str
    is_analyzed: bool = False
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class ComplaintSummary(BaseModel):
    id: uuid.UUID
    complaint_type: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CaseDetailResponse(CaseResponse):
    challans: List[ChallanSummary] = []
    evidence_items: List[EvidenceSummary] = []
    complaints: List[ComplaintSummary] = []
