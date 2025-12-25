/**
 * Dashboard JavaScript
 * Handles form submission, progress tracking, and results visualization
 */

// Global state
let currentJobId = null;
let pollInterval = null;
let lineChartInstance = null;
let barChartInstance = null;

// DOM Elements
const form = document.getElementById('analysisForm');
const startButton = document.getElementById('startButton');
const progressSection = document.getElementById('progressSection');
const resultsSection = document.getElementById('resultsSection');
const errorSection = document.getElementById('errorSection');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Set today's date as default
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('targetDate').value = today;

    // Form submission handler
    form.addEventListener('submit', handleFormSubmit);

    // Download button handler
    document.getElementById('downloadButton').addEventListener('click', handleDownload);

    // Table search handler
    document.getElementById('tableSearch').addEventListener('input', handleTableSearch);

    // Check LLM status on page load
    checkLLMStatus();
});

/**
 * Handle form submission
 */
async function handleFormSubmit(e) {
    e.preventDefault();

    // Get form values
    const appId = document.getElementById('appId').value.trim();
    const targetDate = document.getElementById('targetDate').value;
    const days = parseInt(document.getElementById('days').value);

    // Validate
    if (!appId) {
        showError('Please enter an app package ID or Play Store link');
        return;
    }

    // Hide error and results, show progress
    hideError();
    hideResults();
    showProgress();

    // Disable form
    startButton.disabled = true;
    startButton.innerHTML = `
        <svg class="animate-spin w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
        </svg>
        Processing...
    `;

    try {
        // Start analysis
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                app_id: appId,
                target_date: targetDate,
                days: days
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to start analysis');
        }

        // Store job ID and start polling
        currentJobId = data.job_id;
        startPolling();

    } catch (error) {
        console.error('Error starting analysis:', error);
        showError(error.message);
        resetForm();
    }
}

/**
 * Start polling for job status
 */
