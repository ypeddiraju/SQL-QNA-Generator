/**
 * GenAI SQL Test Data Generator - Main JavaScript
 * Handles all client-side interactions and API communications
 */

// Global configuration
const CONFIG = {
    API_BASE_URL: '/api',
    POLL_INTERVAL: 2000, // 2 seconds
    TOAST_DURATION: 5000 // 5 seconds
};

// State management
const state = {
    jobs: new Map(),
    activeConnections: new Set(),
    currentTab: 'discover',
    isConnected: false
};

// DOM elements cache
const elements = {
    // Navigation
    navButtons: document.querySelectorAll('.nav-btn'),
    tabPanes: document.querySelectorAll('.tab-pane'),
    
    // Forms
    dbConfigForm: document.getElementById('dbConfigForm'),
    openaiConfigForm: document.getElementById('openaiConfigForm'),
    discoveryOptionsForm: document.getElementById('discoveryOptionsForm'),
    generationOptionsForm: document.getElementById('generationOptionsForm'),
    
    // Buttons
    testConnectionBtn: document.getElementById('testConnection'),
    discoverBtn: document.getElementById('discoverBtn'),
    generateBtn: document.getElementById('generateBtn'),
    generateAsyncBtn: document.getElementById('generateAsyncBtn'),
    refreshJobsBtn: document.getElementById('refreshJobs'),
    clearJobsBtn: document.getElementById('clearJobs'),
    
    // Results
    discoveryResults: document.getElementById('discoveryResults'),
    generationResults: document.getElementById('generationResults'),
    jobsList: document.getElementById('jobsList'),
    
    // Status
    statusMessage: document.getElementById('statusMessage'),
    
    // Modals
    modal: document.getElementById('resultModal'),
    modalTitle: document.getElementById('modalTitle'),
    modalBody: document.getElementById('modalContent'),
    modalClose: document.querySelector('.modal-close')
};

/**
 * Initialize the application
 */
function init() {
    setupEventListeners();
    showTab('discover');
    updateStatus('Ready to start');
    loadSavedConfigurations();
    startJobPolling();
}

/**
 * Setup all event listeners
 */
function setupEventListeners() {
    // Navigation
    elements.navButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const tabId = e.currentTarget.dataset.tab;
            showTab(tabId);
        });
    });
    
    // Forms
    elements.dbConfigForm?.addEventListener('submit', handleDatabaseConfig);
    elements.openaiConfigForm?.addEventListener('submit', handleOpenAIConfig);
    elements.discoveryOptionsForm?.addEventListener('submit', handleDiscovery);
    elements.generationOptionsForm?.addEventListener('submit', handleGeneration);
    
    // Buttons
    elements.testConnectionBtn?.addEventListener('click', testDatabaseConnection);
    elements.discoverBtn?.addEventListener('click', discoverTables);
    elements.generateBtn?.addEventListener('click', generateDataset);
    elements.generateAsyncBtn?.addEventListener('click', generateDatasetAsync);
    document.getElementById('generateDemoBtn')?.addEventListener('click', generateDatasetDemo);
    document.getElementById('refreshJobs')?.addEventListener('click', refreshJobs);
    document.getElementById('clearJobs')?.addEventListener('click', clearCompletedJobs);
    document.getElementById('refreshTableCount')?.addEventListener('click', updateTableCountInfo);
    
    // Add input listeners for calculation updates
    document.getElementById('questionsCount')?.addEventListener('input', updateQuestionsCalculation);
    document.getElementById('maxTables')?.addEventListener('input', updateQuestionsCalculation);
    
    // Modal
    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', closeModal);
    });
    elements.modal?.addEventListener('click', (e) => {
        if (e.target === elements.modal) closeModal();
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', handleKeyboardShortcuts);
    
    // Radio button handlers
    setupFormHandlers();
    
    // Auto-save configurations
    setupAutoSave();
}

/**
 * Show a specific tab
 */
function showTab(tabId) {
    // Update navigation
    elements.navButtons.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabId);
    });
    
    // Update tab panes
    elements.tabPanes.forEach(pane => {
        pane.classList.toggle('active', pane.id === `${tabId}Tab`);
    });
    
    state.currentTab = tabId;
    updateStatus(`Switched to ${tabId} tab`);
}

/**
 * Handle database configuration
 */
async function handleDatabaseConfig(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const config = Object.fromEntries(formData.entries());
    
    try {
        updateStatus('Saving database configuration...');
        
        const response = await fetch(`${CONFIG.API_BASE_URL}/config/database`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showToast('Database configuration saved successfully', 'success');
            // Also save to localStorage as backup
            saveConfiguration('database', config);
            updateStatus('Database configuration saved');
            
            // Update connection status
            state.isConnected = false; // Reset connection status
        } else {
            throw new Error(result.detail || 'Failed to save configuration');
        }
    } catch (error) {
        console.error('Database config error:', error);
        showToast(`Error: ${error.message}`, 'error');
        updateStatus('Failed to save database configuration');
    }
}

/**
 * Handle OpenAI configuration
 */
