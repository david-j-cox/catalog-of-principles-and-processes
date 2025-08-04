// Behavioral Process Catalog - JavaScript Functionality

// Sample data for demonstration
let behavioralData = [
    {
        title: "Effects of Variable-Ratio Schedules on Response Rate in Pigeons",
        year: 1995,
        volume: 63,
        issue: 2,
        process: "Variable-Ratio Reinforcement",
        equation: "R = k × (SR/t)"
    },
    {
        title: "Temporal Control in Fixed-Interval Schedules: A Quantitative Analysis",
        year: 1998,
        volume: 69,
        issue: 1,
        process: "Fixed-Interval Responding",
        equation: "P(t) = 1 - e^(-λt)"
    },
    {
        title: "Choice Behavior Under Concurrent Variable-Interval Schedules",
        year: 2001,
        volume: 75,
        issue: 3,
        process: "Concurrent Schedules",
        equation: "B₁/B₂ = (R₁/R₂)^a"
    },
    {
        title: "Delay Discounting and Self-Control in Humans",
        year: 2003,
        volume: 80,
        issue: 1,
        process: "Delay Discounting",
        equation: "V = A/(1 + kD)"
    },
    {
        title: "Stimulus Equivalence and Derived Relational Responding",
        year: 2005,
        volume: 84,
        issue: 2,
        process: "Stimulus Equivalence",
        equation: "P(match) = e^(s×S)/(1 + e^(s×S))"
    },
    {
        title: "Behavioral Economics of Drug Self-Administration",
        year: 2007,
        volume: 88,
        issue: 1,
        process: "Behavioral Economics",
        equation: "Q = Q₀ × 10^(-α×P^β)"
    },
    {
        title: "Resurgence of Previously Reinforced Behavior",
        year: 2010,
        volume: 94,
        issue: 3,
        process: "Resurgence",
        equation: "R(t) = R₀ × e^(-kt) + Rₑ"
    },
    {
        title: "Matching Law in Group Contingencies",
        year: 2012,
        volume: 98,
        issue: 2,
        process: "Matching Law",
        equation: "B₁/(B₁+B₂) = R₁/(R₁+R₂)"
    },
    {
        title: "Contextual Control of Operant Behavior",
        year: 2015,
        volume: 104,
        issue: 1,
        process: "Contextual Control",
        equation: "R = β₀ + β₁×C + β₂×S"
    },
    {
        title: "Peak-Shift Effects in Stimulus Generalization",
        year: 2018,
        volume: 110,
        issue: 2,
        process: "Peak Shift",
        equation: "G(x) = A × e^(-b(x-μ)²)"
    },
    {
        title: "Temporal Bisection and the Scalar Expectancy Theory",
        year: 2020,
        volume: 114,
        issue: 3,
        process: "Temporal Bisection",
        equation: "P(long) = 1/(1 + e^(-β(t-PSE)))"
    },
    {
        title: "Operant Variability and Behavioral Flexibility",
        year: 2022,
        volume: 118,
        issue: 1,
        process: "Operant Variability",
        equation: "U = -Σpᵢ × log₂(pᵢ)"
    }
];

// Load data from localStorage or use default data
function loadData() {
    const savedData = localStorage.getItem('behavioralData');
    if (savedData) {
        behavioralData = JSON.parse(savedData);
    }
    return behavioralData;
}

// Save data to localStorage
function saveData() {
    localStorage.setItem('behavioralData', JSON.stringify(behavioralData));
}

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    loadData();
    initializeNavigation();
    populateTable(behavioralData);
    populateFilters();
    updateStatistics();
    initializeSearch();
    initializeModal();
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
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const newEntry = {
            title: document.getElementById('new-title').value,
            year: parseInt(document.getElementById('new-year').value),
            volume: parseInt(document.getElementById('new-volume').value),
            issue: parseInt(document.getElementById('new-issue').value),
            process: document.getElementById('new-process').value,
            equation: document.getElementById('new-equation').value || 'N/A'
        };
        
        // Add to data array
        behavioralData.push(newEntry);
        
        // Save to localStorage
        saveData();
        
        // Update table and filters
        populateTable(behavioralData);
        populateFilters();
        updateStatistics();
        
        // Close modal and reset form
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
        form.reset();
        
        // Show success animation
        showSuccessMessage('Entry added successfully!');
    });
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