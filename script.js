// Behavioral Process Catalog - JavaScript Functionality

// HTML-escape a string to prevent XSS when inserting into innerHTML
function escapeHtml(str) {
    if (str == null || str === '') return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// Journal display config: key → { label, cssClass }
const JOURNAL_CONFIG = {
    'JEAB':    { label: 'JEAB',    cssClass: 'journal-jeab' },
    'BP':      { label: 'BP',      cssClass: 'journal-bp'   },
    'JEP:ALC': { label: 'JEP:ALC', cssClass: 'journal-jep'  },
};

// Create journal badge HTML
function createJournalBadge(journal) {
    const key = journal || 'JEAB';
    const config = JOURNAL_CONFIG[key] || JOURNAL_CONFIG['JEAB'];
    return `<span class="journal-tag ${config.cssClass}">${escapeHtml(config.label)}</span>`;
}

// Behavioral data will be loaded from data.json
let behavioralData = [];

// Pagination state
let currentPage = 1;
let rowsPerPage = 20;
let currentFilteredData = [];

// Sort state
let currentSortKey = null;
let currentSortDir = null; // 'asc', 'desc', or null

// Edit modal state
let editModalOriginalArticle = null;

// Cached filter DOM elements (populated on DOMContentLoaded)
let filterEls = {};

// Modal focus trap state
let previouslyFocusedElement = null;
let activeTrapHandler = null;

function openModal(modal) {
    previouslyFocusedElement = document.activeElement;
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';

    // Focus first focusable element inside the modal
    const focusable = modal.querySelectorAll('input, select, textarea, button, [tabindex]:not([tabindex="-1"])');
    if (focusable.length) focusable[0].focus();

    // Trap Tab within modal
    activeTrapHandler = function(e) {
        if (e.key !== 'Tab') return;
        const nodes = modal.querySelectorAll('input, select, textarea, button, [tabindex]:not([tabindex="-1"])');
        if (!nodes.length) return;
        const first = nodes[0];
        const last = nodes[nodes.length - 1];
        if (e.shiftKey && document.activeElement === first) {
            e.preventDefault();
            last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
            e.preventDefault();
            first.focus();
        }
    };
    modal.addEventListener('keydown', activeTrapHandler);
}

function closeModal(modal, form) {
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
    if (form) form.reset();
    if (activeTrapHandler) {
        modal.removeEventListener('keydown', activeTrapHandler);
        activeTrapHandler = null;
    }
    if (previouslyFocusedElement) {
        previouslyFocusedElement.focus();
        previouslyFocusedElement = null;
    }
}

// GitHub configuration
const GITHUB_CONFIG = {
    owner: 'david-j-cox',
    repo: 'catalog-of-principles-and-processes',
    dataFile: 'data.json'
};

// Minimal fallback data for local file access (when data.json can't be loaded)
const fallbackData = [
    {
        "title": "Welcome to the Behavioral Process Catalog",
        "year": 2024,
        "volume": 1,
        "issue": 1,
        "pages": "1-5",
        "process": "Getting Started",
        "static-equation": "",
        "static-equation-definitions": "",
        "recursive-equation": "",
        "recursive-equation-definitions": "",
        "abstract": "This is a demonstration entry. For full functionality, please view this site through GitHub Pages or run a local web server. The complete database is stored in data.json and will load automatically when served over HTTP."
    },
    {
        "title": "Effects of Variable-Ratio Schedules on Response Rate in Pigeons",
        "year": 1995,
        "volume": 63,
        "issue": 2,
        "pages": "123-135",
        "process": "Variable-Ratio Reinforcement",
        "static-equation": "R = k \\times (S_R / t)",
        "static-equation-definitions": "R = response rate; k = scaling constant; S_R = reinforcement rate; t = time",
        "recursive-equation": "",
        "recursive-equation-definitions": "",
        "abstract": "Six pigeons responded under variable-ratio (VR) schedules ranging from VR 10 to VR 200. Response rates increased as a power function of ratio size, with individual differences in the exponent."
    }
];

// Load data from data.json file
async function loadData() {
    try {
        const response = await fetch('data.json');
        const jsonData = await response.json();

        // Merge with any local additions (isolated try/catch so corrupt
        // localStorage never discards a successful data.json fetch)
        behavioralData = jsonData;
        try {
            const savedData = localStorage.getItem('behavioralData');
            if (savedData) {
                const localData = JSON.parse(savedData);
                const localOnlyEntries = localData.filter(localEntry =>
                    !jsonData.some(jsonEntry =>
                        jsonEntry.title === localEntry.title &&
                        jsonEntry.year === localEntry.year
                    )
                );
                if (localOnlyEntries.length) {
                    behavioralData = [...jsonData, ...localOnlyEntries];
                }
            }
        } catch (lsError) {
            console.warn('Could not parse localStorage data, ignoring:', lsError);
        }
        
        return behavioralData;
    } catch (error) {
        console.error('Error loading data.json (likely due to local file access), using fallback data:', error);
        
        // Use fallback data, then merge with localStorage
        behavioralData = fallbackData;
        try {
            const savedData = localStorage.getItem('behavioralData');
            if (savedData) {
                const localData = JSON.parse(savedData);
                // Only keep local entries that aren't in the fallback data
                const localOnlyEntries = localData.filter(localEntry =>
                    !fallbackData.some(fallbackEntry =>
                        fallbackEntry.title === localEntry.title &&
                        fallbackEntry.year === localEntry.year
                    )
                );
                behavioralData = [...fallbackData, ...localOnlyEntries];
            }
        } catch (parseError) {
            // Corrupt localStorage — stick with fallback data
        }
        
        return behavioralData;
    }
}

// Save data to localStorage (best-effort; may exceed quota on large datasets)
function saveData() {
    try {
        localStorage.setItem('behavioralData', JSON.stringify(behavioralData));
    } catch (e) {
        // QuotaExceededError — localStorage is too small for the dataset.
        // This is non-critical; data.json is the source of truth.
    }
}

// Create abstract content with expand/collapse functionality
function createAbstractContent(abstract, articleIndex) {
    if (!abstract || abstract === 'No abstract available') {
        return '<em style="opacity: 0.7;">No abstract available</em>';
    }

    const safe = escapeHtml(abstract);
    const maxLength = 80;
    // Truncate on raw text length so collapsed view is consistent after toggle
    const needsTruncation = abstract.length > maxLength;
    const truncated = needsTruncation ? escapeHtml(abstract.substring(0, maxLength)) + '...' : safe;

    const contentId = `abstract-${articleIndex}`;
    const btnId = `btn-${articleIndex}`;

    // Store the full text in a data attribute instead of inline JS
    return `
        <div class="abstract-content collapsed" id="${contentId}" data-full="${safe}">
            ${truncated}
        </div>
        ${needsTruncation ? `<button class="read-more-btn" id="${btnId}" onclick="toggleAbstract('${contentId}', '${btnId}')">Read More</button>` : ''}
    `;
}

// Toggle abstract expand/collapse
function toggleAbstract(contentId, btnId) {
    const content = document.getElementById(contentId);
    const button = document.getElementById(btnId);

    if (!content || !button) return;

    const fullText = content.getAttribute('data-full');
    const isCollapsed = content.classList.contains('collapsed');

    if (isCollapsed) {
        content.classList.remove('collapsed');
        content.classList.add('expanded');
        content.textContent = fullText;
        button.textContent = 'Read Less';
    } else {
        content.classList.remove('expanded');
        content.classList.add('collapsed');
        const truncated = fullText.length > 80 ? fullText.substring(0, 80) + '...' : fullText;
        content.textContent = truncated;
        button.textContent = 'Read More';
    }
    
    // Re-render MathJax for the updated content
    if (window.MathJax && window.MathJax.typesetPromise) {
        setTimeout(() => {
            MathJax.typesetPromise([content]).catch(function (err) {
                console.log('MathJax typeset failed: ' + err.message);
            });
        }, 50);
    }
}

// GitHub API Functions
let githubToken = localStorage.getItem('github_token');
let githubUsername = localStorage.getItem('github_username');
const SIGNOFF_THRESHOLD = 3;

function initializeGitHubAuth() {
    const authSection = document.createElement('div');
    authSection.innerHTML = `
        <div id="github-auth" class="github-auth-panel">
            <div class="auth-content">
                <h3>Connect to GitHub</h3>
                <p>To contribute entries to the catalog, connect your GitHub account:</p>
                <div class="auth-controls">
                    <input type="password" id="github-token" placeholder="GitHub Personal Access Token"
                           aria-label="GitHub Personal Access Token"
                           style="display: ${githubToken ? 'none' : 'block'}">
                    <button id="connect-github" class="auth-btn">${githubToken ? `Connected as @${escapeHtml(githubUsername || '?')}` : 'Connect GitHub'}</button>
                    <button id="disconnect-github" class="auth-btn secondary" 
                            style="display: ${githubToken ? 'block' : 'none'}">Disconnect</button>
                </div>
                <div class="auth-help">
                    <a href="https://github.com/settings/tokens/new?scopes=public_repo&description=Behavioral%20Process%20Catalog"
                       target="_blank">Create a GitHub token</a>
                    <small>Requires 'public_repo' scope for creating pull requests</small>
                </div>
            </div>
        </div>
    `;
    
    document.querySelector('.add-entry-container').before(authSection);
    
    // Event listeners
    document.getElementById('connect-github').addEventListener('click', handleGitHubConnect);
    document.getElementById('disconnect-github').addEventListener('click', handleGitHubDisconnect);
}

function handleGitHubConnect() {
    if (githubToken) {
        showSuccessMessage('Already connected to GitHub!');
        return;
    }
    
    const tokenInput = document.getElementById('github-token');
    const token = tokenInput.value.trim();
    
    if (!token) {
        showErrorMessage('Please enter a GitHub token');
        return;
    }
    
    // Validate token
    validateGitHubToken(token).then(user => {
        if (user) {
            githubToken = token;
            githubUsername = user.login;
            localStorage.setItem('github_token', token);
            localStorage.setItem('github_username', user.login);
            updateAuthUI(true, user.login);
            showSuccessMessage(`Connected as @${user.login}`);
        } else {
            showErrorMessage('Invalid GitHub token. Please check and try again.');
        }
    });
}

function handleGitHubDisconnect() {
    githubToken = null;
    githubUsername = null;
    localStorage.removeItem('github_token');
    localStorage.removeItem('github_username');
    updateAuthUI(false);
    showSuccessMessage('Disconnected from GitHub');
}

function updateAuthUI(connected, username) {
    document.getElementById('github-token').style.display = connected ? 'none' : 'block';
    document.getElementById('connect-github').textContent = connected
        ? `Connected as @${username || githubUsername || '?'}`
        : 'Connect GitHub';
    document.getElementById('disconnect-github').style.display = connected ? 'block' : 'none';
}

async function validateGitHubToken(token) {
    try {
        const response = await fetch('https://api.github.com/user', {
            headers: {
                'Authorization': `token ${token}`,
                'Accept': 'application/vnd.github.v3+json'
            }
        });
        if (!response.ok) return null;
        return await response.json();
    } catch (error) {
        console.error('Token validation failed:', error);
        return null;
    }
}

// ── GitHub API Helpers ────────────────────────────────────────────────────

// Authenticated fetch wrapper — eliminates repeated header blocks
async function ghFetch(url, options = {}) {
    const headers = {
        'Authorization': `token ${githubToken}`,
        'Accept': 'application/vnd.github.v3+json',
        ...options.headers
    };
    if (options.body) headers['Content-Type'] = 'application/json';
    return fetch(url, { ...options, headers });
}

// Fetch data.json via raw.githubusercontent.com (no size limit, no base64)
async function fetchUpstreamData() {
    const url = `https://raw.githubusercontent.com/${GITHUB_CONFIG.owner}/${GITHUB_CONFIG.repo}/main/${GITHUB_CONFIG.dataFile}`;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);
    try {
        const response = await fetch(url, { signal: controller.signal });
        if (!response.ok) throw new Error('Failed to fetch upstream data.json');
        return response.json();
    } finally {
        clearTimeout(timeoutId);
    }
}

