import pytest
from app.services.challan_service import validate_fines, get_schedule_sections


def test_validate_fines_no_overcharge():
    sections = [
        {"section": "184", "amount": 5000},
        {"section": "194B", "amount": 1000},
    ]
    result = validate_fines(sections, "central")

    assert result.is_valid is True
    assert result.has_overcharge is False
    assert result.total_charged == 6000
    assert result.overcharge_amount == 0


def test_validate_fines_with_overcharge():
    sections = [
        {"section": "184", "amount": 15000},  # max is 10000
        {"section": "194B", "amount": 1000},
    ]
    result = validate_fines(sections, "central")

    assert result.has_overcharge is True
    assert result.total_charged == 16000
    assert result.overcharge_amount > 0


def test_validate_fines_unknown_section():
    sections = [{"section": "999", "amount": 500}]
    result = validate_fines(sections, "central")

    # Unknown section should not flag as overcharge
    assert len(result.section_analysis) == 1
    assert result.section_analysis[0].section == "999"
    assert "not found" in result.section_analysis[0].offense.lower()


def test_validate_fines_state_specific():
    sections = [{"section": "184", "amount": 5000}]
    result = validate_fines(sections, "maharashtra")

    assert result.is_valid is True
    assert result.section_analysis[0].offense == "Dangerous driving"


def test_validate_fines_fallback_to_central():
    sections = [{"section": "184", "amount": 5000}]
    result = validate_fines(sections, "nonexistent_state")

    # Should fall back to central schedule
    assert result.is_valid is True
    assert len(result.section_analysis) == 1


def test_get_schedule_sections_maharashtra_includes_184():
    rows = get_schedule_sections("Maharashtra")
    codes = {r["section"] for r in rows}
    assert "184" in codes
    row184 = next(r for r in rows if r["section"] == "184")
    assert "dangerous" in row184["offense"].lower()
    assert row184["max_fine"] >= 5000
