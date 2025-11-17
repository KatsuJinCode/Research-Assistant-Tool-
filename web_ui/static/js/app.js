/**
 * Main Application - Coordinates all modules and handles initialization
 */

const App = {
    socket: null,
    processingInProgress: false,  // Track if document processing is ongoing

    /**
     * Initialize the application
     */
    async init() {
        console.log('Initializing Research Graph Interface...');

        // Setup Socket.IO for real-time updates
        this.initializeSocket();

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

            // Handle different events from the nested data.data.event field
            if (data.data && data.data.event === 'document_created') {
                // Document node created - add incrementally with processing indicator
                console.log('Document created:', data.data.doc_id);
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
                    GraphRenderer.addNodeIncremental(nodeData, null);
                }
            } else if (data.data && data.data.event === 'super_claim_added') {
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
            } else if (data.data && data.data.event === 'claim_added') {
                // Sub-claim added - add incrementally with link to parent
                console.log('Claim added:', data.data.claim_id);
                if (data.data.node_data) {
                    const nodeData = {
                        id: data.data.node_data.id,
                        label: data.data.node_data.summary || data.data.node_data.text?.substring(0, 40) || 'Claim',
                        type: 'sub',
                        fullData: data.data.node_data,
                        fresh: true  // Mark as fresh/newly added
                    };
                    const parentId = data.data.node_data.parent_super_claim || data.data.doc_id;
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
            } else if (data.data && (data.data.event === 'claim_extraction_failed' ||
                       data.data.event === 'claim_simplification_failed')) {
                // Display error prominently
                console.error('AI Agent failure:', data.data.error);
                this.processingInProgress = false;
                alert('AI AGENT FAILURE\n\n' + data.data.error + '\n\nCheck that your AI agent CLI is installed and configured properly.\nSee AGENT_CONFIGURATION.md for setup instructions.');
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

            // File upload handler
            fileInput.addEventListener('change', (e) => {
                console.log('File selected:', e.target.files);
                const file = e.target.files[0];
                if (file) {
                    console.log('Processing file:', file.name);
                    UI.handleFileUpload(file);
                    // Reset input so same file can be uploaded again
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
                        console.log('File dropped:', files[0].name);
                        UI.handleFileUpload(files[0]);
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

        // Agent launcher search depth slider
        const depthSlider = document.getElementById('search-depth');
        const depthValue = document.getElementById('depth-value');
        if (depthSlider && depthValue) {
            depthSlider.addEventListener('input', (e) => {
                depthValue.textContent = e.target.value;
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
