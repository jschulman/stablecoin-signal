#!/usr/bin/env python3
"""
Validate and compute days-until-effective for GENIUS Act tracker.

Reads data/regulatory/genius_act.json, computes days_until_effective
based on effective_date_estimate, and updates the file.
Use --mock to run on existing data without external calls.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GENIUS_PATH = PROJECT_ROOT / "data" / "regulatory" / "genius_act.json"


def compute_days_until(target_date_str):
    """Compute days from today until a target date string (YYYY-MM-DD)."""
    try:
        target = datetime.strptime(target_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None

    now = datetime.now(timezone.utc)
    delta = target - now
    return max(0, delta.days)


def validate_milestones(data):
    """Validate milestone data integrity. Returns list of warnings."""
    warnings = []
    milestones = data.get("milestones", [])

    for ms in milestones:
        if not ms.get("milestone"):
            warnings.append("Milestone entry missing 'milestone' field")
        if ms.get("status") not in ("done", "in_progress", "pending"):
            warnings.append(f"Invalid status '{ms.get('status')}' for: {ms.get('milestone', 'unknown')}")

    if not data.get("act_name"):
        warnings.append("Missing act_name field")
    if not data.get("signed_date"):
        warnings.append("Missing signed_date field")
    if not data.get("effective_date_estimate"):
        warnings.append("Missing effective_date_estimate field")

    return warnings


def process(data):
    """Process genius_act.json: compute days_until_effective and validate."""
    effective_date = data.get("effective_date_estimate")
    if effective_date:
        days = compute_days_until(effective_date)
        if days is not None:
            data["days_until_effective"] = days
            print(f"  Effective date: {effective_date}")
            print(f"  Days until effective: {days}")
        else:
            print(f"  WARNING: Could not parse effective_date_estimate: {effective_date}")
    else:
        print("  WARNING: No effective_date_estimate in data")

    # Also compute days for each milestone with a deadline
    for ms in data.get("milestones", []):
        deadline = ms.get("deadline")
        if deadline and ms.get("status") != "done":
            # Handle YYYY-MM format by appending -01
            if len(deadline) == 7:
                deadline_full = deadline + "-01"
            else:
                deadline_full = deadline
            days = compute_days_until(deadline_full)
            if days is not None:
                ms["days_remaining"] = days

    # Update metadata
    now = datetime.now(timezone.utc)
    if "metadata" not in data:
        data["metadata"] = {}
    data["metadata"]["last_updated"] = now.strftime("%Y-%m-%d")

    return data


def run(mock=False):
    """Main processing logic."""
    if not GENIUS_PATH.exists():
        print(f"ERROR: Data file not found at {GENIUS_PATH}", file=sys.stderr)
        sys.exit(1)

    with open(GENIUS_PATH, "r") as f:
        data = json.load(f)

    label = "Mock mode" if mock else "Live mode"
    print(f"{label}: processing {GENIUS_PATH}")

    # Validate
    warnings = validate_milestones(data)
    if warnings:
        print("  Validation warnings:")
        for w in warnings:
            print(f"    - {w}")
    else:
        print("  Validation: all checks passed")

    # Process
    data = process(data)

    # Count statuses
    statuses = {}
    for ms in data.get("milestones", []):
        s = ms.get("status", "unknown")
        statuses[s] = statuses.get(s, 0) + 1
    print(f"  Milestones: {statuses}")

    # Save
    with open(GENIUS_PATH, "w") as f:
        json.dump(data, f, indent=2)

    print(f"  Saved to {GENIUS_PATH}")
    return data


def main():
    parser = argparse.ArgumentParser(description="Validate and update GENIUS Act regulatory milestones")
    parser.add_argument("--mock", action="store_true", help="Run on existing data (no external API calls needed)")
    args = parser.parse_args()

    run(mock=args.mock)


if __name__ == "__main__":
    main()
