import { getCollection, type CollectionEntry } from 'astro:content';

/**
 * Normalized entry used throughout the site. Derives cleaned/sorted lists
 * and a notability score at build time. Does NOT mutate source markdown.
 */
export interface NormalizedEntry {
  slug: string;
  name: string;
  nameSortKey: string;
  firstLetter: string;
  positions: string[];
  crimes: string[];
  tags: string[];
  sources: string[];
  sourceCount: number;
  bodyLength: number;
  score: number;
  needsResearch: boolean;
  raw: CollectionEntry<'entries'>;
}

/**
 * Lean record shipped to the client for filtering. Strip anything we don't
 * need at runtime to keep the JSON payload small (~200KB for 1,439 entries).
 */
export interface BrowseIndexRow {
  s: string; // slug
  n: string; // name
  p: string[]; // positions (normalized)
  c: string[]; // crimes (normalized)
  t: string[]; // tags (normalized)
  sc: number; // source count
  nr: boolean; // needs research
  sv: number; // score
}

// Acronyms that should preserve their casing through title-casing.
const ACRONYMS = new Set(['us', 'usa', 'dhs', 'fbi', 'cia', 'gop', 'doj', 'nsa', 'ny', 'nyc', 'la', 'dc']);

const toTitleCase = (s: string): string => {
  const lower = s.trim().toLowerCase().replace(/\s+/g, ' ');
  return lower
    .split(' ')
    .map((word) => {
      if (!word) return word;
      if (ACRONYMS.has(word)) return word.toUpperCase();
      return word.charAt(0).toUpperCase() + word.slice(1);
    })
    .join(' ');
};

const toLowerTag = (s: string): string => s.trim().toLowerCase().replace(/\s+/g, ' ');

const uniqCaseInsensitive = (arr: string[], normalizer: (s: string) => string): string[] => {
  const seen = new Map<string, string>();
  for (const item of arr) {
    const normalized = normalizer(item);
    if (!normalized) continue;
    const key = normalized.toLowerCase();
    if (!seen.has(key)) seen.set(key, normalized);
  }
  return [...seen.values()];
};

const stripFrontmatter = (raw: string): string => {
  // The content body excluding the YAML frontmatter block.
  // Astro gives us entry.body already stripped of frontmatter.
  return raw || '';
};

/**
 * Position tier weights — reward entries for the public significance of
 * the role(s) held. A President outranks a state legislator outranks a
 * local official. Matching is case-insensitive substring so variants
 * ("President (45th)") still hit the right tier.
 *
 * Ordered most specific first; first match wins per position.
 */
const POSITION_TIER_WEIGHTS: readonly [RegExp, number][] = [
  // Exact "President" or "President (Nth)" — excludes "College President", "Party President", etc.
  [/^president(\s*\(.*\))?$/i, 50],
  [/^vice\s*president(\s*\(.*\))?$/i, 40],
  [/\bcabinet\b/i, 30],
  [/\btrump\s*administration\b/i, 28],
  [/\bbush\s*administration\b/i, 28],
  [/\bfederal\s*judge\b/i, 28],
  [/\bus\s*senator\b/i, 26],
  [/\bus\s*representative\b/i, 22],
  [/\bsenator\b/i, 22], // state senators fall under generic state legislator below
  [/\bgovernor\b/i, 22],
  [/\bcongressional\s*aide\b/i, 10],
  [/\bcongressional\s*candidate\b/i, 10],
  [/\bstate\s*legislator\b/i, 10],
  [/\bdistrict\s*attorney\b/i, 8],
  [/\bmayor\b/i, 6],
  [/\bjudge\b/i, 6],
  [/\bcounty\s*commissioner\b/i, 5],
  [/\blaw\s*enforcement\b/i, 4],
  [/\blocal\s*official\b/i, 3],
  [/\bparty\s*official\b/i, 3],
  [/\bextremist(?:\s*leader)?\b/i, 3],
  [/\bwhite\s*nationalist\b/i, 3],
  [/\breligious\s*leader\b/i, 2],
  [/\bmedia\s*figure\b/i, 2],
  [/\bcandidate\b/i, 2],
  [/\blobbyist\b/i, 2],
  [/\bjudge\b/i, 2], // fallback
];

