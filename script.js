// Behavioral Process Catalog - JavaScript Functionality

// Behavioral data will be loaded from data.json
let behavioralData = [];

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
        "process": "Getting Started",
        "equation": "N/A",
        "abstract": "This is a demonstration entry. For full functionality, please view this site through GitHub Pages or run a local web server. The complete database is stored in data.json and will load automatically when served over HTTP."
    },
    {
        "title": "Effects of Variable-Ratio Schedules on Response Rate in Pigeons",
        "year": 1995,
        "volume": 63,
        "issue": 2,
        "process": "Variable-Ratio Reinforcement",
        "equation": "R = k × (SR/t)",
        "abstract": "Six pigeons responded under variable-ratio (VR) schedules ranging from VR 10 to VR 200. Response rates increased as a power function of ratio size, with individual differences in the exponent."
    }
];

// Load data from data.json file
async function loadData() {
    try {
        const response = await fetch('data.json');
        const jsonData = await response.json();
        
        // Merge with any local additions
        const savedData = localStorage.getItem('behavioralData');
        if (savedData) {
            const localData = JSON.parse(savedData);
            // Only keep local entries that aren't in the main data
            const localOnlyEntries = localData.filter(localEntry => 
                !jsonData.some(jsonEntry => 
                    jsonEntry.title === localEntry.title && 
                    jsonEntry.year === localEntry.year
                )
            );
            behavioralData = [...jsonData, ...localOnlyEntries];
        } else {
            behavioralData = jsonData;
        }
        
        return behavioralData;
    } catch (error) {
        console.error('Error loading data.json (likely due to local file access), using fallback data:', error);
        
        // Use fallback data, then merge with localStorage
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
        } else {
            behavioralData = fallbackData;
        }
        
        return behavioralData;
    }
}

// Save data to localStorage
function saveData() {
    localStorage.setItem('behavioralData', JSON.stringify(behavioralData));
}

// Create abstract content with expand/collapse functionality
function createAbstractContent(abstract, articleIndex) {
    if (!abstract || abstract === 'No abstract available') {
        return '<em style="opacity: 0.7;">No abstract available</em>';
    }
    
    // Truncate to approximately one line (about 80 characters)
    const maxLength = 80;
    const truncated = abstract.length > maxLength ? abstract.substring(0, maxLength) : abstract;
    const needsTruncation = abstract.length > maxLength;
    
    const contentId = `abstract-${articleIndex}`;
    const btnId = `btn-${articleIndex}`;
    
    return `
        <div class="abstract-content collapsed" id="${contentId}">
            ${needsTruncation ? truncated + '...' : abstract}
        </div>
        ${needsTruncation ? `<button class="read-more-btn" id="${btnId}" onclick="toggleAbstract('${contentId}', '${btnId}', \`${abstract.replace(/`/g, '\\`').replace(/"/g, '&quot;')}\`)">Read More</button>` : ''}
    `;
}

// Toggle abstract expand/collapse
function toggleAbstract(contentId, btnId, fullText) {
    const content = document.getElementById(contentId);
    const button = document.getElementById(btnId);
    
    if (!content || !button) return;
    
    const isCollapsed = content.classList.contains('collapsed');
    
    if (isCollapsed) {
        // Expand
        content.classList.remove('collapsed');
        content.classList.add('expanded');
        content.innerHTML = fullText;
        button.textContent = 'Read Less';
    } else {
        // Collapse
        content.classList.remove('expanded');
        content.classList.add('collapsed');
        const truncated = fullText.length > 80 ? fullText.substring(0, 80) + '...' : fullText;
        content.innerHTML = truncated;
        button.textContent = 'Read More';
    }
}

// GitHub API Functions
let githubToken = localStorage.getItem('github_token');

function initializeGitHubAuth() {
    const authSection = document.createElement('div');
    authSection.innerHTML = `
        <div id="github-auth" class="github-auth-panel">
            <div class="auth-content">
                <h3>Connect to GitHub</h3>
                <p>To contribute entries to the catalog, connect your GitHub account:</p>
                <div class="auth-controls">
                    <input type="password" id="github-token" placeholder="GitHub Personal Access Token" 
                           style="display: ${githubToken ? 'none' : 'block'}">
                    <button id="connect-github" class="auth-btn">${githubToken ? 'Connected' : 'Connect GitHub'}</button>
                    <button id="disconnect-github" class="auth-btn secondary" 
                            style="display: ${githubToken ? 'block' : 'none'}">Disconnect</button>
                </div>
                <div class="auth-help">
                    <a href="https://github.com/settings/tokens/new?scopes=repo&description=Behavioral%20Process%20Catalog" 
                       target="_blank">Create a GitHub token</a>
                    <small>Requires 'repo' scope for creating pull requests</small>
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
    validateGitHubToken(token).then(isValid => {
        if (isValid) {
            githubToken = token;
            localStorage.setItem('github_token', token);
            updateAuthUI(true);
            showSuccessMessage('Successfully connected to GitHub!');
        } else {
            showErrorMessage('Invalid GitHub token. Please check and try again.');
        }
    });
}

