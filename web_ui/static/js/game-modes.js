/**
 * Game Modes & Agent Profiles
 *
 * Defines different visualization modes and agent personality profiles
 * for various research exploration scenarios.
 */

class GameModeManager {
    constructor(animationEngine) {
        this.animationEngine = animationEngine;
        this.currentMode = null;
        this.modes = this.initializeModes();
        this.agentProfiles = this.initializeAgentProfiles();
    }

    /**
     * Initialize available game modes
     */
    initializeModes() {
        return {
            'research': new ResearchMode(this.animationEngine),
            'debate': new DebateMode(this.animationEngine),
            'collaborative': new CollaborativeMode(this.animationEngine),
            'tournament': new TournamentMode(this.animationEngine),
            'speedrun': new SpeedRunMode(this.animationEngine),
            'exploration': new ExplorationMode(this.animationEngine)
        };
    }

    /**
     * Initialize agent personality profiles
     */
    initializeAgentProfiles() {
        return {
            'dr_skeptic': {
                name: 'Dr. Skeptic',
                type: 'critic',
                personality: {
                    speed: 120,
                    thoroughness: 0.9,
                    criticality: 0.95,
                    collaboration: 0.3
                },
                behavior: 'Always challenges claims and demands strong evidence',
                color: '#F44336',
                icon: '⚖️'
            },
            'prof_evidence': {
                name: 'Professor Evidence',
                type: 'validator',
                personality: {
                    speed: 80,
                    thoroughness: 0.95,
                    criticality: 0.7,
                    collaboration: 0.6
                },
                behavior: 'Meticulously verifies every claim with evidence',
                color: '#4CAF50',
                icon: '✓'
            },
            'rapid_reader': {
                name: 'Rapid Reader',
                type: 'explorer',
                personality: {
                    speed: 150,
                    thoroughness: 0.4,
                    criticality: 0.3,
                    collaboration: 0.5
                },
                behavior: 'Quickly scans for interesting patterns',
                color: '#FF9800',
                icon: '🔍'
            },
            'deep_thinker': {
                name: 'Deep Thinker',
                type: 'researcher',
                personality: {
                    speed: 60,
                    thoroughness: 0.98,
                    criticality: 0.6,
                    collaboration: 0.7
                },
                behavior: 'Slow but extremely thorough analysis',
                color: '#2196F3',
                icon: '🔬'
            },
            'team_player': {
                name: 'Team Player',
                type: 'synthesizer',
                personality: {
                    speed: 100,
                    thoroughness: 0.7,
                    criticality: 0.4,
                    collaboration: 0.95
                },
                behavior: 'Focuses on connecting ideas and building consensus',
                color: '#9C27B0',
                icon: '🔗'
            },
            'specialist': {
                name: 'Domain Expert',
                type: 'specialist',
                personality: {
                    speed: 85,
                    thoroughness: 0.85,
                    criticality: 0.75,
                    collaboration: 0.6
                },
                behavior: 'Deep expertise in specific domains',
                color: '#00BCD4',
                icon: '🎯'
            }
        };
    }

    /**
     * Activate a game mode
     */
    activateMode(modeId, config = {}) {
        // Deactivate current mode
        if (this.currentMode) {
            this.currentMode.deactivate();
        }

        const mode = this.modes[modeId];
        if (!mode) {
            console.error(`[GameMode] Unknown mode: ${modeId}`);
            return;
        }

        mode.activate(config);
        this.currentMode = mode;

        console.log(`[GameMode] Activated mode: ${modeId}`);

        // Emit event
        this.animationEngine.emit('modeChanged', {
            mode: modeId,
            config: config
        });
    }

    /**
     * Get current mode
     */
    getCurrentMode() {
        return this.currentMode;
    }

    /**
     * Get agent profile
     */
    getAgentProfile(profileId) {
        return this.agentProfiles[profileId];
    }

    /**
     * Create agent with specific profile
     */
    createProfiledAgent(profileId, config = {}) {
        const profile = this.agentProfiles[profileId];
        if (!profile) {
            console.error(`[GameMode] Unknown profile: ${profileId}`);
            return null;
        }

        return this.animationEngine.createAgent({
            agent_id: config.agent_id || `agent_${Date.now()}`,
            type: profile.type,
            personality: profile.personality,
            ...config
        });
    }
}

