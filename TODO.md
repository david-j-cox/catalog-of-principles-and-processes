# TODO — Behavioral Process Catalog

## High

- [x] Fix 18 corrupted LaTeX commands in data.json (`\right` → CR+ight, `\text` → TAB+ext, `\times` → TAB+imes)
- [x] Fix 15 entries with unbalanced LaTeX braces + 1 garbled equation at index 67 — garbled eq cleared; 15 truncated eqs need manual review against papers
- [x] Add debounce/disable to Verify button to prevent duplicate PRs

## Medium

- [x] Add ARIA tab roles to navigation (`role="tablist"`, `role="tab"`, `aria-selected`)
- [x] Fix render-blocking Google Fonts (preconnect + media swap)
- [x] Replace `alert()` in CSV export error path with `showToast()`

## Low

- [x] Clean remaining whitespace artifacts in data.json (70 fields cleaned)
- [x] Validate URL protocol on PR `html_url` before opening
- [x] Add timeout to `fetchUpstreamData` fetch call (30s AbortController)
- [x] Remove unused `.article-title` CSS class — actually used in JS as semantic class, no action needed

---

## Closed / Won't Fix

- **~~Migrate data.json to Git LFS~~**
  Investigated: GitHub Pages does not serve LFS-tracked files — it would serve the pointer file instead of the actual JSON, breaking the site. Workaround requires a GitHub Actions deploy workflow, which adds complexity for a no-build-step site. The `.git` size (38MB) is manageable at current scale.
