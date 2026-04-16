/**
 * Client-side browse engine. Loads the full normalized index and renders
 * filtered/sorted/paginated results into #entries-grid.
 *
 * Co-operates with:
 *  - #filter-sidebar (checkboxes w/ name=crime|position|tag)
 *  - #sort-select
 *  - #entries-grid (result container)
 *  - #entries-meta (aria-live result count)
 *  - #page-controls (pagination container, rendered dynamically)
 *  - #active-filter-bar (chips rendered here on mobile/desktop)
 */

interface BrowseRow {
  s: string;
  n: string;
  p: string[];
  c: string[];
  t: string[];
  sc: number;
  nr: boolean;
  sv: number;
}

interface BrowsePayload {
  v: number;
  entries: BrowseRow[];
  facets: {
    crimes: { name: string; count: number }[];
    positions: { name: string; count: number }[];
    tags: { name: string; count: number }[];
  };
}

type SortKey = 'notability' | 'name-asc' | 'name-desc' | 'needs-research';

interface FilterState {
  crimes: Set<string>;
  positions: Set<string>;
  tags: Set<string>;
  letter: string | null;
  sort: SortKey;
  page: number;
  perPage: number;
}

const ENTRIES_PER_PAGE = 48;

function getBasePath(): string {
  // Astro injects BASE_URL at build time into <meta name="base-url" content="...">
  // Fallback: derive from first path segment if present.
  const meta = document.querySelector<HTMLMetaElement>('meta[name="base-url"]');
  if (meta?.content) return meta.content;
  const path = window.location.pathname;
  const m = path.match(/^(\/[^/]+\/)/);
  return m ? m[1] : '/';
}

function encodeSet(s: Set<string>): string {
  return [...s].map(encodeURIComponent).join(',');
}

function decodeSet(raw: string | null): Set<string> {
  if (!raw) return new Set();
  return new Set(raw.split(',').filter(Boolean).map(decodeURIComponent));
}

function readUrlState(): Partial<FilterState> {
  const params = new URLSearchParams(window.location.search);
  const sort = (params.get('sort') || 'notability') as SortKey;
  // Detect letter from path: /entries/letter/a/ => letter=A
  const pathMatch = window.location.pathname.match(/\/entries\/letter\/([a-z])\/?/i);
  const pathLetter = pathMatch ? pathMatch[1].toUpperCase() : null;
  return {
    crimes: decodeSet(params.get('crimes')),
    positions: decodeSet(params.get('positions')),
    tags: decodeSet(params.get('tags')),
    letter: params.get('letter') || pathLetter,
    sort,
    page: Math.max(1, parseInt(params.get('page') || '1', 10) || 1),
  };
}

function writeUrlState(state: FilterState, replace = false): void {
  const params = new URLSearchParams();
  if (state.crimes.size) params.set('crimes', encodeSet(state.crimes));
  if (state.positions.size) params.set('positions', encodeSet(state.positions));
  if (state.tags.size) params.set('tags', encodeSet(state.tags));
  if (state.sort !== 'notability') params.set('sort', state.sort);
  if (state.page > 1) params.set('page', state.page.toString());

  // Path represents letter when using the /entries/letter/X/ route.
  // Prefer navigating the path rather than duplicating via ?letter=.
  const base = getBasePath();
  const currentPath = window.location.pathname;
  const pathLetterMatch = currentPath.match(/\/entries\/letter\/([a-z])\/?/i);
  const currentPathLetter = pathLetterMatch ? pathLetterMatch[1].toUpperCase() : null;

  let nextPath = currentPath;
  if (state.letter && state.letter !== currentPathLetter) {
    // Changing letter while NOT already on letter route: add query param (stays on same page)
    params.set('letter', state.letter);
  } else if (!state.letter && currentPathLetter) {
    // Clearing letter while on letter route: navigate back to /entries/
    nextPath = `${base}entries/`;
  }

  const qs = params.toString();
  const url = `${nextPath}${qs ? '?' + qs : ''}`;
  if (replace) history.replaceState(null, '', url);
  else history.pushState(null, '', url);
}

function matches(row: BrowseRow, state: FilterState): boolean {
  if (state.letter) {
    const first = row.n.charAt(0).toUpperCase();
    if (first !== state.letter.toUpperCase()) return false;
  }
  if (state.crimes.size) {
    if (!row.c.some((v) => state.crimes.has(v))) return false;
  }
  if (state.positions.size) {
    if (!row.p.some((v) => state.positions.has(v))) return false;
  }
  if (state.tags.size) {
    if (!row.t.some((v) => state.tags.has(v))) return false;
  }
  return true;
}

