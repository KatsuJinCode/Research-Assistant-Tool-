/**
 * Agent Animation Engine - Core system for game-like graph visualization
 *
 * This module provides the foundation for animated AI agents that navigate
 * the knowledge graph like characters in a game. It manages agent lifecycle,
 * rendering, state management, and coordinates with other animation systems.
 */

class AgentAnimationEngine {
    constructor(graphRenderer) {
        this.graphRenderer = graphRenderer;
        this.agents = new Map(); // agent_id -> AgentAvatar
        this.animationLayer = null;
        this.isRunning = false;
        this.lastFrameTime = 0;
        this.targetFPS = 60;
        this.frameInterval = 1000 / this.targetFPS;
        this.animationFrameId = null;

        // Configuration
        this.config = {
            enabled: true,
            speed: 1.0, // Animation speed multiplier
            quality: 'high', // low, medium, high
            maxAgents: 10,
            showPaths: true,
            showThoughts: true,
            enableParticles: true
        };

        // Activity log
        this.activityLog = [];
        this.maxLogEntries = 100;

        // Event handlers
        this.eventHandlers = new Map();

        this.initialize();
    }

    /**
     * Initialize the animation system
     */
    initialize() {
        console.log('[AgentAnimation] Initializing animation engine...');

        // Create animation layer on top of graph
        this.createAnimationLayer();

        // Load settings from localStorage
        this.loadSettings();

        // Set up event listeners
        this.setupEventListeners();

        console.log('[AgentAnimation] Engine initialized');
    }

    /**
     * Create SVG animation layer on top of existing graph
     */
    createAnimationLayer() {
        const svg = d3.select('#graph-svg');

        // Create dedicated animation group
        let animationGroup = svg.select('.animation-layer');
        if (animationGroup.empty()) {
            // Insert after the graph group so animations appear on top
            animationGroup = svg.append('g')
                .attr('class', 'animation-layer');
        }

        // Create sub-layers for different visual elements
        animationGroup.append('g').attr('class', 'paths-layer');
        animationGroup.append('g').attr('class', 'particles-layer');
        animationGroup.append('g').attr('class', 'agents-layer');
        animationGroup.append('g').attr('class', 'effects-layer');

        this.animationLayer = animationGroup;

        console.log('[AgentAnimation] Animation layer created');
    }

    /**
     * Start the animation loop
     */
    start() {
        if (this.isRunning) return;

        console.log('[AgentAnimation] Starting animation loop...');
        this.isRunning = true;
        this.lastFrameTime = performance.now();
        this.animate();
    }

    /**
     * Stop the animation loop
     */
    stop() {
        if (!this.isRunning) return;

        console.log('[AgentAnimation] Stopping animation loop...');
        this.isRunning = false;

        if (this.animationFrameId) {
            cancelAnimationFrame(this.animationFrameId);
            this.animationFrameId = null;
        }
    }

    /**
     * Main animation loop (60 FPS)
     */
    animate(currentTime = performance.now()) {
        if (!this.isRunning) return;

        // Calculate delta time
        const deltaTime = currentTime - this.lastFrameTime;

        // Only update if enough time has passed (frame limiting)
        if (deltaTime >= this.frameInterval) {
            this.lastFrameTime = currentTime - (deltaTime % this.frameInterval);

            // Update all agents
            this.updateAgents(deltaTime / 1000); // Convert to seconds

            // Update particle effects
            if (this.config.enableParticles && window.ParticleEffects) {
                window.ParticleEffects.update(deltaTime / 1000);
            }
        }

        // Schedule next frame
        this.animationFrameId = requestAnimationFrame((time) => this.animate(time));
    }

    /**
     * Update all agents
     */
    updateAgents(deltaTime) {
        this.agents.forEach((agent, agentId) => {
            agent.update(deltaTime * this.config.speed);
        });
    }

