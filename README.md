# Misconduct Database

Astro-based editorial database for documented sexual-misconduct cases, abuse-cover-up cases, and archive-backed Epstein-network reporting.

## Stack

- Astro content collections for entries in `src/content/entries/`
- Tailwind for UI styling
- Pagefind for full-site search
- Python maintenance scripts for validation, taxonomy cleanup, and Epstein reporting workflows
- GitHub Pages deployment from `main`

## Local Development

Install dependencies:

```bash
npm ci
```

Run the dev server:

```bash
npm run dev
```

Validate content entries:

```bash
npm run validate:entries
```

Run the full local check:

```bash
npm run check
```

Create a production build:

```bash
npm run build
```

## Content Model

Each entry is a Markdown file in `src/content/entries/` with YAML frontmatter and a body.

Required frontmatter fields:

- `name`
- `positions`
- `crimes`
- `tags`
- `sources`

Supported editorial metadata:

- `aliases`
- `roles`
- `case_type`
- `jurisdiction`
- `review_status`
- `reviewed_at`
- `confidence`
- `needs_research`

Example:

```yaml
---
name: "Example Person"
slug: "example-person"
positions:
  - "Attorney"
crimes:
  - "Obstruction Of Justice"
tags:
  - "epstein files"
sources:
  - "https://example.com/story"
  - url: "https://example.gov/filing.pdf"
    title: "Court Filing"
    publisher: "District Court"
    source_type: "court"
    published_at: "2024-02-01"
    primary: true
aliases:
  - "E. Person"
roles:
  - "Defense Attorney"
case_type: "epstein network"
jurisdiction: "Florida"
review_status: "reviewed"
reviewed_at: "2026-04-16"
confidence: "high"
---
```

Notes:

- Astro routes entries by filename. The frontmatter `slug` field is retained for editorial continuity, but the file path remains the route source of truth.
- `sources` may be plain URLs or structured source objects.

## Editorial Rules

- Keep tags canonical and lower-case.
- Keep positions and crimes human-readable and deduplicated.
- Prefer primary documents and direct reporting over tertiary commentary.
- Mark sparse entries with `needs_research: true` instead of inflating weak summaries.
- Use structured source objects when publisher, title, or source type materially improve reviewability.

## Browse Experience

The browse UI is generated from a normalized build-time index in `src/pages/browse-index.json.ts`.

Current browse behavior:

- full-site search via Pagefind
- client-side browse filtering by crime, position, tag, and alphabet route
- facet counts surfaced in the sidebar
- related-entry suggestions on entry pages using shared crimes, tags, positions, and roles

## Epstein Workflow

Epstein-related material stays inside the normal tag and entry system.

Canonical Epstein tags:

- `epstein files`
- `epstein associate`
- `epstein flight logs`
- `epstein communications`
- `epstein testimony`

Generate the reporting lead files from a local `epstein-docs.github.io` clone:

```bash
python scripts/build_epstein_reporting_leads.py --source .claude/tmp/epstein-docs.github.io
```

Apply reviewed Epstein tags to matching entries:

```bash
python scripts/tag_epstein_entries.py --source .claude/tmp/epstein-docs.github.io --apply
```

Rebuild triage coverage for unresolved or resolved non-entry leads:

```bash
python scripts/build_epstein_lead_triage.py
```

Key Epstein files:

- `scripts/epstein_focus_people.json`
- `scripts/epstein_lead_triage.json`
- `reports/epstein-reporting-summary.md`
- `reports/epstein-reporting-leads.json`

## Maintenance Scripts

- `python scripts/validate_entries.py`
  Validates frontmatter shape, source structure, optional metadata, and duplicate-source warnings.

- `python scripts/unify_taxonomy.py --dry-run`
  Checks taxonomy normalization without rewriting files.

- `python scripts/normalize_entries.py --dry-run --flag-sparse`
  Reviews normalization and sparse-entry candidates.

- `python scripts/build_epstein_reporting_leads.py --source ...`
  Regenerates archive-backed reporting leads and summary output.

## Deployment

GitHub Actions runs content validation and production build checks on pull requests and on pushes to `main`. GitHub Pages deployment only runs for pushes to `main`.

Workflow file:

- `.github/workflows/deploy.yml`

### Automated updates

- `deploy.yml` also rebuilds and deploys the Pages site daily at 09:17 UTC, or on demand through `workflow_dispatch`.
- `research-refresh.yml` checks the upstream Epstein archive weekly, commits changed reporting artifacts directly to `main`, and deploys the rebuilt site in the same run.
- The research workflow never creates or edits person entries automatically. It publishes generated reporting leads and triage data without a review gate; Actions must be allowed to write to `main` for this mode to work.
- `agent-findings.yml` ingests daily agent JSON from `data/agent-findings/inbox/`, updates the public ledger, and deploys the `/updates/` page at 10:37 UTC or whenever a new inbox file reaches `main`.
- Agent prompts and the required output contract are in [`AGENT_PROMPTS.md`](AGENT_PROMPTS.md). Only events marked `auto_publish: true` with valid evidence metadata enter the public ledger; quarantined leads remain unpublished.

## Repository Layout

- `src/content/entries/` editorial entry files
- `src/components/` UI components
- `src/pages/` Astro routes
- `src/utils/` normalization and shared indexing helpers
- `scripts/` editorial maintenance scripts
- `reports/` generated reporting outputs

## License

Provided for informational and research purposes.
