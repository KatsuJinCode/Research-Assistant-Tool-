/**
 * Agent Mode Indicator - Shows SDK vs CLI mode status
 *
 * Displays a badge showing whether the chatbot is using:
 * - SDK Mode (full features): Direct API calls with streaming, tool use, etc.
 * - CLI Mode (reduced features): Subprocess calls with limitations
 */

class AgentModeIndicator {
    constructor() {
        this.indicator = null;
        this.mode = null;
        this.init();
    }

    async init() {
        try {
            // Fetch agent mode info from API
            const response = await fetch('/api/agent/mode');
            const modeInfo = await response.json();

            this.mode = modeInfo;

            // Create and show indicator
            this.createIndicator();
            this.updateIndicator(modeInfo);

        } catch (error) {
            console.error('Failed to initialize agent mode indicator:', error);
        }
    }

    createIndicator() {
        // Create mode indicator badge
        this.indicator = document.createElement('div');
        this.indicator.id = 'agent-mode-indicator';
        this.indicator.className = 'agent-mode-indicator';
        this.indicator.title = 'Click for mode details';
        this.indicator.style.cursor = 'pointer';

        // Click handler to show details
        this.indicator.addEventListener('click', () => this.showModeDetails());

        // Add to header (after debug indicator if present)
        const header = document.querySelector('header') || document.querySelector('.stats-header');
        if (header) {
            header.appendChild(this.indicator);
        }

        // Add styles
        this.addStyles();
    }

    updateIndicator(modeInfo) {
        if (!this.indicator) return;

        const isSdk = modeInfo.mode === 'sdk';
        const adapterType = modeInfo.adapter_type || 'Unknown';

        // Set badge content
        const icon = isSdk ? '🚀' : '⚙️';
        const label = isSdk ? 'SDK Mode' : 'CLI Mode';
        const status = isSdk ? 'Full Features' : 'Reduced Features';

        this.indicator.innerHTML = `
            <span class="mode-icon">${icon}</span>
            <span class="mode-text">
                <strong>${adapterType} ${label}</strong>
                <small>${status}</small>
            </span>
        `;

        // Set badge color
        this.indicator.className = `agent-mode-indicator ${isSdk ? 'sdk-mode' : 'cli-mode'}`;

        // Update title with limitations if CLI mode
        if (!isSdk && modeInfo.limitations && modeInfo.limitations.length > 0) {
            this.indicator.title = 'CLI Mode Limitations:\n' + modeInfo.limitations.join('\n');
        }
    }

    showModeDetails() {
        if (!this.mode) return;

        const isSdk = this.mode.mode === 'sdk';
        const features = this.mode.features || {};
        const limitations = this.mode.limitations || [];

        // Create details modal
        const modal = document.createElement('div');
        modal.className = 'agent-mode-modal';
        modal.innerHTML = `
            <div class="agent-mode-modal-content">
                <div class="modal-header">
                    <h3>${isSdk ? '🚀 SDK Mode (Full Features)' : '⚙️ CLI Mode (Reduced Features)'}</h3>
                    <button class="close-btn">×</button>
                </div>
                <div class="modal-body">
                    <div class="mode-section">
                        <h4>Features:</h4>
                        <ul class="feature-list">
                            <li class="${features.streaming ? 'enabled' : 'disabled'}">
                                ${features.streaming ? '✓' : '✗'} Streaming responses
                            </li>
                            <li class="${features.tool_use ? 'enabled' : 'disabled'}">
                                ${features.tool_use ? '✓' : '✗'} Tool use / function calling
                            </li>
                            <li class="${features.full_api_control ? 'enabled' : 'disabled'}">
                                ${features.full_api_control ? '✓' : '✗'} Full API parameter control
                            </li>
                            <li class="${features.lower_latency ? 'enabled' : 'disabled'}">
                                ${features.lower_latency ? '✓' : '✗'} Lower latency
                            </li>
                        </ul>
                    </div>
                    ${limitations.length > 0 ? `
                        <div class="mode-section limitations">
                            <h4>⚠️ Limitations:</h4>
                            <ul class="limitation-list">
                                ${limitations.map(lim => `<li>${lim}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    <div class="mode-section info">
                        <p><strong>Current Mode:</strong> ${this.mode.mode.toUpperCase()}</p>
                        <p><strong>Provider:</strong> ${this.mode.adapter_type || 'Unknown'}</p>
                        ${this.mode.is_dev_mode ? '<p><strong>Environment:</strong> Development</p>' : ''}
                    </div>
                </div>
            </div>
        `;

        // Add to body
        document.body.appendChild(modal);

        // Close handlers
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.remove();
        });
        modal.querySelector('.close-btn').addEventListener('click', () => modal.remove());
    }

    addStyles() {
        const style = document.createElement('style');
        style.textContent = `
            /* Agent Mode Indicator */
            .agent-mode-indicator {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                padding: 0.4rem 0.8rem;
                border-radius: 20px;
                font-size: 0.85rem;
                font-weight: 600;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
                margin-left: 0.5rem;
                transition: transform 0.2s;
            }

            .agent-mode-indicator:hover {
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            }

            .agent-mode-indicator.sdk-mode {
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                color: white;
            }

            .agent-mode-indicator.cli-mode {
                background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
                color: white;
            }

            .mode-icon {
                font-size: 1rem;
            }

            .mode-text {
                display: flex;
                flex-direction: column;
                gap: 0.1rem;
            }

            .mode-text small {
                font-size: 0.7rem;
                opacity: 0.9;
            }

            /* Modal */
            .agent-mode-modal {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10000;
            }

            .agent-mode-modal-content {
                background: white;
                border-radius: 12px;
                max-width: 500px;
                width: 90%;
                max-height: 80vh;
                overflow-y: auto;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            }

            .modal-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 1.5rem;
                border-bottom: 2px solid #e5e7eb;
            }

            .modal-header h3 {
                margin: 0;
                font-size: 1.25rem;
                color: #1f2937;
            }

            .close-btn {
                background: none;
                border: none;
                font-size: 2rem;
                color: #6b7280;
                cursor: pointer;
                line-height: 1;
                padding: 0;
                width: 32px;
                height: 32px;
            }

            .close-btn:hover {
                color: #1f2937;
            }

            .modal-body {
                padding: 1.5rem;
            }

            .mode-section {
                margin-bottom: 1.5rem;
            }

            .mode-section h4 {
                margin: 0 0 0.75rem 0;
                font-size: 1rem;
                color: #374151;
            }

            .feature-list,
            .limitation-list {
                margin: 0;
                padding-left: 1.5rem;
                list-style: none;
            }

            .feature-list li,
            .limitation-list li {
                padding: 0.5rem 0;
                color: #4b5563;
            }

            .feature-list li.enabled {
                color: #059669;
                font-weight: 600;
            }

            .feature-list li.disabled {
                color: #9ca3af;
                text-decoration: line-through;
            }

            .mode-section.limitations {
                background: #fef3c7;
                padding: 1rem;
                border-radius: 8px;
                border-left: 4px solid #f59e0b;
            }

            .limitation-list li {
                color: #92400e;
            }

            .mode-section.info {
                background: #f3f4f6;
                padding: 1rem;
                border-radius: 8px;
            }

            .mode-section.info p {
                margin: 0.5rem 0;
                color: #374151;
            }
        `;
        document.head.appendChild(style);
    }
}

// Initialize mode indicator when page loads
document.addEventListener('DOMContentLoaded', () => {
    new AgentModeIndicator();
});
