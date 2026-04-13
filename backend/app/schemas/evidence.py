from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime


class EvidenceUploadResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    file_type: str
    file_name: str
    file_hash: str
    is_analyzed: bool
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class MisconductFlagResponse(BaseModel):
    id: uuid.UUID
    flag_type: str
    severity: int
    description: str
    timestamp_in_media: Optional[str]
    confidence_score: Optional[float]
    raw_quote: Optional[str]

    model_config = {"from_attributes": True}


class EvidenceDetailResponse(EvidenceUploadResponse):
    transcription: Optional[str]
    analysis: Dict[str, Any]
    misconduct_flags: List[MisconductFlagResponse] = []
