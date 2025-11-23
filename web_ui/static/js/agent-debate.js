/**
 * Multi-Agent Debate System
 *
 * Handles competitive and collaborative interactions between multiple agents.
 * Visualizes debates, arguments, and consensus-building processes.
 */

class DebateSystem {
    constructor(animationEngine) {
        this.animationEngine = animationEngine;
        this.activeDebates = new Map(); // debateId -> Debate instance
        this.debateCounter = 0;
    }

    /**
     * Start a debate at a specific node
     * @param {object} config - Debate configuration
     */
    startDebate(config) {
        const {
            nodeId,
            participants = [], // Array of agent IDs
            mode = 'competitive', // competitive, collaborative, tournament
            topic = 'Node evaluation',
            duration = 10000 // 10 seconds
        } = config;

        const debateId = `debate_${++this.debateCounter}`;

        const debate = new Debate({
            id: debateId,
            nodeId: nodeId,
            participants: participants,
            mode: mode,
            topic: topic,
            duration: duration,
            animationEngine: this.animationEngine,
            debateSystem: this
        });

        this.activeDebates.set(debateId, debate);
        debate.start();

        console.log(`[DebateSystem] Started ${mode} debate at node ${nodeId}`);
        return debate;
    }

    /**
     * End a debate
     */
    endDebate(debateId) {
        const debate = this.activeDebates.get(debateId);
        if (debate) {
            debate.end();
            this.activeDebates.delete(debateId);
        }
    }

    /**
     * Get active debates at a node
     */
    getDebatesAtNode(nodeId) {
        return Array.from(this.activeDebates.values())
            .filter(debate => debate.nodeId === nodeId);
    }

    /**
     * Clear all debates
     */
    clearAll() {
        this.activeDebates.forEach(debate => debate.end());
        this.activeDebates.clear();
    }
}

/**
 * Individual Debate Instance
 */
class Debate {
    constructor(config) {
        this.id = config.id;
        this.nodeId = config.nodeId;
        this.participants = config.participants;
        this.mode = config.mode;
        this.topic = config.topic;
        this.duration = config.duration;
        this.animationEngine = config.animationEngine;
        this.debateSystem = config.debateSystem;

        // Debate state
        this.arguments = []; // Array of {agentId, text, confidence, stance}
        this.currentSpeaker = null;
        this.round = 0;
        this.maxRounds = 3;
        this.startTime = null;
        this.endTime = null;

        // Visual elements
        this.debateGroup = null;
        this.transcriptPanel = null;
    }

    /**
     * Start the debate
     */
    start() {
        this.startTime = Date.now();

        // Move all participants to the debate node
        this.participants.forEach(agentId => {
            this.animationEngine.moveAgent(agentId, this.nodeId);
            this.animationEngine.setAgentAction(agentId, 'debating', {
                thought: 'Preparing argument...'
            });
        });

        // Create visual debate arena
        this.createDebateArena();

        // Start debate rounds
        setTimeout(() => this.runDebateRounds(), 1000);

        // Auto-end after duration
        setTimeout(() => this.end(), this.duration);
    }

    /**
     * Create visual debate arena around node
     */
    createDebateArena() {
        const effectsLayer = d3.select('.effects-layer');
        const graphRenderer = this.animationEngine.graphRenderer;

        // Find the node
        const node = graphRenderer.currentGraphData.nodes.find(n => n.id === this.nodeId);
        if (!node) return;

        // Create debate group
        this.debateGroup = effectsLayer.append('g')
            .attr('class', 'debate-arena')
            .attr('data-debate-id', this.id);

        // Position agents in a circle around the node
        const radius = 60;
        const angleStep = (Math.PI * 2) / this.participants.length;

        this.participants.forEach((agentId, index) => {
            const angle = index * angleStep;
            const x = node.x + Math.cos(angle) * radius;
            const y = node.y + Math.sin(angle) * radius;

            // Position indicator
            this.debateGroup.append('circle')
                .attr('cx', x)
                .attr('cy', y)
                .attr('r', 25)
                .attr('fill', 'none')
                .attr('stroke', '#FFD700')
                .attr('stroke-width', 2)
                .attr('stroke-dasharray', '5,5')
                .attr('class', 'debate-position')
                .style('opacity', 0)
                .transition()
                .duration(500)
                .style('opacity', 0.6);
        });

        // Central debate circle
        this.debateGroup.append('circle')
            .attr('cx', node.x)
            .attr('cy', node.y)
            .attr('r', 50)
            .attr('fill', 'none')
            .attr('stroke', '#FF4081')
            .attr('stroke-width', 3)
            .attr('class', 'debate-ring')
            .style('opacity', 0)
            .transition()
            .duration(500)
            .style('opacity', 0.8);

        // Debate title
        this.debateGroup.append('text')
            .attr('x', node.x)
            .attr('y', node.y - 70)
            .attr('text-anchor', 'middle')
            .attr('font-size', '14px')
            .attr('font-weight', 'bold')
            .attr('fill', '#FFD700')
            .style('text-shadow', '0 2px 4px rgba(0,0,0,0.8)')
            .text(`DEBATE: ${this.topic}`)
            .style('opacity', 0)
            .transition()
            .duration(500)
            .style('opacity', 1);
    }

