/**
 * Development Debugging Agent - Frontend
 *
 * Provides visual indicator, toggle control, and displays debugging messages
 * in the chat interface. Only active in development mode.
 */

class DebugAgent {
    constructor(socket) {
        this.socket = socket;
        this.isEnabled = false;
        this.indicator = null;
        this.toggleButton = null;

        this.init();
    }

    async init() {
        // Check debug agent status
        try {
            const response = await fetch('/api/debug/status');
            const status = await response.json();

            this.isEnabled = status.enabled;
            this.isDevMode = status.dev_mode;

            // Only show debug controls in development mode
            if (this.isDevMode) {
                this.createUI();
                this.setupWebSocketListeners();

                if (this.isEnabled) {
                    this.showIndicator();
                }
            }
        } catch (error) {
            console.error('Failed to initialize debug agent:', error);
        }
    }

    createUI() {
        // Create debug indicator (badge in header)
        this.indicator = document.createElement('div');
        this.indicator.id = 'debug-indicator';
        this.indicator.className = 'debug-indicator';
        this.indicator.innerHTML = `
            <span class="debug-icon">🐛</span>
            <span class="debug-text">Debug Mode</span>
        `;
        this.indicator.style.display = 'none';

        // Create toggle button (next to chat input or in header)
        this.toggleButton = document.createElement('button');
        this.toggleButton.id = 'debug-toggle';
        this.toggleButton.className = 'debug-toggle-btn';
        this.toggleButton.innerHTML = this.isEnabled ? '🐛 Debugging: ON' : '🐛 Debugging: OFF';
        this.toggleButton.title = 'Toggle debugging assistant';

        // Click handler
        this.toggleButton.addEventListener('click', () => this.toggle());

        // Add to DOM
        const header = document.querySelector('header') || document.querySelector('.stats-header');
        if (header) {
            header.appendChild(this.indicator);
            header.appendChild(this.toggleButton);
        }

        // Add styles
        this.addStyles();
    }

    addStyles() {
        const style = document.createElement('style');
        style.textContent = `
            /* Debug Indicator */
            .debug-indicator {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                padding: 0.4rem 0.8rem;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 20px;
                font-size: 0.85rem;
                font-weight: 600;
                box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
                animation: debug-pulse 2s ease-in-out infinite;
                margin-left: auto;
                margin-right: 1rem;
            }

            .debug-icon {
                font-size: 1rem;
                animation: debug-wiggle 1s ease-in-out infinite;
            }

            @keyframes debug-pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.8; }
            }

            @keyframes debug-wiggle {
                0%, 100% { transform: rotate(0deg); }
                25% { transform: rotate(-10deg); }
                75% { transform: rotate(10deg); }
            }

            /* Debug Toggle Button */
            .debug-toggle-btn {
                padding: 0.4rem 1rem;
                background: #4a5568;
                color: white;
                border: 2px solid #667eea;
                border-radius: 6px;
                font-size: 0.85rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
                margin-left: 0.5rem;
            }

            .debug-toggle-btn:hover {
                background: #667eea;
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
            }

            .debug-toggle-btn.active {
                background: #667eea;
                border-color: #764ba2;
            }

            /* Debug Messages in Chat */
            .debug-message {
                margin: 1rem 0;
                padding: 1rem;
                background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
                border-left: 4px solid #667eea;
                border-radius: 8px;
                font-size: 0.9rem;
            }

            .debug-message.severity-critical {
                border-left-color: #e53e3e;
                background: linear-gradient(135deg, #e53e3e15 0%, #c53030 15 100%);
            }

            .debug-message.severity-high {
                border-left-color: #ed8936;
                background: linear-gradient(135deg, #ed893615 0%, #dd6b2015 100%);
            }

            .debug-message.severity-medium {
                border-left-color: #ecc94b;
                background: linear-gradient(135deg, #ecc94b15 0%, #d69e2e15 100%);
            }

            .debug-message-header {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                margin-bottom: 0.5rem;
                font-weight: 600;
                color: #2d3748;
            }

            .debug-message-title {
                flex: 1;
            }

            .debug-severity-badge {
                padding: 0.2rem 0.5rem;
                border-radius: 4px;
                font-size: 0.75rem;
                font-weight: 700;
                text-transform: uppercase;
            }

            .debug-severity-badge.critical {
                background: #e53e3e;
                color: white;
            }

            .debug-severity-badge.high {
                background: #ed8936;
                color: white;
            }

            .debug-severity-badge.medium {
                background: #ecc94b;
                color: #2d3748;
            }

            .debug-message-content {
                margin: 0.5rem 0;
            }

            .debug-error-message {
                font-family: 'Monaco', 'Consolas', monospace;
                font-size: 0.85rem;
                padding: 0.5rem;
                background: #1a202c;
                color: #e53e3e;
                border-radius: 4px;
                margin: 0.5rem 0;
                overflow-x: auto;
            }

            .debug-explanation {
                color: #4a5568;
                margin: 0.5rem 0;
            }

            .debug-solution {
                padding: 0.5rem;
                background: #48bb7815;
                border-left: 3px solid #48bb78;
                border-radius: 4px;
                margin: 0.5rem 0;
            }

            .debug-solution-title {
                font-weight: 600;
                color: #2f855a;
                margin-bottom: 0.3rem;
            }

            .debug-suggestions {
                margin-top: 0.5rem;
            }

            .debug-suggestions-title {
                font-weight: 600;
                color: #2d3748;
                margin-bottom: 0.3rem;
            }

            .debug-suggestions ul {
                margin: 0.3rem 0;
                padding-left: 1.5rem;
            }

            .debug-suggestions li {
                margin: 0.2rem 0;
                color: #4a5568;
            }

            .debug-traceback {
                margin-top: 0.5rem;
            }

            .debug-traceback-toggle {
                color: #667eea;
                cursor: pointer;
                font-size: 0.85rem;
                text-decoration: underline;
            }

            .debug-traceback-toggle:hover {
                color: #764ba2;
            }

            .debug-traceback-content {
                display: none;
                font-family: 'Monaco', 'Consolas', monospace;
                font-size: 0.75rem;
                padding: 0.5rem;
                background: #1a202c;
                color: #cbd5e0;
                border-radius: 4px;
                margin-top: 0.3rem;
                overflow-x: auto;
                max-height: 300px;
                overflow-y: auto;
            }
        `;
        document.head.appendChild(style);
    }

