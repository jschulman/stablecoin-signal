#!/usr/bin/env python3
"""Validate, derive and copy public data in one offline build entry point."""
import argparse
import json
import shutil
from datetime import date, datetime, timezone
from pathlib import Path

from composite_signal import build_signal
from financial_rails import build_summary

ROOT = Path(__file__).resolve().parent.parent


def build(as_of):
    evidence = json.loads((ROOT / "data/rails/evidence.json").read_text())
    summary = build_summary(evidence, as_of)
    # Validation succeeds before any publishing data changes.
    (ROOT / "data/rails/summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    signal = build_signal(as_of.isoformat())
    (ROOT / "data/composite/signal.json").write_text(json.dumps(signal, indent=2, allow_nan=False) + "\n")
    for source in sorted((ROOT / "data").rglob("*.json")):
        if "raw" in source.relative_to(ROOT / "data").parts:
            continue
        target = ROOT / "docs/data" / source.relative_to(ROOT / "data")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    shutil.copyfile(ROOT / "METHODOLOGY.md", ROOT / "docs/METHODOLOGY.md")
    print(f"Built dashboard as of {as_of}; source dates preserved; {summary['summary']['record_count']} rails records")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", type=date.fromisoformat, default=datetime.now(timezone.utc).date())
    build(parser.parse_args().as_of)