// Create a fork (if needed) and a fresh branch. Returns { forkOwner, branchName, baseSha }.
// Owner shortcut: if the authenticated user owns the repo, skip fork and push directly.
async function ensureForkAndBranch(branchPrefix) {
    const { owner, repo } = GITHUB_CONFIG;
    const branchName = `${branchPrefix}-${Date.now()}`;

    // Get upstream HEAD sha
    const mainRef = await ghFetch(`https://api.github.com/repos/${owner}/${repo}/git/refs/heads/main`);
    if (!mainRef.ok) throw new Error('Failed to fetch main branch');
    const mainData = await mainRef.json();
    const baseSha = mainData.object.sha;

    // Owner shortcut — push directly to upstream
    if (githubUsername === owner) {
        const branchRes = await ghFetch(`https://api.github.com/repos/${owner}/${repo}/git/refs`, {
            method: 'POST',
            body: JSON.stringify({ ref: `refs/heads/${branchName}`, sha: baseSha })
        });
        if (!branchRes.ok) {
            // Retry with random suffix on branch name collision
            const retryName = `${branchPrefix}-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
            const retryRes = await ghFetch(`https://api.github.com/repos/${owner}/${repo}/git/refs`, {
                method: 'POST',
                body: JSON.stringify({ ref: `refs/heads/${retryName}`, sha: baseSha })
            });
            if (!retryRes.ok) throw new Error('Failed to create branch');
            return { forkOwner: owner, branchName: retryName, baseSha };
        }
        return { forkOwner: owner, branchName, baseSha };
    }

    // Fork the repo (idempotent — returns 202 even if fork already exists)
    const forkRes = await ghFetch(`https://api.github.com/repos/${owner}/${repo}/forks`, {
        method: 'POST',
        body: JSON.stringify({})
    });
    if (!forkRes.ok && forkRes.status !== 202) throw new Error('Failed to create fork');
    const forkData = await forkRes.json();
    const forkOwner = forkData.owner.login;

    // Wait for fork to be ready (up to 5 tries, 2s apart)
    for (let i = 0; i < 5; i++) {
        const checkRes = await ghFetch(`https://api.github.com/repos/${forkOwner}/${repo}`);
        if (checkRes.ok) {
            const checkData = await checkRes.json();
            if (checkData.size > 0) break;
        }
        await new Promise(resolve => setTimeout(resolve, 2000));
    }

    // Sync fork's main to upstream
    await ghFetch(`https://api.github.com/repos/${forkOwner}/${repo}/merge-upstream`, {
        method: 'POST',
        body: JSON.stringify({ branch: 'main' })
    });

    // Create branch on fork
    const branchRes = await ghFetch(`https://api.github.com/repos/${forkOwner}/${repo}/git/refs`, {
        method: 'POST',
        body: JSON.stringify({ ref: `refs/heads/${branchName}`, sha: baseSha })
    });
    if (!branchRes.ok) {
        const retryName = `${branchPrefix}-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
        const retryRes = await ghFetch(`https://api.github.com/repos/${forkOwner}/${repo}/git/refs`, {
            method: 'POST',
            body: JSON.stringify({ ref: `refs/heads/${retryName}`, sha: baseSha })
        });
        if (!retryRes.ok) throw new Error('Failed to create branch on fork');
        return { forkOwner, branchName: retryName, baseSha };
    }

    return { forkOwner, branchName, baseSha };
}

// Commit updated data via Git Data API (handles 18MB+ files, no btoa needed)
// and open a cross-fork pull request.
async function commitAndCreatePR({ forkOwner, branchName, baseSha, updatedData, commitMessage, prTitle, prBody }) {
    const { owner, repo, dataFile } = GITHUB_CONFIG;

    // 1. Get base tree SHA
    const commitRes = await ghFetch(`https://api.github.com/repos/${owner}/${repo}/git/commits/${baseSha}`);
    if (!commitRes.ok) throw new Error('Failed to fetch base commit');
    const baseCommit = await commitRes.json();

    // 2. Create blob with UTF-8 encoding (up to 100MB, no base64)
    const blobRes = await ghFetch(`https://api.github.com/repos/${forkOwner}/${repo}/git/blobs`, {
        method: 'POST',
        body: JSON.stringify({
            content: JSON.stringify(updatedData, null, 4),
            encoding: 'utf-8'
        })
    });
    if (!blobRes.ok) throw new Error('Failed to create blob');
    const blob = await blobRes.json();

    // 3. Create tree replacing data.json
    const treeRes = await ghFetch(`https://api.github.com/repos/${forkOwner}/${repo}/git/trees`, {
        method: 'POST',
        body: JSON.stringify({
            base_tree: baseCommit.tree.sha,
            tree: [{ path: dataFile, mode: '100644', type: 'blob', sha: blob.sha }]
        })
    });
    if (!treeRes.ok) throw new Error('Failed to create tree');
    const tree = await treeRes.json();

    // 4. Create commit
    const newCommitRes = await ghFetch(`https://api.github.com/repos/${forkOwner}/${repo}/git/commits`, {
        method: 'POST',
        body: JSON.stringify({
            message: commitMessage,
            tree: tree.sha,
            parents: [baseSha]
        })
    });
    if (!newCommitRes.ok) throw new Error('Failed to create commit');
    const newCommit = await newCommitRes.json();

    // 5. Update branch ref
    const refRes = await ghFetch(`https://api.github.com/repos/${forkOwner}/${repo}/git/refs/heads/${branchName}`, {
        method: 'PATCH',
        body: JSON.stringify({ sha: newCommit.sha })
    });
    if (!refRes.ok) throw new Error('Failed to update branch ref');

    // 6. Create cross-fork PR
    const prHead = forkOwner === owner ? branchName : `${forkOwner}:${branchName}`;
    const prRes = await ghFetch(`https://api.github.com/repos/${owner}/${repo}/pulls`, {
        method: 'POST',
        body: JSON.stringify({ title: prTitle, head: prHead, base: 'main', body: prBody })
    });
    if (!prRes.ok) throw new Error('Failed to create pull request');
    return prRes.json();
}