function comparator(sort: SortKey): (a: BrowseRow, b: BrowseRow) => number {
  switch (sort) {
    case 'name-asc':
      return (a, b) => a.n.localeCompare(b.n);
    case 'name-desc':
      return (a, b) => b.n.localeCompare(a.n);
    case 'needs-research':
      return (a, b) => {
        if (a.nr !== b.nr) return a.nr ? -1 : 1;
        return a.n.localeCompare(b.n);
      };
    case 'notability':
    default:
      return (a, b) => b.sv - a.sv || a.n.localeCompare(b.n);
  }
}

function escapeHtml(s: string): string {
  return s.replace(/[&<>"']/g, (c) => {
    switch (c) {
      case '&':
        return '&amp;';
      case '<':
        return '&lt;';
      case '>':
        return '&gt;';
      case '"':
        return '&quot;';
      case "'":
        return '&#39;';
      default:
        return c;
    }
  });
}

function truncate(s: string, n: number): string {
  return s.length > n ? s.slice(0, n) + '…' : s;
}

function renderCard(row: BrowseRow, base: string): string {
  const name = escapeHtml(row.n);
  const slug = encodeURIComponent(row.s);
  const href = `${base}entries/${slug}/`;
  const positions = row.p.slice(0, 2);
  const crimes = row.c.slice(0, 2);
  const extraPos = row.p.length - positions.length;
  const extraCrimes = row.c.length - crimes.length;
  const researchBadge = row.nr
    ? `<span class="badge badge-research" title="Sparse entry — needs research">🔍 Needs research</span>`
    : '';
  const sourceBadge = row.sc > 1
    ? `<span class="badge badge-sources" title="${row.sc} sources">📎 ${row.sc}</span>`
    : '';
  return `
    <div class="entry-cell"
         data-entry-card
         data-crimes="${escapeHtml(row.c.join(','))}"
         data-positions="${escapeHtml(row.p.join(','))}"
         data-tags="${escapeHtml(row.t.join(','))}">
      <article class="entry-card group relative bg-stone-100 dark:bg-stone-800/50 border border-stone-200 dark:border-stone-700/50 rounded-xl overflow-hidden transition-all duration-300 hover:bg-stone-200 dark:hover:bg-stone-800 hover:border-copper hover:shadow-xl hover:-translate-y-1">
        <a href="${href}" class="card-link block p-5 no-underline h-full">
          <div class="card-title-area">
            <h2 class="card-title text-lg font-bold text-stone-800 dark:text-stone-100 group-hover:text-copper transition-colors">${name}</h2>
          </div>
          <div class="card-meta-row">
            ${sourceBadge}${researchBadge}
          </div>
          <div class="card-badges-area positions-area">
            ${positions.length
              ? `<div class="badges-row">${positions
                  .map((p) => `<span class="badge badge-position">${escapeHtml(truncate(p, 25))}</span>`)
                  .join('')}${extraPos > 0 ? `<span class="badge badge-more">+${extraPos}</span>` : ''}</div>`
              : `<div class="badge-placeholder">&nbsp;</div>`}
          </div>
          <div class="card-badges-area crimes-area">
            ${crimes.length
              ? `<div class="badges-row">${crimes
                  .map((c) => `<span class="badge badge-crime">${escapeHtml(c)}</span>`)
                  .join('')}${extraCrimes > 0 ? `<span class="badge badge-more">+${extraCrimes}</span>` : ''}</div>`
              : `<div class="badge-placeholder">&nbsp;</div>`}
          </div>
          <div class="absolute top-5 right-4 text-stone-400 dark:text-stone-500 group-hover:text-copper transition-all group-hover:translate-x-1" aria-hidden="true">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
          </div>
        </a>
      </article>
    </div>`;
}