function handleGitHubDisconnect() {
    githubToken = null;
    localStorage.removeItem('github_token');
    updateAuthUI(false);
    showSuccessMessage('Disconnected from GitHub');
}

function updateAuthUI(connected) {
    document.getElementById('github-token').style.display = connected ? 'none' : 'block';
    document.getElementById('connect-github').textContent = connected ? 'Connected' : 'Connect GitHub';
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
        return response.ok;
    } catch (error) {
        console.error('Token validation failed:', error);
        return false;
    }
}

async function createPullRequest(newEntry) {
    if (!githubToken) {
        throw new Error('GitHub token not found. Please connect your GitHub account first.');
    }
    
    try {
        // 1. Get the current data.json file
        const dataResponse = await fetch(`https://api.github.com/repos/${GITHUB_CONFIG.owner}/${GITHUB_CONFIG.repo}/contents/${GITHUB_CONFIG.dataFile}`, {
            headers: {
                'Authorization': `token ${githubToken}`,
                'Accept': 'application/vnd.github.v3+json'
            }
        });
        
        if (!dataResponse.ok) {
            throw new Error('Failed to fetch current data file');
        }
        
        const dataFile = await dataResponse.json();
        const currentData = JSON.parse(atob(dataFile.content));
        
        // 2. Add the new entry
        const updatedData = [...currentData, newEntry];
        const updatedContent = btoa(JSON.stringify(updatedData, null, 4));
        
        // 3. Create a new branch
        const branchName = `add-entry-${Date.now()}`;
        const mainBranchResponse = await fetch(`https://api.github.com/repos/${GITHUB_CONFIG.owner}/${GITHUB_CONFIG.repo}/git/refs/heads/main`, {
            headers: {
                'Authorization': `token ${githubToken}`,
                'Accept': 'application/vnd.github.v3+json'
            }
        });
        
        const mainBranch = await mainBranchResponse.json();
        
        await fetch(`https://api.github.com/repos/${GITHUB_CONFIG.owner}/${GITHUB_CONFIG.repo}/git/refs`, {
            method: 'POST',
            headers: {
                'Authorization': `token ${githubToken}`,
                'Accept': 'application/vnd.github.v3+json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                ref: `refs/heads/${branchName}`,
                sha: mainBranch.object.sha
            })
        });
        
        // 4. Update the file in the new branch
        await fetch(`https://api.github.com/repos/${GITHUB_CONFIG.owner}/${GITHUB_CONFIG.repo}/contents/${GITHUB_CONFIG.dataFile}`, {
            method: 'PUT',
            headers: {
                'Authorization': `token ${githubToken}`,
                'Accept': 'application/vnd.github.v3+json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: `Add new entry: ${newEntry.title}`,
                content: updatedContent,
                sha: dataFile.sha,
                branch: branchName
            })
        });
        
        // 5. Create the pull request
        const prResponse = await fetch(`https://api.github.com/repos/${GITHUB_CONFIG.owner}/${GITHUB_CONFIG.repo}/pulls`, {
            method: 'POST',
            headers: {
                'Authorization': `token ${githubToken}`,
                'Accept': 'application/vnd.github.v3+json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                title: `Add new behavioral process entry: ${newEntry.title}`,
                head: branchName,
                base: 'main',
                body: `## New Behavioral Process Entry

**Article Title:** ${newEntry.title}
**Authors:** ${newEntry.authors}
**URL:** ${newEntry.url || 'No URL provided'}
**Year:** ${newEntry.year}
**Volume:** ${newEntry.volume}
**Issue:** ${newEntry.issue}
**Behavioral Process:** ${newEntry.process}
**Abstract:** ${newEntry.abstract || 'No abstract provided'}
**Static Equation:** ${newEntry['static-equation'] || 'N/A'}
**Static Equation Definitions:** ${newEntry['static-equation-definitions'] || 'N/A'}
**Recursive Equation:** ${newEntry['recursive-equation'] || 'N/A'}
**Recursive Equation Definitions:** ${newEntry['recursive-equation-definitions'] || 'N/A'}

This entry was submitted through the Behavioral Process Catalog web interface.

Please review and merge if appropriate.`
            })
        });
        
        if (!prResponse.ok) {
            throw new Error('Failed to create pull request');
        }
        
        const pullRequest = await prResponse.json();
        return pullRequest;
        
    } catch (error) {
        console.error('Error creating pull request:', error);
        throw error;
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', async function() {
    await loadData();
    initializeNavigation();
    populateTable(behavioralData);
    populateFilters();
    updateStatistics();
    initializeSearch();
    initializeModal();
    initializeGitHubAuth();
});

