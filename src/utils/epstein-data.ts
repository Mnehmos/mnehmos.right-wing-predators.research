import { readFile } from 'node:fs/promises';

export interface EpsteinCount {
  name: string;
  count: number;
}

export interface EpsteinDocumentSummary {
  id: string;
  documentNumber: string;
  date: string | null;
  dateSort: string | null;
  documentType: string;
  pageCount: number;
  folders: string[];
  hasHandwriting: boolean;
  hasStamps: boolean;
  people: string[];
  organizations: string[];
  locations: string[];
  dates: string[];
  referenceNumbers: string[];
  summary: string | null;
  significance: string | null;
  keyTopics: string[];
  url: string;
}

export interface EpsteinArchiveSummary {
  generatedAt: string;
  sourceRepo: string;
  sourceArchive: string;
  sourcePath: string;
  sourceCommit: string | null;
  stats: {
    documents: number;
    pages: number;
    analyses: number;
    people: number;
    organizations: number;
    locations: number;
    dates: number;
    documentTypes: number;
  };
  topPeople: EpsteinCount[];
  topOrganizations: EpsteinCount[];
  topLocations: EpsteinCount[];
  topDocumentTypes: EpsteinCount[];
  featuredDocuments: EpsteinDocumentSummary[];
  recentDocuments: EpsteinDocumentSummary[];
}

let cachedSummary: EpsteinArchiveSummary | null = null;

export async function getEpsteinSummary(): Promise<EpsteinArchiveSummary | null> {
  if (cachedSummary) return cachedSummary;

  try {
    const fileUrl = new URL('../data/epstein-summary.json', import.meta.url);
    const raw = await readFile(fileUrl, 'utf-8');
    cachedSummary = JSON.parse(raw) as EpsteinArchiveSummary;
    return cachedSummary;
  } catch {
    return null;
  }
}
