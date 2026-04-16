import type { APIRoute } from 'astro';
import { getNormalizedEntries, toBrowseRow, getFacetCounts } from '../utils/entries-index';

export const GET: APIRoute = async () => {
  const entries = await getNormalizedEntries();
  const facets = getFacetCounts(entries);
  const payload = {
    // Generated at build time. `v` lets the client detect cache-stale indexes.
    v: entries.length,
    entries: entries.map(toBrowseRow),
    facets: {
      crimes: facets.crimes.map(([name, count]) => ({ name, count })),
      positions: facets.positions.map(([name, count]) => ({ name, count })),
      tags: facets.tags.map(([name, count]) => ({ name, count })),
    },
  };
  return new Response(JSON.stringify(payload), {
    status: 200,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'public, max-age=300',
    },
  });
};