// Navigation functionality
function initializeNavigation() {
    const navButtons = document.querySelectorAll('.nav-btn');
    const contentSections = document.querySelectorAll('.content-section');

    navButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetView = this.getAttribute('data-view');
            
            // Update active nav button
            navButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // Update active content section
            contentSections.forEach(section => section.classList.remove('active'));
            document.getElementById(targetView + '-view').classList.add('active');
            
            // Update statistics if switching to stats view
            if (targetView === 'stats') {
                updateStatistics();
            }
        });
    });
}

// Create title content with optional link
function createTitleContent(title, url) {
    if (url && url.trim() !== '') {
        return `<a href="${url}" target="_blank" rel="noopener noreferrer" class="article-link">${title}</a>`;
    }
    return title;
}

// Create process content - handle both string and array formats
function createProcessContent(process) {
    if (!process) return '<em style="opacity: 0.7;">N/A</em>';
    
    // Handle array of processes
    if (Array.isArray(process)) {
        return process.map(p => `<span class="process-tag">${p}</span>`).join(' ');
    }
    
    // Handle single process (backward compatibility)
    return `<span class="process-tag">${process}</span>`;
}

// Create authors content - handle both string and array formats
function createAuthorsContent(authors) {
    if (!authors) return '<em style="opacity: 0.7;">Unknown</em>';
    
    // Handle array of authors
    if (Array.isArray(authors)) {
        return authors.map(author => `<span class="author-tag">${author}</span>`).join(' ');
    }
    
    // Handle single author (backward compatibility)
    return `<span class="author-tag">${authors}</span>`;
}

// Helper function for process search matching
function matchesProcessSearch(processField, searchTerm) {
    if (!processField) return false;
    
    if (Array.isArray(processField)) {
        return processField.some(process => process.toLowerCase().includes(searchTerm));
    }
    
    return processField.toLowerCase().includes(searchTerm);
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
    if (!processField) return false;
    
    if (Array.isArray(processField)) {
        return processField.includes(filterValue);
    }
    
    return processField === filterValue;
}