    /**
     * Create a new agent avatar
     */
    createAgent(config) {
        const {
            agent_id,
            type = 'researcher',
            startNodeId = null,
            targetNodeId = null,
            personality = {}
        } = config;

        // Don't exceed max agents
        if (this.agents.size >= this.config.maxAgents) {
            console.warn('[AgentAnimation] Max agents reached, removing oldest');
            const oldestId = Array.from(this.agents.keys())[0];
            this.removeAgent(oldestId);
        }

        // Create agent avatar
        const agent = new AgentAvatar({
            id: agent_id,
            type: type,
            graphRenderer: this.graphRenderer,
            animationEngine: this,
            startNodeId: startNodeId,
            targetNodeId: targetNodeId,
            personality: personality
        });

        this.agents.set(agent_id, agent);

        // Log activity
        this.logActivity(`Agent ${agent.getDisplayName()} spawned`, 'spawn', agent_id);

        // Start animation loop if not running
        if (!this.isRunning) {
            this.start();
        }

        console.log(`[AgentAnimation] Created agent: ${agent_id} (${type})`);
        return agent;
    }

    /**
     * Remove an agent
     */
    removeAgent(agentId) {
        const agent = this.agents.get(agentId);
        if (!agent) return;

        // Fade out and remove
        agent.destroy();
        this.agents.delete(agentId);

        this.logActivity(`Agent ${agent.getDisplayName()} removed`, 'remove', agentId);

        // Stop animation if no agents left
        if (this.agents.size === 0) {
            this.stop();
        }

        console.log(`[AgentAnimation] Removed agent: ${agentId}`);
    }

    /**
     * Get agent by ID
     */
    getAgent(agentId) {
        return this.agents.get(agentId);
    }

    /**
     * Get all agents at a specific node
     */
    getAgentsAtNode(nodeId) {
        return Array.from(this.agents.values())
            .filter(agent => agent.currentNodeId === nodeId);
    }

    /**
     * Move agent to a target node
     */
    moveAgent(agentId, targetNodeId) {
        const agent = this.agents.get(agentId);
        if (!agent) {
            console.warn(`[AgentAnimation] Agent ${agentId} not found`);
            return;
        }

        agent.setTarget(targetNodeId);
        this.logActivity(`Agent ${agent.getDisplayName()} moving to node`, 'move', agentId);
    }

    /**
     * Set agent action/state
     */
    setAgentAction(agentId, action, metadata = {}) {
        const agent = this.agents.get(agentId);
        if (!agent) return;

        agent.setAction(action, metadata);
        this.logActivity(`Agent ${agent.getDisplayName()}: ${action}`, action, agentId);
    }

    /**
     * Log an activity
     */
    logActivity(message, type, agentId = null) {
        const entry = {
            timestamp: Date.now(),
            message: message,
            type: type,
            agentId: agentId
        };

        this.activityLog.unshift(entry);

        // Limit log size
        if (this.activityLog.length > this.maxLogEntries) {
            this.activityLog.pop();
        }

        // Emit event for UI updates
        this.emit('activityLogged', entry);
    }

    /**
     * Get recent activity log
     */
    getActivityLog(limit = 20) {
        return this.activityLog.slice(0, limit);
    }

    /**
     * Clear all agents
     */
    clearAllAgents() {
        console.log('[AgentAnimation] Clearing all agents...');

        this.agents.forEach((agent, agentId) => {
            agent.destroy();
        });

        this.agents.clear();
        this.stop();

        this.logActivity('All agents cleared', 'clear');
    }

    /**
     * Update configuration
     */
    updateConfig(updates) {
        Object.assign(this.config, updates);
        this.saveSettings();

        // Apply changes
        if (updates.enabled !== undefined) {
            if (updates.enabled && this.agents.size > 0) {
                this.start();
            } else if (!updates.enabled) {
                this.stop();
            }
        }

        this.emit('configUpdated', this.config);
    }

    /**
     * Save settings to localStorage
     */
    saveSettings() {
        try {
            localStorage.setItem('agentAnimationConfig', JSON.stringify(this.config));
        } catch (error) {
            console.warn('[AgentAnimation] Failed to save settings:', error);
        }
    }

    /**
     * Load settings from localStorage
     */
    loadSettings() {
        try {
            const saved = localStorage.getItem('agentAnimationConfig');
            if (saved) {
                const config = JSON.parse(saved);
                Object.assign(this.config, config);
                console.log('[AgentAnimation] Loaded settings:', config);
            }
        } catch (error) {
            console.warn('[AgentAnimation] Failed to load settings:', error);
        }
    }