async function handleOpenAIConfig(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const config = Object.fromEntries(formData.entries());
    
    try {
        updateStatus('Saving OpenAI configuration...');
        
        const response = await fetch(`${CONFIG.API_BASE_URL}/config/openai`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showToast('OpenAI configuration saved successfully', 'success');
            saveConfiguration('openai', config);
            updateStatus('OpenAI configuration saved');
        } else {
            throw new Error(result.detail || 'Failed to save configuration');
        }
    } catch (error) {
        console.error('OpenAI config error:', error);
        showToast(`Error: ${error.message}`, 'error');
        updateStatus('Failed to save OpenAI configuration');
    }
}

/**
 * Test database connection
 */
async function testDatabaseConnection() {
    const btn = elements.testConnectionBtn;
    const originalText = btn.innerHTML;
    
    try {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing...';
        updateStatus('Testing database connection...');
        
        const response = await fetch(`${CONFIG.API_BASE_URL}/database/test-connection`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showToast('Database connection successful!', 'success');
            state.isConnected = true;
            updateStatus('Database connection successful');
            
            // Update table count info after successful connection
            await updateTableCountInfo();
        } else {
            throw new Error(result.detail || 'Connection failed');
        }
    } catch (error) {
        console.error('Connection test error:', error);
        showToast(`Connection failed: ${error.message}`, 'error');
        state.isConnected = false;
        updateStatus('Database connection failed');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

/**
 * Discover database tables
 */
async function discoverTables() {
    const btn = elements.discoverBtn;
    const originalText = btn.innerHTML;
    
    try {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Discovering...';
        updateStatus('Discovering database tables...');
        
        // Get discovery options
        const options = {
            exclude_tables: document.getElementById('excludeTables')?.value || ''
        };
        
        const response = await fetch(`${CONFIG.API_BASE_URL}/database/discover`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(options)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            displayDiscoveryResults(result);
            showToast('Database discovery completed!', 'success');
            updateStatus('Database discovery completed');
            
            // Update table count info with fresh discovery results
            updateTableCountInfoFromResult(result);
        } else {
            throw new Error(result.detail || 'Discovery failed');
        }
    } catch (error) {
        console.error('Discovery error:', error);
        showToast(`Discovery failed: ${error.message}`, 'error');
        updateStatus('Database discovery failed');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

/**
 * Handle table discovery with options
 */
async function handleDiscovery(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const options = Object.fromEntries(formData.entries());
    
    try {
        updateStatus('Starting database discovery...');
        
        const response = await fetch(`${CONFIG.API_BASE_URL}/database/discover`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(options)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            displayDiscoveryResults(result);
            showToast('Discovery completed successfully!', 'success');
            updateStatus('Discovery completed');
        } else {
            throw new Error(result.detail || 'Discovery failed');
        }
    } catch (error) {
        console.error('Discovery error:', error);
        showToast(`Discovery failed: ${error.message}`, 'error');
        updateStatus('Discovery failed');
    }
}

/**
 * Handle dataset generation
 */
async function handleGeneration(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const options = Object.fromEntries(formData.entries());
    
    try {
        updateStatus('Starting dataset generation...');
        
        const response = await fetch(`${CONFIG.API_BASE_URL}/generate/dataset`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(options)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            const jobId = result.job_id;
            state.jobs.set(jobId, { id: jobId, status: 'started', ...result });
            showToast(`Generation started! Job ID: ${jobId}`, 'info');
            updateStatus(`Generation job ${jobId} started`);
            refreshJobs();
        } else {
            throw new Error(result.detail || 'Generation failed');
        }
    } catch (error) {
        console.error('Generation error:', error);
        showToast(`Generation failed: ${error.message}`, 'error');
        updateStatus('Generation failed');
    }
}

/**
 * Generate dataset (synchronous)
 */
async function generateDataset() {
    const btn = elements.generateBtn;
    const originalText = btn.innerHTML;
    
    try {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
        updateStatus('Starting dataset generation...');
        
        // Get generation options from form
        let options;
        try {
            options = getGenerationOptions();
        } catch (formError) {
            throw new Error(formError.message);
        }
        
        // Validate that we have tables or are in auto-discovery mode
        const tableMode = document.querySelector('input[name="tableMode"]:checked')?.value || 'discover';
        if (tableMode === 'specific' && (!options.tables || options.tables.length === 0)) {
            throw new Error('Please specify at least one table name for specific table mode, or switch to auto-discovery mode.');
        }
        
        const response = await fetch(`${CONFIG.API_BASE_URL}/generate/dataset`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(options)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            displayGenerationResults(result);
            showToast('Dataset generation completed!', 'success');
            updateStatus('Dataset generation completed');
        } else {
            // Handle validation errors specially
            if (response.status === 422) {
                const errorDetails = result.detail || result.message || 'Validation error';
                if (Array.isArray(errorDetails)) {
                    const errorMessages = errorDetails.map(err => err.msg || err.message || JSON.stringify(err)).join(', ');
                    throw new Error(`Validation error: ${errorMessages}`);
                } else {
                    throw new Error(`Validation error: ${errorDetails}`);
                }
            } else {
                throw new Error(result.detail || result.message || 'Generation failed');
            }
        }
    } catch (error) {
        console.error('Generation error:', error);
        showToast(`Generation failed: ${error.message}`, 'error');
        updateStatus('Generation failed');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

/**
 * Generate dataset using demo mode (no database required)
 */
async function generateDatasetDemo() {
    const btn = document.getElementById('generateDemoBtn');
    const originalText = btn.innerHTML;
    
    try {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating Demo...';
        updateStatus('Starting demo dataset generation...');
        
        // Simple demo request - doesn't need complex form validation
        const options = {
            tables: [],
            questions_per_table: 15,
            include_joins: true,
            difficulty_level: "mixed",
            output_file: null
        };
        
        const response = await fetch(`${CONFIG.API_BASE_URL}/generate/dataset-demo`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(options)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            displayGenerationResults(result);
            showToast('Demo dataset generation completed! This used sample Employee/Department/Project data.', 'success');
            updateStatus('Demo dataset generation completed');
        } else {
            throw new Error(result.detail || result.message || 'Demo generation failed');
        }
    } catch (error) {
        console.error('Demo generation error:', error);
        showToast(`Demo generation failed: ${error.message}`, 'error');
        updateStatus('Demo generation failed');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

/**
 * Generate dataset (asynchronous background job)
 */
async function generateDatasetAsync() {
    const btn = elements.generateAsyncBtn;
    const originalText = btn.innerHTML;
    
    try {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Starting...';
        updateStatus('Starting async dataset generation...');
        
        // Get generation options from form
        let options;
        try {
            options = getGenerationOptions();
        } catch (formError) {
            throw new Error(formError.message);
        }
        
        // Validate that we have tables or are in auto-discovery mode
        const tableMode = document.querySelector('input[name="tableMode"]:checked')?.value || 'discover';
        if (tableMode === 'specific' && (!options.tables || options.tables.length === 0)) {
            throw new Error('Please specify at least one table name for specific table mode, or switch to auto-discovery mode.');
        }
        
        const response = await fetch(`${CONFIG.API_BASE_URL}/generate/dataset-async`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(options)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            const jobId = result.job_id || result.id;
            state.jobs.set(jobId, { id: jobId, status: 'started', ...result });
            showToast(`Async generation started! Job ID: ${jobId}`, 'info');
            updateStatus(`Generation job ${jobId} started`);
            
            // Switch to jobs tab to show progress
            showTab('jobs');
            refreshJobs();
        } else {
            // Handle validation errors specially
            if (response.status === 422) {
                const errorDetails = result.detail || result.message || 'Validation error';
                if (Array.isArray(errorDetails)) {
                    const errorMessages = errorDetails.map(err => err.msg || err.message || JSON.stringify(err)).join(', ');
                    throw new Error(`Validation error: ${errorMessages}`);
                } else {
                    throw new Error(`Validation error: ${errorDetails}`);
                }
            } else {
                throw new Error(result.detail || result.message || 'Generation failed');
            }
        }
    } catch (error) {
        console.error('Generation error:', error);
        showToast(`Generation failed: ${error.message}`, 'error');
        updateStatus('Generation failed');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

/**
 * Get generation options from form
 */
function getGenerationOptions() {
    const tableMode = document.querySelector('input[name="tableMode"]:checked')?.value || 'discover';
    
    // For auto-discovery mode, we need to get the discovered tables first
    let tables = [];
    if (tableMode === 'specific') {
        tables = (document.getElementById('tablesList')?.value || '').split(',').map(t => t.trim()).filter(t => t);
        if (tables.length === 0) {
            throw new Error('Please specify at least one table name for specific table mode');
        }
    } else {
        // For discover mode, we need to get tables from the discovery results
        // If no discovery has been run, we'll use a special flag for the API
        const discoveryResults = elements.discoveryResults;
        if (discoveryResults && discoveryResults.style.display !== 'none') {
            // Try to extract table names from discovery results
            const tableCards = discoveryResults.querySelectorAll('.table-card .table-header h5');
            tables = Array.from(tableCards).map(h5 => h5.textContent.trim()).filter(t => t);
        }
        
        // If we still don't have tables, we'll send an empty array to trigger auto-discovery in the API
        if (tables.length === 0) {
            tables = []; // API will auto-discover all tables
        }
    }
    
    const maxTables = parseInt(document.getElementById('maxTables')?.value) || 12;
    const totalQuestions = parseInt(document.getElementById('questionsCount')?.value) || 25;
    
    // Validate max_tables
    if (maxTables < 2) {
        throw new Error('Max tables must be at least 2 for meaningful Q&A generation');
    }
    if (maxTables > 50) {
        throw new Error('Max tables cannot exceed 50 to prevent token overflow issues');
    }
    
    // Validate total questions
    if (totalQuestions < 5) {
        throw new Error('Total questions must be at least 5');
    }
    if (totalQuestions > 100) {
        throw new Error('Total questions cannot exceed 100 to prevent processing issues');
    }
    
    return {
        tables: tables,
        questions_per_table: totalQuestions,  // This is actually total questions, not per table
        max_tables: maxTables,
        include_joins: document.getElementById('includeJoins')?.checked || true,
        difficulty_level: document.querySelector('input[name="difficulty"]:checked')?.value || 'mixed',
        output_file: document.getElementById('outputFile')?.value || null
    };
}

/**
 * Display generation results
 */
function displayGenerationResults(data) {
    if (!elements.generationResults) return;
    
    console.log('Generation results data:', data);
    
    // Extract statistics from the response
    const stats = data.statistics || {};
    const metadata = data.metadata || {};
    const dataset = data.dataset || [];
    
    const html = `
        <div class="results-content">
            <h3><i class="fas fa-magic"></i> Q&A Dataset Generation Complete</h3>
            <div class="generation-summary">
                <div class="summary-stats">
                    <div class="stat-item">
                        <span class="stat-number">${stats.total_questions || dataset.length}</span>
                        <span class="stat-label">Total Questions</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">${metadata.table_count || 0}</span>
                        <span class="stat-label">Tables Analyzed</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">${stats.join_questions || 0}</span>
                        <span class="stat-label">Join Questions</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">${stats.join_percentage || 0}%</span>
                        <span class="stat-label">Join Coverage</span>
                    </div>
                </div>
                <div class="generation-details">
                    <p><strong>Message:</strong> ${data.message || 'Generation completed successfully'}</p>
                    ${metadata.tables_analyzed ? `<p><strong>Tables:</strong> ${metadata.tables_analyzed.join(', ')}</p>` : ''}
                    ${stats.target_join_percentage ? `<p><strong>Target Join %:</strong> ${stats.target_join_percentage}% ${stats.meets_target ? '✅' : '❌'}</p>` : ''}
                    ${metadata.demo_mode ? '<p><strong>Mode:</strong> Demo (using sample data)</p>' : ''}
                </div>
                
                ${data.token_usage ? `
                    <div class="token-usage-details">
                        <h4><i class="fas fa-calculator"></i> AI Token Usage</h4>
                        <div class="token-stats">
                            <div class="token-item">
                                <span class="token-number">${data.token_usage.total_tokens}</span>
                                <span class="token-label">Total Tokens</span>
                            </div>
                            <div class="token-item">
                                <span class="token-number">${data.token_usage.prompt_tokens}</span>
                                <span class="token-label">Input Tokens</span>
                            </div>
                            <div class="token-item">
                                <span class="token-number">${data.token_usage.completion_tokens}</span>
                                <span class="token-label">Output Tokens</span>
                            </div>
                            <div class="token-item">
                                <span class="token-number">$${data.token_usage.total_cost.toFixed(4)}</span>
                                <span class="token-label">Estimated Cost</span>
                            </div>
                        </div>
                        <div class="token-model">
                            <small><strong>Model:</strong> ${data.token_usage.model}</small>
                        </div>
                    </div>
                ` : ''}
            </div>
            
            ${dataset && dataset.length > 0 ? `
                <div class="questions-preview">
                    <h4>Sample Questions (first 5):</h4>
                    <div class="questions-list">
                        ${dataset.slice(0, 5).map((qaPair, index) => `
                            <div class="question-item">
                                <div class="question-header">
                                    <h5>Question ${index + 1}</h5>
                                </div>
                                <div class="question-content">
                                    <p><strong>Q:</strong> ${qaPair.question}</p>
                                    <p><strong>Expected Answer:</strong> <span class="answer-text">${qaPair.expected_answer}</span></p>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                    
                    ${dataset.length > 5 ? `
                        <div class="more-questions">
                            <p><strong>Total:</strong> ${dataset.length} questions generated</p>
                            <button class="btn btn-outline" onclick="showAllQuestions()">
                                <i class="fas fa-list"></i> View All Questions
                            </button>
                        </div>
                    ` : ''}
                </div>
            ` : '<div class="no-questions"><p>No questions were generated. Please check your configuration and try again.</p></div>'}
            
            <div class="download-section">
                <button class="btn btn-primary" onclick="downloadDataset()">
                    <i class="fas fa-download"></i> Download Complete Dataset (JSON)
                </button>
            </div>
        </div>
    `;
    
    // Store the full dataset and metadata for download
    window.generatedDataset = dataset;
    window.generatedMetadata = metadata;
    window.generatedStatistics = stats;
    window.generatedTokenUsage = data.token_usage;
    
    elements.generationResults.innerHTML = html;
    elements.generationResults.style.display = 'block';
}

/**
 * Display discovery results
 */
function displayDiscoveryResults(data) {
    if (!elements.discoveryResults) return;
    
    const html = `
        <div class="results-content">
            <h3><i class="fas fa-table"></i> Database Schema Discovery</h3>
            <div class="discovery-summary">
                <div class="summary-stats">
                    <div class="stat-item">
                        <span class="stat-number">${data.tables?.length || 0}</span>
                        <span class="stat-label">Tables</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">${data.total_columns || 0}</span>
                        <span class="stat-label">Columns</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">${data.relationships?.length || 0}</span>
                        <span class="stat-label">Relationships</span>
                    </div>
                </div>
            </div>
            
            ${data.tables ? `
                <div class="tables-list">
                    <h4>Tables Found:</h4>
                    <div class="tables-grid">
                        ${data.tables.map(table => `
                            <div class="table-card">
                                <div class="table-header">
                                    <h5>${table.name}</h5>
                                    <span class="column-count">${table.columns?.length || 0} columns</span>
                                </div>
                                ${table.columns ? `
                                    <div class="columns-list">
                                        ${table.columns.map(col => `
                                            <div class="column-item">
                                                <span class="column-name">${col.name}</span>
                                                <span class="column-type">${col.type}</span>
                                            </div>
                                        `).join('')}
                                    </div>
                                ` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
            
            ${data.relationships ? `
                <div class="relationships-list">
                    <h4>Table Relationships:</h4>
                    <div class="relationships-grid">
                        ${data.relationships.map(rel => `
                            <div class="relationship-item">
                                <strong>${rel.parent_table}</strong>
                                <i class="fas fa-arrow-right"></i>
                                <strong>${rel.child_table}</strong>
                                <small>(${rel.parent_column} → ${rel.child_column})</small>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
        </div>
    `;
    
    elements.discoveryResults.innerHTML = html;
    elements.discoveryResults.style.display = 'block';
}

/**
 * Refresh jobs list
 */
async function refreshJobs() {
    try {
        updateStatus('Refreshing jobs...');
        
        const response = await fetch(`${CONFIG.API_BASE_URL}/jobs`);
        const jobs = await response.json();
        
        if (response.ok) {
            displayJobs(jobs);
            updateStatus('Jobs refreshed');
        } else {
            throw new Error('Failed to fetch jobs');
        }
    } catch (error) {
        console.error('Jobs refresh error:', error);
        showToast(`Failed to refresh jobs: ${error.message}`, 'error');
        updateStatus('Failed to refresh jobs');
    }
}

/**
 * Display jobs list
 */
function displayJobs(jobs) {
    if (!elements.jobsList) return;
    
    if (!jobs || jobs.length === 0) {
        elements.jobsList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-briefcase"></i>
                <p>No jobs found. Start by generating a dataset!</p>
            </div>
        `;
        return;
    }
    
    const html = jobs.map(job => `
        <div class="job-item" data-job-id="${job.id}">
            <div class="job-info">
                <div class="job-id">Job ID: ${job.id}</div>
                <div class="job-status">
                    <span class="status-badge ${job.status}">${job.status.toUpperCase()}</span>
                    <span class="job-type">${job.type || 'Generation'}</span>
                </div>
                ${job.progress !== undefined ? `
                    <div class="job-progress">
                        <div class="job-progress-bar" style="width: ${job.progress}%"></div>
                    </div>
                ` : ''}
                <div class="job-details">
                    <small>Created: ${new Date(job.created_at).toLocaleString()}</small>
                    ${job.completed_at ? `
                        <small>Completed: ${new Date(job.completed_at).toLocaleString()}</small>
                    ` : ''}
                </div>
            </div>
            <div class="job-actions">
                <button class="btn btn-outline" onclick="viewJobDetails('${job.id}')">
                    <i class="fas fa-eye"></i> Details
                </button>
                ${job.status === 'completed' ? `
                    <button class="btn btn-primary" onclick="downloadJobResult('${job.id}')">
                        <i class="fas fa-download"></i> Download
                    </button>
                ` : ''}
                ${job.status === 'running' ? `
                    <button class="btn btn-error" onclick="cancelJob('${job.id}')">
                        <i class="fas fa-stop"></i> Cancel
                    </button>
                ` : ''}
            </div>
        </div>
    `).join('');
    
    elements.jobsList.innerHTML = html;
}

/**
 * View job details in modal
 */
async function viewJobDetails(jobId) {
    try {
        updateStatus(`Loading job ${jobId} details...`);
        
        const response = await fetch(`${CONFIG.API_BASE_URL}/jobs/${jobId}`);
        const job = await response.json();
        
        if (response.ok) {
            showModal('Job Details', `
                <div class="job-details-content">
                    <div class="detail-group">
                        <h4>Basic Information</h4>
                        <p><strong>Job ID:</strong> ${job.id}</p>
                        <p><strong>Status:</strong> <span class="status-badge ${job.status}">${job.status.toUpperCase()}</span></p>
                        <p><strong>Type:</strong> ${job.type || 'Dataset Generation'}</p>
                        <p><strong>Created:</strong> ${new Date(job.created_at).toLocaleString()}</p>
                        ${job.completed_at ? `<p><strong>Completed:</strong> ${new Date(job.completed_at).toLocaleString()}</p>` : ''}
                    </div>
                    
                    ${job.parameters ? `
                        <div class="detail-group">
                            <h4>Parameters</h4>
                            <pre class="json-display">${JSON.stringify(job.parameters, null, 2)}</pre>
                        </div>
                    ` : ''}
                    
                    ${job.result ? `
                        <div class="detail-group">
                            <h4>Results</h4>
                            <pre class="json-display">${JSON.stringify(job.result, null, 2)}</pre>
                        </div>
                    ` : ''}
                    
                    ${job.error ? `
                        <div class="detail-group">
                            <h4>Error Details</h4>
                            <div class="error-message">${job.error}</div>
                        </div>
                    ` : ''}
                </div>
            `);
            updateStatus('Job details loaded');
        } else {
            throw new Error(job.detail || 'Failed to load job details');
        }
    } catch (error) {
        console.error('Job details error:', error);
        showToast(`Failed to load job details: ${error.message}`, 'error');
        updateStatus('Failed to load job details');
    }
}

/**
 * Download job result
 */
async function downloadJobResult(jobId) {
    try {
        updateStatus(`Downloading job ${jobId} result...`);
        
        const response = await fetch(`${CONFIG.API_BASE_URL}/jobs/${jobId}/download`);
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `job_${jobId}_result.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            showToast('Download started!', 'success');
            updateStatus('Download completed');
        } else {
            throw new Error('Failed to download result');
        }
    } catch (error) {
        console.error('Download error:', error);
        showToast(`Download failed: ${error.message}`, 'error');
        updateStatus('Download failed');
    }
}

/**
 * Cancel a running job
 */
async function cancelJob(jobId) {
    if (!confirm(`Are you sure you want to cancel job ${jobId}?`)) return;
    
    try {
        updateStatus(`Cancelling job ${jobId}...`);
        
        const response = await fetch(`${CONFIG.API_BASE_URL}/jobs/${jobId}/cancel`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showToast('Job cancelled successfully', 'success');
            refreshJobs();
            updateStatus('Job cancelled');
        } else {
            throw new Error(result.detail || 'Failed to cancel job');
        }
    } catch (error) {
        console.error('Cancel job error:', error);
        showToast(`Failed to cancel job: ${error.message}`, 'error');
        updateStatus('Failed to cancel job');
    }
}

/**
 * Clear completed jobs
 */
async function clearCompletedJobs() {
    if (!confirm('Are you sure you want to clear all completed jobs?')) return;
    
    try {
        updateStatus('Clearing completed jobs...');
        
        const response = await fetch(`${CONFIG.API_BASE_URL}/jobs/clear-completed`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showToast('Completed jobs cleared', 'success');
            refreshJobs();
            updateStatus('Completed jobs cleared');
        } else {
            throw new Error(result.detail || 'Failed to clear jobs');
        }
    } catch (error) {
        console.error('Clear jobs error:', error);
        showToast(`Failed to clear jobs: ${error.message}`, 'error');
        updateStatus('Failed to clear jobs');
    }
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    toast.innerHTML = `
        <div class="toast-content">
            <div class="toast-icon">
                <i class="fas ${getToastIcon(type)}"></i>
            </div>
            <div class="toast-message">${message}</div>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    // Trigger animation
    setTimeout(() => toast.classList.add('show'), 100);
    
    // Auto remove
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => document.body.removeChild(toast), 300);
    }, CONFIG.TOAST_DURATION);
}

/**
 * Get icon for toast type
 */
function getToastIcon(type) {
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    return icons[type] || icons.info;
}

/**
 * Show modal
 */
function showModal(title, content) {
    if (elements.modalTitle) elements.modalTitle.textContent = title;
    if (elements.modalBody) elements.modalBody.innerHTML = content;
    if (elements.modal) elements.modal.classList.add('show');
}

/**
 * Close modal
 */
function closeModal() {
    if (elements.modal) elements.modal.classList.remove('show');
}

/**
 * Update status message
 */
function updateStatus(message) {
    if (elements.statusMessage) {
        elements.statusMessage.textContent = message;
    }
}

/**
 * Handle keyboard shortcuts
 */
function handleKeyboardShortcuts(e) {
    if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
            case '1':
                e.preventDefault();
                showTab('discover');
                break;
            case '2':
                e.preventDefault();
                showTab('generate');
                break;
            case '3':
                e.preventDefault();
                showTab('jobs');
                break;
            case '4':
                e.preventDefault();
                showTab('help');
                break;
        }
    }
    
    if (e.key === 'Escape') {
        closeModal();
    }
}

/**
 * Setup form handlers for interactive elements
 */
function setupFormHandlers() {
    // Table mode radio buttons
    const tableModeRadios = document.querySelectorAll('input[name="tableMode"]');
    const specificTablesDiv = document.getElementById('specificTables');
    
    tableModeRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            if (specificTablesDiv) {
                specificTablesDiv.style.display = e.target.value === 'specific' ? 'block' : 'none';
            }
        });
    });
}

/**
 * Setup auto-save for configurations
 */
function setupAutoSave() {
    const forms = [elements.dbConfigForm, elements.openaiConfigForm];
    
    forms.forEach(form => {
        if (!form) return;
        
        const inputs = form.querySelectorAll('input, select');
        inputs.forEach(input => {
            input.addEventListener('change', () => {
                const formData = new FormData(form);
                const config = Object.fromEntries(formData.entries());
                const configType = form.id.replace('ConfigForm', '').toLowerCase();
                saveConfiguration(configType, config);
            });
        });
    });
}

/**
 * Save configuration to localStorage
 */
function saveConfiguration(type, config) {
    try {
        localStorage.setItem(`qna_config_${type}`, JSON.stringify(config));
    } catch (error) {
        console.warn('Failed to save configuration:', error);
    }
}

/**
 * Load saved configurations and server configuration
 */
async function loadSavedConfigurations() {
    try {
        // Load database config from server (environment variables)
        await loadDatabaseConfiguration();
        
        // Load OpenAI config info
        await loadOpenAIConfiguration();
        
        // Load table count information if database is configured
        await updateTableCountInfo();
        
        // Initialize questions calculation
        updateQuestionsCalculation();
        
    } catch (error) {
        console.warn('Failed to load server configurations:', error);
        
        // Fallback to localStorage
        try {
            // Load database config from localStorage
            const dbConfig = localStorage.getItem('qna_config_database');
            if (dbConfig && elements.dbConfigForm) {
                const config = JSON.parse(dbConfig);
                populateDatabaseForm(config);
            }
        } catch (localError) {
            console.warn('Failed to load local configurations:', localError);
        }
    }
}

/**
 * Load database configuration from server
 */
async function loadDatabaseConfiguration() {
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/config/database`);
        if (response.ok) {
            const config = await response.json();
            populateDatabaseForm(config);
            updateStatus('Database configuration loaded from environment');
        }
    } catch (error) {
        console.warn('Failed to load database configuration from server:', error);
    }
}

/**
 * Load OpenAI configuration info
 */
async function loadOpenAIConfiguration() {
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/config/openai`);
        if (response.ok) {
            const config = await response.json();
            displayOpenAIInfo(config);
        }
    } catch (error) {
        console.warn('Failed to load OpenAI configuration from server:', error);
    }
}

/**
 * Populate database form with configuration data
 */
function populateDatabaseForm(config) {
    if (!elements.dbConfigForm) return;
    
    Object.entries(config).forEach(([key, value]) => {
        const input = elements.dbConfigForm.querySelector(`[name="${key}"]`);
        if (input && value !== undefined) {
            input.value = value;
        }
    });
}

/**
 * Display OpenAI configuration info
 */
function displayOpenAIInfo(config) {
    const configPanel = document.querySelector('.config-panel[style*="display: none"]');
    if (configPanel) {
        const infoDiv = configPanel.querySelector('.config-info');
        if (infoDiv) {
            infoDiv.innerHTML = `
                <p><i class="fas fa-info-circle"></i> OpenAI configuration loaded from environment:</p>
                <ul>
                    <li><strong>Model:</strong> ${config.model}</li>
                    <li><strong>API Key:</strong> ${config.api_key_preview}</li>
                    <li><strong>Status:</strong> ${config.api_key_configured ? '✅ Configured' : '❌ Not configured'}</li>
                </ul>
            `;
        }
        configPanel.style.display = 'block';
    }
}

/**
 * Update questions calculation display
 */
function updateQuestionsCalculation() {
    const questionsCalculationElement = document.getElementById('questionsCalculation');
    const questionsCountInput = document.getElementById('questionsCount');
    const maxTablesInput = document.getElementById('maxTables');
    
    if (!questionsCalculationElement || !questionsCountInput) return;
    
    const totalQuestions = parseInt(questionsCountInput.value) || 25;
    const maxTables = parseInt(maxTablesInput?.value) || 12;
    
    // Calculate approximate questions per table
    const questionsPerTable = Math.ceil(totalQuestions / maxTables);
    
    questionsCalculationElement.textContent = `(~${questionsPerTable} per table)`;
    questionsCalculationElement.className = 'calculation-info';
}

/**
 * Update table count information from discovery result
 */
function updateTableCountInfoFromResult(result) {
    const tablesInfoElement = document.getElementById('tablesInfo');
    const maxTablesHelpElement = document.getElementById('maxTablesHelp');
    const maxTablesInput = document.getElementById('maxTables');
    
    if (!tablesInfoElement || !result.tables) return;
    
    const totalTables = result.tables.length;
    const filteredTables = result.filtered_tables || totalTables;
    
    // Update the info display
    tablesInfoElement.textContent = `(${totalTables} available)`;
    tablesInfoElement.className = 'tables-info';
    
    // Update help text with more context
    if (maxTablesHelpElement) {
        maxTablesHelpElement.textContent = `Maximum tables for auto-discovery. Database has ${totalTables} business tables available. Higher values may cause token overflow.`;
    }
    
    // Adjust max attribute and suggest a good default
    if (maxTablesInput) {
        maxTablesInput.setAttribute('max', Math.min(50, totalTables));
        
        // Suggest a reasonable default (50% of available tables, but not less than 6 or more than 20)
        const suggestedMax = Math.max(6, Math.min(20, Math.floor(totalTables * 0.5)));
        if (maxTablesInput.value == 12) { // Only update if still at default
            maxTablesInput.value = suggestedMax;
        }
    }
    
    // Update questions calculation
    updateQuestionsCalculation();
}

/**
 * Update table count information in the max tables field
 */
async function updateTableCountInfo() {
    const tablesInfoElement = document.getElementById('tablesInfo');
    const maxTablesHelpElement = document.getElementById('maxTablesHelp');
    const maxTablesInput = document.getElementById('maxTables');
    
    if (!tablesInfoElement) return;
    
    try {
        // Show loading state
        tablesInfoElement.textContent = '(checking...)';
        tablesInfoElement.className = 'tables-info loading';
        
        // Try to get table count from discovery endpoint
        const response = await fetch(`${CONFIG.API_BASE_URL}/database/discover`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ exclude_tables: '' })
        });
        
        if (response.ok) {
            const result = await response.json();
            const totalTables = result.tables ? result.tables.length : 0;
            const filteredTables = result.filtered_tables || totalTables;
            
            // Update the info display
            tablesInfoElement.textContent = `(${filteredTables} available)`;
            tablesInfoElement.className = 'tables-info';
            
            // Update help text with more context
            if (maxTablesHelpElement) {
                maxTablesHelpElement.textContent = `Maximum tables for auto-discovery. Database has ${filteredTables} business tables available. Higher values may cause token overflow.`;
            }
            
            // Adjust max attribute and suggest a good default
            if (maxTablesInput) {
                maxTablesInput.setAttribute('max', Math.min(50, filteredTables));
                
                // Suggest a reasonable default (50% of available tables, but not less than 6 or more than 20)
                const suggestedMax = Math.max(6, Math.min(20, Math.floor(filteredTables * 0.5)));
                if (maxTablesInput.value == 12) { // Only update if still at default
                    maxTablesInput.value = suggestedMax;
                }
            }
            
        } else {
            throw new Error('Failed to fetch table information');
        }
        
    } catch (error) {
        console.warn('Failed to update table count info:', error);
        tablesInfoElement.textContent = '(connect DB first)';
        tablesInfoElement.className = 'tables-info error';
        
        if (maxTablesHelpElement) {
            maxTablesHelpElement.textContent = 'Maximum tables for auto-discovery. Connect to database to see available table count.';
        }
    }
}

