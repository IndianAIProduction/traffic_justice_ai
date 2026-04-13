"""
Challan Agent: Validates traffic challans against official fine schedules.
"""
from typing import Dict, Any

from app.services.challan_service import validate_fines
from app.agents.state import TrafficJusticeState
from app.core.logging import get_logger

logger = get_logger(__name__)


def challan_agent_node(state: TrafficJusticeState) -> Dict[str, Any]:
    """LangGraph node for the Challan Agent."""
    sections = state.get("challan_sections", [])
    challan_state = state.get("challan_state") or state.get("state", "central")

    if not sections:
        return {
            "challan_result": {"error": "No challan sections provided"},
            "response": {"error": "No challan sections provided for validation"},
            "messages": ["challan_agent: no sections provided"],
        }

    result = validate_fines(sections, challan_state)
    result_dict = result.model_dump()

    logger.info(
        f"Challan agent validated {len(sections)} sections, "
        f"overcharge={'YES' if result.has_overcharge else 'NO'}"
    )

    return {
        "challan_result": result_dict,
        "response": result_dict,
        "messages": [
            f"challan_agent: validated {len(sections)} sections for {challan_state}, "
            f"overcharge={result.has_overcharge}"
        ],
    }
