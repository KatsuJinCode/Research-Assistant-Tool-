/**
 * AI Assistant Module - Context-Aware Chat Interface
 *
 * Handles:
 * - Chat message handling
 * - Context awareness (active tab, selected nodes, recent actions)
 * - Quick actions
 * - UI element highlighting (attention drawing)
 * - Command processing with approval system
 */

const AIAssistant = {
    // Chat state
    chatHistory: [],
    context: {
        activeTab: 'documents',
        selectedNodes: [],
        recentActions: []
    },

    // Quick action handlers
    quickActions: {
        'Find Similar': 'findSimilar',
        'Analyze': 'analyze',
        'Suggest': 'suggest'
    },

    /**
     * Initialize AI assistant
     */
    init() {
        console.log('[AIAssistant] Initializing AI assistant...');

        // Load chat history
        this.loadChatHistory();

        // Setup event listeners
        this.setupEventListeners();

        // Setup quick actions
        this.setupQuickActions();

        // Send welcome message
        this.displayWelcomeMessage();

        console.log('[AIAssistant] ✓ AI assistant initialized');
    },

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Send button
        const sendBtn = document.getElementById('ai-send-btn');
        if (sendBtn) {
            sendBtn.addEventListener('click', () => this.sendMessage());
        }

        // Input field - Enter key
        const input = document.getElementById('ai-input');
        if (input) {
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
        }

        // Listen for context changes
        window.addEventListener('tabChanged', (e) => {
            this.updateContext(e.detail.tabId);
        });

        window.addEventListener('nodeSelected', (e) => {
            this.addSelectedNode(e.detail.nodeId);
        });

        window.addEventListener('nodeDeselected', (e) => {
            this.removeSelectedNode(e.detail.nodeId);
        });
    },

    /**
     * Setup quick action buttons
     */
    setupQuickActions() {
        const quickActionButtons = document.querySelectorAll('.ai-quick-action');
        quickActionButtons.forEach(button => {
            button.addEventListener('click', () => {
                const action = button.textContent.trim().replace(/^[^\w]+/, '');
                this.handleQuickAction(action);
            });
        });
    },

    /**
     * Display welcome message
     */
    displayWelcomeMessage() {
        if (this.chatHistory.length === 0) {
            this.addAIMessage(
                "Hello! I'm your AI research assistant. I can help you:\n\n" +
                "• Find and analyze documents\n" +
                "• Discover connections between claims\n" +
                "• Search for evidence\n" +
                "• Organize your research\n\n" +
                "What would you like to do?"
            );
        }
    },

    /**
     * Send user message
     */
    sendMessage() {
        const input = document.getElementById('ai-input');
        if (!input) return;

        const message = input.value.trim();
        if (!message) return;

        // Add user message to chat
        this.addUserMessage(message);

        // Clear input
        input.value = '';

        // Process message
        this.processMessage(message);
    },

    /**
     * Process user message
     */
    async processMessage(message) {
        console.log('[AIAssistant] Processing message:', message);

        // Show typing indicator
        this.showTypingIndicator();

        try {
            // Call the real API endpoint
            const response = await fetch('/api/assistant/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    context: this.context
                })
            });

            this.hideTypingIndicator();

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to get response from assistant');
            }

            const data = await response.json();

            // Display the AI's response
            this.addAIMessage(data.response);

        } catch (error) {
            this.hideTypingIndicator();
            console.error('[AIAssistant] Error:', error);

            this.addAIMessage(
                `⚠️ Sorry, I encountered an error: ${error.message}\n\n` +
                `Please try rephrasing your question or check that the backend is running.`
            );
        }
    },

    /**
     * Handle user query based on content and context
     */
    handleUserQuery(query) {
        const lowerQuery = query.toLowerCase();

        // Command detection
        if (lowerQuery.includes('find') || lowerQuery.includes('search')) {
            this.handleSearchCommand(query);
        } else if (lowerQuery.includes('analyze') || lowerQuery.includes('explain')) {
            this.handleAnalyzeCommand(query);
        } else if (lowerQuery.includes('add') || lowerQuery.includes('create')) {
            this.handleCreateCommand(query);
        } else if (lowerQuery.includes('show') || lowerQuery.includes('display')) {
            this.handleDisplayCommand(query);
        } else if (lowerQuery.includes('help')) {
            this.handleHelpCommand();
        } else {
            // General query
            this.handleGeneralQuery(query);
        }
    },

    /**
     * Handle search command
     */
    handleSearchCommand(query) {
        const response = `I'll help you search. Let me extract the key terms from your query...\n\n`;

        // Extract search terms (simplified)
        const searchTerms = query.replace(/find|search|for|the|a|an/gi, '').trim();

        if (searchTerms) {
            this.addAIMessage(
                response +
                `I found these relevant items related to "${searchTerms}":\n\n` +
                `📄 3 documents\n` +
                `📝 5 claims\n` +
                `🔗 2 evidence links\n\n` +
                `Would you like me to filter the graph to show these results?`,
                [
                    { text: 'Yes, show results', action: 'showSearchResults' },
                    { text: 'No, just list them', action: 'listSearchResults' }
                ]
            );
        } else {
            this.addAIMessage('What would you like to search for?');
        }
    },

    /**
     * Handle analyze command
     */
    handleAnalyzeCommand(query) {
        if (this.context.selectedNodes.length === 0) {
            this.addAIMessage(
                'Please select a node in the graph that you want me to analyze.\n\n' +
                'You can click on any document, claim, or evidence node.'
            );
            this.highlightElement('graph-container', 'Click a node to analyze');
        } else {
            this.addAIMessage(
                `I'll analyze the selected ${this.context.selectedNodes.length} node(s)...\n\n` +
                `**Analysis:**\n` +
                `• Connection strength: High\n` +
                `• Related claims: 3\n` +
                `• Evidence quality: Good\n\n` +
                `Would you like me to find similar documents?`,
                [
                    { text: 'Find similar', action: 'findSimilar' },
                    { text: 'Show connections', action: 'showConnections' }
                ]
            );
        }
    },

    /**
     * Handle create command
     */
    handleCreateCommand(query) {
        this.addAIMessage(
            '⚠️ **Approval Required**\n\n' +
            `I can create new items in your research graph, but I need your approval first.\n\n` +
            `What would you like me to create?\n\n` +
            `• Document\n` +
            `• Claim\n` +
            `• Evidence link\n` +
            `• Project`,
            [
                { text: 'Create Document', action: 'requestCreateDocument' },
                { text: 'Create Claim', action: 'requestCreateClaim' },
                { text: 'Cancel', action: 'cancel' }
            ]
        );
    },

    /**
     * Handle display command
     */
    handleDisplayCommand(query) {
        const lowerQuery = query.toLowerCase();

        if (lowerQuery.includes('document')) {
            this.switchTabAndNotify('documents', 'Showing all documents');
        } else if (lowerQuery.includes('claim')) {
            this.switchTabAndNotify('documents', 'Filtering to show claims...');
        } else if (lowerQuery.includes('agent')) {
            this.switchTabAndNotify('agents', 'Showing AI agents');
        } else if (lowerQuery.includes('project')) {
            this.switchTabAndNotify('projects', 'Showing projects');
        } else {
            this.addAIMessage('What would you like me to display?');
        }
    },

    /**
     * Handle help command
     */
    handleHelpCommand() {
        this.addAIMessage(
            '**I can help you with:**\n\n' +
            '**📄 Documents**\n' +
            '• "Find documents about X"\n' +
            '• "Show me all documents"\n' +
            '• "Analyze this document"\n\n' +
            '**🔍 Search**\n' +
            '• "Search for X"\n' +
            '• "Find similar documents"\n' +
            '• "Show connections"\n\n' +
            '**📝 Claims & Evidence**\n' +
            '• "Show claims from this document"\n' +
            '• "Find evidence for this claim"\n' +
            '• "Analyze evidence quality"\n\n' +
            '**🤖 Agents**\n' +
            '• "Show active agents"\n' +
            '• "What are agents doing?"\n\n' +
            '**Navigation**\n' +
            '• "Show documents/claims/agents/projects"\n' +
            '• "Switch to X tab"\n\n' +
            'Just ask naturally - I\'ll understand!'
        );
    },

    /**
     * Handle general query
     */
    handleGeneralQuery(query) {
        this.addAIMessage(
            `I understand you're asking about: "${query}"\n\n` +
            `Based on your current context (${this.context.activeTab} tab), ` +
            `I can help you explore this topic. Would you like me to:\n\n` +
            `• Search for related documents\n` +
            `• Analyze existing connections\n` +
            `• Suggest next steps`,
            [
                { text: 'Search', action: 'search' },
                { text: 'Analyze', action: 'analyze' },
                { text: 'Suggest', action: 'suggest' }
            ]
        );
    },

    /**
     * Handle quick action
     */
    handleQuickAction(action) {
        console.log('[AIAssistant] Quick action:', action);

        if (action === 'Find Similar') {
            this.handleSearchCommand('find similar documents');
        } else if (action === 'Analyze') {
            this.handleAnalyzeCommand('analyze');
        } else if (action === 'Suggest') {
            this.addAIMessage(
                '**Suggestions based on your current research:**\n\n' +
                '• You have uncategorized documents - would you like me to help organize them?\n' +
                '• Some claims lack evidence - I can search for supporting sources\n' +
                '• Consider creating a new project to separate topics\n\n' +
                'What would you like to focus on?'
            );
        }
    },

    /**
     * Add user message to chat
     */
    addUserMessage(text) {
        const chatArea = document.getElementById('ai-chat-area');
        if (!chatArea) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = 'ai-message user';
        messageDiv.innerHTML = `
            <div>${this.escapeHtml(text)}</div>
            <div class="ai-message-time">${this.getTimeStamp()}</div>
        `;

        chatArea.appendChild(messageDiv);
        this.scrollToBottom();

        // Save to history
        this.chatHistory.push({ type: 'user', text, timestamp: Date.now() });
        this.saveChatHistory();
    },

    /**
     * Add AI message to chat
     */
    addAIMessage(text, actions = null) {
        const chatArea = document.getElementById('ai-chat-area');
        if (!chatArea) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = 'ai-message ai';

        // Convert markdown-like formatting
        const formattedText = this.formatText(text);

        let html = `
            <div>${formattedText}</div>
        `;

        // Add action buttons if provided
        if (actions && actions.length > 0) {
            html += '<div style="display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap;">';
            actions.forEach(action => {
                html += `
                    <button onclick="AIAssistant.handleActionButton('${action.action}')"
                            style="padding: 6px 12px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.3); border-radius: 4px; color: white; cursor: pointer; font-size: 12px;">
                        ${action.text}
                    </button>
                `;
            });
            html += '</div>';
        }

        html += `<div class="ai-message-time">${this.getTimeStamp()}</div>`;

        messageDiv.innerHTML = html;
        chatArea.appendChild(messageDiv);
        this.scrollToBottom();

        // Save to history
        this.chatHistory.push({ type: 'ai', text, actions, timestamp: Date.now() });
        this.saveChatHistory();
    },

    /**
     * Handle action button click
     */
    handleActionButton(action) {
        console.log('[AIAssistant] Action button clicked:', action);

        switch (action) {
            case 'showSearchResults':
                this.addUserMessage('Yes, show results');
                this.addAIMessage('Filtering graph to show search results...');
                break;
            case 'listSearchResults':
                this.addUserMessage('No, just list them');
                this.addAIMessage('Here are the search results:\n• Document 1\n• Document 2\n• Claim 1');
                break;
            case 'findSimilar':
                this.addUserMessage('Find similar');
                this.handleSearchCommand('find similar');
                break;
            case 'showConnections':
                this.addUserMessage('Show connections');
                this.addAIMessage('Displaying connections in graph...');
                break;
            case 'cancel':
                this.addUserMessage('Cancel');
                this.addAIMessage('Okay, cancelled.');
                break;
            default:
                this.handleQuickAction(action);
        }
    },

    /**
     * Show typing indicator
     */
    showTypingIndicator() {
        const chatArea = document.getElementById('ai-chat-area');
        if (!chatArea) return;

        const indicator = document.createElement('div');
        indicator.id = 'ai-typing-indicator';
        indicator.className = 'ai-message ai';
        indicator.innerHTML = `
            <div style="display: flex; gap: 4px; align-items: center;">
                <span style="animation: pulse 1.4s infinite;">●</span>
                <span style="animation: pulse 1.4s infinite 0.2s;">●</span>
                <span style="animation: pulse 1.4s infinite 0.4s;">●</span>
            </div>
        `;

        chatArea.appendChild(indicator);
        this.scrollToBottom();
    },

    /**
     * Hide typing indicator
     */
    hideTypingIndicator() {
        const indicator = document.getElementById('ai-typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    },

    /**
     * Scroll chat to bottom
     */
    scrollToBottom() {
        const chatArea = document.getElementById('ai-chat-area');
        if (chatArea) {
            setTimeout(() => {
                chatArea.scrollTop = chatArea.scrollHeight;
            }, 100);
        }
    },

    /**
     * Update context when tab changes
     */
    updateContext(tabId) {
        this.context.activeTab = tabId;

        // Update context badge
        const badge = document.getElementById('ai-context-badge');
        if (badge) {
            const labels = {
                'documents': 'Documents',
                'search': 'Search',
                'agents': 'Agents',
                'projects': 'Projects'
            };
            badge.textContent = labels[tabId] || tabId;
        }

        console.log('[AIAssistant] Context updated:', this.context);
    },

    /**
     * Add selected node to context
     */
    addSelectedNode(nodeId) {
        if (!this.context.selectedNodes.includes(nodeId)) {
            this.context.selectedNodes.push(nodeId);
            console.log('[AIAssistant] Node selected:', nodeId);
        }
    },

    /**
     * Remove selected node from context
     */
    removeSelectedNode(nodeId) {
        this.context.selectedNodes = this.context.selectedNodes.filter(id => id !== nodeId);
        console.log('[AIAssistant] Node deselected:', nodeId);
    },

    /**
     * Highlight UI element to draw attention
     */
    highlightElement(elementId, message = null) {
        const element = document.getElementById(elementId);
        if (!element) return;

        element.classList.add('ui-attention');

        if (message) {
            // Show tooltip or notification
            if (window.UI && UI.showNotification) {
                UI.showNotification(message, 'info');
            }
        }

        // Remove highlight after animation
        setTimeout(() => {
            element.classList.remove('ui-attention');
        }, 3000);
    },

    /**
     * Switch tab and notify user
     */
    switchTabAndNotify(tabId, message) {
        if (window.TabManager) {
            TabManager.switchTab(tabId);
        }
        this.addAIMessage(message);
    },

    /**
     * Format text with markdown-like syntax
     */
    formatText(text) {
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>')
            .replace(/• /g, '&bull; ');
    },

    /**
     * Escape HTML
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    /**
     * Get formatted timestamp
     */
    getTimeStamp() {
        const now = new Date();
        return now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    },

    /**
     * Save chat history to localStorage
     */
    saveChatHistory() {
        try {
            // Only save last 50 messages
            const recentHistory = this.chatHistory.slice(-50);
            localStorage.setItem('aiChatHistory', JSON.stringify(recentHistory));
        } catch (e) {
            console.warn('[AIAssistant] Failed to save chat history:', e);
        }
    },

    /**
     * Load chat history from localStorage
     */
    loadChatHistory() {
        try {
            const saved = localStorage.getItem('aiChatHistory');
            if (saved) {
                this.chatHistory = JSON.parse(saved);

                // Restore chat display
                const chatArea = document.getElementById('ai-chat-area');
                if (chatArea) {
                    chatArea.innerHTML = ''; // Clear welcome message

                    this.chatHistory.forEach(msg => {
                        if (msg.type === 'user') {
                            this.addUserMessage(msg.text);
                        } else if (msg.type === 'ai') {
                            this.addAIMessage(msg.text, msg.actions);
                        }
                    });
                }
            }
        } catch (e) {
            console.warn('[AIAssistant] Failed to load chat history:', e);
        }
    },

    /**
     * Clear chat history
     */
    clearChat() {
        this.chatHistory = [];
        this.saveChatHistory();

        const chatArea = document.getElementById('ai-chat-area');
        if (chatArea) {
            chatArea.innerHTML = '';
        }

        this.displayWelcomeMessage();
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        AIAssistant.init();
    }, 250);
});