// Helper function for author filter matching
function matchesAuthorFilter(authorsField, filterValue) {
    if (!authorsField) return false;
    
    if (Array.isArray(authorsField)) {
        return authorsField.includes(filterValue);
    }
    
    return authorsField === filterValue;
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

// Create equation content for table cell - render both types directly in table
function createEquationContent(equation, definitions) {
    if (!equation || equation === 'N/A' || equation === 'None' || equation.trim() === '') {
        return '<em style="opacity: 0.7;">N/A</em>';
    }
    
    // Prepare equation for rendering
    let renderedEquation = equation;
    if (equation.includes('$$')) {
        renderedEquation = equation;
    } else if (equation.includes('$')) {
        renderedEquation = equation;
    } else {
        renderedEquation = `$$${equation}$$`;
    }
    
    let content = `<div class="equation-display">${renderedEquation}</div>`;
    
    // Add definitions if available - render as LaTeX
    if (definitions && definitions.trim() !== '') {
        const definitionList = definitions.split(';').map(def => def.trim()).filter(def => def.length > 0);
        
        if (definitionList.length > 0) {
            content += `
                <div class="equation-definitions-inline">
                    <div class="where-label">Where:</div>
                    ${definitionList.map(def => {
                        // Smart LaTeX parsing: only wrap variables, keep text as regular text
                        let processedDef = def;
                        
                        if (!def.includes('$')) {
                            // Parse definition: variable = description
                            const parts = def.split('=');
                            if (parts.length === 2) {
                                const variable = parts[0].trim();
                                const description = parts[1].trim();
                                
                                // Wrap only the variable part in LaTeX, keep description as text
                                processedDef = `$${variable}$ = ${description}`;
                            } else {
                                // If no '=' found, treat as regular text
                                processedDef = def;
                            }
                        } else {
                            // Already has LaTeX markup, use as-is
                            processedDef = def;
                        }
                        
                        return `<div class="definition-item">${processedDef}</div>`;
                    }).join('')}
                </div>
            `;
        }
    }
    
    return content;
}

// Table population and management
function populateTable(data) {
    const tableBody = document.getElementById('table-body');
    tableBody.innerHTML = '';
    
    data.forEach((article, index) => {
        const row = document.createElement('tr');
        
        // Handle different equation field names for backward compatibility
        const staticEquation = article['static-equation'] || article.equation || '';
        const staticDefinitions = article['static-equation-definitions'] || '';
        const recursiveEquation = article['recursive-equation'] || '';
        const recursiveDefinitions = article['recursive-equation-definitions'] || '';
        
        row.innerHTML = `
            <td class="article-title">${createTitleContent(article.title, article.url)}</td>
            <td class="authors">${createAuthorsContent(article.authors)}</td>
            <td class="year">${article.year}</td>
            <td class="volume">${article.volume}</td>
            <td class="issue">${article.issue}</td>
            <td class="abstract-cell">${createAbstractContent(article.abstract || 'No abstract available', index)}</td>
            <td class="process">${createProcessContent(article.process)}</td>
            <td class="static-equation">${createEquationContent(staticEquation, staticDefinitions)}</td>
            <td class="recursive-equation">${createEquationContent(recursiveEquation, recursiveDefinitions)}</td>
        `;
        
        // Add click animation
        row.addEventListener('click', function() {
            this.style.animation = 'none';
            setTimeout(() => {
                this.style.animation = 'pulse 0.6s ease-in-out';
            }, 10);
        });
        
        tableBody.appendChild(row);
    });
    
    // Re-render MathJax after table update
    if (window.MathJax) {
        setTimeout(() => {
            if (window.MathJax.typesetPromise) {
                MathJax.typesetPromise([tableBody]).catch(function (err) {
                    console.log('MathJax typeset failed: ' + err.message);
                });
            }
        }, 200);
    }
}

// Filter population
function populateFilters() {
    const yearFilter = document.getElementById('year-filter');
    const processFilter = document.getElementById('process-filter');
    const authorFilter = document.getElementById('author-filter');
    
    // Get unique years and sort
    const years = [...new Set(behavioralData.map(article => article.year))].sort((a, b) => b - a);
    years.forEach(year => {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year;
        yearFilter.appendChild(option);
    });
    
    // Get unique processes and sort (flatten arrays)
    const allProcesses = [];
    behavioralData.forEach(article => {
        if (Array.isArray(article.process)) {
            allProcesses.push(...article.process);
        } else if (article.process) {
            allProcesses.push(article.process);
        }
    });
    const processes = [...new Set(allProcesses)].sort();
    processes.forEach(process => {
        const option = document.createElement('option');
        option.value = process;
        option.textContent = process;
        processFilter.appendChild(option);
    });
    
    // Get unique authors and sort (flatten arrays)
    const allAuthors = [];
    behavioralData.forEach(article => {
        if (Array.isArray(article.authors)) {
            allAuthors.push(...article.authors);
        } else if (article.authors) {
            allAuthors.push(article.authors);
        }
    });
    const authors = [...new Set(allAuthors)].sort();
    authors.forEach(author => {
        const option = document.createElement('option');
        option.value = author;
        option.textContent = author;
        authorFilter.appendChild(option);
    });
    
    // Add filter event listeners
    yearFilter.addEventListener('change', applyFilters);
    processFilter.addEventListener('change', applyFilters);
    authorFilter.addEventListener('change', applyFilters);
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
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    const yearFilter = document.getElementById('year-filter').value;
    const processFilter = document.getElementById('process-filter').value;
    const authorFilter = document.getElementById('author-filter').value;
    
    let filteredData = behavioralData;
    
    // Apply search filter
    if (searchTerm) {
        filteredData = filteredData.filter(article => 
            article.title.toLowerCase().includes(searchTerm) ||
            matchesProcessSearch(article.process, searchTerm) ||
            matchesAuthorsSearch(article.authors, searchTerm) ||
            (article.equation && article.equation.toLowerCase().includes(searchTerm)) ||
            (article['static-equation'] && article['static-equation'].toLowerCase().includes(searchTerm)) ||
            (article['static-equation-definitions'] && article['static-equation-definitions'].toLowerCase().includes(searchTerm)) ||
            (article['recursive-equation'] && article['recursive-equation'].toLowerCase().includes(searchTerm)) ||
            (article['recursive-equation-definitions'] && article['recursive-equation-definitions'].toLowerCase().includes(searchTerm)) ||
            (article.abstract && article.abstract.toLowerCase().includes(searchTerm))
        );
    }
    
    // Apply year filter
    if (yearFilter) {
        filteredData = filteredData.filter(article => article.year.toString() === yearFilter);
    }
    
    // Apply process filter
    if (processFilter) {
        filteredData = filteredData.filter(article => matchesProcessFilter(article.process, processFilter));
    }
    
    // Apply author filter
    if (authorFilter) {
        filteredData = filteredData.filter(article => matchesAuthorFilter(article.authors, authorFilter));
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
    const uniqueProcesses = new Set(behavioralData.map(article => article.process)).size;
    const years = behavioralData.map(article => article.year);
    const yearRange = `${Math.min(...years)} - ${Math.max(...years)}`;
    const latestVolume = Math.max(...behavioralData.map(article => article.volume));
    
    // Animate the numbers
    animateNumber('total-articles', totalArticles);
    animateNumber('unique-processes', uniqueProcesses);
    document.getElementById('year-range').textContent = yearRange;
    animateNumber('latest-volume', latestVolume);
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
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    });
    
    // Close modal
    closeButton.addEventListener('click', function() {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
        form.reset();
    });
    
    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
            form.reset();
        }
    });
    
    // Handle form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const submitButton = form.querySelector('.submit-btn');
        const originalText = submitButton.textContent;
        submitButton.textContent = 'Processing...';
        submitButton.disabled = true;
        
        const newEntry = {
            title: document.getElementById('new-title').value,
            authors: parseAuthorsInput(document.getElementById('new-authors').value),
            url: document.getElementById('new-url').value || '',
            year: parseInt(document.getElementById('new-year').value),
            volume: parseInt(document.getElementById('new-volume').value),
            issue: parseInt(document.getElementById('new-issue').value),
            abstract: document.getElementById('new-abstract').value || 'No abstract available',
            process: parseProcessInput(document.getElementById('new-process').value),
            'static-equation': document.getElementById('new-static-equation').value || '',
            'static-equation-definitions': document.getElementById('new-static-definitions').value || '',
            'recursive-equation': document.getElementById('new-recursive-equation').value || '',
            'recursive-equation-definitions': document.getElementById('new-recursive-definitions').value || ''
        };
        
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
                // Fallback to local storage only
                behavioralData.push(newEntry);
                saveData();
                showSuccessMessage('Entry saved locally! Connect GitHub to contribute to the main catalog.');
            }
            
            // Update table and filters
            populateTable(behavioralData);
            populateFilters();
            updateStatistics();
            
            // Close modal and reset form
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
            form.reset();
            
        } catch (error) {
            console.error('Error submitting entry:', error);
            
            // Fallback to local storage
            behavioralData.push(newEntry);
            saveData();
            populateTable(behavioralData);
            populateFilters();
            updateStatistics();
            
            // Close modal
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
            form.reset();
            
            showErrorMessage(`Failed to create pull request: ${error.message}. Entry saved locally instead.`);
        } finally {
            submitButton.textContent = originalText;
            submitButton.disabled = false;
        }
    });
}

