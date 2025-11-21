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

                    <!-- Add expandable section for agent transcript and created nodes -->
                    ${agent.id !== 'document_queue' ? `
                        <div class="agent-actions" style="margin-top: 8px; display: flex; gap: 6px;">
                            <button onclick="AgentMonitor.showAgentDetails('${agent.id}')"
                                    style="background: #2196F3; color: white; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer; font-size: 11px; flex: 1;">
                                View Details
                            </button>
                            <button onclick="AgentMonitor.showCreatedNodes('${agent.id}')"
                                    style="background: #4CAF50; color: white; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer; font-size: 11px; flex: 1;">
                                View Nodes
                            </button>
                        </div>
                    ` : ''}
                </div>
            `;
        }

        agentList.innerHTML = html;
    },

    /**
     * Show agent details (transcript)
     */
    async showAgentDetails(agentId) {
        // Use the UI module's showAgentTranscript function
        if (UI && UI.showAgentTranscript) {
            await UI.showAgentTranscript(agentId);
        }
    },

    /**
     * Show nodes created by this agent
     */
    async showCreatedNodes(agentId) {
        try {
            console.log('🔍 Fetching created nodes for agent:', agentId);
            const response = await fetch(`/api/agents/${agentId}/created-nodes`);

            if (!response.ok) {
                UI.showNotification('Failed to fetch agent nodes', 'error');
                return;
            }

            const data = await response.json();
            console.log('✓ Agent created nodes:', data);

            // Create modal to display created nodes
            let modalHTML = `
                <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 10000; display: flex; align-items: center; justify-content: center;"
                     onclick="this.remove()">
                    <div style="background: white; width: 80%; max-width: 800px; max-height: 80%; border-radius: 8px; padding: 24px; overflow-y: auto;"
                         onclick="event.stopPropagation();">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                            <h2 style="margin: 0; color: #333;">Nodes Created by Agent</h2>
                            <button onclick="this.closest('[onclick*=remove]').remove()"
                                    style="background: #f44336; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                                Close
                            </button>
                        </div>

                        <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                            <p><strong>Agent ID:</strong> <span style="font-family: monospace; font-size: 11px;">${data.agent_id}</span></p>
                            <p><strong>Total Nodes Created:</strong> <span style="color: #2196F3; font-weight: bold;">${data.total_nodes}</span></p>
                            <div style="display: flex; gap: 15px; margin-top: 10px;">
                                <span>📄 Documents: <strong>${data.counts.documents}</strong></span>
                                <span>📝 Claims: <strong>${data.counts.claims}</strong></span>
                                <span>⏳ Pending: <strong>${data.counts.pending_documents}</strong></span>
                            </div>
                        </div>
            `;

            // Display Documents
            if (data.documents.length > 0) {
                modalHTML += `
                    <h3 style="margin: 20px 0 10px 0; color: #4CAF50;">📄 Documents (${data.documents.length})</h3>
                    <div style="max-height: 200px; overflow-y: auto; border: 1px solid #ddd; border-radius: 4px; padding: 10px; background: #fafafa;">
                `;

                data.documents.forEach((doc, index) => {
                    modalHTML += `
                        <div style="margin-bottom: 10px; padding: 10px; background: white; border-left: 4px solid #4CAF50; border-radius: 4px;">
                            <div style="display: flex; justify-content: space-between; align-items: start;">
                                <div style="flex: 1;">
                                    <strong style="color: #333;">${this.escapeHtml(doc.title)}</strong>
                                    <div style="font-size: 11px; color: #666; margin-top: 4px;">
                                        Status: ${doc.status} | Created: ${new Date(doc.created_at).toLocaleString()}
                                    </div>
                                </div>
                                <button onclick="AgentMonitor.highlightNodeInGraph('${doc.id}')"
                                        style="background: #2196F3; color: white; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer; font-size: 11px; margin-left: 8px;">
                                    Show in Graph
                                </button>
                            </div>
                        </div>
                    `;
                });

                modalHTML += `</div>`;
            }

            // Display Claims
            if (data.claims.length > 0) {
                modalHTML += `
                    <h3 style="margin: 20px 0 10px 0; color: #2196F3;">📝 Claims (${data.claims.length})</h3>
                    <div style="max-height: 200px; overflow-y: auto; border: 1px solid #ddd; border-radius: 4px; padding: 10px; background: #fafafa;">
                `;

                data.claims.forEach((claim, index) => {
                    const claimText = claim.text.length > 100 ? claim.text.substring(0, 100) + '...' : claim.text;
                    modalHTML += `
                        <div style="margin-bottom: 10px; padding: 10px; background: white; border-left: 4px solid #2196F3; border-radius: 4px;">
                            <div style="display: flex; justify-content: space-between; align-items: start;">
                                <div style="flex: 1;">
                                    <div style="color: #333; font-size: 13px;">${this.escapeHtml(claimText)}</div>
                                    <div style="font-size: 11px; color: #666; margin-top: 4px;">
                                        Status: ${claim.status} | Created: ${new Date(claim.created_at).toLocaleString()}
                                    </div>
                                </div>
                                <button onclick="AgentMonitor.highlightNodeInGraph('${claim.id}')"
                                        style="background: #2196F3; color: white; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer; font-size: 11px; margin-left: 8px;">
                                    Show in Graph
                                </button>
                            </div>
                        </div>
                    `;
                });

                modalHTML += `</div>`;
            }

            // Display Pending Documents
            if (data.pending_documents.length > 0) {
                modalHTML += `
                    <h3 style="margin: 20px 0 10px 0; color: #FF9800;">⏳ Pending Documents (${data.pending_documents.length})</h3>
                    <div style="max-height: 150px; overflow-y: auto; border: 1px solid #ddd; border-radius: 4px; padding: 10px; background: #fafafa;">
                `;

                data.pending_documents.forEach((doc, index) => {
                    modalHTML += `
                        <div style="margin-bottom: 10px; padding: 10px; background: white; border-left: 4px solid #FF9800; border-radius: 4px;">
                            <strong style="color: #333;">${this.escapeHtml(doc.filename)}</strong>
                            <div style="font-size: 11px; color: #666; margin-top: 4px;">
                                Status: ${doc.status} | Created: ${new Date(doc.created_at).toLocaleString()}
                            </div>
                        </div>
                    `;
                });

                modalHTML += `</div>`;
            }

            if (data.total_nodes === 0) {
                modalHTML += `
                    <div style="text-align: center; padding: 40px; color: #999;">
                        <p>This agent hasn't created any nodes yet.</p>
                        <p style="font-size: 12px;">Nodes will appear here as the agent completes its work.</p>
                    </div>
                `;
            }

            modalHTML += `</div></div>`;

            // Add modal to page
            const modalDiv = document.createElement('div');
            modalDiv.innerHTML = modalHTML;
            document.body.appendChild(modalDiv);

        } catch (error) {
            console.error('Error fetching agent created nodes:', error);
            UI.showNotification('Failed to load agent nodes', 'error');
        }
    },

    /**
     * Highlight a specific node in the graph
     */
    highlightNodeInGraph(nodeId) {
        console.log('🎯 Highlighting node in graph:', nodeId);

        // Close the modal
        const modal = document.querySelector('[onclick*="remove"]');
        if (modal) modal.remove();

        // Use GraphRenderer to highlight the node
        if (window.GraphRenderer && GraphRenderer.highlightNode) {
            GraphRenderer.highlightNode(nodeId);
        } else {
            // Fallback: show node details
            if (window.showClaimDetails) {
                showClaimDetails(nodeId);
            }
        }
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
