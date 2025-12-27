/**
 * Dashboard JavaScript - ChatGPT-like Interface
 * Handles history, progress tracking, chat, and results visualization
 */

// Global state
let currentJobId = null;
let pollInterval = null;
let lineChartInstance = null;
let barChartInstance = null;
let chatHistory = [];
let sidebarVisible = true;
let isSendingMessage = false;

// DOM Elements
const form = document.getElementById('analysisForm');
const startButton = document.getElementById('startButton');
const configPanel = document.getElementById('configPanel');
const progressPanel = document.getElementById('progressPanel');
const resultsPanel = document.getElementById('resultsPanel');
const errorPanel = document.getElementById('errorPanel');
const historySidebar = document.getElementById('historySidebar');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Set default date range (end date = today, start date = 30 days ago)
    const today = new Date();
    const endDate = today.toISOString().split('T')[0];

    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    const startDate = thirtyDaysAgo.toISOString().split('T')[0];

    document.getElementById('endDate').value = endDate;
    document.getElementById('startDate').value = startDate;

    // Handle days dropdown change
    document.getElementById('days').addEventListener('change', handleDaysChange);

    // Load job history
    loadJobHistory();

    // Refresh history every 10 seconds
    setInterval(loadJobHistory, 10000);

    // Event handlers
    form.addEventListener('submit', handleFormSubmit);
    document.getElementById('newAnalysisBtn').addEventListener('click', showConfigPanel);
    document.getElementById('toggleSidebarBtn').addEventListener('click', toggleSidebar);
    document.getElementById('downloadButton').addEventListener('click', handleDownload);
    document.getElementById('tableSearch').addEventListener('input', handleTableSearch);

    // History search
    document.getElementById('historySearch').addEventListener('input', handleHistorySearch);
});

/**
 * Handle days dropdown change
 */
function handleDaysChange(e) {
    const days = e.target.value;
    const customDateRange = document.getElementById('customDateRange');

    if (days === 'custom') {
        // Show custom date range inputs
        customDateRange.style.display = 'grid';
    } else {
        // Hide custom date range and update dates based on selection
        customDateRange.style.display = 'none';

        const today = new Date();
        const endDate = today.toISOString().split('T')[0];

        const pastDate = new Date();
        pastDate.setDate(pastDate.getDate() - parseInt(days));
        const startDate = pastDate.toISOString().split('T')[0];

        document.getElementById('endDate').value = endDate;
        document.getElementById('startDate').value = startDate;
    }
}

/**
 * Load and display job history
 */
async function loadJobHistory() {
    try {
        const response = await fetch('/api/history?limit=50');
        const data = await response.json();

        renderHistoryList(data.jobs);
    } catch (error) {
        console.error('Failed to load history:', error);
    }
}

/**
 * Render history list in sidebar
 */
