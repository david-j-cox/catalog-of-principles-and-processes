# TODO — Behavioral Process Catalog

All audit items complete. One item investigated and closed.

---

## Closed / Won't Fix

- **~~Migrate data.json to Git LFS~~**
  Investigated: GitHub Pages does not serve LFS-tracked files — it would serve the pointer file instead of the actual JSON, breaking the site. Workaround requires a GitHub Actions deploy workflow, which adds complexity for a no-build-step site. The `.git` size (38MB) is manageable at current scale.
