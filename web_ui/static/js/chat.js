/**
 * Chat Module - AI Assistant Interface
 */

const Chat = {
    messages: [],
    isTyping: false,

    /**
     * Initialize chat system
     */
    init() {
        console.log('[Chat] Initializing chat system...');

        // Setup event listeners
        this.setupEventListeners();

        // Send welcome message
        this.addMessage('ai',
            '👋 **Welcome to your Research Assistant!**\n\n' +
            'I can help you manage your research graph through natural conversation:\n\n' +
            '**📄 Documents:**\n' +
            '• Upload and process PDFs, TXT, DOCX\n' +
            '• Track processing progress\n\n' +
            '**🎯 Claims:**\n' +
            '• Add claims: "Add claim \\"Your text here\\""\n' +
            '• Adjust confidence: "Set to 80%" or "Mark as true"\n' +
            '• Remove invalid evidence\n\n' +
            '**🔍 Research & Investigation:**\n' +
            '• Select claim + "investigate this"\n' +
            '• "Find supporting evidence"\n' +
            '• "Find contradicting evidence"\n' +
            '• "Search ArXiv for [topic]"\n' +
            '• "Find citations for this claim"\n' +
            '• "Fact check this"\n\n' +
            '**⚙️ Monitoring:**\n' +
            '• "What agents are running?"\n' +
            '• Check processing queue status\n' +
            '• View graph statistics\n\n' +
            '**Try:** Type `/help` for slash commands, or just tell me what you need!'
        );

        // Poll for selection changes and update context chips
        setInterval(() => {
            this.updateContextChips();
        }, 500); // Check every 500ms

        console.log('[Chat] ✓ Chat initialized');
    },

    /**
     * Setup chat event listeners
     */
    setupEventListeners() {
        const sendBtn = document.getElementById('chat-send-btn');
        const input = document.getElementById('chat-input');

        if (sendBtn && input) {
            // Send button click
            sendBtn.addEventListener('click', () => {
                this.sendMessage();
            });

            // Enter key in input
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
        }

        // Listen for WebSocket chat responses
        if (App.socket) {
            App.socket.on('chat_response', (data) => {
                console.log('[Chat] Received response:', data);
                this.handleAIResponse(data);
            });
        }
    },

    /**
     * Send user message
     */
    sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();

        if (!message) return;

        // Add user message to UI
        this.addMessage('user', message);

        // Clear input
        input.value = '';

        // Show typing indicator
        this.showTyping();

        // Send to backend via WebSocket
        if (App.socket) {
            App.socket.emit('chat_message', {
                message: message,
                timestamp: new Date().toISOString(),
                context: this.getGraphContext()
            });
        } else {
            // Fallback: Simple echo response for testing
            setTimeout(() => {
                this.hideTyping();
                this.addMessage('ai', `I heard you say: "${message}"\n\nNote: WebSocket not connected. This is a test response.`);
            }, 1000);
        }
    },

    /**
     * Handle AI response from backend
     */
    handleAIResponse(data) {
        this.hideTyping();

        // Add AI message
        this.addMessage('ai', data.message || 'I understand. Let me help with that.');

        // Handle any actions requested by AI
        if (data.actions && Array.isArray(data.actions)) {
            data.actions.forEach(action => {
                this.executeAction(action);
            });
        }
    },

    /**
     * Execute an action requested by AI
     */
    executeAction(action) {
        console.log('[Chat] Executing action:', action);

        switch (action.type) {
            case 'highlight_upload':
                this.highlightElement('#upload-zone');
                break;

            case 'open_claim':
                if (action.claim_id) {
                    UI.showClaimDetails(action.claim_id);
                }
                break;

            case 'start_investigation':
                if (action.claim_id && action.investigation_type) {
                    // Trigger investigation
                    window.investigateClaim(action.investigation_type);
                }
                break;

            case 'reload_graph':
                App.loadGraph();
                break;

            default:
                console.warn('[Chat] Unknown action type:', action.type);
        }
    },

    /**
     * Highlight an element temporarily
     */
    highlightElement(selector) {
        const element = document.querySelector(selector);
        if (!element) return;

        element.style.boxShadow = '0 0 20px #FFD700';
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });

        setTimeout(() => {
            element.style.boxShadow = '';
        }, 3000);
    },

    /**
     * Get current graph context for AI
     */
    getGraphContext() {
        return {
            selected_nodes: Array.from(GraphRenderer.selectedNodeIds || []),
            total_nodes: GraphRenderer.currentGraphData?.nodes?.length || 0,
            total_links: GraphRenderer.currentGraphData?.links?.length || 0,
            search_query: GraphRenderer.searchQuery || ''
        };
    },

    /**
     * Update context chips display based on selected nodes
     */
    updateContextChips() {
        const contextArea = document.getElementById('chat-context-area');
        const chipsContainer = document.getElementById('chat-context-chips');

        if (!contextArea || !chipsContainer) return;

        const selectedNodes = Array.from(GraphRenderer.selectedNodeIds || []);

        if (selectedNodes.length === 0) {
            contextArea.style.display = 'none';
            chipsContainer.innerHTML = '';
            return;
        }

        // Show context area
        contextArea.style.display = 'block';

        // Get node data
        const nodes = GraphRenderer.currentGraphData?.nodes || [];
        const nodeMap = new Map(nodes.map(n => [n.id, n]));

        // Create chips
        let chipsHTML = '';
        selectedNodes.forEach(nodeId => {
            const node = nodeMap.get(nodeId);
            if (!node) return;

            const nodeType = node.type || 'unknown';
            const nodeLabel = node.label || node.id.substring(0, 20);

            // Color based on type
            let chipColor = '#666';
            if (nodeType === 'claim') chipColor = '#4CAF50';
            else if (nodeType === 'document') chipColor = '#2196F3';
            else if (nodeType === 'evidence') chipColor = '#FF9800';

            chipsHTML += `
                <div class="context-chip" data-node-id="${nodeId}" style="
                    background: ${chipColor};
                    color: white;
                    padding: 4px 8px;
                    border-radius: 12px;
                    font-size: 11px;
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    cursor: pointer;
                ">
                    <span>${nodeType.toUpperCase()}: ${this.escapeHtml(nodeLabel)}</span>
                    <span onclick="Chat.removeContextNode('${nodeId}')" style="
                        cursor: pointer;
                        font-weight: bold;
                        opacity: 0.7;
                        hover: opacity: 1;
                    ">✕</span>
                </div>
            `;
        });

        chipsContainer.innerHTML = chipsHTML;
    },

    /**
     * Remove node from context
     */
    removeContextNode(nodeId) {
        // Deselect in graph
        if (GraphRenderer.selectedNodeIds) {
            GraphRenderer.selectedNodeIds.delete(nodeId);
            GraphRenderer.renderGraph(GraphRenderer.currentGraphData);
        }

        // Update chips
        this.updateContextChips();
    },

    /**
     * Add message to chat
     */
    addMessage(sender, text) {
        const messagesContainer = document.getElementById('chat-messages');
        if (!messagesContainer) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender}`;

        const avatar = document.createElement('div');
        avatar.className = 'chat-message-avatar';
        avatar.textContent = sender === 'ai' ? '🤖' : '👤';

        const content = document.createElement('div');
        content.className = 'chat-message-content';
        content.textContent = text;

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);

        messagesContainer.appendChild(messageDiv);

        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // Store message
        this.messages.push({
            sender,
            text,
            timestamp: new Date().toISOString()
        });
    },

    /**
     * Show typing indicator
     */
    showTyping() {
        if (this.isTyping) return;
        this.isTyping = true;

        const messagesContainer = document.getElementById('chat-messages');
        if (!messagesContainer) return;

        const typingDiv = document.createElement('div');
        typingDiv.className = 'chat-message ai';
        typingDiv.id = 'typing-indicator';

        const avatar = document.createElement('div');
        avatar.className = 'chat-message-avatar';
        avatar.textContent = '🤖';

        const dots = document.createElement('div');
        dots.className = 'chat-typing-indicator';
        dots.innerHTML = '<div class="chat-typing-dot"></div><div class="chat-typing-dot"></div><div class="chat-typing-dot"></div>';

        typingDiv.appendChild(avatar);
        typingDiv.appendChild(dots);

        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    },

    /**
     * Hide typing indicator
     */
    hideTyping() {
        this.isTyping = false;
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    },

    /**
     * Clear chat history
     */
    clearHistory() {
        this.messages = [];
        const messagesContainer = document.getElementById('chat-messages');
        if (messagesContainer) {
            messagesContainer.innerHTML = '';
        }
    }
};

// Initialize chat when app is ready
document.addEventListener('DOMContentLoaded', () => {
    // Wait for App to initialize first
    setTimeout(() => {
        Chat.init();
    }, 500);
});