// ── PR Creation Functions ─────────────────────────────────────────────────

async function createPullRequest(newEntry) {
    if (!githubToken) {
        throw new Error('GitHub token not found. Please connect your GitHub account first.');
    }

    try {
        const currentData = await fetchUpstreamData();
        const updatedData = [...currentData, newEntry];
        const { forkOwner, branchName, baseSha } = await ensureForkAndBranch('add-entry');

        return await commitAndCreatePR({
            forkOwner, branchName, baseSha, updatedData,
            commitMessage: `Add new entry: ${newEntry.title}`,
            prTitle: `Add new behavioral process entry: ${newEntry.title}`,
            prBody: `## New Behavioral Process Entry

**Article Title:** ${newEntry.title}
**Journal:** ${newEntry.journal || 'JEAB'}
**Authors:** ${newEntry.authors}
**URL:** ${newEntry.url || 'No URL provided'}
**Year:** ${newEntry.year}
**Volume:** ${newEntry.volume}
**Issue:** ${newEntry.issue}
**Pages:** ${newEntry.pages || 'N/A'}
**Behavioral Process:** ${newEntry.process}
**Abstract:** ${newEntry.abstract || 'No abstract provided'}
**Static Equation:** ${newEntry['static-equation'] || 'N/A'}
**Static Equation Definitions:** ${newEntry['static-equation-definitions'] || 'N/A'}
**Recursive Equation:** ${newEntry['recursive-equation'] || 'N/A'}
**Recursive Equation Definitions:** ${newEntry['recursive-equation-definitions'] || 'N/A'}

This entry was submitted through the Behavioral Process Catalog web interface.

Please review and merge if appropriate.`
        });
    } catch (error) {
        console.error('Error creating pull request:', error);
        throw error;
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', async function() {
    await loadData();
    const loadingIndicator = document.getElementById('loading-indicator');
    if (loadingIndicator) loadingIndicator.classList.add('hidden');
    initializeNavigation();
    populateTable(behavioralData);
    const subtitle = document.getElementById('catalog-subtitle');
    if (subtitle) {
        subtitle.textContent = behavioralData.length.toLocaleString()
            + ' entries across JEAB, Behavioural Processes, and JEP: Animal Learning & Cognition';
    }
    filterEls = {
        search:  document.getElementById('search-input'),
        journal: document.getElementById('journal-filter'),
        year:    document.getElementById('year-filter'),
        volume:  document.getElementById('volume-filter'),
        issue:   document.getElementById('issue-filter'),
        process: document.getElementById('process-filter'),
        review:  document.getElementById('review-filter'),
    };
    populateFilters();
    initializeFilterListeners();
    updateStatistics();
    initializeSearch();
    initializeModal();
    initializeGitHubAuth();
    initializeEditModal();
    initializeSorting();

    // Tooltips for keyboard shortcuts
    document.getElementById('search-input').title = 'Press Ctrl+K to focus search';
    document.querySelector('.add-entry-btn').title = 'Press Ctrl+Enter to add new entry';

    // CSV export
    const exportButton = document.getElementById('export-csv-btn');
    if (exportButton) {
        exportButton.addEventListener('click', exportTableToCSV);
    }
});

// Navigation functionality
function initializeNavigation() {
    const navButtons = document.querySelectorAll('.nav-btn');
    const contentSections = document.querySelectorAll('.content-section');

    navButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetView = this.getAttribute('data-view');
            
            // Update active nav button
            navButtons.forEach(btn => {
                btn.classList.remove('active');
                btn.setAttribute('aria-selected', 'false');
            });
            this.classList.add('active');
            this.setAttribute('aria-selected', 'true');
            
            // Update active content section
            contentSections.forEach(section => section.classList.remove('active'));
            document.getElementById(targetView + '-view').classList.add('active');
            
            // Update statistics if switching to stats view
            if (targetView === 'stats') {
                updateStatistics();
            }

            // Render contributors leaderboard if switching to contributors view
            if (targetView === 'contributors') {
                renderContributors();
            }
        });
    });
}

// Create title content with optional link
function createTitleContent(title, url) {
    const safeTitle = escapeHtml(title);
    if (url && url.trim() !== '') {
        // Only allow http/https URLs
        const safeUrl = /^https?:\/\//i.test(url.trim()) ? escapeHtml(url) : '#';
        return `<a href="${safeUrl}" target="_blank" rel="noopener noreferrer" class="article-link">${safeTitle}</a>`;
    }
    return safeTitle;
}

