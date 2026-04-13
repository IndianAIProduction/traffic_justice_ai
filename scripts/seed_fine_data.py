"""
Script to verify fine schedule data is loaded correctly.
Run: python -m scripts.seed_fine_data
"""
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.challan_service import load_fine_schedule
from app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

FINE_SCHEDULES_DIR = os.path.join(
    os.path.dirname(__file__), "..", "backend", "data", "fine_schedules"
)


def main():
    states = ["central", "maharashtra", "karnataka"]

    for state in states:
        try:
            schedule = load_fine_schedule(state)
            section_count = len(schedule.get("sections", {}))
            logger.info(f"{state.title()}: {section_count} sections loaded")
        except FileNotFoundError:
            logger.warning(f"{state.title()}: No fine schedule file found")

    logger.info("Fine schedule verification complete")


if __name__ == "__main__":
    main()
