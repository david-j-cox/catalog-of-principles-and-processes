# Behavioral Process Catalog

A searchable catalog of behavioral processes and equations from JEAB, Behavioural Processes, and JEP: Animal Learning & Cognition.

**Live site:** [david-j-cox.github.io/catalog-of-principles-and-processes](https://david-j-cox.github.io/catalog-of-principles-and-processes/)

## What Is This?

The Behavioral Process Catalog indexes **11,920 articles** across three journals to answer the question: *What is the total set of processes that combine to create a behavioral system?*

Each entry includes citation metadata, the behavioral process studied, mathematical equations (static and recursive), variable definitions, and an abstract. The catalog is fully searchable, filterable, and exportable.

## Features

- **Search & filter** — full-text search across titles, authors, abstracts, processes, and equations; filter by journal, year, volume, issue, process, author, and review status
- **MathJax equations** — LaTeX-rendered static and recursive equations with variable definitions
- **CSV export** — download the current filtered view as a spreadsheet
- **Verification system** — community sign-off workflow; 3 independent verifications mark an entry as "Reviewed"
- **Contributor leaderboard** — points for submissions, corrections, and verifications

## Contributing

### With a GitHub account

1. Create a [Personal Access Token](https://github.com/settings/tokens/new?scopes=public_repo&description=Behavioral%20Process%20Catalog) with `public_repo` scope
2. On the site, click **Connect** and paste your token
3. **Add entries** with the "+ Add New Entry" button — this opens a pull request against the catalog
4. **Suggest corrections** with the pencil button on any row — also opens a PR
5. **Verify entries** with the checkmark button — confirms an entry's accuracy
6. A maintainer reviews and merges your PR; you appear on the leaderboard

### Without a GitHub account

Adding an entry or suggesting a correction without a token opens a pre-filled **GitHub Issue** for a maintainer to review. No account is needed to browse, search, filter, or export.

## Data Structure

Each entry in `data.json`:

```json
{
  "title": "Article title",
  "journal": "JEAB",
  "year": 1958,
  "volume": 1,
  "issue": 1,
  "pages": "1-15",
  "authors": ["Ferster, C. B.", "Skinner, B. F."],
  "url": "https://doi.org/...",
  "abstract": "...",
  "process": ["Reinforcement"],
  "static-equation": "R = k \\cdot r / (r + r_e)",
  "static-equation-definitions": "R = response rate; k = asymptote; r = reinforcement rate; r_e = half-max constant",
  "recursive-equation": "",
  "recursive-equation-definitions": "",
  "reviewed": false,
  "signoffs": [],
  "contributor": "github-username"
}
```

## Technical Stack

- Vanilla HTML, CSS, and JavaScript — no build step
- [MathJax 3](https://www.mathjax.org/) for equation rendering
- GitHub REST API for pull requests and fork-based contributions
- Hosted on GitHub Pages

## File Structure

```
catalog-of-principles-and-processes/
├── index.html       # Main page
├── script.js        # Application logic
├── styles.css       # Dark theme styles
├── data.json        # 11,920 catalog entries
├── DataToAdd/       # Incoming data submissions
└── README.md
```

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+K` / `Cmd+K` | Focus search input |
| `Ctrl+Enter` / `Cmd+Enter` | Open add-entry modal |
| `Escape` | Close modal |

## License

MIT

## Citation

Perez, O. D., McNulty, K. P., & Cox, D. J. (2025). What is the total set of behavioral processes? *Perspectives on Behavior Science*.
