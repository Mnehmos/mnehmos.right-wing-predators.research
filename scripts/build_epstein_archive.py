#!/usr/bin/env python3
"""
Build compact research artifacts from the public Epstein archive repo.

Outputs:
  - src/data/epstein-summary.json
      Small build-time summary consumed by Astro pages.
  - public/data/epstein-documents.json
      Compact client-searchable document index.

This script intentionally avoids copying the upstream raw OCR corpus into the
site. Instead, it groups page-level JSON into document records and emits a
lightweight local bridge layer for research.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any


DEFAULT_SOURCE = Path(".claude/tmp/epstein-docs.github.io")
DEFAULT_SUMMARY_OUT = Path("src/data/epstein-summary.json")
DEFAULT_DOCS_OUT = Path("public/data/epstein-documents.json")
LIVE_ARCHIVE_URL = "https://epstein-docs.github.io/"
SOURCE_REPO_URL = "https://github.com/epstein-docs/epstein-docs.github.io"

TOP_PEOPLE = 18
TOP_ORGANIZATIONS = 18
TOP_LOCATIONS = 18
TOP_TYPES = 12
FEATURED_DOCUMENTS = 18
RECENT_DOCUMENTS = 18
MAX_DOC_PEOPLE = 8
MAX_DOC_ORGANIZATIONS = 6
MAX_DOC_LOCATIONS = 5
MAX_DOC_REFERENCES = 6
MAX_DOC_TOPICS = 5
MAX_SUMMARY_LEN = 360
MAX_SIGNIFICANCE_LEN = 220

MONTHS = {
    "jan": "01",
    "january": "01",
    "feb": "02",
    "february": "02",
    "mar": "03",
    "march": "03",
    "apr": "04",
    "april": "04",
    "may": "05",
    "jun": "06",
    "june": "06",
    "jul": "07",
    "july": "07",
    "aug": "08",
    "august": "08",
    "sep": "09",
    "sept": "09",
    "september": "09",
    "oct": "10",
    "october": "10",
    "nov": "11",
    "november": "11",
    "dec": "12",
    "december": "12",
}


@dataclass
class DocumentAccumulator:
    key: str
    raw_numbers: Counter[str] = field(default_factory=Counter)
    folders: set[str] = field(default_factory=set)
    page_count: int = 0
    best_page_rank: int = 10**9
    best_meta: dict[str, Any] = field(default_factory=dict)
    doc_type_counts: Counter[str] = field(default_factory=Counter)
    date_counts: Counter[str] = field(default_factory=Counter)
    people: Counter[str] = field(default_factory=Counter)
    organizations: Counter[str] = field(default_factory=Counter)
    locations: Counter[str] = field(default_factory=Counter)
    dates: Counter[str] = field(default_factory=Counter)
    reference_numbers: Counter[str] = field(default_factory=Counter)
    has_handwriting: bool = False
    has_stamps: bool = False


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value or "document"


def normalize_doc_num(value: str | None) -> str:
    if not value:
        return ""
    return slugify(value)


def normalize_spaces(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = re.sub(r"\s+", " ", str(value)).strip()
    if not cleaned:
        return None
    if cleaned.lower() in {"null", "none", "unknown", "n/a", "na"}:
        return None
    return cleaned


def trim_text(value: str | None, limit: int) -> str | None:
    text = normalize_spaces(value)
    if not text:
        return None
    if len(text) <= limit:
        return text
    clipped = text[: limit - 1].rsplit(" ", 1)[0].strip()
    return f"{clipped}..."


def parse_page_rank(value: str | None) -> int:
    if not value:
        return 10**9
    match = re.search(r"\d+", str(value))
    return int(match.group(0)) if match else 10**9


def normalize_date(value: str | None) -> str | None:
    if not value:
        return None

    raw = normalize_spaces(value)
    if not raw:
        return None

    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        return raw

    if re.fullmatch(r"\d{4}", raw):
        return f"{raw}-00-00"

    match = re.fullmatch(r"(\d{1,2})[/.](\d{1,2})[/.](\d{4})", raw)
    if match:
        month = match.group(1).zfill(2)
        day = match.group(2).zfill(2)
        return f"{match.group(3)}-{month}-{day}"

    match = re.fullmatch(r"(\d{4})[/.](\d{1,2})[/.](\d{1,2})", raw)
    if match:
        month = match.group(2).zfill(2)
        day = match.group(3).zfill(2)
        return f"{match.group(1)}-{month}-{day}"

    match = re.fullmatch(r"(?:[A-Za-z]+,?\s+)?([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})", raw)
    if match:
        month = MONTHS.get(match.group(1).lower())
        if month:
            day = match.group(2).zfill(2)
            return f"{match.group(3)}-{month}-{day}"

    match = re.fullmatch(r"(?:[A-Za-z]+,?\s+)?(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", raw)
    if match:
        month = MONTHS.get(match.group(2).lower())
        if month:
            day = match.group(1).zfill(2)
            return f"{match.group(3)}-{month}-{day}"

    match = re.fullmatch(r"Filed\s+(\d{1,2})/(\d{1,2})/(\d{2,4})", raw, flags=re.IGNORECASE)
    if match:
        year = match.group(3)
        if len(year) == 2:
            year = f"20{year}"
        month = match.group(1).zfill(2)
        day = match.group(2).zfill(2)
        return f"{year}-{month}-{day}"

    try:
        parsed = parsedate_to_datetime(raw)
        return parsed.date().isoformat()
    except Exception:
        pass

    return raw


def format_date(value: str | None) -> str | None:
    if not value:
        return None
    if re.fullmatch(r"\d{4}-00-00", value):
        return value[:4]
    match = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", value)
    if not match:
        return value
    year, month, day = match.groups()
    month_idx = int(month)
    day_idx = int(day)
    if month_idx < 1 or month_idx > 12:
        return value
    month_names = [
        "",
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]
    return f"{month_names[month_idx]} {day_idx}, {year}"


def canonicalize(mapping: dict[str, str], value: str | None) -> str | None:
    cleaned = normalize_spaces(value)
    if not cleaned:
        return None
    return normalize_spaces(mapping.get(cleaned, cleaned))


def choose_counter_value(counter: Counter[str]) -> str | None:
    if not counter:
        return None
    return sorted(counter.items(), key=lambda item: (-item[1], item[0].lower()))[0][0]


def top_counter_values(counter: Counter[str], limit: int) -> list[str]:
    if not counter:
        return []
    return [name for name, _ in sorted(counter.items(), key=lambda item: (-item[1], item[0].lower()))[:limit]]


def safe_load_json(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def load_mapping(path: Path, key: str | None = None) -> dict[str, str]:
    data = safe_load_json(path)
    if not isinstance(data, dict):
        return {}
    if key is None:
        return data
    sub = data.get(key)
    return sub if isinstance(sub, dict) else {}


def get_source_commit(source_dir: Path) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(source_dir), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        return proc.stdout.strip() or None
    except Exception:
        return None


def build_documents(source_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    results_dir = source_dir / "results"
    if not results_dir.is_dir():
        raise FileNotFoundError(f"Missing results directory: {results_dir}")

    people_map = load_mapping(source_dir / "dedupe.json", "people")
    org_map = load_mapping(source_dir / "dedupe.json", "organizations")
    loc_map = load_mapping(source_dir / "dedupe.json", "locations")
    type_map = load_mapping(source_dir / "dedupe_types.json", "mappings")

    analyses_raw = safe_load_json(source_dir / "analyses.json") or {}
    analyses_lookup: dict[str, dict[str, Any]] = {}
    analyses = analyses_raw.get("analyses") if isinstance(analyses_raw, dict) else []
    if isinstance(analyses, list):
        for item in analyses:
            if not isinstance(item, dict):
                continue
            key = normalize_doc_num(item.get("document_id") or item.get("document_number"))
            if not key:
                continue
            analysis = item.get("analysis")
            if isinstance(analysis, dict):
                analyses_lookup[key] = analysis

    accumulators: dict[str, DocumentAccumulator] = {}
    total_pages = 0

    for json_path in sorted(results_dir.rglob("*.json")):
        data = safe_load_json(json_path)
        if not isinstance(data, dict):
            continue

        metadata = data.get("document_metadata")
        metadata = metadata if isinstance(metadata, dict) else {}
        raw_number = normalize_spaces(metadata.get("document_number")) or json_path.stem
        doc_key = normalize_doc_num(raw_number)
        if not doc_key:
            continue

        acc = accumulators.setdefault(doc_key, DocumentAccumulator(key=doc_key))
        acc.raw_numbers[raw_number] += 1
        acc.page_count += 1
        total_pages += 1

        folder = json_path.parent.relative_to(results_dir).as_posix()
        acc.folders.add(folder)

        page_rank = parse_page_rank(metadata.get("page_number"))
        if page_rank < acc.best_page_rank:
            acc.best_page_rank = page_rank
            acc.best_meta = dict(metadata)

        doc_type = normalize_spaces(metadata.get("document_type"))
        canonical_type = normalize_spaces(type_map.get(doc_type, doc_type)) if doc_type else None
        if canonical_type:
            acc.doc_type_counts[canonical_type] += 1

        raw_date = metadata.get("date")
        normalized_doc_date = normalize_date(raw_date)
        if normalized_doc_date:
            acc.date_counts[normalized_doc_date] += 1

        acc.has_handwriting = acc.has_handwriting or bool(metadata.get("has_handwriting"))
        acc.has_stamps = acc.has_stamps or bool(metadata.get("has_stamps"))

        entities = data.get("entities")
        entities = entities if isinstance(entities, dict) else {}

        for person in entities.get("people") or []:
            canonical = canonicalize(people_map, person)
            if canonical:
                acc.people[canonical] += 1

        for org in entities.get("organizations") or []:
            canonical = canonicalize(org_map, org)
            if canonical:
                acc.organizations[canonical] += 1

        for loc in entities.get("locations") or []:
            canonical = canonicalize(loc_map, loc)
            if canonical:
                acc.locations[canonical] += 1

        for date_value in entities.get("dates") or []:
            normalized = normalize_date(date_value)
            if normalized:
                display = format_date(normalized) or str(date_value)
                acc.dates[display] += 1

        for ref in entities.get("reference_numbers") or []:
            cleaned = normalize_spaces(ref)
            if cleaned:
                acc.reference_numbers[cleaned] += 1

    documents: list[dict[str, Any]] = []
    people_index = Counter[str]()
    org_index = Counter[str]()
    loc_index = Counter[str]()
    type_index = Counter[str]()
    date_index = Counter[str]()

    for key, acc in accumulators.items():
        preferred_number = choose_counter_value(acc.raw_numbers) or key
        document_type = choose_counter_value(acc.doc_type_counts) or "Unknown"
        normalized_date = choose_counter_value(acc.date_counts)
        display_date = format_date(normalized_date) if normalized_date else None
        analysis = analyses_lookup.get(key, {})
        analysis_summary = trim_text(analysis.get("summary"), MAX_SUMMARY_LEN)
        analysis_significance = trim_text(analysis.get("significance"), MAX_SIGNIFICANCE_LEN)
        key_topics = []
        if isinstance(analysis.get("key_topics"), list):
            key_topics = [normalize_spaces(topic) for topic in analysis["key_topics"] if normalize_spaces(topic)]
        key_topics = key_topics[:MAX_DOC_TOPICS]

        people = top_counter_values(acc.people, MAX_DOC_PEOPLE)
        organizations = top_counter_values(acc.organizations, MAX_DOC_ORGANIZATIONS)
        locations = top_counter_values(acc.locations, MAX_DOC_LOCATIONS)
        references = top_counter_values(acc.reference_numbers, MAX_DOC_REFERENCES)

        url = f"{LIVE_ARCHIVE_URL.rstrip('/')}/document/{slugify(key)}/"

        doc_record = {
            "id": key,
            "documentNumber": preferred_number,
            "date": display_date,
            "dateSort": normalized_date,
            "documentType": document_type,
            "pageCount": acc.page_count,
            "folders": sorted(acc.folders),
            "hasHandwriting": acc.has_handwriting,
            "hasStamps": acc.has_stamps,
            "people": people,
            "organizations": organizations,
            "locations": locations,
            "dates": top_counter_values(acc.dates, 5),
            "referenceNumbers": references,
            "summary": analysis_summary,
            "significance": analysis_significance,
            "keyTopics": key_topics,
            "url": url,
        }
        documents.append(doc_record)

        for person in acc.people:
            people_index[person] += 1
        for org in acc.organizations:
            org_index[org] += 1
        for loc in acc.locations:
            loc_index[loc] += 1
        for date_value in acc.dates:
            date_index[date_value] += 1
        if document_type and document_type != "Unknown":
            type_index[document_type] += 1

    def featured_score(doc: dict[str, Any]) -> tuple[int, int, int]:
        text_bonus = 5 if doc.get("summary") else 0
        entity_bonus = len(doc["people"]) + len(doc["organizations"]) + len(doc["locations"])
        return (
            doc["pageCount"] * 2 + text_bonus + entity_bonus,
            doc["pageCount"],
            entity_bonus,
        )

    documents.sort(
        key=lambda doc: (
            doc["dateSort"] or "",
            featured_score(doc),
            doc["documentNumber"].lower(),
        ),
        reverse=True,
    )

    featured = sorted(documents, key=featured_score, reverse=True)[:FEATURED_DOCUMENTS]
    recent = [doc for doc in documents if doc.get("dateSort")] [:RECENT_DOCUMENTS]

    commit = get_source_commit(source_dir)
    metadata = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "sourceRepo": SOURCE_REPO_URL,
        "sourceArchive": LIVE_ARCHIVE_URL,
        "sourcePath": str(source_dir),
        "sourceCommit": commit,
        "stats": {
            "documents": len(documents),
            "pages": total_pages,
            "analyses": len(analyses_lookup),
            "people": len(people_index),
            "organizations": len(org_index),
            "locations": len(loc_index),
            "dates": len(date_index),
            "documentTypes": len(type_index),
        },
        "topPeople": [
            {"name": name, "count": count}
            for name, count in people_index.most_common(TOP_PEOPLE)
        ],
        "topOrganizations": [
            {"name": name, "count": count}
            for name, count in org_index.most_common(TOP_ORGANIZATIONS)
        ],
        "topLocations": [
            {"name": name, "count": count}
            for name, count in loc_index.most_common(TOP_LOCATIONS)
        ],
        "topDocumentTypes": [
            {"name": name, "count": count}
            for name, count in type_index.most_common(TOP_TYPES)
        ],
        "featuredDocuments": featured,
        "recentDocuments": recent,
    }

    return documents, metadata


def make_compact_index(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    compact: list[dict[str, Any]] = []
    for doc in documents:
        compact.append(
            {
                "id": doc["id"],
                "n": doc["documentNumber"],
                "d": doc["date"],
                "ds": doc["dateSort"],
                "t": doc["documentType"],
                "p": doc["pageCount"],
                "u": doc["url"],
                "pe": doc["people"],
                "og": doc["organizations"],
                "lo": doc["locations"],
                "rf": doc["referenceNumbers"],
                "tp": doc["keyTopics"],
                "s": doc["summary"],
            }
        )
    return compact


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Build site-friendly Epstein archive research artifacts.")
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help=f"Path to the cloned upstream repo (default: {DEFAULT_SOURCE})",
    )
    parser.add_argument(
        "--summary-out",
        type=Path,
        default=DEFAULT_SUMMARY_OUT,
        help=f"Output path for the small build-time summary (default: {DEFAULT_SUMMARY_OUT})",
    )
    parser.add_argument(
        "--documents-out",
        type=Path,
        default=DEFAULT_DOCS_OUT,
        help=f"Output path for the client-searchable document index (default: {DEFAULT_DOCS_OUT})",
    )
    args = parser.parse_args()

    source_dir = args.source.resolve()
    if not source_dir.exists():
        raise FileNotFoundError(f"Source repo not found: {source_dir}")

    documents, summary = build_documents(source_dir)
    compact_index = make_compact_index(documents)

    write_json(args.summary_out, summary)
    write_json(args.documents_out, compact_index)

    size_mb = args.documents_out.stat().st_size / (1024 * 1024)
    print(f"Wrote summary: {args.summary_out}")
    print(f"Wrote document index: {args.documents_out} ({size_mb:.2f} MB)")
    print(
        "Archive stats:",
        f"{summary['stats']['documents']} documents,",
        f"{summary['stats']['pages']} pages,",
        f"{summary['stats']['analyses']} analyses",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
