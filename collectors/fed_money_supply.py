#!/usr/bin/env python3
"""
Fetch M1 money supply from FRED API.

Writes to data/comparison/m1.json.
Use --mock to skip API calls and read existing data instead.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
M1_PATH = PROJECT_ROOT / "data" / "comparison" / "m1.json"

FRED_M1_URL = (
    "https://api.stlouisfed.org/fred/series/observations"
    "?series_id=M1SL&api_key={key}&file_type=json&sort_order=desc&limit=24"
)


def fetch_m1(api_key):
    """Fetch M1 money supply observations from FRED."""
    url = FRED_M1_URL.format(key=api_key)
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    observations = []
    for obs in data.get("observations", []):
        val = obs.get("value", ".")
        if val == ".":
            continue
        date_str = obs.get("date", "")
        date_month = date_str[:7]  # YYYY-MM
        # M1SL is in billions of dollars
        value_bn = float(val)
        value_trillion = round(value_bn / 1000.0, 2)
        observations.append({
            "date": date_month,
            "value_trillion": value_trillion,
        })

    # FRED returns desc order, reverse to chronological
    observations.reverse()
    return observations


def run_live():
    """Fetch live M1 data from FRED and save."""
    api_key = os.environ.get("FRED_API_KEY")
    if not api_key:
        print("ERROR: FRED_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    print("Fetching M1 money supply from FRED...")
    observations = fetch_m1(api_key)

    if not observations:
        print("ERROR: No M1 observations returned from FRED.", file=sys.stderr)
        sys.exit(1)

    latest = observations[-1]
    print(f"  {len(observations)} observations fetched")
    print(f"  Latest: {latest['date']} - {latest['value_trillion']}T")

    now = datetime.now(timezone.utc)
    result = {
        "metadata": {
            "last_updated": now.strftime("%Y-%m-%d"),
            "source": "FRED M1SL series (Federal Reserve Economic Data)",
            "series_id": "M1SL",
            "unit": "USD trillions",
            "frequency": "monthly",
            "note": "M1 includes currency in circulation, demand deposits, and other liquid deposits.",
        },
        "observations": observations,
    }

    M1_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(M1_PATH, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Saved to {M1_PATH}")
    return result


def run_mock():
    """Read existing data without making API calls."""
    if not M1_PATH.exists():
        print(f"Mock data not found at {M1_PATH}. Generating placeholder from supply data...")
        # Fall back to extracting M1 from supply.json if available
        supply_path = PROJECT_ROOT / "data" / "onchain" / "supply.json"
        if supply_path.exists():
            with open(supply_path, "r") as f:
                supply = json.load(f)
            observations = []
            for entry in supply.get("monthly", []):
                observations.append({
                    "date": entry["date"],
                    "value_trillion": entry.get("m1_trillion", 0),
                })
            result = {
                "metadata": {
                    "last_updated": supply.get("metadata", {}).get("last_updated", "unknown"),
                    "source": "Derived from supply.json (mock mode)",
                    "series_id": "M1SL",
                    "unit": "USD trillions",
                    "frequency": "monthly",
                    "note": "M1 includes currency in circulation, demand deposits, and other liquid deposits.",
                },
                "observations": observations,
            }
            M1_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(M1_PATH, "w") as f:
                json.dump(result, f, indent=2)
            print(f"Generated mock M1 data with {len(observations)} observations")
            return result
        else:
            print("ERROR: No supply.json available for mock data generation.", file=sys.stderr)
            sys.exit(1)

    with open(M1_PATH, "r") as f:
        data = json.load(f)

    observations = data.get("observations", [])
    print(f"Mock mode: loaded {len(observations)} observations from {M1_PATH}")
    if observations:
        latest = observations[-1]
        print(f"  Latest: {latest['date']} - {latest['value_trillion']}T")
    return data


def main():
    parser = argparse.ArgumentParser(description="Fetch M1 money supply from FRED")
    parser.add_argument("--mock", action="store_true", help="Use existing data instead of fetching from API")
    args = parser.parse_args()

    if args.mock:
        run_mock()
    else:
        run_live()


if __name__ == "__main__":
    main()