function startPolling() {
    // Poll every 2 seconds
    pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/status/${currentJobId}`);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to get job status');
            }

            // Update progress
            updateProgress(data);

            // Check if job is complete
            if (data.status === 'completed') {
                stopPolling();
                await loadResults();
            } else if (data.status === 'failed') {
                stopPolling();
                showError(data.error || 'Analysis failed');
                resetForm();
            }

        } catch (error) {
            console.error('Error polling status:', error);
            stopPolling();
            showError(error.message);
            resetForm();
        }
    }, 2000);
}

/**
 * Stop polling
 */
function stopPolling() {
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
}

/**
 * Update progress UI
 */
function updateProgress(data) {
    const { phase, progress_pct, message } = data;

    // Update progress bar
    document.getElementById('progressBar').style.width = `${progress_pct}%`;
    document.getElementById('progressPercent').textContent = `${progress_pct}%`;
    document.getElementById('progressPhase').textContent = phase;
    document.getElementById('progressMessage').textContent = message;

    // Update phase checklist
    const phaseMapping = {
        'Data Collection': 1,
        'Topic Extraction': 2,
        'Topic Consolidation': 3,
        'Trend Analysis': 4,
        'Report Generation': 5,
        'Complete': 5
    };

    const currentPhaseNum = phaseMapping[phase] || 0;

    for (let i = 1; i <= 5; i++) {
        const phaseEl = document.getElementById(`phase${i}`);
        const iconEl = phaseEl.querySelector('.phase-icon');
        const textEl = phaseEl.querySelector('.phase-text');

        if (i < currentPhaseNum) {
            // Completed phase
            iconEl.textContent = '✅';
            phaseEl.classList.remove('text-gray-500');
            phaseEl.classList.add('text-green-600', 'font-medium');
        } else if (i === currentPhaseNum) {
            // Current phase
            iconEl.textContent = '⏳';
            phaseEl.classList.remove('text-gray-500', 'text-green-600');
            phaseEl.classList.add('text-blue-600', 'font-semibold');
        } else {
            // Pending phase
            iconEl.textContent = '⏳';
            phaseEl.classList.remove('text-green-600', 'text-blue-600', 'font-medium', 'font-semibold');
            phaseEl.classList.add('text-gray-500');
        }
    }
}

/**
 * Load and display results
 */
async function loadResults() {
    try {
        const response = await fetch(`/api/results/${currentJobId}`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to load results');
        }

        // Hide progress, show results
        hideProgress();
        showResults();
        resetForm();

        // Update summary cards
        document.getElementById('totalReviews').textContent = data.summary.total_reviews.toLocaleString();
        document.getElementById('totalTopics').textContent = data.summary.total_topics;
        document.getElementById('dateRange').textContent = data.summary.date_range;

        // Render charts
        renderLineChart(data.line_chart);
        renderBarChart(data.bar_chart);
        renderTopicsTable(data.topics_table);

    } catch (error) {
        console.error('Error loading results:', error);
        showError(error.message);
        resetForm();
    }
}

/**
 * Render line chart (Topic trends over time)
 */
function renderLineChart(chartData) {
    const ctx = document.getElementById('lineChart').getContext('2d');

    // Destroy existing chart
    if (lineChartInstance) {
        lineChartInstance.destroy();
    }

    // Set Chart.js defaults for dark mode
    Chart.defaults.color = '#a3a3a3'; // Light gray text
    Chart.defaults.borderColor = '#1a1a1a'; // Dark borders

    lineChartInstance = new Chart(ctx, {
        type: 'line',
        data: chartData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        boxWidth: 12,
                        padding: 10,
                        font: {
                            size: 11
                        },
                        color: '#a3a3a3'
                    }
                },
                title: {
                    display: true,
                    text: 'Top 10 Topics - Daily Mentions',
                    font: {
                        size: 14,
                        weight: 'normal'
                    },
                    color: '#ffffff'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: '#111111',
                    borderColor: '#1a1a1a',
                    borderWidth: 1,
                    titleColor: '#ffffff',
                    bodyColor: '#a3a3a3'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0,
                        color: '#a3a3a3'
                    },
                    title: {
                        display: true,
                        text: 'Number of Mentions',
                        color: '#a3a3a3'
                    },
                    grid: {
                        color: '#1a1a1a'
                    }
                },
                x: {
                    ticks: {
                        color: '#a3a3a3'
                    },
                    title: {
                        display: true,
                        text: 'Date',
                        color: '#a3a3a3'
                    },
                    grid: {
                        color: '#1a1a1a'
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

/**
 * Render bar chart (Top topics by frequency)
 */
function renderBarChart(chartData) {
    const ctx = document.getElementById('barChart').getContext('2d');

    // Destroy existing chart
    if (barChartInstance) {
        barChartInstance.destroy();
    }

    barChartInstance = new Chart(ctx, {
        type: 'bar',
        data: chartData,
        options: {
            indexAxis: 'y',  // Horizontal bar chart
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: 'Top 15 Topics - Total Mentions',
                    font: {
                        size: 14,
                        weight: 'normal'
                    },
                    color: '#ffffff'
                },
                tooltip: {
                    backgroundColor: '#111111',
                    borderColor: '#1a1a1a',
                    borderWidth: 1,
                    titleColor: '#ffffff',
                    bodyColor: '#a3a3a3',
                    callbacks: {
                        label: function(context) {
                            return `Mentions: ${context.parsed.x}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0,
                        color: '#a3a3a3'
                    },
                    title: {
                        display: true,
                        text: 'Total Mentions',
                        color: '#a3a3a3'
                    },
                    grid: {
                        color: '#1a1a1a'
                    }
                },
                y: {
                    ticks: {
                        color: '#a3a3a3'
                    },
                    grid: {
                        color: '#1a1a1a'
                    }
                }
            }
        }
    });
}

/**
 * Render topics table
 */
function renderTopicsTable(topics) {
    const tbody = document.getElementById('topicsTableBody');
    tbody.innerHTML = '';

    topics.forEach((topic, index) => {
        const row = document.createElement('tr');
        row.className = index % 2 === 0 ? 'bg-[#0a0a0a]' : 'bg-[#111111]';
        row.innerHTML = `
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${index + 1}</td>
            <td class="px-6 py-4 text-sm font-medium text-white">${escapeHtml(topic.topic)}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-white">
                <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-600/30 text-blue-400 border border-blue-500/30">
                    ${topic.total_count.toLocaleString()}
                </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-400">${topic.variation_count}</td>
        `;
        tbody.appendChild(row);
    });

    // Store original data for filtering
    tbody.dataset.originalData = JSON.stringify(topics);
}

