#!/usr/bin/env python3
"""Tag database entries using evidence from the public Epstein files archive.

This script uses the existing entry tag system. It does not add new schema
fields or sidecar pages.

Canonical tags:
  - epstein files
  - epstein associate
  - epstein flight logs
  - epstein communications
  - epstein testimony
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
ENTRIES_DIR = REPO_ROOT / "src" / "content" / "entries"
DEFAULT_SOURCE = REPO_ROOT / ".claude" / "tmp" / "epstein-docs.github.io"
DEFAULT_FOCUS_CONFIG = REPO_ROOT / "scripts" / "epstein_focus_people.json"

NAME_RE = re.compile(r"[^a-z0-9]+")


def normalize_name(value: str) -> str:
    lowered = re.sub(r"\s+", " ", value.strip().lower())
    return NAME_RE.sub(" ", lowered).strip()


def entry_aliases(value: str) -> set[str]:
    clean = re.sub(r"\s+", " ", value.strip())
    if not clean:
        return set()

    raw_forms = {
        clean,
        clean.split(",", 1)[0].strip(),
        re.split(r"\s+-\s+|\s+\(|,", clean)[0].strip(),
    }
    return {normalize_name(item) for item in raw_forms if item.strip()}


def load_focus_config(path: Path) -> dict[str, dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    focus: dict[str, dict] = {}
    for item in payload:
        slug = (item.get("entrySlug") or "").strip()
        if not slug:
            continue
        aliases = {
            normalize_name(value)
            for value in ([item.get("name")] + list(item.get("archiveNames") or []))
            if value and normalize_name(value)
        }
        focus[slug] = {
            "aliases": aliases,
            "sources": [value.strip() for value in (item.get("sources") or []) if value and value.strip()],
        }
    return focus


def split_frontmatter(text: str) -> tuple[str | None, str | None]:
    if not text.startswith("---\n"):
        return None, None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, None
    return parts[1].strip(), parts[2].lstrip("\n")


def yaml_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def dump_frontmatter(data: dict) -> str:
    key_order = ["name", "slug", "positions", "crimes", "tags", "sources", "needs_research"]
    ordered = {key: data[key] for key in key_order if key in data}
    lines: list[str] = []
    for key, value in ordered.items():
        if isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        elif isinstance(value, list):
            if not value:
                lines.append(f"{key}: []")
            else:
                lines.append(f"{key}:")
                for item in value:
                    lines.append(f"  - {yaml_quote(str(item))}")
        elif isinstance(value, str):
            lines.append(f"{key}: {yaml_quote(value)}")
        else:
            lines.append(f"{key}: {value}")
    return "\n".join(lines)


def classify_document(item: dict) -> set[str]:
    analysis = item.get("analysis") or {}
    document_type = (analysis.get("document_type") or "").lower()
    summary = (analysis.get("summary") or "").lower()
    significance = (analysis.get("significance") or "").lower()
    combined = " ".join([document_type, summary, significance])

    tags = {"epstein files"}

    if any(term in combined for term in ("flight log", "flight logs", "aircraft", "passenger")):
        tags.add("epstein flight logs")
    if any(term in combined for term in ("telephone", "phone", "message", "caller", "email", "contact information")):
        tags.add("epstein communications")
    if any(term in combined for term in ("testimony", "transcript", "cross", "deposition", "witness")):
        tags.add("epstein testimony")
    if any(term in combined for term in ("associate", "acquaintance", "socialized", "friend", "introduced", "social circle")):
        tags.add("epstein associate")

    return tags


def load_exact_matches(source_dir: Path) -> dict[str, set[str]]:
    analyses_path = source_dir / "analyses.json"
    payload = json.loads(analyses_path.read_text(encoding="utf-8"))
    matches: dict[str, set[str]] = {}
    for item in payload.get("analyses", []):
        analysis = item.get("analysis") or {}
        doc_tags = classify_document(item)
        for person in analysis.get("key_people") or []:
            normalized = normalize_name(person.get("name") or "")
            if not normalized:
                continue
            matches.setdefault(normalized, set()).update(doc_tags)
    return matches


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=str(DEFAULT_SOURCE), help="Path to the local epstein-docs.github.io checkout")
    parser.add_argument("--focus-config", default=str(DEFAULT_FOCUS_CONFIG), help="Path to the scoped focus-people config JSON")
    parser.add_argument("--apply", action="store_true", help="Write tag and source updates into entry frontmatter")
    args = parser.parse_args()

    exact_matches = load_exact_matches(Path(args.source).resolve())
    focus_config = load_focus_config(Path(args.focus_config).resolve())
    changes: list[tuple[Path, list[str]]] = []

    for path in sorted(ENTRIES_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        frontmatter, body = split_frontmatter(text)
        if frontmatter is None or body is None:
            continue
        data = yaml.safe_load(frontmatter) or {}
        matched_tags: set[str] = set()
        for alias in entry_aliases(data.get("name") or ""):
            matched_tags.update(exact_matches.get(alias, set()))
        for alias in focus_config.get(path.stem, {}).get("aliases", set()):
            matched_tags.update(exact_matches.get(alias, set()))
        if not matched_tags:
            continue

        tags = [tag.strip() for tag in (data.get("tags") or []) if tag.strip()]
        sources = [source.strip() for source in (data.get("sources") or []) if source.strip()]

        new_tags = sorted(set(tags) | matched_tags)
        new_sources = list(sources)
        for source in focus_config.get(path.stem, {}).get("sources", []):
            if source not in new_sources:
                new_sources.append(source)

        entry_changes = []
        if new_tags != tags:
            data["tags"] = new_tags
            entry_changes.append(f"tags -> {new_tags}")
        if new_sources != sources:
            data["sources"] = new_sources
            entry_changes.append(f"sources +{len(new_sources) - len(sources)} Epstein archive links")

        if not entry_changes:
            continue

        changes.append((path, entry_changes))
        if args.apply:
            new_frontmatter = dump_frontmatter(data)
            path.write_text(f"---\n{new_frontmatter}\n---\n{body}", encoding="utf-8", newline="\n")

    mode = "applied" if args.apply else "dry-run"
    print(f"{mode}: {len(changes)} entries matched the Epstein tagging rules")
    for path, entry_changes in changes[:20]:
        print(f"  {path.name}")
        for change in entry_changes:
            print(f"    - {change}")


if __name__ == "__main__":
    main()