// Normalize a process field into a clean array of strings.
// Handles: proper arrays, raw JSON strings like '["A","B"]',
// comma-delimited strings, and strips stray brackets/quotes/asterisks.
function normalizeProcesses(value) {
    if (!value) return [];
    const items = Array.isArray(value) ? value : [String(value)];
    const result = [];
    for (const item of items) {
        let s = String(item).trim();
        // Strip outer [ ] if the whole string is a bracket-wrapped list
        s = s.replace(/^\[|\]$/g, '').trim();
        // Split on commas (user-specified delimiter)
        for (const part of s.split(',')) {
            const cleaned = part
                .replace(/["'\[\]\*]/g, '')  // remove quotes, brackets, asterisks
                .trim();
            if (cleaned) result.push(cleaned);
        }
    }
    return result;
}

// Create process content - handle both string and array formats
function createProcessContent(process) {
    const processes = normalizeProcesses(process);
    if (!processes.length) return '<em style="opacity: 0.7;">N/A</em>';
    return processes.map(p => `<span class="process-tag">${escapeHtml(p)}</span>`).join(' ');
}

// Create authors content - handle both string and array formats
function createAuthorsContent(authors) {
    if (!authors) return '<em style="opacity: 0.7;">Unknown</em>';
    
    // Handle array of authors
    if (Array.isArray(authors)) {
        return authors.map(author => `<span class="author-tag">${escapeHtml(author)}</span>`).join(' ');
    }

    // Handle single author (backward compatibility)
    return `<span class="author-tag">${escapeHtml(authors)}</span>`;
}

// Helper function for process search matching
function matchesProcessSearch(processField, searchTerm) {
    return normalizeProcesses(processField).some(p => p.toLowerCase().includes(searchTerm));
}

// Helper function for authors search matching
function matchesAuthorsSearch(authorsField, searchTerm) {
    if (!authorsField) return false;
    
    if (Array.isArray(authorsField)) {
        return authorsField.some(author => author.toLowerCase().includes(searchTerm));
    }
    
    return authorsField.toLowerCase().includes(searchTerm);
}

// Helper function for process filter matching
function matchesProcessFilter(processField, filterValue) {
    return normalizeProcesses(processField).includes(filterValue);
}

// Read all entry fields from an add/edit form by prefix ('new' or 'edit')
function readEntryForm(prefix) {
    return {
        title: document.getElementById(`${prefix}-title`).value,
        journal: document.getElementById(`${prefix}-journal`).value,
        authors: parseAuthorsInput(document.getElementById(`${prefix}-authors`).value),
        url: document.getElementById(`${prefix}-url`).value || '',
        year: parseInt(document.getElementById(`${prefix}-year`).value, 10),
        volume: parseInt(document.getElementById(`${prefix}-volume`).value, 10),
        issue: parseInt(document.getElementById(`${prefix}-issue`).value, 10),
        pages: document.getElementById(`${prefix}-pages`).value || '',
        abstract: document.getElementById(`${prefix}-abstract`).value || '',
        process: parseProcessInput(document.getElementById(`${prefix}-process`).value),
        'static-equation': document.getElementById(`${prefix}-static-equation`).value || '',
        'static-equation-definitions': document.getElementById(`${prefix}-static-definitions`).value || '',
        'recursive-equation': document.getElementById(`${prefix}-recursive-equation`).value || '',
        'recursive-equation-definitions': document.getElementById(`${prefix}-recursive-definitions`).value || '',
    };
}

// Parse process input from form (handles comma-separated values)
function parseProcessInput(processInput) {
    if (!processInput || typeof processInput !== 'string') return '';
    
    // Split by comma, trim whitespace, and remove empty values
    const processes = processInput.split(',')
        .map(p => p.trim())
        .filter(p => p.length > 0);
    
    // Return single string if only one process, array if multiple
    return processes.length === 1 ? processes[0] : processes;
}

// Parse authors input from form (handles & or comma-separated values)
function parseAuthorsInput(authorsInput) {
    if (!authorsInput || typeof authorsInput !== 'string') return '';
    
    // Split by & first, then by comma, trim whitespace, and remove empty values
    let authors = [];
    if (authorsInput.includes(' & ')) {
        authors = authorsInput.split(' & ');
    } else {
        authors = authorsInput.split(',');
    }
    
    authors = authors
        .map(a => a.trim())
        .filter(a => a.length > 0);
    
    // Return single string if only one author, array if multiple
    return authors.length === 1 ? authors[0] : authors;
}

// Normalize an equation field to a plain string (global version for use outside renderPage)
function normalizeEqGlobal(eq) {
    if (!eq) return '';
    if (Array.isArray(eq)) return eq.filter(Boolean).join('; ');
    return eq;
}

// Format authors array for edit form input
function formatAuthorsForInput(authors) {
    if (!authors) return '';
    if (Array.isArray(authors)) return authors.join(' & ');
    return authors;
}

// Format process field for edit form input
function formatProcessForInput(process) {
    if (!process) return '';
    if (Array.isArray(process)) return process.join(', ');
    return process;
}

// Create equation content for table cell - render both types directly in table
function createEquationContent(equation, definitions) {
    if (!equation || equation === 'N/A' || equation === 'None' || equation.trim() === '') {
        return '<em style="opacity: 0.7;">N/A</em>';
    }
    
    // Prepare equation for rendering
    let renderedEquation = equation;
    if (!equation.includes('$')) {
        renderedEquation = `$$${equation}$$`;
    }
    
    let content = `<div class="equation-display">${escapeHtml(renderedEquation)}</div>`;
    
    // Add definitions if available - render each on a new line
    if (definitions && definitions.trim() !== '') {
        const definitionList = definitions
            // treat MathJax line breaks as separators too
            .replace(/\\\\/g, ' __BRK__ ')
            .split(/;|__BRK__/)
            .map(def => def.trim())
            .filter(Boolean);
        
        if (definitionList.length > 0) {
            content += `
                <div class="equation-definitions-block">
                    <div class="where-label">Where:</div>
                    ${definitionList.map(def => {
                        let processedDef = def.trim();
                        
                        // Keep MathJax formatting intact
                        if (!processedDef.startsWith('$')) {
                            processedDef = `$${processedDef}$`;
                        }
                        
                        return `<div class="definition-item">${escapeHtml(processedDef)}</div>`;
                    }).join('')}
                </div>
            `;
        }
    }
    
    return content;
}

// ── Column Sorting ────────────────────────────────────────────────────────
const NUMERIC_SORT_KEYS = new Set(['year', 'volume', 'issue']);

function getSortValue(article, key) {
    if (key === 'authors') {
        const a = article.authors;
        if (Array.isArray(a) && a.length) return String(a[0]).toLowerCase();
        return String(a || '').toLowerCase();
    }
    if (key === 'process') {
        const p = article.process;
        if (Array.isArray(p) && p.length) return String(p[0]).toLowerCase();
        return String(p || '').toLowerCase();
    }
    if (key === 'journal') return (article.journal || 'JEAB').toLowerCase();
    const val = article[key];
    if (NUMERIC_SORT_KEYS.has(key)) return Number(val) || 0;
    return String(val || '').toLowerCase();
}

function sortData(data, key, dir) {
    const sorted = [...data];
    const isNumeric = NUMERIC_SORT_KEYS.has(key);
    const mult = dir === 'asc' ? 1 : -1;
    sorted.sort((a, b) => {
        const va = getSortValue(a, key);
        const vb = getSortValue(b, key);
        if (isNumeric) return (va - vb) * mult;
        if (va < vb) return -1 * mult;
        if (va > vb) return 1 * mult;
        return 0;
    });
    return sorted;
}

function handleSort(key) {
    if (currentSortKey === key) {
        if (currentSortDir === 'asc') currentSortDir = 'desc';
        else if (currentSortDir === 'desc') { currentSortKey = null; currentSortDir = null; }
    } else {
        currentSortKey = key;
        currentSortDir = 'asc';
    }
    updateSortIndicators();
    // Re-sort current filtered data in place and re-render
    if (currentSortKey) {
        currentFilteredData = sortData(currentFilteredData, currentSortKey, currentSortDir);
    } else {
        // Restore original filter order by re-applying filters
        applyFilters();
        return;
    }
    currentPage = 1;
    renderPage();
}

function updateSortIndicators() {
    document.querySelectorAll('.data-table th[data-sort-key]').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
        if (th.dataset.sortKey === currentSortKey) {
            th.classList.add(currentSortDir === 'asc' ? 'sort-asc' : 'sort-desc');
        }
    });
}

function initializeSorting() {
    document.querySelectorAll('.data-table th[data-sort-key]').forEach(th => {
        th.addEventListener('click', () => handleSort(th.dataset.sortKey));
    });
}

// Table population and management
function populateTable(data) {
    currentFilteredData = currentSortKey
        ? sortData(data, currentSortKey, currentSortDir)
        : data;
    currentPage = 1;
    renderPage();
}

function renderPage() {
    const tableBody = document.getElementById('table-body');
    tableBody.innerHTML = '';

    const start = (currentPage - 1) * rowsPerPage;
    const pageData = currentFilteredData.slice(start, start + rowsPerPage);

    pageData.forEach((article, index) => {
        const row = document.createElement('tr');

        const staticEquation = normalizeEqGlobal(article['static-equation']);
        const staticDefinitions = article['static-equation-definitions'] || '';
        const recursiveEquation = normalizeEqGlobal(article['recursive-equation']);
        const recursiveDefinitions = article['recursive-equation-definitions'] || '';

        const isReviewed = article.reviewed === true ||
            (article.signoffs || []).length >= SIGNOFF_THRESHOLD;
        const statusBadge = isReviewed
            ? `<span class="badge-reviewed">✓ Reviewed</span>`
            : `<span class="badge-needs-review">Needs Review</span>`;

        let signoffBtn = '';
        if (githubToken && githubUsername &&
            !(article.signoffs || []).includes(githubUsername) &&
            (article.signoffs || []).length < SIGNOFF_THRESHOLD) {
            signoffBtn = `<button class="signoff-btn" title="Verify this entry is accurate">✓ Verify</button>`;
        }

        row.innerHTML = `
            <td class="article-title">
                ${createTitleContent(article.title, article.url)}
                <div class="row-meta">
                    ${statusBadge}
                    ${signoffBtn}
                    <button class="edit-row-btn" title="Suggest a correction">✏</button>
                </div>
            </td>
            <td class="journal-cell">${createJournalBadge(article.journal)}</td>
            <td class="authors">${createAuthorsContent(article.authors)}</td>
            <td class="year">${escapeHtml(article.year)}</td>
            <td class="volume">${escapeHtml(article.volume)}</td>
            <td class="issue">${escapeHtml(article.issue)}</td>
            <td class="pages">${escapeHtml(article.pages) || 'N/A'}</td>
            <td class="abstract-cell">${createAbstractContent(article.abstract || 'No abstract available', index)}</td>
            <td class="process">${createProcessContent(article.process)}</td>
            <td class="static-equation">${createEquationContent(staticEquation, staticDefinitions)}</td>
            <td class="recursive-equation">${createEquationContent(recursiveEquation, recursiveDefinitions)}</td>
        `;

        tableBody.appendChild(row);

        const signoffEl = row.querySelector('.signoff-btn');
        if (signoffEl) {
            signoffEl.addEventListener('click', async (e) => {
                e.stopPropagation();
                if (signoffEl.disabled) return;
                signoffEl.disabled = true;
                signoffEl.textContent = '⏳';
                try {
                    await createSignoffPullRequest(article);
                } finally {
                    signoffEl.disabled = false;
                    signoffEl.textContent = '✓ Verify';
                }
            });
        }

        row.querySelector('.edit-row-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            openEditModal(article);
        });
    });
    
    // Re-render MathJax after table update
    if (window.MathJax) {
        setTimeout(() => {
            if (window.MathJax.typesetPromise) {
                MathJax.startup.document.clear();
                MathJax.typesetPromise([tableBody]).catch(function (err) {
                    console.log('MathJax typeset failed: ' + err.message);
                });
            } else if (window.MathJax.Hub) {
                MathJax.Hub.Queue(["Typeset", MathJax.Hub, tableBody]);
            }
        }, 200);
    }

    renderPagination();
}

