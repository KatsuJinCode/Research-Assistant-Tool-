/**
 * Workflows.js - Frontend logic for Workflow Engine
 *
 * Handles workflow library, execution, history, and visual builder.
 */

// Global state
let workflows = [];
let activeExecutions = [];
let selectedWorkflowId = null;
let socket = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeWebSocket();
    loadWorkflows();
    initializeBuilder();

    // Refresh active executions every 5 seconds
    setInterval(loadActiveExecutions, 5000);
});

/**
 * Initialize WebSocket connection for real-time updates
 */
function initializeWebSocket() {
    socket = io();

    socket.on('workflow_completed', function(data) {
        console.log('Workflow completed:', data);
        showNotification('Workflow completed: ' + data.workflow_id, 'success');
        loadActiveExecutions();
        loadWorkflows();
    });

    socket.on('workflow_failed', function(data) {
        console.log('Workflow failed:', data);
        showNotification('Workflow failed: ' + data.error, 'error');
        loadActiveExecutions();
    });
}

/**
 * Load all workflows from API
 */
async function loadWorkflows() {
    try {
        const response = await fetch('/api/workflows?include_templates=true');
        const data = await response.json();

        if (data.success) {
            workflows = data.workflows;
            renderWorkflowGrid();
        } else {
            showNotification('Failed to load workflows: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Error loading workflows:', error);
        showNotification('Error loading workflows', 'error');
    }
}

/**
 * Render workflow grid
 */
function renderWorkflowGrid() {
    const grid = document.getElementById('workflow-grid');

    if (workflows.length === 0) {
        grid.innerHTML = `
            <div class="empty-state" style="grid-column: 1 / -1;">
                <div class="empty-state-icon">📋</div>
                <div class="empty-state-title">No workflows found</div>
                <div class="empty-state-text">Upload a workflow YAML file to get started</div>
            </div>
        `;
        return;
    }

    grid.innerHTML = workflows.map(workflow => `
        <div class="workflow-card ${workflow.source}" onclick="selectWorkflow('${workflow.workflow_id}')">
            <div class="workflow-header">
                <div>
                    <div class="workflow-title">${escapeHtml(workflow.name)}</div>
                </div>
                <span class="workflow-badge badge-${workflow.source}">${workflow.source}</span>
            </div>
            <div class="workflow-description">
                ${escapeHtml(workflow.description || 'No description')}
            </div>
            <div class="workflow-stats">
                <div class="workflow-stat">
                    <span>⚙</span>
                    <span>${workflow.step_count} steps</span>
                </div>
                <div class="workflow-stat">
                    <span>📊</span>
                    <span>v${workflow.version}</span>
                </div>
            </div>
            <div class="workflow-actions">
                <button class="btn btn-primary btn-small" onclick="event.stopPropagation(); showExecuteModal('${workflow.workflow_id}', '${escapeHtml(workflow.name)}')">
                    Run
                </button>
                <button class="btn btn-secondary btn-small" onclick="event.stopPropagation(); viewWorkflowDetails('${workflow.workflow_id}')">
                    Details
                </button>
                <button class="btn btn-secondary btn-small" onclick="event.stopPropagation(); cloneWorkflow('${workflow.workflow_id}')">
                    Clone
                </button>
            </div>
        </div>
    `).join('');
}

/**
 * Select a workflow
 */
function selectWorkflow(workflowId) {
    selectedWorkflowId = workflowId;
    // Could highlight the selected card or show details
}

/**
 * View workflow details
 */
async function viewWorkflowDetails(workflowId) {
    try {
        const response = await fetch(`/api/workflow/${workflowId}`);
        const data = await response.json();

        if (data.success) {
            const workflow = data.workflow;
            alert(`Workflow: ${workflow.name}\n\nSteps:\n${workflow.steps.map(s => `- ${s.name}`).join('\n')}`);
        } else {
            showNotification('Failed to load workflow details', 'error');
        }
    } catch (error) {
        console.error('Error loading workflow details:', error);
        showNotification('Error loading workflow details', 'error');
    }
}

/**
 * Clone a workflow
 */
async function cloneWorkflow(workflowId) {
    const newName = prompt('Enter name for cloned workflow:');
    if (!newName) return;

    try {
        const response = await fetch(`/api/workflow/${workflowId}/clone`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name: newName})
        });

        const data = await response.json();

        if (data.success) {
            showNotification('Workflow cloned successfully', 'success');
            loadWorkflows();
        } else {
            showNotification('Failed to clone workflow: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Error cloning workflow:', error);
        showNotification('Error cloning workflow', 'error');
    }
}

/**
 * Show execute modal
 */