/**
 * Base Game Mode Class
 */
class GameMode {
    constructor(animationEngine) {
        this.animationEngine = animationEngine;
        this.isActive = false;
        this.config = {};
    }

    activate(config) {
        this.isActive = true;
        this.config = config;
        console.log(`[${this.constructor.name}] Activated`);
    }

    deactivate() {
        this.isActive = false;
        console.log(`[${this.constructor.name}] Deactivated`);
    }

    update(deltaTime) {
        // Override in subclasses
    }
}

/**
 * Research Mode - Single agent methodical exploration
 */
class ResearchMode extends GameMode {
    activate(config) {
        super.activate(config);

        // Clear existing agents
        this.animationEngine.clearAllAgents();

        // Create a single researcher agent
        const startNodeId = config.startNodeId || this.getRandomNode();

        this.agent = this.animationEngine.createAgent({
            agent_id: 'researcher_1',
            type: 'researcher',
            startNodeId: startNodeId,
            personality: {
                speed: 90,
                thoroughness: 0.85
            }
        });

        // Set up methodical exploration pattern
        this.setupExplorationPattern(startNodeId);
    }

    setupExplorationPattern(startNodeId) {
        // Breadth-first exploration of graph
        const graphData = this.animationEngine.graphRenderer.currentGraphData;
        const visited = new Set([startNodeId]);
        const queue = [startNodeId];

        const explore = () => {
            if (queue.length === 0 || !this.isActive) return;

            const currentId = queue.shift();

            // Find unvisited neighbors
            const neighbors = graphData.links
                .filter(l => {
                    const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
                    const targetId = typeof l.target === 'object' ? l.target.id : l.target;
                    return sourceId === currentId || targetId === currentId;
                })
                .map(l => {
                    const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
                    const targetId = typeof l.target === 'object' ? l.target.id : l.target;
                    return sourceId === currentId ? targetId : sourceId;
                })
                .filter(id => !visited.has(id));

            // Add to queue
            neighbors.forEach(id => {
                if (!visited.has(id)) {
                    visited.add(id);
                    queue.push(id);
                }
            });

            // Move to next node
            if (queue.length > 0) {
                this.animationEngine.moveAgent('researcher_1', queue[0]);
                this.animationEngine.setAgentAction('researcher_1', 'analyzing', {
                    thought: 'Analyzing claim...'
                });

                // Continue after delay
                setTimeout(explore, 3000);
            }
        };

        // Start exploration
        setTimeout(explore, 1000);
    }

    getRandomNode() {
        const nodes = this.animationEngine.graphRenderer.currentGraphData.nodes;
        return nodes[Math.floor(Math.random() * nodes.length)]?.id;
    }

    deactivate() {
        super.deactivate();
        this.animationEngine.clearAllAgents();
    }
}

/**
 * Debate Mode - Multiple agents with opposing views
 */
class DebateMode extends GameMode {
    activate(config) {
        super.activate(config);

        // Clear existing agents
        this.animationEngine.clearAllAgents();

        // Create opposing agents
        const targetNodeId = config.targetNodeId || this.getRandomClaimNode();

        this.agentIds = [
            this.animationEngine.createAgent({
                agent_id: 'critic_1',
                type: 'critic',
                targetNodeId: targetNodeId
            }).id,
            this.animationEngine.createAgent({
                agent_id: 'validator_1',
                type: 'validator',
                targetNodeId: targetNodeId
            }).id
        ];

        // Start debate when agents arrive
        setTimeout(() => {
            if (window.DebateSystem) {
                this.debate = new window.DebateSystem(this.animationEngine);
                this.debate.startDebate({
                    nodeId: targetNodeId,
                    participants: this.agentIds,
                    mode: 'competitive',
                    topic: 'Claim Validity'
                });
            }
        }, 3000);
    }

    getRandomClaimNode() {
        const nodes = this.animationEngine.graphRenderer.currentGraphData.nodes
            .filter(n => n.type === 'super' || n.type === 'sub');
        return nodes[Math.floor(Math.random() * nodes.length)]?.id;
    }

    deactivate() {
        super.deactivate();
        if (this.debate) {
            this.debate.clearAll();
        }
        this.animationEngine.clearAllAgents();
    }
}

