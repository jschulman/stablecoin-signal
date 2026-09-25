#!/usr/bin/env python3
"""Validate curated Financial Rails evidence and build a deterministic summary.

The explicit schema below is enforced with the standard library; no network or
third-party packages are needed. Missing measurements are null, never inferred 0.
"""
import argparse
import copy
import json
import math
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "data/rails/evidence.json"
OUTPUT = ROOT / "data/rails/summary.json"
STAGES = ("announced", "pilot", "limited-production", "recurring-production", "paused", "discontinued")
CATEGORIES = ("payment-settlement", "institutional-treasury", "securities-collateral", "fund-operations")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def shape(value, keys, label):
    require(isinstance(value, dict) and set(value) == set(keys.split()), f"{label}: expected fields {keys}")


def text(value, label):
    require(isinstance(value, str) and bool(value.strip()), f"{label}: nonempty string required")


def texts(value, label, allow_empty=False):
    require(isinstance(value, list) and (allow_empty or bool(value)), f"{label}: array required")
    for item in value:
        text(item, label)
    require(len(set(value)) == len(value), f"{label}: duplicates")


def day(value, label):
    text(value, label)
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{label}: ISO date required") from exc
    require(parsed.isoformat() == value, f"{label}: YYYY-MM-DD required")
    return parsed


def refs(value, source_ids, label, required=False):
    texts(value, label, allow_empty=not required)
    require(set(value) <= source_ids, f"{label}: unknown source reference")


def validate(data, as_of):
    """Strict schema and cross-field evidence validation. Fail closed on mistakes."""
    shape(data, "schema_version metadata records", "root")
    require(type(data["schema_version"]) is int and data["schema_version"] == 1, "Unsupported schema version")
    meta = data["metadata"]
    shape(meta, "scope review_cadence_days coverage_note", "metadata")
    text(meta["scope"], "scope")
    text(meta["coverage_note"], "coverage_note")
    cadence = meta["review_cadence_days"]
    require(type(cadence) is int and 1 <= cadence <= 90, "review cadence must be 1–90 days")
    require(isinstance(data["records"], list), "records: array required")
    ids, events = set(), set()
    for record in data["records"]:
        shape(record, "id event_id institutions rail asset_legal_claim category use_cases geography event_date event_date_precision stage stage_evidence sources reviewed_at recurring_evidence volume customer_visibility operating_evidence control_implications procurement_evidence next_review_question", "record")
        for key in ("id", "event_id", "rail", "asset_legal_claim", "geography", "customer_visibility", "next_review_question"):
            text(record[key], key)
        require(record["id"] not in ids, "Duplicate record id")
        require(record["event_id"] not in events, "Duplicate event: one record per event prevents duplicate volume")
        ids.add(record["id"])
        events.add(record["event_id"])
        for key in ("institutions", "use_cases", "control_implications"):
            texts(record[key], key)
        require(record["category"] in CATEGORIES, "Unknown category")
        require(record["stage"] in STAGES, "Unknown stage")
        require(record["event_date_precision"] in ("exact", "reported-by"), "Unknown event date precision")
        event = day(record["event_date"], "event_date")
        reviewed = day(record["reviewed_at"], "reviewed_at")
        require(event <= reviewed <= as_of, "Event/review date cannot be future or reviewed before event")
        require(isinstance(record["sources"], list) and record["sources"], "Primary sources required")
        source_ids = set()
        for source in record["sources"]:
            shape(source, "id title url published_date", "source")
            for key in ("id", "title", "url"):
                text(source[key], key)
            url = urlparse(source["url"])
            require(url.scheme == "https" and bool(url.hostname) and not url.username and not url.password, "Public HTTPS source required")
            require(source["id"] not in source_ids, "Duplicate source id")
            source_ids.add(source["id"])
            require(day(source["published_date"], "published_date") <= reviewed, "Source postdates review")
        stage = record["stage_evidence"]
        shape(stage, "production_observed details source_ids", "stage_evidence")
        require(type(stage["production_observed"]) is bool, "production_observed: boolean required")
        text(stage["details"], "stage details")
        refs(stage["source_ids"], source_ids, "stage sources", required=True)
        if record["stage"] in ("limited-production", "recurring-production"):
            require(stage["production_observed"], "Production stage requires observed production evidence")
            stage_dates = [day(s["published_date"], "stage date") for s in record["sources"] if s["id"] in stage["source_ids"]]
            require(max(stage_dates) >= event, "Production evidence predates the event")
        recurring = record["recurring_evidence"]
        shape(recurring, "status details observation_dates source_ids", "recurring_evidence")
        require(recurring["status"] in ("unknown", "documented"), "Invalid recurring status")
        text(recurring["details"], "recurring details")
        texts(recurring["observation_dates"], "recurring dates", allow_empty=True)
        for observed in recurring["observation_dates"]:
            require(event <= day(observed, "observation date") <= reviewed, "Recurring observation outside event/review period")
        refs(recurring["source_ids"], source_ids, "recurring sources", required=recurring["status"] == "documented")
        if recurring["status"] == "documented":
            require(len(recurring["observation_dates"]) >= 2, "Recurring activity requires at least two distinct observation dates")
            recurring_source_dates = [s["published_date"] for s in record["sources"] if s["id"] in recurring["source_ids"]]
            require(max(recurring_source_dates) >= max(recurring["observation_dates"]), "Recurring source predates claimed repeat observation")
        else:
            require(not recurring["observation_dates"] and not recurring["source_ids"], "Unknown recurring evidence must not imply observations")
        if record["stage"] == "recurring-production":
            require(recurring["status"] == "documented", "Recurring production requires documented repeat activity")
        volume = record["volume"]
        shape(volume, "value unit period denominator source_ids note", "volume")
        text(volume["note"], "volume note")
        for key in ("unit", "period", "denominator"):
            if volume[key] is not None:
                text(volume[key], "volume " + key)
        refs(volume["source_ids"], source_ids, "volume sources", required=volume["value"] is not None)
        if volume["value"] is not None:
            require(type(volume["value"]) in (int, float) and math.isfinite(volume["value"]) and volume["value"] >= 0, "Volume must be finite nonnegative number or null")
            require(volume["unit"] is not None and volume["period"] is not None, "Known volume requires unit and period")
        else:
            require(not volume["source_ids"], "Unknown volume must not imply measurement sources")
        operating = record["operating_evidence"]
        shape(operating, "availability cost_change prefunding_change note", "operating_evidence")
        text(operating["note"], "operating note")
        for key in ("availability", "cost_change", "prefunding_change"):
            if operating[key] is not None:
                text(operating[key], key)
        procurement = record["procurement_evidence"]
        shape(procurement, "status details source_ids", "procurement_evidence")
        require(procurement["status"] in ("unknown", "documented"), "Invalid procurement status")
        text(procurement["details"], "procurement details")
        refs(procurement["source_ids"], source_ids, "procurement sources", required=procurement["status"] == "documented")
        if procurement["status"] == "unknown":
            require(not procurement["source_ids"], "Unknown procurement cannot claim source evidence")
    return data


