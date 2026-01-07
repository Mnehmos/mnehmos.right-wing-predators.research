# Entry Splitter Script Specification

**Purpose**: Transform batched markdown files into individual Astro Content Collection entries.

## Overview

```
Input:  data/entries-*.md (16 batched files, ~100 entries each)
Output: src/content/entries/*.md (1,506 individual files with frontmatter)
```

## Input Format Analysis

Each batched markdown file follows this structure:

```markdown
---
title: Republican Sexual Misconduct Database - Entries X-Y
description: ...
---

# Person Name

## Overview
Brief summary paragraph...

## Details

### Positions
- Position 1
- Position 2

### Crimes
- Crime 1
- Crime 2

### Description
Full description text...

### Sources
- [Link text](url)
- [Link text](url)

### Tags
- Tag 1
- Tag 2


---

# Next Person Name
...
```

### Parsing Rules

1. **Entry Delimiter**: `---` on its own line (horizontal rule between entries)
2. **Entry Start**: `# {Name}` (H1 heading marks new entry)
3. **File Header**: First `---` block is YAML frontmatter for the file itself (skip)
4. **Section Markers**:
   - `## Overview` → overview text
   - `### Positions` → list of positions
   - `### Crimes` → list of crimes  
   - `### Description` → full description
   - `### Sources` → list of URLs (extract from markdown links)
   - `### Tags` → list of tags

## Output Format

Each individual file should have:

```markdown
---
name: "Person Full Name"
slug: "person-full-name"
positions:
  - "Position 1"
  - "Position 2"
crimes:
  - "Crime 1"
  - "Crime 2"
tags:
  - "Tag 1"
  - "Tag 2"
sources:
  - "https://example.com/source1"
  - "https://example.com/source2"
---

## Overview

Brief summary paragraph...

## Description

Full description text...
```

## Slug Generation

```typescript
function generateSlug(name: string): string {
  return name
    .toLowerCase()
    .normalize('NFD')                    // Decompose accents
    .replace(/[\u0300-\u036f]/g, '')     // Remove accent marks
    .replace(/[^a-z0-9]+/g, '-')         // Replace non-alphanumeric with dash
    .replace(/^-+|-+$/g, '')             // Trim leading/trailing dashes
    .replace(/-+/g, '-');                // Collapse multiple dashes
}

// Examples:
// "Donald Trump" → "donald-trump"
// "Dr. W. David Hager" → "dr-w-david-hager"
// "NYC Republican-Queens, Dennis Gallagher" → "nyc-republican-queens-dennis-gallagher"
// "Earl \"Butch\" Kimmerling" → "earl-butch-kimmerling"
```

## Collision Handling

If two entries generate the same slug:

```typescript
const slugCounts = new Map<string, number>();

function getUniqueSlug(baseName: string): string {
  const baseSlug = generateSlug(baseName);
  const count = slugCounts.get(baseSlug) || 0;
  slugCounts.set(baseSlug, count + 1);
  
  if (count === 0) {
    return baseSlug;
  }
  return `${baseSlug}-${count + 1}`;
}
```

## Implementation (TypeScript/Node.js)

```typescript
// scripts/split-entries.ts

import * as fs from 'fs';
import * as path from 'path';
import * as glob from 'glob';

interface ParsedEntry {
  name: string;
  slug: string;
  overview: string;
  positions: string[];
  crimes: string[];
  description: string;
  sources: string[];
  tags: string[];
}

const INPUT_GLOB = 'data/entries-*.md';
const OUTPUT_DIR = 'src/content/entries';

function parseMarkdownFile(content: string): ParsedEntry[] {
  const entries: ParsedEntry[] = [];
  
  // Remove file-level frontmatter
  const withoutFrontmatter = content.replace(/^---[\s\S]*?---\n/, '');
  
  // Split by horizontal rule (entry delimiter)
  const rawEntries = withoutFrontmatter.split(/\n---\n/).filter(e => e.trim());
  
  for (const rawEntry of rawEntries) {
    const entry = parseEntry(rawEntry);
    if (entry) {
      entries.push(entry);
    }
  }
  
  return entries;
}

function parseEntry(raw: string): ParsedEntry | null {
  // Extract name from H1
  const nameMatch = raw.match(/^#\s+(.+)$/m);
  if (!nameMatch) return null;
  
  const name = nameMatch[1].trim();
  
  // Extract sections
  const overview = extractSection(raw, '## Overview');
  const positions = extractList(raw, '### Positions');
  const crimes = extractList(raw, '### Crimes');
  const description = extractSection(raw, '### Description');
  const sourcesRaw = extractSection(raw, '### Sources');
  const tags = extractList(raw, '### Tags');
  
  // Parse source URLs from markdown links
  const sources = extractUrls(sourcesRaw);
  
  return {
    name,
    slug: '', // Will be set with collision handling
    overview: overview || description?.substring(0, 200) || '',
    positions,
    crimes,
    description: description || '',
    sources,
    tags,
  };
}

function extractSection(raw: string, heading: string): string {
  const regex = new RegExp(`${escapeRegex(heading)}\\s*\\n([\\s\\S]*?)(?=\\n##|\\n###|$)`);
  const match = raw.match(regex);
  return match ? match[1].trim() : '';
}