function renderHistoryList(jobs) {
    const historyList = document.getElementById('historyList');

    if (!jobs || jobs.length === 0) {
        historyList.innerHTML = `
            <div class="text-center text-gray-600 text-sm py-8">
                No history yet
            </div>
        `;
        return;
    }

    const statusColors = {
        'completed': 'text-green-500',
        'failed': 'text-red-500',
        'running': 'text-blue-500',
        'cancelled': 'text-gray-500',
        'started': 'text-blue-500'
    };

    const statusIcons = {
        'completed': '✓',
        'failed': '✕',
        'running': '⚙️',      // Gear icon for active processing
        'started': '▶️',      // Play icon for just started
        'cancelled': '⏹️',     // Stop square
        'pending': '⏳'       // Hourglass for queued (if ever implemented)
    };

    historyList.innerHTML = jobs.map(job => `
        <div
            class="group p-3 mb-2 rounded-lg cursor-pointer transition-all relative ${
                currentJobId === job.job_id ? 'bg-[#1a1a1a] border border-[#2a2a2a]' : 'hover:bg-[#1a1a1a]'
            }"
            onclick="loadJobById('${job.job_id}')"
        >
            <div class="flex items-start justify-between mb-1">
                <div class="flex-1 min-w-0 pr-2">
                    <div class="text-sm font-medium text-white truncate">
                        ${escapeHtml(job.app_name || job.app_id)}
                    </div>
                    <div class="text-xs text-gray-500 mt-0.5">
                        ${formatDate(job.created_at)}
                    </div>
                </div>
                <div class="flex items-center gap-2">
                    <div class="${statusColors[job.status]} text-xs font-medium ${
                        job.status === 'running' ? 'status-running' : ''
                    }">
                        ${statusIcons[job.status]}
                    </div>
                    ${job.status === 'failed' || job.status === 'cancelled' ? `
                        <button
                            onclick="event.stopPropagation(); retryJobById('${job.job_id}')"
                            class="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-green-600/20 rounded mr-1"
                            title="Retry"
                        >
                            <svg class="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                            </svg>
                        </button>
                    ` : ''}
                    ${job.status === 'running' || job.status === 'started' ? `
                        <button
                            onclick="event.stopPropagation(); cancelJobById('${job.job_id}')"
                            class="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-yellow-600/20 rounded mr-1"
                            title="Cancel"
                        >
                            <svg class="w-4 h-4 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                            </svg>
                        </button>
                    ` : ''}
                    <button
                        onclick="event.stopPropagation(); deleteJobById('${job.job_id}')"
                        class="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-red-600/20 rounded"
                        title="${job.status === 'running' || job.status === 'started' ? 'Cancel & Delete' : 'Delete'}"
                    >
                        <svg class="w-4 h-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                        </svg>
                    </button>
                </div>
            </div>
            ${job.status === 'running' && job.progress_pct ? `
                <div class="mt-2">
                    <div class="w-full bg-[#0a0a0a] rounded-full h-1">
                        <div class="h-1 rounded-full bg-blue-600" style="width: ${job.progress_pct}%"></div>
                    </div>
                </div>
            ` : ''}
        </div>
    `).join('');
}

/**
 * Load job by ID
 */
async function loadJobById(jobId) {
    try {
        const response = await fetch(`/api/job/${jobId}`);
        const job = await response.json();

        currentJobId = jobId;

        if (job.status === 'running' || job.status === 'started') {
            // Show progress panel and start polling
            showProgressPanel();
            startPolling();
        } else if (job.status === 'completed') {
            // Load and display results
            await loadResults();
        } else if (job.status === 'failed') {
            showError(job.error || 'Job failed');
        } else if (job.status === 'cancelled') {
            showError('Job was cancelled');
        }
    } catch (error) {
        showError('Failed to load job: ' + error.message);
    }
}

/**
 * Cancel running job by ID
 */
