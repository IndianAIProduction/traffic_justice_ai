"""
Challan validation service.
Compares challan fines against official state/central fine schedules.
"""
import json
import os
from typing import Dict, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.challan import Challan
from app.models.case import Case, CaseType, CaseStatus
from app.schemas.challan import (
    ChallanValidateRequest,
    ChallanValidationResult,
    SectionAnalysis,
)
from app.core.logging import get_logger
from app.core.exceptions import NotFoundException, ForbiddenException

logger = get_logger(__name__)

FINE_SCHEDULES_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "fine_schedules"
)

_schedule_cache: Dict[str, Dict] = {}

STATE_NAME_ALIASES: Dict[str, str] = {
    "ap": "andhra_pradesh", "andhra": "andhra_pradesh", "andhra pradesh": "andhra_pradesh",
    "ar": "arunachal_pradesh", "arunachal": "arunachal_pradesh", "arunachal pradesh": "arunachal_pradesh",
    "as": "assam",
    "br": "bihar",
    "cg": "chhattisgarh",
    "ch": "chandigarh",
    "dl": "delhi", "new delhi": "delhi",
    "ga": "goa",
    "gj": "gujarat",
    "hp": "himachal_pradesh", "himachal": "himachal_pradesh", "himachal pradesh": "himachal_pradesh",
    "hr": "haryana",
    "jh": "jharkhand",
    "jk": "jammu_kashmir", "j&k": "jammu_kashmir", "jammu": "jammu_kashmir",
    "jammu and kashmir": "jammu_kashmir", "jammu & kashmir": "jammu_kashmir",
    "ka": "karnataka",
    "kl": "kerala",
    "la": "central",  # Ladakh falls back to central
    "mh": "maharashtra",
    "ml": "meghalaya",
    "mn": "manipur",
    "mp": "madhya_pradesh", "madhya": "madhya_pradesh", "madhya pradesh": "madhya_pradesh",
    "mz": "mizoram",
    "nl": "nagaland",
    "od": "odisha", "orissa": "odisha",
    "pb": "punjab",
    "py": "puducherry", "pondicherry": "puducherry",
    "rj": "rajasthan",
    "sk": "sikkim",
    "tn": "tamil_nadu", "tamil": "tamil_nadu", "tamil nadu": "tamil_nadu", "tamilnadu": "tamil_nadu",
    "tr": "tripura",
    "ts": "telangana",
    "uk": "uttarakhand",
    "up": "uttar_pradesh", "uttar": "uttar_pradesh", "uttar pradesh": "uttar_pradesh",
    "wb": "west_bengal", "west bengal": "west_bengal", "bengal": "west_bengal",
}


def _normalize_state_key(state: str) -> str:
    """Normalize user-provided state name to a file-system key."""
    key = state.lower().strip()
    if key in STATE_NAME_ALIASES:
        return STATE_NAME_ALIASES[key]
    return key.replace(" ", "_")


def load_fine_schedule(state: str) -> Dict:
    state_key = _normalize_state_key(state)
    if state_key in _schedule_cache:
        return _schedule_cache[state_key]

    filepath = os.path.join(FINE_SCHEDULES_DIR, f"{state_key}.json")
    if not os.path.exists(filepath):
        logger.warning(f"No fine schedule found for '{state}' (resolved: {state_key}), falling back to central")
        filepath = os.path.join(FINE_SCHEDULES_DIR, "central.json")

    with open(filepath, "r", encoding="utf-8") as f:
        schedule = json.load(f)

    _schedule_cache[state_key] = schedule
    return schedule


def get_available_states() -> List[Dict[str, str]]:
    """Return list of all available states with their fine schedules."""
    index_path = os.path.join(FINE_SCHEDULES_DIR, "states_index.json")
    if not os.path.exists(index_path):
        return []
    with open(index_path, "r", encoding="utf-8") as f:
        index = json.load(f)

    result = []
    for entry in index.get("states", []) + index.get("union_territories", []):
        result.append({
            "name": entry["name"],
            "code": entry["code"],
            "confidence": entry.get("confidence", "unknown"),
            "has_reductions": entry.get("has_reductions", False),
        })
    return result


def get_schedule_sections(state: str) -> List[Dict]:
    """Return all section codes and offenses from the fine schedule for the given state."""
    schedule = load_fine_schedule(state)
    raw = schedule.get("sections") or {}
    items: List[Dict] = []
    for code, info in raw.items():
        first = float(info.get("first_offense") or 0)
        repeat = info.get("repeat")
        if repeat is not None:
            max_fine = max(first, float(repeat))
        else:
            max_fine = first
        items.append({
            "section": str(code),
            "offense": str(info.get("offense") or ""),
            "max_fine": max_fine,
        })
    items.sort(key=lambda x: x["section"].lower())
    return items