    setupWebSocketListeners() {
        // Listen for debug status changes
        this.socket.on('debug_status', (data) => {
            this.isEnabled = data.enabled;
            this.updateUI();

            // Show notification
            if (data.message) {
                this.showNotification(data.message);
            }
        });

        // Listen for debug messages (errors, warnings, etc.)
        this.socket.on('debug_message', (data) => {
            this.displayDebugMessage(data);
        });
    }

    async toggle() {
        try {
            const response = await fetch('/api/debug/toggle', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'}
            });

            const result = await response.json();
            this.isEnabled = result.enabled;
            this.updateUI();

            this.showNotification(result.message);
        } catch (error) {
            console.error('Failed to toggle debug agent:', error);
        }
    }

    updateUI() {
        if (this.isEnabled) {
            this.showIndicator();
            this.toggleButton.innerHTML = '🐛 Debugging: ON';
            this.toggleButton.classList.add('active');
        } else {
            this.hideIndicator();
            this.toggleButton.innerHTML = '🐛 Debugging: OFF';
            this.toggleButton.classList.remove('active');
        }
    }

    showIndicator() {
        if (this.indicator) {
            this.indicator.style.display = 'flex';
        }
    }

    hideIndicator() {
        if (this.indicator) {
            this.indicator.style.display = 'none';
        }
    }

    displayDebugMessage(data) {
        // Find or create messages container
        let messagesContainer = document.querySelector('.ai-messages');
        if (!messagesContainer) {
            // Fallback to chat container
            messagesContainer = document.querySelector('.chat-messages') ||
                               document.querySelector('.messages-container');
        }

        if (!messagesContainer) {
            console.warn('Cannot find messages container for debug message');
            return;
        }

        // Create debug message element
        const messageEl = document.createElement('div');
        messageEl.className = `debug-message severity-${data.severity}`;

        let html = `
            <div class="debug-message-header">
                <span class="debug-message-title">${data.title}</span>
                <span class="debug-severity-badge ${data.severity}">${data.severity}</span>
            </div>
        `;

        // Error message
        if (data.error_message) {
            html += `
                <div class="debug-error-message">${this.escapeHtml(data.error_message)}</div>
            `;
        }

        // Explanation
        if (data.explanation) {
            html += `
                <div class="debug-explanation">${this.escapeHtml(data.explanation)}</div>
            `;
        }

        // Solution
        if (data.solution) {
            html += `
                <div class="debug-solution">
                    <div class="debug-solution-title">💡 Suggested Solution:</div>
                    <div>${this.escapeHtml(data.solution)}</div>
                </div>
            `;
        }

        // Suggestions
        if (data.suggestions && data.suggestions.length > 0) {
            html += `
                <div class="debug-suggestions">
                    <div class="debug-suggestions-title">📋 Things to try:</div>
                    <ul>
                        ${data.suggestions.map(s => `<li>${this.escapeHtml(s)}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        // Traceback (collapsible)
        if (data.traceback) {
            const tracebackId = 'traceback-' + Date.now();
            html += `
                <div class="debug-traceback">
                    <span class="debug-traceback-toggle" onclick="document.getElementById('${tracebackId}').style.display = document.getElementById('${tracebackId}').style.display === 'none' ? 'block' : 'none'">
                        Show/Hide Stack Trace
                    </span>
                    <pre class="debug-traceback-content" id="${tracebackId}">${this.escapeHtml(data.traceback)}</pre>
                </div>
            `;
        }

        messageEl.innerHTML = html;

        // Add to messages container
        messagesContainer.appendChild(messageEl);

        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    showNotification(message) {
        // Simple notification (you can enhance this)
        console.log('🐛 Debug Agent:', message);

        // You could also show a toast notification here
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize debug agent when page loads
let debugAgent = null;

document.addEventListener('DOMContentLoaded', () => {
    // Wait for socket to be available (it's initialized in the main page)
    const initDebugAgent = () => {
        if (typeof socket !== 'undefined') {
            debugAgent = new DebugAgent(socket);
        } else {
            // Retry after a short delay
            setTimeout(initDebugAgent, 500);
        }
    };

    initDebugAgent();
});