    /**
     * Run debate rounds
     */
    async runDebateRounds() {
        while (this.round < this.maxRounds && Date.now() - this.startTime < this.duration) {
            this.round++;

            console.log(`[Debate ${this.id}] Round ${this.round}`);

            // Each participant presents their argument
            for (const agentId of this.participants) {
                await this.presentArgument(agentId);
                await this.sleep(1500); // Pause between speakers
            }

            await this.sleep(1000); // Pause between rounds
        }

        // Determine winner
        this.determineWinner();
    }

    /**
     * Agent presents their argument
     */
    async presentArgument(agentId) {
        this.currentSpeaker = agentId;

        const agent = this.animationEngine.getAgent(agentId);
        if (!agent) return;

        // Generate argument based on agent type and mode
        const argument = this.generateArgument(agent);

        // Store argument
        this.arguments.push({
            agentId: agentId,
            text: argument.text,
            confidence: argument.confidence,
            stance: argument.stance,
            round: this.round
        });

        // Visual feedback
        this.showArgument(agentId, argument);

        // Log to activity
        this.animationEngine.logActivity(
            `${agent.getDisplayName()}: "${argument.text}"`,
            'debate_argument',
            agentId
        );
    }

    /**
     * Generate argument based on agent type
     */
    generateArgument(agent) {
        const argumentTemplates = {
            'researcher': [
                'Based on the evidence...',
                'The data suggests...',
                'Research indicates...',
                'Studies show...'
            ],
            'critic': [
                'I disagree because...',
                'This claim is questionable...',
                'The evidence is weak...',
                'I challenge this assertion...'
            ],
            'synthesizer': [
                'Combining both views...',
                'The connection between...',
                'This relates to...',
                'We can unify these...'
            ],
            'validator': [
                'This checks out...',
                'I verified that...',
                'The logic is sound...',
                'This is valid because...'
            ]
        };

        const templates = argumentTemplates[agent.type] || ['My analysis shows...'];
        const template = templates[Math.floor(Math.random() * templates.length)];

        // Generate stance based on mode
        let stance = 'neutral';
        if (this.mode === 'competitive') {
            stance = Math.random() > 0.5 ? 'support' : 'oppose';
        } else if (this.mode === 'collaborative') {
            stance = 'support';
        }

        return {
            text: template,
            confidence: 0.6 + Math.random() * 0.4,
            stance: stance
        };
    }

    /**
     * Show argument visually (speech bubble)
     */
    showArgument(agentId, argument) {
        const agent = this.animationEngine.getAgent(agentId);
        if (!agent) return;

        // Show thought bubble
        agent.showThought(argument.text);

        // Highlight agent's confidence with meter
        const graphRenderer = this.animationEngine.graphRenderer;
        const node = graphRenderer.currentGraphData.nodes.find(n => n.id === this.nodeId);
        if (!node) return;

        // Find agent position
        const agentIndex = this.participants.indexOf(agentId);
        const radius = 60;
        const angleStep = (Math.PI * 2) / this.participants.length;
        const angle = agentIndex * angleStep;
        const x = node.x + Math.cos(angle) * radius;
        const y = node.y + Math.sin(angle) * radius;

        // Confidence meter
        const meterGroup = this.debateGroup.append('g')
            .attr('class', 'confidence-meter')
            .attr('transform', `translate(${x}, ${y + 35})`);

        // Background
        meterGroup.append('rect')
            .attr('x', -20)
            .attr('y', 0)
            .attr('width', 40)
            .attr('height', 5)
            .attr('fill', '#333')
            .attr('rx', 2);

        // Confidence bar
        const stanceColor = {
            'support': '#4CAF50',
            'oppose': '#F44336',
            'neutral': '#FFC107'
        };

        meterGroup.append('rect')
            .attr('x', -20)
            .attr('y', 0)
            .attr('width', 0)
            .attr('height', 5)
            .attr('fill', stanceColor[argument.stance])
            .attr('rx', 2)
            .transition()
            .duration(1000)
            .attr('width', 40 * argument.confidence);

        // Remove after delay
        setTimeout(() => {
            meterGroup.transition()
                .duration(500)
                .style('opacity', 0)
                .remove();
        }, 2000);
    }