/**
 * Start polling for job updates
 */
function startJobPolling() {
    setInterval(async () => {
        if (state.currentTab === 'jobs' && state.jobs.size > 0) {
            try {
                const response = await fetch(`${CONFIG.API_BASE_URL}/jobs`);
                if (response.ok) {
                    const jobs = await response.json();
                    displayJobs(jobs);
                }
            } catch (error) {
                console.warn('Job polling error:', error);
            }
        }
    }, CONFIG.POLL_INTERVAL);
}

/**
 * Download generation result file
 */
async function downloadGenerationResult(filename) {
    try {
        updateStatus(`Downloading ${filename}...`);
        
        const response = await fetch(`${CONFIG.API_BASE_URL}/download/${filename}`);
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            showToast('Download started!', 'success');
            updateStatus('Download completed');
        } else {
            throw new Error('Failed to download file');
        }
    } catch (error) {
        console.error('Download error:', error);
        showToast(`Download failed: ${error.message}`, 'error');
        updateStatus('Download failed');
    }
}

/**
 * Show all questions in a modal
 */
function showAllQuestions() {
    if (!window.generatedDataset || window.generatedDataset.length === 0) {
        showToast('No questions available to display', 'warning');
        return;
    }
    
    const content = `
        <div class="all-questions-content">
            <p><strong>Total Questions:</strong> ${window.generatedDataset.length}</p>
            <div class="questions-list-full">
                ${window.generatedDataset.map((qaPair, index) => `
                    <div class="question-item-full">
                        <div class="question-header">
                            <h5>Question ${index + 1}</h5>
                        </div>
                        <div class="question-content">
                            <p><strong>Q:</strong> ${qaPair.question}</p>
                            <p><strong>Expected Answer:</strong> <span class="answer-text">${qaPair.expected_answer}</span></p>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
    
    showModal('All Generated Questions', content);
}