// Pull request success message
function showPullRequestSuccess(pullRequest) {
    const successDiv = document.createElement('div');
    successDiv.innerHTML = `
        <div>🎉 Pull request created successfully!</div>
        <div style="margin-top: 8px;">
            <a href="${pullRequest.html_url}" target="_blank" style="color: var(--bg-dark); text-decoration: underline;">
                View PR #${pullRequest.number}
            </a>
        </div>
        <div style="font-size: 0.9em; margin-top: 4px;">Your contribution will be reviewed and merged if approved.</div>
    `;
    successDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: var(--success-green);
        color: var(--bg-dark);
        padding: 15px 25px;
        border-radius: 5px;
        font-family: 'Orbitron', monospace;
        font-weight: 700;
        z-index: 1001;
        animation: slideIn 0.5s ease-out;
        box-shadow: 0 5px 15px rgba(0, 255, 0, 0.3);
        max-width: 350px;
        line-height: 1.4;
    `;
    
    document.body.appendChild(successDiv);
    
    setTimeout(() => {
        successDiv.style.animation = 'slideOut 0.5s ease-in';
        setTimeout(() => {
            if (document.body.contains(successDiv)) {
                document.body.removeChild(successDiv);
            }
        }, 500);
    }, 5000);
}

// Success message display
function showSuccessMessage(message) {
    const successDiv = document.createElement('div');
    successDiv.textContent = message;
    successDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: var(--success-green);
        color: var(--bg-dark);
        padding: 15px 25px;
        border-radius: 5px;
        font-family: 'Orbitron', monospace;
        font-weight: 700;
        z-index: 1001;
        animation: slideIn 0.5s ease-out;
        box-shadow: 0 5px 15px rgba(0, 255, 0, 0.3);
    `;
    
    document.body.appendChild(successDiv);
    
    setTimeout(() => {
        successDiv.style.animation = 'slideOut 0.5s ease-in';
        setTimeout(() => {
            document.body.removeChild(successDiv);
        }, 500);
    }, 3000);
}

