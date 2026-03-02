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

- [x] **Add loading indicator while data.json fetches** *(done c95f738)*
  Spinner + "Loading catalog data..." in the table container during fetch, hidden when load completes.

- [x] **Add column sorting** *(done c95f738)*
  8 sortable columns (title, journal, authors, year, volume, issue, pages, process) with 3-state click toggle (asc → desc → clear). Arrow indicators on headers. Sort persists across filter changes.

- [x] **Add review guidelines / rubric** *(done c95f738)*
  6-item verification checklist on Contributors tab between info cards and onboarding guide: metadata, journal, process label, abstract, equations, URL/DOI.

- [x] **Unify "Reviewed" / "Research Grade" terminology** *(done 4e47f15)*
  Changed "Research Grade" to "Reviewed" in Contributors tab. Consistent with catalog badge terminology.

- [x] **Add review progress metric** *(done c95f738)*
  Animated progress bar on Statistics tab showing reviewed/total entries with percentage.

- [x] **Add "My Submissions" view for connected contributors** *(done c95f738)*
  "My Activity" dashboard above leaderboard when connected: 3 stat boxes (Submitted/Corrected/Verified), compact table of up to 10 entries, empty state when no activity. Disappears when disconnected.

## P3 — Polish

- [x] **Improve landing page orientation** *(done 5fafd9f)*
  Catalog subtitle dynamically shows entry count + journal names once data loads. Static fallback text displays during load.

- [x] **Fix disabled author filter UX** *(done 5fafd9f)*
  Removed the disabled author dropdown entirely. Author search is handled by the text search box.

- [x] **Separate verify and correct actions** *(done 5fafd9f)*
  Removed "Mark as reviewed" checkbox from edit modal. Verification is handled exclusively by the Verify button (signoff flow).

- [x] **Add search placeholder shortening** *(done 5fafd9f)*
  Shortened placeholder to "Search articles, authors, processes..." — fits mobile and mentions authors.

- [x] **Add column help tooltips** *(done 5fafd9f)*
  Added title attributes to Abstract, Behavioral Process, Static Equation, and Recursive Equation column headers.