function showExecuteModal(workflowId, workflowName) {
    selectedWorkflowId = workflowId;
    document.getElementById('exec-workflow-name').value = workflowName;
    document.getElementById('exec-inputs').value = '{}';
    document.getElementById('execute-modal').classList.add('active');
}

/**
 * Hide execute modal
 */
function hideExecuteModal() {
    document.getElementById('execute-modal').classList.remove('active');
}

/**
 * Execute workflow
 */
async function executeWorkflow() {
    if (!selectedWorkflowId) return;

    const inputsStr = document.getElementById('exec-inputs').value;
    let inputs = {};

    try {
        inputs = JSON.parse(inputsStr);
    } catch (error) {
        showNotification('Invalid JSON in input parameters', 'error');
        return;
    }

    try {
        const response = await fetch(`/api/workflow/${selectedWorkflowId}/execute`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({inputs: inputs})
        });

        const data = await response.json();

        if (data.success) {
            showNotification('Workflow execution started', 'success');
            hideExecuteModal();
            switchTab('execution');
            loadActiveExecutions();
        } else {
            showNotification('Failed to execute workflow: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Error executing workflow:', error);
        showNotification('Error executing workflow', 'error');
    }
}

/**
 * Load active executions
 */
async function loadActiveExecutions() {
    // For now, show empty state
    // In a real implementation, this would query /api/workflow/executions or similar
    const container = document.getElementById('active-executions');
    container.innerHTML = `
        <div class="empty-state">
            <div class="empty-state-icon">⚙</div>
            <div class="empty-state-title">No active executions</div>
            <div class="empty-state-text">Start a workflow to see it here</div>
        </div>
    `;
}

/**
 * Show upload modal
 */
function showUploadModal() {
    document.getElementById('upload-modal').classList.add('active');
}

/**
 * Hide upload modal
 */
function hideUploadModal() {
    document.getElementById('upload-modal').classList.remove('active');
}

/**
 * Upload workflow
 */
async function uploadWorkflow() {
    const fileInput = document.getElementById('workflow-file');
    const file = fileInput.files[0];

    if (!file) {
        showNotification('Please select a file', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/workflow/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            showNotification('Workflow uploaded successfully', 'success');
            hideUploadModal();
            loadWorkflows();
        } else {
            showNotification('Failed to upload workflow: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Error uploading workflow:', error);
        showNotification('Error uploading workflow', 'error');
    }
}

/**
 * Switch between tabs
 */
function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    event.target.classList.add('active');

    // Update content sections
    document.querySelectorAll('.section-content').forEach(section => {
        section.classList.remove('active');
    });
    document.getElementById(`${tabName}-section`).classList.add('active');

    // Load data for tab
    if (tabName === 'execution') {
        loadActiveExecutions();
    } else if (tabName === 'history') {
        loadExecutionHistory();
    } else if (tabName === 'library') {
        loadWorkflows();
    }
}

/**
 * Load execution history
 */
async function loadExecutionHistory() {
    const tbody = document.getElementById('history-tbody');
    tbody.innerHTML = `
        <tr>
            <td colspan="6" style="text-align: center; padding: 40px; color: #666;">
                <div>No execution history</div>
                <div style="font-size: 13px; margin-top: 8px;">Execute workflows to see history here</div>
            </td>
        </tr>
    `;
}

/**
 * Initialize workflow builder
 */
function initializeBuilder() {
    const stepTypes = [
        {name: 'Search', type: 'search', icon: '🔍'},
        {name: 'Extract', type: 'extract', icon: '📄'},
        {name: 'Analyze', type: 'analyze', icon: '📊'},
        {name: 'Filter', type: 'filter', icon: '🔧'},
        {name: 'Synthesize', type: 'synthesize', icon: '🧩'},
        {name: 'Export', type: 'export', icon: '💾'},
        {name: 'Custom', type: 'custom', icon: '⚙'},
        {name: 'Parallel', type: 'parallel', icon: '⚡'},
        {name: 'Loop', type: 'loop', icon: '🔁'},
        {name: 'Condition', type: 'condition', icon: '🔀'}
    ];

    const palette = document.getElementById('step-palette');
    palette.innerHTML = stepTypes.map(step => `
        <div class="palette-item" draggable="true" data-step-type="${step.type}">
            <span>${step.icon}</span>
            <span>${step.name}</span>
        </div>
    `).join('');

    // Add drag event listeners (simplified for now)
    document.querySelectorAll('.palette-item').forEach(item => {
        item.addEventListener('dragstart', handleDragStart);
    });
}

/**
 * Handle drag start
 */
function handleDragStart(event) {
    event.dataTransfer.setData('stepType', event.target.dataset.stepType);
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    // Simple alert for now - could be replaced with a toast notification system
    console.log(`[${type.toUpperCase()}] ${message}`);
    alert(message);
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
