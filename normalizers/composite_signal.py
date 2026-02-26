#!/usr/bin/env python3
"""
Compute the composite signal from all data sources.

Reads supply, volume, wallets, remittance, adoption layers, regulatory,
treasury, and tax data. Produces data/composite/signal.json.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Input paths
SUPPLY_PATH = DATA_DIR / "onchain" / "supply.json"
VOLUME_PATH = DATA_DIR / "onchain" / "volume.json"
WALLETS_PATH = DATA_DIR / "onchain" / "wallets.json"
REMITTANCE_PATH = DATA_DIR / "remittance" / "comparison.json"
ADOPTION_PATH = DATA_DIR / "adoption" / "layers.json"
REGULATORY_PATH = DATA_DIR / "regulatory" / "genius_act.json"
TREASURY_PATH = DATA_DIR / "treasury" / "reserves.json"
TAX_PATH = DATA_DIR / "tax" / "status.json"

# Output path
SIGNAL_PATH = DATA_DIR / "composite" / "signal.json"


def load_json(path):
    """Load a JSON file, returning empty dict if not found."""
    if not path.exists():
        print(f"  WARNING: {path} not found, using empty data")
        return {}
    with open(path, "r") as f:
        return json.load(f)


def get_latest_entry(data, key="monthly"):
    """Get the last entry from a list under the given key."""
    entries = data.get(key, [])
    if entries:
        return entries[-1]
    return {}


def compute_layers_summary(adoption):
    """Extract layer statuses from adoption data."""
    layers = adoption.get("layers", [])
    summary = {}
    name_map = {1: "hold", 2: "earn", 3: "spend", 4: "borrow", 5: "invisible"}
    for layer in layers:
        num = layer.get("number")
        name = name_map.get(num, layer.get("name", "").lower())
        summary[name] = layer.get("status", "unknown")
    return summary


def compute_canary_status(adoption):
    """Extract canary statuses from adoption data."""
    status = {}

    # Primary canary
    canary = adoption.get("canary", {})
    status["payroll"] = canary.get("status", "unknown")

    # Secondary canaries
    secondary = adoption.get("secondary_canaries", [])
    canary_map = {
        "Tax equivalence": "tax_equivalence",
        "Stablecoin > Western Union": "western_union_surpassed",
        "1% of ACH": "one_pct_ach",
        "Top-25 bank custody": "top25_bank_custody",
    }

    for sc in secondary:
        key = canary_map.get(sc.get("name"))
        if key:
            status[key] = sc.get("status", "unknown")

    return status


def compute_days_until_effective(regulatory):
    """Compute days until GENIUS Act effective date."""
    # Use pre-computed value if available
    if "days_until_effective" in regulatory:
        return regulatory["days_until_effective"]

    effective_date = regulatory.get("effective_date_estimate")
    if not effective_date:
        return None

    try:
        target = datetime.strptime(effective_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = target - now
        return max(0, delta.days)
    except ValueError:
        return None


def build_signal():
    """Build the composite signal from all data sources."""
    print("Loading data sources...")

    supply = load_json(SUPPLY_PATH)
    volume = load_json(VOLUME_PATH)
    wallets = load_json(WALLETS_PATH)
    remittance = load_json(REMITTANCE_PATH)
    adoption = load_json(ADOPTION_PATH)
    regulatory = load_json(REGULATORY_PATH)
    treasury = load_json(TREASURY_PATH)
    tax = load_json(TAX_PATH)

    # Extract latest values
    latest_supply = get_latest_entry(supply, "monthly")
    latest_volume = get_latest_entry(volume, "monthly")
    latest_wallets = get_latest_entry(wallets, "monthly")
    latest_remittance = get_latest_entry(remittance, "quarterly")
    latest_treasury = get_latest_entry(treasury, "monthly")

    # Compute layers summary
    layers_summary = compute_layers_summary(adoption)
    print(f"  Layers: {layers_summary}")

    # Compute key metrics
    supply_pct = latest_supply.get("pct_of_m1", 0)
    commercial_pct = latest_volume.get("commercial_pct_of_ach", 0)
    remittance_pct = latest_remittance.get("stablecoin_pct", 0)
    treasury_pct = latest_treasury.get("pct_of_market", 0)
    tax_friction = tax.get("current_friction", "unknown")
    active_wallets = latest_wallets.get("monthly_active_m", 0)
    days_until = compute_days_until_effective(regulatory)

    key_metrics = {
        "supply_pct_of_m1": supply_pct,
        "commercial_pct_of_ach": commercial_pct,
        "remittance_pct_of_outbound": remittance_pct,
        "treasury_pct_of_tbills": treasury_pct,
        "tax_friction": tax_friction,
        "active_wallets_m": active_wallets,
    }

    if days_until is not None:
        key_metrics["genius_act_days_until_effective"] = days_until

    print(f"  Key metrics: {key_metrics}")

    # Compute canary statuses
    canary_status = compute_canary_status(adoption)
    print(f"  Canaries: {canary_status}")

    # Build the composite signal
    now = datetime.now(timezone.utc)
    signal = {
        "metadata": {
            "last_updated": now.strftime("%Y-%m-%d"),
            "computed_by": "normalizers/composite_signal.py",
        },
        "layers_summary": layers_summary,
        "key_metrics": key_metrics,
        "canary_status": canary_status,
    }

    return signal


def run():
    """Build and save the composite signal."""
    signal = build_signal()

    SIGNAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SIGNAL_PATH, "w") as f:
        json.dump(signal, f, indent=2)

    print(f"Saved composite signal to {SIGNAL_PATH}")
    return signal


def main():
    parser = argparse.ArgumentParser(description="Compute composite stablecoin signal from all data sources")
    parser.add_argument("--mock", action="store_true", help="Use existing data files (same behavior, flag for consistency)")
    args = parser.parse_args()

    if args.mock:
        print("Mock mode: computing signal from existing data files")
    else:
        print("Live mode: computing signal from data files")

    run()


if __name__ == "__main__":
    main()
