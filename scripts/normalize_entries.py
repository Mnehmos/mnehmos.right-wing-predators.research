#!/usr/bin/env python3
"""
Normalize & flag entries in src/content/entries/*.md.

Modes:
  --dry-run         Report all proposed changes, write nothing. (default)
  --apply           Rewrite frontmatter in place. Body is preserved byte-for-byte.
  --find-dupes      Emit scripts/merge-candidates.json for manual review.
                    Does NOT auto-merge — merges are irreversible and need a human.
  --flag-sparse     Tag entries with 0 sources or body < 100 chars as needs_research: true.

Examples:
  python scripts/normalize_entries.py --dry-run
  python scripts/normalize_entries.py --apply --flag-sparse
  python scripts/normalize_entries.py --find-dupes
"""

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
ENTRIES_DIR = REPO_ROOT / "src" / "content" / "entries"
OUTPUT_DIR = REPO_ROOT / "scripts"

ACRONYMS = {
    "cia",
    "dc",
    "dhs",
    "doj",
    "fbi",
    "gop",
    "la",
    "nsa",
    "ny",
    "nyc",
    "usa",
    "us",
}


def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)


def split_frontmatter(text: str):
    """Return (frontmatter_text, body_text) or (None, None) if no frontmatter."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None, None
    return m.group(1), m.group(2)


def parse_frontmatter(fm_text: str) -> dict:
    """Parse YAML frontmatter using PyYAML for correctness."""
    return yaml.safe_load(fm_text) or {}


def dump_frontmatter(data: dict, key_order: list) -> str:
    """Emit YAML frontmatter preserving key order.

    String VALUES (not keys) are double-quoted to match the repo's existing
    style. Lists are block-style with 2-space indent.
    """
    ordered = {k: data[k] for k in key_order if k in data}

    # Build YAML manually — simpler than wrangling PyYAML's representer dispatch
    # to distinguish keys from values. This project's frontmatter shape is
    # predictable: scalar strings, boolean flag, and string arrays.
    lines = []
    for key, val in ordered.items():
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


def yaml_quote(s: str) -> str:
    """Produce a double-quoted YAML string with proper escaping.

    YAML double-quoted strings: `\\` for literal backslash, `\"` for literal quote.
    """
    escaped = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def normalize_titleish(s: str) -> str:
    """Normalize human-readable labels without destroying canonical acronyms."""
    s = re.sub(r"\s+", " ", s.strip())
    if not s:
        return s

    letters_only = re.sub(r"[^A-Za-z]+", "", s)
    should_recase = bool(letters_only) and (letters_only.islower() or letters_only.isupper())
    if not should_recase:
        return s

    def normalize_chunk(chunk: str) -> str:
        lower = chunk.lower()
        if lower in ACRONYMS:
            return lower.upper()
        ordinal = re.fullmatch(r"(\d+)(st|nd|rd|th)", lower)
        if ordinal:
            return f"{ordinal.group(1)}{ordinal.group(2)}"
        return chunk[:1].upper() + chunk[1:].lower()

    def normalize_token(token: str) -> str:
        parts = re.split(r"([-/])", token)
        return "".join(
            part if part in "-/" else normalize_chunk(part)
            for part in parts
        )

    tokens = s.split(" ")
    return " ".join(
        normalize_token(token)
        for token in tokens
    )


def normalize_position(s: str) -> str:
    return normalize_titleish(s)


def normalize_crime(s: str) -> str:
    return normalize_titleish(s)


def normalize_tag(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip()).lower() if s.strip() else s.strip()


def dedupe(items, normalizer):
    """Case-insensitive dedupe preserving first-seen normalized form."""
    seen = {}
    for item in items:
        norm = normalizer(item)
        if not norm:
            continue
        key = norm.lower()
        if key not in seen:
            seen[key] = norm
    return list(seen.values())


def normalize_entry(data: dict) -> tuple[dict, list]:
    """Return (new_data, change_notes). Non-destructive — ignores unknown fields."""
    changes = []
    new = dict(data)

    for key, normalizer in (
        ("positions", normalize_position),
        ("crimes", normalize_crime),
        ("tags", normalize_tag),
    ):
        original = data.get(key, []) or []
        new_values = dedupe(original, normalizer)
        if new_values != original:
            changes.append(f"{key}: {original} -> {new_values}")
        new[key] = new_values

    # Trim sources.
    sources = [s.strip() for s in (data.get("sources", []) or []) if s.strip()]
    if sources != data.get("sources", []):
        changes.append(f"sources trimmed ({len(sources)} entries)")
    new["sources"] = sources

    # Trim name.
    name = (data.get("name") or "").strip()
    if name != data.get("name"):
        changes.append(f"name: {data.get('name')!r} -> {name!r}")
    new["name"] = name

    return new, changes


def body_length(body: str) -> int:
    # Strip markdown headings and collapse whitespace for a fair length estimate.
    text = re.sub(r"^#{1,6}\s.*$", "", body, flags=re.MULTILINE)
    text = re.sub(r"\s+", " ", text).strip()
    return len(text)


def should_flag_sparse(data: dict, body: str) -> bool:
    sources = data.get("sources", []) or []
    return len(sources) == 0 or body_length(body) < 100


def process_entry(path: Path, apply: bool, flag_sparse: bool) -> dict | None:
    text = read_file(path)
    fm_text, body = split_frontmatter(text)
    if fm_text is None:
        return {"path": str(path), "error": "no frontmatter"}

    data = parse_frontmatter(fm_text)
    new_data, changes = normalize_entry(data)

    sparse_now = should_flag_sparse(new_data, body)
    if flag_sparse:
        current_flag = bool(new_data.get("needs_research"))
        if sparse_now and not current_flag:
            new_data["needs_research"] = True
            changes.append("needs_research: true (sparse)")
        elif not sparse_now and current_flag:
            # Un-flag if entry is no longer sparse.
            new_data.pop("needs_research", None)
            changes.append("needs_research removed (no longer sparse)")

    if not changes:
        return None

    if apply:
        key_order = ["name", "slug", "positions", "crimes", "tags", "sources", "needs_research"]
        new_fm = dump_frontmatter(new_data, key_order)
        write_file(path, f"---\n{new_fm}\n---\n{body}")

    return {"path": path.name, "changes": changes}


def find_duplicates() -> list[dict]:
    """Find near-duplicate entries for manual merge review.

    Heuristics:
      - Strong name similarity (SequenceMatcher ratio) >= 0.94
      - OR slug similarity >= 0.97 AND name similarity >= 0.88
      - OR name similarity >= 0.88 AND Jaccard overlap on (crimes + positions) >= 0.8
    """
    print("Scanning entries for merge candidates...", file=sys.stderr)
    entries = []
    for path in sorted(ENTRIES_DIR.glob("*.md")):
        text = read_file(path)
        fm_text, body = split_frontmatter(text)
        if fm_text is None:
            continue
        data = parse_frontmatter(fm_text)
        entries.append({
            "slug": path.stem,
            "path": path.name,
            "name": (data.get("name") or "").strip(),
            "name_lower": (data.get("name") or "").strip().lower(),
            "positions": [normalize_position(p) for p in (data.get("positions") or [])],
            "crimes": [normalize_crime(c) for c in (data.get("crimes") or [])],
            "source_count": len(data.get("sources") or []),
        })

    # Bucket by first word of name for O(n*k) comparisons instead of O(n^2).
    buckets = defaultdict(list)
    for e in entries:
        first_word = e["name_lower"].split()[0] if e["name_lower"] else ""
        if first_word:
            buckets[first_word].append(e)

    candidates = []
    seen_pairs = set()
    for first_word, bucket in buckets.items():
        if len(bucket) < 2:
            continue
        for i, a in enumerate(bucket):
            for b in bucket[i + 1 :]:
                pair_key = tuple(sorted([a["slug"], b["slug"]]))
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                name_ratio = SequenceMatcher(None, a["name_lower"], b["name_lower"]).ratio()
                slug_ratio = SequenceMatcher(None, a["slug"], b["slug"]).ratio()

                a_set = set(a["positions"] + a["crimes"])
                b_set = set(b["positions"] + b["crimes"])
                jaccard = (
                    len(a_set & b_set) / len(a_set | b_set) if (a_set | b_set) else 0.0
                )

                score = 0.0
                reasons = []
                if name_ratio >= 0.94:
                    score = max(score, name_ratio)
                    reasons.append(f"name similarity {name_ratio:.2f}")
                if slug_ratio >= 0.97 and name_ratio >= 0.88:
                    score = max(score, slug_ratio)
                    reasons.append(f"slug similarity {slug_ratio:.2f}")
                if jaccard >= 0.8 and name_ratio >= 0.88:
                    score = max(score, jaccard)
                    reasons.append(f"crimes+positions jaccard {jaccard:.2f}")

                if score > 0:
                    candidates.append({
                        "score": round(score, 3),
                        "reasons": reasons,
                        "a": {"slug": a["slug"], "name": a["name"], "source_count": a["source_count"]},
                        "b": {"slug": b["slug"], "name": b["name"], "source_count": b["source_count"]},
                    })

    candidates.sort(key=lambda c: -c["score"])
    return candidates


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="Rewrite frontmatter in place")
    parser.add_argument("--dry-run", action="store_true", help="Report changes only (default)")
    parser.add_argument("--find-dupes", action="store_true", help="Emit merge candidates")
    parser.add_argument("--flag-sparse", action="store_true", help="Set needs_research on sparse entries")
    args = parser.parse_args()

    if not ENTRIES_DIR.exists():
        print(f"ERROR: Entries directory not found: {ENTRIES_DIR}", file=sys.stderr)
        sys.exit(1)

    if args.find_dupes:
        candidates = find_duplicates()
        out_path = OUTPUT_DIR / "merge-candidates.json"
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(candidates, indent=2), encoding="utf-8")
        print(f"Wrote {len(candidates)} merge candidates to {out_path}")
        print("Review manually — this script does not auto-merge.")
        return

    apply = args.apply
    mode = "APPLY" if apply else "DRY-RUN"
    flag_sparse = args.flag_sparse
    print(f"Running in {mode} mode. flag_sparse={flag_sparse}")

    changed = 0
    errors = 0
    change_counter = Counter()
    all_changes = []
    for path in sorted(ENTRIES_DIR.glob("*.md")):
        result = process_entry(path, apply=apply, flag_sparse=flag_sparse)
        if result is None:
            continue
        if "error" in result:
            errors += 1
            print(f"  ERROR {result['path']}: {result['error']}", file=sys.stderr)
            continue
        changed += 1
        for c in result["changes"]:
            key = c.split(":", 1)[0]
            change_counter[key] += 1
        all_changes.append(result)

    print(f"\n=== Summary ({mode}) ===")
    print(f"Total files: {len(list(ENTRIES_DIR.glob('*.md')))}")
    print(f"Files with changes: {changed}")
    print(f"Errors: {errors}")
    print("Change types:")
    for key, count in change_counter.most_common():
        print(f"  {key}: {count}")

    if not apply and changed > 0:
        print("\nSample of changes (first 10 files):")
        for r in all_changes[:10]:
            print(f"  {r['path']}:")
            for c in r["changes"][:5]:
                print(f"    - {c}")
        print("\nRe-run with --apply to write changes.")


if __name__ == "__main__":
    main()