/**
 * Collaborative Mode - Team of agents working together
 */
class CollaborativeMode extends GameMode {
    activate(config) {
        super.activate(config);

        // Clear existing agents
        this.animationEngine.clearAllAgents();

        // Create team of diverse agents
        const teamSize = config.teamSize || 4;
        const types = ['researcher', 'critic', 'synthesizer', 'validator'];

        this.team = [];
        for (let i = 0; i < teamSize; i++) {
            const agent = this.animationEngine.createAgent({
                agent_id: `team_${i}`,
                type: types[i % types.length],
                startNodeId: this.getRandomNode()
            });
            this.team.push(agent.id);
        }

        // Assign different exploration zones
        this.assignZones();
    }

    assignZones() {
        const nodes = this.animationEngine.graphRenderer.currentGraphData.nodes;
        const zoneSize = Math.ceil(nodes.length / this.team.length);

        this.team.forEach((agentId, index) => {
            const zoneNodes = nodes.slice(index * zoneSize, (index + 1) * zoneSize);
            this.exploreSone(agentId, zoneNodes);
        });
    }

    exploreZone(agentId, zoneNodes) {
        let nodeIndex = 0;

        const visitNext = () => {
            if (nodeIndex >= zoneNodes.length || !this.isActive) return;

            const nodeId = zoneNodes[nodeIndex].id;
            this.animationEngine.moveAgent(agentId, nodeId);
            this.animationEngine.setAgentAction(agentId, 'analyzing', {
                thought: 'Analyzing...'
            });

            nodeIndex++;
            setTimeout(visitNext, 2000);
        };

        visitNext();
    }

    getRandomNode() {
        const nodes = this.animationEngine.graphRenderer.currentGraphData.nodes;
        return nodes[Math.floor(Math.random() * nodes.length)]?.id;
    }

    deactivate() {
        super.deactivate();
        this.animationEngine.clearAllAgents();
    }
}

/**
 * Tournament Mode - Bracket-style agent competition
 */
class TournamentMode extends GameMode {
    activate(config) {
        super.activate(config);

        // Clear existing agents
        this.animationEngine.clearAllAgents();

        // Create tournament bracket
        this.bracket = this.createBracket(config.participants || 4);
        this.currentRound = 0;

        // Start first round
        this.startRound();
    }

    createBracket(numParticipants) {
        const profiles = Object.keys(this.animationEngine.gameModeManager?.agentProfiles || {});
        const participants = [];

        for (let i = 0; i < numParticipants; i++) {
            const profileId = profiles[i % profiles.length];
            participants.push({
                profileId: profileId,
                agentId: `tournament_${i}`,
                score: 0
            });
        }

        return participants;
    }

    startRound() {
        console.log(`[Tournament] Round ${this.currentRound + 1}`);

        // Pair up participants
        const pairs = [];
        for (let i = 0; i < this.bracket.length; i += 2) {
            if (i + 1 < this.bracket.length) {
                pairs.push([this.bracket[i], this.bracket[i + 1]]);
            }
        }

        // Run debates for each pair
        pairs.forEach((pair, index) => {
            const targetNode = this.getRandomClaimNode();

            // Create agents
            pair.forEach(participant => {
                const profile = this.animationEngine.gameModeManager.getAgentProfile(participant.profileId);
                this.animationEngine.createAgent({
                    agent_id: participant.agentId,
                    type: profile.type,
                    targetNodeId: targetNode,
                    personality: profile.personality
                });
            });

            // Start debate
            setTimeout(() => {
                if (window.DebateSystem) {
                    const debate = new window.DebateSystem(this.animationEngine);
                    debate.startDebate({
                        nodeId: targetNode,
                        participants: pair.map(p => p.agentId),
                        mode: 'competitive',
                        topic: `Tournament Round ${this.currentRound + 1}`
                    });
                }
            }, 2000 + index * 1000);
        });

        // Advance to next round after delay
        setTimeout(() => {
            this.currentRound++;
            if (this.currentRound < Math.log2(this.bracket.length)) {
                this.startRound();
            } else {
                this.declareWinner();
            }
        }, 15000);
    }

