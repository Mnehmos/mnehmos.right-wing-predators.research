interface EpsteinDocumentRow {
  id: string;
  n: string;
  d: string | null;
  ds: string | null;
  t: string;
  p: number;
  u: string;
  pe: string[];
  og: string[];
  lo: string[];
  rf: string[];
  tp: string[];
  s: string | null;
}

interface PreparedDocumentRow extends EpsteinDocumentRow {
  haystack: string;
}

const MAX_RESULTS = 40;

function getBasePath(): string {
  const meta = document.querySelector<HTMLMetaElement>('meta[name="base-url"]');
  if (meta?.content) return meta.content;
  const path = window.location.pathname;
  const match = path.match(/^(\/[^/]+\/)/);
  return match ? match[1] : '/';
}

function normalizeQuery(value: string): string {
  return value.trim().toLowerCase().replace(/\s+/g, ' ');
}

function escapeHtml(value: string): string {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function makeHaystack(doc: EpsteinDocumentRow): string {
  return [
    doc.n,
    doc.d ?? '',
    doc.t,
    doc.pe.join(' '),
    doc.og.join(' '),
    doc.lo.join(' '),
    doc.rf.join(' '),
    doc.tp.join(' '),
    doc.s ?? '',
  ]
    .join(' ')
    .toLowerCase();
}

function scoreDocument(doc: PreparedDocumentRow, query: string, tokens: string[]): number {
  let score = 0;
  const title = doc.n.toLowerCase();
  const type = doc.t.toLowerCase();
  const summary = (doc.s ?? '').toLowerCase();

  if (title.includes(query)) score += 60;
  if (type.includes(query)) score += 20;
  if (summary.includes(query)) score += 10;
  if (doc.pe.some((person) => person.toLowerCase().includes(query))) score += 35;
  if (doc.og.some((org) => org.toLowerCase().includes(query))) score += 25;
  if (doc.lo.some((loc) => loc.toLowerCase().includes(query))) score += 15;

  for (const token of tokens) {
    if (!token) continue;
    if (title.includes(token)) score += 10;
    if (type.includes(token)) score += 4;
    if (doc.haystack.includes(token)) score += 2;
  }

  if (tokens.length > 1 && tokens.every((token) => doc.haystack.includes(token))) {
    score += 18;
  }

  score += Math.min(doc.p, 24);
  return score;
}

function renderResults(rows: PreparedDocumentRow[], container: HTMLElement): void {
  if (!rows.length) {
    container.innerHTML = `
      <div class="card p-5 xl:col-span-2">
        <p class="text-sm text-stone-600 dark:text-stone-300">
          No matching documents were found in the local index. Try a document number, a surname, an organization,
          or a topic phrase from the archive.
        </p>
      </div>
    `;
    return;
  }

  container.innerHTML = rows
    .map((doc) => {
      const meta = [doc.t, doc.d, `${doc.p} pages`].filter(Boolean).map(escapeHtml);
      const people = doc.pe.slice(0, 4).map((person) => `<span class="badge badge-copper">${escapeHtml(person)}</span>`).join('');
      const orgs = doc.og.slice(0, 3).map((org) => `<span class="badge badge-stone">${escapeHtml(org)}</span>`).join('');
      const topics = doc.tp.slice(0, 3).map((topic) => `<span class="badge badge-stone">${escapeHtml(topic)}</span>`).join('');
      const summary = doc.s ? `<p class="text-sm text-stone-600 dark:text-stone-300 leading-relaxed">${escapeHtml(doc.s)}</p>` : '';

      return `
        <article class="card card-hover p-5 h-full flex flex-col gap-4">
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="text-xs uppercase tracking-[0.16em] text-copper mb-2">${escapeHtml(doc.t)}</p>
              <h3 class="text-lg font-bold font-display text-stone-800 dark:text-stone-100 leading-tight">${escapeHtml(doc.n)}</h3>
            </div>
            <span class="badge badge-stone">${doc.p} pages</span>
          </div>

          <div class="flex flex-wrap gap-2 text-xs text-stone-500 dark:text-stone-400">
            ${meta.map((item) => `<span>${item}</span>`).join('')}
          </div>

          ${summary}

          ${people ? `<div class="flex flex-wrap gap-2">${people}</div>` : ''}
          ${orgs ? `<div class="flex flex-wrap gap-2">${orgs}</div>` : ''}
          ${topics ? `<div class="flex flex-wrap gap-2">${topics}</div>` : ''}

          <div class="mt-auto pt-2">
            <a href="${escapeHtml(doc.u)}" class="text-sm font-medium no-underline inline-flex items-center gap-2">
              Open upstream document
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5h5m0 0v5m0-5L10 14" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12v7h7" />
              </svg>
            </a>
          </div>
        </article>
      `;
    })
    .join('');
}

function initEpsteinResearch(): void {
  const root = document.getElementById('epstein-search-root');
  if (!root) return;

  const input = document.getElementById('epstein-search') as HTMLInputElement | null;
  const clear = document.getElementById('epstein-clear') as HTMLButtonElement | null;
  const meta = document.getElementById('epstein-results-meta');
  const results = document.getElementById('epstein-results');
  if (!input || !clear || !meta || !results) return;

  const base = getBasePath();
  const dataUrl = `${base}data/epstein-documents.json`;

  let docs: PreparedDocumentRow[] | null = null;
  let loadPromise: Promise<PreparedDocumentRow[]> | null = null;

  async function ensureDocsLoaded(): Promise<PreparedDocumentRow[]> {
    if (docs) return docs;
    if (loadPromise) return loadPromise;

    meta.textContent = 'Loading the local Epstein document index...';
    loadPromise = fetch(dataUrl)
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`Failed to load ${dataUrl}: ${response.status}`);
        }
        const payload = (await response.json()) as EpsteinDocumentRow[];
        docs = payload.map((doc) => ({ ...doc, haystack: makeHaystack(doc) }));
        meta.textContent = `Loaded ${docs.length.toLocaleString()} grouped documents. Enter a search term to filter them.`;
        return docs;
      })
      .catch((error: unknown) => {
        const message = error instanceof Error ? error.message : 'Unknown error';
        meta.textContent = `Unable to load the local research index: ${message}`;
        results.innerHTML = '';
        throw error;
      });

    return loadPromise;
  }

  async function runSearch(): Promise<void> {
    const query = normalizeQuery(input.value);
    if (!query) {
      results.innerHTML = '';
      meta.textContent = docs
        ? `Loaded ${docs.length.toLocaleString()} grouped documents. Enter a search term to filter them.`
        : 'Focus the search field to load the local document index on demand.';
      return;
    }

    const loadedDocs = await ensureDocsLoaded();
    const tokens = query.split(' ').filter(Boolean);

    const ranked = loadedDocs
      .map((doc) => ({ doc, score: scoreDocument(doc, query, tokens) }))
      .filter((item) => item.score > 0)
      .sort((a, b) => b.score - a.score || b.doc.p - a.doc.p || a.doc.n.localeCompare(b.doc.n))
      .slice(0, MAX_RESULTS)
      .map((item) => item.doc);

    meta.textContent = `${ranked.length.toLocaleString()} result${ranked.length === 1 ? '' : 's'} shown for "${query}".`;
    renderResults(ranked, results);
  }

  input.addEventListener('focus', () => {
    void ensureDocsLoaded();
  }, { once: true });

  input.addEventListener('input', () => {
    void runSearch();
  });

  clear.addEventListener('click', () => {
    input.value = '';
    results.innerHTML = '';
    meta.textContent = docs
      ? `Loaded ${docs.length.toLocaleString()} grouped documents. Enter a search term to filter them.`
      : 'Focus the search field to load the local document index on demand.';
    input.focus();
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initEpsteinResearch, { once: true });
} else {
  initEpsteinResearch();
}
