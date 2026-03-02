# TODO — Behavioral Process Catalog

Critical and medium audit items complete. Low-priority items remain.

---

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