    getRandomClaimNode() {
        const nodes = this.animationEngine.graphRenderer.currentGraphData.nodes
            .filter(n => n.type === 'super' || n.type === 'sub');
        return nodes[Math.floor(Math.random() * nodes.length)]?.id;
    }

    declareWinner() {
        // Winner is participant with highest score
        const winner = this.bracket.reduce((best, current) =>
            current.score > best.score ? current : best
        );

        console.log(`[Tournament] Winner: ${winner.agentId}`);

        this.animationEngine.logActivity(
            `Tournament winner: ${winner.agentId}`,
            'tournament_end',
            winner.agentId
        );
    }

    deactivate() {
        super.deactivate();
        this.animationEngine.clearAllAgents();
    }
}

/**
 * Speed Run Mode - Race to find evidence
 */
class SpeedRunMode extends GameMode {
    activate(config) {
        super.activate(config);

        // Clear existing agents
        this.animationEngine.clearAllAgents();

        // Create racing agents
        const racers = config.racers || 3;
        const targetNodeId = config.targetNodeId || this.getRandomNode();

        this.racerIds = [];
        this.startPositions = this.getSpreadStartNodes(racers);

        for (let i = 0; i < racers; i++) {
            const agent = this.animationEngine.createAgent({
                agent_id: `racer_${i}`,
                type: 'explorer',
                startNodeId: this.startPositions[i],
                targetNodeId: targetNodeId,
                personality: {
                    speed: 130 + Math.random() * 40
                }
            });
            this.racerIds.push(agent.id);
        }

        // Start timer
        this.startTime = Date.now();
        this.displayTimer();

        // Listen for arrivals
        this.animationEngine.on('agentArrived', (data) => {
            if (data.nodeId === targetNodeId && this.racerIds.includes(data.agentId)) {
                this.declareWinner(data.agentId);
            }
        });
    }

    getSpreadStartNodes(count) {
        const nodes = this.animationEngine.graphRenderer.currentGraphData.nodes;
        const step = Math.floor(nodes.length / count);
        return Array.from({ length: count }, (_, i) => nodes[i * step]?.id);
    }

    getRandomNode() {
        const nodes = this.animationEngine.graphRenderer.currentGraphData.nodes;
        return nodes[Math.floor(Math.random() * nodes.length)]?.id;
    }

    displayTimer() {
        // Timer display in UI (would need UI element)
        const updateTimer = () => {
            if (!this.isActive) return;

            const elapsed = Date.now() - this.startTime;
            const seconds = (elapsed / 1000).toFixed(1);

            console.log(`[SpeedRun] Time: ${seconds}s`);

            setTimeout(updateTimer, 100);
        };

        updateTimer();
    }

    declareWinner(agentId) {
        const elapsed = Date.now() - this.startTime;
        const seconds = (elapsed / 1000).toFixed(2);

        console.log(`[SpeedRun] Winner: ${agentId} in ${seconds}s`);

        this.animationEngine.logActivity(
            `Speed run winner: ${agentId} (${seconds}s)`,
            'speedrun_end',
            agentId
        );

        this.deactivate();
    }

    deactivate() {
        super.deactivate();
        this.animationEngine.clearAllAgents();
    }
}

/**
 * Exploration Mode - Free-form discovery
 */
class ExplorationMode extends GameMode {
    activate(config) {
        super.activate(config);

        // Create a few explorers
        const explorerCount = config.explorerCount || 2;

        for (let i = 0; i < explorerCount; i++) {
            const agent = this.animationEngine.createAgent({
                agent_id: `explorer_${i}`,
                type: 'explorer',
                startNodeId: this.getRandomNode()
            });

            // Random walk behavior
            this.startRandomWalk(agent.id);
        }
    }

    startRandomWalk(agentId) {
        const walk = () => {
            if (!this.isActive) return;

            const randomNode = this.getRandomNode();
            this.animationEngine.moveAgent(agentId, randomNode);

            setTimeout(walk, 3000 + Math.random() * 2000);
        };

        walk();
    }

    getRandomNode() {
        const nodes = this.animationEngine.graphRenderer.currentGraphData.nodes;
        return nodes[Math.floor(Math.random() * nodes.length)]?.id;
    }

    deactivate() {
        super.deactivate();
        this.animationEngine.clearAllAgents();
    }
}

// Export to global scope
window.GameModeManager = GameModeManager;