def build_summary(data, as_of):
    validate(data, as_of)
    records = sorted(copy.deepcopy(data["records"]), key=lambda r: r["id"])
    cadence = data["metadata"]["review_cadence_days"]
    for record in records:
        reviewed = day(record["reviewed_at"], "reviewed_at")
        due = reviewed + timedelta(days=cadence)
        record["review_age_days"] = (as_of - reviewed).days
        record["review_due"] = due.isoformat()
        record["review_status"] = "overdue" if as_of > due else "current"
        record["source_age_days"] = (as_of - max(day(s["published_date"], "source") for s in record["sources"])).days
    stage_counts = Counter(r["stage"] for r in records)
    category_counts = Counter(r["category"] for r in records)
    all_sources = [s["published_date"] for r in records for s in r["sources"]]
    return {
        "schema_version": 1,
        "metadata": {
            **data["metadata"],
            "built_at": as_of.isoformat(),
            "latest_source_date": max(all_sources, default=None),
            "oldest_review_date": min((r["reviewed_at"] for r in records), default=None),
            "volume_aggregation": "none: heterogeneous and potentially overlapping workflows",
        },
        "summary": {
            "record_count": len(records),
            "stage_counts": {stage: stage_counts[stage] for stage in STAGES},
            "category_counts": {category: category_counts[category] for category in CATEGORIES},
            "overdue_reviews": sum(r["review_status"] == "overdue" for r in records),
            "recurring_records": stage_counts["recurring-production"],
            "unknown_volume_records": sum(r["volume"]["value"] is None for r in records),
        },
        "records": records,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--as-of", type=date.fromisoformat, default=datetime.now(timezone.utc).date())
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    try:
        result = build_summary(json.loads(args.source.read_text()), args.as_of)
    except (ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    if not args.validate_only:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(f"Validated {result['summary']['record_count']} Financial Rails records; {result['summary']['overdue_reviews']} overdue reviews as of {args.as_of}")


if __name__ == "__main__":
    main()
