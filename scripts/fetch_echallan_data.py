"""
Utility to help collect and verify traffic fine data from official sources.

This script provides helpers for:
1. Checking state transport department websites for latest notifications
2. Cross-referencing fine amounts across states
3. Generating comparison reports between state and central rates

Usage:
    python scripts/fetch_echallan_data.py --report
    python scripts/fetch_echallan_data.py --compare gujarat central
    python scripts/fetch_echallan_data.py --summary
"""
import json
import os
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Optional

FINE_SCHEDULES_DIR = Path(__file__).parent.parent / "backend" / "data" / "fine_schedules"

OFFICIAL_SOURCES = {
    "echallan_national": "https://echallan.parivahan.gov.in",
    "parivahan": "https://parivahan.gov.in",
    "india_code": "https://indiacode.nic.in",
    "egazette": "https://egazette.nic.in",
}

STATE_TRANSPORT_URLS = {
    "andhra_pradesh": "https://aptransport.org",
    "assam": "https://transport.assam.gov.in",
    "bihar": "https://transport.bihar.gov.in",
    "chhattisgarh": "https://transport.cg.gov.in",
    "delhi": "https://transport.delhi.gov.in",
    "goa": "https://goatransport.gov.in",
    "gujarat": "https://rtogujarat.gov.in",
    "haryana": "https://haryanatransport.gov.in",
    "himachal_pradesh": "https://himachal.nic.in/transport",
    "jharkhand": "https://jhtransport.gov.in",
    "karnataka": "https://transport.karnataka.gov.in",
    "kerala": "https://mvd.kerala.gov.in",
    "madhya_pradesh": "https://transport.mp.gov.in",
    "maharashtra": "https://transport.maharashtra.gov.in",
    "odisha": "https://odishatransport.gov.in",
    "punjab": "https://punjabtransport.org",
    "rajasthan": "https://transport.rajasthan.gov.in",
    "tamil_nadu": "https://tnsta.gov.in",
    "telangana": "https://transport.telangana.gov.in",
    "uttar_pradesh": "https://uptransport.upsdc.gov.in",
    "uttarakhand": "https://transport.uk.gov.in",
    "west_bengal": "https://transport.wb.gov.in",
}


def load_schedule(state_key: str) -> Optional[dict]:
    filepath = FINE_SCHEDULES_DIR / f"{state_key}.json"
    if not filepath.exists():
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def compare_states(state1_key: str, state2_key: str):
    """Compare fine amounts between two states."""
    s1 = load_schedule(state1_key)
    s2 = load_schedule(state2_key)

    if not s1:
        print(f"File not found for: {state1_key}")
        return
    if not s2:
        print(f"File not found for: {state2_key}")
        return

    s1_name = s1.get("state", state1_key)
    s2_name = s2.get("state", state2_key)
    s1_sections = s1.get("sections", {})
    s2_sections = s2.get("sections", {})

    all_sections = sorted(set(list(s1_sections.keys()) + list(s2_sections.keys())))

    print(f"\n{'Section':<10} {'Offense':<45} {s1_name:>12} {s2_name:>12} {'Diff':>10}")
    print("-" * 90)

    for sec in all_sections:
        d1 = s1_sections.get(sec, {})
        d2 = s2_sections.get(sec, {})

        f1 = d1.get("first_offense", "N/A")
        f2 = d2.get("first_offense", "N/A")
        offense = d1.get("offense", d2.get("offense", "Unknown"))[:44]

        if isinstance(f1, (int, float)) and isinstance(f2, (int, float)):
            diff = f1 - f2
            diff_str = f"+{diff}" if diff > 0 else str(diff)
        else:
            diff_str = "-"

        f1_str = f"Rs {f1:,}" if isinstance(f1, (int, float)) else str(f1)
        f2_str = f"Rs {f2:,}" if isinstance(f2, (int, float)) else str(f2)

        print(f"{sec:<10} {offense:<45} {f1_str:>12} {f2_str:>12} {diff_str:>10}")