// Add CSS animations for success message
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K for search focus
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        document.getElementById('search-input').focus();
    }
    
    // Escape key to close modal
    if (e.key === 'Escape') {
        const modal = document.getElementById('add-entry-modal');
        if (modal.style.display === 'block') {
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
            document.getElementById('add-entry-form').reset();
        }
    }
    
    // Ctrl/Cmd + Enter to add new entry
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        document.querySelector('.add-entry-btn').click();
    }
});

// Add tooltips for keyboard shortcuts
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('search-input');
    const addButton = document.querySelector('.add-entry-btn');
    
    searchInput.title = 'Press Ctrl+K to focus search';
    addButton.title = 'Press Ctrl+Enter to add new entry';
    
    // Add CSV export button event listener
    const exportButton = document.getElementById('export-csv-btn');
    if (exportButton) {
        exportButton.addEventListener('click', exportTableToCSV);
    }
});

// No popup functions needed - equations render directly in table

// CSV Export functionality
function exportTableToCSV() {
    // Get currently displayed data (respects filters)
    const currentData = getCurrentDisplayedData();
    
    if (currentData.length === 0) {
        alert('No data to export. Please check your filters.');
        return;
    }
    
    // Define CSV headers
    const headers = [
        'Article Title',
        'Authors', 
        'Year',
        'Volume',
        'Issue',
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
            `"${formatAuthorsForCSV(article.authors)}"`,
            article.year || '',
            article.volume || '',
            article.issue || '',
            `"${(article.abstract || '').replace(/"/g, '""')}"`,
            `"${formatProcessForCSV(article.process)}"`,
            `"${cleanEquationForCSV(article['static-equation'] || article.equation || '')}"`,
            `"${(article['static-equation-definitions'] || '').replace(/"/g, '""')}"`,
            `"${cleanEquationForCSV(article['recursive-equation'] || '')}"`,
            `"${(article['recursive-equation-definitions'] || '').replace(/"/g, '""')}"`,
            `"${(article.url || '').replace(/"/g, '""')}"`
        ].join(','))
    ].join('\n');
    
    // Create and trigger download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
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
    }
}

