/**
 * Header Manager Module - Unified Header Navigation and Control
 *
 * Handles:
 * - Clickable stat cards navigation
 * - Project selector
 * - Future tab system integration
 */

const HeaderManager = {
    currentProject: 'Default Project',
    activeTab: null,

    /**
     * Initialize header manager
     */
    init() {
        console.log('[HeaderManager] Initializing unified header...');
        this.setupEventListeners();
        this.updateStats();
        console.log('[HeaderManager] ✓ Header manager initialized');
    },

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Stats will update via the existing refresh mechanism
        // Just ensure we're ready to receive updates
        console.log('[HeaderManager] Event listeners ready');
    },

    /**
     * Navigate to a specific stat view
     * This will eventually switch tabs - for now it filters/highlights
     */
    navigateToStat(statType) {
        console.log(`[HeaderManager] Navigating to stat: ${statType}`);

        // Visual feedback - highlight the clicked card
        this.highlightStatCard(statType);

        // Show notification about what was clicked
        const messages = {
            'documents': 'Showing all documents',
            'claims': 'Showing all claims',
            'evidence': 'Showing evidence relationships',
            'pending': 'Showing pending documents'
        };

        if (window.UI && UI.showNotification) {
            UI.showNotification(messages[statType] || 'Navigating...', 'info');
        }

        // TODO: When tab system is implemented, switch to the appropriate tab
        // For now, we can filter the sidebar or graph view
        this.filterByType(statType);
    },

    /**
     * Highlight the clicked stat card
     */
    highlightStatCard(statType) {
        // Remove previous highlights
        document.querySelectorAll('.stat-card').forEach(card => {
            card.style.border = '2px solid rgba(255, 255, 255, 0.2)';
        });

        // Highlight the clicked card
        const cardId = `stat-card-${statType}`;
        const card = document.getElementById(cardId);
        if (card) {
            card.style.border = '2px solid rgba(255, 255, 255, 0.8)';

            // Reset after 2 seconds
            setTimeout(() => {
                card.style.border = '2px solid rgba(255, 255, 255, 0.2)';
            }, 2000);
        }
    },

    /**
     * Filter view by type (temporary until tab system is ready)
     */
    filterByType(type) {
        console.log(`[HeaderManager] Filtering by type: ${type}`);

        // Map stat types to node types
        const typeMap = {
            'documents': 'Document',
            'claims': 'Claim',
            'evidence': 'Evidence',
            'pending': 'PendingDocument'
        };

        const nodeType = typeMap[type];
        if (!nodeType) return;

        // If GraphRenderer exists, we could filter the graph
        if (window.GraphRenderer && GraphRenderer.currentGraphData) {
            const filteredNodes = GraphRenderer.currentGraphData.nodes.filter(n => {
                if (type === 'evidence') {
                    // For evidence, show nodes that have evidence links
                    return true; // TODO: Implement proper evidence filtering
                }
                return n.type === nodeType;
            });

            console.log(`[HeaderManager] Found ${filteredNodes.length} nodes of type ${nodeType}`);

            // You could highlight these nodes or update the sidebar
            // For now, just log the count
        }

        // Update sidebar title to reflect filter
        const sidebarTitle = document.querySelector('#sidebar h2');
        if (sidebarTitle) {
            sidebarTitle.textContent = {
                'documents': '📄 Documents',
                'claims': '📝 Claims',
                'evidence': '🔗 Evidence Links',
                'pending': '⏳ Pending Documents'
            }[type] || 'Documents';
        }
    },

    /**
     * Open project selector modal
     */
    openProjectSelector() {
        console.log('[HeaderManager] Opening project selector...');

        // Create modal for project selection
        const modalHTML = `
            <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 10000; display: flex; align-items: center; justify-content: center;"
                 onclick="this.remove()">
                <div style="background: #2a2a2a; width: 500px; max-width: 90%; border-radius: 12px; padding: 30px; box-shadow: 0 8px 32px rgba(0,0,0,0.5);"
                     onclick="event.stopPropagation();">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px;">
                        <h2 style="margin: 0; color: #2196F3;">📁 Select Project</h2>
                        <button onclick="this.closest('[onclick*=remove]').remove()"
                                style="background: none; border: none; color: #999; font-size: 24px; cursor: pointer; padding: 0; width: 30px; height: 30px; line-height: 1;"
                                title="Close">×</button>
                    </div>

                    <div style="margin-bottom: 20px;">
                        <p style="color: #999; font-size: 13px; margin-bottom: 15px;">
                            Project management allows you to organize your research into separate workspaces.
                        </p>
                    </div>

                    <div id="project-list" style="max-height: 300px; overflow-y: auto; margin-bottom: 20px;">
                        <div class="project-item" style="background: #333; padding: 15px; border-radius: 6px; margin-bottom: 10px; cursor: pointer; border: 2px solid #2196F3;"
                             onclick="HeaderManager.selectProject('Default Project')">
                            <div style="display: flex; align-items: center; gap: 12px;">
                                <span style="font-size: 24px;">📁</span>
                                <div style="flex: 1;">
                                    <div style="font-weight: 600; color: white; margin-bottom: 4px;">Default Project</div>
                                    <div style="font-size: 12px; color: #999;">Active project</div>
                                </div>
                                <span style="color: #2196F3; font-size: 20px;">✓</span>
                            </div>
                        </div>

                        <div style="text-align: center; padding: 40px 20px; color: #666; font-style: italic;">
                            <p style="margin-bottom: 10px;">More projects coming soon!</p>
                            <p style="font-size: 12px;">Project management system in development.</p>
                        </div>
                    </div>

                    <div style="display: flex; gap: 10px;">
                        <button style="flex: 1; background: #2196F3; color: white; border: none; padding: 12px; border-radius: 6px; cursor: pointer; font-weight: 500;"
                                onclick="HeaderManager.createNewProject()">
                            ➕ New Project
                        </button>
                        <button style="flex: 1; background: #555; color: white; border: none; padding: 12px; border-radius: 6px; cursor: pointer; font-weight: 500;"
                                onclick="this.closest('[onclick*=remove]').remove()">
                            Cancel
                        </button>
                    </div>
                </div>
            </div>
        `;

        const modalDiv = document.createElement('div');
        modalDiv.innerHTML = modalHTML;
        document.body.appendChild(modalDiv);
    },

    /**
     * Select a project
     */
    selectProject(projectName) {
        this.currentProject = projectName;
        document.getElementById('current-project-name').textContent = projectName;

        // Close modal
        document.querySelector('[onclick*="remove"]').click();

        if (window.UI && UI.showNotification) {
            UI.showNotification(`Switched to project: ${projectName}`, 'success');
        }

        console.log(`[HeaderManager] Switched to project: ${projectName}`);
    },

    /**
     * Create new project (placeholder for future implementation)
     */
    createNewProject() {
        console.log('[HeaderManager] Opening project management modal');

        // Open the project management modal (which has create functionality)
        if (window.ProjectManager && ProjectManager.openProjectModal) {
            ProjectManager.openProjectModal();
        } else {
            console.error('[HeaderManager] ProjectManager not available');
            if (window.UI && UI.showNotification) {
                UI.showNotification('Project manager not loaded', 'error');
            }
        }
    },

    /**
     * Update stats in the unified header
     */
    updateStats() {
        // This will be called by the existing stats update mechanism
        // The stats are already being updated via the existing system
        console.log('[HeaderManager] Stats update requested');
    },

    /**
     * Set active tab (for future tab system)
     */
    setActiveTab(tabName) {
        this.activeTab = tabName;
        console.log(`[HeaderManager] Active tab set to: ${tabName}`);

        // TODO: Update tab visual state when tab system is implemented
    },

    /**
     * Add visual indicator when data is loading
     */
    showLoadingState() {
        const statsContainer = document.querySelector('.stats-container');
        if (statsContainer) {
            statsContainer.style.opacity = '0.6';
            statsContainer.style.pointerEvents = 'none';
        }
    },

    /**
     * Remove loading state
     */
    hideLoadingState() {
        const statsContainer = document.querySelector('.stats-container');
        if (statsContainer) {
            statsContainer.style.opacity = '1';
            statsContainer.style.pointerEvents = 'auto';
        }
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        HeaderManager.init();
    }, 100);
});