def generate_summary():
    """Generate a summary report of all states and their deviation from central rates."""
    central = load_schedule("central")
    if not central:
        print("Central schedule not found!")
        return

    central_sections = central.get("sections", {})

    print("\n" + "=" * 80)
    print("TRAFFIC FINE COMPARISON: ALL STATES vs CENTRAL RATES")
    print("=" * 80)

    json_files = sorted(FINE_SCHEDULES_DIR.glob("*.json"))
    state_files = [f for f in json_files if f.stem not in ("states_index", "central")]

    common_sections = ["177", "181", "183", "184", "185", "194", "194B", "194D"]

    header = f"{'State':<20}"
    for sec in common_sections:
        header += f" S.{sec:>5}"
    print(header)
    print("-" * (20 + 7 * len(common_sections)))

    central_row = f"{'CENTRAL (max)':<20}"
    for sec in common_sections:
        val = central_sections.get(sec, {}).get("first_offense", 0)
        central_row += f" {val:>6}"
    print(central_row)
    print("-" * (20 + 7 * len(common_sections)))

    for filepath in state_files:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        state_name = data.get("state", filepath.stem)[:19]
        sections = data.get("sections", {})

        row = f"{state_name:<20}"
        for sec in common_sections:
            val = sections.get(sec, {}).get("first_offense", "-")
            if isinstance(val, (int, float)):
                central_val = central_sections.get(sec, {}).get("first_offense", 0)
                if val < central_val:
                    row += f" {val:>5}*"
                else:
                    row += f" {val:>6}"
            else:
                row += f" {'N/A':>6}"
        print(row)

    print("\n* = reduced from central rate")
    print(f"\nSections: " + ", ".join(f"S.{s}" for s in common_sections))
    print("177=General, 181=No licence, 183=Speeding, 184=Dangerous driving,")
    print("185=Drunk driving, 194=No insurance, 194B=No helmet, 194D=Mobile phone")


def generate_report():
    """Generate a full verification report with links to check."""
    print("\n" + "=" * 70)
    print("TRAFFIC FINE DATA VERIFICATION REPORT")
    print("=" * 70)

    json_files = sorted(FINE_SCHEDULES_DIR.glob("*.json"))
    state_files = [f for f in json_files if f.stem not in ("states_index",)]

    stats = {"high": 0, "medium": 0, "low": 0}

    for filepath in state_files:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        state = data.get("state", filepath.stem)
        confidence = data.get("confidence", "unknown")
        effective = data.get("effective_date", "unknown")
        n_sections = len(data.get("sections", {}))

        stats[confidence] = stats.get(confidence, 0) + 1

        state_key = filepath.stem
        url = STATE_TRANSPORT_URLS.get(state_key, "N/A")

        print(f"\n  {state} [{confidence.upper()}]")
        print(f"    Sections: {n_sections} | Effective: {effective}")
        print(f"    Verify at: {url}")

    print(f"\n{'='*70}")
    print(f"Total files: {len(state_files)}")
    print(f"Confidence: {stats.get('high',0)} high, {stats.get('medium',0)} medium, {stats.get('low',0)} low")
    print(f"\nNational eChallan portal: {OFFICIAL_SOURCES['echallan_national']}")
    print(f"India Code (full Act): {OFFICIAL_SOURCES['india_code']}")
    print(f"{'='*70}")


def main():
    parser = argparse.ArgumentParser(description="Traffic fine data collection utility")
    parser.add_argument("--report", action="store_true", help="Generate verification report")
    parser.add_argument("--compare", nargs=2, metavar=("STATE1", "STATE2"),
                        help="Compare two states (use file names without .json)")
    parser.add_argument("--summary", action="store_true", help="Summary table of all states vs central")
    args = parser.parse_args()

    if args.compare:
        compare_states(args.compare[0], args.compare[1])
    elif args.summary:
        generate_summary()
    elif args.report:
        generate_report()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
