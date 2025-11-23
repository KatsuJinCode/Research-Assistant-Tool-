/**
 * Property Viewer Module
 *
 * Displays comprehensive node details in a slide-in side panel with tabs:
 * - Properties: Editable node attributes
 * - Relationships: Connected nodes with navigation
 * - History: Timeline of modifications
 * - Provenance: Creation and discovery lineage
 */

const PropertyViewer = {
    isOpen: false,
    currentNodeId: null,
    currentNodeData: null,
    activeTab: 'properties',

    /**
     * Initialize the Property Viewer
     */
    init() {
        console.log('[PropertyViewer] Initializing...');

        // Listen for node selection events from graph
        document.addEventListener('nodeSelected', (event) => {
            const { nodeId, nodeData } = event.detail;
            this.show(nodeId, nodeData);
        });

        // Close on Escape key
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && this.isOpen) {
                this.hide();
            }
        });

        console.log('[PropertyViewer] Initialized');
    },

    /**
     * Show the property viewer for a specific node
     */
    async show(nodeId, nodeData) {
        console.log('[PropertyViewer] Opening for node:', nodeId);

        this.currentNodeId = nodeId;
        this.currentNodeData = nodeData;
        this.isOpen = true;

        // Get the panel element
        const panel = document.getElementById('property-viewer-panel');
        if (!panel) {
            console.error('[PropertyViewer] Panel element not found');
            return;
        }

        // Show the panel with slide-in animation
        panel.classList.add('visible');

        // Fetch full node details from API
        await this.loadNodeDetails(nodeId);
    },

    /**
     * Hide the property viewer
     */
    hide() {
        console.log('[PropertyViewer] Closing');

        const panel = document.getElementById('property-viewer-panel');
        if (panel) {
            panel.classList.remove('visible');
        }

        this.isOpen = false;
        this.currentNodeId = null;
        this.currentNodeData = null;
    },

    /**
     * Load full node details from API
     */
    async loadNodeDetails(nodeId) {
        try {
            // Show loading state
            this.showLoadingState();

            const response = await fetch(`/api/nodes/${nodeId}/full-details`);
            if (!response.ok) {
                throw new Error(`Failed to fetch node details: ${response.statusText}`);
            }

            const data = await response.json();
            console.log('[PropertyViewer] Loaded node details:', data);

            // Store the full data
            this.currentNodeData = data;

            // Render all tabs
            this.renderPropertiesTab(data);
            this.renderRelationshipsTab(data);
            this.renderHistoryTab(data);
            this.renderProvenanceTab(data);

            // Switch to the active tab
            this.switchTab(this.activeTab);

        } catch (error) {
            console.error('[PropertyViewer] Error loading node details:', error);
            this.showErrorState(error.message);
        }
    },

    /**
     * Show loading state in all tabs
     */
    showLoadingState() {
        const tabs = ['properties', 'relationships', 'history', 'provenance'];
        tabs.forEach(tab => {
            const content = document.getElementById(`pv-tab-${tab}`);
            if (content) {
                content.innerHTML = '<div class="pv-loading">Loading...</div>';
            }
        });
    },

    /**
     * Show error state
     */
    showErrorState(message) {
        const tabs = ['properties', 'relationships', 'history', 'provenance'];
        tabs.forEach(tab => {
            const content = document.getElementById(`pv-tab-${tab}`);
            if (content) {
                content.innerHTML = `<div class="pv-error">Error: ${message}</div>`;
            }
        });
    },

    /**
     * Render Properties tab
     */
    renderPropertiesTab(data) {
        const content = document.getElementById('pv-tab-properties');
        if (!content) return;

        const node = data.node;
        const labels = node.labels || [];
        const nodeType = labels[0] || 'Unknown';

        // Build editable fields
        const confidence = node.confidence !== undefined ? node.confidence : 0.5;
        const investigationValue = node.investigation_value !== undefined ? node.investigation_value : 0;
        const notes = node.notes || '';

        content.innerHTML = `
            <div class="pv-section">
                <h4>Node Type</h4>
                <div class="pv-node-type">
                    ${labels.map(label => `<span class="pv-label-badge">${label}</span>`).join(' ')}
                </div>
            </div>

            <div class="pv-section">
                <h4>Title / Text</h4>
                <div class="pv-text">${node.text || node.title || node.summary || 'N/A'}</div>
            </div>

            <div class="pv-section">
                <h4>Confidence</h4>
                <div class="pv-editable-field">
                    <input type="range"
                           id="pv-confidence-slider"
                           min="0"
                           max="1"
                           step="0.01"
                           value="${confidence}">
                    <span id="pv-confidence-value">${(confidence * 100).toFixed(0)}%</span>
                </div>
            </div>

            <div class="pv-section">
                <h4>Investigation Value</h4>
                <div class="pv-editable-field">
                    <input type="range"
                           id="pv-investigation-slider"
                           min="0"
                           max="1"
                           step="0.01"
                           value="${investigationValue}">
                    <span id="pv-investigation-value">${(investigationValue * 100).toFixed(0)}%</span>
                </div>
            </div>

            <div class="pv-section">
                <h4>Notes</h4>
                <textarea id="pv-notes"
                          class="pv-notes-input"
                          placeholder="Add notes about this node...">${notes}</textarea>
            </div>

            <div class="pv-section">
                <h4>Metadata</h4>
                <div class="pv-metadata">
                    ${Object.entries(node)
                        .filter(([key]) => !['text', 'title', 'summary', 'confidence', 'investigation_value', 'notes', 'labels', 'internal_id'].includes(key))
                        .map(([key, value]) => `
                            <div class="pv-metadata-row">
                                <span class="pv-metadata-key">${key}:</span>
                                <span class="pv-metadata-value">${this.formatValue(value)}</span>
                            </div>
                        `).join('')}
                </div>
            </div>

            <div class="pv-actions">
                <button class="pv-btn pv-btn-primary" onclick="PropertyViewer.saveProperties()">Save Changes</button>
                <button class="pv-btn pv-btn-secondary" onclick="PropertyViewer.cancelEdit()">Cancel</button>
            </div>
        `;

        // Add event listeners for sliders
        const confidenceSlider = document.getElementById('pv-confidence-slider');
        const confidenceValue = document.getElementById('pv-confidence-value');
        if (confidenceSlider && confidenceValue) {
            confidenceSlider.addEventListener('input', (e) => {
                confidenceValue.textContent = `${(e.target.value * 100).toFixed(0)}%`;
            });
        }

        const investigationSlider = document.getElementById('pv-investigation-slider');
        const investigationValueElement = document.getElementById('pv-investigation-value');
        if (investigationSlider && investigationValueElement) {
            investigationSlider.addEventListener('input', (e) => {
                investigationValueElement.textContent = `${(e.target.value * 100).toFixed(0)}%`;
            });
        }
    },

    /**
     * Render Relationships tab
     */
    renderRelationshipsTab(data) {
        const content = document.getElementById('pv-tab-relationships');
        if (!content) return;

        const relationships = data.relationships || {};
        const relCount = Object.values(relationships).reduce((sum, rels) => sum + rels.length, 0);

        if (relCount === 0) {
            content.innerHTML = '<div class="pv-empty">No relationships found</div>';
            return;
        }

        let html = '<div class="pv-relationships">';

        // Group by relationship type
        for (const [relType, rels] of Object.entries(relationships)) {
            html += `
                <div class="pv-rel-group">
                    <h4 class="pv-rel-type">${relType} (${rels.length})</h4>
                    <div class="pv-rel-list">
                        ${rels.map(rel => {
                            const direction = rel.direction === 'outgoing' ? '→' : '←';
                            const node = rel.related_node;
                            const nodeLabel = node.text || node.title || node.id;
                            return `
                                <div class="pv-rel-item" onclick="PropertyViewer.navigateToNode('${node.id}')">
                                    <span class="pv-rel-direction">${direction}</span>
                                    <span class="pv-rel-node-type">${node.labels?.[0] || 'Node'}</span>
                                    <span class="pv-rel-node-label">${nodeLabel}</span>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            `;
        }

        html += '</div>';
        content.innerHTML = html;
    },

    /**
     * Render History tab
     */
    renderHistoryTab(data) {
        const content = document.getElementById('pv-tab-history');
        if (!content) return;

        const history = data.history || [];

        if (history.length === 0) {
            content.innerHTML = '<div class="pv-empty">No modification history available</div>';
            return;
        }

        const html = `
            <div class="pv-history">
                ${history.map(event => `
                    <div class="pv-history-item">
                        <div class="pv-history-timestamp">${this.formatTimestamp(event.timestamp)}</div>
                        <div class="pv-history-event">${event.event}</div>
                        ${event.agent_id ? `
                            <div class="pv-history-agent">
                                by ${event.agent_type}
                                <a href="#" onclick="PropertyViewer.viewAgent('${event.agent_id}'); return false;">
                                    (${event.agent_id.substring(0, 8)}...)
                                </a>
                            </div>
                        ` : ''}
                    </div>
                `).join('')}
            </div>
        `;

        content.innerHTML = html;
    },

    /**
     * Render Provenance tab
     */
    renderProvenanceTab(data) {
        const content = document.getElementById('pv-tab-provenance');
        if (!content) return;

        const node = data.node;

        let html = '<div class="pv-provenance">';

        // Created By
        if (node.created_by_agent_id) {
            html += `
                <div class="pv-prov-section">
                    <h4>Created By</h4>
                    <div class="pv-prov-agent">
                        <span class="pv-prov-agent-type">${node.created_by || 'Agent'}</span>
                        <a href="#" onclick="PropertyViewer.viewAgent('${node.created_by_agent_id}'); return false;">
                            ${node.created_by_agent_id.substring(0, 12)}...
                        </a>
                        ${node.created_at ? `<span class="pv-prov-time">${this.formatTimestamp(node.created_at)}</span>` : ''}
                    </div>
                </div>
            `;
        }

        // Discovered By
        if (node.discovered_by_agent_id) {
            html += `
                <div class="pv-prov-section">
                    <h4>Discovered By</h4>
                    <div class="pv-prov-agent">
                        <span class="pv-prov-agent-type">${node.discovered_by || 'Agent'}</span>
                        <a href="#" onclick="PropertyViewer.viewAgent('${node.discovered_by_agent_id}'); return false;">
                            ${node.discovered_by_agent_id.substring(0, 12)}...
                        </a>
                        ${node.discovered_at ? `<span class="pv-prov-time">${this.formatTimestamp(node.discovered_at)}</span>` : ''}
                    </div>
                </div>
            `;
        }

        // Lineage chain (if available)
        if (node.provenance_chain) {
            html += `
                <div class="pv-prov-section">
                    <h4>Lineage Chain</h4>
                    <div class="pv-prov-chain">
                        ${node.provenance_chain.map((item, idx) => `
                            <div class="pv-prov-chain-item">
                                <span class="pv-prov-chain-step">${idx + 1}.</span>
                                <span class="pv-prov-chain-desc">${item}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        // If no provenance data
        if (!node.created_by_agent_id && !node.discovered_by_agent_id && !node.provenance_chain) {
            html += '<div class="pv-empty">No provenance information available</div>';
        }

        html += '</div>';
        content.innerHTML = html;
    },

    /**
     * Switch to a different tab
     */
    switchTab(tabName) {
        console.log('[PropertyViewer] Switching to tab:', tabName);

        this.activeTab = tabName;

        // Update tab buttons
        const tabs = document.querySelectorAll('.pv-tab');
        tabs.forEach(tab => {
            if (tab.dataset.tab === tabName) {
                tab.classList.add('active');
            } else {
                tab.classList.remove('active');
            }
        });

        // Update tab content
        const contents = document.querySelectorAll('.pv-tab-content');
        contents.forEach(content => {
            if (content.id === `pv-tab-${tabName}`) {
                content.classList.add('active');
            } else {
                content.classList.remove('active');
            }
        });

        // Load comments when switching to Comments tab
        if (tabName === 'comments' && this.currentNodeId) {
            if (typeof CommentSystem !== 'undefined') {
                CommentSystem.loadComments(this.currentNodeId);
            }
        }
    },

    /**
     * Save property changes
     */
    async saveProperties() {
        console.log('[PropertyViewer] Saving properties...');

        const confidence = parseFloat(document.getElementById('pv-confidence-slider')?.value);
        const investigationValue = parseFloat(document.getElementById('pv-investigation-slider')?.value);
        const notes = document.getElementById('pv-notes')?.value;

        const updates = {
            confidence,
            investigation_value: investigationValue,
            notes
        };

        try {
            const response = await fetch(`/api/nodes/${this.currentNodeId}/update`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(updates)
            });

            if (!response.ok) {
                throw new Error(`Failed to update node: ${response.statusText}`);
            }

            const result = await response.json();
            console.log('[PropertyViewer] Saved successfully:', result);

            // Show success notification
            if (window.UI && UI.showNotification) {
                UI.showNotification('Properties saved successfully', 'success');
            }

            // Reload details to reflect changes
            await this.loadNodeDetails(this.currentNodeId);

        } catch (error) {
            console.error('[PropertyViewer] Error saving properties:', error);
            if (window.UI && UI.showNotification) {
                UI.showNotification(`Error: ${error.message}`, 'error');
            }
        }
    },

    /**
     * Cancel editing and reload original data
     */
    async cancelEdit() {
        console.log('[PropertyViewer] Canceling edit');
        await this.loadNodeDetails(this.currentNodeId);
    },

    /**
     * Navigate to a different node
     */
    navigateToNode(nodeId) {
        console.log('[PropertyViewer] Navigating to node:', nodeId);

        // Trigger graph to select the new node
        if (window.GraphRenderer && GraphRenderer.highlightNode) {
            GraphRenderer.highlightNode(nodeId);
        }

        // Load details for the new node
        this.show(nodeId, null);
    },

    /**
     * View agent details (open agent transcript)
     */
    viewAgent(agentId) {
        console.log('[PropertyViewer] Viewing agent:', agentId);

        // Close property viewer
        this.hide();

        // Open agent monitor if available
        if (window.AgentMonitor && AgentMonitor.showAgentDetails) {
            AgentMonitor.showAgentDetails(agentId);
        } else if (window.UI && UI.showNotification) {
            UI.showNotification(`Agent ID: ${agentId}`, 'info');
        }
    },

    /**
     * Format a value for display
     */
    formatValue(value) {
        if (value === null || value === undefined) {
            return '<em>null</em>';
        }
        if (typeof value === 'boolean') {
            return value ? 'true' : 'false';
        }
        if (typeof value === 'object') {
            return '<pre>' + JSON.stringify(value, null, 2) + '</pre>';
        }
        if (typeof value === 'string' && value.length > 100) {
            return value.substring(0, 100) + '...';
        }
        return value.toString();
    },

    /**
     * Format timestamp for display
     */
    formatTimestamp(timestamp) {
        if (!timestamp) return 'Unknown';

        try {
            const date = new Date(timestamp);
            return date.toLocaleString();
        } catch (e) {
            return timestamp.toString();
        }
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    PropertyViewer.init();
});
