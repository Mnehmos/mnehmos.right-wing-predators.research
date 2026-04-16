#!/usr/bin/env python3
"""Build Epstein archive reporting leads for database updates.

This script is meant to support newsroom work inside this repo:
- cross-reference archive people against current database entries
- separate focused archive figures from generic procedural noise
- surface substantive unmatched leads that merit editorial review

It does not write database entries automatically.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
ENTRIES_DIR = REPO_ROOT / "src" / "content" / "entries"
DEFAULT_SOURCE = REPO_ROOT / ".claude" / "tmp" / "epstein-docs.github.io"
DEFAULT_JSON_OUTPUT = REPO_ROOT / "reports" / "epstein-reporting-leads.json"
DEFAULT_MD_OUTPUT = REPO_ROOT / "reports" / "epstein-reporting-summary.md"
DEFAULT_FOCUS_CONFIG = REPO_ROOT / "scripts" / "epstein_focus_people.json"
DEFAULT_TRIAGE_CONFIG = REPO_ROOT / "scripts" / "epstein_lead_triage.json"
ARCHIVE_DOCUMENT_BASE = "https://epstein-docs.github.io/document/"
NAME_RE = re.compile(r"[^a-z0-9]+")

EXCLUDED_NAME_PATTERNS = [
    re.compile(r"^\(?\[?b\(\d+\)"),
    re.compile(r"^\(b\)\(\d+\)"),
    re.compile(r"^\[redacted\]$"),
    re.compile(r"\bunknown\b"),
    re.compile(r"^defense counsel$"),
    re.compile(r"\bdefendant\b"),
    re.compile(r"\bplaintiff\b"),
    re.compile(r"\brecipient\b"),
    re.compile(r"\bsender\b"),
    re.compile(r"\bwitness\b"),
    re.compile(r"\bvictim\b"),
    re.compile(r"\bjane doe\b"),
    re.compile(r"\bjohn doe\b"),
    re.compile(r"^the defendant$"),
    re.compile(r"^the plaintiff$"),
    re.compile(r"^the court$"),
    re.compile(r"^court$"),
    re.compile(r"^mr\.?\s"),
    re.compile(r"^ms\.?\s"),
    re.compile(r"^mrs\.?\s"),
]

PROCEDURAL_ROLE_PATTERNS = [
    re.compile(r"\bjudge\b"),
    re.compile(r"\bjuror\b"),
    re.compile(r"\bprosecutor\b"),
    re.compile(r"\bassistant u\.?s\.? attorney\b"),
    re.compile(r"\battorney for\b"),
    re.compile(r"\bdefense attorney\b"),
    re.compile(r"\bcounsel\b"),
    re.compile(r"\breporter\b"),
    re.compile(r"\bpublic information\b"),
    re.compile(r"\bwarden\b"),
    re.compile(r"\bassociate warden\b"),
    re.compile(r"\bchief psychologist\b"),
    re.compile(r"\breviewing officer\b"),
    re.compile(r"\brecipient\b"),
    re.compile(r"\bsender\b"),
]

SUBSTANTIVE_ROLE_PATTERNS = [
    re.compile(r"\bco-?defendant\b"),
    re.compile(r"\bdefendant\b"),
    re.compile(r"\bco-?conspirator\b"),
    re.compile(r"\bparticipant in .*abuse\b"),
    re.compile(r"\bimplicated\b"),
    re.compile(r"\balleged\b"),
    re.compile(r"\bassociate\b"),
    re.compile(r"\bpassenger\b"),
    re.compile(r"\bcaller\b"),
    re.compile(r"\bcontact person\b"),
    re.compile(r"\bassistant involved\b"),
    re.compile(r"\brecruit\w*\b"),
    re.compile(r"\bscout\b"),
    re.compile(r"\bsuspect\b"),
]

SUBSTANTIVE_TEXT_PATTERNS = [
    re.compile(r"\bsexual abuse\b"),
    re.compile(r"\bsexual assault\b"),
    re.compile(r"\bsex trafficking\b"),
    re.compile(r"\bsex crimes?\b"),
    re.compile(r"\bunderage\b"),
    re.compile(r"\bminor\b"),
    re.compile(r"\bco-?conspirator\b"),
    re.compile(r"\bimplicat\w+\b"),
    re.compile(r"\balleg\w+\b"),
    re.compile(r"\babuse\b"),
    re.compile(r"\bflight log\b"),
    re.compile(r"\btelephone message\b"),
    re.compile(r"\bphone\b"),
]

FOCUS_CATEGORIES = {
    "existing-entry": 0,
    "candidate-addition": 1,
    "context-only": 2,
}

TRIAGE_CATEGORY_ORDER = {
    "alias-or-duplicate": 0,
    "victim-or-plaintiff": 1,
    "procedural-government": 2,
    "shield-figure-context": 3,
    "network-associate-context": 4,
    "incidental-flight-or-phone": 5,
    "unrelated-proceeding": 6,
    "low-signal-context": 7,
}


def normalize_spaces(value: str | None) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", value.strip())


def normalize_name(value: str | None) -> str:
    return NAME_RE.sub(" ", normalize_spaces(value).lower()).strip()


def alias_forms(name: str | None) -> set[str]:
    clean = normalize_spaces(name)
    if not clean:
        return set()

    raw_forms = {
        clean,
        clean.split(",", 1)[0].strip(),
        re.split(r"\s+-\s+|\s+\(|,", clean)[0].strip(),
    }
    return {normalize_name(item) for item in raw_forms if item.strip()}


def slugify_document_id(value: str) -> str:
    return NAME_RE.sub("-", value.lower()).strip("-")


def load_focus_people(path: Path) -> tuple[list[dict], dict[str, dict], dict[str, dict]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    focus_list: list[dict] = []
    focus_canonical_lookup: dict[str, dict] = {}
    focus_alias_lookup: dict[str, dict] = {}

    for index, item in enumerate(payload):
        canonical_name = normalize_spaces(item.get("name"))
        normalized = normalize_name(canonical_name)
        if not canonical_name or not normalized:
            continue

        archive_names = [normalize_spaces(value) for value in (item.get("archiveNames") or [canonical_name]) if normalize_spaces(value)]
        record = {
            "name": canonical_name,
            "category": item.get("category", "context-only"),
            "notes": normalize_spaces(item.get("notes", "")),
            "entrySlug": normalize_spaces(item.get("entrySlug", "")),
            "archiveNames": archive_names,
            "sources": [normalize_spaces(value) for value in (item.get("sources") or []) if normalize_spaces(value)],
            "order": index,
        }
        focus_list.append(record)
        focus_canonical_lookup[normalized] = record
        for alias in archive_names + [canonical_name]:
            alias_normalized = normalize_name(alias)
            if alias_normalized:
                focus_alias_lookup[alias_normalized] = record

    return focus_list, focus_canonical_lookup, focus_alias_lookup


def load_triage_people(path: Path) -> tuple[list[dict], dict[str, dict], dict[str, dict]]:
    if not path.exists():
        return [], {}, {}

    payload = json.loads(path.read_text(encoding="utf-8"))
    triage_list: list[dict] = []
    triage_canonical_lookup: dict[str, dict] = {}
    triage_alias_lookup: dict[str, dict] = {}

    for index, item in enumerate(payload):
        canonical_name = normalize_spaces(item.get("name"))
        normalized = normalize_name(canonical_name)
        if not canonical_name or not normalized:
            continue

        archive_names = [normalize_spaces(value) for value in (item.get("archiveNames") or [canonical_name]) if normalize_spaces(value)]
        record = {
            "name": canonical_name,
            "category": normalize_spaces(item.get("category", "low-signal-context")),
            "notes": normalize_spaces(item.get("notes", "")),
            "archiveNames": archive_names,
            "order": index,
        }
        triage_list.append(record)
        triage_canonical_lookup[normalized] = record
        for alias in archive_names + [canonical_name]:
            alias_normalized = normalize_name(alias)
            if alias_normalized:
                triage_alias_lookup[alias_normalized] = record

    return triage_list, triage_canonical_lookup, triage_alias_lookup


def should_exclude_name(value: str, focus_alias_lookup: dict[str, dict]) -> bool:
    normalized = normalize_name(value)
    if not normalized:
        return True
    if normalized in focus_alias_lookup:
        return False

    lower = normalize_spaces(value).lower()
    if any(pattern.search(lower) for pattern in EXCLUDED_NAME_PATTERNS):
        return True
    if role_matches(PROCEDURAL_ROLE_PATTERNS, value):
        return True

    alpha_tokens = re.findall(r"[a-zA-Z]+", value)
    if len(alpha_tokens) < 2:
        return True

    return False


def role_matches(patterns: list[re.Pattern[str]], role: str) -> bool:
    lower = normalize_spaces(role).lower()
    return any(pattern.search(lower) for pattern in patterns)


def score_signal(role: str, document_type: str, summary: str, significance: str, focus_record: dict | None) -> int:
    combined = " ".join([document_type, summary, significance]).lower()
    score = 0

    if role_matches(SUBSTANTIVE_ROLE_PATTERNS, role):
        score += 2
    if any(pattern.search(combined) for pattern in SUBSTANTIVE_TEXT_PATTERNS):
        score += 2
    if any(term in document_type.lower() for term in ("pilot's flight log", "telephone message", "telephone record", "phone")):
        score += 1
    if role_matches(PROCEDURAL_ROLE_PATTERNS, role):
        score -= 2
    if focus_record and focus_record["category"] in {"existing-entry", "candidate-addition"}:
        score += 2

    return score


def load_entry_lookup() -> tuple[dict[str, dict], dict[str, dict]]:
    candidates: dict[str, list[dict]] = defaultdict(list)
    slug_lookup: dict[str, dict] = {}
    for path in sorted(ENTRIES_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        parts = text.split("---", 2)
        if len(parts) < 3:
            continue
        data = yaml.safe_load(parts[1]) or {}
        name = normalize_spaces(data.get("name", ""))
        slug_lookup[path.stem] = {"slug": path.stem, "name": name}
        for alias in alias_forms(name):
            candidates[alias].append({
                "slug": path.stem,
                "name": name,
            })

    lookup: dict[str, dict] = {}
    for alias, matches in candidates.items():
        unique = {(item["slug"], item["name"]) for item in matches}
        if len(unique) == 1:
            slug, name = next(iter(unique))
            lookup[alias] = {"slug": slug, "name": name}
    return lookup, slug_lookup


def classify_document_tags(item: dict) -> list[str]:
    analysis = item.get("analysis") or {}
    combined = " ".join([
        (analysis.get("document_type") or "").lower(),
        (analysis.get("summary") or "").lower(),
        (analysis.get("significance") or "").lower(),
    ])
    tags = {"epstein files"}
    if any(term in combined for term in ("flight log", "flight logs", "aircraft", "passenger")):
        tags.add("epstein flight logs")
    if any(term in combined for term in ("telephone", "phone", "message", "caller", "email", "contact information")):
        tags.add("epstein communications")
    if any(term in combined for term in ("testimony", "transcript", "cross", "deposition", "witness")):
        tags.add("epstein testimony")
    if any(term in combined for term in ("associate", "acquaintance", "socialized", "friend", "introduced", "social circle")):
        tags.add("epstein associate")
    return sorted(tags)


def build_record(
    normalized: str,
    bucket: dict,
    entry_lookup: dict[str, dict],
    entries_by_slug: dict[str, dict],
    focus_canonical_lookup: dict[str, dict],
    triage_canonical_lookup: dict[str, dict],
) -> dict:
    focus_record = focus_canonical_lookup.get(normalized)
    triage_record = triage_canonical_lookup.get(normalized)
    canonical_name = (
        focus_record["name"]
        if focus_record
        else triage_record["name"]
        if triage_record
        else bucket["variants"].most_common(1)[0][0]
    )
    entry_match = entry_lookup.get(normalized)
    if not entry_match and focus_record and focus_record.get("entrySlug"):
        entry_match = entries_by_slug.get(focus_record["entrySlug"])

    record = {
        "name": canonical_name,
        "normalizedName": normalized,
        "docCount": len(bucket["doc_ids"]),
        "topRoles": [role for role, _ in bucket["roles"].most_common(5)],
        "topDocumentTypes": [doc_type for doc_type, _ in bucket["document_types"].most_common(5)],
        "suggestedTags": [tag for tag, _ in bucket["suggested_tags"].most_common()],
        "samples": bucket["samples"][:5],
        "substantiveScore": bucket["substantive_score"],
        "proceduralHits": bucket["procedural_hits"],
        "focusCategory": focus_record["category"] if focus_record else None,
        "focusNotes": focus_record["notes"] if focus_record else "",
        "triageCategory": triage_record["category"] if triage_record else None,
        "triageNotes": triage_record["notes"] if triage_record else "",
    }

    if entry_match:
        record["entrySlug"] = entry_match["slug"]
        record["entryName"] = entry_match["name"]

    return record


def build_report(source_dir: Path, focus_config_path: Path, triage_config_path: Path) -> dict:
    payload = json.loads((source_dir / "analyses.json").read_text(encoding="utf-8"))
    focus_people, focus_canonical_lookup, focus_alias_lookup = load_focus_people(focus_config_path)
    triage_people, triage_canonical_lookup, triage_alias_lookup = load_triage_people(triage_config_path)
    entry_lookup, entries_by_slug = load_entry_lookup()

    people: dict[str, dict] = {}
    for item in payload.get("analyses", []):
        analysis = item.get("analysis") or {}
        document_id = normalize_spaces(item.get("document_id", ""))
        document_number = normalize_spaces(item.get("document_number") or document_id)
        document_type = normalize_spaces(analysis.get("document_type") or "Document")
        summary = normalize_spaces(analysis.get("summary") or "")
        significance = normalize_spaces(analysis.get("significance") or "")
        document_tags = classify_document_tags(item)

        for person in analysis.get("key_people") or []:
            raw_name = normalize_spaces((person or {}).get("name", ""))
            if should_exclude_name(raw_name, focus_alias_lookup):
                continue

            raw_normalized = normalize_name(raw_name)
            focus_record = focus_alias_lookup.get(raw_normalized)
            triage_record = triage_alias_lookup.get(raw_normalized) if not focus_record else None
            normalized = (
                normalize_name(focus_record["name"])
                if focus_record
                else normalize_name(triage_record["name"])
                if triage_record
                else raw_normalized
            )
            role = normalize_spaces((person or {}).get("role", ""))
            signal_score = score_signal(role, document_type, summary, significance, focus_record)

            bucket = people.setdefault(normalized, {
                "variants": Counter(),
                "doc_ids": set(),
                "roles": Counter(),
                "document_types": Counter(),
                "suggested_tags": Counter(),
                "samples": [],
                "substantive_score": 0,
                "procedural_hits": 0,
            })

            bucket["variants"][raw_name] += 1
            bucket["doc_ids"].add(document_id)
            if role:
                bucket["roles"][role] += 1
            if document_type:
                bucket["document_types"][document_type] += 1
            for tag in document_tags:
                bucket["suggested_tags"][tag] += 1

            if role_matches(PROCEDURAL_ROLE_PATTERNS, role):
                bucket["procedural_hits"] += 1
            if signal_score > 0:
                bucket["substantive_score"] += signal_score

            if len(bucket["samples"]) < 8:
                bucket["samples"].append({
                    "documentId": document_id,
                    "documentNumber": document_number,
                    "documentType": document_type,
                    "role": role,
                    "summary": summary,
                    "significance": significance,
                    "url": f"{ARCHIVE_DOCUMENT_BASE}{slugify_document_id(document_id)}/",
                })

    all_people = [
        build_record(normalized, bucket, entry_lookup, entries_by_slug, focus_canonical_lookup, triage_canonical_lookup)
        for normalized, bucket in people.items()
    ]

    existing_matches = [item for item in all_people if item.get("entrySlug")]
    unmatched_people = [item for item in all_people if not item.get("entrySlug")]
    focus_matches = [item for item in all_people if item.get("focusCategory")]
    candidate_additions = [
        item for item in focus_matches
        if item["focusCategory"] == "candidate-addition" and not item.get("entrySlug")
    ]
    triaged_non_entry = [
        item for item in all_people
        if not item.get("entrySlug") and item.get("triageCategory")
    ]
    substantive_unmatched = [
        item for item in unmatched_people
        if item["substantiveScore"] > 0 and item["proceduralHits"] < item["docCount"] and not item.get("triageCategory")
    ]

    existing_matches.sort(key=lambda item: (-item["docCount"], item["entrySlug"]))
    unmatched_people.sort(key=lambda item: (-item["docCount"], item["name"].lower()))
    substantive_unmatched.sort(key=lambda item: (-item["substantiveScore"], -item["docCount"], item["name"].lower()))
    triaged_non_entry.sort(
        key=lambda item: (
            TRIAGE_CATEGORY_ORDER.get(item["triageCategory"], 99),
            -item["docCount"],
            item["name"].lower(),
        )
    )
    focus_matches.sort(
        key=lambda item: (
            FOCUS_CATEGORIES.get(item["focusCategory"], 99),
            focus_canonical_lookup[item["normalizedName"]]["order"],
        )
    )
    candidate_additions.sort(key=lambda item: (-item["substantiveScore"], -item["docCount"], item["name"].lower()))
    triage_counts = Counter(item["triageCategory"] for item in triaged_non_entry)

    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "sourceRepo": "https://github.com/epstein-docs/epstein-docs.github.io",
        "focusPeopleConfig": str(focus_config_path.relative_to(REPO_ROOT)),
        "triageConfig": str(triage_config_path.relative_to(REPO_ROOT)) if triage_config_path.exists() else "",
        "totalDocumentsAnalyzed": len(payload.get("analyses", [])),
        "peopleIndexed": len(all_people),
        "existingEntryMatches": existing_matches,
        "focusPeople": focus_matches,
        "candidateAdditions": candidate_additions,
        "resolvedNonEntryLeads": triaged_non_entry,
        "resolvedNonEntryCounts": dict(sorted(triage_counts.items(), key=lambda item: (TRIAGE_CATEGORY_ORDER.get(item[0], 99), item[0]))),
        "substantiveUnmatchedPeople": substantive_unmatched,
        "unmatchedPeople": unmatched_people,
    }


def write_person_block(lines: list[str], person: dict, include_entry: bool = False) -> None:
    heading = person["name"]
    if include_entry and person.get("entrySlug"):
        heading = f"{person['entryName']} (`{person['entrySlug']}`)"

    lines.append(f"### {heading}")
    lines.append("")
    lines.append(f"- Archive documents: {person['docCount']}")
    if person.get("focusCategory"):
        lines.append(f"- Focus category: {person['focusCategory']}")
    if person.get("focusNotes"):
        lines.append(f"- Notes: {person['focusNotes']}")
    if person.get("suggestedTags"):
        lines.append(f"- Suggested tags: {', '.join(person['suggestedTags'])}")
    if person.get("topRoles"):
        lines.append(f"- Top roles: {', '.join(person['topRoles'])}")
    if person.get("topDocumentTypes"):
        lines.append(f"- Top document types: {', '.join(person['topDocumentTypes'])}")
    if person.get("samples"):
        sample = person["samples"][0]
        lines.append(f"- Example document: [{sample['documentId']}]({sample['url']})")
    lines.append("")


def write_markdown(report: dict, output_path: Path) -> None:
    lines = [
        "# Epstein Reporting Leads",
        "",
        f"Generated: {report['generatedAt']}",
        "",
        f"- Documents analyzed: {report['totalDocumentsAnalyzed']}",
        f"- Unique people indexed: {report['peopleIndexed']}",
        f"- Existing entry matches: {len(report['existingEntryMatches'])}",
        f"- Focus people matched: {len(report['focusPeople'])}",
        f"- Resolved non-entry leads: {len(report.get('resolvedNonEntryLeads', []))}",
        f"- Candidate additions: {len(report['candidateAdditions'])}",
        f"- Substantive unmatched leads: {len(report['substantiveUnmatchedPeople'])}",
        "",
        "## Existing Entry Matches",
        "",
    ]

    if not report["existingEntryMatches"]:
        lines.append("No current database entries matched the archive people index.")
        lines.append("")
    else:
        for person in report["existingEntryMatches"][:25]:
            write_person_block(lines, person, include_entry=True)

    lines.extend([
        "## Focus Archive People",
        "",
        "These names come from the scoped focus list used to keep archive reporting aligned with this database.",
        "",
    ])

    if not report["focusPeople"]:
        lines.append("No focus people were found in the current archive run.")
        lines.append("")
    else:
        for person in report["focusPeople"]:
            write_person_block(lines, person, include_entry=bool(person.get("entrySlug")))

    lines.extend([
        "## Triage Coverage",
        "",
        "These archive names were explicitly resolved as aliases, victims, procedural actors, incidental mentions, or other non-entry context instead of remaining in the unmatched queue.",
        "",
    ])

    if not report.get("resolvedNonEntryCounts"):
        lines.append("No non-entry lead triage has been recorded yet.")
        lines.append("")
    else:
        for category, count in report["resolvedNonEntryCounts"].items():
            lines.append(f"- {category}: {count}")
        lines.append("")

    lines.extend([
        "## Candidate Additions",
        "",
        "These focus people are not yet in the database and still look relevant enough for editorial review.",
        "",
    ])

    if not report["candidateAdditions"]:
        lines.append("No focused candidate additions were identified.")
        lines.append("")
    else:
        for person in report["candidateAdditions"]:
            write_person_block(lines, person)

    lines.extend([
        "## Substantive Unmatched Leads",
        "",
        "These archive names cleared basic noise filtering and showed allegation, association, flight-log, or communications signals.",
        "",
    ])

    if not report["substantiveUnmatchedPeople"]:
        lines.append("No substantive unmatched leads were identified.")
        lines.append("")
    else:
        for person in report["substantiveUnmatchedPeople"][:40]:
            write_person_block(lines, person)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=str(DEFAULT_SOURCE), help="Path to the local epstein-docs.github.io checkout")
    parser.add_argument("--focus-config", default=str(DEFAULT_FOCUS_CONFIG), help="Path to the scoped focus-people config JSON")
    parser.add_argument("--triage-config", default=str(DEFAULT_TRIAGE_CONFIG), help="Path to the lead-triage config JSON")
    parser.add_argument("--json-output", default=str(DEFAULT_JSON_OUTPUT), help="Path for the JSON report")
    parser.add_argument("--md-output", default=str(DEFAULT_MD_OUTPUT), help="Path for the Markdown summary")
    args = parser.parse_args()

    report = build_report(
        Path(args.source).resolve(),
        Path(args.focus_config).resolve(),
        Path(args.triage_config).resolve(),
    )

    json_output = Path(args.json_output).resolve()
    md_output = Path(args.md_output).resolve()
    json_output.parent.mkdir(parents=True, exist_ok=True)

    json_output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_markdown(report, md_output)

    print(f"Wrote JSON report to {json_output}")
    print(f"Wrote Markdown summary to {md_output}")
    print(f"Existing entry matches: {len(report['existingEntryMatches'])}")
    print(f"Candidate additions: {len(report['candidateAdditions'])}")
    print(f"Substantive unmatched leads: {len(report['substantiveUnmatchedPeople'])}")


if __name__ == "__main__":
    main()
