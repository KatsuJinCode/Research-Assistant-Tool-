/**
 * Activity Feed - Real-time activity tracking and history
 *
 * Features:
 * - Timeline of all actions
 * - Real-time updates via WebSocket
 * - Filter by type, date range, entity
 * - Activity statistics dashboard
 * - Export activity log
 */

const ActivityFeed = {
    activities: [],
    filters: {
        type: null,
        entity_id: null,
        since: null
    },
    sidebarOpen: false,
    autoScroll: true,
    pollInterval: null,

    /**
     * Initialize the activity feed
     */
    init() {
        console.log('Initializing Activity Feed...');

        // Setup WebSocket listeners for real-time updates
        if (App.socket) {
            App.socket.on('activity_added', (activity) => this.handleActivityAdded(activity));
        }

        // Setup UI
        this.createSidebar();
        this.setupEventListeners();

        // Load initial activities
        this.loadActivities();

        // Poll for updates every 30 seconds (fallback if WebSocket fails)
        this.pollInterval = setInterval(() => this.loadActivities(true), 30000);

        console.log('✓ Activity Feed initialized');
    },

    /**
     * Create activity feed sidebar
     */
    createSidebar() {
        // Check if sidebar already exists
        if (document.getElementById('activity-feed-sidebar')) {
            return;
        }

        const sidebar = document.createElement('div');
        sidebar.id = 'activity-feed-sidebar';
        sidebar.className = 'activity-feed-sidebar collapsed';
        sidebar.innerHTML = `
            <div class="activity-feed-header">
                <h3>Activity Feed</h3>
                <div class="activity-feed-controls">
                    <button id="activity-filter-btn" class="btn-icon" title="Filter">
                        🔍
                    </button>
                    <button id="activity-stats-btn" class="btn-icon" title="Statistics">
                        📊
                    </button>
                    <button id="activity-export-btn" class="btn-icon" title="Export">
                        💾
                    </button>
                    <button id="activity-close-btn" class="btn-icon" title="Close">
                        ✖
                    </button>
                </div>
            </div>
            <div id="activity-filter-panel" class="activity-filter-panel" style="display: none;">
                <div class="filter-group">
                    <label>Activity Type:</label>
                    <select id="activity-type-filter">
                        <option value="">All Types</option>
                        <option value="document_uploaded">Document Uploaded</option>
                        <option value="document_processed">Document Processed</option>
                        <option value="claim_created">Claim Created</option>
                        <option value="claim_edited">Claim Edited</option>
                        <option value="node_edited">Node Edited</option>
                        <option value="comment_added">Comment Added</option>
                        <option value="search_performed">Search Performed</option>
                        <option value="report_generated">Report Generated</option>
                        <option value="analysis_run">Analysis Run</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label>Since:</label>
                    <select id="activity-since-filter">
                        <option value="">All Time</option>
                        <option value="1h">Last Hour</option>
                        <option value="24h">Last 24 Hours</option>
                        <option value="7d">Last 7 Days</option>
                        <option value="30d">Last 30 Days</option>
                    </select>
                </div>
                <div class="filter-actions">
                    <button id="apply-filters-btn" class="btn btn-primary btn-sm">Apply</button>
                    <button id="clear-filters-btn" class="btn btn-secondary btn-sm">Clear</button>
                </div>
            </div>
            <div id="activity-feed-content" class="activity-feed-content">
                <div class="loading">Loading activities...</div>
            </div>
        `;

        document.body.appendChild(sidebar);

        // Create toggle button in header
        this.createToggleButton();
    },

    /**
     * Create toggle button for activity feed
     */
    createToggleButton() {
        const header = document.querySelector('.header-right') || document.querySelector('header');
        if (!header) {
            console.warn('Header not found, cannot add activity feed toggle');
            return;
        }

        const toggleBtn = document.createElement('button');
        toggleBtn.id = 'activity-feed-toggle';
        toggleBtn.className = 'btn btn-icon';
        toggleBtn.title = 'Activity Feed';
        toggleBtn.innerHTML = '📋';

        toggleBtn.addEventListener('click', () => this.toggleSidebar());

        header.appendChild(toggleBtn);
    },

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Close button
        document.addEventListener('click', (e) => {
            if (e.target.matches('#activity-close-btn')) {
                this.closeSidebar();
            }
        });

        // Filter button
        document.addEventListener('click', (e) => {
            if (e.target.matches('#activity-filter-btn')) {
                this.toggleFilterPanel();
            }
        });

        // Stats button
        document.addEventListener('click', (e) => {
            if (e.target.matches('#activity-stats-btn')) {
                this.showStats();
            }
        });

        // Export button
        document.addEventListener('click', (e) => {
            if (e.target.matches('#activity-export-btn')) {
                this.exportActivities();
            }
        });

        // Apply filters
        document.addEventListener('click', (e) => {
            if (e.target.matches('#apply-filters-btn')) {
                this.applyFilters();
            }
        });

        // Clear filters
        document.addEventListener('click', (e) => {
            if (e.target.matches('#clear-filters-btn')) {
                this.clearFilters();
            }
        });

        // Activity item click (navigate to entity)
        document.addEventListener('click', (e) => {
            if (e.target.matches('.activity-item') || e.target.closest('.activity-item')) {
                const item = e.target.matches('.activity-item') ? e.target : e.target.closest('.activity-item');
                const entityId = item.dataset.entityId;
                if (entityId) {
                    this.navigateToEntity(entityId);
                }
            }
        });
    },

    /**
     * Load activities from API
     */
    async loadActivities(silent = false) {
        try {
            const params = new URLSearchParams({
                limit: 50,
                offset: 0
            });

            // Apply filters
            if (this.filters.type) {
                params.append('type', this.filters.type);
            }
            if (this.filters.entity_id) {
                params.append('entity_id', this.filters.entity_id);
            }
            if (this.filters.since) {
                params.append('since', this.filters.since);
            }

            const response = await fetch(`/api/activity?${params}`);
            const data = await response.json();

            if (data.success) {
                this.activities = data.activities;
                this.renderActivities(data.grouped);
            } else if (!silent) {
                console.error('Failed to load activities:', data.error);
            }
        } catch (error) {
            if (!silent) {
                console.error('Error loading activities:', error);
            }
        }
    },

    /**
     * Render activities grouped by date
     */
    renderActivities(grouped) {
        const content = document.getElementById('activity-feed-content');
        if (!content) return;

        if (this.activities.length === 0) {
            content.innerHTML = '<div class="no-activities">No activities yet</div>';
            return;
        }

        let html = '';

        // Render each date group
        for (const [groupName, activities] of Object.entries(grouped)) {
            html += `
                <div class="activity-group">
                    <div class="activity-group-header">${groupName}</div>
                    <div class="activity-group-items">
                        ${activities.map(activity => this.renderActivityItem(activity)).join('')}
                    </div>
                </div>
            `;
        }

        content.innerHTML = html;

        // Scroll to bottom if auto-scroll enabled
        if (this.autoScroll) {
            content.scrollTop = content.scrollHeight;
        }
    },

    /**
     * Render a single activity item
     */
    renderActivityItem(activity) {
        const icon = this.getActivityIcon(activity.type);
        const timestamp = new Date(activity.created_at).toLocaleTimeString();

        return `
            <div class="activity-item" data-activity-id="${activity.id}" data-entity-id="${activity.entity_id}">
                <span class="activity-icon">${icon}</span>
                <div class="activity-details">
                    <div class="activity-description">${activity.description}</div>
                    <div class="activity-timestamp">${timestamp}</div>
                </div>
            </div>
        `;
    },

    /**
     * Get icon for activity type
     */
    getActivityIcon(type) {
        const icons = {
            'document_uploaded': '📄',
            'document_processed': '✅',
            'claim_created': '💡',
            'claim_edited': '✏️',
            'claim_deleted': '🗑️',
            'node_edited': '✏️',
            'comment_added': '💬',
            'comment_edited': '✏️',
            'comment_deleted': '🗑️',
            'project_created': '📁',
            'project_switched': '🔄',
            'search_performed': '🔍',
            'report_generated': '📊',
            'analysis_run': '🔬',
            'workflow_started': '⚙️',
            'workflow_completed': '✓',
            'agent_spawned': '🤖',
            'agent_completed': '✓'
        };
        return icons[type] || '•';
    },

    /**
     * Toggle sidebar open/closed
     */
    toggleSidebar() {
        if (this.sidebarOpen) {
            this.closeSidebar();
        } else {
            this.openSidebar();
        }
    },

    /**
     * Open sidebar
     */
    openSidebar() {
        const sidebar = document.getElementById('activity-feed-sidebar');
        if (sidebar) {
            sidebar.classList.remove('collapsed');
            this.sidebarOpen = true;
            this.loadActivities();
        }
    },

    /**
     * Close sidebar
     */
    closeSidebar() {
        const sidebar = document.getElementById('activity-feed-sidebar');
        if (sidebar) {
            sidebar.classList.add('collapsed');
            this.sidebarOpen = false;
        }
    },

    /**
     * Toggle filter panel
     */
    toggleFilterPanel() {
        const panel = document.getElementById('activity-filter-panel');
        if (panel) {
            panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
        }
    },

    /**
     * Apply filters
     */
    applyFilters() {
        const typeFilter = document.getElementById('activity-type-filter');
        const sinceFilter = document.getElementById('activity-since-filter');

        this.filters.type = typeFilter.value || null;

        // Convert since filter to ISO timestamp
        const since = sinceFilter.value;
        if (since) {
            const now = new Date();
            switch (since) {
                case '1h':
                    this.filters.since = new Date(now - 3600000).toISOString();
                    break;
                case '24h':
                    this.filters.since = new Date(now - 86400000).toISOString();
                    break;
                case '7d':
                    this.filters.since = new Date(now - 604800000).toISOString();
                    break;
                case '30d':
                    this.filters.since = new Date(now - 2592000000).toISOString();
                    break;
                default:
                    this.filters.since = null;
            }
        } else {
            this.filters.since = null;
        }

        this.loadActivities();
        this.toggleFilterPanel();
    },

    /**
     * Clear all filters
     */
    clearFilters() {
        this.filters = {
            type: null,
            entity_id: null,
            since: null
        };

        document.getElementById('activity-type-filter').value = '';
        document.getElementById('activity-since-filter').value = '';

        this.loadActivities();
        this.toggleFilterPanel();
    },

    /**
     * Show activity statistics
     */
    async showStats() {
        try {
            const response = await fetch('/api/activity/stats');
            const data = await response.json();

            if (data.success) {
                this.renderStats(data.stats);
            } else {
                UI.showError(data.error || 'Failed to load stats');
            }
        } catch (error) {
            console.error('Error loading stats:', error);
            UI.showError('Error loading stats');
        }
    },

    /**
     * Render statistics modal
     */
    renderStats(stats) {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content activity-stats-modal">
                <div class="modal-header">
                    <h2>Activity Statistics</h2>
                    <button class="close-modal">✖</button>
                </div>
                <div class="modal-body">
                    <div class="stats-grid">
                        <div class="stat-card">
                            <h3>Total Activities</h3>
                            <div class="stat-value">${stats.total}</div>
                        </div>
                        <div class="stat-card">
                            <h3>Recent Activity (Last Hour)</h3>
                            <div class="stat-value">${stats.recent_activity.length}</div>
                        </div>
                    </div>

                    <div class="stats-section">
                        <h3>Activities by Type</h3>
                        <div class="stats-chart">
                            ${this.renderTypeChart(stats.by_type)}
                        </div>
                    </div>

                    <div class="stats-section">
                        <h3>Activity Timeline (Last 7 Days)</h3>
                        <div class="stats-chart">
                            ${this.renderDayChart(stats.by_day)}
                        </div>
                    </div>

                    <div class="stats-section">
                        <h3>Most Active Entities</h3>
                        <div class="stats-list">
                            ${stats.most_active_entities.map(entity => `
                                <div class="stats-list-item">
                                    <span>${entity.entity_type}: ${entity.entity_id.substring(0, 8)}...</span>
                                    <span class="badge">${entity.activity_count}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Close modal on click
        modal.querySelector('.close-modal').addEventListener('click', () => {
            modal.remove();
        });
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    },

    /**
     * Render simple bar chart for activity types
     */
    renderTypeChart(byType) {
        const max = Math.max(...Object.values(byType));
        return Object.entries(byType).map(([type, count]) => {
            const percentage = (count / max) * 100;
            return `
                <div class="chart-bar">
                    <span class="chart-label">${type}</span>
                    <div class="chart-bar-container">
                        <div class="chart-bar-fill" style="width: ${percentage}%"></div>
                    </div>
                    <span class="chart-value">${count}</span>
                </div>
            `;
        }).join('');
    },

    /**
     * Render simple line chart for daily activity
     */
    renderDayChart(byDay) {
        const values = Object.values(byDay);
        const max = Math.max(...values, 1);
        return Object.entries(byDay).map(([day, count]) => {
            const percentage = (count / max) * 100;
            const date = new Date(day);
            const label = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            return `
                <div class="chart-bar">
                    <span class="chart-label">${label}</span>
                    <div class="chart-bar-container">
                        <div class="chart-bar-fill" style="width: ${percentage}%"></div>
                    </div>
                    <span class="chart-value">${count}</span>
                </div>
            `;
        }).join('');
    },

    /**
     * Export activities
     */
    async exportActivities() {
        const format = confirm('Export as CSV?\n(Cancel for JSON)') ? 'csv' : 'json';

        try {
            const params = new URLSearchParams({ format });

            // Apply current filters
            if (this.filters.since) {
                params.append('since', this.filters.since);
            }

            const response = await fetch(`/api/activity/export?${params}`);

            if (format === 'csv') {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `activity_log_${new Date().toISOString().split('T')[0]}.csv`;
                a.click();
            } else {
                const data = await response.json();
                if (data.success) {
                    const blob = new Blob([JSON.stringify(data.activities, null, 2)], { type: 'application/json' });
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `activity_log_${new Date().toISOString().split('T')[0]}.json`;
                    a.click();
                }
            }

            UI.showSuccess('Activity log exported');
        } catch (error) {
            console.error('Error exporting activities:', error);
            UI.showError('Error exporting activities');
        }
    },

    /**
     * Navigate to entity
     */
    navigateToEntity(entityId) {
        // Focus on node in graph
        if (typeof GraphRenderer !== 'undefined') {
            GraphRenderer.focusNode(entityId);
        }

        // Load entity in property viewer
        if (typeof PropertyViewer !== 'undefined') {
            PropertyViewer.showNodeProperties(entityId);
        }

        // Close sidebar
        this.closeSidebar();
    },

    /**
     * WebSocket event handler
     */
    handleActivityAdded(activity) {
        // Add to beginning of array
        this.activities.unshift(activity);

        // Trim if too large
        if (this.activities.length > 100) {
            this.activities = this.activities.slice(0, 100);
        }

        // Reload if sidebar is open
        if (this.sidebarOpen) {
            this.loadActivities(true);
        }

        // Show notification for important activities
        if (this.shouldNotify(activity.type)) {
            this.showNotification(activity);
        }
    },

    /**
     * Check if activity type should trigger notification
     */
    shouldNotify(type) {
        const notifyTypes = [
            'document_processed',
            'analysis_run',
            'workflow_completed',
            'report_generated'
        ];
        return notifyTypes.includes(type);
    },

    /**
     * Show activity notification
     */
    showNotification(activity) {
        if (typeof UI !== 'undefined' && UI.showInfo) {
            UI.showInfo(activity.description);
        }
    },

    /**
     * Cleanup
     */
    destroy() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
        }
    }
};

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', () => {
    ActivityFeed.init();
});
