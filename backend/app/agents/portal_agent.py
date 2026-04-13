"""
Portal Agent: Automates complaint submission to grievance portals.
Uses the state portal registry for smart routing.
"""
from typing import Dict, Any

from app.agents.state import TrafficJusticeState
from app.services.portal_registry import resolve_submission_target
from app.core.logging import get_logger

logger = get_logger(__name__)


def portal_agent_node(state: TrafficJusticeState) -> Dict[str, Any]:
    """LangGraph node for the Portal Agent."""
    complaint_draft = state.get("complaint_draft", {})
    if not complaint_draft:
        return {
            "portal_result": {"error": "No complaint draft available for submission"},
            "response": {"error": "No complaint draft to submit"},
            "messages": ["portal_agent: no complaint draft available"],
        }

    user_state = state.get("state", "central")
    complaint_type = "general"
    if isinstance(complaint_draft, dict):
        complaint_type = complaint_draft.get("complaint_type", "general")

    target = resolve_submission_target(user_state, complaint_type)

    complaint_data = {
        "name": "Complainant",
        "subject": complaint_draft.get("subject", "Traffic Grievance")
        if isinstance(complaint_draft, dict) else "Traffic Grievance",
        "body": complaint_draft.get("body", "")
        if isinstance(complaint_draft, dict) else str(complaint_draft),
        "category": "Traffic / Transport",
    }

    logger.info(f"Portal agent routing to {target.portal.name} for state={user_state}")

    result = {
        "status": "prepared",
        "portal_name": target.portal.name,
        "portal_url": target.portal.url,
        "state_name": target.state_name,
        "emails": target.emails,
        "complaint_data": complaint_data,
        "complaint_form_url": target.portal.complaint_form_url,
        "helplines": target.helplines,
        "message": (
            f"Complaint prepared for submission to {target.portal.name} "
            f"({target.state_name}). Emails will be sent to: {', '.join(target.emails)}. "
            f"User consent is required before actual submission."
        ),
    }

    return {
        "portal_result": result,
        "response": result,
        "messages": [f"portal_agent: prepared submission for {target.portal.name} ({target.state_name})"],
    }
