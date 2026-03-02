# TODO — Behavioral Process Catalog

Second audit pass. P0–P3 complete. Items below from deep scan.

---

## Critical (must fix)

- [ ] **Fix localStorage quota overflow**
  `saveData()` stores 16MB JSON in localStorage (5-10MB limit). Unhandled `QuotaExceededError` crashes form submission after a successful PR. Wrap in try/catch or remove localStorage caching entirely.

- [ ] **Fix unhandled JSON.parse in fetch-error fallback**
  If `fetch('data.json')` fails AND localStorage is corrupt, `JSON.parse(savedData)` throws unhandled, preventing the app from loading. Wrap in its own try/catch.

- [ ] **Fix 20 entries with corrupted LaTeX**
  `\frac` became form-feed char (U+000C) + `rac` in 20 entries. MathJax cannot render these. Replace `\x0c` with `\f` in static-equation fields.

- [ ] **Fix CSV export not normalizing equations**
  `renderPage()` calls `normalizeEqGlobal()` but `exportTableToCSV()` does not. Array equations (if re-introduced via PR) would crash `.replace()`. Add `normalizeEqGlobal()` call in CSV path.

## Medium (should fix)

- [ ] **Fix `Math.min(...years)` stack overflow risk**
  Spread on 11,920-element array in `updateStatistics()`. Safe now but will crash at ~65K entries. Use a reduce loop instead.

- [ ] **Fix abstract toggle display inconsistency**
  Collapsed shows HTML-escaped text via innerHTML, expanded shows decoded text from `getAttribute('data-full')` via textContent. Text differs for abstracts containing `&`, `<`, etc.

- [ ] **Add focus trap and ARIA attributes to modals**
  Missing `role="dialog"`, `aria-modal="true"`, focus management, and focus return on close. WCAG 2.1 AA failure.

- [ ] **Fix color contrast for text-muted on bg-card**
  `#8b949e` on `#161b22` = ~4.0:1, below WCAG AA 4.5:1 minimum. Lighten `--text-muted` or darken selectively.

- [ ] **Add Open Graph meta tags**
  No `og:title`, `og:description`, `og:image`, `og:url`. Social sharing shows generic preview.

- [ ] **Fix CSV process field quote escaping**
  `formatProcessForCSV()` joins array items without escaping double quotes. Process names containing `"` corrupt CSV output.

- [ ] **Remove junk recursive equation at data.json index 62**
  Contains only a stray `"` character. Should be empty string.

## Low (nice to have)

- [ ] **Add `<noscript>` fallback**
  Loading spinner stuck forever with JS disabled. Add message telling users JS is required.

- [ ] **Add SRI hash to MathJax CDN script tag**
  No Subresource Integrity attribute. CDN compromise = XSS vector.

- [ ] **Increase edit/verify button touch targets**
  ~20x14px currently, below 44x44px WCAG recommended minimum.

- [ ] **Decode raw HTML entities in 10 data.json entries**
  `&amp;`, `&gt;`, `&#13;`, `&#62;`, `&#x02022;` stored literally in titles and abstracts.

- [ ] **Remove zero-width spaces from 24 data.json entries**
  U+200B in equation fields causes invisible rendering issues.

- [ ] **Add UTF-8 BOM to CSV export**
  Excel on Windows may garble accented author names without BOM.

- [ ] **Remove double scrollbar from `.container` overflow-x**
  Both `.container` and `.table-container` have `overflow-x: auto`, causing nested scrollbars.

- [ ] **Migrate data.json to Git LFS**
  `.git` is 38MB with 24 versions of 16MB file. Will grow with each commit.

- [ ] **Update PR template terminology**
  `.github/pull_request_template.md` still says "IV → DV Equation" instead of "Static/Recursive Equation".
