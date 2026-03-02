# TODO — Behavioral Process Catalog

P0–P3 complete. Items below are from a full codebase audit before public launch.

---

## Phase 1 — Security + Repo Hygiene (must do)

- [ ] **Sanitize equation rendering against XSS**
  `createEquationContent()` injects raw `data.json` strings into `innerHTML` without `escapeHtml()`. A malicious PR could inject `<img src=x onerror=alert(1)>`. Combined with the GitHub token in `localStorage`, this is an exploitable XSS-to-token-theft chain. Must escape HTML while preserving MathJax delimiters.

- [ ] **Add aria-labels to all unlabeled form controls**
  The 6 filter `<select>` elements (`#journal-filter`, `#year-filter`, `#volume-filter`, `#issue-filter`, `#process-filter`, `#review-filter`), `#search-input`, `.search-btn`, and the dynamically-created `#github-token` input all lack `<label>` or `aria-label`. WCAG failure — screen readers announce them as unlabeled controls.

- [ ] **Remove tracked non-site files from git**
  `git rm --cached` the following tracked files that bloat the repo and are publicly accessible on the GitHub Pages URL: `scrapers/output/*.json` (~5.5 MB), `DataToAdd/*.json` and `*.xlsx`, all `*.py` scripts (`scraper.py`, `backfill_journal.py`, `extract_equations.py`, `judge_equations.py`, `merge_equations.py`, `scrapers/*.py`), `data_colleciton_template.xlsx`. Student names appear in DataToAdd filenames.

- [ ] **Update `_config.yml` exclude list and description**
  Description says "retro-themed" and "from JEAB" — both wrong (dark GitHub-style theme, three journals). Exclude list only covers `README.md`, `.gitignore`, `.DS_Store` — must also exclude `TODO.md`, `*.py`, `DataToAdd/`, `scrapers/`, `data_colleciton_template.xlsx`.

## Phase 2 — Bug Fixes (should do)

- [ ] **Fix `populateFilters()` stacking duplicate event listeners**
  Called on init and again after adding an entry. Each call adds new `change` listeners to the same filter elements, causing `applyFilters` to fire multiple times per change.

- [ ] **Fix `escapeHtml(0)` returning empty string**
  The `!str` guard treats falsy numeric values (year=0, volume=0) as empty, rendering blank cells instead of `0`.

- [ ] **Fix GitHub username sanitization stripping valid characters**
  Regex `[^a-zA-Z0-9\-]` on the leaderboard (~line 1992) removes underscores and dots, breaking profile links for usernames that contain them.

- [ ] **Fix `updateStatistics` not using `normalizeProcesses()`**
  Statistics tab counts processes with raw `Array.isArray` / string check, while the filter dropdown uses `normalizeProcesses()`. Counts will differ for entries with comma-separated or JSON-encoded process strings.

- [ ] **Fix Ctrl+Enter shortcut firing globally**
  Opens the add-entry modal even when the user is typing in the search box, edit modal, or GitHub token field. Should only fire when no modal/input is focused.

- [ ] **Fix localStorage corruption discarding valid data.json**
  If `JSON.parse(savedData)` throws inside the `try` block after a successful `fetch('data.json')`, the catch falls to fallback data, losing all 11,920 real entries. Parse localStorage separately or wrap it in its own try/catch.

- [ ] **Fix global error handler showing misleading toasts**
  `window.addEventListener('error', ...)` fires on any unhandled error (MathJax rendering, network image failures, third-party scripts), showing "An error occurred. Please refresh." Remove or scope to application-specific errors only.

- [ ] **Fix comment syntax error on script.js ~line 306**
  `/ Owner shortcut:` should be `// Owner shortcut:`. Currently evaluates as a harmless division expression but is technically a bug.

- [ ] **Remove dead code**
  - `exportData()` function (~line 1597) — defined but never called.
  - `normalizeEq` inside `renderPage()` — duplicates `normalizeEqGlobal` at module scope.
  - Legacy `article.equation` field — referenced in search (~line 1091) and fallback (~line 805) but never rendered or editable.
  - Two separate `DOMContentLoaded` listeners (lines ~484 and ~1474) — consolidate into one.

- [ ] **Remove dead CSS and HTML**
  - Dead CSS selectors: `.subtitle`, `.math-equation`, `.equation-definitions-inline`, `.MathJax_Display`, `.data-table th::before { display: none }`.
  - Dead HTML: `<div class="dna-helix"></div>` (empty div, `display: none`).
  - Missing `@keyframes pulse` — referenced in JS row-click animation but never defined. Either add it or remove the animation call.

## Phase 3 — Polish (nice to have)

- [ ] **Unify three near-identical toast notification functions**
  `showPullRequestSuccess`, `showSuccessMessage`, and `showErrorMessage` all create a div, set inline CSS, append to body, and setTimeout to remove. Extract a shared `showToast(message, type)` helper.

- [ ] **Deduplicate form-reading logic between add-entry and edit-entry**
  Both handlers read 14 form fields with `document.getElementById(...)` and construct entry objects identically. Only the ID prefix differs (`new-` vs `edit-`). Extract a shared `readEntryForm(prefix)` helper.

- [ ] **Cache filter DOM element references**
  `applyFilters()` re-queries all 6 filter elements via `getElementById` on every keystroke/change. Cache them once at init.

- [ ] **Add `404.html`**
  No custom 404 page exists. GitHub Pages shows a generic 404 for mistyped URLs. A simple redirect-to-index page would improve UX.

- [ ] **Add missing `focus-visible` outlines**
  `.search-btn`, `.search-input`, and `.size-btn` are interactive elements missing from the `focus-visible` CSS rule block. Keyboard users get no visible focus indicator.

- [ ] **Fix minor CSS issues**
  - Conflicting `width: 200px; min-width: 600px` on abstract column — `width` is meaningless, remove it.
  - Invalid `justify-content: stretch` in mobile media query — not a valid value for `justify-content`.
  - `overflow-x: auto` on `.container` — could create double scrollbar alongside `.table-container`.
  - Add `-webkit-backdrop-filter` prefix for older Safari on `.modal`.

- [ ] **Add `parseInt` radix and revoke blob URLs**
  Several `parseInt()` calls lack a radix parameter. CSV export creates a blob URL via `URL.createObjectURL()` but never calls `URL.revokeObjectURL()`.

- [ ] **Normalize `static-equation` field types in data.json**
  3,529 entries use arrays (mostly empty `[]`), 8,391 use strings. JS handles both but it's fragile. Normalize all to strings.

- [ ] **Move inline toast styles and injected keyframes to CSS**
  Toast functions use `style.cssText` with inline CSS. `@keyframes slideIn`/`slideOut` are injected via JS. Move both to `styles.css` alongside the existing `@keyframes spin`.
