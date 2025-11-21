/**
 * Main Application - Coordinates all modules and handles initialization
 */

const App = {
    socket: null,
    processingInProgress: false,  // Track if document processing is ongoing
    claimStates: {},  // Track claim processing states for live updates

    /**
     * Initialize the application
     */
    async init() {
        console.log('Initializing Research Graph Interface...');

        // Setup Socket.IO for real-time updates
        this.initializeSocket();

        // Load version info (build hash, restart count)
        await this.loadVersionInfo();

        // Load initial data (safe to call even during processing)
        await this.loadGraph();
        await this.loadStats();

        // Setup event listeners
        this.setupEventListeners();

        console.log('✓ Application ready');
    },

    /**
     * Initialize WebSocket connection
     */
    initializeSocket() {
        this.socket = io();

        this.socket.on('connect', () => {
            console.log('✓ WebSocket connected');
        });

        this.socket.on('processing_update', (data) => {
            console.log('Processing update:', data);

            // Update progress UI
            UI.updateProcessingStatus(data.message, data.progress);

            // Handle node updates (e.g., document title changes)
            if (data.data && data.data.node_update) {
                console.log('Node update:', data.data.node_update);
                GraphRenderer.updateNodeLabel(
                    data.data.node_update.node_id,
                    data.data.node_update.updates.title
                );
            }

            // Handle different events from the nested data.data.event field
            if (data.data && data.data.event === 'document_created') {
                // Document node created - add incrementally with processing indicator
                console.log('[app.js] Document created event received:', data.data.doc_id, data.data.node_data);
                this.processingInProgress = true;
                if (data.data.node_data) {
                    const nodeData = {
                        id: data.data.node_data.id,
                        label: data.data.node_data.title || 'Untitled Document',
                        type: 'document',
                        fullData: data.data.node_data,
                        processing: true,  // Mark as processing
                        progress: data.progress || 0
                    };
                    console.log('[app.js] Adding document node to graph:', nodeData);
                    GraphRenderer.addNodeIncremental(nodeData, null);
                } else {
                    console.error('[app.js] document_created event missing node_data!', data);
                }
            // MVP: super_claim_added event disabled - using flat structure
            // Will be re-enabled when community detection is implemented
            /* } else if (data.data && data.data.event === 'super_claim_added') {
                // Super-claim added - add incrementally with link to document
                console.log('Super-claim added:', data.data.super_claim_id);
                if (data.data.node_data) {
                    const nodeData = {
                        id: data.data.node_data.id,
                        label: data.data.node_data.summary || data.data.node_data.text?.substring(0, 40) || 'Claim',
                        type: 'super',
                        fullData: data.data.node_data,
                        fresh: true  // Mark as fresh/newly added
                    };
                    GraphRenderer.addNodeIncremental(nodeData, data.data.doc_id);
                }
                // Update document progress
                if (data.data.doc_id && data.progress) {
                    GraphRenderer.updateDocumentProgress(data.data.doc_id, data.progress);
                }
            */
            } else if (data.data && data.data.event === 'claim_added') {
                // Claim added - add incrementally with link to parent (MVP: all claims link directly to document)
                console.log('Claim added:', data.data.claim_id);
                if (data.data.node_data) {
                    const nodeData = {
                        id: data.data.node_data.id,
                        label: data.data.node_data.summary || data.data.node_data.text?.substring(0, 40) || 'Claim',
                        type: 'sub',  // Visual type (can be 'super' later for community detection)
                        fullData: data.data.node_data,
                        fresh: true  // Mark as fresh/newly added
                    };
                    // MVP: Use parent_id from event (directly to document, no super-claims)
                    const parentId = data.data.parent_id || data.data.doc_id;
                    GraphRenderer.addNodeIncremental(nodeData, parentId);
                }
                // Update document progress
                if (data.data.doc_id && data.progress) {
                    GraphRenderer.updateDocumentProgress(data.data.doc_id, data.progress);
                }
            } else if (data.data && data.data.event === 'processing_complete') {
                // Mark document as complete
                console.log('Document processing complete');
                this.processingInProgress = false;
                UI.updateProcessingStatus('Processing complete!', 100);
                if (data.data.doc_id) {
                    GraphRenderer.markDocumentComplete(data.data.doc_id);
                }
                // Mark all fresh nodes as processed after a delay
                setTimeout(() => {
                    GraphRenderer.clearFreshFlags();
                }, 2000);
                this.loadStats();
            } else if (data.data && data.data.event === 'claim_updated') {
                // Claim finished processing - update its appearance
                console.log('Claim updated:', data.data.claim_id, data.data.updates);
                if (data.data.claim_id && data.data.updates) {
                    GraphRenderer.updateClaimNode(
                        data.data.claim_id,
                        data.data.updates
                    );
                }
                // Update document progress
                if (data.data.doc_id && data.progress) {
                    GraphRenderer.updateDocumentProgress(data.data.doc_id, data.progress);
                }
            } else if (data.data && (data.data.event === 'claim_extraction_failed' ||
                       data.data.event === 'claim_simplification_failed')) {
                // Display error prominently
                console.error('AI Agent failure:', data.data.error);
                this.processingInProgress = false;
                alert('AI AGENT FAILURE\n\n' + data.data.error + '\n\nCheck that your AI agent CLI is installed and configured properly.\nSee AGENT_CONFIGURATION.md for setup instructions.');
            } else if (data.data && data.data.event === 'duplicates_found') {
                // Duplicate claims detected
                console.log('Duplicates found:', data.data.duplicates);
                const duplicates = data.data.duplicates || [];

                // Mark duplicate claims in the graph
                duplicates.forEach(dup => {
                    GraphRenderer.markClaimAsDuplicate(
                        dup.new_claim_id,
                        dup.existing_claim_id,
                        dup.similarity_score,
                        dup.match_quality
                    );
                });

                // Show notification to user
                if (duplicates.length > 0) {
                    UI.showNotification(
                        `Found ${duplicates.length} duplicate claim${duplicates.length > 1 ? 's' : ''} from previous documents`,
                        'info'
                    );
                }
            }
        });

        this.socket.on('claim_added', (data) => {
            console.log('Deprecated claim_added event:', data.claim_summary);
            // This event is deprecated - processing_update handles incremental adds
        });

        this.socket.on('document_processed', (data) => {
            console.log('Document processing complete:', data.doc_id);
            UI.updateProcessingStatus('Processing complete!', 100);
            this.loadGraph();
            this.loadStats();
        });

        this.socket.on('queue_update', (data) => {
            console.log('Queue update:', data);
            UI.updateQueueStatus(data.processing, data.queue_size);
        });

        // NEW: Claim stage update events for live 4-stage pipeline visualization
        this.socket.on('claim_stage_update', (data) => {
            const { claim_id, stage, status } = data;
            console.log(`Claim ${claim_id} - ${stage}: ${status}`, data);

            // Initialize claim state if needed
            if (!this.claimStates[claim_id]) {
                this.claimStates[claim_id] = {
                    stages: {
                        analysis: { status: 'pending' },
                        clarification: { status: 'pending' },
                        simplification: { status: 'pending' },
                        validation: { status: 'pending' }
                    },
                    allData: {}
                };
            }

            // Update stage status
            this.claimStates[claim_id].stages[stage] = { status, ...data.data };
            this.claimStates[claim_id].allData[stage] = data.data;

            // Update visual processing stage label on the node
            if (status === 'in_progress') {
                const stageLabels = {
                    'analysis': 'Analyzing...',
                    'clarification': 'Clarifying...',
                    'simplification': 'Simplifying...',
                    'validation': 'Validating...'
                };
                GraphRenderer.updateProcessingStage(claim_id, stageLabels[stage] || stage);
            } else if (status === 'complete') {
                const duration = data.data?.duration_ms;
                console.log(`✓ ${stage} complete ${duration ? `(${(duration/1000).toFixed(1)}s)` : ''}`);
            }
        });

        // NEW: Claim complete event - final results ready
        this.socket.on('claim_complete', (data) => {
            const { claim_id, final_text, quality_score, disposition, total_duration_ms } = data;
            console.log(`✓ Claim ${claim_id} complete:`, {
                text: final_text,
                quality: quality_score,
                disposition: disposition,
                duration: `${(total_duration_ms/1000).toFixed(1)}s`
            });

            // Store final data
            if (this.claimStates[claim_id]) {
                this.claimStates[claim_id].final = {
                    text: final_text,
                    quality_score: quality_score,
                    disposition: disposition,
                    total_duration_ms: total_duration_ms
                };
            }
        });
    },

    /**
     * Load and render graph data
     */
    async loadGraph() {
        try {
            const graphData = await API.fetchGraph();
            GraphRenderer.updateGraphSmooth(graphData);
            console.log(`✓ Loaded graph: ${graphData.length} documents`);
        } catch (error) {
            console.error('Failed to load graph:', error);
        }
    },

    /**
     * Load and display statistics
     */
    async loadStats() {
        try {
            const stats = await API.fetchStats();
            UI.updateStats(stats);
        } catch (error) {
            console.error('Failed to load stats:', error);
        }
    },

    /**
     * Load and display version info (build hash, restart count)
     */
    async loadVersionInfo() {
        try {
            // Add cache-busting timestamp to force fresh load
            const response = await fetch('/static/VERSION.json?t=' + Date.now());
            const version = await response.json();

            const buildEl = document.getElementById('version-build');
            const restartEl = document.getElementById('version-restart');

            if (buildEl) {
                buildEl.textContent = `Build: ${version.build_hash}`;
            }
            if (restartEl) {
                restartEl.textContent = `Restart #${version.restart_count}`;
            }

            console.log('✓ Version loaded:', version);
        } catch (error) {
            console.warn('Could not load version info:', error);
            const buildEl = document.getElementById('version-build');
            if (buildEl) {
                buildEl.textContent = 'Build: unknown';
            }
        }
    },

    /**
     * Setup UI event listeners
     */
    setupEventListeners() {
        // Upload button - triggers file input
        const uploadBtn = document.getElementById('upload-btn');
        const fileInput = document.getElementById('file-input');
        const uploadZone = document.getElementById('upload-zone');

        console.log('Upload button found:', uploadBtn);
        console.log('File input found:', fileInput);
        console.log('Upload zone found:', uploadZone);

        if (uploadBtn && fileInput) {
            // Main upload button click handler
            uploadBtn.addEventListener('click', (e) => {
                // CRITICAL: Don't call preventDefault() or stopPropagation() before fileInput.click()
                // Browser security requires file picker to be triggered in same call stack as user event
                fileInput.click();
            });

            // Also allow clicking the upload zone (except the button itself)
            if (uploadZone) {
                uploadZone.addEventListener('click', (e) => {
                    // Don't trigger if clicking the button or URL input
                    if (e.target === uploadBtn || e.target.id === 'url-input') {
                        return;
                    }

                    // CRITICAL: Don't call preventDefault() or stopPropagation() before fileInput.click()
                    // Browser security requires file picker to be triggered in same call stack as user event
                    fileInput.click();
                });
            }

            // File upload handler (supports multiple files)
            fileInput.addEventListener('change', (e) => {
                console.log('File(s) selected:', e.target.files.length, 'file(s)');
                const files = e.target.files;
                if (files.length > 0) {
                    if (files.length === 1) {
                        console.log('Processing file:', files[0].name);
                    } else {
                        console.log(`Processing ${files.length} files:`, Array.from(files).map(f => f.name));
                    }
                    UI.handleFileUpload(files);
                    // Reset input so same files can be uploaded again
                    fileInput.value = '';
                }
            });

            // Drag and drop on upload zone
            if (uploadZone) {
                uploadZone.addEventListener('dragover', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    uploadZone.style.opacity = '0.7';
                });

                uploadZone.addEventListener('dragleave', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    uploadZone.style.opacity = '1';
                });

                uploadZone.addEventListener('drop', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    uploadZone.style.opacity = '1';

                    const files = e.dataTransfer.files;
                    if (files.length > 0) {
                        if (files.length === 1) {
                            console.log('File dropped:', files[0].name);
                        } else {
                            console.log(`${files.length} files dropped:`, Array.from(files).map(f => f.name));
                        }
                        UI.handleFileUpload(files);
                    }
                });
            }
        } else {
            console.error('CRITICAL: Upload elements not found!');
            console.error('uploadBtn:', uploadBtn);
            console.error('fileInput:', fileInput);
        }

        // Clear all button
        const clearBtn = document.getElementById('clear-all-btn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                UI.confirmClearAll();
            });
        }

        // Cross-document clustering button
        const clusteringBtn = document.getElementById('run-clustering-btn');
        const clusteringStatus = document.getElementById('clustering-status');
        if (clusteringBtn) {
            clusteringBtn.addEventListener('click', async () => {
                try {
                    clusteringBtn.disabled = true;
                    clusteringBtn.textContent = '⏳ Clustering...';
                    if (clusteringStatus) {
                        clusteringStatus.style.display = 'block';
                        clusteringStatus.textContent = 'Running Leiden algorithm across all documents...';
                    }

                    const response = await fetch('/api/run-cross-document-clustering', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' }
                    });

                    if (response.ok) {
                        const data = await response.json();
                        if (clusteringStatus) {
                            clusteringStatus.textContent = `✓ Created ${data.super_claims || 0} super-claims from ${data.clusters || 0} communities (modularity: ${(data.modularity || 0).toFixed(3)})`;
                        }
                        // Refresh the graph to show new super-claims
                        await App.loadGraph();
                    } else {
                        throw new Error('Clustering failed');
                    }
                } catch (error) {
                    console.error('Clustering error:', error);
                    if (clusteringStatus) {
                        clusteringStatus.textContent = '❌ Clustering failed. Check console for details.';
                    }
                } finally {
                    clusteringBtn.disabled = false;
                    clusteringBtn.textContent = '🚀 Run Clustering';
                }
            });
        }

        // Agent launcher search depth slider
        const depthSlider = document.getElementById('search-depth');
        const depthValue = document.getElementById('depth-value');
        if (depthSlider && depthValue) {
            depthSlider.addEventListener('input', (e) => {
                depthValue.textContent = e.target.value;
            });
        }

        // Search and filter event listeners
        const searchInput = document.getElementById('search-input');
        const searchResultsCount = document.getElementById('search-results-count');
        if (searchInput && searchResultsCount) {
            // Debounced search
            let searchTimeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    const query = e.target.value;
                    const results = GraphRenderer.searchNodes(query);
                    if (query) {
                        searchResultsCount.textContent = `${results.matches} of ${results.total} nodes match`;
                    } else {
                        searchResultsCount.textContent = '';
                    }
                }, 300);
            });
        }

        // Filter checkboxes
        const filterDocs = document.getElementById('filter-documents');
        const filterClaims = document.getElementById('filter-claims');
        const filterDuplicates = document.getElementById('filter-duplicates');

        if (filterDocs) {
            filterDocs.addEventListener('change', (e) => {
                GraphRenderer.updateFilters({ documents: e.target.checked });
            });
        }
        if (filterClaims) {
            filterClaims.addEventListener('change', (e) => {
                GraphRenderer.updateFilters({ claims: e.target.checked });
            });
        }
        if (filterDuplicates) {
            filterDuplicates.addEventListener('change', (e) => {
                GraphRenderer.updateFilters({ duplicates: e.target.checked });
            });
        }

        // Quality filter slider
        const qualityFilter = document.getElementById('quality-filter');
        const qualityFilterValue = document.getElementById('quality-filter-value');
        if (qualityFilter && qualityFilterValue) {
            qualityFilter.addEventListener('input', (e) => {
                const value = parseInt(e.target.value);
                qualityFilterValue.textContent = `${value}%`;
                GraphRenderer.updateFilters({ minQuality: value });
            });
        }

        // Clear filters button
        const clearFiltersBtn = document.getElementById('clear-filters-btn');
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', () => {
                // Reset UI elements
                if (searchInput) searchInput.value = '';
                if (searchResultsCount) searchResultsCount.textContent = '';
                if (filterDocs) filterDocs.checked = true;
                if (filterClaims) filterClaims.checked = true;
                if (filterDuplicates) filterDuplicates.checked = true;
                if (qualityFilter) qualityFilter.value = 0;
                if (qualityFilterValue) qualityFilterValue.textContent = '0%';

                // Clear filters in graph renderer
                GraphRenderer.clearFilters();
            });
        }

        // Focus search results button
        const focusSearchBtn = document.getElementById('focus-search-btn');
        if (focusSearchBtn) {
            focusSearchBtn.addEventListener('click', () => {
                GraphRenderer.focusFilteredNodes();
            });
        }

        console.log('✓ Event listeners setup complete');
    },

    /**
     * Toggle agent launcher panel
     */
    toggleAgentLauncher() {
        const launcher = document.getElementById('agent-launcher');
        const toggle = document.getElementById('launcher-toggle');

        if (launcher && toggle) {
            launcher.classList.toggle('collapsed');
            toggle.textContent = launcher.classList.contains('collapsed') ? '▲' : '▼';
        }
    },

    /**
     * Quick investigate current selected claim
     */
    async quickInvestigate() {
        if (!GraphRenderer.selectedNodeId) {
            alert('Please select a claim node first');
            return;
        }

        const agentType = document.getElementById('agent-type')?.value || 'arxiv_search';
        console.log('Quick investigate:', GraphRenderer.selectedNodeId, 'with agent:', agentType);

        try {
            const result = await API.investigateClaim(GraphRenderer.selectedNodeId, 'support');
            alert(`Investigation started: ${result.agent}`);
            this.loadGraph();
        } catch (error) {
            console.error('Investigation failed:', error);
            alert(`Failed to start investigation: ${error.message}`);
        }
    },

    /**
     * Custom investigate with full options
     */
    async customInvestigate() {
        if (!GraphRenderer.selectedNodeId) {
            alert('Please select a claim node first');
            return;
        }

        const agentType = document.getElementById('agent-type')?.value || 'arxiv_search';
        const searchDepth = document.getElementById('search-depth')?.value || 3;
        const searchStrategy = document.getElementById('search-strategy')?.value || 'breadth-first';
        const customPrompt = document.getElementById('custom-prompt')?.value || '';

        console.log('Custom investigate:', {
            claimId: GraphRenderer.selectedNodeId,
            agentType,
            searchDepth,
            searchStrategy,
            customPrompt
        });

        try {
            // TODO: API doesn't support these parameters yet, using simple investigation
            const result = await API.investigateClaim(GraphRenderer.selectedNodeId, 'support');
            alert(`Investigation started with ${agentType}\nDepth: ${searchDepth}\nStrategy: ${searchStrategy}`);
            this.loadGraph();
        } catch (error) {
            console.error('Investigation failed:', error);
            alert(`Failed to start investigation: ${error.message}`);
        }
    },

    /**
     * Handle upload via drag-and-drop
     */
    setupDragAndDrop() {
        const dropZone = document.getElementById('graph-svg');

        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.style.opacity = '0.7';
        });

        dropZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.style.opacity = '1';
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.style.opacity = '1';

            const files = e.dataTransfer.files;
            if (files.length > 0) {
                UI.handleFileUpload(files[0]);
            }
        });
    }
};

// Make functions globally accessible for inline onclick handlers
window.toggleLauncher = () => App.toggleAgentLauncher();
window.quickInvestigate = () => App.quickInvestigate();
window.customInvestigate = () => App.customInvestigate();

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