function renderPagination(container: HTMLElement, current: number, total: number): void {
  if (total <= 1) {
    container.innerHTML = '';
    return;
  }
  const pages: (number | string)[] = [];
  const show = 5;
  if (total <= show + 2) {
    for (let i = 1; i <= total; i++) pages.push(i);
  } else {
    pages.push(1);
    let start = Math.max(2, current - 1);
    let end = Math.min(total - 1, current + 1);
    if (current <= 3) end = Math.min(total - 1, show - 1);
    else if (current >= total - 2) start = Math.max(2, total - show + 2);
    if (start > 2) pages.push('…');
    for (let i = start; i <= end; i++) pages.push(i);
    if (end < total - 1) pages.push('…');
    pages.push(total);
  }

  const btn = (label: string, page: number, disabled: boolean, extra = ''): string => {
    if (disabled) {
      return `<span class="pg-btn pg-btn-disabled" aria-disabled="true">${label}</span>`;
    }
    return `<button class="pg-btn" data-page="${page}" ${extra}>${label}</button>`;
  };

  container.innerHTML = `
    <nav class="flex items-center justify-center flex-wrap gap-1 mt-8" aria-label="Pagination">
      ${btn('‹ Prev', current - 1, current === 1, 'aria-label="Previous page"')}
      <div class="flex items-center gap-1">
        ${pages
          .map((p) => {
            if (p === '…') return `<span class="px-2 py-2 text-stone-400 dark:text-stone-500">…</span>`;
            const n = p as number;
            if (n === current) {
              return `<span class="pg-btn pg-btn-current" aria-current="page">${n}</span>`;
            }
            return `<button class="pg-btn" data-page="${n}">${n}</button>`;
          })
          .join('')}
      </div>
      ${btn('Next ›', current + 1, current === total, 'aria-label="Next page"')}
    </nav>
    <div class="text-center text-sm text-stone-500 dark:text-stone-400 mt-3">Page ${current} of ${total}</div>
  `;
}

function renderChips(container: HTMLElement, state: FilterState, onRemove: (type: 'crime' | 'position' | 'tag' | 'letter', value: string) => void): void {
  const items: { type: 'crime' | 'position' | 'tag' | 'letter'; value: string; label: string }[] = [];
  state.crimes.forEach((v) => items.push({ type: 'crime', value: v, label: v }));
  state.positions.forEach((v) => items.push({ type: 'position', value: v, label: v }));
  state.tags.forEach((v) => items.push({ type: 'tag', value: v, label: v }));
  if (state.letter) items.push({ type: 'letter', value: state.letter, label: `Starts with ${state.letter.toUpperCase()}` });

  if (!items.length) {
    container.classList.add('hidden');
    container.innerHTML = '';
    return;
  }
  container.classList.remove('hidden');
  container.innerHTML = items
    .map(
      (it, i) =>
        `<button class="chip" data-type="${it.type}" data-value="${escapeHtml(it.value)}" data-idx="${i}" aria-label="Remove filter ${escapeHtml(it.label)}">
          <span>${escapeHtml(truncate(it.label, 28))}</span>
          <svg class="w-3 h-3" aria-hidden="true" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
        </button>`
    )
    .join('');
  container.querySelectorAll<HTMLButtonElement>('.chip').forEach((btn) => {
    btn.addEventListener('click', () => {
      const type = btn.dataset.type as 'crime' | 'position' | 'tag' | 'letter';
      const value = btn.dataset.value || '';
      onRemove(type, value);
    });
  });
}

