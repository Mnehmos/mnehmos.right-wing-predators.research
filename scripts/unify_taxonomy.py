#!/usr/bin/env python3
"""
Unify the tag/position taxonomy across all entries.

Applied transformations:
  1. Normalize position casing artifacts (e.g. "45Th" -> "45th").
  2. Consolidate synonymous positions (Congressman (IL-19) -> US Representative).
  3. Strip tags that duplicate a position on the same entry (case-insensitive).
  4. Normalize tag casing to lowercase.

Usage:
  python scripts/unify_taxonomy.py --dry-run
  python scripts/unify_taxonomy.py --apply
"""

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
ENTRIES_DIR = REPO_ROOT / "src" / "content" / "entries"


# --- Position consolidation rules ---
# Mapping from case-insensitive pattern -> canonical position.
# First match wins.
POSITION_ALIASES = [
    # Federal legislative
    (re.compile(r"^congressman\s*\(.*\)$", re.I), "US Representative"),
    (re.compile(r"^us representative$", re.I), "US Representative"),
    (re.compile(r"^congress$", re.I), "US Representative"),
    # Executive
    (re.compile(r"^president\s*\(.*?\)$", re.I), "President"),
    (re.compile(r"^president$", re.I), "President"),
    # Casing fix for "45Th" artifact
    (re.compile(r"\b(\d+)Th\b"), lambda m: f"{m.group(1)}th"),
    # Federal judge vs judge — keep "Federal Judge" distinct from local "Judge"
    # Media
    (re.compile(r"^media personality$", re.I), "Media Figure"),
    (re.compile(r"^commentator$", re.I), "Media Figure"),
    # Teacher/Educator
    (re.compile(r"^teacher$", re.I), "Educator"),
    # Church roles — keep Religious Leader as umbrella; Youth Pastor stays for specificity
    (re.compile(r"^church leader$", re.I), "Religious Leader"),
    (re.compile(r"^church official$", re.I), "Religious Leader"),
    (re.compile(r"^student minister$", re.I), "Religious Leader"),
    (re.compile(r"^music director$", re.I), "Religious Leader"),
    (re.compile(r"^religious counselor$", re.I), "Religious Leader"),
    (re.compile(r"^methodist$", re.I), "Religious Leader"),
    (re.compile(r"^baptist$", re.I), "Religious Leader"),
    (re.compile(r"^southern baptist$", re.I), "Religious Leader"),
    (re.compile(r"^flds offshoot leader$", re.I), "Religious Leader"),
    (re.compile(r"^self-proclaimed prophet$", re.I), "Religious Leader"),
    # Business
    (re.compile(r"^businessman$", re.I), "Business Owner"),
    # Extremist
    (re.compile(r"^extremist leader$", re.I), "Extremist"),
    (re.compile(r"^extremist/militia$", re.I), "Extremist"),
    (re.compile(r"^neo-nazi$", re.I), "White Nationalist"),
    (re.compile(r"^national vanguard founder$", re.I), "White Nationalist"),
    # Trump administration — add also as ideology tag
    # "Trump Administration" stays as-is
    # Party member cleanup
    (re.compile(r"^republican party member$", re.I), "Party Member"),
]


def canonicalize_position(p: str) -> str:
    p = p.strip()
    for pat, repl in POSITION_ALIASES:
        if callable(repl):
            new = pat.sub(repl, p)
            if new != p:
                return new
        else:
            if pat.search(p):
                return repl
    return p


def dedupe_preserve(items, key=None):
    seen = set()
    out = []
    for item in items:
        k = key(item) if key else item
        if k in seen:
            continue
        seen.add(k)
        out.append(item)
    return out


def yaml_quote(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def dump_fm(data: dict) -> str:
    key_order = ["name", "slug", "positions", "crimes", "tags", "sources", "needs_research"]
    lines = []
    for key in key_order:
        if key not in data:
            continue
        val = data[key]
        if isinstance(val, bool):
            lines.append(f"{key}: {'true' if val else 'false'}")
        elif isinstance(val, list):
            if not val:
                lines.append(f"{key}: []")
            else:
                lines.append(f"{key}:")
                for item in val:
                    lines.append(f"  - {yaml_quote(str(item))}")
        elif isinstance(val, str):
            lines.append(f"{key}: {yaml_quote(val)}")
        else:
            lines.append(f"{key}: {val}")
    return "\n".join(lines)


def process_entry(path: Path, apply: bool) -> dict | None:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not m:
        return {"path": path.name, "error": "no frontmatter"}
    data = yaml.safe_load(m.group(1)) or {}
    body = m.group(2)
    changes = []

    # 1. Canonicalize positions
    positions = data.get("positions", []) or []
    new_positions = [canonicalize_position(p) for p in positions]
    new_positions = dedupe_preserve(new_positions, key=lambda s: s.lower())
    if new_positions != positions:
        changes.append(f"positions: {positions} -> {new_positions}")

    # 2. Strip tags that duplicate any position on this entry (case-insensitive)
    tags = data.get("tags", []) or []
    position_lower = {p.lower() for p in new_positions}
    stripped_tags = [t for t in tags if t.lower() not in position_lower]
    # Lowercase + dedupe
    normalized_tags = dedupe_preserve(
        [t.strip().lower() for t in stripped_tags if t.strip()],
    )
    if normalized_tags != tags:
        changes.append(f"tags: {tags} -> {normalized_tags}")

    if not changes:
        return None

    if apply:
        data["positions"] = new_positions
        data["tags"] = normalized_tags
        new_text = f"---\n{dump_fm(data)}\n---\n{body}"
        path.write_text(new_text, encoding="utf-8", newline="\n")

    return {"path": path.name, "changes": changes}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    apply = args.apply
    mode = "APPLY" if apply else "DRY-RUN"
    print(f"Running in {mode} mode.")

    changed = 0
    errors = 0
    change_counter = Counter()
    samples = []
    for path in sorted(ENTRIES_DIR.glob("*.md")):
        result = process_entry(path, apply=apply)
        if result is None:
            continue
        if "error" in result:
            errors += 1
            continue
        changed += 1
        for c in result["changes"]:
            change_counter[c.split(":", 1)[0]] += 1
        if len(samples) < 10:
            samples.append(result)

    print(f"\n=== Summary ({mode}) ===")
    print(f"Files with changes: {changed}")
    print(f"Errors: {errors}")
    print("Change types:")
    for key, count in change_counter.most_common():
        print(f"  {key}: {count}")
    if not apply and changed > 0:
        print("\nSample:")
        for s in samples:
            print(f"  {s['path']}:")
            for c in s["changes"]:
                print(f"    - {c}")


if __name__ == "__main__":
    main()