function renderPagination() {
    const total = currentFilteredData.length;
    const totalPages = Math.max(1, Math.ceil(total / rowsPerPage));
    const start = total === 0 ? 0 : (currentPage - 1) * rowsPerPage + 1;
    const end = Math.min(currentPage * rowsPerPage, total);

    let bar = document.getElementById('pagination-bar');
    if (!bar) return;

    bar.innerHTML = `
        <div class="pagination-info">
            Showing <strong>${start}–${end}</strong> of <strong>${total}</strong> entries
        </div>
        <div class="pagination-controls">
            <button class="page-btn" id="page-prev" ${currentPage === 1 ? 'disabled' : ''}>&#8592; Prev</button>
            <span class="page-indicator">Page ${currentPage} / ${totalPages}</span>
            <button class="page-btn" id="page-next" ${currentPage >= totalPages ? 'disabled' : ''}>Next &#8594;</button>
        </div>
        <div class="pagination-size">
            Show:
            ${[20, 50, 100].map(n => `
                <button class="size-btn ${rowsPerPage === n ? 'active' : ''}" data-size="${n}">${n}</button>
            `).join('')}
        </div>
    `;

    bar.querySelector('#page-prev').addEventListener('click', () => {
        if (currentPage > 1) { currentPage--; renderPage(); window.scrollTo(0, 0); }
    });
    bar.querySelector('#page-next').addEventListener('click', () => {
        if (currentPage < totalPages) { currentPage++; renderPage(); window.scrollTo(0, 0); }
    });
    bar.querySelectorAll('.size-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            rowsPerPage = parseInt(btn.dataset.size, 10);
            currentPage = 1;
            renderPage();
        });
    });
}

// Filter population
function populateFilters() {
    const yearFilter = document.getElementById('year-filter');
    const volumeFilter = document.getElementById('volume-filter');
    const issueFilter = document.getElementById('issue-filter');
    const processFilter = document.getElementById('process-filter');

    // Helper: clear dropdown options, keeping the first default "All..." option
    function clearDropdown(select) {
        const defaultOption = select.querySelector('option');
        select.innerHTML = '';
        if (defaultOption) select.appendChild(defaultOption);
    }

    clearDropdown(yearFilter);
    clearDropdown(volumeFilter);
    clearDropdown(issueFilter);
    clearDropdown(processFilter);

    // Get unique years and sort
    const years = [...new Set(behavioralData.map(article => article.year).filter(y => y != null))].sort((a, b) => b - a);
    years.forEach(year => {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year;
        yearFilter.appendChild(option);
    });

    // Get unique volumes and sort
    const volumes = [...new Set(behavioralData.map(article => article.volume).filter(v => v != null))].sort((a, b) => a - b);
    volumes.forEach(volume => {
        const option = document.createElement('option');
        option.value = volume;
        option.textContent = volume;
        volumeFilter.appendChild(option);
    });

    // Get unique issues and sort
    const issues = [...new Set(behavioralData.map(article => article.issue).filter(i => i != null))].sort((a, b) => a - b);
    issues.forEach(issue => {
        const option = document.createElement('option');
        option.value = issue;
        option.textContent = issue;
        issueFilter.appendChild(option);
    });

    // Get unique processes — normalize all entries through normalizeProcesses()
    // so raw JSON strings, comma-lists, stray brackets etc. are cleaned first
    const allProcesses = [];
    behavioralData.forEach(article => {
        allProcesses.push(...normalizeProcesses(article.process));
    });
    const processes = [...new Set(allProcesses)].filter(Boolean).sort();
    processes.forEach(process => {
        const option = document.createElement('option');
        option.value = process;
        option.textContent = process;
        processFilter.appendChild(option);
    });
    
}

// Attach filter event listeners (called once at init, not on every populateFilters call)
function initializeFilterListeners() {
    const yearFilter = document.getElementById('year-filter');
    const volumeFilter = document.getElementById('volume-filter');

    document.getElementById('journal-filter').addEventListener('change', applyFilters);
    yearFilter.addEventListener('change', () => { rebuildDependentDropdowns(); applyFilters(); });
    volumeFilter.addEventListener('change', () => { rebuildDependentDropdowns(); applyFilters(); });
    document.getElementById('issue-filter').addEventListener('change', applyFilters);
    document.getElementById('process-filter').addEventListener('change', applyFilters);
    document.getElementById('review-filter').addEventListener('change', applyFilters);
}

// Rebuild volume and issue dropdowns based on current year/volume selection
function rebuildDependentDropdowns() {
    const yearVal   = document.getElementById('year-filter').value;
    const volumeVal = document.getElementById('volume-filter').value;
    const volumeFilter = document.getElementById('volume-filter');
    const issueFilter  = document.getElementById('issue-filter');

    // Narrow dataset by year first
    let subset = behavioralData;
    if (yearVal) {
        subset = subset.filter(a => a.year != null && a.year.toString() === yearVal);
    }

    // Rebuild volume options from year-filtered subset
    const prevVolume = volumeFilter.value;
    volumeFilter.innerHTML = '<option value="">All Volumes</option>';
    [...new Set(subset.map(a => a.volume).filter(v => v != null))]
        .sort((a, b) => a - b)
        .forEach(v => {
            const opt = document.createElement('option');
            opt.value = v; opt.textContent = v;
            volumeFilter.appendChild(opt);
        });
    // Restore volume selection if it still exists in the new list
    if (prevVolume && [...volumeFilter.options].some(o => o.value === prevVolume)) {
        volumeFilter.value = prevVolume;
    }

    // Narrow further by (possibly restored) volume for issue options
    const activeVolume = volumeFilter.value;
    if (activeVolume) {
        subset = subset.filter(a => a.volume != null && a.volume.toString() === activeVolume);
    }

    // Rebuild issue options from year+volume-filtered subset
    const prevIssue = issueFilter.value;
    issueFilter.innerHTML = '<option value="">All Issues</option>';
    [...new Set(subset.map(a => a.issue).filter(i => i != null))]
        .sort((a, b) => a - b)
        .forEach(i => {
            const opt = document.createElement('option');
            opt.value = i; opt.textContent = i;
            issueFilter.appendChild(opt);
        });
    // Restore issue selection if it still exists in the new list
    if (prevIssue && [...issueFilter.options].some(o => o.value === prevIssue)) {
        issueFilter.value = prevIssue;
    }
}

// Search functionality
function initializeSearch() {
    const searchInput = document.getElementById('search-input');
    const searchButton = document.querySelector('.search-btn');
    
    function performSearch() {
        applyFilters();
    }
    
    searchInput.addEventListener('input', debounce(performSearch, 300));
    searchButton.addEventListener('click', performSearch);
    
    // Add enter key support
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
}

// Apply filters and search
function applyFilters() {
    const searchTerm = filterEls.search.value.toLowerCase();
    const journalFilter = filterEls.journal.value;
    const yearFilter = filterEls.year.value;
    const volumeFilter = filterEls.volume.value;
    const issueFilter = filterEls.issue.value;
    const processFilter = filterEls.process.value;
    const reviewFilter = filterEls.review.value;

    let filteredData = behavioralData;

    // Apply journal filter
    if (journalFilter) {
        filteredData = filteredData.filter(article => (article.journal || 'JEAB') === journalFilter);
    }

    // Apply search filter
    if (searchTerm) {
        filteredData = filteredData.filter(article =>
            (article.title || '').toLowerCase().includes(searchTerm) ||
            (article.journal || 'JEAB').toLowerCase().includes(searchTerm) ||
            matchesProcessSearch(article.process, searchTerm) ||
            matchesAuthorsSearch(article.authors, searchTerm) ||
            (article['static-equation'] && [].concat(article['static-equation']).join(' ').toLowerCase().includes(searchTerm)) ||
            (article['static-equation-definitions'] && article['static-equation-definitions'].toLowerCase().includes(searchTerm)) ||
            (article['recursive-equation'] && [].concat(article['recursive-equation']).join(' ').toLowerCase().includes(searchTerm)) ||
            (article['recursive-equation-definitions'] && article['recursive-equation-definitions'].toLowerCase().includes(searchTerm)) ||
            (article.abstract && article.abstract.toLowerCase().includes(searchTerm))
        );
    }

    // Apply year filter
    if (yearFilter) {
        filteredData = filteredData.filter(article => article.year != null && article.year.toString() === yearFilter);
    }

    // Apply volume filter
    if (volumeFilter) {
        filteredData = filteredData.filter(article => article.volume != null && article.volume.toString() === volumeFilter);
    }

    // Apply issue filter
    if (issueFilter) {
        filteredData = filteredData.filter(article => article.issue != null && article.issue.toString() === issueFilter);
    }

    // Apply process filter
    if (processFilter) {
        filteredData = filteredData.filter(article => matchesProcessFilter(article.process, processFilter));
    }

    // Apply review status filter
    if (reviewFilter === 'reviewed') {
        filteredData = filteredData.filter(a =>
            a.reviewed === true || (a.signoffs || []).length >= SIGNOFF_THRESHOLD);
    } else if (reviewFilter === 'needs-review') {
        filteredData = filteredData.filter(a =>
            a.reviewed !== true && (a.signoffs || []).length < SIGNOFF_THRESHOLD);
    }

    populateTable(filteredData);
}

