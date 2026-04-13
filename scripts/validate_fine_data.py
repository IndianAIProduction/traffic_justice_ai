"""
Validate fine schedule data files for consistency and completeness.

Usage:
    python scripts/validate_fine_data.py
    python scripts/validate_fine_data.py --verbose
    python scripts/validate_fine_data.py --state maharashtra
"""
import json
import os
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Tuple

FINE_SCHEDULES_DIR = Path(__file__).parent.parent / "backend" / "data" / "fine_schedules"
STATES_INDEX = FINE_SCHEDULES_DIR / "states_index.json"

REQUIRED_SECTIONS = ["177", "181", "183", "184", "185", "194", "194A", "194B", "194D"]

REQUIRED_FIELDS = ["offense", "first_offense"]

CENTRAL_MAX = {
    "177": 500, "177A": 500, "179": 2000, "180": 5000, "181": 5000,
    "182": 10000, "183": 2000, "184": 5000, "185": 10000, "186": 1000,
    "189": 5000, "190": 5000, "192": 5000, "192A": 10000, "194": 2000,
    "194A": 1000, "194B": 1000, "194C": 10000, "194D": 5000, "194E": 1000,
    "196": 5000, "199": 25000,
}


def load_json(filepath: Path) -> dict:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_state_file(filepath: Path, verbose: bool = False) -> Tuple[List[str], List[str]]:
    """Validate a single state fine schedule file. Returns (errors, warnings)."""
    errors = []
    warnings = []
    filename = filepath.name

    try:
        data = load_json(filepath)
    except json.JSONDecodeError as e:
        return [f"{filename}: Invalid JSON - {e}"], []

    if "state" not in data:
        errors.append(f"{filename}: Missing 'state' field")
    if "sections" not in data:
        errors.append(f"{filename}: Missing 'sections' field")
        return errors, warnings
    if "confidence" not in data:
        warnings.append(f"{filename}: Missing 'confidence' field")

    sections = data.get("sections", {})

    for req in REQUIRED_SECTIONS:
        if req not in sections:
            warnings.append(f"{filename}: Missing recommended section {req}")

    for section_key, section_data in sections.items():
        for field in REQUIRED_FIELDS:
            if field not in section_data:
                errors.append(f"{filename}: Section {section_key} missing '{field}'")

        first = section_data.get("first_offense")
        repeat = section_data.get("repeat")

        if first is not None and not isinstance(first, (int, float)):
            errors.append(f"{filename}: Section {section_key} 'first_offense' must be numeric, got {type(first).__name__}")
        if repeat is not None and not isinstance(repeat, (int, float)):
            errors.append(f"{filename}: Section {section_key} 'repeat' must be numeric, got {type(repeat).__name__}")

        if first is not None and first < 0:
            errors.append(f"{filename}: Section {section_key} 'first_offense' cannot be negative")

        base_key = section_key.replace("_heavy", "")
        if base_key in CENTRAL_MAX and first is not None:
            if first > CENTRAL_MAX[base_key]:
                warnings.append(
                    f"{filename}: Section {section_key} first_offense Rs {first} "
                    f"exceeds central max Rs {CENTRAL_MAX[base_key]}"
                )

        if verbose and first is not None and section_key in CENTRAL_MAX:
            if first < CENTRAL_MAX[section_key]:
                print(
                    f"  INFO: {filename} Section {section_key}: "
                    f"Rs {first} (reduced from central Rs {CENTRAL_MAX[section_key]})"
                )

    return errors, warnings


def validate_index(verbose: bool = False) -> Tuple[List[str], List[str]]:
    """Validate the states index file against actual files on disk."""
    errors = []
    warnings = []

    if not STATES_INDEX.exists():
        return [f"States index file not found: {STATES_INDEX}"], []

    try:
        index = load_json(STATES_INDEX)
    except json.JSONDecodeError as e:
        return [f"Invalid JSON in states index: {e}"], []

    all_entries = index.get("states", []) + index.get("union_territories", [])

    for entry in all_entries:
        name = entry.get("name", "Unknown")
        file_name = entry.get("file")
        if file_name is None:
            if verbose:
                print(f"  INFO: {name} has no file (uses central fallback)")
            continue

        filepath = FINE_SCHEDULES_DIR / file_name
        if not filepath.exists():
            errors.append(f"Index references '{file_name}' for {name} but file does not exist")

    json_files = set(f.name for f in FINE_SCHEDULES_DIR.glob("*.json")
                     if f.name not in ("states_index.json",))
    indexed_files = set(e["file"] for e in all_entries if e.get("file"))

    unindexed = json_files - indexed_files - {"states_index.json"}
    if unindexed:
        for f in sorted(unindexed):
            warnings.append(f"File '{f}' exists on disk but is not in states_index.json")

    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description="Validate fine schedule data files")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed info")
    parser.add_argument("--state", "-s", type=str, help="Validate a specific state file only")
    args = parser.parse_args()

    all_errors = []
    all_warnings = []

    print("=" * 60)
    print("Traffic Fine Data Validation")
    print("=" * 60)

    if args.state:
        filepath = FINE_SCHEDULES_DIR / f"{args.state.lower().replace(' ', '_')}.json"
        if not filepath.exists():
            print(f"File not found: {filepath}")
            sys.exit(1)
        errs, warns = validate_state_file(filepath, args.verbose)
        all_errors.extend(errs)
        all_warnings.extend(warns)
    else:
        print(f"\nScanning: {FINE_SCHEDULES_DIR}")
        json_files = sorted(FINE_SCHEDULES_DIR.glob("*.json"))
        state_files = [f for f in json_files if f.name != "states_index.json"]

        print(f"Found {len(state_files)} state/UT fine schedule files\n")

        for filepath in state_files:
            errs, warns = validate_state_file(filepath, args.verbose)
            all_errors.extend(errs)
            all_warnings.extend(warns)

        idx_errs, idx_warns = validate_index(args.verbose)
        all_errors.extend(idx_errs)
        all_warnings.extend(idx_warns)

    print("\n" + "-" * 60)
    if all_errors:
        print(f"\nERRORS ({len(all_errors)}):")
        for e in all_errors:
            print(f"  [ERROR] {e}")

    if all_warnings:
        print(f"\nWARNINGS ({len(all_warnings)}):")
        for w in all_warnings:
            print(f"  [WARN]  {w}")

    if not all_errors and not all_warnings:
        print("\nAll validations passed!")

    print(f"\nSummary: {len(all_errors)} errors, {len(all_warnings)} warnings")
    print("=" * 60)

    sys.exit(1 if all_errors else 0)


if __name__ == "__main__":
    main()
