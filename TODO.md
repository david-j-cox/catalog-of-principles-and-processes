# TODO — Behavioral Process Catalog

P0–P3 complete. Items below are from a full codebase audit before public launch.

---

## Phase 1 — Security + Repo Hygiene (must do)

- [x] **Sanitize equation rendering against XSS**
- [x] **Add aria-labels to all unlabeled form controls**
- [x] **Remove tracked non-site files from git**
- [x] **Update `_config.yml` exclude list and description**

## Phase 2 — Bug Fixes (should do)

- [x] **Fix `populateFilters()` stacking duplicate event listeners**
- [x] **Fix `escapeHtml(0)` returning empty string**
- [x] **Fix GitHub username sanitization stripping valid characters**
- [x] **Fix `updateStatistics` not using `normalizeProcesses()`**
- [x] **Fix Ctrl+Enter shortcut firing globally**
- [x] **Fix localStorage corruption discarding valid data.json**
- [x] **Fix global error handler showing misleading toasts**
- [x] **Fix comment syntax error on script.js ~line 306** (false positive — already correct)
- [x] **Remove dead code**
- [x] **Remove dead CSS and HTML**

## Phase 3 — Polish (nice to have)

- [x] **Unify three near-identical toast notification functions**
- [x] **Deduplicate form-reading logic between add-entry and edit-entry**
- [x] **Cache filter DOM element references**
- [x] **Add `404.html`**
- [x] **Add missing `focus-visible` outlines**
- [x] **Fix minor CSS issues**
- [x] **Add `parseInt` radix and revoke blob URLs**
- [x] **Normalize `static-equation` field types in data.json**
- [x] **Move inline toast styles and injected keyframes to CSS**