/**
 * Download the generated dataset as JSON
 */
function downloadDataset() {
    if (!window.generatedDataset || window.generatedDataset.length === 0) {
        showToast('No dataset available for download', 'warning');
        return;
    }
    
    try {
        // Include full generation results with token usage
        const downloadData = {
            dataset: window.generatedDataset,
            metadata: window.generatedMetadata || {},
            statistics: window.generatedStatistics || {},
            token_usage: window.generatedTokenUsage || {},
            generation_info: {
                download_timestamp: new Date().toISOString(),
                total_questions: window.generatedDataset.length
            }
        };
        
        const dataStr = JSON.stringify(downloadData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        
        const url = URL.createObjectURL(dataBlob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `qna_dataset_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        showToast('Dataset downloaded successfully with token usage info!', 'success');
        updateStatus('Dataset download completed');
    } catch (error) {
        console.error('Download error:', error);
        showToast(`Download failed: ${error.message}`, 'error');
        updateStatus('Download failed');
    }
}

// Export functions for global access
window.viewJobDetails = viewJobDetails;
window.downloadJobResult = downloadJobResult;
window.cancelJob = cancelJob;
window.downloadGenerationResult = downloadGenerationResult;
window.showAllQuestions = showAllQuestions;
window.downloadDataset = downloadDataset;
window.updateTableCountInfo = updateTableCountInfo;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', init);