async function init(): Promise<void> {
  const grid = document.getElementById('entries-grid');
  const meta = document.getElementById('entries-meta');
  const pageControls = document.getElementById('page-controls');
  const chipsBar = document.getElementById('active-filter-bar');
  const sortSelect = document.getElementById('sort-select') as HTMLSelectElement | null;
  const sidebar = document.getElementById('filter-sidebar');
  if (!grid || !meta || !pageControls || !chipsBar) return;

  const base = getBasePath();

  // Load index
  let payload: BrowsePayload;
  try {
    const res = await fetch(`${base}browse-index.json`);
    payload = await res.json();
  } catch (err) {
    console.error('Failed to load browse index', err);
    return;
  }

  const initial = readUrlState();
  const state: FilterState = {
    crimes: initial.crimes ?? new Set(),
    positions: initial.positions ?? new Set(),
    tags: initial.tags ?? new Set(),
    letter: initial.letter ?? null,
    sort: initial.sort ?? 'notability',
    page: initial.page ?? 1,
    perPage: ENTRIES_PER_PAGE,
  };

  // Sync sort select with URL state
  if (sortSelect) sortSelect.value = state.sort;

  // Sync checkboxes with URL state
  const syncCheckboxes = () => {
    document.querySelectorAll<HTMLInputElement>('.filter-checkbox').forEach((cb) => {
      const setRef = cb.name === 'crime' ? state.crimes
        : cb.name === 'position' ? state.positions
        : cb.name === 'tag' ? state.tags
        : null;
      if (setRef) cb.checked = setRef.has(cb.value);
    });
  };
  syncCheckboxes();

  const render = (pushUrl = true): void => {
    const filtered = payload.entries.filter((row) => matches(row, state));
    filtered.sort(comparator(state.sort));
    const total = filtered.length;
    const totalPages = Math.max(1, Math.ceil(total / state.perPage));
    if (state.page > totalPages) state.page = totalPages;
    if (state.page < 1) state.page = 1;
    const start = (state.page - 1) * state.perPage;
    const slice = filtered.slice(start, start + state.perPage);

    grid.innerHTML = slice.length
      ? slice.map((r) => renderCard(r, base)).join('')
      : `<div class="col-span-full text-center py-16">
          <div class="text-4xl mb-3" aria-hidden="true">🔍</div>
          <h3 class="text-lg font-semibold text-stone-800 dark:text-stone-100 mb-2">No entries match your filters</h3>
          <p class="text-stone-600 dark:text-stone-400 text-sm">Try adjusting your filter criteria or <button id="reset-btn" class="text-copper underline">clear all</button>.</p>
        </div>`;

    const resetBtn = grid.querySelector<HTMLButtonElement>('#reset-btn');
    resetBtn?.addEventListener('click', clearAll);

    const showingStart = total === 0 ? 0 : start + 1;
    const showingEnd = Math.min(start + state.perPage, total);
    meta.textContent = total === 0
      ? `No entries match your filters`
      : `Showing ${showingStart.toLocaleString()}–${showingEnd.toLocaleString()} of ${total.toLocaleString()} entries`;

    renderPagination(pageControls, state.page, totalPages);
    pageControls.querySelectorAll<HTMLButtonElement>('.pg-btn[data-page]').forEach((btn) => {
      btn.addEventListener('click', () => {
        state.page = parseInt(btn.dataset.page || '1', 10);
        window.scrollTo({ top: grid.offsetTop - 80, behavior: 'smooth' });
        render();
      });
    });

    renderChips(chipsBar, state, (type, value) => {
      if (type === 'crime') state.crimes.delete(value);
      else if (type === 'position') state.positions.delete(value);
      else if (type === 'tag') state.tags.delete(value);
      else if (type === 'letter') state.letter = null;
      state.page = 1;
      syncCheckboxes();
      render();
    });

    if (pushUrl) writeUrlState(state);
  };

  const clearAll = (): void => {
    state.crimes.clear();
    state.positions.clear();
    state.tags.clear();
    state.letter = null;
    state.page = 1;
    syncCheckboxes();
    render();
  };

  // Wire checkbox changes
  document.querySelectorAll<HTMLInputElement>('.filter-checkbox').forEach((cb) => {
    cb.addEventListener('change', () => {
      const setRef = cb.name === 'crime' ? state.crimes
        : cb.name === 'position' ? state.positions
        : cb.name === 'tag' ? state.tags
        : null;
      if (!setRef) return;
      if (cb.checked) setRef.add(cb.value);
      else setRef.delete(cb.value);
      state.page = 1;
      render();
    });
  });

  // Clear-all buttons: desktop sidebar and mobile sheet render separate controls.
  ['clear-filters', 'm-clear-filters'].forEach((id) => {
    document.getElementById(id)?.addEventListener('click', clearAll);
  });

  // Sort select
  sortSelect?.addEventListener('change', () => {
    state.sort = sortSelect.value as SortKey;
    state.page = 1;
    render();
  });

  // Back/forward nav
  window.addEventListener('popstate', () => {
    const next = readUrlState();
    state.crimes = next.crimes ?? new Set();
    state.positions = next.positions ?? new Set();
    state.tags = next.tags ?? new Set();
    state.letter = next.letter ?? null;
    state.sort = next.sort ?? 'notability';
    state.page = next.page ?? 1;
    if (sortSelect) sortSelect.value = state.sort;
    syncCheckboxes();
    render(false);
  });

  // Expose total for sidebar "showing N" text
  (window as unknown as { __totalEntries?: number }).__totalEntries = payload.entries.length;

  render(false);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
