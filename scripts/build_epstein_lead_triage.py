#!/usr/bin/env python3
"""Build a triage ledger for unresolved Epstein archive leads.

The output of this script is a non-entry disposition file used by the
reporting workflow to mark archive leads as resolved context instead of
leaving them in the substantive unmatched queue forever.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REPORT = REPO_ROOT / "reports" / "epstein-reporting-leads.json"
DEFAULT_OUTPUT = REPO_ROOT / "scripts" / "epstein_lead_triage.json"
NAME_RE = re.compile(r"[^a-z0-9]+")

VICTIM_PATTERNS = [
    re.compile(r"\bvictim\b"),
    re.compile(r"\balleged victim\b"),
    re.compile(r"\bplaintiff\b"),
    re.compile(r"\bwitness\b"),
]

PROCEDURAL_PATTERNS = [
    re.compile(r"\bassistant u\.?s\.? attorney\b"),
    re.compile(r"\bprosecutor\b"),
    re.compile(r"\battorney general\b"),
    re.compile(r"\bunited states attorney\b"),
    re.compile(r"\bstate attorney\b"),
    re.compile(r"\bjudge\b"),
    re.compile(r"\bbop\b"),
    re.compile(r"\bcorrectional\b"),
    re.compile(r"\bpsychologist\b"),
    re.compile(r"\badministrator\b"),
    re.compile(r"\binvestigating officer\b"),
]

SHIELD_PATTERNS = [
    re.compile(r"\bcounsel\b"),
    re.compile(r"\bdefense attorney\b"),
    re.compile(r"\battorney\b"),
    re.compile(r"\blawyer\b"),
    re.compile(r"\bco-executor\b"),
    re.compile(r"\bestate\b"),
]

NETWORK_PATTERNS = [
    re.compile(r"\bco-?conspirator\b"),
    re.compile(r"\brecruit\w*\b"),
    re.compile(r"\bassociate\b"),
    re.compile(r"\bbrother\b"),
    re.compile(r"\bmentor\b"),
    re.compile(r"\bclient\b"),
    re.compile(r"\bfriend\b"),
    re.compile(r"\bscout\b"),
    re.compile(r"\bguarantor\b"),
    re.compile(r"\bco-surety\b"),
    re.compile(r"\bpresent with epstein\b"),
]

INCIDENTAL_PATTERNS = [
    re.compile(r"\bpilot\b"),
    re.compile(r"\bco-pilot\b"),
    re.compile(r"\bpassenger\b"),
    re.compile(r"\bcaller\b"),
    re.compile(r"\bcrew member\b"),
    re.compile(r"\bflight attendant\b"),
    re.compile(r"\bobserver\b"),
    re.compile(r"\bshipper\b"),
    re.compile(r"\brecipient\b"),
    re.compile(r"\baccount holder\b"),
]

ALIAS_TARGETS = {
    "sarah kellen a k a sarah kensignton or sarah vickers": "Sarah Kellen",
    "virginia roberts giuffre": "Virginia Giuffre",
    "virginia l giuffre": "Virginia Giuffre",
    "virginia roberts": "Virginia Giuffre",
    "bill clinton": "Bill Clinton",
    "president clinton": "Bill Clinton",
    "g m": "Telephone log shorthand",
}

CATEGORY_NOTES = {
    "alias-or-duplicate": "Alias or duplicate naming variant already accounted for elsewhere in the archive workflow.",
    "victim-or-plaintiff": "Victim, plaintiff, or witness context lead; retained as archival context rather than promoted to a subject entry.",
    "procedural-government": "Procedural government, court, prison, or investigator lead; relevant to the record but not a subject entry.",
    "shield-figure-context": "Legal or protective actor tied to the Epstein case who remains triaged as context rather than a standalone entry in this pass.",
    "network-associate-context": "Associate, relative, or broader network figure tracked as context rather than promoted to a standalone entry in this pass.",
    "incidental-flight-or-phone": "Lead appears mainly in flight logs, message slips, shipping records, or similar incidental archive traces.",
    "unrelated-proceeding": "Likely contamination from unrelated proceedings bundled into the archive corpus rather than an Epstein-network subject lead.",
    "low-signal-context": "Mentioned in the archive but not strong enough on current evidence for a standalone entry.",
}


def normalize_name(value: str | None) -> str:
    if not value:
        return ""
    lowered = re.sub(r"\s+", " ", value.strip().lower())
    return NAME_RE.sub(" ", lowered).strip()


def text_blob(person: dict) -> str:
    parts: list[str] = []
    parts.extend(person.get("topRoles") or [])
    parts.extend(person.get("topDocumentTypes") or [])
    for sample in person.get("samples") or []:
        parts.append(sample.get("summary") or "")
        parts.append(sample.get("significance") or "")
    return " ".join(parts).lower()


def matches(patterns: list[re.Pattern[str]], text: str) -> bool:
    return any(pattern.search(text) for pattern in patterns)


def classify_person(person: dict) -> tuple[str, str]:
    normalized = normalize_name(person.get("name"))
    blob = text_blob(person)

    if normalized in ALIAS_TARGETS:
        target = ALIAS_TARGETS[normalized]
        return "alias-or-duplicate", f"Alias or duplicate variant of {target}."

    if matches(VICTIM_PATTERNS, blob):
        return "victim-or-plaintiff", CATEGORY_NOTES["victim-or-plaintiff"]

    if matches(PROCEDURAL_PATTERNS, blob):
        return "procedural-government", CATEGORY_NOTES["procedural-government"]

    epstein_specific = any(term in blob for term in ("epstein", "maxwell", "giuffre", "jane doe"))
    if ("defendant" in blob or "trial" in blob or "deposition" in blob) and not epstein_specific:
        return "unrelated-proceeding", CATEGORY_NOTES["unrelated-proceeding"]

    if matches(SHIELD_PATTERNS, blob):
        return "shield-figure-context", CATEGORY_NOTES["shield-figure-context"]

    if matches(NETWORK_PATTERNS, blob):
        return "network-associate-context", CATEGORY_NOTES["network-associate-context"]

    if matches(INCIDENTAL_PATTERNS, blob):
        return "incidental-flight-or-phone", CATEGORY_NOTES["incidental-flight-or-phone"]

    return "low-signal-context", CATEGORY_NOTES["low-signal-context"]


def load_existing(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    records: dict[str, dict] = {}
    for item in payload:
        normalized = normalize_name(item.get("name"))
        if normalized:
            records[normalized] = item
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", default=str(DEFAULT_REPORT), help="Path to reports/epstein-reporting-leads.json")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Path for the triage JSON")
    args = parser.parse_args()

    report_path = Path(args.report).resolve()
    output_path = Path(args.output).resolve()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    existing = load_existing(output_path)

    records: list[dict] = []
    counts: Counter[str] = Counter()

    for person in report.get("substantiveUnmatchedPeople", []):
        normalized = normalize_name(person.get("name"))
        if not normalized:
            continue

        if normalized in existing:
            record = existing[normalized]
        else:
            category, notes = classify_person(person)
            record = {
                "name": person["name"],
                "category": category,
                "notes": notes,
                "archiveNames": [person["name"]],
            }

        counts[record["category"]] += 1
        records.append(record)

    records.sort(key=lambda item: (item["category"], item["name"].lower()))
    output_path.write_text(json.dumps(records, indent=2), encoding="utf-8")

    print(f"Wrote triage config to {output_path}")
    print(f"Resolved substantive leads: {len(records)}")
    for category, count in sorted(counts.items()):
        print(f"  {category}: {count}")


if __name__ == "__main__":
    main()
