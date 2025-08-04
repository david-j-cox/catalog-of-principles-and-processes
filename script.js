// Behavioral Process Catalog - JavaScript Functionality

// Behavioral data will be loaded from data.json
let behavioralData = [];

// GitHub configuration
const GITHUB_CONFIG = {
    owner: 'david-j-cox',
    repo: 'catalog-of-principles-and-processes',
    dataFile: 'data.json'
};

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
        console.error('Error loading data:', error);
        // Fallback to localStorage only
        const savedData = localStorage.getItem('behavioralData');
        if (savedData) {
            behavioralData = JSON.parse(savedData);
        }
        return behavioralData;
    }
}

// Save data to localStorage
function saveData() {
    localStorage.setItem('behavioralData', JSON.stringify(behavioralData));
}

// GitHub API Functions
let githubToken = localStorage.getItem('github_token');

function initializeGitHubAuth() {
    const authSection = document.createElement('div');
    authSection.innerHTML = `
        <div id="github-auth" class="github-auth-panel">
            <div class="auth-content">
                <h3>🔗 Connect to GitHub</h3>
                <p>To contribute entries to the catalog, connect your GitHub account:</p>
                <div class="auth-controls">
                    <input type="password" id="github-token" placeholder="GitHub Personal Access Token" 
                           style="display: ${githubToken ? 'none' : 'block'}">
                    <button id="connect-github" class="auth-btn">${githubToken ? '✅ Connected' : 'Connect GitHub'}</button>
                    <button id="disconnect-github" class="auth-btn secondary" 
                            style="display: ${githubToken ? 'block' : 'none'}">Disconnect</button>
                </div>
                <div class="auth-help">
                    <a href="https://github.com/settings/tokens/new?scopes=repo&description=Behavioral%20Process%20Catalog" 
                       target="_blank">📝 Create a GitHub token</a>
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
    document.getElementById('connect-github').textContent = connected ? '✅ Connected' : 'Connect GitHub';
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
**Year:** ${newEntry.year}
**Volume:** ${newEntry.volume}
**Issue:** ${newEntry.issue}
**Behavioral Process:** ${newEntry.process}
**Equation:** ${newEntry.equation || 'N/A'}

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

// Table population and management
function populateTable(data) {
    const tableBody = document.getElementById('table-body');
    tableBody.innerHTML = '';
    
    data.forEach((article, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td class="article-title">${article.title}</td>
            <td class="year">${article.year}</td>
            <td class="volume">${article.volume}</td>
            <td class="issue">${article.issue}</td>
            <td class="process">${article.process}</td>
            <td class="equation">${article.equation || 'N/A'}</td>
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
}

// Filter population
function populateFilters() {
    const yearFilter = document.getElementById('year-filter');
    const processFilter = document.getElementById('process-filter');
    
    // Get unique years and sort
    const years = [...new Set(behavioralData.map(article => article.year))].sort((a, b) => b - a);
    years.forEach(year => {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year;
        yearFilter.appendChild(option);
    });
    
    // Get unique processes and sort
    const processes = [...new Set(behavioralData.map(article => article.process))].sort();
    processes.forEach(process => {
        const option = document.createElement('option');
        option.value = process;
        option.textContent = process;
        processFilter.appendChild(option);
    });
    
    // Add filter event listeners
    yearFilter.addEventListener('change', applyFilters);
    processFilter.addEventListener('change', applyFilters);
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
    
    let filteredData = behavioralData;
    
    // Apply search filter
    if (searchTerm) {
        filteredData = filteredData.filter(article => 
            article.title.toLowerCase().includes(searchTerm) ||
            article.process.toLowerCase().includes(searchTerm) ||
            (article.equation && article.equation.toLowerCase().includes(searchTerm))
        );
    }
    
    // Apply year filter
    if (yearFilter) {
        filteredData = filteredData.filter(article => article.year.toString() === yearFilter);
    }
    
    // Apply process filter
    if (processFilter) {
        filteredData = filteredData.filter(article => article.process === processFilter);
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
            year: parseInt(document.getElementById('new-year').value),
            volume: parseInt(document.getElementById('new-volume').value),
            issue: parseInt(document.getElementById('new-issue').value),
            process: document.getElementById('new-process').value,
            equation: document.getElementById('new-equation').value || 'N/A'
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
});

// Export functionality for potential future use
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