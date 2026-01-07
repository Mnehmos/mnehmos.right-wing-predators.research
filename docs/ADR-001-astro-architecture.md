# ADR-001: Astro App Architecture for Republican Sexual Misconduct Database

**Status**: Proposed  
**Date**: 2026-01-07  
**Deciders**: Architecture Team  

## Context

We need to build a public-facing web application to present **1,506 documented entries** of Republican-affiliated individuals accused of sexual misconduct. The data currently exists in:

- **16 markdown files** (`data/entries-*.md`) - well-structured, ~100 entries each
- **16 JSON files** (`data/data-*.json`) - inconsistent formatting, duplicates

### Requirements

1. **Sharp, Functional UI** - Modern, professional, accessible
2. **Search & Filter** - Full-text search + filtering by crime, position, tag, year
3. **Individual Entry Pages** - SEO-friendly URLs for each person
4. **Performance** - Handle 1,500+ entries efficiently
5. **SEO-friendly** - Static generation for maximum discoverability

### Constraints

- Markdown files are the canonical, well-formatted source
- Must handle sensitive content professionally
- Build time should remain reasonable (~minutes, not hours)

---

## Decision 1: Content Strategy

### Decision: Markdown as Source → Individual Content Collection Files

**Choice**: Transform batched markdown files into individual `.md` files at build time using a preprocessing script.

### Rationale

| Option | Pros | Cons |
|--------|------|------|
| **A: Individual .md files** ✓ | Clean routing, git-trackable, Astro Content Collections native | Requires transformation script |
| B: Parse batched at build | Fewer source files | Complex parsing, no individual git history |
| C: JSON source | Programmatic access | Poor formatting, duplicates, less human-readable |

The markdown files were specifically transcribed for this purpose and are well-structured. A one-time transformation script creates individual files that:
- Work natively with Astro Content Collections
- Enable individual page generation
- Support frontmatter-based filtering
- Allow granular git tracking of changes

### Implementation

```
data/entries-*.md (batched) 
    ↓ [scripts/split-entries.ts]
src/content/entries/*.md (individual)
```

---

## Decision 2: Content Schema

### Decision: Typed Frontmatter with Zod Validation

Each individual entry file will have:

```markdown
---
id: string (slug)
name: string
positions: string[]
crimes: string[]
year: number | null
tags: string[]
sources: string[]
---

## Overview
[Brief summary extracted from first paragraph]

## Description
[Full description]
```

### Schema Definition (src/content/config.ts)

```typescript
import { defineCollection, z } from 'astro:content';

const entries = defineCollection({
  type: 'content',
  schema: z.object({
    id: z.string(),
    name: z.string(),
    positions: z.array(z.string()).default([]),
    crimes: z.array(z.string()).default([]),
    year: z.number().nullable().default(null),
    tags: z.array(z.string()).default([]),
    sources: z.array(z.string()).default([]),
  }),
});

export const collections = { entries };
```

---

## Decision 3: Routing Architecture

### Decision: Static Generation with Dynamic Routing

| Route | Purpose | Generation |
|-------|---------|------------|
| `/` | Landing page with stats | Static |
| `/entries` | Browse/search all entries | Static + Client hydration |
| `/entries/[slug]` | Individual entry page | Static (getStaticPaths) |
| `/crimes/[crime]` | Entries filtered by crime type | Static |
| `/positions/[position]` | Entries filtered by position | Static |
| `/years/[year]` | Timeline view by year | Static |
| `/about` | About the project | Static |

### URL Slug Generation

```typescript
// Generate URL-safe slug from name
function generateSlug(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
}
// "Donald Trump" → "donald-trump"
// "Dr. W. David Hager" → "dr-w-david-hager"
```

---

## Decision 4: Search Implementation

### Decision: Pagefind + Client-Side Filtering

