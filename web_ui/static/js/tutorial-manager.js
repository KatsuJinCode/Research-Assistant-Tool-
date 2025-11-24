/**
 * Tutorial Manager - Interactive Tutorial System
 * Guides first-time users through key features with an interactive wizard
 */

class TutorialManager {
    // State management
    static currentStep = 0;
    static totalSteps = 8;
    static isActive = false;
    static tutorialData = {};
    static validationTimeout = null;

    // LocalStorage keys
    static TUTORIAL_COMPLETED = 'tutorial_completed';
    static TUTORIAL_SKIPPED = 'tutorial_skipped';
    static TUTORIAL_CURRENT_STEP = 'tutorial_current_step';
    static FIRST_VISIT = 'first_visit';

    /**
     * Tutorial step definitions
     */
    static steps = [
        {
            // Step 1: Welcome
            title: 'Welcome to Research Assistant!',
            content: `
                <div style="text-align: center; padding: 20px 0;">
                    <div style="font-size: 48px; margin-bottom: 20px;">👋</div>
                    <p style="font-size: 16px; margin-bottom: 15px;">
                        Welcome! This tool helps you analyze research documents, extract claims,
                        and visualize connections in your research.
                    </p>
                    <p style="font-size: 14px; color: #999; margin-bottom: 20px;">
                        Let's take a quick tour of the key features. This will take about 2 minutes.
                    </p>
                    <div style="display: flex; gap: 10px; justify-content: center; margin-top: 20px;">
                        <button class="tutorial-btn" onclick="TutorialManager.nextStep()">Start Tour</button>
                        <button class="tutorial-btn tutorial-btn-secondary" onclick="TutorialManager.skip()">Skip</button>
                    </div>
                </div>
            `,
            target: null,
            position: 'center',
            requireAction: false
        },
        {
            // Step 2: Upload Document
            title: 'Upload Your First Document',
            content: `
                <p style="margin-bottom: 15px;">
                    Start by uploading a research document. We support PDF, DOCX, and TXT files.
                </p>
                <p style="font-size: 13px; color: #999; margin-bottom: 15px;">
                    <strong>Try it:</strong> Click the upload zone or drag & drop a file to continue.
                </p>
                <p style="font-size: 12px; color: #666;">
                    💡 Tip: You can upload multiple documents to analyze connections between them.
                </p>
            `,
            target: '#upload-zone',
            position: 'bottom',
            requireAction: true,
            validation: () => {
                // Check if at least one document exists
                const stats = document.getElementById('stat-nodes');
                return stats && parseInt(stats.textContent) > 0;
            }
        },
        {
            // Step 3: View Graph
            title: 'Explore the Knowledge Graph',
            content: `
                <p style="margin-bottom: 15px;">
                    Your research is visualized as an interactive graph:
                </p>
                <ul style="font-size: 13px; line-height: 1.8; margin-left: 20px; margin-bottom: 15px;">
                    <li><span style="color: #9C27B0;">●</span> <strong>Purple nodes</strong> = Documents</li>
                    <li><span style="color: #2196F3;">●</span> <strong>Blue nodes</strong> = Claims extracted from documents</li>
                </ul>
                <p style="font-size: 13px; color: #999; margin-bottom: 10px;">
                    You can zoom with mouse wheel and pan by dragging the background.
                </p>
                <p style="font-size: 12px; color: #666;">
                    💡 Tip: The graph uses a force-directed layout - nodes push apart while connections pull together.
                </p>
            `,
            target: '#graph-container',
            position: 'right',
            requireAction: false
        },
        {
            // Step 4: Interact with Nodes
            title: 'Click Nodes to View Details',
            content: `
                <p style="margin-bottom: 15px;">
                    Click any node to view its full details in the property panel.
                </p>
                <p style="font-size: 13px; color: #999; margin-bottom: 15px;">
                    <strong>Try it:</strong> Click on any node in the graph to continue.
                </p>
                <p style="font-size: 12px; color: #666;">
                    💡 Tip: For claims, you'll see confidence scores, evidence, and AI-generated summaries.
                </p>
            `,
            target: '#graph-container',
            position: 'right',
            requireAction: true,
            validation: () => {
                // Check if property viewer is visible
                const panel = document.querySelector('.property-viewer-panel');
                return panel && panel.style.display !== 'none';
            }
        },
        {
            // Step 5: Use AI Assistant
            title: 'Ask Questions with AI',
            content: `
                <p style="margin-bottom: 15px;">
                    The AI Assistant can help you understand your research better.
                </p>
                <ul style="font-size: 13px; line-height: 1.8; margin-left: 20px; margin-bottom: 15px;">
                    <li>Ask questions about your documents</li>
                    <li>Get summaries of key claims</li>
                    <li>Find connections between concepts</li>
                    <li>Generate research insights</li>
                </ul>
                <p style="font-size: 12px; color: #666;">
                    💡 Tip: Try asking "What are the main claims in my research?"
                </p>
            `,
            target: '.ai-assistant-panel',
            position: 'left',
            requireAction: false
        },
        {
            // Step 6: Explore Search
            title: 'Search Your Knowledge Base',
            content: `
                <p style="margin-bottom: 15px;">
                    Use the Search tab to find specific information across all your documents.
                </p>
                <ul style="font-size: 13px; line-height: 1.8; margin-left: 20px; margin-bottom: 15px;">
                    <li>Search by keywords</li>
                    <li>Filter by document type</li>
                    <li>Filter by confidence score</li>
                    <li>Hide duplicate claims</li>
                </ul>
                <p style="font-size: 12px; color: #666;">
                    💡 Tip: Use the "Focus Search Results" button to zoom in on matching nodes.
                </p>
            `,
            target: '[data-tab="search"]',
            position: 'bottom',
            requireAction: false
        },
        {
            // Step 7: View Projects
            title: 'Organize with Projects',
            content: `
                <p style="margin-bottom: 15px;">
                    Projects help you organize different research topics or themes.
                </p>
                <ul style="font-size: 13px; line-height: 1.8; margin-left: 20px; margin-bottom: 15px;">
                    <li>Create separate projects for different topics</li>
                    <li>Switch between projects easily</li>
                    <li>Each project has its own graph and documents</li>
                </ul>
                <p style="font-size: 12px; color: #666;">
                    💡 Tip: Use the project selector in the header to switch projects.
                </p>
            `,
            target: '.project-selector',
            position: 'bottom',
            requireAction: false
        },
        {
            // Step 8: Complete
            title: 'You\'re All Set! 🎉',
            content: `
                <div style="text-align: center; padding: 20px 0;">
                    <div style="font-size: 48px; margin-bottom: 20px;">✅</div>
                    <p style="font-size: 16px; margin-bottom: 15px;">
                        <strong>Congratulations!</strong> You've completed the tutorial.
                    </p>
                    <p style="font-size: 14px; color: #999; margin-bottom: 20px;">
                        Here's a quick recap of what you can do:
                    </p>
                    <ul style="text-align: left; font-size: 13px; line-height: 1.8; margin-left: 40px; margin-bottom: 20px;">
                        <li>📄 Upload documents (PDF, DOCX, TXT)</li>
                        <li>🔍 Explore the interactive knowledge graph</li>
                        <li>💡 View detailed claim information</li>
                        <li>🤖 Ask AI questions about your research</li>
                        <li>🔎 Search and filter your knowledge base</li>
                        <li>📁 Organize with projects</li>
                    </ul>
                    <p style="font-size: 12px; color: #666; margin-bottom: 20px;">
                        You can restart this tutorial anytime by clicking the Help button (?) in the header.
                    </p>
                    <button class="tutorial-btn" onclick="TutorialManager.end()">Get Started!</button>
                </div>
            `,
            target: null,
            position: 'center',
            requireAction: false
        }
    ];