// Debounce function for search
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Statistics calculation
function updateStatistics() {
    const totalArticles = behavioralData.length;
    const allProcesses = new Set();
    behavioralData.forEach(article => {
        normalizeProcesses(article.process).forEach(p => allProcesses.add(p));
    });
    const uniqueProcesses = allProcesses.size;
    const years = behavioralData.map(a => a.year).filter(y => y != null && y > 0);
    const minYear = years.reduce((m, y) => y < m ? y : m, Infinity);
    const maxYear = years.reduce((m, y) => y > m ? y : m, -Infinity);
    const yearRange = years.length ? `${minYear} - ${maxYear}` : 'N/A';
    const volumes = behavioralData.map(a => a.volume).filter(v => v != null && v > 0);
    const latestVolume = volumes.reduce((m, v) => v > m ? v : m, 0);

    // Per-journal counts
    const journalCounts = {};
    behavioralData.forEach(a => {
        const j = a.journal || 'JEAB';
        journalCounts[j] = (journalCounts[j] || 0) + 1;
    });

    // Animate the numbers
    animateNumber('total-articles', totalArticles);
    animateNumber('unique-processes', uniqueProcesses);
    document.getElementById('year-range').textContent = yearRange;
    animateNumber('latest-volume', latestVolume);

    // Render per-journal breakdown below stats grid
    let breakdownEl = document.getElementById('journal-breakdown');
    if (!breakdownEl) {
        breakdownEl = document.createElement('div');
        breakdownEl.id = 'journal-breakdown';
        breakdownEl.style.cssText = 'text-align:center;margin-top:16px;color:var(--text-muted);font-size:0.88rem;';
        document.querySelector('.stats-grid').after(breakdownEl);
    }
    const parts = Object.entries(journalCounts)
        .sort((a, b) => b[1] - a[1])
        .map(([j, c]) => `${j}: ${c.toLocaleString()}`);
    breakdownEl.textContent = parts.join('  ·  ');

    // Review progress bar
    const reviewedCount = behavioralData.filter(a =>
        a.reviewed === true || (a.signoffs || []).length >= SIGNOFF_THRESHOLD
    ).length;
    const pct = totalArticles > 0 ? ((reviewedCount / totalArticles) * 100) : 0;
    const progressEl = document.getElementById('review-progress');
    if (progressEl) {
        progressEl.innerHTML = `
            <h3>Review Progress</h3>
            <div class="progress-bar-container">
                <div class="progress-bar-fill" id="progress-bar-fill" style="width: 0%"></div>
            </div>
            <p class="progress-label">
                <strong>${reviewedCount.toLocaleString()}</strong> of
                <strong>${totalArticles.toLocaleString()}</strong> entries reviewed
                (<strong>${pct.toFixed(1)}%</strong>)
            </p>
        `;
        requestAnimationFrame(() => {
            const fill = document.getElementById('progress-bar-fill');
            if (fill) fill.style.width = pct + '%';
        });
    }
}

// Number animation for statistics
function animateNumber(elementId, targetNumber) {
    const element = document.getElementById(elementId);
    const startNumber = 0;
    const duration = 1000;
    const startTime = performance.now();
    
    function updateNumber(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const currentNumber = Math.floor(startNumber + (targetNumber - startNumber) * easeOutCubic(progress));
        
        element.textContent = currentNumber;
        
        if (progress < 1) {
            requestAnimationFrame(updateNumber);
        }
    }
    
    requestAnimationFrame(updateNumber);
}

// Easing function for smooth animation
function easeOutCubic(t) {
    return 1 - Math.pow(1 - t, 3);
}

// Modal functionality
function initializeModal() {
    const modal = document.getElementById('add-entry-modal');
    const addButton = document.querySelector('.add-entry-btn');
    const closeButton = document.querySelector('.close-modal');
    const form = document.getElementById('add-entry-form');
    
    // Open modal
    addButton.addEventListener('click', function() {
        openModal(modal);
    });

    // Close modal
    closeButton.addEventListener('click', function() {
        closeModal(modal, form);
    });

    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            closeModal(modal, form);
        }
    });
    
    // Handle form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const submitButton = form.querySelector('.submit-btn');
        const originalText = submitButton.textContent;
        submitButton.textContent = 'Processing...';
        submitButton.disabled = true;
        
        const newEntry = readEntryForm('new');
        if (!newEntry.abstract) newEntry.abstract = 'No abstract available';

        if (githubUsername) {
            newEntry.contributor = githubUsername;
            newEntry.signoffs = [];
        }

        try {
            if (githubToken) {
                // Try to create pull request
                const pullRequest = await createPullRequest(newEntry);
                
                // Show success with PR link
                showPullRequestSuccess(pullRequest);
                
                // Also add to local data for immediate display
                behavioralData.push(newEntry);
                saveData();
                
            } else {
                // No token — open pre-filled GitHub Issue
                window.open(buildNewEntryIssueUrl(newEntry), '_blank');
                showSuccessMessage('A GitHub Issue has been opened with your entry. A maintainer will review and add it to the catalog.');
            }
            
            // Update table and filters
            populateTable(behavioralData);
            populateFilters();
            updateStatistics();
            
            // Close modal and reset form
            closeModal(modal, form);

        } catch (error) {
            console.error('Error submitting entry:', error);

            // PR failed — fall back to GitHub Issue
            window.open(buildNewEntryIssueUrl(newEntry), '_blank');

            // Close modal
            closeModal(modal, form);

            showErrorMessage(`Pull request failed: ${error.message}. A GitHub Issue has been opened instead.`);
        } finally {
            submitButton.textContent = originalText;
            submitButton.disabled = false;
        }
    });
}

// Pull request success message
// Unified toast notification
function showToast(contentOrMessage, type = 'success', duration = 3000) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    if (typeof contentOrMessage === 'string') {
        toast.textContent = contentOrMessage;
    } else {
        toast.appendChild(contentOrMessage);
    }
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('toast-exit');
        setTimeout(() => {
            if (document.body.contains(toast)) document.body.removeChild(toast);
        }, 500);
    }, duration);
}

function showPullRequestSuccess(pullRequest) {
    const prUrl = pullRequest.html_url;
    const safeUrl = (typeof prUrl === 'string' && prUrl.startsWith('https://')) ? prUrl : '#';
    const content = document.createElement('div');
    content.innerHTML = `
        <div>Pull request created successfully!</div>
        <div style="margin-top: 8px;">
            <a href="${escapeHtml(safeUrl)}" target="_blank" rel="noopener" style="color: var(--bg-dark); text-decoration: underline;">
                View PR #${escapeHtml(String(pullRequest.number))}
            </a>
        </div>
        <div style="font-size: 0.9em; margin-top: 4px;">Your contribution will be reviewed and merged if approved.</div>
    `;
    showToast(content, 'success', 5000);
}

function showSuccessMessage(message) {
    showToast(message, 'success', 3000);
}

function showErrorMessage(message) {
    showToast(message, 'error', 5000);
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K for search focus
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        document.getElementById('search-input').focus();
    }
    
    // Escape key to close modals
    if (e.key === 'Escape') {
        const modal = document.getElementById('add-entry-modal');
        if (modal.style.display === 'block') {
            closeModal(modal, document.getElementById('add-entry-form'));
        }
        const editModal = document.getElementById('edit-entry-modal');
        if (editModal && editModal.style.display === 'block') {
            closeEditModal();
        }
    }
    
    // Ctrl/Cmd + Enter to add new entry (only when not focused on an input or inside a modal)
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        const tag = document.activeElement && document.activeElement.tagName;
        const inInput = tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT';
        const inModal = document.activeElement && document.activeElement.closest('.modal');
        if (!inInput && !inModal) {
            e.preventDefault();
            document.querySelector('.add-entry-btn').click();
        }
    }
});

// No popup functions needed - equations render directly in table

// CSV Export functionality
function exportTableToCSV() {
    // Use the already-filtered data from the last applyFilters() call
    const currentData = currentFilteredData;
    
    if (currentData.length === 0) {
        showToast('No data to export. Please check your filters.', 'error');
        return;
    }
    
    // Define CSV headers
    const headers = [
        'Article Title',
        'Journal',
        'Authors',
        'Year',
        'Volume',
        'Issue',
        'Pages',
        'Abstract',
        'Behavioral Process',
        'Static Equation',
        'Static Equation Definitions',
        'Recursive Equation',
        'Recursive Equation Definitions',
        'URL'
    ];

    // Convert data to CSV format
    const csvContent = [
        headers.join(','),
        ...currentData.map(article => [
            `"${(article.title || '').replace(/"/g, '""')}"`,
            `"${(article.journal || 'JEAB').replace(/"/g, '""')}"`,
            `"${formatAuthorsForCSV(article.authors)}"`,
            article.year || '',
            article.volume || '',
            article.issue || '',
            `"${(article.pages || '').replace(/"/g, '""')}"`,
            `"${(article.abstract || '').replace(/"/g, '""')}"`,
            `"${formatProcessForCSV(article.process)}"`,
            `"${cleanEquationForCSV(normalizeEqGlobal(article['static-equation']))}"`,
            `"${normalizeEqGlobal(article['static-equation-definitions']).replace(/"/g, '""')}"`,
            `"${cleanEquationForCSV(normalizeEqGlobal(article['recursive-equation']))}"`,
            `"${normalizeEqGlobal(article['recursive-equation-definitions']).replace(/"/g, '""')}"`,
            `"${(article.url || '').replace(/"/g, '""')}"`
        ].join(','))
    ].join('\n');
    
    // Create and trigger download
    const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        
        // Generate filename with timestamp
        const now = new Date();
        const timestamp = now.toISOString().slice(0, 19).replace(/:/g, '-');
        link.setAttribute('download', `behavioral-data-export-${timestamp}.csv`);
        
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }
}

