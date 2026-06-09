#!/usr/bin/env python3
"""Validate content entry frontmatter and editorial metadata."""

from __future__ import annotations

import os
from urllib.parse import urlparse

import yaml

ENTRIES_DIR = "src/content/entries"
SOURCE_TYPES = {"news", "court", "government", "archive", "social", "reference", "video", "other"}
CASE_TYPES = {"sexual misconduct", "abuse cover-up", "epstein network", "other"}
REVIEW_STATUSES = {"draft", "reviewed", "verified"}
CONFIDENCE_LEVELS = {"low", "medium", "high"}


def is_http_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
    except Exception:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def normalize_url(value: str) -> str:
    parsed = urlparse(value.strip())
    path = parsed.path.rstrip("/")
    normalized = parsed._replace(
        scheme=parsed.scheme.lower(),
        netloc=parsed.netloc.lower(),
        path=path,
        fragment="",
    )
    return normalized.geturl()


def validate_string_list(data: dict, field: str) -> list[str]:
    value = data.get(field, [])
    errors = []
    if not isinstance(value, list):
        return [f"Field {field} must be a list"]
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            errors.append(f"Field {field}[{index}] must be a non-empty string")
    return errors


def validate_source(source: object, index: int) -> list[str]:
    errors: list[str] = []

    if isinstance(source, str):
        if not is_http_url(source.strip()):
            errors.append(f"sources[{index}] must be an http(s) URL")
        return errors

    if not isinstance(source, dict):
        return [f"sources[{index}] must be a string URL or object"]

    url = source.get("url")
    if not isinstance(url, str) or not is_http_url(url.strip()):
        errors.append(f"sources[{index}].url must be an http(s) URL")

    for field in ("title", "publisher", "published_at", "notes"):
        if field in source and (not isinstance(source[field], str) or not source[field].strip()):
            errors.append(f"sources[{index}].{field} must be a non-empty string")

    if "archive_url" in source:
        archive_url = source["archive_url"]
        if not isinstance(archive_url, str) or not is_http_url(archive_url.strip()):
            errors.append(f"sources[{index}].archive_url must be an http(s) URL")

    if "source_type" in source and source["source_type"] not in SOURCE_TYPES:
        errors.append(f"sources[{index}].source_type must be one of {sorted(SOURCE_TYPES)}")

    if "primary" in source and not isinstance(source["primary"], bool):
        errors.append(f"sources[{index}].primary must be true or false")

    return errors


def main() -> int:
    files = sorted(f for f in os.listdir(ENTRIES_DIR) if f.endswith(".md"))
    valid = 0
    invalid: list[tuple[str, str]] = []
    warnings: list[tuple[str, str]] = []

    for filename in files:
        filepath = os.path.join(ENTRIES_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as handle:
                content = handle.read()

            parts = content.split("---")
            if len(parts) < 3:
                invalid.append((filename, "No frontmatter found"))
                continue

            frontmatter = parts[1].strip()
            data = yaml.safe_load(frontmatter)
            if not isinstance(data, dict):
                invalid.append((filename, "Frontmatter must decode to a mapping"))
                continue

            required = ["name", "positions", "crimes", "tags", "sources"]
            missing = [field for field in required if field not in data]
            if missing:
                invalid.append((filename, f"Missing fields: {missing}"))
                continue

            if not isinstance(data["name"], str) or not data["name"].strip():
                invalid.append((filename, "Field name must be a non-empty string"))
                continue

            file_errors: list[str] = []
            for field in ("positions", "crimes", "tags", "aliases", "roles"):
                if field in data:
                    file_errors.extend(validate_string_list(data, field))

            sources = data.get("sources", [])
            if not isinstance(sources, list):
                file_errors.append("Field sources must be a list")
            else:
                for index, source in enumerate(sources):
                    file_errors.extend(validate_source(source, index))

            if "needs_research" in data and not isinstance(data["needs_research"], bool):
                file_errors.append("Field needs_research must be true or false")

            if "jurisdiction" in data and (not isinstance(data["jurisdiction"], str) or not data["jurisdiction"].strip()):
                file_errors.append("Field jurisdiction must be a non-empty string")

            if "case_type" in data and data["case_type"] not in CASE_TYPES:
                file_errors.append(f"Field case_type must be one of {sorted(CASE_TYPES)}")

            if "review_status" in data and data["review_status"] not in REVIEW_STATUSES:
                file_errors.append(f"Field review_status must be one of {sorted(REVIEW_STATUSES)}")

            if "confidence" in data and data["confidence"] not in CONFIDENCE_LEVELS:
                file_errors.append(f"Field confidence must be one of {sorted(CONFIDENCE_LEVELS)}")

            if "reviewed_at" in data and (not isinstance(data["reviewed_at"], str) or len(data["reviewed_at"].strip()) < 4):
                file_errors.append("Field reviewed_at must be a non-empty date-like string")

            if file_errors:
                invalid.append((filename, "; ".join(file_errors[:3])))
                continue

            slug = data.get("slug")
            if isinstance(slug, str) and slug.strip() and slug.strip() != filename[:-3]:
                warnings.append((filename, f"Frontmatter slug '{slug.strip()}' does not match filename slug '{filename[:-3]}'"))

            for field in ("positions", "crimes", "tags", "aliases", "roles"):
                if field not in data:
                    continue
                seen = set()
                duplicates = set()
                for item in data[field]:
                    normalized = item.strip().lower()
                    if normalized in seen:
                        duplicates.add(item.strip())
                    else:
                        seen.add(normalized)
                if duplicates:
                    warnings.append((filename, f"Duplicate values in {field}: {sorted(duplicates)}"))

            normalized_source_urls = []
            for source in sources:
                url = source if isinstance(source, str) else source["url"]
                normalized_source_urls.append(normalize_url(url))
            if len(normalized_source_urls) != len(set(normalized_source_urls)):
                warnings.append((filename, "Duplicate source URLs found"))

            valid += 1
        except Exception as exc:
            invalid.append((filename, str(exc)[:120]))

    print(f"Validated {valid}/{len(files)} files successfully")

    if invalid:
        print(f"\nInvalid files ({len(invalid)}):")
        for filename, error in invalid[:10]:
            print(f"  {filename}: {error}")
        if len(invalid) > 10:
            print(f"  ... and {len(invalid) - 10} more")
    else:
        print("All files have valid YAML frontmatter!")

    if warnings:
        print(f"\nWarnings ({len(warnings)}):")
        for filename, warning in warnings[:10]:
            print(f"  {filename}: {warning}")
        if len(warnings) > 10:
            print(f"  ... and {len(warnings) - 10} more")

    return 1 if invalid else 0


if __name__ == "__main__":
    raise SystemExit(main())
