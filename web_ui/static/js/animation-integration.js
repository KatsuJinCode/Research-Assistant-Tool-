/**
 * Animation System Integration
 *
 * Integrates the agent animation system with the existing graph renderer
 * and sets up all necessary connections.
 */

(function() {
    'use strict';

    // Global animation engine instance
    window.animationEngine = null;

    /**
     * Initialize the animation system when the graph is ready
     */
    function initializeAnimationSystem() {
        console.log('[AnimationIntegration] Initializing animation system...');

        // Wait for GraphRenderer to be ready
        if (typeof GraphRenderer === 'undefined') {
            console.warn('[AnimationIntegration] GraphRenderer not ready, retrying...');
            setTimeout(initializeAnimationSystem, 500);
            return;
        }

        try {
            // Create animation engine
            window.animationEngine = new AgentAnimationEngine(GraphRenderer);

            // Create debate system
            if (typeof DebateSystem !== 'undefined') {
                window.animationEngine.debateSystem = new DebateSystem(window.animationEngine);
            }

            // Create API visualization system
            if (typeof APIVisualizationSystem !== 'undefined') {
                window.animationEngine.apiSystem = new APIVisualizationSystem(GraphRenderer);
            }

            // Initialize controls
            if (typeof initializeControls === 'function') {
                initializeControls(window.animationEngine);
            }

            // Set up WebSocket event handlers for real-time agent updates
            setupWebSocketHandlers();

            // Set up graph event handlers
            setupGraphEventHandlers();

            console.log('[AnimationIntegration] Animation system initialized successfully');

            // Show notification
            if (typeof UI !== 'undefined' && typeof UI.showNotification === 'function') {
                UI.showNotification('Animation system ready! Click the game controller icon to start.', 'success');
            }

        } catch (error) {
            console.error('[AnimationIntegration] Failed to initialize:', error);
        }
    }

    /**
     * Set up WebSocket handlers for real-time agent updates
     */
    function setupWebSocketHandlers() {
        if (typeof socket === 'undefined') {
            console.warn('[AnimationIntegration] Socket.io not available');
            return;
        }

        // Listen for agent spawn events
        socket.on('agent_spawned', (data) => {
            console.log('[AnimationIntegration] Agent spawned:', data);

            if (window.animationEngine && data.agent_id) {
                window.animationEngine.createAgent({
                    agent_id: data.agent_id,
                    type: data.type || 'researcher',
                    startNodeId: data.start_node_id,
                    targetNodeId: data.target_node_id
                });
            }
        });

        // Listen for agent movement events
        socket.on('agent_moved', (data) => {
            if (window.animationEngine && data.agent_id && data.target_node_id) {
                window.animationEngine.moveAgent(data.agent_id, data.target_node_id);
            }
        });

        // Listen for agent action events
        socket.on('agent_action', (data) => {
            if (window.animationEngine && data.agent_id && data.action) {
                window.animationEngine.setAgentAction(data.agent_id, data.action, data.metadata || {});
            }
        });

        // Listen for debate events
        socket.on('debate_started', (data) => {
            if (window.animationEngine && window.animationEngine.debateSystem) {
                window.animationEngine.debateSystem.startDebate({
                    nodeId: data.node_id,
                    participants: data.participants || [],
                    mode: data.mode || 'competitive',
                    topic: data.topic || 'Node evaluation'
                });
            }
        });

        // Listen for API request events
        socket.on('api_request', (data) => {
            if (window.animationEngine && window.animationEngine.apiSystem) {
                window.animationEngine.apiSystem.visualizeRequest({
                    apiNodeId: data.api_node_id,
                    targetNodeId: data.target_node_id,
                    query: data.query,
                    status: data.status || 'pending'
                });
            }
        });

        console.log('[AnimationIntegration] WebSocket handlers configured');
    }

    /**
     * Set up graph event handlers
     */
    function setupGraphEventHandlers() {
        // Listen for node additions (trigger particle effects)
        document.addEventListener('nodeAdded', (event) => {
            if (!window.animationEngine || !window.animationEngine.config.enableParticles) return;

            const nodeData = event.detail;
            if (nodeData && nodeData.position) {
                // Spawn effect when new node is added
                if (window.ParticleEffects) {
                    window.ParticleEffects.createSuccessEffect(
                        nodeData.position.x,
                        nodeData.position.y
                    );
                }
            }
        });

        // Listen for processing updates (add visual effects)
        document.addEventListener('nodeProcessing', (event) => {
            if (!window.animationEngine || !window.animationEngine.config.enableParticles) return;

            const { nodeId, stage } = event.detail;
            const node = GraphRenderer.currentGraphData.nodes.find(n => n.id === nodeId);

            if (node && window.ParticleEffects) {
                // Create sparks during processing
                const stopSparks = window.ParticleEffects.createSparks(nodeId, GraphRenderer);

                // Store cleanup function
                if (!window.activeEffects) {
                    window.activeEffects = new Map();
                }
                window.activeEffects.set(nodeId, stopSparks);
            }
        });

        // Listen for processing completion
        document.addEventListener('nodeProcessingComplete', (event) => {
            const { nodeId } = event.detail;

            // Stop sparks
            if (window.activeEffects && window.activeEffects.has(nodeId)) {
                const stopSparks = window.activeEffects.get(nodeId);
                if (stopSparks) stopSparks();
                window.activeEffects.delete(nodeId);
            }

            // Success effect
            const node = GraphRenderer.currentGraphData.nodes.find(n => n.id === nodeId);
            if (node && window.ParticleEffects && window.animationEngine?.config.enableParticles) {
                window.ParticleEffects.createSuccessEffect(node.x, node.y);
            }
        });

        console.log('[AnimationIntegration] Graph event handlers configured');
    }

    /**
     * Add keyboard shortcuts for animation controls
     */
    function setupKeyboardShortcuts() {
        document.addEventListener('keydown', (event) => {
            // Ctrl + Shift + A - Toggle animation panel
            if (event.ctrlKey && event.shiftKey && event.key === 'A') {
                event.preventDefault();
                toggleControlPanel();
            }

            // Ctrl + Shift + D - Start demo
            if (event.ctrlKey && event.shiftKey && event.key === 'D') {
                event.preventDefault();
                if (typeof startDemo === 'function') {
                    startDemo();
                }
            }

            // Ctrl + Shift + C - Clear agents
            if (event.ctrlKey && event.shiftKey && event.key === 'C') {
                event.preventDefault();
                if (window.animationEngine) {
                    window.animationEngine.clearAllAgents();
                }
            }

            // Ctrl + Shift + S - Spawn random agent
            if (event.ctrlKey && event.shiftKey && event.key === 'S') {
                event.preventDefault();
                if (typeof spawnAgent === 'function') {
                    spawnAgent();
                }
            }
        });

        console.log('[AnimationIntegration] Keyboard shortcuts configured');
    }

    /**
     * Add helper functions to GraphRenderer for animation integration
     */
    function extendGraphRenderer() {
        if (typeof GraphRenderer === 'undefined') return;

        // Add method to get node by ID with position
        GraphRenderer.getNodeWithPosition = function(nodeId) {
            const node = this.currentGraphData.nodes.find(n => n.id === nodeId);
            if (node && node.x !== undefined && node.y !== undefined) {
                return {
                    id: node.id,
                    type: node.type,
                    position: { x: node.x, y: node.y },
                    data: node.fullData
                };
            }
            return null;
        };

        // Add method to spawn agent at node
        GraphRenderer.spawnAgentAtNode = function(nodeId, agentType = 'researcher') {
            if (!window.animationEngine) return null;

            return window.animationEngine.createAgent({
                agent_id: `agent_${Date.now()}`,
                type: agentType,
                startNodeId: nodeId
            });
        };

        // Add method to visualize API call
        GraphRenderer.visualizeAPICall = function(sourceNodeId, targetNodeId, apiSource = 'API') {
            if (!window.animationEngine || !window.animationEngine.apiSystem) return;

            // Create API node if it doesn't exist
            const apiNodeId = `api_${apiSource.toLowerCase()}`;
            let apiNode = window.animationEngine.apiSystem.apiNodes.get(apiNodeId);

            if (!apiNode) {
                const sourceNode = this.currentGraphData.nodes.find(n => n.id === sourceNodeId);
                apiNode = window.animationEngine.apiSystem.createAPINode({
                    id: apiNodeId,
                    source: apiSource,
                    position: sourceNode ? { x: sourceNode.x - 100, y: sourceNode.y } : { x: 0, y: 0 }
                });
            }

            // Visualize request
            window.animationEngine.apiSystem.visualizeRequest({
                apiNodeId: apiNodeId,
                targetNodeId: targetNodeId,
                query: 'Research query',
                status: 'pending'
            });
        };

        console.log('[AnimationIntegration] GraphRenderer extended with animation methods');
    }

    /**
     * Initialize everything when DOM is ready
     */
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            initializeAnimationSystem();
            setupKeyboardShortcuts();
            extendGraphRenderer();
        });
    } else {
        // DOM already loaded
        initializeAnimationSystem();
        setupKeyboardShortcuts();
        extendGraphRenderer();
    }

    // Export utility functions
    window.AnimationIntegration = {
        initialize: initializeAnimationSystem,
        setupWebSocket: setupWebSocketHandlers,
        setupGraph: setupGraphEventHandlers
    };

})();
