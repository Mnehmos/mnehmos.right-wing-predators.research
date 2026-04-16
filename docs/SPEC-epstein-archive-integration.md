# Epstein Archive Integration

## Goal

Provide a durable bridge between this Astro site and the public
[`epstein-docs/epstein-docs.github.io`](https://github.com/epstein-docs/epstein-docs.github.io)
archive without importing the upstream site's full raw corpus into this repo.

The local bridge is meant to support:

- research triage
- source discovery
- appends to existing entries
- insertion of new entry material after review

## What We Import

The local build step reads the upstream repo's processed artifacts:

- `results/**/*.json` page-level OCR output
- `analyses.json` AI document analyses
- `dedupe.json` entity canonicalization mappings
- `dedupe_types.json` document-type canonicalization mappings

It groups page JSON into document records and emits two local artifacts:

- `src/data/epstein-summary.json`
  - small build-time summary used by Astro pages
- `public/data/epstein-documents.json`
  - runtime search index used by `/research/epstein/`

## Why This Shape

The upstream archive contains tens of thousands of page files. That is useful for
source preservation, but it is not a good fit for this site's static build.

Instead, we keep:

- a compact summary for SSR
- a grouped document index for client-side search
- direct links back to the live upstream document pages for full review

This keeps the current site fast while still making the archive actionable.

## Refresh Workflow

1. Sync the upstream repo locally.

```powershell
git -C .claude\tmp\epstein-docs.github.io pull
```

2. Rebuild the local bridge artifacts.

```powershell
python scripts/build_epstein_archive.py --source .claude\tmp\epstein-docs.github.io
```

3. Verify the site still builds cleanly.

```powershell
npm run build
```

4. Review the research page locally.

- `/research/`
- `/research/epstein/`

## Editorial Workflow

Use the archive as a prescreened lead source, not as automatic copy.

Recommended flow:

1. Search the local research hub for a person, organization, document number, or topic.
2. Open the upstream document page and review the document context directly.
3. Corroborate claims with the document itself and, where appropriate, outside reporting or court filings.
4. Only then append to an existing entry or insert a new entry draft.

## Guardrails

- OCR output can be wrong.
- AI entity extraction can be noisy.
- AI analyses are useful summaries, not final citations.
- A document mention alone is not enough to justify an allegation in this database.

The archive bridge should speed up research, not lower the verification bar.
