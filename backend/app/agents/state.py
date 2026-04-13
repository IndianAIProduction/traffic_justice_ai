"""
Shared state definition for the LangGraph multi-agent orchestrator.
Uses LangGraph's native message handling for checkpointer-based memory.
"""
from typing import TypedDict, Optional, List, Dict, Any, Annotated, Sequence
from operator import add

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class TrafficJusticeState(TypedDict, total=False):
    # Input
    user_id: str
    query: str
    intent: str
    state: str  # Indian state
    city: Optional[str]  # User's city for location-aware responses
    language: Optional[str]  # Response language code (en, hi, mr, ta, etc.)
    language_explicit: Optional[bool]  # True if user explicitly chose language from dropdown
    vehicle_type: Optional[str]  # two_wheeler, four_wheeler, or heavy
    case_id: Optional[str]

    # LangGraph-native chat memory (persisted by checkpointer)
    chat_messages: Annotated[Sequence[BaseMessage], add_messages]

    # Challan data (when applicable)
    challan_sections: Optional[List[Dict[str, Any]]]
    challan_state: Optional[str]

    # Evidence data (when applicable)
    evidence_id: Optional[str]
    transcription: Optional[str]

    # Complaint data (when applicable)
    complaint_id: Optional[str]
    case_details: Optional[str]
    evidence_summary: Optional[str]

    # Agent outputs
    legal_response: Optional[Dict[str, Any]]
    challan_result: Optional[Dict[str, Any]]
    evidence_analysis: Optional[Dict[str, Any]]
    complaint_draft: Optional[Dict[str, Any]]
    portal_result: Optional[Dict[str, Any]]
    tracker_result: Optional[Dict[str, Any]]

    # Final output
    response: Optional[Dict[str, Any]]
    error: Optional[str]

    # Audit trail (internal orchestrator messages)
    messages: Annotated[List[str], add]
