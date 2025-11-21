/**
 * Property Viewer Module - Comprehensive Node Details and Editing
 *
 * Handles:
 * - Full node property display
 * - Editable fields (confidence, investigation value, notes)
 * - Relationship visualization
 * - Provenance details with clickable links
 * - Node history timeline
 * - Export node data
 */

const PropertyViewer = {
    currentNode: null,
    isExpanded: false,

    /**
     * Initialize property viewer
     */
    init() {
        console.log('[PropertyViewer] Initializing...');
        this.setupEventListeners();
        console.log('[PropertyViewer] ✓ Property viewer initialized');
    },

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Listen for node selection events
        window.addEventListener('nodeSelected', (e) => {
            this.showNodeProperties(e.detail.nodeId);
        });

        // Listen for property panel toggle
        document.addEventListener('click', (e) => {
            if (e.target.id === 'toggle-properties-btn') {
                this.togglePropertiesPanel();
            }
        });
    },

    /**
     * Show detailed properties for a node
     */
    async showNodeProperties(nodeId) {
        console.log(`[PropertyViewer] Showing properties for node: ${nodeId}`);

        try {
            // Fetch full node details
            const response = await fetch(`/api/nodes/${nodeId}/full-details`);

            if (!response.ok) {
                throw new Error('Failed to fetch node details');
            }

            const nodeData = await response.json();
            this.currentNode = nodeData;

            // Update the detail panel with enhanced view
            this.renderProperties(nodeData);

        } catch (error) {
            console.error('[PropertyViewer] Error fetching node details:', error);
            this.showError('Failed to load node properties');
        }
    },

    /**
     * Render comprehensive properties view
     */
    renderProperties(node) {
        const detailPanel = document.getElementById('detail-panel');
        if (!detailPanel) return;

        // Build comprehensive property view
        const html = `
            <div class="property-viewer-container">
                <!-- Header with node type and actions -->
                <div class="property-header">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h3 style="margin: 0; color: #2196F3;">
                            ${this.getNodeIcon(node.type)} ${node.type || 'Node'}
                        </h3>
                        <div class="property-actions">
                            <button onclick="PropertyViewer.exportNode()" class="property-action-btn" title="Export">
                                📤
                            </button>
                            <button onclick="PropertyViewer.refreshNode()" class="property-action-btn" title="Refresh">
                                🔄
                            </button>
                            <button onclick="PropertyViewer.toggleExpanded()" class="property-action-btn" title="Expand/Collapse">
                                ${this.isExpanded ? '🔽' : '▶️'}
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Main content -->
                <div class="property-content" style="max-height: ${this.isExpanded ? 'none' : '600px'}; overflow-y: auto;">

                    <!-- Core Properties Section -->
                    <div class="property-section">
                        <div class="property-section-title">Core Properties</div>
                        ${this.renderCoreProperties(node)}
                    </div>

                    <!-- Editable Fields Section -->
                    <div class="property-section">
                        <div class="property-section-title">Editable Fields</div>
                        ${this.renderEditableFields(node)}
                    </div>

                    <!-- Provenance Section -->
                    ${this.renderProvenanceSection(node)}

                    <!-- Relationships Section -->
                    <div class="property-section">
                        <div class="property-section-title">
                            Relationships (${this.getRelationshipCount(node)})
                        </div>
                        ${this.renderRelationships(node)}
                    </div>

                    <!-- Metadata Section -->
                    <div class="property-section">
                        <div class="property-section-title">Metadata</div>
                        ${this.renderMetadata(node)}
                    </div>

                    <!-- History Timeline (if available) -->
                    ${this.renderHistoryTimeline(node)}

                    <!-- Raw Properties (collapsed by default) -->
                    <div class="property-section">
                        <div class="property-section-title" style="cursor: pointer;" onclick="PropertyViewer.toggleRawProperties()">
                            🔧 Raw Properties (Debug)
                            <span id="raw-props-toggle">▶️</span>
                        </div>
                        <div id="raw-properties-content" style="display: none;">
                            <pre style="background: #1a1a1a; padding: 10px; border-radius: 4px; overflow-x: auto; font-size: 11px;">${JSON.stringify(node, null, 2)}</pre>
                        </div>
                    </div>
                </div>
            </div>
        `;

        detailPanel.innerHTML = html;
        detailPanel.style.display = 'block';
    },

    /**
     * Render core properties
     */
    renderCoreProperties(node) {
        let html = '<div class="property-grid">';

        // Common properties
        if (node.id) {
            html += this.renderPropertyRow('ID', node.id, true);
        }

        if (node.text) {
            html += this.renderPropertyRow('Text', node.text, false, true);
        }

        if (node.title) {
            html += this.renderPropertyRow('Title', node.title);
        }

        if (node.status) {
            html += this.renderPropertyRow('Status', node.status, false, false, this.getStatusBadge(node.status));
        }

        if (node.type) {
            html += this.renderPropertyRow('Type', node.type);
        }

        html += '</div>';
        return html;
    },

    /**
     * Render editable fields
     */
    renderEditableFields(node) {
        return `
            <div class="editable-fields">
                <!-- Confidence Score -->
                <div class="editable-field">
                    <label>Confidence Score</label>
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <input type="range"
                               id="edit-confidence"
                               min="0"
                               max="100"
                               value="${node.confidence || 50}"
                               oninput="PropertyViewer.updateConfidenceDisplay(this.value)"
                               style="flex: 1;">
                        <span id="confidence-display" style="min-width: 45px; font-weight: bold; color: #2196F3;">
                            ${node.confidence || 50}%
                        </span>
                    </div>
                </div>

                <!-- Investigation Value -->
                <div class="editable-field">
                    <label>Investigation Value</label>
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <input type="range"
                               id="edit-investigation"
                               min="0"
                               max="100"
                               value="${node.investigation_value || 50}"
                               oninput="PropertyViewer.updateInvestigationDisplay(this.value)"
                               style="flex: 1;">
                        <span id="investigation-display" style="min-width: 45px; font-weight: bold; color: #4CAF50;">
                            ${node.investigation_value || 50}%
                        </span>
                    </div>
                </div>

                <!-- Notes -->
                <div class="editable-field">
                    <label>Notes</label>
                    <textarea id="edit-notes"
                              rows="3"
                              placeholder="Add your notes here..."
                              style="width: 100%; background: #333; border: 1px solid #555; border-radius: 4px; padding: 8px; color: white; resize: vertical;">${node.notes || ''}</textarea>
                </div>

                <!-- Save Button -->
                <button onclick="PropertyViewer.saveChanges()"
                        style="width: 100%; padding: 10px; background: #2196F3; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 500;">
                    💾 Save Changes
                </button>
            </div>
        `;
    },

    /**
     * Render provenance section
     */
    renderProvenanceSection(node) {
        if (!node.created_by && !node.discovered_by) {
            return '';
        }

        return `
            <div class="property-section provenance-section">
                <div class="property-section-title">🔍 Provenance</div>
                <div class="provenance-content">
                    ${node.created_by ? `
                        <div class="provenance-item">
                            <strong>Created by:</strong>
                            <div style="margin-top: 4px;">
                                <span class="provenance-badge">${node.created_by}</span>
                                ${node.created_by_agent_id ? `
                                    <a href="#" onclick="PropertyViewer.viewAgentTranscript('${node.created_by_agent_id}')"
                                       class="provenance-link">
                                        View Agent ${node.created_by_agent_id.substring(0, 8)}...
                                    </a>
                                ` : ''}
                            </div>
                        </div>
                    ` : ''}

                    ${node.discovered_by ? `
                        <div class="provenance-item">
                            <strong>Discovered by:</strong>
                            <div style="margin-top: 4px;">
                                <span class="provenance-badge">${node.discovered_by}</span>
                                ${node.discovered_by_agent_id ? `
                                    <a href="#" onclick="PropertyViewer.viewAgentTranscript('${node.discovered_by_agent_id}')"
                                       class="provenance-link">
                                        View Agent ${node.discovered_by_agent_id.substring(0, 8)}...
                                    </a>
                                ` : ''}
                            </div>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    },

    /**
     * Render relationships
     */
    renderRelationships(node) {
        if (!node.relationships || node.relationships.length === 0) {
            return '<div style="color: #999; font-style: italic; padding: 10px;">No relationships found</div>';
        }

        let html = '<div class="relationships-list">';

        // Group relationships by type
        const grouped = {};
        node.relationships.forEach(rel => {
            if (!grouped[rel.type]) {
                grouped[rel.type] = [];
            }
            grouped[rel.type].push(rel);
        });

        // Render each group
        for (const [type, rels] of Object.entries(grouped)) {
            html += `
                <div class="relationship-group">
                    <div class="relationship-type">${type} (${rels.length})</div>
                    <div class="relationship-items">
                        ${rels.map(rel => `
                            <div class="relationship-item" onclick="PropertyViewer.navigateToNode('${rel.target_id}')">
                                <span class="relationship-icon">${this.getRelationshipIcon(type)}</span>
                                <span class="relationship-label">${rel.target_label || rel.target_id}</span>
                                <span class="relationship-arrow">→</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        html += '</div>';
        return html;
    },

    /**
     * Render metadata
     */
    renderMetadata(node) {
        const metadata = [];

        if (node.created_at) {
            metadata.push({ label: 'Created', value: new Date(node.created_at).toLocaleString() });
        }

        if (node.updated_at) {
            metadata.push({ label: 'Updated', value: new Date(node.updated_at).toLocaleString() });
        }

        if (node.version) {
            metadata.push({ label: 'Version', value: node.version });
        }

        if (metadata.length === 0) {
            return '<div style="color: #999; font-style: italic; padding: 10px;">No metadata available</div>';
        }

        return `
            <div class="metadata-grid">
                ${metadata.map(item => `
                    <div class="metadata-item">
                        <div class="metadata-label">${item.label}</div>
                        <div class="metadata-value">${item.value}</div>
                    </div>
                `).join('')}
            </div>
        `;
    },

    /**
     * Render history timeline
     */
    renderHistoryTimeline(node) {
        if (!node.history || node.history.length === 0) {
            return '';
        }

        return `
            <div class="property-section">
                <div class="property-section-title">📅 History Timeline</div>
                <div class="history-timeline">
                    ${node.history.map(event => `
                        <div class="timeline-event">
                            <div class="timeline-dot"></div>
                            <div class="timeline-content">
                                <div class="timeline-time">${new Date(event.timestamp).toLocaleString()}</div>
                                <div class="timeline-action">${event.action}</div>
                                ${event.user ? `<div class="timeline-user">by ${event.user}</div>` : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    },

    /**
     * Helper: Render property row
     */
    renderPropertyRow(label, value, copyable = false, multiline = false, customContent = null) {
        if (customContent) {
            return `
                <div class="property-row">
                    <div class="property-label">${label}</div>
                    <div class="property-value">${customContent}</div>
                </div>
            `;
        }

        const valueContent = multiline ?
            `<div class="property-value-multiline">${value}</div>` :
            `<span>${value}</span>`;

        const copyBtn = copyable ?
            `<button onclick="PropertyViewer.copyToClipboard('${value}')" class="copy-btn" title="Copy">📋</button>` :
            '';

        return `
            <div class="property-row">
                <div class="property-label">${label}</div>
                <div class="property-value">
                    ${valueContent}
                    ${copyBtn}
                </div>
            </div>
        `;
    },

    /**
     * Update confidence display
     */
    updateConfidenceDisplay(value) {
        const display = document.getElementById('confidence-display');
        if (display) {
            display.textContent = `${value}%`;
        }
    },

    /**
     * Update investigation display
     */
    updateInvestigationDisplay(value) {
        const display = document.getElementById('investigation-display');
        if (display) {
            display.textContent = `${value}%`;
        }
    },

    /**
     * Save changes to node
     */
    async saveChanges() {
        if (!this.currentNode) return;

        const confidence = document.getElementById('edit-confidence')?.value;
        const investigation = document.getElementById('edit-investigation')?.value;
        const notes = document.getElementById('edit-notes')?.value;

        try {
            const response = await fetch(`/api/nodes/${this.currentNode.id}/update`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    confidence: parseFloat(confidence),
                    investigation_value: parseFloat(investigation),
                    notes: notes
                })
            });

            if (!response.ok) {
                throw new Error('Failed to save changes');
            }

            if (window.UI && UI.showNotification) {
                UI.showNotification('Changes saved successfully', 'success');
            }

            // Refresh the view
            await this.showNodeProperties(this.currentNode.id);

        } catch (error) {
            console.error('[PropertyViewer] Error saving changes:', error);
            if (window.UI && UI.showNotification) {
                UI.showNotification('Failed to save changes', 'error');
            }
        }
    },

    /**
     * View agent transcript
     */
    async viewAgentTranscript(agentId) {
        console.log(`[PropertyViewer] Viewing transcript for agent: ${agentId}`);

        // TODO: Open transcript in modal or side panel
        if (window.AgentMonitor) {
            AgentMonitor.showTranscript(agentId);
        }
    },

    /**
     * Navigate to related node
     */
    navigateToNode(nodeId) {
        console.log(`[PropertyViewer] Navigating to node: ${nodeId}`);

        // Trigger node selection in graph
        if (window.GraphRenderer) {
            GraphRenderer.selectNode(nodeId);
        }
    },

    /**
     * Export node data
     */
    exportNode() {
        if (!this.currentNode) return;

        const dataStr = JSON.stringify(this.currentNode, null, 2);
        const blob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = `node_${this.currentNode.id}_${Date.now()}.json`;
        a.click();

        URL.revokeObjectURL(url);

        if (window.UI && UI.showNotification) {
            UI.showNotification('Node exported successfully', 'success');
        }
    },

    /**
     * Refresh node data
     */
    async refreshNode() {
        if (!this.currentNode) return;

        await this.showNodeProperties(this.currentNode.id);

        if (window.UI && UI.showNotification) {
            UI.showNotification('Node refreshed', 'info');
        }
    },

    /**
     * Toggle expanded view
     */
    toggleExpanded() {
        this.isExpanded = !this.isExpanded;
        if (this.currentNode) {
            this.renderProperties(this.currentNode);
        }
    },

    /**
     * Toggle raw properties display
     */
    toggleRawProperties() {
        const content = document.getElementById('raw-properties-content');
        const toggle = document.getElementById('raw-props-toggle');

        if (content && toggle) {
            if (content.style.display === 'none') {
                content.style.display = 'block';
                toggle.textContent = '🔽';
            } else {
                content.style.display = 'none';
                toggle.textContent = '▶️';
            }
        }
    },

    /**
     * Copy to clipboard
     */
    copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            if (window.UI && UI.showNotification) {
                UI.showNotification('Copied to clipboard', 'success');
            }
        });
    },

    /**
     * Show error message
     */
    showError(message) {
        const detailPanel = document.getElementById('detail-panel');
        if (detailPanel) {
            detailPanel.innerHTML = `
                <div style="padding: 20px; text-align: center; color: #f44336;">
                    <div style="font-size: 48px; margin-bottom: 10px;">⚠️</div>
                    <div>${message}</div>
                </div>
            `;
        }
    },

    /**
     * Helper: Get node icon
     */
    getNodeIcon(type) {
        const icons = {
            'Document': '📄',
            'Claim': '📝',
            'Evidence': '🔗',
            'SuperClaim': '⭐',
            'PendingDocument': '⏳'
        };
        return icons[type] || '📌';
    },

    /**
     * Helper: Get status badge
     */
    getStatusBadge(status) {
        const colors = {
            'active': '#4CAF50',
            'pending': '#FF9800',
            'completed': '#2196F3',
            'failed': '#f44336'
        };
        const color = colors[status] || '#999';
        return `<span style="background: ${color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">${status}</span>`;
    },

    /**
     * Helper: Get relationship count
     */
    getRelationshipCount(node) {
        return node.relationships ? node.relationships.length : 0;
    },

    /**
     * Helper: Get relationship icon
     */
    getRelationshipIcon(type) {
        const icons = {
            'CONTAINS_CLAIM': '📦',
            'HAS_SUB_CLAIM': '🔻',
            'SUPPORTS': '✅',
            'CONTRADICTS': '❌',
            'EVIDENCE_FOR': '🔗',
            'PARENT_OF': '⬆️',
            'CHILD_OF': '⬇️'
        };
        return icons[type] || '→';
    },

    /**
     * Toggle properties panel visibility
     */
    togglePropertiesPanel() {
        const detailPanel = document.getElementById('detail-panel');
        if (detailPanel) {
            if (detailPanel.style.display === 'none') {
                if (this.currentNode) {
                    this.renderProperties(this.currentNode);
                }
            } else {
                detailPanel.style.display = 'none';
            }
        }
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        PropertyViewer.init();
    }, 300);
});