async function cancelJobById(jobId) {
    if (!confirm('Are you sure you want to cancel this running analysis?')) {
        return;
    }

    try {
        const response = await fetch(`/api/cancel/${jobId}`, {
            method: 'POST'
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to cancel job');
        }

        showToast('Analysis cancelled', 'info');

        // Refresh history to show updated status
        loadJobHistory();

    } catch (error) {
        showToast(error.message, 'error');
    }
}

/**
 * Delete job by ID (supports deleting running jobs - will cancel first)
 */
async function deleteJobById(jobId) {
    // Get job status first
    const jobElement = document.querySelector(`[onclick*="${jobId}"]`);
    const isRunning = jobElement && jobElement.closest('.group').querySelector('.status-running');

    const message = isRunning
        ? 'This analysis is currently running. Are you sure you want to cancel and delete it?'
        : 'Are you sure you want to delete this analysis? This cannot be undone.';

    if (!confirm(message)) {
        return;
    }

    try {
        // If running, cancel first
        if (isRunning) {
            await fetch(`/api/cancel/${jobId}`, { method: 'POST' });
            // Wait a moment for cancellation to process
            await new Promise(resolve => setTimeout(resolve, 500));
        }

        // Now delete
        const response = await fetch(`/api/delete/${jobId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to delete job');
        }

        // Show success message
        showToast(isRunning ? 'Analysis cancelled and deleted' : 'Analysis deleted successfully', 'info');

        // If the deleted job is currently displayed, go back to config
        if (currentJobId === jobId) {
            showConfigPanel();
        }

        // Refresh history
        loadJobHistory();

    } catch (error) {
        showToast(error.message, 'error');
    }
}

/**
 * Retry failed job
 */
async function retryJobById(jobId) {
    try {
        const response = await fetch(`/api/retry/${jobId}`, {
            method: 'POST'
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to retry job');
        }

        showToast('Retrying analysis...', 'info');

        // Load the new job
        setTimeout(() => {
            loadJobById(data.job_id);
            loadJobHistory();
        }, 500);

    } catch (error) {
        showToast(error.message, 'error');
    }
}

/**
 * Handle history search
 */
function handleHistorySearch(e) {
    const searchTerm = e.target.value.toLowerCase();
    const historyItems = document.querySelectorAll('#historyList > div');

    historyItems.forEach(item => {
        const text = item.textContent.toLowerCase();
        if (text.includes(searchTerm)) {
            item.style.display = '';
        } else {
            item.style.display = 'none';
        }
    });
}

/**
 * Toggle sidebar visibility
 */
function toggleSidebar() {
    sidebarVisible = !sidebarVisible;
    if (sidebarVisible) {
        historySidebar.classList.remove('hidden');
    } else {
        historySidebar.classList.add('hidden');
    }
}

/**
 * Handle form submission
 */
async function handleFormSubmit(e) {
    e.preventDefault();

    // Get form values
    const appId = document.getElementById('appId').value.trim();
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;

    // Validate
    if (!appId) {
        showError('Please enter an app package ID or Play Store link');
        return;
    }

    if (!startDate || !endDate) {
        showError('Please select both start and end dates');
        return;
    }

    // Validate date range
    if (new Date(startDate) > new Date(endDate)) {
        showError('Start date must be before end date');
        return;
    }

    // Show progress
    showProgressPanel();

    // Disable form
    startButton.disabled = true;

    try {
        // Start analysis
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                app_link: appId,
                start_date: startDate,
                end_date: endDate
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to start analysis');
        }

        // Store job ID and start polling
        currentJobId = data.job_id;
        startPolling();

        // Add stop button
        addStopButton();

        // Refresh history
        loadJobHistory();

    } catch (error) {
        console.error('Error starting analysis:', error);
        showError(error.message);
        resetForm();
    }
}

/**
 * Add stop button to top actions
 */
function addStopButton() {
    const topActions = document.getElementById('topActions');
    topActions.innerHTML = `
        <button
            onclick="cancelCurrentJob()"
            class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm rounded-lg transition-all flex items-center gap-2"
        >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
            Stop
        </button>
    `;
}

/**
 * Cancel current job
 */
async function cancelCurrentJob() {
    if (!currentJobId) return;

    if (!confirm('Are you sure you want to stop this analysis? Progress will be lost.')) {
        return;
    }

    try {
        const response = await fetch(`/api/cancel/${currentJobId}`, {
            method: 'POST'
        });

        if (response.ok) {
            stopPolling();
            showToast('Analysis cancelled', 'warning');
            setTimeout(() => {
                showConfigPanel();
                loadJobHistory();
            }, 1500);
        }
    } catch (error) {
        showError('Failed to cancel job: ' + error.message);
    }
}

/**
 * Start polling for job status
 */
function startPolling() {
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
                removeStopButton();
                await loadResults();
                loadJobHistory();
            } else if (data.status === 'failed') {
                stopPolling();
                removeStopButton();
                showError(data.error || 'Analysis failed');
                resetForm();
                loadJobHistory();
            } else if (data.status === 'cancelled') {
                stopPolling();
                removeStopButton();
                showError('Analysis was cancelled');
                resetForm();
                loadJobHistory();
            }

        } catch (error) {
            console.error('Error polling status:', error);
            stopPolling();
            removeStopButton();
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
 * Remove stop button
 */
function removeStopButton() {
    document.getElementById('topActions').innerHTML = '';
}

/**
 * Update progress UI
 */
function updateProgress(data) {
    const { phase, progress_pct, message } = data;

    // Update title
    document.getElementById('mainTitle').textContent = `Analyzing ${data.app_name || data.app_id}...`;

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

        if (i < currentPhaseNum) {
            // Completed phase
            iconEl.textContent = '✓';
            phaseEl.classList.remove('text-gray-600');
            phaseEl.classList.add('text-green-500');
        } else if (i === currentPhaseNum) {
            // Current phase
            iconEl.textContent = '⏳';
            phaseEl.classList.remove('text-gray-600', 'text-green-500');
            phaseEl.classList.add('text-blue-500');
        } else {
            // Pending phase
            iconEl.textContent = '⏳';
            phaseEl.classList.remove('text-green-500', 'text-blue-500');
            phaseEl.classList.add('text-gray-600');
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

        // Show results panel
        showResultsPanel();
        resetForm();

        // Update title
        document.getElementById('mainTitle').textContent = `Results: ${data.summary.app_name || currentJobId}`;

        // Update summary cards
        document.getElementById('totalReviews').textContent = data.summary.total_reviews.toLocaleString();
        document.getElementById('totalTopics').textContent = data.summary.total_topics;
        document.getElementById('dateRange').textContent = data.summary.date_range;

        // Render charts
        renderLineChart(data.line_chart);
        renderBarChart(data.bar_chart);
        renderTopicsTable(data.topics_table);

        // Load chat history from database
        await loadChatHistory();

    } catch (error) {
        console.error('Error loading results:', error);
        showError(error.message);
        resetForm();
    }
}

/**
 * Render line chart
 */
function renderLineChart(chartData) {
    const ctx = document.getElementById('lineChart').getContext('2d');

    if (lineChartInstance) {
        lineChartInstance.destroy();
    }

    Chart.defaults.color = '#6b7280';
    Chart.defaults.borderColor = '#1a1a1a';

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
                        boxWidth: 10,
                        padding: 8,
                        font: { size: 10 },
                        color: '#6b7280'
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: '#111111',
                    borderColor: '#2a2a2a',
                    borderWidth: 1,
                    titleColor: '#ffffff',
                    bodyColor: '#9ca3af'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { precision: 0, color: '#6b7280' },
                    grid: { color: '#1a1a1a' }
                },
                x: {
                    ticks: { color: '#6b7280' },
                    grid: { color: '#1a1a1a' }
                }
            }
        }
    });
}

/**
 * Render bar chart
 */
function renderBarChart(chartData) {
    const ctx = document.getElementById('barChart').getContext('2d');

    if (barChartInstance) {
        barChartInstance.destroy();
    }

    barChartInstance = new Chart(ctx, {
        type: 'bar',
        data: chartData,
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#111111',
                    borderColor: '#2a2a2a',
                    borderWidth: 1,
                    titleColor: '#ffffff',
                    bodyColor: '#9ca3af',
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
                    ticks: { precision: 0, color: '#6b7280' },
                    grid: { color: '#1a1a1a' }
                },
                y: {
                    ticks: { color: '#6b7280' },
                    grid: { color: '#1a1a1a' }
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
        row.innerHTML = `
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${index + 1}</td>
            <td class="px-6 py-4 text-sm font-medium text-white">${escapeHtml(topic.topic)}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-white">
                <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-600/30 text-blue-400 border border-blue-500/30">
                    ${topic.total_count.toLocaleString()}
                </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-400">${topic.variation_count}</td>
        `;
        tbody.appendChild(row);
    });

    tbody.dataset.originalData = JSON.stringify(topics);
}

/**
 * Handle table search
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
 * Chat functions
 */
/**
 * Load chat history from database
 */
async function loadChatHistory() {
    if (!currentJobId) return;

    try {
        // Clear existing chat UI
        chatHistory = [];
        document.getElementById('chatMessages').innerHTML = '';

        // Fetch chat history from database
        const response = await fetch(`/api/chat/${currentJobId}`, {
            method: 'GET'
        });

        if (!response.ok) {
            console.warn('Could not load chat history');
            return;
        }

        const data = await response.json();
        const messages = data.messages || [];

        // Render each message
        for (const msg of messages) {
            addChatMessage(msg.content, msg.role, false);
        }

    } catch (error) {
        console.error('Error loading chat history:', error);
        // Don't show error to user - just start with empty chat
    }
}

async function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const question = input.value.trim();

    if (!question || !currentJobId || isSendingMessage) return;

    // Set flag to prevent duplicate sends
    isSendingMessage = true;

    // Add user message to chat
    addChatMessage(question, 'user');
    input.value = '';

    // Show loading indicator
    const loadingId = addChatMessage('Thinking...', 'assistant', true);

    try {
        const response = await fetch(`/api/chat/${currentJobId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });

        const data = await response.json();

        // Remove loading, add real response
        removeChatMessage(loadingId);
        addChatMessage(data.answer, 'assistant');

    } catch (error) {
        removeChatMessage(loadingId);
        addChatMessage('Sorry, I encountered an error: ' + error.message, 'assistant');
    } finally {
        // Reset flag to allow next message
        isSendingMessage = false;
    }
}

function addChatMessage(text, sender, isLoading = false) {
    const messagesDiv = document.getElementById('chatMessages');
    const messageId = `msg-${Date.now()}`;

    const messageDiv = document.createElement('div');
    messageDiv.id = messageId;
    messageDiv.className = `flex ${sender === 'user' ? 'justify-end' : 'justify-start'} chat-message`;

    messageDiv.innerHTML = `
        <div class="max-w-[80%] px-4 py-2 rounded-lg ${
            sender === 'user'
                ? 'bg-white text-black'
                : 'bg-[#1a1a1a] text-gray-100'
        }">
            ${isLoading ? '<span class="animate-pulse">●●●</span>' : escapeHtml(text)}
        </div>
    `;

    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;

    chatHistory.push({ id: messageId, text, sender });

    return messageId;
}

function removeChatMessage(messageId) {
    const msg = document.getElementById(messageId);
    if (msg) msg.remove();
    chatHistory = chatHistory.filter(m => m.id !== messageId);
}

function askQuickQuestion(question) {
    document.getElementById('chatInput').value = question;
    sendChatMessage();
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
        window.open(`/api/download/${currentJobId}`, '_blank');
    } catch (error) {
        console.error('Error downloading file:', error);
        showError('Failed to download Excel file');
    }
}