    /**
     * Event system - register handler
     */
    on(event, handler) {
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, []);
        }
        this.eventHandlers.get(event).push(handler);
    }

    /**
     * Event system - emit event
     */
    emit(event, data) {
        const handlers = this.eventHandlers.get(event);
        if (handlers) {
            handlers.forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`[AgentAnimation] Error in event handler for ${event}:`, error);
                }
            });
        }
    }

    /**
     * Set up global event listeners
     */
    setupEventListeners() {
        // Listen for graph updates
        document.addEventListener('graphUpdated', (event) => {
            // Update agent positions if nodes moved
            this.handleGraphUpdate(event.detail);
        });

        // Listen for window visibility changes (pause when hidden)
        document.addEventListener('visibilitychange', () => {
            if (document.hidden && this.isRunning) {
                this.stop();
            } else if (!document.hidden && this.agents.size > 0 && this.config.enabled) {
                this.start();
            }
        });
    }

    /**
     * Handle graph updates (node positions changed, etc.)
     */
    handleGraphUpdate(detail) {
        // Update agent positions to match graph layout
        this.agents.forEach(agent => {
            agent.updatePositionFromGraph();
        });
    }

    /**
     * Get animation statistics
     */
    getStats() {
        return {
            agentCount: this.agents.size,
            isRunning: this.isRunning,
            fps: Math.round(1000 / this.frameInterval),
            config: this.config,
            activityLogSize: this.activityLog.length
        };
    }

    /**
     * Enable/disable animation system
     */
    toggle() {
        this.config.enabled = !this.config.enabled;
        if (this.config.enabled && this.agents.size > 0) {
            this.start();
        } else {
            this.stop();
        }
        this.saveSettings();
        this.emit('toggled', this.config.enabled);
    }
}

/**
 * Agent Avatar - Represents an individual animated agent
 */
class AgentAvatar {
    constructor(config) {
        this.id = config.id;
        this.type = config.type;
        this.graphRenderer = config.graphRenderer;
        this.animationEngine = config.animationEngine;
        this.personality = config.personality || {};

        // Position and movement
        this.currentNodeId = config.startNodeId;
        this.targetNodeId = config.targetNodeId;
        this.position = { x: 0, y: 0 };
        this.velocity = { x: 0, y: 0 };
        this.path = []; // Array of node IDs to traverse
        this.pathIndex = 0;

        // State
        this.currentAction = 'idle';
        this.actionMetadata = {};
        this.thoughtBubble = null;

        // Visual properties
        this.sprite = null;
        this.element = null;

        // Timing
        this.idleTimer = 0;
        this.actionTimer = 0;

        this.initialize();
    }

    /**
     * Initialize the agent avatar
     */
    initialize() {
        // Get starting position from node
        if (this.currentNodeId) {
            const node = this.graphRenderer.currentGraphData.nodes.find(n => n.id === this.currentNodeId);
            if (node) {
                this.position.x = node.x || 0;
                this.position.y = node.y || 0;
            }
        }

        // Create visual representation
        this.createSprite();

        // If we have a target, start moving
        if (this.targetNodeId) {
            this.setTarget(this.targetNodeId);
        }
    }

    /**
     * Create the sprite (visual representation)
     */
    createSprite() {
        const agentsLayer = d3.select('.agents-layer');

        // Create agent group
        const group = agentsLayer.append('g')
            .attr('class', `agent-sprite agent-${this.type}`)
            .attr('data-agent-id', this.id)
            .attr('transform', `translate(${this.position.x}, ${this.position.y})`);

        // Get agent appearance based on type
        const appearance = this.getAppearance();

        // Create circle background
        group.append('circle')
            .attr('r', appearance.radius)
            .attr('fill', appearance.color)
            .attr('stroke', '#fff')
            .attr('stroke-width', 2)
            .attr('class', 'agent-body')
            .style('filter', 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))');

