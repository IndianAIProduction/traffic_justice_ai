"""
Tools available to the Challan Agent for fine validation.
"""
from typing import List, Dict
from langchain_core.tools import tool

from app.services.challan_service import validate_fines, load_fine_schedule


@tool
def validate_challan_fines(
    sections_with_fines: List[Dict[str, float]],
    state: str,
) -> Dict:
    """Validate challan fines against the official fine schedule.

    Args:
        sections_with_fines: List of dicts with 'section' and 'amount' keys.
        state: Indian state where the challan was issued.
    """
    result = validate_fines(sections_with_fines, state)
    return result.model_dump()


@tool
def get_fine_schedule(state: str) -> Dict:
    """Get the official fine schedule for a given Indian state.

    Args:
        state: Indian state name (e.g., 'Maharashtra', 'Karnataka').
    """
    schedule = load_fine_schedule(state)
    return schedule
