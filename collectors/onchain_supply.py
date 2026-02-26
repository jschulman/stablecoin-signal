#!/usr/bin/env python3
"""
Fetch stablecoin supply data from DefiLlama and M1 from FRED.

Writes to data/onchain/supply.json matching the existing schema.
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
SUPPLY_PATH = PROJECT_ROOT / "data" / "onchain" / "supply.json"

DEFILLAMA_URL = "https://stablecoins.llama.fi/stablecoins?includePrices=true"
FRED_M1_URL = (
    "https://api.stlouisfed.org/fred/series/observations"
    "?series_id=M1SL&api_key={key}&file_type=json&sort_order=desc&limit=24"
)


def fetch_defillama():
    """Fetch current stablecoin supplies from DefiLlama."""
    resp = requests.get(DEFILLAMA_URL, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    usdc_supply = 0.0
    usdt_supply = 0.0
    others_supply = 0.0

    for coin in data.get("peggedAssets", []):
        symbol = coin.get("symbol", "").upper()
        chains = coin.get("chainCirculating", {})
        total = 0.0
        for chain_data in chains.values():
            pegged = chain_data.get("current", {}).get("peggedUSD", 0)
            if pegged:
                total += float(pegged)

        if symbol == "USDC":
            usdc_supply = total
        elif symbol == "USDT":
            usdt_supply = total
        else:
            others_supply += total

    # Convert to billions
    usdc_bn = round(usdc_supply / 1e9, 1) if usdc_supply > 1e6 else usdc_supply
    usdt_bn = round(usdt_supply / 1e9, 1) if usdt_supply > 1e6 else usdt_supply
    others_bn = round(others_supply / 1e9, 1) if others_supply > 1e6 else others_supply

    # DefiLlama may already report in raw USD or in billions depending on version
    # If values are already in a reasonable range (< 10000), treat as billions
    if usdc_bn > 10000:
        usdc_bn = round(usdc_bn / 1e9, 1)
    if usdt_bn > 10000:
        usdt_bn = round(usdt_bn / 1e9, 1)
    if others_bn > 10000:
        others_bn = round(others_bn / 1e9, 1)

    return usdc_bn, usdt_bn, others_bn


def fetch_m1_from_fred(api_key):
    """Fetch M1 money supply from FRED. Returns list of (date, value_trillion)."""
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
        # FRED date is YYYY-MM-DD, we want YYYY-MM
        date_month = date_str[:7]
        # FRED M1SL is in billions of dollars
        value_bn = float(val)
        value_trillion = round(value_bn / 1000.0, 2)
        observations.append({
            "date": date_month,
            "value_billion": value_bn,
            "value_trillion": value_trillion,
        })

    return observations


def compute_pct_of_m1(total_stablecoin_bn, m1_billion):
    """
    Compute stablecoin supply as percentage of M1.
    Both total_stablecoin_bn and m1 are in billions.
    pct_of_m1 = total_stablecoin / (m1 * 1000) -- but since both are in billions:
    pct_of_m1 = total_stablecoin_bn / (m1_trillion * 1000) = total_bn / m1_bn * 100
    Actually: pct_of_m1 as shown in data is (total_bn / m1_bn) * 100 roughly
    Looking at data: 255 bn / 18.62 tn = 255 / 18620 = 0.0137 -> 1.37%
    So the formula is: total_stablecoin_bn / (m1_trillion * 1000) * 100
    But m1 from FRED is in billions, so: total_stablecoin_bn / m1_billion * 100
    255 / 18620 * 100 = 1.37  -- matches!
    """
    if m1_billion <= 0:
        return 0.0
    return round(total_stablecoin_bn / m1_billion * 100, 2)


def build_supply_entry(date_str, usdc, usdt, others, m1_trillion, pct):
    """Build a single monthly supply entry matching the schema."""
    total = round(usdc + usdt + others, 1)
    return {
        "date": date_str,
        "usdc": usdc,
        "usdt": usdt,
        "others": others,
        "total": total,
        "m1_trillion": m1_trillion,
        "pct_of_m1": pct,
    }


def update_milestones(monthly):
    """Update milestone statuses based on the latest data."""
    latest = monthly[-1] if monthly else None
    if not latest:
        return []

    total = latest.get("total", 0)
    m1_tn = latest.get("m1_trillion", 18.0)
    m1_bn = m1_tn * 1000

    milestones = [
        {"threshold": "1% of M1", "target_bn": round(m1_bn * 0.01), "status": "pending", "note": "Structurally noticeable"},
        {"threshold": "2% of M1", "target_bn": round(m1_bn * 0.02), "status": "pending", "note": "Material monetary instrument"},
        {"threshold": "5% of M1", "target_bn": round(m1_bn * 0.05), "status": "pending", "note": "Systemically significant"},
        {"threshold": "10% of M1", "target_bn": round(m1_bn * 0.10), "status": "pending", "note": "Parallel monetary system"},
    ]

    for ms in milestones:
        if total >= ms["target_bn"]:
            ms["status"] = "passed"
            # Find earliest month where total exceeded target
            for m in monthly:
                if m.get("total", 0) >= ms["target_bn"]:
                    ms["date"] = m["date"]
                    break

    return milestones


def run_live():
    """Fetch live data from APIs and update supply.json."""
    api_key = os.environ.get("FRED_API_KEY")
    if not api_key:
        print("ERROR: FRED_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    print("Fetching stablecoin supply from DefiLlama...")
    usdc_bn, usdt_bn, others_bn = fetch_defillama()
    total_bn = round(usdc_bn + usdt_bn + others_bn, 1)
    print(f"  USDC: {usdc_bn}B, USDT: {usdt_bn}B, Others: {others_bn}B, Total: {total_bn}B")

    print("Fetching M1 from FRED...")
    m1_observations = fetch_m1_from_fred(api_key)
    if not m1_observations:
        print("ERROR: No M1 observations returned from FRED.", file=sys.stderr)
        sys.exit(1)

    latest_m1 = m1_observations[0]
    m1_bn_val = latest_m1["value_billion"]
    m1_tn_val = latest_m1["value_trillion"]
    print(f"  Latest M1: {m1_tn_val}T ({latest_m1['date']})")

    pct = compute_pct_of_m1(total_bn, m1_bn_val)
    print(f"  Stablecoin as % of M1: {pct}%")

    # Load existing data to preserve history
    existing = {}
    if SUPPLY_PATH.exists():
        with open(SUPPLY_PATH, "r") as f:
            existing = json.load(f)

    monthly = existing.get("monthly", [])
    now = datetime.now(timezone.utc)
    current_month = now.strftime("%Y-%m")

    new_entry = build_supply_entry(current_month, usdc_bn, usdt_bn, others_bn, m1_tn_val, pct)

    # Replace or append current month
    replaced = False
    for i, entry in enumerate(monthly):
        if entry.get("date") == current_month:
            monthly[i] = new_entry
            replaced = True
            break

    if not replaced:
        monthly.append(new_entry)

    # Keep last 24 months
    monthly = monthly[-24:]

    milestones = update_milestones(monthly)

    result = {
        "metadata": {
            "last_updated": now.strftime("%Y-%m-%d"),
            "source": "DefiLlama Stablecoins API, FRED M1SL series",
            "note": "Supply in USD billions. M1 in USD trillions. Edit to add manual corrections. Push to trigger rebuild.",
        },
        "monthly": monthly,
        "milestones": milestones,
    }

    SUPPLY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SUPPLY_PATH, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Saved to {SUPPLY_PATH}")
    return result


def run_mock():
    """Read existing data without making API calls."""
    if not SUPPLY_PATH.exists():
        print(f"ERROR: Mock data not found at {SUPPLY_PATH}", file=sys.stderr)
        sys.exit(1)

    with open(SUPPLY_PATH, "r") as f:
        data = json.load(f)

    print(f"Mock mode: loaded {len(data.get('monthly', []))} monthly entries from {SUPPLY_PATH}")
    latest = data.get("monthly", [{}])[-1]
    print(f"  Latest: {latest.get('date')} - Total: {latest.get('total')}B - {latest.get('pct_of_m1')}% of M1")
    return data


def main():
    parser = argparse.ArgumentParser(description="Fetch stablecoin supply data")
    parser.add_argument("--mock", action="store_true", help="Use existing data instead of fetching from APIs")
    args = parser.parse_args()

    if args.mock:
        run_mock()
    else:
        run_live()


if __name__ == "__main__":
    main()
