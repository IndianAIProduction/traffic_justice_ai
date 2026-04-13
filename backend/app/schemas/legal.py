from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid


class LegalQueryRequest(BaseModel):
    query: str = Field(min_length=5, max_length=2000)
    state: str = Field(default="central", description="Indian state for context")
    city: Optional[str] = Field(default=None, description="User's city for location-aware responses")
    language: str = Field(default="en", description="Response language code (en, hi, mr, ta, te, kn, ml, etc.)")
    language_explicit: bool = Field(default=False, description="True if user explicitly chose the language from dropdown")
    vehicle_type: Optional[str] = Field(default=None, description="Vehicle type: two_wheeler, four_wheeler, or heavy")
    case_id: Optional[uuid.UUID] = None
    thread_id: Optional[str] = Field(default=None, description="Chat thread ID for conversation memory")


class LegalQueryResponse(BaseModel):
    id: uuid.UUID
    query: str
    response: Dict[str, Any]
    intent: str
    audit_trail: List[str]
    thread_id: str = Field(description="Thread ID for continuing this conversation")

    model_config = {"from_attributes": True}