function extractList(raw: string, heading: string): string[] {
  const section = extractSection(raw, heading);
  return section
    .split('\n')
    .map(line => line.replace(/^[-*]\s*/, '').trim())
    .filter(line => line.length > 0);
}

function extractUrls(markdown: string): string[] {
  const urlRegex = /\[([^\]]*)\]\(([^)]+)\)/g;
  const plainUrlRegex = /https?:\/\/[^\s\)]+/g;
  
  const urls: string[] = [];
  
  // Extract from markdown links
  let match;
  while ((match = urlRegex.exec(markdown)) !== null) {
    urls.push(match[2]);
  }
  
  // Extract plain URLs
  while ((match = plainUrlRegex.exec(markdown)) !== null) {
    if (!urls.includes(match[0])) {
      urls.push(match[0]);
    }
  }
  
  return urls;
}

function escapeRegex(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function generateSlug(name: string): string {
  return name
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .replace(/-+/g, '-');
}

function generateFrontmatter(entry: ParsedEntry): string {
  const yaml = [
    '---',
    `name: "${entry.name.replace(/"/g, '\\"')}"`,
    `slug: "${entry.slug}"`,
  ];
  
  if (entry.positions.length > 0) {
    yaml.push('positions:');
    entry.positions.forEach(p => yaml.push(`  - "${p.replace(/"/g, '\\"')}"`));
  } else {
    yaml.push('positions: []');
  }
  
  if (entry.crimes.length > 0) {
    yaml.push('crimes:');
    entry.crimes.forEach(c => yaml.push(`  - "${c.replace(/"/g, '\\"')}"`));
  } else {
    yaml.push('crimes: []');
  }
  
  if (entry.tags.length > 0) {
    yaml.push('tags:');
    entry.tags.forEach(t => yaml.push(`  - "${t.replace(/"/g, '\\"')}"`));
  } else {
    yaml.push('tags: []');
  }
  
  if (entry.sources.length > 0) {
    yaml.push('sources:');
    entry.sources.forEach(s => yaml.push(`  - "${s}"`));
  } else {
    yaml.push('sources: []');
  }
  
  yaml.push('---');
  
  return yaml.join('\n');
}

function generateMarkdownBody(entry: ParsedEntry): string {
  const sections: string[] = [];
  
  if (entry.overview) {
    sections.push(`## Overview\n\n${entry.overview}`);
  }
  
  if (entry.description) {
    sections.push(`## Description\n\n${entry.description}`);
  }
  
  return sections.join('\n\n');
}

async function main() {
  // Ensure output directory exists
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  
  // Find all input files
  const inputFiles = glob.sync(INPUT_GLOB);
  console.log(`Found ${inputFiles.length} input files`);
  
  const allEntries: ParsedEntry[] = [];
  const slugCounts = new Map<string, number>();
  
  // Parse all files
  for (const inputFile of inputFiles) {
    console.log(`Parsing: ${inputFile}`);
    const content = fs.readFileSync(inputFile, 'utf-8');
    const entries = parseMarkdownFile(content);
    allEntries.push(...entries);
  }
  
  console.log(`Parsed ${allEntries.length} entries total`);
  
  // Assign unique slugs
  for (const entry of allEntries) {
    const baseSlug = generateSlug(entry.name);
    const count = slugCounts.get(baseSlug) || 0;
    slugCounts.set(baseSlug, count + 1);
    
    entry.slug = count === 0 ? baseSlug : `${baseSlug}-${count + 1}`;
  }
  
  // Write individual files
  let written = 0;
  for (const entry of allEntries) {
    const filename = `${entry.slug}.md`;
    const filepath = path.join(OUTPUT_DIR, filename);
    
    const content = [
      generateFrontmatter(entry),
      '',
      generateMarkdownBody(entry),
    ].join('\n');
    
    fs.writeFileSync(filepath, content, 'utf-8');
    written++;
  }
  
  console.log(`Wrote ${written} entry files to ${OUTPUT_DIR}`);
  
  // Report slug collisions
  const collisions = Array.from(slugCounts.entries())
    .filter(([_, count]) => count > 1);
  
  if (collisions.length > 0) {
    console.log('\nSlug collisions detected:');
    collisions.forEach(([slug, count]) => {
      console.log(`  ${slug}: ${count} entries`);
    });
  }
}

main().catch(console.error);
```

## Alternative: Python Implementation

```python
#!/usr/bin/env python3
# scripts/split_entries.py

import os
import re
import glob
import unicodedata
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field

INPUT_GLOB = 'data/entries-*.md'
OUTPUT_DIR = 'src/content/entries'

@dataclass
class ParsedEntry:
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

def extract_section(raw: str, heading: str) -> str:
    """Extract content under a heading until next heading."""
    pattern = re.escape(heading) + r'\s*\n([\s\S]*?)(?=\n##|\n###|$)'
    match = re.search(pattern, raw)
    return match.group(1).strip() if match else ''

def extract_list(raw: str, heading: str) -> List[str]:
    """Extract list items under a heading."""
    section = extract_section(raw, heading)
    items = []
    for line in section.split('\n'):
        line = re.sub(r'^[-*]\s*', '', line).strip()
        if line:
            items.append(line)
    return items

def extract_urls(markdown: str) -> List[str]:
    """Extract URLs from markdown links and plain URLs."""
    urls = []
    # Markdown links
    for match in re.finditer(r'\[([^\]]*)\]\(([^)]+)\)', markdown):
        urls.append(match.group(2))
    # Plain URLs
    for match in re.finditer(r'https?://[^\s\)]+', markdown):
        if match.group(0) not in urls:
            urls.append(match.group(0))
    return urls

def parse_entry(raw: str) -> Optional[ParsedEntry]:
    """Parse a single entry from raw markdown."""
    # Extract name from H1
    name_match = re.search(r'^#\s+(.+)$', raw, re.MULTILINE)
    if not name_match:
        return None
    
    name = name_match.group(1).strip()
    overview = extract_section(raw, '## Overview')
    positions = extract_list(raw, '### Positions')
    crimes = extract_list(raw, '### Crimes')
    description = extract_section(raw, '### Description')
    sources_raw = extract_section(raw, '### Sources')
    tags = extract_list(raw, '### Tags')
    sources = extract_urls(sources_raw)
    
    return ParsedEntry(
        name=name,
        overview=overview or (description[:200] if description else ''),
        positions=positions,
        crimes=crimes,
        description=description,
        sources=sources,
        tags=tags,
    )

def parse_markdown_file(content: str) -> List[ParsedEntry]:
    """Parse all entries from a batched markdown file."""
    # Remove file-level frontmatter
    content = re.sub(r'^---[\s\S]*?---\n', '', content)
    
    # Split by horizontal rule
    raw_entries = re.split(r'\n---\n', content)
    
    entries = []
    for raw in raw_entries:
        if raw.strip():
            entry = parse_entry(raw)
            if entry:
                entries.append(entry)
    
    return entries

def generate_frontmatter(entry: ParsedEntry) -> str:
    """Generate YAML frontmatter for entry."""
    def escape_yaml(s: str) -> str:
        return s.replace('"', '\\"')
    
    lines = [
        '---',
        f'name: "{escape_yaml(entry.name)}"',
        f'slug: "{entry.slug}"',
    ]
    
    lines.append('positions:' if entry.positions else 'positions: []')
    for p in entry.positions:
        lines.append(f'  - "{escape_yaml(p)}"')
    
    lines.append('crimes:' if entry.crimes else 'crimes: []')
    for c in entry.crimes:
        lines.append(f'  - "{escape_yaml(c)}"')
    
    lines.append('tags:' if entry.tags else 'tags: []')
    for t in entry.tags:
        lines.append(f'  - "{escape_yaml(t)}"')
    
    lines.append('sources:' if entry.sources else 'sources: []')
    for s in entry.sources:
        lines.append(f'  - "{s}"')
    
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
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Find input files
    input_files = sorted(glob.glob(INPUT_GLOB))
    print(f'Found {len(input_files)} input files')
    
    all_entries: List[ParsedEntry] = []
    slug_counts: Dict[str, int] = {}
    
    # Parse all files
    for input_file in input_files:
        print(f'Parsing: {input_file}')
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        entries = parse_markdown_file(content)
        all_entries.extend(entries)
    
    print(f'Parsed {len(all_entries)} entries total')
    
    # Assign unique slugs
    for entry in all_entries:
        base_slug = generate_slug(entry.name)
        count = slug_counts.get(base_slug, 0)
        slug_counts[base_slug] = count + 1
        entry.slug = base_slug if count == 0 else f'{base_slug}-{count + 1}'
    
    # Write individual files
    written = 0
    for entry in all_entries:
        filename = f'{entry.slug}.md'
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        content = '\n'.join([
            generate_frontmatter(entry),
            '',
            generate_body(entry),
        ])
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        written += 1
    
    print(f'Wrote {written} entry files to {OUTPUT_DIR}')
    
    # Report collisions
    collisions = [(slug, count) for slug, count in slug_counts.items() if count > 1]
    if collisions:
        print('\nSlug collisions detected:')
        for slug, count in collisions:
            print(f'  {slug}: {count} entries')

if __name__ == '__main__':
    main()
```

## Running the Script

### TypeScript
```bash
cd republican-misconduct-db
npm install glob
npx ts-node scripts/split-entries.ts
```

### Python
```bash
python scripts/split_entries.py
```

## Expected Output

```
Found 16 input files
Parsing: data/entries-001-100.md
Parsing: data/entries-094-193.md
...
Parsed 1506 entries total
Wrote 1506 entry files to src/content/entries

Slug collisions detected:
  roy-moore: 2 entries
  edison-misla-aldarondo: 2 entries
```

## Validation

After running, verify:

1. File count matches expected: `ls src/content/entries/*.md | wc -l`
2. Frontmatter is valid YAML: Use a YAML linter
3. Astro build succeeds: `npm run build`
4. No duplicate slugs in filenames
