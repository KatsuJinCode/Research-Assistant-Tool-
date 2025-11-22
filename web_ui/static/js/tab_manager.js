/**
 * Tab Manager Module - Tab Navigation and State Management
 *
 * Handles:
 * - Tab switching with smooth transitions
 * - Tab state preservation (scroll positions, filters)
 * - Tab badge updates (notifications)
 * - Integration with AI assistant context
 */

const TabManager = {
    currentTab: 'documents',
    tabStates: {},
    currentAgentFilter: 'active', // Track current agent filter

    /**
     * Initialize tab manager
     */
    init() {
        console.log('[TabManager] Initializing tab navigation system...');

        // Initialize tab states
        this.tabStates = {
            documents: { scrollTop: 0, filters: {} },
            search: { scrollTop: 0, query: '', filters: {} },
            agents: { scrollTop: 0, expandedAgents: [] },
            projects: { scrollTop: 0, selectedProject: null }
        };

        // Load saved states from localStorage
        this.loadTabStates();

        // Set initial tab
        this.switchTab('documents', false);

        console.log('[TabManager] ✓ Tab manager initialized');
    },

    /**
     * Switch to a different tab
     */
    switchTab(tabId, saveCurrentState = true) {
        console.log(`[TabManager] Switching to tab: ${tabId}`);

        // Save current tab state before switching
        if (saveCurrentState && this.currentTab) {
            this.saveCurrentTabState();
        }

        // Hide all tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.style.display = 'none';
            content.classList.remove('active');
        });

        // Remove active class from all tabs
        document.querySelectorAll('.tab').forEach(tab => {
            tab.classList.remove('active');
        });

        // Show selected tab content
        const tabContent = document.getElementById(`tab-${tabId}`);
        if (tabContent) {
            tabContent.style.display = 'block';
            tabContent.classList.add('active');

            // Restore scroll position
            const contentArea = document.getElementById('tab-content-area');
            if (contentArea && this.tabStates[tabId]) {
                setTimeout(() => {
                    contentArea.scrollTop = this.tabStates[tabId].scrollTop || 0;
                }, 50);
            }
        }

        // Activate tab button
        const tabButton = document.querySelector(`.tab[data-tab="${tabId}"]`);
        if (tabButton) {
            tabButton.classList.add('active');
        }

        // Update current tab
        this.currentTab = tabId;

        // Render tab-specific content
        this.renderTabContent(tabId);

        // Update AI assistant context
        if (window.AIAssistant) {
            AIAssistant.updateContext(tabId);
        }

        // Save tab states
        this.saveTabStates();

        // Notify other systems
        this.notifyTabChange(tabId);
    },

    /**
     * Save current tab's scroll position and state
     */
    saveCurrentTabState() {
        if (!this.currentTab) return;

        const contentArea = document.getElementById('tab-content-area');
        if (contentArea) {
            this.tabStates[this.currentTab].scrollTop = contentArea.scrollTop;
        }

        // Save tab-specific state
        switch (this.currentTab) {
            case 'search':
                const searchInput = document.getElementById('search-input');
                if (searchInput) {
                    this.tabStates.search.query = searchInput.value;
                }
                break;

            case 'agents':
                // Save which agents are expanded
                const expandedAgents = [];
                document.querySelectorAll('.agent-item.expanded').forEach(agent => {
                    expandedAgents.push(agent.dataset.agentId);
                });
                this.tabStates.agents.expandedAgents = expandedAgents;
                break;
        }
    },

    /**
     * Render tab-specific content
     */
    renderTabContent(tabId) {
        switch (tabId) {
            case 'documents':
                this.renderDocumentsTab();
                break;
            case 'search':
                this.renderSearchTab();
                break;
            case 'agents':
                this.renderAgentsTab();
                break;
            case 'projects':
                this.renderProjectsTab();
                break;
        }
    },

    /**
     * Render Documents tab content
     */
    renderDocumentsTab() {
        // Documents content is already in the HTML
        // Just ensure it's visible and stats are updated
        if (window.UI && UI.updateStats) {
            UI.updateStats();
        }
    },

    /**
     * Render Search tab content
     */
    renderSearchTab() {
        const tabContent = document.getElementById('tab-search');
        if (!tabContent) return;

        if (tabContent.children.length === 0) {
            tabContent.innerHTML = `
                <h2 style="margin-bottom: 15px;">🔍 Advanced Search</h2>

                <div style="margin-bottom: 20px;">
                    <input type="text" id="search-input" placeholder="Search documents, claims, evidence..."
                           style="width: 100%; padding: 10px; background: #333; border: 1px solid #555; border-radius: 6px; color: white;"
                           value="${this.tabStates.search.query || ''}" />
                </div>

                <div style="margin-bottom: 20px;">
                    <h3 style="font-size: 13px; color: #999; margin-bottom: 10px;">Search Type</h3>
                    <div style="display: flex; flex-direction: column; gap: 8px;">
                        <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                            <input type="radio" name="search-type" value="text" checked />
                            <span>Text Search</span>
                        </label>
                        <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                            <input type="radio" name="search-type" value="semantic" />
                            <span>Semantic Search</span>
                        </label>
                        <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                            <input type="radio" name="search-type" value="llm" />
                            <span>LLM-Powered Search</span>
                        </label>
                    </div>
                </div>

                <div style="margin-bottom: 20px;">
                    <h3 style="font-size: 13px; color: #999; margin-bottom: 10px;">Filter by Type</h3>
                    <div style="display: flex; flex-direction: column; gap: 8px;">
                        <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                            <input type="checkbox" checked />
                            <span>📄 Documents</span>
                        </label>
                        <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                            <input type="checkbox" checked />
                            <span>📝 Claims</span>
                        </label>
                        <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                            <input type="checkbox" checked />
                            <span>🔗 Evidence</span>
                        </label>
                    </div>
                </div>

                <button onclick="TabManager.executeSearch()"
                        style="width: 100%; padding: 12px; background: linear-gradient(135deg, #2196F3, #1976D2); color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 500;">
                    Search
                </button>

                <div id="search-results" style="margin-top: 20px;"></div>
            `;

            // Add search input listener
            const searchInput = document.getElementById('search-input');
            if (searchInput) {
                searchInput.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        this.executeSearch();
                    }
                });
            }
        }
    },

    /**
     * Render Agents tab content
     */
    renderAgentsTab() {
        const tabContent = document.getElementById('tab-agents');
        if (!tabContent) return;

        const activeStyle = 'flex: 1; padding: 8px; background: #2196F3; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 600;';
        const inactiveStyle = 'flex: 1; padding: 8px; background: #333; color: #999; border: 1px solid #444; border-radius: 6px; cursor: pointer;';

        tabContent.innerHTML = `
            <div style="margin-bottom: 12px; display: flex; gap: 4px;">
                <button id="agent-filter-active" onclick="TabManager.setAgentFilter('active')"
                        style="${this.currentAgentFilter === 'active' ? activeStyle : inactiveStyle}">
                    Active (<span id="active-agent-count">0</span>)
                </button>
                <button id="agent-filter-completed" onclick="TabManager.setAgentFilter('completed')"
                        style="${this.currentAgentFilter === 'completed' ? activeStyle : inactiveStyle}">
                    Completed (<span id="completed-agent-count">0</span>)
                </button>
                <button id="agent-filter-failed" onclick="TabManager.setAgentFilter('failed')"
                        style="${this.currentAgentFilter === 'failed' ? activeStyle : inactiveStyle}">
                    Failed (<span id="failed-agent-count">0</span>)
                </button>
            </div>

            <div id="agent-list" style="display: flex; flex-direction: column; gap: 10px;">
                <div style="text-align: center; padding: 40px 20px; color: #666;">
                    <div style="font-size: 48px; margin-bottom: 10px;">🤖</div>
                    <p>No ${this.currentAgentFilter} agents</p>
                    <p style="font-size: 12px; color: #999; margin-top: 10px;">
                        Agents will appear here when processing documents
                    </p>
                </div>
            </div>
        `;

        // Load agent data if AgentMonitor exists
        if (window.AgentMonitor) {
            this.updateAgentList();
        }
    },

    /**
     * Render Projects tab content
     */
    renderProjectsTab() {
        const tabContent = document.getElementById('tab-projects');
        if (!tabContent) return;

        tabContent.innerHTML = `
            <h2 style="margin-bottom: 15px;">📁 Projects</h2>

            <div style="margin-bottom: 20px;">
                <button onclick="HeaderManager.createNewProject()"
                        style="width: 100%; padding: 12px; background: linear-gradient(135deg, #2196F3, #1976D2); color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 500;">
                    ➕ New Project
                </button>
            </div>

            <div id="project-list" style="display: flex; flex-direction: column; gap: 10px;">
                <div class="project-card" style="background: #333; padding: 15px; border-radius: 8px; border: 2px solid #2196F3; cursor: pointer;">
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <span style="font-size: 32px;">📁</span>
                        <div style="flex: 1;">
                            <div style="font-weight: 600; color: white; margin-bottom: 4px;">Default Project</div>
                            <div style="font-size: 12px; color: #999;">Active • 0 documents</div>
                        </div>
                        <span style="color: #2196F3; font-size: 20px;">✓</span>
                    </div>
                </div>

                <div style="text-align: center; padding: 40px 20px; color: #666; border: 2px dashed #444; border-radius: 8px;">
                    <p style="margin-bottom: 10px;">Create more projects to organize your research</p>
                    <p style="font-size: 12px; color: #999;">Project management system coming soon</p>
                </div>
            </div>
        `;
    },

    /**
     * Execute search
     */
    executeSearch() {
        const searchInput = document.getElementById('search-input');
        const query = searchInput ? searchInput.value : '';

        if (!query.trim()) {
            if (window.UI && UI.showNotification) {
                UI.showNotification('Please enter a search query', 'warning');
            }
            return;
        }

        console.log(`[TabManager] Executing search: ${query}`);

        // Get search type
        const searchType = document.querySelector('input[name="search-type"]:checked')?.value || 'text';

        // Get filters
        const includeDocuments = document.querySelector('input[type="checkbox"]')?.checked;

        // Show loading state
        const resultsDiv = document.getElementById('search-results');
        if (resultsDiv) {
            resultsDiv.innerHTML = '<div style="text-align: center; padding: 20px; color: #999;">Searching...</div>';
        }

        // Perform search based on type
        if (searchType === 'text') {
            this.performTextSearch(query);
        } else if (searchType === 'semantic') {
            this.performSemanticSearch(query);
        } else if (searchType === 'llm') {
            this.performLLMSearch(query);
        }
    },

    /**
     * Perform text search
     */
    performTextSearch(query) {
        // Use existing search functionality
        if (window.UI && UI.searchDocuments) {
            UI.searchDocuments(query);
        }

        // Display results in search tab
        setTimeout(() => {
            const resultsDiv = document.getElementById('search-results');
            if (resultsDiv) {
                resultsDiv.innerHTML = `
                    <div style="padding: 15px; background: #333; border-radius: 6px;">
                        <div style="color: #2196F3; margin-bottom: 10px;">Search results for: "${query}"</div>
                        <div style="font-size: 12px; color: #999;">Results are displayed in the graph view</div>
                    </div>
                `;
            }
        }, 500);
    },

    /**
     * Perform semantic search
     */
    performSemanticSearch(query) {
        console.log(`[TabManager] Semantic search: ${query}`);

        const resultsDiv = document.getElementById('search-results');
        if (resultsDiv) {
            resultsDiv.innerHTML = `
                <div style="padding: 15px; background: #333; border-radius: 6px;">
                    <div style="color: #2196F3; margin-bottom: 10px;">Semantic search coming soon!</div>
                    <div style="font-size: 12px; color: #999;">This will use embeddings to find semantically similar content</div>
                </div>
            `;
        }
    },

    /**
     * Perform LLM search
     */
    performLLMSearch(query) {
        console.log(`[TabManager] LLM search: ${query}`);

        const resultsDiv = document.getElementById('search-results');
        if (resultsDiv) {
            resultsDiv.innerHTML = `
                <div style="padding: 15px; background: #333; border-radius: 6px;">
                    <div style="color: #2196F3; margin-bottom: 10px;">LLM-powered search coming soon!</div>
                    <div style="font-size: 12px; color: #999;">This will use AI to understand natural language queries</div>
                </div>
            `;
        }
    },

    /**
     * Update agent list with optional filter
     */
    updateAgentList(filter = null) {
        const filterToUse = filter || this.currentAgentFilter;

        console.log(`[TabManager] Updating agent list (filter: ${filterToUse})...`);

        // Get agent list container
        const agentList = document.getElementById('agent-list');
        if (!agentList) return;

        // If AgentMonitor exists, use it to get agents
        if (window.AgentMonitor && window.AgentMonitor.getAgents) {
            const allAgents = window.AgentMonitor.getAgents();

            // Filter agents by status
            const filteredAgents = allAgents.filter(agent => {
                if (filterToUse === 'active') {
                    return agent.status === 'active' || agent.status === 'running' || agent.status === 'processing';
                } else if (filterToUse === 'completed') {
                    return agent.status === 'completed' || agent.status === 'success' || agent.status === 'done';
                } else if (filterToUse === 'failed') {
                    return agent.status === 'failed' || agent.status === 'error';
                }
                return false;
            });

            // Update counts
            const activeCount = allAgents.filter(a => ['active', 'running', 'processing'].includes(a.status)).length;
            const completedCount = allAgents.filter(a => ['completed', 'success', 'done'].includes(a.status)).length;
            const failedCount = allAgents.filter(a => ['failed', 'error'].includes(a.status)).length;

            const activeCountEl = document.getElementById('active-agent-count');
            const completedCountEl = document.getElementById('completed-agent-count');
            const failedCountEl = document.getElementById('failed-agent-count');

            if (activeCountEl) activeCountEl.textContent = activeCount;
            if (completedCountEl) completedCountEl.textContent = completedCount;
            if (failedCountEl) failedCountEl.textContent = failedCount;

            // Render filtered agents
            if (filteredAgents.length === 0) {
                agentList.innerHTML = `
                    <div style="text-align: center; padding: 40px 20px; color: #666;">
                        <div style="font-size: 48px; margin-bottom: 10px;">🤖</div>
                        <p>No ${filterToUse} agents</p>
                        <p style="font-size: 12px; color: #999; margin-top: 10px;">
                            Agents will appear here when processing documents
                        </p>
                    </div>
                `;
            } else {
                // Render agent cards
                agentList.innerHTML = filteredAgents.map(agent => `
                    <div class="agent-card" style="background: #333; padding: 12px; border-radius: 6px; border-left: 4px solid ${this.getAgentStatusColor(agent.status)};">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <div style="font-weight: 600; color: white;">${agent.name || 'Agent'}</div>
                            <div style="font-size: 10px; color: #999; text-transform: uppercase;">${agent.status}</div>
                        </div>
                        <div style="font-size: 12px; color: #ccc; margin-bottom: 4px;">${agent.type || 'Unknown type'}</div>
                        <div style="font-size: 11px; color: #999;">${agent.description || 'Processing...'}</div>
                    </div>
                `).join('');
            }
        } else {
            // No AgentMonitor - show empty state
            agentList.innerHTML = `
                <div style="text-align: center; padding: 40px 20px; color: #666;">
                    <div style="font-size: 48px; margin-bottom: 10px;">🤖</div>
                    <p>No ${filterToUse} agents</p>
                    <p style="font-size: 12px; color: #999; margin-top: 10px;">
                        Agents will appear here when processing documents
                    </p>
                </div>
            `;
        }
    },

    /**
     * Get status color for agent
     */
    getAgentStatusColor(status) {
        const statusColors = {
            'active': '#2196F3',
            'running': '#2196F3',
            'processing': '#2196F3',
            'completed': '#4CAF50',
            'success': '#4CAF50',
            'done': '#4CAF50',
            'failed': '#f44336',
            'error': '#f44336'
        };
        return statusColors[status] || '#666';
    },

    /**
     * Set agent filter (active, completed, failed)
     */
    setAgentFilter(filter) {
        console.log(`[TabManager] Setting agent filter: ${filter}`);

        this.currentAgentFilter = filter;

        // Update button styles
        const activeStyle = 'flex: 1; padding: 8px; background: #2196F3; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 600;';
        const inactiveStyle = 'flex: 1; padding: 8px; background: #333; color: #999; border: 1px solid #444; border-radius: 6px; cursor: pointer;';

        const activeBtn = document.getElementById('agent-filter-active');
        const completedBtn = document.getElementById('agent-filter-completed');
        const failedBtn = document.getElementById('agent-filter-failed');

        if (activeBtn) activeBtn.style.cssText = filter === 'active' ? activeStyle : inactiveStyle;
        if (completedBtn) completedBtn.style.cssText = filter === 'completed' ? activeStyle : inactiveStyle;
        if (failedBtn) failedBtn.style.cssText = filter === 'failed' ? activeStyle : inactiveStyle;

        // Update agent list with filter
        this.updateAgentList(filter);
    },

    /**
     * Update tab badge (notification count)
     */
    updateBadge(tabId, count) {
        const badge = document.querySelector(`.tab[data-tab="${tabId}"] .tab-badge`);
        if (badge) {
            if (count > 0) {
                badge.textContent = count;
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }
        }
    },

    /**
     * Notify other systems of tab change
     */
    notifyTabChange(tabId) {
        const event = new CustomEvent('tabChanged', { detail: { tabId } });
        window.dispatchEvent(event);
    },

    /**
     * Save tab states to localStorage
     */
    saveTabStates() {
        try {
            localStorage.setItem('tabStates', JSON.stringify(this.tabStates));
            localStorage.setItem('currentTab', this.currentTab);
        } catch (e) {
            console.warn('[TabManager] Failed to save tab states:', e);
        }
    },

    /**
     * Load tab states from localStorage
     */
    loadTabStates() {
        try {
            const savedStates = localStorage.getItem('tabStates');
            if (savedStates) {
                this.tabStates = { ...this.tabStates, ...JSON.parse(savedStates) };
            }

            const savedTab = localStorage.getItem('currentTab');
            if (savedTab) {
                this.currentTab = savedTab;
            }
        } catch (e) {
            console.warn('[TabManager] Failed to load tab states:', e);
        }
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        TabManager.init();
    }, 150);
});