def validate_fines(
    sections_with_fines: List[Dict[str, float]],
    state: str,
) -> ChallanValidationResult:
    schedule = load_fine_schedule(state)
    schedule_sections = schedule.get("sections", {})

    analyses = []
    total_charged = 0.0
    total_valid = 0.0
    has_overcharge = False
    has_unknown = False

    for item in sections_with_fines:
        section = str(item["section"]).strip()
        charged = float(item["amount"])
        total_charged += charged

        section_key = section.replace("Section ", "").replace("Sec ", "").strip()

        if section_key in schedule_sections:
            info = schedule_sections[section_key]
            first = info.get("first_offense", 0) or 0
            repeat = info.get("repeat") or first

            max_fine = max(first, repeat) if repeat else first
            is_over = charged > max_fine

            if is_over:
                has_overcharge = True
                valid_amount = max_fine
            else:
                valid_amount = charged

            total_valid += valid_amount

            analyses.append(SectionAnalysis(
                section=section_key,
                offense=info.get("offense", "Unknown"),
                charged_amount=charged,
                valid_range={"min": first, "max": max_fine},
                is_overcharged=is_over,
                note=(
                    f"Overcharged by Rs {charged - max_fine:.0f}! Official max is Rs {max_fine:.0f}" if is_over
                    else "Fine is within valid range"
                ),
            ))
        else:
            has_unknown = True
            analyses.append(SectionAnalysis(
                section=section_key,
                offense="Unknown section — not found in official schedule",
                charged_amount=charged,
                valid_range={"min": None, "max": None},
                is_overcharged=False,
                note=(
                    f"Section '{section_key}' is not in our database. "
                    "This may be an invalid section number. "
                    "Please verify with the official Motor Vehicles Act."
                ),
            ))

    overcharge_amount = max(0, total_charged - total_valid)

    if has_overcharge:
        action = (
            f"Overcharge of Rs {overcharge_amount:.0f} detected! "
            "Do NOT pay the excess. Ask for an official receipt with the correct amount. "
            "You can file a complaint with the traffic police authority."
        )
    elif has_unknown:
        action = (
            "Some sections could not be verified against official records. "
            "Please double-check the section numbers on your challan and try again with correct section numbers "
            "(e.g. 177, 184, 194A, 194E)."
        )
    else:
        action = (
            "All fines are within the official range. "
            "Pay through official channels and always collect a receipt."
        )

    return ChallanValidationResult(
        is_valid=not has_overcharge and not has_unknown,
        has_overcharge=has_overcharge,
        section_analysis=analyses,
        total_valid_fine=total_valid,
        total_charged=total_charged,
        overcharge_amount=overcharge_amount,
        recommended_action=action,
    )


async def create_and_validate_challan(
    data: ChallanValidateRequest,
    user_id,
    db: AsyncSession,
) -> Challan:
    if data.case_id:
        result = await db.execute(select(Case).where(Case.id == data.case_id))
        case = result.scalar_one_or_none()
        if not case:
            raise NotFoundException("Case")
        if case.user_id != user_id:
            raise ForbiddenException("You do not own this case")
    else:
        case = Case(
            user_id=user_id,
            case_type=CaseType.CHALLAN,
            status=CaseStatus.OPEN,
            title=f"Challan {data.challan_number or 'Validation'}",
            state=data.state,
            location=data.location,
        )
        db.add(case)
        await db.flush()

    sections_with_fines = [
        {"section": sf.section, "amount": sf.amount} for sf in data.sections
    ]
    validation = validate_fines(sections_with_fines, data.state)

    challan = Challan(
        case_id=case.id,
        challan_number=data.challan_number,
        sections={sf.section: sf.amount for sf in data.sections},
        fines={a.section: a.charged_amount for a in validation.section_analysis},
        total_fine_charged=validation.total_charged,
        total_fine_valid=validation.total_valid_fine,
        issuing_officer=data.issuing_officer,
        officer_badge_number=data.officer_badge_number,
        location=data.location,
        issued_at=data.issued_at,
        is_valid=validation.is_valid,
        has_overcharge=validation.has_overcharge,
        validation_result=validation.model_dump(),
        raw_text=data.raw_text,
    )
    db.add(challan)
    await db.flush()
    await db.refresh(challan)

    return challan
