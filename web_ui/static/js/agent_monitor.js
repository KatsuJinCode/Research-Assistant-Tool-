/**
 * Agent Monitor Module - Track Background Agent Activity
 */

const AgentMonitor = {
    activeAgents: new Map(), // Map of agent_id -> agent_data
    nextAgentId: 1,

    /**
     * Initialize agent monitor
     */
    init() {
        console.log('[AgentMonitor] Initializing agent monitor...');
        this.setupEventListeners();
        console.log('[AgentMonitor] ✓ Agent monitor initialized');
    },

    /**
     * Setup WebSocket event listeners for agent activity
     */
    setupEventListeners() {
        if (!App.socket) {
            console.warn('[AgentMonitor] No socket connection');
            return;
        }

        // Listen for document processing updates
        App.socket.on('processing_update', (data) => {
            this.handleProcessingUpdate(data);
        });

        // Listen for queue updates
        App.socket.on('queue_update', (data) => {
            this.handleQueueUpdate(data);
        });

        // Listen for investigation agents (if implemented)
        App.socket.on('agent_started', (data) => {
            this.addAgent(data);
        });

        App.socket.on('agent_progress', (data) => {
            this.updateAgentProgress(data);
        });

        App.socket.on('agent_completed', (data) => {
            this.removeAgent(data.agent_id);
        });
    },

    /**
     * Handle document processing update
     */
    handleProcessingUpdate(data) {
        const { message, progress, data: extra } = data;

        // Create or update agent for document processing
        const agentId = 'document_processor';

        if (progress !== null && progress !== undefined) {
            this.activeAgents.set(agentId, {
                id: agentId,
                name: 'Document Processor',
                type: 'document',
                status: 'processing',
                task: message,
                progress: progress,
                startTime: this.activeAgents.get(agentId)?.startTime || Date.now()
            });
        } else {
            // No progress - might be a status message
            if (this.activeAgents.has(agentId)) {
                const agent = this.activeAgents.get(agentId);
                agent.task = message;
            }
        }

        this.render();
    },

    /**
     * Handle queue update
     */
    handleQueueUpdate(data) {
        const { processing, queue_size } = data;

        if (!processing && queue_size === 0) {
            // No processing, remove document processor agent
            this.activeAgents.delete('document_processor');
        } else if (processing) {
            // Update agent with current file
            const agentId = 'document_processor';
            if (!this.activeAgents.has(agentId)) {
                this.activeAgents.set(agentId, {
                    id: agentId,
                    name: 'Document Processor',
                    type: 'document',
                    status: 'processing',
                    task: `Processing: ${processing}`,
                    progress: 0,
                    startTime: Date.now()
                });
            }
        }

        // Show queue info
        if (queue_size > 0) {
            const queueAgentId = 'document_queue';
            this.activeAgents.set(queueAgentId, {
                id: queueAgentId,
                name: 'Processing Queue',
                type: 'queue',
                status: 'idle',
                task: `${queue_size} document(s) waiting`,
                progress: null,
                startTime: Date.now()
            });
        } else {
            this.activeAgents.delete('document_queue');
        }

        this.render();
    },

    /**
     * Add a new agent
     */
    addAgent(agentData) {
        const agentId = agentData.id || `agent_${this.nextAgentId++}`;
        this.activeAgents.set(agentId, {
            id: agentId,
            name: agentData.name || 'Unknown Agent',
            type: agentData.type || 'generic',
            status: agentData.status || 'processing',
            task: agentData.task || 'Working...',
            progress: agentData.progress || 0,
            startTime: Date.now()
        });

        this.render();
    },

    /**
     * Update agent progress
     */
    updateAgentProgress(data) {
        const { agent_id, progress, task, status } = data;

        if (this.activeAgents.has(agent_id)) {
            const agent = this.activeAgents.get(agent_id);
            if (progress !== undefined) agent.progress = progress;
            if (task) agent.task = task;
            if (status) agent.status = status;

            this.render();
        }
    },

    /**
     * Remove agent
     */
    removeAgent(agentId) {
        this.activeAgents.delete(agentId);
        this.render();
    },

    /**
     * Render agent list
     */
    render() {
        const agentList = document.getElementById('agent-list');
        const emptyState = document.getElementById('agent-empty-state');
        const countBadge = document.getElementById('agent-count-badge');

        if (!agentList || !emptyState || !countBadge) return;

        const agentCount = this.activeAgents.size;

        // Update badge
        countBadge.textContent = agentCount;
        countBadge.style.display = agentCount > 0 ? 'inline-block' : 'none';

        if (agentCount === 0) {
            agentList.innerHTML = '';
            emptyState.style.display = 'block';
            return;
        }

        emptyState.style.display = 'none';

        // Render agent items
        let html = '';
        for (const [id, agent] of this.activeAgents) {
            const statusClass = agent.status === 'processing' ? 'processing' : 'idle';
            const showProgress = agent.progress !== null && agent.progress !== undefined;

            html += `
                <div class="agent-item" data-agent-id="${agent.id}">
                    <div class="agent-item-header">
                        <span class="agent-name">${this.escapeHtml(agent.name)}</span>
                        <span class="agent-status ${statusClass}">${agent.status.toUpperCase()}</span>
                    </div>
                    <div class="agent-task">${this.escapeHtml(agent.task)}</div>
                    ${showProgress ? `
                        <div class="agent-progress">
                            <div class="agent-progress-fill" style="width: ${agent.progress}%"></div>
                        </div>
                    ` : ''}
                </div>
            `;
        }

        agentList.innerHTML = html;
    },

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    /**
     * Clear all agents
     */
    clear() {
        this.activeAgents.clear();
        this.render();
    }
};

// Initialize agent monitor when app is ready
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        AgentMonitor.init();
    }, 500);
});