    /**
     * Determine debate winner
     */
    determineWinner() {
        console.log(`[Debate ${this.id}] Determining winner...`);

        if (this.arguments.length === 0) {
            this.showResult('No arguments presented');
            return;
        }

        // Calculate scores based on confidence and stance
        const scores = new Map();

        this.participants.forEach(agentId => {
            const agentArgs = this.arguments.filter(a => a.agentId === agentId);

            // Score: average confidence * stance multiplier
            let score = 0;
            agentArgs.forEach(arg => {
                let stanceMultiplier = 1.0;
                if (this.mode === 'competitive') {
                    stanceMultiplier = arg.stance === 'support' ? 1.2 : 0.8;
                }
                score += arg.confidence * stanceMultiplier;
            });

            score = score / Math.max(agentArgs.length, 1);
            scores.set(agentId, score);
        });

        // Find winner
        let winnerId = null;
        let highestScore = -1;

        scores.forEach((score, agentId) => {
            if (score > highestScore) {
                highestScore = score;
                winnerId = agentId;
            }
        });

        const winner = this.animationEngine.getAgent(winnerId);
        const winnerName = winner ? winner.getDisplayName() : 'Unknown';

        // Show result
        this.showResult(`Winner: ${winnerName} (score: ${highestScore.toFixed(2)})`);

        // Log result
        this.animationEngine.logActivity(
            `Debate concluded. Winner: ${winnerName}`,
            'debate_end',
            winnerId
        );

        // Emit event
        this.animationEngine.emit('debateEnded', {
            debateId: this.id,
            winnerId: winnerId,
            score: highestScore,
            arguments: this.arguments
        });
    }

    /**
     * Show debate result
     */
    showResult(message) {
        const graphRenderer = this.animationEngine.graphRenderer;
        const node = graphRenderer.currentGraphData.nodes.find(n => n.id === this.nodeId);
        if (!node) return;

        // Result banner
        const banner = this.debateGroup.append('g')
            .attr('class', 'debate-result');

        // Background
        banner.append('rect')
            .attr('x', node.x - 80)
            .attr('y', node.y - 90)
            .attr('width', 160)
            .attr('height', 30)
            .attr('rx', 15)
            .attr('fill', '#FFD700')
            .attr('stroke', '#000')
            .attr('stroke-width', 2);

        // Text
        banner.append('text')
            .attr('x', node.x)
            .attr('y', node.y - 70)
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'central')
            .attr('font-size', '12px')
            .attr('font-weight', 'bold')
            .attr('fill', '#000')
            .text(message);

        // Fade out after 3 seconds
        setTimeout(() => {
            banner.transition()
                .duration(1000)
                .style('opacity', 0)
                .remove();
        }, 3000);
    }

    /**
     * End the debate
     */
    end() {
        this.endTime = Date.now();

        // Reset agent states
        this.participants.forEach(agentId => {
            this.animationEngine.setAgentAction(agentId, 'idle');
        });

        // Remove visual elements
        if (this.debateGroup) {
            this.debateGroup.transition()
                .duration(1000)
                .style('opacity', 0)
                .remove();
        }

        console.log(`[Debate ${this.id}] Ended after ${this.round} rounds`);
    }

    /**
     * Sleep utility
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Get debate transcript
     */
    getTranscript() {
        return {
            id: this.id,
            nodeId: this.nodeId,
            mode: this.mode,
            topic: this.topic,
            rounds: this.round,
            arguments: this.arguments,
            startTime: this.startTime,
            endTime: this.endTime
        };
    }
}

// Export to global scope
window.DebateSystem = DebateSystem;
window.Debate = Debate;