    /**
     * Context-sensitive help content
     */
    static contextHelp = {
        'upload': {
            title: 'Uploading Documents',
            content: `
                <p style="margin-bottom: 15px;">There are three ways to add content:</p>
                <ol style="font-size: 13px; line-height: 1.8; margin-left: 20px; margin-bottom: 15px;">
                    <li><strong>Upload Files:</strong> Click the upload zone or drag & drop PDF, DOCX, or TXT files</li>
                    <li><strong>Add URL:</strong> Paste a URL to extract content from a webpage</li>
                    <li><strong>Manual Claim:</strong> Enter a claim directly for analysis</li>
                </ol>
                <p style="font-size: 12px; color: #666;">
                    💡 The system will automatically extract claims and analyze connections.
                </p>
            `
        },
        'search': {
            title: 'Searching Your Research',
            content: `
                <p style="margin-bottom: 15px;">Use advanced search features to find what you need:</p>
                <ul style="font-size: 13px; line-height: 1.8; margin-left: 20px; margin-bottom: 15px;">
                    <li><strong>Keyword Search:</strong> Enter any text to search across all content</li>
                    <li><strong>Type Filters:</strong> Show/hide documents, claims, or duplicates</li>
                    <li><strong>Quality Filter:</strong> Filter claims by confidence score</li>
                    <li><strong>Focus Results:</strong> Zoom the graph to show only matching nodes</li>
                </ul>
                <p style="font-size: 12px; color: #666;">
                    💡 Search results are highlighted in the graph with a glow effect.
                </p>
            `
        },
        'projects': {
            title: 'Managing Projects',
            content: `
                <p style="margin-bottom: 15px;">Projects keep your research organized:</p>
                <ul style="font-size: 13px; line-height: 1.8; margin-left: 20px; margin-bottom: 15px;">
                    <li><strong>Create Project:</strong> Use the Projects tab to create a new project</li>
                    <li><strong>Switch Projects:</strong> Click the project selector in the header</li>
                    <li><strong>Isolated Data:</strong> Each project has its own documents and graph</li>
                </ul>
                <p style="font-size: 12px; color: #666;">
                    💡 Great for separating different research topics or time periods.
                </p>
            `
        },
        'graph': {
            title: 'Understanding the Graph',
            content: `
                <p style="margin-bottom: 15px;">The knowledge graph shows relationships in your research:</p>
                <ul style="font-size: 13px; line-height: 1.8; margin-left: 20px; margin-bottom: 15px;">
                    <li><strong>Navigation:</strong> Zoom with mouse wheel, pan by dragging</li>
                    <li><strong>Node Types:</strong> Purple = documents, Blue = claims</li>
                    <li><strong>Connections:</strong> Lines show claim-to-document relationships</li>
                    <li><strong>Duplicates:</strong> Orange dashed lines indicate similar claims</li>
                </ul>
                <p style="font-size: 12px; color: #666;">
                    💡 The layout automatically organizes nodes to minimize visual clutter.
                </p>
            `
        },
        'ai': {
            title: 'Using the AI Assistant',
            content: `
                <p style="margin-bottom: 15px;">The AI Assistant provides intelligent insights:</p>
                <ul style="font-size: 13px; line-height: 1.8; margin-left: 20px; margin-bottom: 15px;">
                    <li><strong>Quick Actions:</strong> Use preset buttons for common tasks</li>
                    <li><strong>Custom Questions:</strong> Ask anything about your research</li>
                    <li><strong>Context-Aware:</strong> If a node is selected, AI focuses on it</li>
                </ul>
                <p style="font-size: 12px; color: #666;">
                    💡 Try: "Compare the claims in different documents" or "What's the strongest evidence?"
                </p>
            `
        }
    };