/**
 * Handle table search/filter
 */
function handleTableSearch(e) {
    const searchTerm = e.target.value.toLowerCase();
    const tbody = document.getElementById('topicsTableBody');
    const originalData = JSON.parse(tbody.dataset.originalData || '[]');

    if (!searchTerm) {
        renderTopicsTable(originalData);
        return;
    }

    const filtered = originalData.filter(topic =>
        topic.topic.toLowerCase().includes(searchTerm)
    );

    renderTopicsTable(filtered);
}

/**
 * Handle Excel download
 */
async function handleDownload() {
    if (!currentJobId) {
        showError('No analysis results available');
        return;
    }

    try {
        // Open download in new tab
        window.open(`/api/download/${currentJobId}`, '_blank');
    } catch (error) {
        console.error('Error downloading file:', error);
        showError('Failed to download Excel file');
    }
}

/**
 * Show/Hide UI sections
 */
function showProgress() {
    progressSection.classList.remove('hidden');
}

function hideProgress() {
    progressSection.classList.add('hidden');
}

function showResults() {
    resultsSection.classList.remove('hidden');
}

function hideResults() {
    resultsSection.classList.add('hidden');
}

function showError(message) {
    errorSection.classList.remove('hidden');
    document.getElementById('errorMessage').textContent = message;
}

function hideError() {
    errorSection.classList.add('hidden');
}

/**
 * Reset form to initial state
 */
function resetForm() {
    startButton.disabled = false;
    startButton.innerHTML = `
        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
        </svg>
        Start Analysis
    `;
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Format date for display
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

/**
 * Check LLM provider status and display banner
 */
async function checkLLMStatus() {
    try {
        const response = await fetch('/api/health/llm');
        const data = await response.json();

        const banner = document.getElementById('llmStatusBanner');
        banner.classList.remove('hidden');

        if (data.status === 'ok') {
            // Ollama is ready
            const modelInfo = data.extraction_model && data.consolidation_model
                ? `${data.extraction_model} (extraction) + ${data.consolidation_model} (consolidation)`
                : data.models ? data.models.join(', ') : 'Ready';

            banner.innerHTML = `
                <div class="bg-green-900/30 border border-green-500/50 rounded-lg p-4 flex items-start">
                    <svg class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    <div class="flex-1">
                        <p class="text-sm font-medium text-green-400">
                            ${data.message}
                        </p>
                        <p class="text-xs text-green-300 mt-1">
                            Models: ${modelInfo}
                            ${data.provider === 'ollama' ? ' • 100% Free & Local' : ''}
                        </p>
                    </div>
                </div>
            `;
        } else if (data.status === 'warning') {
            // Missing models
            banner.innerHTML = `
                <div class="bg-yellow-900/30 border border-yellow-500/50 rounded-lg p-4 flex items-start">
                    <svg class="w-5 h-5 text-yellow-500 mr-3 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
                    </svg>
                    <div class="flex-1">
                        <p class="text-sm font-medium text-yellow-400">
                            ${data.message}
                        </p>
                        ${data.instructions ? `<p class="text-xs text-yellow-300 mt-1 font-mono">${escapeHtml(data.instructions)}</p>` : ''}
                    </div>
                </div>
            `;
        } else {
            // Error
            banner.innerHTML = `
                <div class="bg-red-900/30 border border-red-500/50 rounded-lg p-4 flex items-start">
                    <svg class="w-5 h-5 text-red-500 mr-3 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    <div class="flex-1">
                        <p class="text-sm font-medium text-red-400">
                            ${data.message}
                        </p>
                        ${data.instructions ? `<p class="text-xs text-red-300 mt-1">${escapeHtml(data.instructions)}</p>` : ''}
                    </div>
                </div>
            `;
        }
    } catch (error) {
        console.error('Failed to check LLM status:', error);
        // Silently fail - don't show error banner if health check fails
    }
}