// Clean LaTeX equations for CSV export (remove LaTeX markup)
function cleanEquationForCSV(equation) {
    if (!equation) return '';
    
    // Remove LaTeX delimiters and basic formatting
    return equation
        .replace(/\$+/g, '')           // Remove $ delimiters
        .replace(/\\begin\{[^}]+\}/g, '') // Remove \begin{} commands
        .replace(/\\end\{[^}]+\}/g, '')   // Remove \end{} commands
        .replace(/\\[a-zA-Z]+/g, '')      // Remove LaTeX commands
        .replace(/[{}]/g, '')             // Remove braces
        .replace(/\s+/g, ' ')             // Normalize whitespace
        .trim();
}

// Format process field for CSV export
function formatProcessForCSV(processField) {
    if (!processField) return '';
    
    if (Array.isArray(processField)) {
        return processField.join('; ').replace(/"/g, '""');
    }

    return processField.replace(/"/g, '""');
}

// Format authors field for CSV export
function formatAuthorsForCSV(authorsField) {
    if (!authorsField) return '';
    
    if (Array.isArray(authorsField)) {
        return authorsField.join('; ').replace(/"/g, '""');
    }
    
    return authorsField.replace(/"/g, '""');
}

// ── Edit Entry Feature ────────────────────────────────────────────────────

function closeEditModal() {
    const modal = document.getElementById('edit-entry-modal');
    if (modal) {
        closeModal(modal, document.getElementById('edit-entry-form'));
    }
}

function openEditModal(article) {
    editModalOriginalArticle = article;
    document.getElementById('edit-title').value = article.title || '';
    document.getElementById('edit-authors').value = formatAuthorsForInput(article.authors);
    document.getElementById('edit-url').value = article.url || '';
    document.getElementById('edit-journal').value = article.journal || 'JEAB';
    document.getElementById('edit-year').value = article.year || '';
    document.getElementById('edit-volume').value = article.volume || '';
    document.getElementById('edit-issue').value = article.issue || '';
    document.getElementById('edit-pages').value = article.pages || '';
    document.getElementById('edit-abstract').value = article.abstract || '';
    document.getElementById('edit-process').value = formatProcessForInput(article.process);
    document.getElementById('edit-static-equation').value = normalizeEqGlobal(article['static-equation']);
    document.getElementById('edit-static-definitions').value = article['static-equation-definitions'] || '';
    document.getElementById('edit-recursive-equation').value = normalizeEqGlobal(article['recursive-equation']);
    document.getElementById('edit-recursive-definitions').value = article['recursive-equation-definitions'] || '';

    openModal(document.getElementById('edit-entry-modal'));
}

function initializeEditModal() {
    const modal = document.getElementById('edit-entry-modal');
    const closeButton = document.querySelector('.close-edit-modal');
    const form = document.getElementById('edit-entry-form');

    closeButton.addEventListener('click', closeEditModal);

    window.addEventListener('click', function(event) {
        if (event.target === modal) closeEditModal();
    });

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        const original = editModalOriginalArticle;
        if (!original) return;

        const submitButton = form.querySelector('.submit-btn');
        const originalText = submitButton.textContent;
        submitButton.textContent = 'Processing...';
        submitButton.disabled = true;

        const editedEntry = { ...original, ...readEntryForm('edit') };

        if (githubUsername) {
            const existing = editedEntry.correctors || [];
            if (!existing.includes(githubUsername)) {
                editedEntry.correctors = [...existing, githubUsername];
            }
        }

        try {
            if (githubToken) {
                await createEditPullRequest(original, editedEntry);
            } else {
                window.open(buildGitHubIssueUrl(original, editedEntry), '_blank');
                showSuccessMessage('Opening GitHub issue with your correction. Thank you!');
                closeEditModal();
            }
        } catch (error) {
            console.error('Error submitting correction:', error);
            showErrorMessage(`Failed to submit correction: ${error.message}`);
        } finally {
            submitButton.textContent = originalText;
            submitButton.disabled = false;
        }
    });
}

async function createEditPullRequest(original, edited) {
    if (!githubToken) {
        throw new Error('GitHub token not found. Please connect your GitHub account first.');
    }

    try {
        const currentData = await fetchUpstreamData();

        // Find and replace the entry (match on title+year+journal)
        const idx = currentData.findIndex(e =>
            e.title === original.title && e.year === original.year &&
            (e.journal || 'JEAB') === (original.journal || 'JEAB'));
        if (idx === -1) {
            window.open(buildGitHubIssueUrl(original, edited), '_blank');
            showSuccessMessage('Could not locate entry in data file. Opening GitHub issue instead.');
            closeEditModal();
            return;
        }

        currentData[idx] = edited;
        const { forkOwner, branchName, baseSha } = await ensureForkAndBranch('edit-entry');

        const pr = await commitAndCreatePR({
            forkOwner, branchName, baseSha, updatedData: currentData,
            commitMessage: `Correction: ${original.title.slice(0, 60)}`,
            prTitle: `Correction: ${original.title.slice(0, 60)}`,
            prBody: `## Suggested Correction\n\n**Article:** ${original.title}\n**Journal:** ${original.journal || 'JEAB'} (${original.year}, Vol. ${original.volume})\n\nSubmitted via catalog edit form.`
        });

        showPullRequestSuccess(pr);
        closeEditModal();
    } catch (error) {
        console.error('Error creating edit pull request:', error);
        throw error;
    }
}

function buildGitHubIssueUrl(original, edited) {
    const fields = ['title', 'journal', 'authors', 'url', 'year', 'volume', 'issue', 'pages',
                    'process', 'static-equation', 'static-equation-definitions',
                    'recursive-equation', 'recursive-equation-definitions'];
    const changed = fields.filter(f => {
        const a = Array.isArray(original[f]) ? original[f].join('; ') : String(original[f] || '');
        const b = Array.isArray(edited[f]) ? edited[f].join('; ') : String(edited[f] || '');
        return a !== b;
    });

    let body = `## Suggested Correction\n\n`;
    body += `**Article:** ${original.title} (${original.year}, Vol. ${original.volume})\n\n`;
    body += `### Changed Fields\n| Field | Current | Suggested |\n|---|---|---|\n`;
    for (const f of changed) {
        const curr = String(original[f] || '').slice(0, 120);
        const sugg = String(edited[f] || '').slice(0, 120);
        body += `| ${f} | ${curr} | ${sugg} |\n`;
    }
    body += `\n*Submitted via catalog edit form*`;

    const title = encodeURIComponent(`Correction: ${original.title.slice(0, 60)}`);
    const bodyEnc = encodeURIComponent(body);
    return `https://github.com/david-j-cox/catalog-of-principles-and-processes/issues/new?title=${title}&body=${bodyEnc}`;
}

// ── New Entry Issue Fallback ──────────────────────────────────────────────

function buildNewEntryIssueUrl(entry) {
    const process = Array.isArray(entry.process) ? entry.process.join('; ') : String(entry.process || '');
    let body = `## New Entry Submission\n\n`;
    body += `| Field | Value |\n|---|---|\n`;
    body += `| Title | ${entry.title || ''} |\n`;
    body += `| Journal | ${entry.journal || 'JEAB'} |\n`;
    body += `| Authors | ${[].concat(entry.authors || []).join('; ')} |\n`;
    body += `| URL | ${entry.url || ''} |\n`;
    body += `| Year | ${entry.year || ''} |\n`;
    body += `| Volume | ${entry.volume || ''} |\n`;
    body += `| Issue | ${entry.issue || ''} |\n`;
    body += `| Pages | ${entry.pages || ''} |\n`;
    body += `| Abstract | ${(entry.abstract || '').slice(0, 300)} |\n`;
    body += `| Process | ${process} |\n`;
    body += `| Static Equation | ${(entry['static-equation'] || '').slice(0, 500)} |\n`;
    body += `| Static Equation Definitions | ${(entry['static-equation-definitions'] || '').slice(0, 500)} |\n`;
    body += `| Recursive Equation | ${(entry['recursive-equation'] || '').slice(0, 500)} |\n`;
    body += `| Recursive Equation Definitions | ${(entry['recursive-equation-definitions'] || '').slice(0, 500)} |\n`;
    body += `\n*Submitted via catalog add-entry form*`;

    const title = encodeURIComponent(`New entry: ${(entry.title || '').slice(0, 60)}`);
    const bodyEnc = encodeURIComponent(body);
    return `https://github.com/${GITHUB_CONFIG.owner}/${GITHUB_CONFIG.repo}/issues/new?title=${title}&body=${bodyEnc}`;
}

// ── Signoff Pull Request ──────────────────────────────────────────────────

async function createSignoffPullRequest(article) {
    if (!githubToken || !githubUsername) return;

    const signoffs = article.signoffs || [];
    if (signoffs.includes(githubUsername)) {
        showSuccessMessage("You've already verified this entry.");
        return;
    }

    try {
        const currentData = await fetchUpstreamData();

        // Find entry and add signoff (match on title+year+journal)
        const idx = currentData.findIndex(e =>
            e.title === article.title && e.year === article.year &&
            (e.journal || 'JEAB') === (article.journal || 'JEAB'));
        if (idx === -1) throw new Error('Could not locate entry in data file');

        const newSignoffs = [...(currentData[idx].signoffs || []), githubUsername];
        currentData[idx].signoffs = newSignoffs;
        if (newSignoffs.length >= SIGNOFF_THRESHOLD) {
            currentData[idx].reviewed = true;
        }

        const { forkOwner, branchName, baseSha } = await ensureForkAndBranch('signoff-entry');

        const signoffCount = newSignoffs.length;
        const pr = await commitAndCreatePR({
            forkOwner, branchName, baseSha, updatedData: currentData,
            commitMessage: `Signoff: ${article.title.slice(0, 60)}`,
            prTitle: `Signoff: ${article.title.slice(0, 60)}`,
            prBody: `## Verification Sign-off\n\n**Article:** ${article.title}\n**Journal:** ${article.journal || 'JEAB'} (${article.year}, Vol. ${article.volume})\n\n**Sign-off count:** ${signoffCount}/${SIGNOFF_THRESHOLD}\n\nVerified by @${githubUsername} via the Behavioral Process Catalog web interface.`
        });

        showPullRequestSuccess(pr);
    } catch (error) {
        console.error('Error creating signoff pull request:', error);
        showErrorMessage(`Failed to submit verification: ${error.message}`);
    }
}

// ── Leaderboard ───────────────────────────────────────────────────────────

function computeLeaderboard() {
    const stats = {};
    for (const entry of behavioralData) {
        // Original submission credit
        if (entry.contributor) {
            if (!stats[entry.contributor]) {
                stats[entry.contributor] = { verified: 0, pending: 0, corrections: 0, reviews: 0 };
            }
            const n = (entry.signoffs || []).length;
            if (n >= SIGNOFF_THRESHOLD) {
                stats[entry.contributor].verified++;
            } else {
                stats[entry.contributor].pending++;
            }
        }
        // Correction credit
        for (const c of (entry.correctors || [])) {
            if (!stats[c]) stats[c] = { verified: 0, pending: 0, corrections: 0, reviews: 0 };
            stats[c].corrections++;
        }
        // Sign-off credit
        for (const r of (entry.signoffs || [])) {
            if (!stats[r]) stats[r] = { verified: 0, pending: 0, corrections: 0, reviews: 0 };
            stats[r].reviews++;
        }
    }
    return Object.entries(stats)
        .map(([name, s]) => ({
            name, ...s,
            score: s.verified * 3 + s.pending + s.corrections + s.reviews
        }))
        .sort((a, b) => b.score - a.score);
}

function renderMySubmissions() {
    const existing = document.getElementById('my-submissions');
    const container = document.getElementById('leaderboard-container');
    if (!container) return;

    if (!githubUsername) {
        if (existing) existing.remove();
        return;
    }

    const submitted = [];
    const corrected = [];
    const verified = [];

    behavioralData.forEach(entry => {
        if (entry.contributor === githubUsername) submitted.push(entry);
        if ((entry.correctors || []).includes(githubUsername)) corrected.push(entry);
        if ((entry.signoffs || []).includes(githubUsername)) verified.push(entry);
    });

    // Build combined list with roles for the compact table
    const seen = new Set();
    const rows = [];
    const addRow = (entry, role) => {
        const key = entry.title + '|' + entry.year;
        if (!seen.has(key)) {
            seen.add(key);
            rows.push({ entry, role });
        }
    };
    submitted.forEach(e => addRow(e, 'Submitted'));
    corrected.forEach(e => addRow(e, 'Corrected'));
    verified.forEach(e => addRow(e, 'Verified'));

    let dash = existing;
    if (!dash) {
        dash = document.createElement('div');
        dash.id = 'my-submissions';
        dash.className = 'my-submissions';
        container.parentNode.insertBefore(dash, container);
    }

    if (rows.length === 0) {
        dash.innerHTML = `
            <h3>My Activity &mdash; @${escapeHtml(githubUsername)}</h3>
            <p class="my-empty">No submissions, corrections, or verifications yet. Get started by adding or verifying an entry!</p>
        `;
        return;
    }

    const MAX_ROWS = 10;
    const displayRows = rows.slice(0, MAX_ROWS);
    const remaining = rows.length - MAX_ROWS;

    const tableRows = displayRows.map(({ entry, role }) => {
        const isReviewed = entry.reviewed === true ||
            (entry.signoffs || []).length >= SIGNOFF_THRESHOLD;
        const badge = isReviewed
            ? '<span class="badge-reviewed">Reviewed</span>'
            : '<span class="badge-needs-review">Needs Review</span>';
        return `<tr>
            <td>${escapeHtml(role)}</td>
            <td>${escapeHtml(entry.title)}</td>
            <td>${escapeHtml(entry.year)}</td>
            <td>${badge}</td>
        </tr>`;
    }).join('');

    dash.innerHTML = `
        <h3>My Activity &mdash; @${escapeHtml(githubUsername)}</h3>
        <div class="my-stats-row">
            <div class="my-stat">
                <div class="my-stat-num">${submitted.length}</div>
                <div class="my-stat-label">Submitted</div>
            </div>
            <div class="my-stat">
                <div class="my-stat-num">${corrected.length}</div>
                <div class="my-stat-label">Corrected</div>
            </div>
            <div class="my-stat">
                <div class="my-stat-num">${verified.length}</div>
                <div class="my-stat-label">Verified</div>
            </div>
        </div>
        <table class="my-entries-table">
            <thead><tr>
                <th>Role</th>
                <th>Title</th>
                <th>Year</th>
                <th>Status</th>
            </tr></thead>
            <tbody>${tableRows}</tbody>
        </table>
        ${remaining > 0 ? `<p class="my-more-note">${remaining} more not shown</p>` : ''}
    `;
}

function renderContributors() {
    renderMySubmissions();
    const container = document.getElementById('leaderboard-container');
    if (!container) return;

    const leaders = computeLeaderboard();
    const totalVerified = behavioralData.filter(e =>
        e.reviewed === true || (e.signoffs || []).length >= SIGNOFF_THRESHOLD
    ).length;

    if (leaders.length === 0) {
        container.innerHTML = `
            <p class="no-contributors">No contributors yet. Connect your GitHub account and add or verify entries to appear here!</p>
        `;
        return;
    }

    const medals = ['🥇', '🥈', '🥉'];

    const rows = leaders.map((l, i) => {
        const rankCell = i < 3
            ? `<span class="rank-medal">${medals[i]}</span>`
            : `#${i + 1}`;
        const rowClass = i < 3 ? ' class="top-contributor"' : '';
        const safeName = escapeHtml(l.name);
        return `
            <tr${rowClass}>
                <td class="rank-cell">${rankCell}</td>
                <td class="contributor-name"><a href="https://github.com/${encodeURIComponent(l.name)}" target="_blank" rel="noopener noreferrer">@${safeName}</a></td>
                <td class="stat-cell verified-cell">${l.verified}</td>
                <td class="stat-cell">${l.pending}</td>
                <td class="stat-cell">${l.corrections}</td>
                <td class="stat-cell">${l.reviews}</td>
                <td class="stat-cell score-cell">${l.score}</td>
            </tr>
        `;
    }).join('');

    container.innerHTML = `
        <div class="leaderboard-stats">
            <span>${leaders.length} contributor${leaders.length !== 1 ? 's' : ''}</span>
            <span>·</span>
            <span>${totalVerified} verified ${totalVerified !== 1 ? 'entries' : 'entry'}</span>
        </div>
        <table class="leaderboard-table">
            <thead>
                <tr>
                    <th class="rank-cell">Rank</th>
                    <th>Contributor</th>
                    <th class="stat-cell">Verified</th>
                    <th class="stat-cell">Pending</th>
                    <th class="stat-cell">Corrections</th>
                    <th class="stat-cell">Reviews Given</th>
                    <th class="stat-cell">Score</th>
                </tr>
            </thead>
            <tbody>${rows}</tbody>
        </table>
        <p class="scoring-note">Verified contribution: 3 pts · Pending contribution: 1 pt · Correction: 1 pt · Verification given: 1 pt</p>
    `;
}