    /**
     * Initialize the tutorial system
     */
    static init() {
        console.log('[Tutorial] Initializing tutorial system');

        // Create tutorial overlay if it doesn't exist
        this.createOverlay();

        // Setup keyboard shortcuts
        this.setupKeyboardShortcuts();

        // Check for first visit
        if (!localStorage.getItem(this.FIRST_VISIT)) {
            console.log('[Tutorial] First visit detected - showing tutorial after delay');
            // Show tutorial after a short delay to let the page load
            setTimeout(() => {
                this.start();
                localStorage.setItem(this.FIRST_VISIT, 'true');
            }, 1500);
        } else {
            // Check if tutorial was in progress
            const inProgress = localStorage.getItem(this.TUTORIAL_CURRENT_STEP);
            const completed = localStorage.getItem(this.TUTORIAL_COMPLETED);
            const skipped = localStorage.getItem(this.TUTORIAL_SKIPPED);

            if (inProgress && !completed && !skipped) {
                console.log('[Tutorial] Tutorial in progress - showing resume option');
                this.showResumePrompt();
            }
        }

        console.log('[Tutorial] Tutorial system ready');
    }

    /**
     * Create the tutorial overlay HTML
     */
    static createOverlay() {
        // Check if overlay already exists
        if (document.getElementById('tutorial-overlay')) {
            return;
        }

        const overlay = document.createElement('div');
        overlay.id = 'tutorial-overlay';
        overlay.style.display = 'none';
        overlay.innerHTML = `
            <div class="tutorial-backdrop"></div>
            <div class="tutorial-spotlight" id="tutorial-spotlight"></div>
            <div class="tutorial-panel" id="tutorial-panel">
                <div class="tutorial-header">
                    <span class="tutorial-title" id="tutorial-title"></span>
                    <button class="tutorial-close" onclick="TutorialManager.skip()">×</button>
                </div>
                <div class="tutorial-content" id="tutorial-content"></div>
                <div class="tutorial-footer">
                    <span class="tutorial-progress" id="tutorial-progress">Step 1 of ${this.totalSteps}</span>
                    <div class="tutorial-buttons">
                        <button class="tutorial-btn tutorial-btn-secondary" id="tutorial-prev-btn" onclick="TutorialManager.previousStep()">Previous</button>
                        <button class="tutorial-btn tutorial-btn-secondary" id="tutorial-skip-btn" onclick="TutorialManager.skip()">Skip Tour</button>
                        <button class="tutorial-btn" id="tutorial-next-btn" onclick="TutorialManager.nextStep()">Next</button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);
    }

    /**
     * Check if this is the first visit
     */
    static checkFirstVisit() {
        return !localStorage.getItem(this.FIRST_VISIT);
    }

    /**
     * Start the tutorial from beginning
     */
    static start() {
        console.log('[Tutorial] Starting tutorial');
        this.currentStep = 0;
        this.isActive = true;
        this.show();
        this.showStep(0);
    }

    /**
     * Resume from saved step
     */
    static resume() {
        const step = parseInt(localStorage.getItem(this.TUTORIAL_CURRENT_STEP)) || 0;
        console.log('[Tutorial] Resuming from step', step);
        this.currentStep = step;
        this.isActive = true;
        this.show();
        this.showStep(step);
    }

    /**
     * Show resume prompt
     */
    static showResumePrompt() {
        const step = parseInt(localStorage.getItem(this.TUTORIAL_CURRENT_STEP)) || 0;

        // Create a simple notification
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            background: #2a2a2a;
            border: 2px solid #2196F3;
            border-radius: 8px;
            padding: 20px;
            max-width: 350px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
            z-index: 9999;
            animation: slideIn 0.3s ease;
        `;

        notification.innerHTML = `
            <div style="font-size: 14px; font-weight: 600; margin-bottom: 10px;">
                Continue Tutorial?
            </div>
            <div style="font-size: 13px; color: #999; margin-bottom: 15px;">
                You were on step ${step + 1} of ${this.totalSteps}. Would you like to continue?
            </div>
            <div style="display: flex; gap: 10px;">
                <button class="tutorial-btn" onclick="TutorialManager.resume(); this.parentElement.parentElement.remove();">
                    Continue
                </button>
                <button class="tutorial-btn tutorial-btn-secondary" onclick="this.parentElement.parentElement.remove();">
                    Not Now
                </button>
            </div>
        `;

        document.body.appendChild(notification);

        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 10000);
    }

    /**
     * Skip tutorial
     */
    static skip() {
        const confirmed = confirm('Skip tutorial? You can restart it anytime from the Help menu.');
        if (confirmed) {
            console.log('[Tutorial] Tutorial skipped');
            localStorage.setItem(this.TUTORIAL_SKIPPED, 'true');
            localStorage.removeItem(this.TUTORIAL_CURRENT_STEP);
            this.hide();
        }
    }

    /**
     * Move to next step
     */
    static nextStep() {
        const step = this.steps[this.currentStep];

        // Validate if action is required
        if (step.requireAction && step.validation) {
            if (!step.validation()) {
                this.showValidationMessage();
                return;
            }
        }

        // Move to next step
        if (this.currentStep < this.totalSteps - 1) {
            this.currentStep++;
            this.showStep(this.currentStep);
            this.saveTutorialState();
        } else {
            this.end();
        }
    }

    /**
     * Go back one step
     */
    static previousStep() {
        if (this.currentStep > 0) {
            this.currentStep--;
            this.showStep(this.currentStep);
            this.saveTutorialState();
        }
    }

    /**
     * Jump to specific step
     */
    static goToStep(n) {
        if (n >= 0 && n < this.totalSteps) {
            this.currentStep = n;
            this.showStep(n);
            this.saveTutorialState();
        }
    }

    /**
     * End tutorial
     */
    static end() {
        console.log('[Tutorial] Tutorial completed');
        localStorage.setItem(this.TUTORIAL_COMPLETED, 'true');
        localStorage.removeItem(this.TUTORIAL_CURRENT_STEP);
        this.hide();

        // Show completion notification
        if (window.UI && window.UI.showNotification) {
            window.UI.showNotification('Tutorial completed! You can restart it anytime from the Help menu.', 'success', 5000);
        }
    }

    /**
     * Reset tutorial state
     */
    static reset() {
        localStorage.removeItem(this.TUTORIAL_COMPLETED);
        localStorage.removeItem(this.TUTORIAL_SKIPPED);
        localStorage.removeItem(this.TUTORIAL_CURRENT_STEP);
        this.currentStep = 0;
        console.log('[Tutorial] Tutorial state reset');
    }

    /**
     * Show tutorial overlay
     */
    static show() {
        const overlay = document.getElementById('tutorial-overlay');
        if (overlay) {
            overlay.style.display = 'block';
            this.isActive = true;
        }
    }

    /**
     * Hide tutorial overlay
     */
    static hide() {
        const overlay = document.getElementById('tutorial-overlay');
        if (overlay) {
            overlay.style.display = 'none';
            this.isActive = false;
        }
    }

    /**
     * Show a specific step
     */
    static showStep(stepNumber) {
        if (stepNumber < 0 || stepNumber >= this.totalSteps) {
            return;
        }

        const step = this.steps[stepNumber];

        // Update content
        document.getElementById('tutorial-title').textContent = step.title;
        document.getElementById('tutorial-content').innerHTML = step.content;
        document.getElementById('tutorial-progress').textContent = `Step ${stepNumber + 1} of ${this.totalSteps}`;

        // Update buttons
        const prevBtn = document.getElementById('tutorial-prev-btn');
        const nextBtn = document.getElementById('tutorial-next-btn');

        prevBtn.style.display = stepNumber > 0 ? 'inline-block' : 'none';

        if (stepNumber === this.totalSteps - 1) {
            nextBtn.textContent = 'Finish';
        } else {
            nextBtn.textContent = 'Next';
        }

        // Position spotlight and panel
        if (step.target) {
            this.highlightElement(step.target);
            this.positionPanel(step.position || 'auto');
        } else {
            // No target - center the panel
            this.hideSpotlight();
            this.centerPanel();
        }

        // Handle backdrop pointer events
        const backdrop = document.querySelector('.tutorial-backdrop');
        if (backdrop) {
            if (stepNumber === 0 || stepNumber === this.totalSteps - 1) {
                // Welcome and completion screens - keep backdrop clickable to close
                backdrop.style.pointerEvents = 'all';
            } else if (step.target) {
                // When highlighting an element - allow clicks through backdrop
                backdrop.style.pointerEvents = 'none';
            } else {
                // No specific target - backdrop should block
                backdrop.style.pointerEvents = 'all';
            }
        }
    }

    /**
     * Highlight a target element with spotlight
     */
    static highlightElement(selector) {
        const element = document.querySelector(selector);
        if (!element) {
            console.warn('[Tutorial] Target element not found:', selector);
            this.hideSpotlight();
            return;
        }

        const rect = element.getBoundingClientRect();
        const spotlight = document.getElementById('tutorial-spotlight');

        if (spotlight) {
            spotlight.style.display = 'block';
            spotlight.style.top = (rect.top - 10) + 'px';
            spotlight.style.left = (rect.left - 10) + 'px';
            spotlight.style.width = (rect.width + 20) + 'px';
            spotlight.style.height = (rect.height + 20) + 'px';
            spotlight.classList.add('pulse');
        }
    }

    /**
     * Hide spotlight
     */
    static hideSpotlight() {
        const spotlight = document.getElementById('tutorial-spotlight');
        if (spotlight) {
            spotlight.style.display = 'none';
            spotlight.classList.remove('pulse');
        }
    }

    /**
     * Position the tutorial panel relative to spotlight or screen
     */
    static positionPanel(position = 'auto') {
        const panel = document.getElementById('tutorial-panel');
        const spotlight = document.getElementById('tutorial-spotlight');

        if (!panel) return;

        // Reset positioning
        panel.style.top = 'auto';
        panel.style.left = 'auto';
        panel.style.right = 'auto';
        panel.style.bottom = 'auto';
        panel.style.transform = 'none';

        if (position === 'center' || !spotlight || spotlight.style.display === 'none') {
            this.centerPanel();
            return;
        }

        const spotlightRect = spotlight.getBoundingClientRect();
        const panelRect = panel.getBoundingClientRect();
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;

        let top, left;

        if (position === 'auto') {
            // Calculate best position based on available space
            const spaceRight = viewportWidth - spotlightRect.right;
            const spaceLeft = spotlightRect.left;
            const spaceBottom = viewportHeight - spotlightRect.bottom;
            const spaceTop = spotlightRect.top;

            if (spaceRight > panelRect.width + 40) {
                position = 'right';
            } else if (spaceLeft > panelRect.width + 40) {
                position = 'left';
            } else if (spaceBottom > panelRect.height + 40) {
                position = 'bottom';
            } else if (spaceTop > panelRect.height + 40) {
                position = 'top';
            } else {
                position = 'center';
            }
        }

        switch (position) {
            case 'right':
                top = spotlightRect.top + (spotlightRect.height / 2) - (panelRect.height / 2);
                left = spotlightRect.right + 30;
                break;

            case 'left':
                top = spotlightRect.top + (spotlightRect.height / 2) - (panelRect.height / 2);
                left = spotlightRect.left - panelRect.width - 30;
                break;

            case 'bottom':
                top = spotlightRect.bottom + 30;
                left = spotlightRect.left + (spotlightRect.width / 2) - (panelRect.width / 2);
                break;

            case 'top':
                top = spotlightRect.top - panelRect.height - 30;
                left = spotlightRect.left + (spotlightRect.width / 2) - (panelRect.width / 2);
                break;

            default:
                this.centerPanel();
                return;
        }

        // Ensure panel stays within viewport
        top = Math.max(20, Math.min(top, viewportHeight - panelRect.height - 20));
        left = Math.max(20, Math.min(left, viewportWidth - panelRect.width - 20));

        panel.style.top = top + 'px';
        panel.style.left = left + 'px';
    }

    /**
     * Center the panel on screen
     */
    static centerPanel() {
        const panel = document.getElementById('tutorial-panel');
        if (panel) {
            panel.style.top = '50%';
            panel.style.left = '50%';
            panel.style.transform = 'translate(-50%, -50%)';
            panel.style.right = 'auto';
            panel.style.bottom = 'auto';
        }
    }

    /**
     * Show validation message
     */
    static showValidationMessage() {
        const content = document.getElementById('tutorial-content');
        if (!content) return;

        // Add a pulsing message
        const existingMsg = content.querySelector('.validation-message');
        if (existingMsg) {
            existingMsg.remove();
        }

        const msg = document.createElement('div');
        msg.className = 'validation-message';
        msg.style.cssText = `
            background: rgba(255, 152, 0, 0.2);
            border: 1px solid #FF9800;
            border-radius: 4px;
            padding: 10px;
            margin-top: 15px;
            font-size: 13px;
            color: #FF9800;
            animation: pulse 1s infinite;
        `;
        msg.textContent = '⚠ Please complete the action above to continue';

        content.appendChild(msg);

        // Remove after 3 seconds
        setTimeout(() => {
            if (msg.parentElement) {
                msg.remove();
            }
        }, 3000);
    }

    /**
     * Show context-sensitive help
     */
    static showContextHelp(context) {
        const helpData = this.contextHelp[context];
        if (!helpData) {
            console.warn('[Tutorial] No help content for context:', context);
            return;
        }

        this.showHelpModal(helpData);
    }

    /**
     * Show general help modal
     */
    static showHelpModal(data) {
        // Create modal
        const modal = document.createElement('div');
        modal.className = 'tutorial-help-modal';
        modal.style.cssText = `
            position: fixed;
            top: 0; left: 0;
            width: 100vw; height: 100vh;
            background: rgba(0, 0, 0, 0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10100;
            animation: fadeIn 0.2s ease;
        `;

        modal.innerHTML = `
            <div style="
                background: #2a2a2a;
                border: 2px solid #2196F3;
                border-radius: 12px;
                padding: 30px;
                max-width: 500px;
                width: 90%;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h3 style="margin: 0; color: #2196F3;">${data.title}</h3>
                    <button class="tutorial-close" onclick="this.closest('.tutorial-help-modal').remove()">×</button>
                </div>
                <div style="color: #e0e0e0;">
                    ${data.content}
                </div>
                <div style="margin-top: 20px; text-align: right;">
                    <button class="tutorial-btn" onclick="this.closest('.tutorial-help-modal').remove()">Got it!</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Close on backdrop click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    /**
     * Setup keyboard shortcuts
     */
    static setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (!this.isActive) return;

            switch (e.key) {
                case 'Escape':
                    this.skip();
                    break;
                case 'ArrowRight':
                case 'Enter':
                    if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
                        this.nextStep();
                        e.preventDefault();
                    }
                    break;
                case 'ArrowLeft':
                    if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
                        this.previousStep();
                        e.preventDefault();
                    }
                    break;
            }
        });
    }

    /**
     * Save tutorial progress
     */
    static saveTutorialState() {
        localStorage.setItem(this.TUTORIAL_CURRENT_STEP, this.currentStep.toString());
    }

    /**
     * Show help (restart tutorial or show help menu)
     */
    static showHelp() {
        // Create help menu modal
        const modal = document.createElement('div');
        modal.className = 'tutorial-help-modal';
        modal.style.cssText = `
            position: fixed;
            top: 0; left: 0;
            width: 100vw; height: 100vh;
            background: rgba(0, 0, 0, 0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10100;
            animation: fadeIn 0.2s ease;
        `;

        modal.innerHTML = `
            <div style="
                background: #2a2a2a;
                border: 2px solid #2196F3;
                border-radius: 12px;
                padding: 30px;
                max-width: 600px;
                width: 90%;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h3 style="margin: 0; color: #2196F3;">Help & Resources</h3>
                    <button class="tutorial-close" onclick="this.closest('.tutorial-help-modal').remove()">×</button>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px;">
                    <button class="tutorial-help-option" onclick="TutorialManager.restart(); this.closest('.tutorial-help-modal').remove();">
                        <div style="font-size: 24px; margin-bottom: 8px;">🎓</div>
                        <strong>Start Tutorial</strong>
                        <div style="font-size: 11px; color: #999; margin-top: 4px;">Interactive walkthrough</div>
                    </button>

                    <button class="tutorial-help-option" onclick="TutorialManager.showContextHelp('upload'); this.closest('.tutorial-help-modal').remove();">
                        <div style="font-size: 24px; margin-bottom: 8px;">📤</div>
                        <strong>Upload Help</strong>
                        <div style="font-size: 11px; color: #999; margin-top: 4px;">How to add documents</div>
                    </button>

                    <button class="tutorial-help-option" onclick="TutorialManager.showContextHelp('graph'); this.closest('.tutorial-help-modal').remove();">
                        <div style="font-size: 24px; margin-bottom: 8px;">🔍</div>
                        <strong>Graph Guide</strong>
                        <div style="font-size: 11px; color: #999; margin-top: 4px;">Navigate the graph</div>
                    </button>

                    <button class="tutorial-help-option" onclick="TutorialManager.showContextHelp('ai'); this.closest('.tutorial-help-modal').remove();">
                        <div style="font-size: 24px; margin-bottom: 8px;">🤖</div>
                        <strong>AI Assistant</strong>
                        <div style="font-size: 11px; color: #999; margin-top: 4px;">Ask questions</div>
                    </button>

                    <button class="tutorial-help-option" onclick="TutorialManager.showContextHelp('search'); this.closest('.tutorial-help-modal').remove();">
                        <div style="font-size: 24px; margin-bottom: 8px;">🔎</div>
                        <strong>Search Help</strong>
                        <div style="font-size: 11px; color: #999; margin-top: 4px;">Find information</div>
                    </button>

                    <button class="tutorial-help-option" onclick="TutorialManager.showContextHelp('projects'); this.closest('.tutorial-help-modal').remove();">
                        <div style="font-size: 24px; margin-bottom: 8px;">📁</div>
                        <strong>Projects</strong>
                        <div style="font-size: 11px; color: #999; margin-top: 4px;">Organize research</div>
                    </button>
                </div>

                <div style="text-align: right;">
                    <button class="tutorial-btn tutorial-btn-secondary" onclick="this.closest('.tutorial-help-modal').remove()">Close</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Close on backdrop click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    /**
     * Restart tutorial (reset and start)
     */
    static restart() {
        this.reset();
        this.start();
    }
}

// Make globally accessible
window.TutorialManager = TutorialManager;

// Listen for events to auto-advance tutorial
document.addEventListener('DOMContentLoaded', () => {
    // Document uploaded event
    document.addEventListener('documentUploaded', () => {
        if (TutorialManager.isActive && TutorialManager.currentStep === 1) {
            console.log('[Tutorial] Document uploaded - advancing');
            setTimeout(() => TutorialManager.nextStep(), 1000);
        }
    });

    // Node selected event
    document.addEventListener('nodeSelected', () => {
        if (TutorialManager.isActive && TutorialManager.currentStep === 3) {
            console.log('[Tutorial] Node selected - advancing');
            setTimeout(() => TutorialManager.nextStep(), 1000);
        }
    });
});