**Primary Search**: [Pagefind](https://pagefind.app/) - Build-time indexed search
- Zero-runtime JavaScript for static search
- Automatic index generation from HTML
- Excellent performance with large datasets
- Supports weighted fields, filtering

**Filtering**: Client-side with minimal JavaScript
- Astro Islands for interactive filter components
- Precomputed filter options from build data

### Implementation

```typescript
// astro.config.mjs
import pagefind from 'astro-pagefind';

export default defineConfig({
  integrations: [pagefind()],
  build: {
    format: 'directory',
  },
});
```

### Data Attributes for Pagefind

```html
<article data-pagefind-body>
  <h1 data-pagefind-meta="title">{{ name }}</h1>
  <div data-pagefind-filter="crime">{{ crimes.join(', ') }}</div>
  <div data-pagefind-filter="position">{{ positions.join(', ') }}</div>
  <div data-pagefind-filter="year">{{ year }}</div>
</article>
```

---

## Decision 5: UI Framework

### Decision: Astro + Tailwind CSS + Custom Components

**Stack**:
- **Astro** - Static site generation, Content Collections
- **Tailwind CSS** - Utility-first styling
- **No heavy component library** - Custom components for control

### Design Principles

1. **Typography-first** - Content readability paramount
2. **Dark mode support** - Prefers-color-scheme respected
3. **Responsive** - Mobile-first breakpoints
4. **Accessible** - WCAG 2.1 AA compliance
5. **Fast** - <1s FCP, perfect Lighthouse scores

### Color Palette (tentative)

```css
/* Serious, professional, not sensational */
--color-bg: #0f172a;        /* Slate 900 */
--color-surface: #1e293b;   /* Slate 800 */
--color-text: #f8fafc;      /* Slate 50 */
--color-muted: #94a3b8;     /* Slate 400 */
--color-accent: #3b82f6;    /* Blue 500 */
--color-danger: #ef4444;    /* Red 500 - for crime severity */
```

---

## Decision 6: Project Structure

```
republican-misconduct-db/
├── astro.config.mjs
├── package.json
├── tailwind.config.mjs
├── tsconfig.json
│
├── scripts/
│   └── split-entries.ts      # Transform batched → individual
│
├── src/
│   ├── content/
│   │   ├── config.ts         # Content collection schema
│   │   └── entries/          # Generated individual .md files
│   │       ├── donald-trump.md
│   │       ├── roy-moore.md
│   │       └── ... (1500+ files)
│   │
│   ├── components/
│   │   ├── EntryCard.astro
│   │   ├── EntryDetail.astro
│   │   ├── FilterSidebar.astro
│   │   ├── SearchBar.astro
│   │   ├── SourceLink.astro
│   │   ├── TagBadge.astro
│   │   └── Pagination.astro
│   │
│   ├── layouts/
│   │   ├── BaseLayout.astro
│   │   └── EntryLayout.astro
│   │
│   ├── pages/
│   │   ├── index.astro
│   │   ├── about.astro
│   │   ├── entries/
│   │   │   ├── index.astro
│   │   │   └── [slug].astro
│   │   ├── crimes/
│   │   │   └── [crime].astro
│   │   ├── positions/
│   │   │   └── [position].astro
│   │   └── years/
│   │       └── [year].astro
│   │
│   ├── styles/
│   │   └── global.css
│   │
│   └── lib/
│       ├── utils.ts          # Slug generation, formatting
│       └── filters.ts        # Filter logic helpers
│
├── public/
│   ├── favicon.ico
│   └── og-image.png
│
└── data/                     # Source markdown (from current repo)
    └── entries-*.md
```

---

## Decision 7: Data Transformation Requirements

### Entry Splitter Script Specification

**Input**: `data/entries-*.md` (batched markdown files)  
**Output**: `src/content/entries/*.md` (individual files with frontmatter)

**Parsing Logic**:

```typescript
// scripts/split-entries.ts
interface ParsedEntry {
  name: string;
  overview: string;
  positions: string[];
  crimes: string[];
  description: string;
  sources: string[];
  tags: string[];
  year?: number;
}

// Entry delimiter: "---" on its own line (after Tags section)
// Entry start: "# {Name}" (H1 heading)

// Extraction patterns:
// - Name: First H1 after delimiter
// - Overview: Text after "## Overview" until next heading
// - Positions: List items after "### Positions"
// - Crimes: List items after "### Crimes"
// - Description: Text after "### Description"
// - Sources: Links after "### Sources"
// - Tags: List items after "### Tags"
```

**Output Format**:

```markdown
---
id: "donald-trump"
name: "Donald Trump"
positions:
  - "President (45th)"
  - "Businessman"
crimes:
  - "Assault"
  - "Rape"
  - "Sexual assault"
year: 2023
tags:
  - "Maga"
sources:
  - "https://en.wikipedia.org/wiki/Donald_Trump_sexual_misconduct_allegations"
  - "https://www.gzeromedia.com/..."
---

## Overview

Donald Trump is accused of sexual assault by more than two dozen women...

## Description

Donald Trump is accused of sexual assault by more than two dozen women...
```

---

## Decision 8: Build & Deployment

### Decision: Static Hosting (Vercel/Netlify/Cloudflare Pages)

**Build Process**:
1. Run `scripts/split-entries.ts` (pre-build hook)
2. Astro static build
3. Pagefind index generation (post-build)
4. Deploy to static host

**Expected Build Metrics**:
- ~1,500 pages generated
- Build time: ~3-5 minutes
- Output size: ~50-100MB (with search index)

**Recommended Host**: Cloudflare Pages
- Free tier handles traffic
- Global CDN
- Excellent performance
- Easy GitHub integration

---

## Component Hierarchy Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      BaseLayout                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Header (Navigation, Search trigger)                   │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Main Content (slot)                                   │   │
│  │                                                       │   │
│  │  ┌────────────────────────────────────────────────┐  │   │
│  │  │ Page: /entries                                  │  │   │
│  │  │  ┌─────────────┐  ┌─────────────────────────┐  │  │   │
│  │  │  │ FilterSidebar│  │ Entry Grid              │  │  │   │
│  │  │  │  - Crimes    │  │  ┌─────────┐ ┌───────┐  │  │  │   │
│  │  │  │  - Positions │  │  │EntryCard│ │       │  │  │  │   │
│  │  │  │  - Years     │  │  └─────────┘ └───────┘  │  │  │   │
│  │  │  │  - Tags      │  │  ┌─────────┐ ┌───────┐  │  │  │   │
│  │  │  └─────────────┘  │  │         │ │       │  │  │  │   │
│  │  │                   │  └─────────┘ └───────┘  │  │  │   │
│  │  │                   │  Pagination             │  │  │   │
│  │  │                   └─────────────────────────┘  │  │   │
│  │  └────────────────────────────────────────────────┘  │   │
│  │                                                       │   │
│  │  ┌────────────────────────────────────────────────┐  │   │
│  │  │ Page: /entries/[slug]                          │  │   │
│  │  │  EntryDetail                                    │  │   │
│  │  │  ├── Name (H1)                                 │  │   │
│  │  │  ├── Overview                                   │  │   │
│  │  │  ├── Positions (TagBadge[])                    │  │   │
│  │  │  ├── Crimes (TagBadge[])                       │  │   │
│  │  │  ├── Description                               │  │   │
│  │  │  └── Sources (SourceLink[])                    │  │   │
│  │  └────────────────────────────────────────────────┘  │   │
│  │                                                       │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Footer                                                │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Consequences

### Positive

- **SEO Excellence**: Static HTML, proper meta tags, individual URLs
- **Performance**: No runtime JS for basic browsing, instant page loads
- **Maintainability**: Markdown source is human-editable, git-friendly
- **Scalability**: Static hosting handles any traffic volume
- **Search**: Pagefind provides fast, accurate full-text search
- **Type Safety**: Zod schemas catch data issues at build time

### Negative

- **Build Time**: ~5 minutes for 1,500 pages (acceptable)
- **Transformation Script**: One-time development cost
- **File Count**: 1,500+ individual files in content collection

### Risks

- **Markdown Parser Edge Cases**: Some entries may have formatting inconsistencies
  - *Mitigation*: Add validation in split script, log warnings
- **Slug Collisions**: Two people with same name
  - *Mitigation*: Append numeric suffix if collision detected

---

## Implementation Order

1. **Phase 1**: Entry splitter script (transforms batched → individual)
2. **Phase 2**: Astro project scaffold with Content Collections
3. **Phase 3**: Base layouts and components
4. **Phase 4**: Entry detail pages (`[slug].astro`)
5. **Phase 5**: Browse page with filtering
6. **Phase 6**: Pagefind integration
7. **Phase 7**: Category pages (crimes, positions, years)
8. **Phase 8**: Polish, dark mode, accessibility audit
9. **Phase 9**: Deployment pipeline

---

## References

- [Astro Content Collections](https://docs.astro.build/en/guides/content-collections/)
- [Pagefind Documentation](https://pagefind.app/docs/)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Cloudflare Pages](https://pages.cloudflare.com/)
