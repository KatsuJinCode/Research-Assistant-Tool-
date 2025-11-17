/**
 * Main Application - Coordinates all modules and handles initialization
 */

const App = {
    socket: null,

    /**
     * Initialize the application
     */
    async init() {
        console.log('Initializing Research Graph Interface...');

        // Setup Socket.IO for real-time updates
        this.initializeSocket();

        // Load initial data
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
            UI.updateProcessingStatus(data.message, data.progress);
        });

        this.socket.on('claim_added', (data) => {
            console.log('New claim added:', data.claim_summary);
            // Reload graph to show new claim
            this.loadGraph();
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
        // Upload button
        document.getElementById('upload-btn').addEventListener('click', () => {
            UI.showUploadModal();
        });

        // File upload
        document.getElementById('file-upload').addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                UI.handleFileUpload(file);
            }
        });

        // Clear all button
        document.getElementById('clear-all-btn').addEventListener('click', () => {
            UI.confirmClearAll();
        });

        // Close modal buttons
        document.querySelectorAll('.close-modal').forEach(btn => {
            btn.addEventListener('click', () => {
                UI.closeClaimModal();
                UI.hideUploadModal();
            });
        });

        // Click outside modal to close
        window.addEventListener('click', (event) => {
            const claimModal = document.getElementById('claim-modal');
            const uploadModal = document.getElementById('upload-modal');

            if (event.target === claimModal) {
                UI.closeClaimModal();
            }
            if (event.target === uploadModal) {
                UI.hideUploadModal();
            }
        });

        console.log('✓ Event listeners setup');
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

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
