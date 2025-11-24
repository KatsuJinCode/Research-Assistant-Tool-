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

        // Initialize contextual suggestions for current tab
        this.updateContextualSuggestions(this.context.activeTab);

        console.log('[AIAssistant] ✓ AI assistant initialized');
    },

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Send button (no need for listener, using inline onclick)

        // Input field - Enter key (new bottom panel)
        const input = document.getElementById('ai-input-bottom');
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
     * Fill the input field with a suggested prompt (doesn't submit)
     * User can edit the prompt before sending
     */
    fillPrompt(promptText) {
        const input = document.getElementById('ai-input-bottom');
        if (!input) return;

        // Fill the input with the suggested prompt
        input.value = promptText;

        // Focus the input so user can edit if desired
        input.focus();

        // Move cursor to end of text
        input.setSelectionRange(promptText.length, promptText.length);
    },

    /**
     * Send user message
     */
    sendMessage() {
        const input = document.getElementById('ai-input-bottom');
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
    addUserMessage(text, skipSave = false) {
        const chatArea = document.getElementById('ai-chat-messages-bottom');
        if (!chatArea) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = 'ai-message user';
        messageDiv.style.cssText = 'padding: 8px; background: rgba(33, 150, 243, 0.2); border-radius: 4px; margin-bottom: 8px; font-size: 11px; color: white;';
        messageDiv.innerHTML = `
            <div>${this.escapeHtml(text)}</div>
            <div style="font-size: 9px; color: #999; margin-top: 4px;">${this.getTimeStamp()}</div>
        `;

        chatArea.appendChild(messageDiv);
        this.scrollToBottom();

        // Save to history (unless we're restoring from localStorage)
        if (!skipSave) {
            this.chatHistory.push({ type: 'user', text, timestamp: Date.now() });
            this.saveChatHistory();
        }
    },

    /**
     * Add AI message to chat
     */
    addAIMessage(text, actions = null, skipSave = false) {
        const chatArea = document.getElementById('ai-chat-messages-bottom');
        if (!chatArea) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = 'ai-message ai';
        messageDiv.style.cssText = 'padding: 8px; background: rgba(255, 255, 255, 0.05); border-left: 3px solid #2196F3; border-radius: 4px; margin-bottom: 8px; font-size: 11px; color: #ccc;';

        // Convert markdown-like formatting
        const formattedText = this.formatText(text);

        let html = `
            <div>${formattedText}</div>
        `;

        // Add action buttons if provided
        if (actions && actions.length > 0) {
            html += '<div style="display: flex; gap: 4px; margin-top: 8px; flex-wrap: wrap;">';
            actions.forEach(action => {
                html += `
                    <button onclick="AIAssistant.handleActionButton('${action.action}')"
                            style="padding: 4px 8px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.3); border-radius: 3px; color: white; cursor: pointer; font-size: 10px;">
                        ${action.text}
                    </button>
                `;
            });
            html += '</div>';
        }

        html += `<div style="font-size: 9px; color: #666; margin-top: 4px;">${this.getTimeStamp()}</div>`;

        messageDiv.innerHTML = html;
        chatArea.appendChild(messageDiv);
        this.scrollToBottom();

        // Save to history (unless we're restoring from localStorage)
        if (!skipSave) {
            this.chatHistory.push({ type: 'ai', text, actions, timestamp: Date.now() });
            this.saveChatHistory();
        }
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
        const chatArea = document.getElementById('ai-chat-messages-bottom');
        if (!chatArea) return;

        const indicator = document.createElement('div');
        indicator.id = 'ai-typing-indicator';
        indicator.style.cssText = 'padding: 8px; background: rgba(255, 255, 255, 0.05); border-left: 3px solid #2196F3; border-radius: 4px; margin-bottom: 8px; font-size: 11px;';
        indicator.innerHTML = `
            <div style="display: flex; gap: 4px; align-items: center; color: #2196F3;">
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
        const chatArea = document.getElementById('ai-chat-messages-bottom');
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

        // Update context badge with selected nodes
        this.updateContextBadge();

        // Update contextual suggestions based on tab
        this.updateContextualSuggestions(tabId);

        console.log('[AIAssistant] Context updated:', this.context);
    },

    /**
     * Update the context badge to show active tab + selected nodes
     */
    updateContextBadge() {
        const badge = document.getElementById('ai-context-badge');
        if (!badge) return;

        const labels = {
            'documents': 'Documents',
            'search': 'Search',
            'agents': 'Agents',
            'projects': 'Projects'
        };

        let badgeText = labels[this.context.activeTab] || this.context.activeTab;

        // Add selected nodes count if any are selected
        if (this.context.selectedNodes && this.context.selectedNodes.length > 0) {
            badgeText += ` + ${this.context.selectedNodes.length} node${this.context.selectedNodes.length > 1 ? 's' : ''}`;
        }

        badge.textContent = badgeText;
    },

    /**
     * Update contextual suggestions based on active tab and data state
     */
    async updateContextualSuggestions(tabId) {
        console.log('[AIAssistant] Updating suggestions for tab:', tabId);

        try {
            // Fetch current graph stats to make suggestions intelligent
            const statsResponse = await fetch('/api/graph-stats');
            const stats = statsResponse.ok ? await statsResponse.json() : {};

            // First check for workflow patterns that override tab-specific suggestions
            const workflowSuggestions = await this.detectWorkflowPatterns(stats);

            if (workflowSuggestions.length > 0) {
                console.log('[AIAssistant] Workflow pattern detected, using workflow suggestions');
                this.renderSuggestions(workflowSuggestions);
                return;
            }

            // If nodes are selected, use node-specific suggestions
            if (this.context.selectedNodes.length > 0) {
                console.log('[AIAssistant] Nodes selected, maintaining node-specific suggestions');
                return; // Keep current node-specific suggestions
            }

            // Generate tab-specific suggestions
            let suggestions = [];

            switch (tabId) {
                case 'documents':
                    suggestions = this.getDocumentsSuggestions(stats);
                    break;
                case 'graph':
                    suggestions = this.getGraphSuggestions(stats);
                    break;
                case 'agents':
                    suggestions = this.getAgentsSuggestions(stats);
                    break;
                case 'projects':
                    suggestions = this.getProjectsSuggestions(stats);
                    break;
                default:
                    suggestions = this.getDefaultSuggestions();
            }

            // Render suggestions
            this.renderSuggestions(suggestions);

        } catch (error) {
            console.error('[AIAssistant] Error updating suggestions:', error);
            // Fall back to default suggestions
            this.renderSuggestions(this.getDefaultSuggestions());
        }
    },

    /**
     * Detect workflow patterns and return priority suggestions
     * Returns high-priority suggestions if critical patterns detected, otherwise empty array
     */
    async detectWorkflowPatterns(stats) {
        const prioritySuggestions = [];

        // Pattern 1: Multiple pending documents (urgent action needed)
        if (stats.documents_pending >= 3) {
            prioritySuggestions.push({
                icon: '⚡',
                text: `Process ${stats.documents_pending} pending documents`,
                prompt: `I have ${stats.documents_pending} pending documents. Process them all and extract claims.`
            });
        }

        // Pattern 2: Agent failures (needs investigation)
        if (stats.agents_failed >= 2) {
            prioritySuggestions.push({
                icon: '⚠️',
                text: `Investigate ${stats.agents_failed} failed agents`,
                prompt: `${stats.agents_failed} agents have failed. Help me investigate what went wrong.`
            });
        }

        // Pattern 3: Many orphaned claims (research gaps)
        if (stats.claims_without_evidence >= 5) {
            prioritySuggestions.push({
                icon: '🔍',
                text: `${stats.claims_without_evidence} claims need evidence`,
                prompt: `I have ${stats.claims_without_evidence} claims without evidence. Help me prioritize which to research first.`
            });
        }

        // Pattern 4: Empty database (onboarding)
        if (stats.total_documents === 0 && stats.total_claims === 0) {
            return this.getOnboardingSuggestions();
        }

        // Pattern 5: First-time user (show welcome)
        if (stats.total_documents > 0 && stats.total_documents < 3 && stats.total_claims < 10) {
            prioritySuggestions.push({
                icon: '👋',
                text: 'Take a tour of features',
                prompt: 'Show me what I can do with this research assistant'
            });
        }

        // Return priority suggestions if any critical patterns detected
        return prioritySuggestions.slice(0, 4);
    },

    /**
     * Get onboarding suggestions for new users with empty database
     */
    getOnboardingSuggestions() {
        return [
            {
                icon: '📄',
                text: 'Upload your first document',
                prompt: 'I want to upload a research paper to get started'
            },
            {
                icon: '💡',
                text: 'Create a manual claim',
                prompt: 'How do I manually create a claim?'
            },
            {
                icon: '🎓',
                text: 'Explain how this works',
                prompt: 'Explain how the research assistant works and what it can do'
            },
            {
                icon: '📊',
                text: 'Import existing data',
                prompt: 'I have existing research data. How can I import it?'
            }
        ];
    },

    /**
     * Get context-aware suggestions for Documents tab
     */
    getDocumentsSuggestions(stats) {
        const suggestions = [];

        // Check if there are pending documents
        if (stats.documents_pending > 0) {
            suggestions.push({
                icon: '⚡',
                text: `Process ${stats.documents_pending} pending document${stats.documents_pending > 1 ? 's' : ''}`,
                prompt: `Process all pending documents and extract claims`
            });
        }

        // Upload suggestion
        suggestions.push({
            icon: '📄',
            text: 'Upload new document',
            prompt: 'I want to upload a new research document'
        });

        // Search suggestion
        if (stats.total_documents > 0) {
            suggestions.push({
                icon: '🔍',
                text: 'Search for related papers',
                prompt: 'Search for papers related to my current documents'
            });
        }

        // Summarization suggestion
        if (stats.total_claims > 5) {
            suggestions.push({
                icon: '💬',
                text: 'Summarize key findings',
                prompt: 'Summarize the key claims across all documents'
            });
        }

        return suggestions.slice(0, 4); // Max 4 suggestions
    },

    /**
     * Get context-aware suggestions for Graph tab
     */
    getGraphSuggestions(stats) {
        const suggestions = [];

        // Find unsupported claims
        if (stats.total_claims > 0) {
            suggestions.push({
                icon: '🎯',
                text: 'Find unsupported claims',
                prompt: 'Show me claims that need more evidence'
            });
        }

        // Explore connections
        if (stats.total_claims > 3) {
            suggestions.push({
                icon: '🔗',
                text: 'Explore claim connections',
                prompt: 'Find relationships between claims'
            });
        }

        // Find contradictions
        if (stats.total_claims > 5) {
            suggestions.push({
                icon: '⚡',
                text: 'Find contradictions',
                prompt: 'Find claims that contradict each other'
            });
        }

        // Analyze evidence quality
        if (stats.total_evidence > 0) {
            suggestions.push({
                icon: '📊',
                text: 'Analyze evidence strength',
                prompt: 'Analyze the strength of evidence for each claim'
            });
        }

        return suggestions.slice(0, 4);
    },

    /**
     * Get context-aware suggestions for Agents tab
     */
    getAgentsSuggestions(stats) {
        const suggestions = [];

        // Check active agents
        if (stats.agents_active > 0) {
            suggestions.push({
                icon: '👀',
                text: `Monitor ${stats.agents_active} active agent${stats.agents_active > 1 ? 's' : ''}`,
                prompt: 'Show me what active agents are working on'
            });
        }

        // Spawn research agent
        suggestions.push({
            icon: '🤖',
            text: 'Spawn research agent',
            prompt: 'Spawn a new research agent to find evidence'
        });

        // Review completed agents
        if (stats.agents_completed > 0) {
            suggestions.push({
                icon: '✅',
                text: `Review ${stats.agents_completed} completed agent${stats.agents_completed > 1 ? 's' : ''}`,
                prompt: 'Show me results from completed agents'
            });
        }

        // Check for failed agents
        if (stats.agents_failed > 0) {
            suggestions.push({
                icon: '⚠️',
                text: `Fix ${stats.agents_failed} failed agent${stats.agents_failed > 1 ? 's' : ''}`,
                prompt: 'Investigate why agents failed and retry'
            });
        }

        return suggestions.slice(0, 4);
    },

    /**
     * Get context-aware suggestions for Projects tab
     */
    getProjectsSuggestions(stats) {
        const suggestions = [];

        // Create new project
        suggestions.push({
            icon: '➕',
            text: 'Create new project',
            prompt: 'Create a new research project'
        });

        // Export project
        if (stats.total_documents > 0) {
            suggestions.push({
                icon: '💾',
                text: 'Export project data',
                prompt: 'Export current project as markdown or JSON'
            });
        }

        // Organize documents
        if (stats.total_documents > 5) {
            suggestions.push({
                icon: '📂',
                text: 'Organize documents',
                prompt: 'Help me organize documents into projects'
            });
        }

        // Generate report
        if (stats.total_claims > 10) {
            suggestions.push({
                icon: '📄',
                text: 'Generate research report',
                prompt: 'Generate a comprehensive research report from all claims'
            });
        }

        return suggestions.slice(0, 4);
    },

    /**
     * Get default suggestions when tab is unknown or no data
     */
    getDefaultSuggestions() {
        return [
            {
                icon: '💬',
                text: 'Summarize key claims',
                prompt: 'Summarize the key claims in this document'
            },
            {
                icon: '⚡',
                text: 'Find contradictions',
                prompt: 'Find claims that contradict each other'
            },
            {
                icon: '🎯',
                text: 'Show strongest evidence',
                prompt: 'Show me the strongest evidence for this claim'
            },
            {
                icon: '🔍',
                text: 'Identify research gaps',
                prompt: 'What are the research gaps in this topic?'
            }
        ];
    },

    /**
     * Render suggestion buttons
     */
    renderSuggestions(suggestions) {
        const container = document.getElementById('ai-quick-actions');
        if (!container) return;

        // Clear existing suggestions
        container.innerHTML = '';

        // Render each suggestion
        suggestions.forEach(suggestion => {
            const button = document.createElement('button');
            button.className = 'ai-quick-action';
            button.onclick = () => this.fillPrompt(suggestion.prompt);
            button.style.cssText = 'padding: 3px 8px; background: #333; border: 1px solid #444; color: #999; border-radius: 3px; font-size: 9px; cursor: pointer; white-space: nowrap;';
            button.innerHTML = `
                <span>${suggestion.icon}</span> ${suggestion.text}
            `;
            container.appendChild(button);
        });

        console.log(`[AIAssistant] Rendered ${suggestions.length} suggestions`);
    },

    /**
     * Add selected node to context with full details
     */
    async addSelectedNode(nodeId) {
        // Check if already in context
        if (this.context.selectedNodes.some(n => n.id === nodeId)) {
            console.log('[AIAssistant] Node already in context:', nodeId);
            return;
        }

        try {
            // Fetch full node details from backend
            const response = await fetch(`/api/nodes/${nodeId}/full-details`);

            if (!response.ok) {
                throw new Error('Failed to fetch node details');
            }

            const fullDetails = await response.json();

            // Store full node data in context (not just ID)
            this.context.selectedNodes.push({
                id: nodeId,
                ...fullDetails
            });

            console.log('[AIAssistant] Node added to context with full details:', nodeId);

            // Update context badge
            this.updateContextBadge();

            // Display visual feedback badge
            this.displaySelectedNodeBadge(fullDetails);

            // Update suggestions based on selected node
            this.updateSuggestionsForSelectedNode(fullDetails);

        } catch (error) {
            console.error('[AIAssistant] Error fetching node details:', error);

            // Fallback: Add just the node ID
            this.context.selectedNodes.push({ id: nodeId });

            // Update context badge
            this.updateContextBadge();

            // Show simplified badge
            this.displaySelectedNodeBadge({ node: { id: nodeId, title: nodeId.substring(0, 8) } });
        }
    },

    /**
     * Remove selected node from context
     */
    removeSelectedNode(nodeId) {
        this.context.selectedNodes = this.context.selectedNodes.filter(n => n.id !== nodeId);
        console.log('[AIAssistant] Node deselected:', nodeId);

        // Update context badge
        this.updateContextBadge();

        // Remove visual badge
        const badge = document.querySelector(`.ai-context-node-badge[data-node-id="${nodeId}"]`);
        if (badge) {
            badge.remove();
        }

        // Update suggestions based on remaining selection
        if (this.context.selectedNodes.length === 0) {
            // No nodes selected - return to tab-specific suggestions
            this.updateContextualSuggestions(this.context.activeTab);
        } else if (this.context.selectedNodes.length === 1) {
            // One node remaining - show single-node suggestions
            this.updateSuggestionsForSelectedNode(this.context.selectedNodes[0]);
        } else {
            // Multiple nodes still selected - show multi-node suggestions
            this.updateMultiNodeSuggestions();
        }
    },

    /**
     * Display visual feedback badge for selected node
     */
    displaySelectedNodeBadge(nodeDetails) {
        const node = nodeDetails.node || {};
        const nodeId = node.id || nodeDetails.id || 'unknown';
        const nodeType = (node.labels && node.labels[0]) || 'unknown';
        const nodeTitle = node.title || node.text?.substring(0, 40) || node.summary?.substring(0, 40) || nodeId.substring(0, 8);

        // Get or create container for node badges
        let badgeContainer = document.getElementById('ai-selected-nodes-container');

        if (!badgeContainer) {
            // Create container below the context badge
            const contextBadge = document.getElementById('ai-context-badge');
            if (!contextBadge || !contextBadge.parentElement) return;

            badgeContainer = document.createElement('div');
            badgeContainer.id = 'ai-selected-nodes-container';
            badgeContainer.style.cssText = 'display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px;';

            // Insert after context badge
            contextBadge.parentElement.insertBefore(badgeContainer, contextBadge.nextSibling);
        }

        // Check if badge already exists
        if (badgeContainer.querySelector(`[data-node-id="${nodeId}"]`)) {
            return;
        }

        // Create badge
        const badge = document.createElement('div');
        badge.className = 'ai-context-node-badge';
        badge.dataset.nodeId = nodeId;

        // Icon based on node type
        const icons = {
            'Document': '📄',
            'Claim': '💡',
            'Evidence': '📊',
            'Agent': '🤖'
        };
        const icon = icons[nodeType] || '📌';

        badge.innerHTML = `
            <span>${icon}</span>
            <span class="node-title">${nodeTitle}</span>
            <button onclick="AIAssistant.removeSelectedNode('${nodeId}')" class="remove-node-btn">×</button>
        `;

        badge.style.cssText = `
            background: rgba(33, 150, 243, 0.2);
            border: 1px solid rgba(33, 150, 243, 0.5);
            border-radius: 12px;
            padding: 4px 10px;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            font-size: 12px;
            color: #64B5F6;
            animation: slideIn 0.3s ease;
        `;

        const removeBtn = badge.querySelector('.remove-node-btn');
        removeBtn.style.cssText = `
            background: none;
            border: none;
            color: #64B5F6;
            cursor: pointer;
            font-size: 16px;
            line-height: 1;
            padding: 0;
            margin-left: 4px;
        `;

        badgeContainer.appendChild(badge);

        // Add animation
        if (!document.querySelector('style#ai-badge-animations')) {
            const style = document.createElement('style');
            style.id = 'ai-badge-animations';
            style.textContent = `
                @keyframes slideIn {
                    from { opacity: 0; transform: translateX(-10px); }
                    to { opacity: 1; transform: translateX(0); }
                }
            `;
            document.head.appendChild(style);
        }

        console.log('[AIAssistant] Displayed badge for node:', nodeId);
    },

    /**
     * Update suggestions based on selected node properties
     */
    updateSuggestionsForSelectedNode(nodeDetails) {
        // Check if multiple nodes are selected
        if (this.context.selectedNodes.length > 1) {
            this.updateMultiNodeSuggestions();
            return;
        }

        const node = nodeDetails.node || {};
        const relationships = nodeDetails.relationships || {};

        // Count evidence and relationships
        const evidenceCount = relationships.HAS_EVIDENCE?.length || 0;
        const supportsCount = relationships.SUPPORTS?.length || 0;
        const contradictsCount = relationships.CONTRADICTS?.length || 0;

        const suggestions = [];

        // Determine node type
        const nodeType = (node.labels && node.labels[0]) || 'unknown';

        // Node-type specific suggestions
        if (nodeType === 'Claim') {
            // Orphaned claim (no evidence)
            if (evidenceCount === 0) {
                suggestions.push({
                    icon: '🔍',
                    text: 'Find evidence for this claim',
                    prompt: 'Search for evidence supporting this claim'
                });
                suggestions.push({
                    icon: '🤖',
                    text: 'Spawn evidence research agent',
                    prompt: 'Spawn an agent to research evidence for this claim'
                });
            }

            // Well-supported claim
            if (evidenceCount > 2) {
                suggestions.push({
                    icon: '✅',
                    text: 'Analyze evidence strength',
                    prompt: 'Analyze the strength and quality of evidence for this claim'
                });
            }

            // Find related claims
            suggestions.push({
                icon: '🔗',
                text: 'Find related claims',
                prompt: 'Find similar or related claims in the knowledge base'
                });
        } else if (nodeType === 'Document') {
            suggestions.push({
                icon: '📊',
                text: 'Summarize this document',
                prompt: 'Summarize the key findings in this document'
            });
            suggestions.push({
                icon: '💡',
                text: 'Extract key claims',
                prompt: 'Show me the key claims from this document'
            });
        } else if (nodeType === 'Evidence') {
            suggestions.push({
                icon: '🎯',
                text: 'Assess evidence credibility',
                prompt: 'Assess the credibility and strength of this evidence'
            });
        }

        // Always offer to explain the node
        suggestions.push({
            icon: '💬',
            text: 'Explain this node',
            prompt: 'Explain this node and its role in my research'
        });

        // Render the suggestions
        this.renderSuggestions(suggestions.slice(0, 4));

        console.log('[AIAssistant] Updated suggestions based on selected node');
    },

    /**
     * Update suggestions for multiple selected nodes
     */
    updateMultiNodeSuggestions() {
        const nodeCount = this.context.selectedNodes.length;
        const nodes = this.context.selectedNodes;

        // Analyze node types
        const nodeTypes = nodes.map(n => (n.node?.labels && n.node.labels[0]) || 'unknown');
        const uniqueTypes = [...new Set(nodeTypes)];

        const suggestions = [];

        // Check if all nodes are claims
        const allClaims = uniqueTypes.length === 1 && uniqueTypes[0] === 'Claim';
        const allDocuments = uniqueTypes.length === 1 && uniqueTypes[0] === 'Document';
        const mixedTypes = uniqueTypes.length > 1;

        // Comparative analysis
        suggestions.push({
            icon: '🔍',
            text: `Compare ${nodeCount} selected nodes`,
            prompt: `Compare the ${nodeCount} selected nodes and identify commonalities, differences, and relationships between them`
        });

        // Type-specific suggestions
        if (allClaims) {
            suggestions.push({
                icon: '🔗',
                text: 'Find connections between claims',
                prompt: 'Analyze the relationships between these claims and identify any logical connections or contradictions'
            });

            suggestions.push({
                icon: '🤖',
                text: 'Research knowledge gaps',
                prompt: 'Identify knowledge gaps between these claims and spawn agents to fill them'
            });

            suggestions.push({
                icon: '⚖️',
                text: 'Assess claim consistency',
                prompt: 'Evaluate whether these claims are logically consistent with each other or if there are contradictions'
            });
        } else if (allDocuments) {
            suggestions.push({
                icon: '📊',
                text: 'Synthesize findings across documents',
                prompt: 'Synthesize the key findings across these documents and identify common themes'
            });

            suggestions.push({
                icon: '🔄',
                text: 'Cross-reference citations',
                prompt: 'Check if these documents cite each other or share common references'
            });
        } else if (mixedTypes) {
            suggestions.push({
                icon: '🧩',
                text: 'Analyze node relationships',
                prompt: 'Explain how these different types of nodes relate to each other in my research'
            });

            suggestions.push({
                icon: '📈',
                text: 'Trace evidence chain',
                prompt: 'Trace the chain of evidence from documents through claims'
            });
        }

        // Render suggestions
        this.renderSuggestions(suggestions.slice(0, 4));

        console.log(`[AIAssistant] Updated suggestions for ${nodeCount} selected nodes (types: ${uniqueTypes.join(', ')})`);
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
                const chatArea = document.getElementById('ai-chat-messages-bottom');
                if (chatArea) {
                    chatArea.innerHTML = ''; // Clear welcome message

                    this.chatHistory.forEach(msg => {
                        if (msg.type === 'user') {
                            this.addUserMessage(msg.text, true);  // skipSave=true when restoring
                        } else if (msg.type === 'ai') {
                            this.addAIMessage(msg.text, msg.actions, true);  // skipSave=true when restoring
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

        const chatArea = document.getElementById('ai-chat-messages-bottom');
        if (chatArea) {
            chatArea.innerHTML = '';
        }

        this.displayWelcomeMessage();
    },

    /**
     * Show help modal with AI assistant usage instructions
     */
    showHelp() {
        const modal = document.createElement('div');
        modal.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.8); display: flex; align-items: center; justify-content: center; z-index: 10000;';

        modal.innerHTML = `
            <div style="background: #2a2a2a; padding: 32px; border-radius: 12px; max-width: 700px; max-height: 80vh; overflow-y: auto; color: white; border: 1px solid #444;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h2 style="margin: 0; color: #2196F3;">🤖 AI Research Assistant Help</h2>
                    <button onclick="this.closest('div[style*=fixed]').remove()" style="background: none; border: none; color: #999; font-size: 28px; cursor: pointer; padding: 0; width: 32px; height: 32px; line-height: 28px;">×</button>
                </div>

                <div style="margin-bottom: 24px;">
                    <h3 style="color: #64B5F6; margin-bottom: 12px;">📝 What is the AI Assistant?</h3>
                    <p style="color: #ccc; line-height: 1.6; margin: 0;">
                        Your AI Research Assistant helps you navigate, analyze, and organize your research.
                        It provides context-aware suggestions based on your current tab and can answer questions
                        about your documents, claims, evidence, and agents.
                    </p>
                </div>

                <div style="margin-bottom: 24px;">
                    <h3 style="color: #64B5F6; margin-bottom: 12px;">💡 Context-Aware Suggestions</h3>
                    <p style="color: #ccc; line-height: 1.6; margin-bottom: 12px;">
                        The AI assistant provides different suggestions based on which tab you're viewing:
                    </p>
                    <ul style="color: #ccc; line-height: 1.8; margin: 0; padding-left: 24px;">
                        <li><strong style="color: #64B5F6;">Documents:</strong> Upload, process, and search for papers</li>
                        <li><strong style="color: #64B5F6;">Graph:</strong> Find connections, contradictions, and unsupported claims</li>
                        <li><strong style="color: #64B5F6;">Agents:</strong> Monitor active agents, review results, fix failures</li>
                        <li><strong style="color: #64B5F6;">Projects:</strong> Create projects, export data, generate reports</li>
                    </ul>
                </div>

                <div style="margin-bottom: 24px;">
                    <h3 style="color: #64B5F6; margin-bottom: 12px;">🎯 How to Use</h3>
                    <ol style="color: #ccc; line-height: 1.8; margin: 0; padding-left: 24px;">
                        <li><strong style="color: white;">Click suggested prompts</strong> - Suggestion buttons auto-fill the input box. Edit if needed before sending.</li>
                        <li><strong style="color: white;">Type your own questions</strong> - Ask naturally in plain English. Examples:
                            <ul style="margin-top: 8px; margin-bottom: 8px;">
                                <li>"Find documents about transformers"</li>
                                <li>"Summarize the key claims"</li>
                                <li>"What are agents working on?"</li>
                            </ul>
                        </li>
                        <li><strong style="color: white;">Use the context badge</strong> - The blue badge shows your current tab context</li>
                    </ol>
                </div>

                <div style="margin-bottom: 24px;">
                    <h3 style="color: #64B5F6; margin-bottom: 12px;">🔧 Example Commands</h3>
                    <div style="background: #1a1a1a; padding: 16px; border-radius: 6px; font-family: monospace; font-size: 13px;">
                        <div style="margin-bottom: 8px;"><span style="color: #4CAF50;">▸</span> "Find claims that contradict each other"</div>
                        <div style="margin-bottom: 8px;"><span style="color: #4CAF50;">▸</span> "Show me the strongest evidence"</div>
                        <div style="margin-bottom: 8px;"><span style="color: #4CAF50;">▸</span> "Process all pending documents"</div>
                        <div style="margin-bottom: 8px;"><span style="color: #4CAF50;">▸</span> "What are the research gaps?"</div>
                        <div><span style="color: #4CAF50;">▸</span> "Spawn a research agent to find evidence"</div>
                    </div>
                </div>

                <div style="margin-bottom: 24px;">
                    <h3 style="color: #64B5F6; margin-bottom: 12px;">⚡ Tips & Tricks</h3>
                    <ul style="color: #ccc; line-height: 1.8; margin: 0; padding-left: 24px;">
                        <li>Suggestions update automatically when you switch tabs</li>
                        <li>Suggestions show real counts (e.g., "Process 3 pending documents")</li>
                        <li>Click suggested prompts to edit them before sending</li>
                        <li>The assistant remembers recent conversations</li>
                        <li>Ask follow-up questions for deeper analysis</li>
                    </ul>
                </div>

                <div style="background: rgba(33, 150, 243, 0.1); padding: 16px; border-radius: 6px; border-left: 3px solid #2196F3;">
                    <p style="color: #64B5F6; margin: 0; font-size: 13px;">
                        <strong>💬 Need more help?</strong> Just ask! Type "help" in the chat for assistance
                        or ask specific questions about features you want to understand.
                    </p>
                </div>

                <button onclick="this.closest('div[style*=fixed]').remove()" style="width: 100%; padding: 12px; margin-top: 24px; background: #2196F3; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 14px;">
                    Got it, thanks!
                </button>
            </div>
        `;

        // Close on click outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });

        document.body.appendChild(modal);
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        AIAssistant.init();
    }, 250);
});
