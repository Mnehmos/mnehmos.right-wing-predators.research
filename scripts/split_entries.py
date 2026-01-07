#!/usr/bin/env python3
"""
Entry Splitter Script

Transforms batched markdown files into individual Astro Content Collection entries.

Input:  data/entries-*.md (16 batched files, ~100 entries each)
Output: src/content/entries/*.md (individual files with frontmatter)

Handles TWO input formats:
  Format A: # Name, ## Overview, ### Positions, etc. (structured headings)
  Format B: ## Entry NNN: Name, **Position:**, **Crime:**, etc. (inline bold fields)
"""

import os
import re
import glob
import unicodedata
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

INPUT_GLOB = 'data/entries-*.md'
OUTPUT_DIR = 'src/content/entries'


@dataclass
class ParsedEntry:
    """Represents a parsed entry from the batched markdown files."""
    name: str
    slug: str = ''
    overview: str = ''
    positions: List[str] = field(default_factory=list)
    crimes: List[str] = field(default_factory=list)
    description: str = ''
    sources: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


def generate_slug(name: str) -> str:
    """Generate URL-safe slug from name."""
    # Normalize unicode and remove accents
    normalized = unicodedata.normalize('NFD', name.lower())
    ascii_only = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    # Replace non-alphanumeric with dashes
    slug = re.sub(r'[^a-z0-9]+', '-', ascii_only)
    # Clean up dashes
    slug = re.sub(r'^-+|-+$', '', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug


# ============================================================================
# FORMAT A PARSING (Structured headings: # Name, ## Overview, ### Positions)
# ============================================================================

def extract_section_format_a(raw: str, heading: str) -> str:
    """Extract content under a heading until next heading of same or higher level."""
    escaped = re.escape(heading)
    
    if heading.startswith('###'):
        pattern = escaped + r'\s*\n([\s\S]*?)(?=\n###|\n##|\n#(?!#)|$)'
    elif heading.startswith('##'):
        pattern = escaped + r'\s*\n([\s\S]*?)(?=\n##|\n#(?!#)|$)'
    else:
        pattern = escaped + r'\s*\n([\s\S]*?)(?=\n#|$)'
    
    match = re.search(pattern, raw)
    return match.group(1).strip() if match else ''


def extract_list_format_a(raw: str, heading: str) -> List[str]:
    """Extract list items under a heading."""
    section = extract_section_format_a(raw, heading)
    items = []
    for line in section.split('\n'):
        line = re.sub(r'^[-*]\s*', '', line).strip()
        if line:
            items.append(line)
    return items


def parse_entry_format_a(raw: str) -> Optional[ParsedEntry]:
    """Parse a single entry from Format A (structured headings)."""
    # Extract name from H1
    name_match = re.search(r'^#\s+(.+)$', raw, re.MULTILINE)
    if not name_match:
        return None
    
    name = name_match.group(1).strip()
    overview = extract_section_format_a(raw, '## Overview')
    positions = extract_list_format_a(raw, '### Positions')
    crimes = extract_list_format_a(raw, '### Crimes')
    description = extract_section_format_a(raw, '### Description')
    sources_raw = extract_section_format_a(raw, '### Sources')
    sources = extract_urls(sources_raw)
    tags = extract_list_format_a(raw, '### Tags')
    
    return ParsedEntry(
        name=name,
        overview=overview or (description[:200] + '...' if len(description) > 200 else description) if description else '',
        positions=positions,
        crimes=crimes,
        description=description,
        sources=sources,
        tags=tags,
    )


# ============================================================================
# FORMAT B PARSING (Inline bold fields: ## Entry NNN: Name, **Position:**)
# ============================================================================

def extract_bold_field(raw: str, field_name: str) -> str:
    """Extract content after **FieldName:** on the same line or following lines."""
    # Match **Field:** or **Field** followed by content
    pattern = rf'\*\*{re.escape(field_name)}:?\*\*\s*(.+?)(?=\n\*\*|\n---|\n##|$)'
    match = re.search(pattern, raw, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ''


def extract_bold_list(raw: str, field_name: str) -> List[str]:
    """Extract comma-separated or newline-separated list from bold field."""
    content = extract_bold_field(raw, field_name)
    if not content:
        return []
    
    # Check if it's markdown links (Sources)
    if '[' in content and '](' in content:
        return extract_urls(content)
    
    # Split by comma or newline, handling "- " prefix
    items = []
    for item in re.split(r'[,\n]', content):
        item = re.sub(r'^[-*]\s*', '', item).strip()
        if item and item.lower() not in ['none', 'unknown', 'n/a']:
            items.append(item)
    return items


def parse_entry_format_b(raw: str) -> Optional[ParsedEntry]:
    """Parse a single entry from Format B (inline bold fields)."""
    # Extract name from ## Entry NNN: Name
    name_match = re.search(r'^##\s+Entry\s+\d+:\s*(.+?)(?:\s*$|\s*\n)', raw, re.MULTILINE)
    if not name_match:
        return None
    
    name = name_match.group(1).strip()
    
    # Extract fields using bold pattern
    position_str = extract_bold_field(raw, 'Position')
    crime_str = extract_bold_field(raw, 'Crime')
    
    # Positions and crimes are comma-separated
    positions = [p.strip() for p in re.split(r',\s*', position_str) if p.strip() and p.strip().lower() not in ['unknown', 'none']]
    crimes = [c.strip() for c in re.split(r',\s*', crime_str) if c.strip() and c.strip().lower() not in ['unknown', 'none']]
    
    # Tags can be after **Tags:** label
    tags_str = extract_bold_field(raw, 'Tags')
    tags = [t.strip() for t in re.split(r',\s*', tags_str) if t.strip() and t.strip().lower() not in ['none', 'unknown']]
    
    # Sources - extract URLs
    sources_section = extract_bold_field(raw, 'Sources')
    sources = extract_urls(sources_section)
    
    # Description is the main text between header fields and Sources/Tags
    # Find text after Year line but before **Sources:**
    desc_match = re.search(
        r'\*\*Year:?\*\*[^\n]*\n\n?([\s\S]*?)(?=\*\*Sources|\*\*Tags|---\s*$|$)',
        raw, re.IGNORECASE
    )
    if desc_match:
        description = desc_match.group(1).strip()
    else:
        # Fallback: get text between first paragraph break and **Sources
        desc_match = re.search(
            r'(?:\*\*Crime:?\*\*[^\n]*\n|\*\*Position:?\*\*[^\n]*\n)\n?([\s\S]*?)(?=\*\*Sources|\*\*Tags|---\s*$|$)',
            raw, re.IGNORECASE
        )
        description = desc_match.group(1).strip() if desc_match else ''
    
    # Clean up description - remove **Year:** line if present at start
    description = re.sub(r'^\*\*Year:?\*\*[^\n]*\n*', '', description).strip()
    
    # Overview is first ~200 chars of description
    overview = (description[:200] + '...') if len(description) > 200 else description
    
    return ParsedEntry(
        name=name,
        overview=overview,
        positions=positions,
        crimes=crimes,
        description=description,
        sources=sources,
        tags=tags,
    )


# ============================================================================
# SHARED UTILITIES
# ============================================================================

def extract_urls(markdown: str) -> List[str]:
    """Extract URLs from markdown links and plain URLs."""
    urls = []
    # Markdown links [text](url)
    for match in re.finditer(r'\[([^\]]*)\]\(([^)]+)\)', markdown):
        url = match.group(2).strip()
        if url and url not in urls:
            urls.append(url)
    # Plain URLs not already captured
    for match in re.finditer(r'https?://[^\s\)\]<>]+', markdown):
        url = match.group(0).strip()
        url = url.rstrip('.,;:')
        if url not in urls:
            urls.append(url)
    return urls


def detect_format(raw: str) -> str:
    """Detect which format an entry block uses."""
    # Format A: starts with # Name (H1)
    if re.search(r'^#\s+[^#]', raw, re.MULTILINE):
        return 'A'
    # Format B: starts with ## Entry NNN:
    if re.search(r'^##\s+Entry\s+\d+:', raw, re.MULTILINE):
        return 'B'
    return 'unknown'


def parse_entry(raw: str) -> Optional[ParsedEntry]:
    """Parse a single entry, auto-detecting format."""
    fmt = detect_format(raw)
    if fmt == 'A':
        return parse_entry_format_a(raw)
    elif fmt == 'B':
        return parse_entry_format_b(raw)
    return None


def parse_markdown_file(content: str, filename: str) -> Tuple[List[ParsedEntry], List[str]]:
    """Parse all entries from a batched markdown file."""
    entries = []
    parse_errors = []
    
    # Remove file-level frontmatter (YAML between --- at start)
    content = re.sub(r'^---[\s\S]*?---\n', '', content)
    
    # Also remove file-level H1 title if present (# Title without entry content)
    content = re.sub(r'^#\s+[^\n]+\n+(?=##\s+Entry)', '', content)
    
    # Split by horizontal rule (entry delimiter)
    raw_entries = re.split(r'\n---\n', content)
    
    for i, raw in enumerate(raw_entries):
        raw = raw.strip()
        if not raw:
            continue
        
        # Skip index/footer sections
        if raw.startswith('*Last updated:') or raw.startswith('*End of entries'):
            continue
        
        entry = parse_entry(raw)
        if entry:
            entries.append(entry)
        else:
            preview = raw[:80].replace('\n', ' ')
            parse_errors.append(f"  Entry {i+1}: Could not parse - '{preview}...'")
    
    return entries, parse_errors


def escape_yaml_string(s: str) -> str:
    """Escape a string for YAML, handling quotes and special characters."""
    s = s.replace('\\', '\\\\')
    s = s.replace('"', '\\"')
    return s


def generate_frontmatter(entry: ParsedEntry) -> str:
    """Generate YAML frontmatter for entry."""
    lines = [
        '---',
        f'name: "{escape_yaml_string(entry.name)}"',
        f'slug: "{entry.slug}"',
    ]
    
    if entry.positions:
        lines.append('positions:')
        for p in entry.positions:
            lines.append(f'  - "{escape_yaml_string(p)}"')
    else:
        lines.append('positions: []')
    
    if entry.crimes:
        lines.append('crimes:')
        for c in entry.crimes:
            lines.append(f'  - "{escape_yaml_string(c)}"')
    else:
        lines.append('crimes: []')
    
    if entry.tags:
        lines.append('tags:')
        for t in entry.tags:
            lines.append(f'  - "{escape_yaml_string(t)}"')
    else:
        lines.append('tags: []')
    
    if entry.sources:
        lines.append('sources:')
        for s in entry.sources:
            lines.append(f'  - "{escape_yaml_string(s)}"')
    else:
        lines.append('sources: []')
    
    lines.append('---')
    return '\n'.join(lines)


def generate_body(entry: ParsedEntry) -> str:
    """Generate markdown body for entry."""
    sections = []
    if entry.overview:
        sections.append(f'## Overview\n\n{entry.overview}')
    if entry.description:
        sections.append(f'## Description\n\n{entry.description}')
    return '\n\n'.join(sections)


def main():
    """Main entry point."""
    print("=" * 60)
    print("Entry Splitter Script")
    print("=" * 60)
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"\nOutput directory: {OUTPUT_DIR}")
    
    # Find input files (exclude index file)
    input_files = sorted([f for f in glob.glob(INPUT_GLOB) if 'index' not in f.lower()])
    print(f"Found {len(input_files)} input files")
    
    if not input_files:
        print("ERROR: No input files found matching pattern:", INPUT_GLOB)
        return
    
    all_entries: List[ParsedEntry] = []
    slug_counts: Dict[str, int] = {}
    file_entry_counts = []
    all_parse_errors = []
    
    # Parse all files
    print("\n--- Parsing Files ---")
    for input_file in input_files:
        print(f"Parsing: {input_file}")
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        entries, errors = parse_markdown_file(content, input_file)
        file_entry_counts.append((input_file, len(entries)))
        all_entries.extend(entries)
        
        if errors:
            all_parse_errors.extend([(input_file, e) for e in errors[:3]])  # Limit errors per file
            if len(errors) > 3:
                all_parse_errors.append((input_file, f"  ... and {len(errors) - 3} more issues"))
    
    print(f"\nParsed {len(all_entries)} entries total")
    
    # Assign unique slugs
    print("\n--- Generating Slugs ---")
    for entry in all_entries:
        base_slug = generate_slug(entry.name)
        if not base_slug:
            base_slug = 'unnamed-entry'
        count = slug_counts.get(base_slug, 0)
        slug_counts[base_slug] = count + 1
        entry.slug = base_slug if count == 0 else f'{base_slug}-{count + 1}'
    
    # Write individual files
    print("\n--- Writing Files ---")
    written = 0
    write_errors = []
    
    for entry in all_entries:
        filename = f'{entry.slug}.md'
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        content = '\n'.join([
            generate_frontmatter(entry),
            '',
            generate_body(entry),
        ])
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            written += 1
        except Exception as e:
            write_errors.append(f"  {filename}: {e}")
    
    print(f"Wrote {written} entry files to {OUTPUT_DIR}")
    
    if write_errors:
        print("\nWrite errors:")
        for error in write_errors[:10]:
            print(error)
    
    # Report collisions
    collisions = [(slug, count) for slug, count in slug_counts.items() if count > 1]
    if collisions:
        print(f"\n--- Slug Collisions ({len(collisions)}) ---")
        for slug, count in sorted(collisions, key=lambda x: -x[1])[:20]:
            print(f"  {slug}: {count} entries")
        if len(collisions) > 20:
            print(f"  ... and {len(collisions) - 20} more collisions")
    else:
        print("\nNo slug collisions detected.")
    
    # Report parse errors summary
    if all_parse_errors:
        print(f"\n--- Parse Issues (showing first few per file) ---")
        for filepath, error in all_parse_errors[:15]:
            print(f"  {Path(filepath).name}: {error}")
        if len(all_parse_errors) > 15:
            print(f"  ... and more issues in other files")
    
    # Summary statistics
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Input files processed:  {len(input_files)}")
    print(f"Total entries parsed:   {len(all_entries)}")
    print(f"Files written:          {written}")
    print(f"Slug collisions:        {len(collisions)}")
    
    # Per-file breakdown
    print("\n--- Entries Per File ---")
    for filepath, count in file_entry_counts:
        print(f"  {Path(filepath).name}: {count} entries")
    
    # Validation commands
    print("\n--- Validation Commands ---")
    print(f'  Count files: dir /b "{OUTPUT_DIR}" | find /c /v ""')
    print(f'  Or (PowerShell): (Get-ChildItem "{OUTPUT_DIR}" -Filter *.md).Count')


if __name__ == '__main__':
    main()
