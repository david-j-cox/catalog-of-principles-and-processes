# TODO — Behavioral Process Catalog

All audit items complete. Three full audit passes conducted and resolved.

## Manual Review

- **15 truncated equations** need verification against original papers (indices: 2120, 2121, 2131, 2134, 2144, 2150, 2171, 2175, 2176, 2204, 2210, 2211, 2212, 2248, 4331)

---

## Closed / Won't Fix

- **~~Migrate data.json to Git LFS~~**
  Investigated: GitHub Pages does not serve LFS-tracked files — it would serve the pointer file instead of the actual JSON, breaking the site. Workaround requires a GitHub Actions deploy workflow, which adds complexity for a no-build-step site. The `.git` size (38MB) is manageable at current scale.
