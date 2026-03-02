# TODO — Behavioral Process Catalog

## P0 — Broken Features (non-functional)

- [x] **Fix PR creation for outside contributors (fork-based flow)** *(done d650fbd)*
  Replaced direct-push with fork-based flow using Git Data API. Non-collaborators fork → sync → branch → commit → cross-fork PR. Repo owner bypasses fork. Git Blobs API with UTF-8 encoding handles 18MB+ data.json.

- [x] **Fix verify buttons never appearing** *(done d650fbd)*
  Removed `article.contributor` guard from verify button condition. All unreviewed entries now show the Verify button when logged in.

- [x] **Reduce GitHub token scope from `repo` to `public_repo`** *(done d650fbd)*
  Token creation URL and help text now request `public_repo` only.

## P1 — Confusing or Drives People Away

- [x] **Add visible tagline/subtitle on landing page** *(done 4e47f15)*
  Added `<p class="header-subtitle">` with meta description copy below the h1.

- [x] **Add contribution path for users without GitHub** *(done 4e47f15)*
  No-token and PR-failure paths now open a pre-filled GitHub Issue via `buildNewEntryIssueUrl()`. Removed misleading localStorage fallback.

- [x] **Rewrite README.md** *(done 4e47f15)*
  Full rewrite: live site link, 11,920 entries, features, two contributing paths, data schema, tech stack, file structure, keyboard shortcuts, citation.

- [x] **Add contributor onboarding / how-to guide** *(done 4e47f15)*
  5-step onboarding guide in Contributors tab: create token, connect, contribute (add/edit/verify), what happens next, no-GitHub fallback.

## P2 — Missing Expected Features

- [ ] **Add loading indicator while data.json fetches**
  The page loads a ~6MB JSON file. On slow connections the table is empty for several seconds with no feedback — no spinner, skeleton screen, or "Loading..." message.

- [ ] **Add column sorting**
  Expected behavior for a data table. The README even mentions it as a "future enhancement." Users should be able to sort by year, title, process, etc.

- [ ] **Add review guidelines / rubric**
  Reviewers don't know what "verified all fields are correct" means. Should they check the original paper? Verify metadata matches the DOI? Check the equation? Need a clear rubric explaining what to verify and to what standard.

- [x] **Unify "Reviewed" / "Research Grade" terminology** *(done 4e47f15)*
  Changed "Research Grade" to "Reviewed" in Contributors tab. Consistent with catalog badge terminology.

- [ ] **Add review progress metric**
  No way to see overall review coverage (e.g., "127 / 4,366 entries verified"). A progress bar or stat on the Statistics tab would motivate reviewers by showing collective progress.

- [ ] **Add "My Submissions" view for connected contributors**
  After contributing, users have no way to see what they submitted, PR status, or whether anything was merged. A simple list of their activity would close the feedback loop.

## P3 — Polish

- [ ] **Improve landing page orientation**
  Move the About content (or a condensed version) to be visible on first load instead of hidden behind a tab. Add a link to JEAB. Show entry count prominently on the catalog view, not just under Statistics.

- [ ] **Fix disabled author filter UX**
  The author dropdown is grayed out with a tooltip that only shows on hover (invisible on mobile). Either add visible helper text or remove the dropdown entirely and rely on the search box.

- [ ] **Separate verify and correct actions**
  Currently a reviewer who wants to verify without changing anything must open the edit modal, change nothing, check the "Mark as reviewed" box, and submit. Verify and correct are distinct actions that should have distinct UI paths.

- [ ] **Add search placeholder shortening**
  The current placeholder ("Search articles, processes, abstracts, static equations, or recursive equations...") is too long and gets truncated on most screens. Shorten to something like "Search articles, authors, processes..."

- [ ] **Add column help tooltips**
  "Static Equation" and "Recursive Equation" are domain-specific terms that may confuse some visitors. Add tooltips or a small help icon explaining what each column represents.