        // Add emoji/icon
        group.append('text')
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'central')
            .attr('font-size', `${appearance.radius * 1.2}px`)
            .attr('class', 'agent-icon')
            .text(appearance.icon);

        // Add name label
        group.append('text')
            .attr('text-anchor', 'middle')
            .attr('y', appearance.radius + 15)
            .attr('font-size', '10px')
            .attr('font-weight', 'bold')
            .attr('fill', '#fff')
            .attr('class', 'agent-label')
            .style('text-shadow', '0 1px 2px rgba(0,0,0,0.8)')
            .text(this.getDisplayName());

        this.element = group;

        // Spawn animation
        this.playSpawnAnimation();
    }

    /**
     * Get visual appearance based on agent type
     */
    getAppearance() {
        const appearances = {
            'researcher': { icon: '🔬', color: '#2196F3', radius: 18 },
            'critic': { icon: '⚖️', color: '#F44336', radius: 18 },
            'synthesizer': { icon: '🔗', color: '#9C27B0', radius: 18 },
            'validator': { icon: '✓', color: '#4CAF50', radius: 18 },
            'explorer': { icon: '🔍', color: '#FF9800', radius: 18 },
            'specialist': { icon: '🎯', color: '#00BCD4', radius: 18 }
        };

        return appearances[this.type] || { icon: '🤖', color: '#757575', radius: 18 };
    }

    /**
     * Get display name
     */
    getDisplayName() {
        const names = {
            'researcher': 'Dr. Research',
            'critic': 'Prof. Skeptic',
            'synthesizer': 'Syn-thesis',
            'validator': 'Val-idator',
            'explorer': 'Scout',
            'specialist': 'Expert'
        };

        return names[this.type] || 'Agent';
    }

    /**
     * Update agent state each frame
     */
    update(deltaTime) {
        // Update action timer
        this.actionTimer += deltaTime;

        // Handle current action
        switch (this.currentAction) {
            case 'idle':
                this.updateIdle(deltaTime);
                break;
            case 'moving':
                this.updateMoving(deltaTime);
                break;
            case 'analyzing':
                this.updateAnalyzing(deltaTime);
                break;
            case 'debating':
                this.updateDebating(deltaTime);
                break;
        }

        // Update position
        this.updatePosition(deltaTime);
    }

    /**
     * Update idle behavior
     */
    updateIdle(deltaTime) {
        this.idleTimer += deltaTime;

        // Gentle bobbing animation
        const bobOffset = Math.sin(this.idleTimer * 2) * 2;
        this.element.select('.agent-body')
            .attr('cy', bobOffset);
        this.element.select('.agent-icon')
            .attr('y', bobOffset);
    }

    /**
     * Update moving behavior
     */
    updateMoving(deltaTime) {
        if (this.path.length === 0 || this.pathIndex >= this.path.length) {
            // Reached destination
            this.setAction('idle');
            return;
        }

        // Get current target node
        const targetNodeId = this.path[this.pathIndex];
        const targetNode = this.graphRenderer.currentGraphData.nodes.find(n => n.id === targetNodeId);

        if (!targetNode) {
            console.warn(`[AgentAvatar] Target node ${targetNodeId} not found`);
            this.setAction('idle');
            return;
        }

        // Calculate direction and distance
        const dx = targetNode.x - this.position.x;
        const dy = targetNode.y - this.position.y;
        const distance = Math.sqrt(dx * dx + dy * dy);

        // Movement speed based on personality
        const baseSpeed = this.personality.speed || this.getTypeSpeed();
        const speed = baseSpeed * deltaTime * 60; // Normalize for 60 FPS

        if (distance < speed) {
            // Reached node
            this.position.x = targetNode.x;
            this.position.y = targetNode.y;
            this.currentNodeId = targetNodeId;
            this.pathIndex++;

            // Emit arrival event
            this.animationEngine.emit('agentArrived', {
                agentId: this.id,
                nodeId: targetNodeId
            });

            // Play arrival animation
            this.playArrivalAnimation();
        } else {
            // Move towards target
            this.velocity.x = (dx / distance) * speed;
            this.velocity.y = (dy / distance) * speed;

            // Add walking animation (rotation based on direction)
            const angle = Math.atan2(dy, dx) * (180 / Math.PI);
            this.element.select('.agent-icon')
                .attr('transform', `rotate(${angle % 360})`);
        }
    }

    /**
     * Update analyzing behavior
     */
    updateAnalyzing(deltaTime) {
        // Pulsing animation
        const scale = 1 + Math.sin(this.actionTimer * 4) * 0.1;
        this.element.select('.agent-body')
            .attr('transform', `scale(${scale})`);
    }

    /**
     * Update debating behavior
     */
    updateDebating(deltaTime) {
        // Rapid pulsing
        const scale = 1 + Math.sin(this.actionTimer * 8) * 0.15;
        this.element.select('.agent-body')
            .attr('transform', `scale(${scale})`);
    }

    /**
     * Update visual position
     */
    updatePosition(deltaTime) {
        this.position.x += this.velocity.x;
        this.position.y += this.velocity.y;

        // Damping
        this.velocity.x *= 0.9;
        this.velocity.y *= 0.9;

        // Update DOM
        this.element.attr('transform', `translate(${this.position.x}, ${this.position.y})`);
    }

    /**
     * Set target node (triggers pathfinding)
     */
    setTarget(targetNodeId) {
        this.targetNodeId = targetNodeId;

        // Calculate path
        if (window.AgentMovement) {
            this.path = window.AgentMovement.findPath(
                this.currentNodeId,
                targetNodeId,
                this.graphRenderer.currentGraphData
            );
        } else {
            // Simple direct path
            this.path = [targetNodeId];
        }

        this.pathIndex = 0;
        this.setAction('moving');
    }

    /**
     * Set current action
     */
    setAction(action, metadata = {}) {
        this.currentAction = action;
        this.actionMetadata = metadata;
        this.actionTimer = 0;

        // Update visual appearance
        this.element.attr('class', `agent-sprite agent-${this.type} action-${action}`);

        // Show thought bubble if applicable
        if (metadata.thought) {
            this.showThought(metadata.thought);
        }
    }

    /**
     * Show thought bubble
     */
    showThought(text) {
        // Remove existing thought
        if (this.thoughtBubble) {
            this.thoughtBubble.remove();
        }

        // Create thought bubble
        const bubble = this.element.append('g')
            .attr('class', 'thought-bubble')
            .attr('transform', 'translate(0, -30)');

        // Background
        bubble.append('rect')
            .attr('x', -40)
            .attr('y', -15)
            .attr('width', 80)
            .attr('height', 30)
            .attr('rx', 15)
            .attr('fill', 'rgba(255, 255, 255, 0.95)')
            .attr('stroke', '#333')
            .attr('stroke-width', 1);

        // Text
        bubble.append('text')
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'central')
            .attr('font-size', '10px')
            .attr('fill', '#333')
            .text(text.length > 15 ? text.substring(0, 15) + '...' : text);

        this.thoughtBubble = bubble;

        // Auto-hide after 3 seconds
        setTimeout(() => {
            if (this.thoughtBubble) {
                this.thoughtBubble.transition()
                    .duration(500)
                    .style('opacity', 0)
                    .remove();
                this.thoughtBubble = null;
            }
        }, 3000);
    }

    /**
     * Play spawn animation
     */
    playSpawnAnimation() {
        this.element
            .style('opacity', 0)
            .transition()
            .duration(500)
            .style('opacity', 1)
            .select('.agent-body')
            .attr('r', 0)
            .transition()
            .duration(500)
            .attr('r', this.getAppearance().radius);
    }

    /**
     * Play arrival animation (bounce)
     */
    playArrivalAnimation() {
        const radius = this.getAppearance().radius;
        this.element.select('.agent-body')
            .transition()
            .duration(150)
            .attr('r', radius * 1.3)
            .transition()
            .duration(150)
            .attr('r', radius);
    }

    /**
     * Get type-specific speed
     */
    getTypeSpeed() {
        const speeds = {
            'researcher': 80,  // Methodical, slow
            'critic': 120,     // Fast, direct
            'synthesizer': 100, // Moderate
            'validator': 90,   // Thorough
            'explorer': 140,   // Very fast
            'specialist': 85   // Slow, careful
        };

        return speeds[this.type] || 100;
    }

    /**
     * Update position from graph (in case graph layout changed)
     */
    updatePositionFromGraph() {
        if (this.currentNodeId) {
            const node = this.graphRenderer.currentGraphData.nodes.find(n => n.id === this.currentNodeId);
            if (node && (node.x !== this.position.x || node.y !== this.position.y)) {
                this.position.x = node.x;
                this.position.y = node.y;
            }
        }
    }

    /**
     * Destroy the agent (cleanup)
     */
    destroy() {
        if (this.element) {
            this.element
                .transition()
                .duration(500)
                .style('opacity', 0)
                .remove();
        }

        if (this.thoughtBubble) {
            this.thoughtBubble.remove();
        }
    }
}

// Export to global scope
window.AgentAnimationEngine = AgentAnimationEngine;
window.AgentAvatar = AgentAvatar;