// Get currently displayed data (respects search and filters)
function getCurrentDisplayedData() {
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    const yearFilter = document.getElementById('year-filter').value;
    const processFilter = document.getElementById('process-filter').value;
    
    return behavioralData.filter(article => {
        // Apply search filter
        const matchesSearch = !searchTerm || 
            (article.title && article.title.toLowerCase().includes(searchTerm)) ||
            matchesAuthorsSearch(article.authors, searchTerm) ||
            (article.abstract && article.abstract.toLowerCase().includes(searchTerm)) ||
            (article.process && matchesProcessSearch(article.process, searchTerm)) ||
            (article['static-equation'] && article['static-equation'].toLowerCase().includes(searchTerm)) ||
            (article['recursive-equation'] && article['recursive-equation'].toLowerCase().includes(searchTerm)) ||
            (article['static-equation-definitions'] && article['static-equation-definitions'].toLowerCase().includes(searchTerm)) ||
            (article['recursive-equation-definitions'] && article['recursive-equation-definitions'].toLowerCase().includes(searchTerm));
        
        // Apply year filter
        const matchesYear = !yearFilter || article.year.toString() === yearFilter;
        
        // Apply process filter
        const matchesProcess = !processFilter || matchesProcessFilter(article.process, processFilter);
        
        return matchesSearch && matchesYear && matchesProcess;
    });
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
        return processField.join('; ');
    }
    
    return processField.replace(/"/g, '""');
}

// Format authors field for CSV export
function formatAuthorsForCSV(authorsField) {
    if (!authorsField) return '';
    
    if (Array.isArray(authorsField)) {
        return authorsField.join('; ');
    }
    
    return authorsField.replace(/"/g, '""');
}

// Export functionality for potential future use (JSON)
function exportData() {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(behavioralData, null, 2));
    const downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href", dataStr);
    downloadAnchorNode.setAttribute("download", "behavioral_process_catalog.json");
    document.body.appendChild(downloadAnchorNode);
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
}

// Error handling
window.addEventListener('error', function(e) {
    console.error('Application error:', e.error);
    showErrorMessage('An error occurred. Please refresh the page.');
});

function showErrorMessage(message) {
    const errorDiv = document.createElement('div');
    errorDiv.textContent = message;
    errorDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: var(--warning-orange);
        color: var(--text-bright);
        padding: 15px 25px;
        border-radius: 5px;
        font-family: 'Orbitron', monospace;
        font-weight: 700;
        z-index: 1001;
        animation: slideIn 0.5s ease-out;
        box-shadow: 0 5px 15px rgba(255, 102, 0, 0.3);
    `;
    
    document.body.appendChild(errorDiv);
    
    setTimeout(() => {
        errorDiv.style.animation = 'slideOut 0.5s ease-in';
        setTimeout(() => {
            if (document.body.contains(errorDiv)) {
                document.body.removeChild(errorDiv);
            }
        }, 500);
    }, 5000);
}