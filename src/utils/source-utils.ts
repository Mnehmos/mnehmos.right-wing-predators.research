export const SOURCE_TYPES = [
  'news',
  'court',
  'government',
  'archive',
  'social',
  'reference',
  'video',
  'other',
] as const;

export type SourceType = (typeof SOURCE_TYPES)[number];

export interface StructuredSource {
  url: string;
  title?: string;
  publisher?: string;
  source_type?: SourceType;
  published_at?: string;
  archive_url?: string;
  primary?: boolean;
  notes?: string;
}

export type EntrySource = string | StructuredSource;

export interface NormalizedSource {
  url: string;
  title?: string;
  publisher?: string;
  sourceType: SourceType;
  publishedAt?: string;
  archiveUrl?: string;
  primary: boolean;
  notes?: string;
  domain: string;
  displayDomain: string;
  archived: boolean;
}

const NEWS_HINTS = ['news', 'times', 'post', 'cnn', 'nbc', 'abc', 'cbs', 'guardian', 'reuters'];
const SOCIAL_HINTS = ['twitter.com', 'x.com', 'facebook.com', 'instagram.com', 'tiktok.com', 'reddit.com'];
const VIDEO_HINTS = ['youtube.com', 'youtu.be', 'vimeo.com'];
const REFERENCE_HINTS = ['wikipedia.org', 'wikimedia.org', 'britannica.com'];
const ARCHIVE_HINTS = ['archive.org', 'web.archive.org', 'epstein-docs.github.io'];

export function isStructuredSource(source: EntrySource): source is StructuredSource {
  return typeof source === 'object' && source !== null && 'url' in source;
}

export function getSourceUrl(source: EntrySource): string {
  return typeof source === 'string' ? source : source.url;
}

export function getSourceDomain(url: string): string {
  try {
    return new URL(url).hostname.toLowerCase();
  } catch {
    return '';
  }
}

export function getDisplayDomain(url: string): string {
  const domain = getSourceDomain(url);
  return domain.replace(/^www\./, '') || url;
}

export function isArchivedUrl(url: string): boolean {
  const domain = getSourceDomain(url);
  return ARCHIVE_HINTS.some((hint) => domain.includes(hint));
}

export function inferSourceType(url: string): SourceType {
  const domain = getSourceDomain(url);

  if (!domain) return 'other';
  if (ARCHIVE_HINTS.some((hint) => domain.includes(hint))) return 'archive';
  if (domain.includes('.gov') || domain.includes('justice') || domain.includes('fbi') || domain.includes('senate.gov')) {
    return 'government';
  }
  if (domain.includes('court') || domain.includes('uscourts')) return 'court';
  if (SOCIAL_HINTS.some((hint) => domain.includes(hint))) return 'social';
  if (VIDEO_HINTS.some((hint) => domain.includes(hint))) return 'video';
  if (REFERENCE_HINTS.some((hint) => domain.includes(hint))) return 'reference';
  if (NEWS_HINTS.some((hint) => domain.includes(hint))) return 'news';
  return 'other';
}

export function normalizeSource(source: EntrySource): NormalizedSource {
  const structured = isStructuredSource(source) ? source : undefined;
  const url = getSourceUrl(source).trim();

  return {
    url,
    title: structured?.title?.trim() || undefined,
    publisher: structured?.publisher?.trim() || undefined,
    sourceType: structured?.source_type ?? inferSourceType(url),
    publishedAt: structured?.published_at?.trim() || undefined,
    archiveUrl: structured?.archive_url?.trim() || undefined,
    primary: structured?.primary === true,
    notes: structured?.notes?.trim() || undefined,
    domain: getSourceDomain(url),
    displayDomain: getDisplayDomain(url),
    archived: isArchivedUrl(url) || Boolean(structured?.archive_url),
  };
}

export function normalizeSources(sources: EntrySource[] = []): NormalizedSource[] {
  return sources.map(normalizeSource).filter((source) => source.url.length > 0);
}

export function sourceTypeLabel(type: SourceType): string {
  switch (type) {
    case 'court':
      return 'Court';
    case 'government':
      return 'Government';
    case 'archive':
      return 'Archive';
    case 'social':
      return 'Social';
    case 'reference':
      return 'Reference';
    case 'video':
      return 'Video';
    case 'news':
      return 'News';
    case 'other':
    default:
      return 'Source';
  }
}

export function formatSourceDate(raw?: string): string | null {
  if (!raw) return null;
  const parsed = new Date(raw);
  if (Number.isNaN(parsed.getTime())) return raw;
  return parsed.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}