/**
 * Show/Hide panels
 */
function showConfigPanel() {
    configPanel.classList.remove('hidden');
    progressPanel.classList.add('hidden');
    resultsPanel.classList.add('hidden');
    errorPanel.classList.add('hidden');
    document.getElementById('mainTitle').textContent = 'Review Trend Analysis';
    removeStopButton();
    currentJobId = null;
}

function showProgressPanel() {
    configPanel.classList.add('hidden');
    progressPanel.classList.remove('hidden');
    resultsPanel.classList.add('hidden');
    errorPanel.classList.add('hidden');
}

function showResultsPanel() {
    configPanel.classList.add('hidden');
    progressPanel.classList.add('hidden');
    resultsPanel.classList.remove('hidden');
    errorPanel.classList.add('hidden');
}

function showError(message) {
    configPanel.classList.add('hidden');
    progressPanel.classList.add('hidden');
    resultsPanel.classList.add('hidden');
    errorPanel.classList.remove('hidden');
    document.getElementById('errorMessage').textContent = message;
    document.getElementById('mainTitle').textContent = 'Error';
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `fixed top-4 right-4 px-6 py-3 rounded-lg text-white shadow-lg z-50 ${
        type === 'warning' ? 'bg-yellow-600' :
        type === 'error' ? 'bg-red-600' : 'bg-blue-600'
    }`;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => toast.remove(), 3000);
}

/**
 * Reset form
 */
function resetForm() {
    startButton.disabled = false;
}

/**
 * Utility functions
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric'
    });
}
