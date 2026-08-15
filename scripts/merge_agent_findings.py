#!/usr/bin/env python3
"""Merge daily agent JSON findings into the public updates ledger."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parent.parent
INBOX = REPO_ROOT / "data" / "agent-findings" / "inbox"
OUTPUT = REPO_ROOT / "src" / "data" / "agent-findings.json"
INGESTION_REPORT = REPO_ROOT / "reports" / "agent-findings-ingestion.json"
ALLOWED_CONFIDENCE = {"high", "medium", "low"}
ALLOWED_STATUS = {
    "official_action",
    "criminal_charge",
    "court_filing",
    "ethics_finding",
    "reported_allegation",
    "other",
}


def is_http_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def clean_text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def stable_event_id(event: dict) -> str:
    seed = "|".join(
        clean_text(event.get(key)).lower()
        for key in ("person", "event_type", "jurisdiction", "published_at", "source_url")
    )
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]


def load_payload(path: Path) -> tuple[dict | None, list[str]]:
    errors: list[str] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"{path}: {exc}"]

    if not isinstance(payload, dict):
        return None, [f"{path}: top-level JSON must be an object"]
    if not clean_text(payload.get("agent")):
        errors.append(f"{path}: missing agent")
    if not clean_text(payload.get("run_date")):
        errors.append(f"{path}: missing run_date")
    if not isinstance(payload.get("events", []), list):
        errors.append(f"{path}: events must be a list")
    return payload, errors


def normalize_event(event: object, payload: dict, path: Path) -> tuple[dict | None, str | None]:
    if not isinstance(event, dict):
        return None, f"{path}: event must be an object"

    person = clean_text(event.get("person"))
    source_url = clean_text(event.get("source_url"))
    status = clean_text(event.get("status"))
    confidence = clean_text(event.get("confidence"))
    summary = clean_text(event.get("summary"))
    if not person or not source_url or not summary:
        return None, f"{path}: event requires person, source_url, and summary"
    if not is_http_url(source_url):
        return None, f"{path}: event source_url is not http(s)"
    if status not in ALLOWED_STATUS:
        return None, f"{path}: unsupported event status '{status}'"
    if confidence not in ALLOWED_CONFIDENCE:
        return None, f"{path}: unsupported confidence '{confidence}'"

    normalized = {
        "event_id": clean_text(event.get("event_id")) or stable_event_id(event),
        "agent": clean_text(payload.get("agent")),
        "run_date": clean_text(payload.get("run_date")),
        "person": person,
        "aliases": event.get("aliases") if isinstance(event.get("aliases"), list) else [],
        "role": clean_text(event.get("role")),
        "affiliation": clean_text(event.get("affiliation")),
        "jurisdiction": clean_text(event.get("jurisdiction")),
        "government_level": clean_text(event.get("government_level")),
        "branch": clean_text(event.get("branch")),
        "event_type": clean_text(event.get("event_type")),
        "status": status,
        "auto_publish": event.get("auto_publish") is True,
        "confidence": confidence,
        "source_url": source_url,
        "source_title": clean_text(event.get("source_title")),
        "publisher": clean_text(event.get("publisher")),
        "published_at": clean_text(event.get("published_at")),
        "source_type": clean_text(event.get("source_type")),
        "subject_response": clean_text(event.get("subject_response")),
        "summary": summary,
        "reason_for_status": clean_text(event.get("reason_for_status")),
        "source_file": str(path.resolve().relative_to(REPO_ROOT)).replace("\\", "/"),
    }
    return normalized, None


def main() -> int:
    files = sorted(INBOX.glob("**/*.json")) if INBOX.exists() else []
    published: dict[str, dict] = {}
    errors: list[str] = []
    quarantined = 0
    accepted = 0

    for path in files:
        payload, payload_errors = load_payload(path)
        errors.extend(payload_errors)
        if payload is None:
            continue
        for raw_event in payload.get("events", []):
            event, event_error = normalize_event(raw_event, payload, path)
            if event_error:
                errors.append(event_error)
                continue
            assert event is not None
            if not event["auto_publish"] or event["confidence"] == "low":
                quarantined += 1
                continue
            published[event["event_id"]] = event
            accepted += 1

    events = sorted(
        published.values(),
        key=lambda item: (item["published_at"], item["person"].lower(), item["event_id"]),
        reverse=True,
    )
    source_digest = hashlib.sha256(
        json.dumps(events, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    ledger = {
        "schema_version": 1,
        "source_digest": source_digest,
        "event_count": len(events),
        "events": events,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")

    report = {
        "run_date": date.today().isoformat(),
        "input_files": len(files),
        "accepted_events": len(events),
        "accepted_event_occurrences": accepted,
        "quarantined_events": quarantined,
        "validation_errors": errors,
    }
    INGESTION_REPORT.parent.mkdir(parents=True, exist_ok=True)
    INGESTION_REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    # Invalid files are quarantined by omission so one malformed agent result
    # cannot prevent valid findings from reaching the daily publication run.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
