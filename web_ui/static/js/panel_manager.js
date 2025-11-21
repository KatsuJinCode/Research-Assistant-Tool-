/**
 * Panel Manager Module - Draggable Panel System
 *
 * Handles:
 * - Horizontal divider (resize left panel width vs graph area)
 * - Vertical divider (resize tab content vs AI assistant)
 * - Panel size constraints (min/max)
 * - Size persistence in localStorage
 */

const PanelManager = {
    // Panel size state
    leftPanelWidth: 350,
    aiPanelHeight: 250,

    // Dragging state
    isDraggingHorizontal: false,
    isDraggingVertical: false,

    // Min/max constraints
    constraints: {
        leftPanel: { min: 250, max: 600 },
        aiPanel: { min: 150, max: 500 }
    },

    /**
     * Initialize panel manager
     */
    init() {
        console.log('[PanelManager] Initializing draggable panel system...');

        // Load saved panel sizes
        this.loadPanelSizes();

        // Apply initial sizes
        this.applyPanelSizes();

        // Setup draggable dividers
        this.setupHorizontalDivider();
        this.setupVerticalDivider();

        console.log('[PanelManager] ✓ Panel manager initialized');
    },

    /**
     * Setup horizontal divider (resize left panel width)
     */
    setupHorizontalDivider() {
        const divider = document.getElementById('horizontal-divider');
        if (!divider) {
            console.warn('[PanelManager] Horizontal divider not found');
            return;
        }

        divider.addEventListener('mousedown', (e) => {
            this.isDraggingHorizontal = true;
            document.body.style.cursor = 'ew-resize';
            document.body.style.userSelect = 'none';
            e.preventDefault();
        });

        document.addEventListener('mousemove', (e) => {
            if (!this.isDraggingHorizontal) return;

            const newWidth = e.clientX;

            // Apply constraints
            if (newWidth >= this.constraints.leftPanel.min &&
                newWidth <= this.constraints.leftPanel.max) {
                this.leftPanelWidth = newWidth;
                this.applyPanelSizes();
            }
        });

        document.addEventListener('mouseup', () => {
            if (this.isDraggingHorizontal) {
                this.isDraggingHorizontal = false;
                document.body.style.cursor = '';
                document.body.style.userSelect = '';
                this.savePanelSizes();
            }
        });
    },

    /**
     * Setup vertical divider (resize tab content vs AI assistant)
     */
    setupVerticalDivider() {
        const divider = document.getElementById('vertical-divider');
        if (!divider) {
            console.warn('[PanelManager] Vertical divider not found');
            return;
        }

        divider.addEventListener('mousedown', (e) => {
            this.isDraggingVertical = true;
            document.body.style.cursor = 'ns-resize';
            document.body.style.userSelect = 'none';
            e.preventDefault();
        });

        document.addEventListener('mousemove', (e) => {
            if (!this.isDraggingVertical) return;

            const sidebar = document.getElementById('sidebar');
            if (!sidebar) return;

            const sidebarRect = sidebar.getBoundingClientRect();
            const relativeY = e.clientY - sidebarRect.top;

            // Calculate new AI panel height (from bottom)
            const newAiHeight = sidebarRect.height - relativeY;

            // Apply constraints
            if (newAiHeight >= this.constraints.aiPanel.min &&
                newAiHeight <= this.constraints.aiPanel.max) {
                this.aiPanelHeight = newAiHeight;
                this.applyPanelSizes();
            }
        });

        document.addEventListener('mouseup', () => {
            if (this.isDraggingVertical) {
                this.isDraggingVertical = false;
                document.body.style.cursor = '';
                document.body.style.userSelect = '';
                this.savePanelSizes();
            }
        });
    },

    /**
     * Apply panel sizes to DOM
     */
    applyPanelSizes() {
        // Apply left panel width
        const sidebar = document.getElementById('sidebar');
        if (sidebar) {
            sidebar.style.width = `${this.leftPanelWidth}px`;
        }

        // Apply AI panel height using flex-basis
        const aiPanel = document.getElementById('ai-assistant-panel');
        const contentArea = document.getElementById('tab-content-area');

        if (aiPanel && contentArea) {
            // Calculate flex values based on AI panel height
            const sidebar = document.getElementById('sidebar');
            if (sidebar) {
                const totalHeight = sidebar.clientHeight;
                const contentHeight = totalHeight - this.aiPanelHeight - 4; // 4px for divider

                aiPanel.style.flexBasis = `${this.aiPanelHeight}px`;
                aiPanel.style.flexGrow = '0';
                aiPanel.style.flexShrink = '0';

                contentArea.style.flexBasis = `${contentHeight}px`;
                contentArea.style.flexGrow = '1';
                contentArea.style.flexShrink = '1';
            }
        }
    },

    /**
     * Save panel sizes to localStorage
     */
    savePanelSizes() {
        try {
            localStorage.setItem('leftPanelWidth', this.leftPanelWidth.toString());
            localStorage.setItem('aiPanelHeight', this.aiPanelHeight.toString());
            console.log('[PanelManager] Panel sizes saved');
        } catch (e) {
            console.warn('[PanelManager] Failed to save panel sizes:', e);
        }
    },

    /**
     * Load panel sizes from localStorage
     */
    loadPanelSizes() {
        try {
            const savedLeftWidth = localStorage.getItem('leftPanelWidth');
            const savedAiHeight = localStorage.getItem('aiPanelHeight');

            if (savedLeftWidth) {
                const width = parseInt(savedLeftWidth);
                if (width >= this.constraints.leftPanel.min &&
                    width <= this.constraints.leftPanel.max) {
                    this.leftPanelWidth = width;
                }
            }

            if (savedAiHeight) {
                const height = parseInt(savedAiHeight);
                if (height >= this.constraints.aiPanel.min &&
                    height <= this.constraints.aiPanel.max) {
                    this.aiPanelHeight = height;
                }
            }

            console.log('[PanelManager] Panel sizes loaded');
        } catch (e) {
            console.warn('[PanelManager] Failed to load panel sizes:', e);
        }
    },

    /**
     * Reset panel sizes to defaults
     */
    resetPanelSizes() {
        this.leftPanelWidth = 350;
        this.aiPanelHeight = 250;
        this.applyPanelSizes();
        this.savePanelSizes();
        console.log('[PanelManager] Panel sizes reset to defaults');
    },

    /**
     * Collapse/expand left panel
     */
    toggleLeftPanel() {
        const sidebar = document.getElementById('sidebar');
        if (!sidebar) return;

        if (sidebar.style.display === 'none') {
            sidebar.style.display = 'flex';
            this.applyPanelSizes();
        } else {
            sidebar.style.display = 'none';
        }
    },

    /**
     * Collapse/expand AI panel
     */
    toggleAIPanel() {
        const aiPanel = document.getElementById('ai-assistant-panel');
        const divider = document.getElementById('vertical-divider');

        if (!aiPanel || !divider) return;

        if (aiPanel.style.display === 'none') {
            aiPanel.style.display = 'flex';
            divider.style.display = 'block';
            this.applyPanelSizes();
        } else {
            aiPanel.style.display = 'none';
            divider.style.display = 'none';
        }
    },

    /**
     * Get current panel configuration
     */
    getPanelConfig() {
        return {
            leftPanelWidth: this.leftPanelWidth,
            aiPanelHeight: this.aiPanelHeight,
            constraints: this.constraints
        };
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        PanelManager.init();
    }, 200);
});