function positionTierBonus(positions: string[]): number {
  let max = 0;
  for (const pos of positions) {
    for (const [pat, weight] of POSITION_TIER_WEIGHTS) {
      if (pat.test(pos)) {
        if (weight > max) max = weight;
        break; // first match per position
      }
    }
  }
  return max;
}

const computeScore = (args: {
  sources: number;
  crimes: number;
  positions: number;
  tags: number;
  bodyLength: number;
  positionTier: number;
}): number =>
  args.sources * 3 +
  args.crimes * 2 +
  args.positions +
  args.tags +
  (args.bodyLength > 200 ? 2 : 0) +
  args.positionTier;

export function normalize(entry: CollectionEntry<'entries'>): NormalizedEntry {
  const positions = uniqCaseInsensitive(entry.data.positions ?? [], toTitleCase);
  const crimes = uniqCaseInsensitive(entry.data.crimes ?? [], toTitleCase);
  const tags = uniqCaseInsensitive(entry.data.tags ?? [], toLowerTag);
  const sources = (entry.data.sources ?? []).map((s) => s.trim()).filter(Boolean);
  const body = stripFrontmatter(entry.body);
  const bodyLength = body.length;

  const name = entry.data.name.trim().replace(/\s+/g, ' ');
  const firstChar = name.charAt(0).toUpperCase();
  const firstLetter = /[A-Z]/.test(firstChar) ? firstChar : '#';

  const positionTier = positionTierBonus(positions);
  const score = computeScore({
    sources: sources.length,
    crimes: crimes.length,
    positions: positions.length,
    tags: tags.length,
    bodyLength,
    positionTier,
  });

  const needsResearch =
    entry.data.needs_research === true || sources.length === 0 || bodyLength < 100;

  return {
    slug: entry.slug,
    name,
    nameSortKey: name.toLowerCase(),
    firstLetter,
    positions,
    crimes,
    tags,
    sources,
    sourceCount: sources.length,
    bodyLength,
    score,
    needsResearch,
    raw: entry,
  };
}

let cached: NormalizedEntry[] | null = null;

export async function getNormalizedEntries(): Promise<NormalizedEntry[]> {
  if (cached) return cached;
  const entries = await getCollection('entries');
  cached = entries.map(normalize).sort((a, b) => a.nameSortKey.localeCompare(b.nameSortKey));
  return cached;
}

export function getLettersWithEntries(entries: NormalizedEntry[]): Set<string> {
  const set = new Set<string>();
  for (const e of entries) if (/[A-Z]/.test(e.firstLetter)) set.add(e.firstLetter);
  return set;
}

export function getFacetCounts(entries: NormalizedEntry[]): {
  crimes: [string, number][];
  positions: [string, number][];
  tags: [string, number][];
} {
  const crime = new Map<string, number>();
  const pos = new Map<string, number>();
  const tag = new Map<string, number>();
  for (const e of entries) {
    for (const c of e.crimes) crime.set(c, (crime.get(c) ?? 0) + 1);
    for (const p of e.positions) pos.set(p, (pos.get(p) ?? 0) + 1);
    for (const t of e.tags) tag.set(t, (tag.get(t) ?? 0) + 1);
  }
  const sortByCountDesc = (a: [string, number], b: [string, number]) => b[1] - a[1];
  return {
    crimes: [...crime.entries()].sort(sortByCountDesc),
    positions: [...pos.entries()].sort(sortByCountDesc),
    tags: [...tag.entries()].sort(sortByCountDesc),
  };
}

export function getTopByScore(entries: NormalizedEntry[], n: number): NormalizedEntry[] {
  return [...entries].sort((a, b) => b.score - a.score || a.nameSortKey.localeCompare(b.nameSortKey)).slice(0, n);
}

export function toBrowseRow(e: NormalizedEntry): BrowseIndexRow {
  return {
    s: e.slug,
    n: e.name,
    p: e.positions,
    c: e.crimes,
    t: e.tags,
    sc: e.sourceCount,
    nr: e.needsResearch,
    sv: e.score,
  };
}
