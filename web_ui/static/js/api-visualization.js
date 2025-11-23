/**
 * API Nodes & Search Visualization System
 *
 * Visualizes external API calls, search results, and data source integrations.
 * Shows animated connections to external services like arXiv, PubMed, etc.
 */

class APIVisualizationSystem {
    constructor(graphRenderer) {
        this.graphRenderer = graphRenderer;
        this.apiNodes = new Map(); // apiNodeId -> APINode instance
        this.activeRequests = new Map(); // requestId -> Request instance
        this.requestCounter = 0;
    }

    /**
     * Create an API source node
     * @param {object} config - API node configuration
     */
    createAPINode(config) {
        const {
            id,
            source = 'API', // arXiv, PubMed, Wikipedia, etc.
            position = null,
            metadata = {}
        } = config;

        const apiNode = new APINode({
            id: id,
            source: source,
            position: position,
            metadata: metadata,
            graphRenderer: this.graphRenderer,
            apiSystem: this
        });

        this.apiNodes.set(id, apiNode);

        console.log(`[APIVisualization] Created API node: ${id} (${source})`);
        return apiNode;
    }

    /**
     * Visualize an API request
     * @param {object} config - Request configuration
     */
    visualizeRequest(config) {
        const {
            apiNodeId,
            targetNodeId = null,
            query = '',
            status = 'pending' // pending, success, error
        } = config;

        const requestId = `req_${++this.requestCounter}`;

        const request = new APIRequest({
            id: requestId,
            apiNodeId: apiNodeId,
            targetNodeId: targetNodeId,
            query: query,
            status: status,
            apiSystem: this,
            graphRenderer: this.graphRenderer
        });

        this.activeRequests.set(requestId, request);
        request.start();

        console.log(`[APIVisualization] Started request ${requestId}`);
        return request;
    }

    /**
     * Animate search results flying in
     * @param {object} config - Results configuration
     */
    animateSearchResults(config) {
        const {
            apiNodeId,
            results = [], // Array of {id, title, relevance}
            targetPosition = null
        } = config;

        const apiNode = this.apiNodes.get(apiNodeId);
        if (!apiNode) {
            console.warn(`[APIVisualization] API node ${apiNodeId} not found`);
            return;
        }

        // Animate each result flying in
        results.forEach((result, index) => {
            setTimeout(() => {
                this.animateSingleResult(apiNode, result, index);
            }, index * 300); // Stagger animations
        });
    }

    /**
     * Animate a single search result
     */
    animateSingleResult(apiNode, result, index) {
        const effectsLayer = d3.select('.effects-layer');

        // Create result node
        const resultGroup = effectsLayer.append('g')
            .attr('class', 'search-result')
            .attr('transform', `translate(${apiNode.position.x}, ${apiNode.position.y})`);

        // Result bubble
        const relevanceColor = d3.interpolateRgb('#4CAF50', '#FFC107')(1 - result.relevance);

        resultGroup.append('circle')
            .attr('r', 8 + result.relevance * 12)
            .attr('fill', relevanceColor)
            .attr('stroke', '#fff')
            .attr('stroke-width', 2)
            .style('filter', 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))')
            .style('opacity', 0);

        // Result label
        resultGroup.append('text')
            .attr('text-anchor', 'middle')
            .attr('y', 30)
            .attr('font-size', '9px')
            .attr('fill', '#fff')
            .style('text-shadow', '0 1px 2px rgba(0,0,0,0.8)')
            .text(result.title.substring(0, 20) + '...')
            .style('opacity', 0);

        // Calculate target position (spread around API node)
        const angle = (index / 10) * Math.PI * 2;
        const radius = 100 + index * 20;
        const targetX = apiNode.position.x + Math.cos(angle) * radius;
        const targetY = apiNode.position.y + Math.sin(angle) * radius;

        // Animate: fade in, fly out, then add to graph
        resultGroup.transition()
            .duration(300)
            .style('opacity', 1)
            .selectAll('circle, text')
            .style('opacity', 1);

        resultGroup.transition()
            .delay(300)
            .duration(1000)
            .attr('transform', `translate(${targetX}, ${targetY})`)
            .on('end', () => {
                // Fade out (result would be added to graph at this point)
                resultGroup.transition()
                    .duration(500)
                    .style('opacity', 0)
                    .remove();
            });
    }

    /**
     * Show rate limit warning
     */
    showRateLimit(apiNodeId) {
        const apiNode = this.apiNodes.get(apiNodeId);
        if (!apiNode) return;

        apiNode.showRateLimitWarning();
    }

    /**
     * Update API node status
     */
    updateAPINodeStatus(apiNodeId, status) {
        const apiNode = this.apiNodes.get(apiNodeId);
        if (apiNode) {
            apiNode.updateStatus(status);
        }
    }

    /**
     * Clear all API visualizations
     */
    clearAll() {
        this.apiNodes.forEach(node => node.destroy());
        this.apiNodes.clear();

        this.activeRequests.forEach(req => req.cancel());
        this.activeRequests.clear();
    }
}

/**
 * API Node - Represents an external data source
 */
class APINode {
    constructor(config) {
        this.id = config.id;
        this.source = config.source;
        this.position = config.position || { x: 0, y: 0 };
        this.metadata = config.metadata;
        this.graphRenderer = config.graphRenderer;
        this.apiSystem = config.apiSystem;

        this.element = null;
        this.status = 'idle'; // idle, requesting, success, error, rate_limited

        this.createVisual();
    }

    /**
     * Create visual representation
     */
    createVisual() {
        const effectsLayer = d3.select('.effects-layer');

        // Create API node group
        const group = effectsLayer.append('g')
            .attr('class', 'api-node')
            .attr('data-api-id', this.id)
            .attr('transform', `translate(${this.position.x}, ${this.position.y})`);

        // Outer ring (pulsing when active)
        group.append('circle')
            .attr('r', 35)
            .attr('fill', 'none')
            .attr('stroke', '#00BCD4')
            .attr('stroke-width', 2)
            .attr('class', 'api-ring')
            .style('opacity', 0.5);

        // Main circle
        group.append('circle')
            .attr('r', 25)
            .attr('fill', '#00BCD4')
            .attr('stroke', '#fff')
            .attr('stroke-width', 2)
            .attr('class', 'api-body')
            .style('filter', 'drop-shadow(0 2px 6px rgba(0,0,0,0.4))');

        // Icon
        const icon = this.getSourceIcon();
        group.append('text')
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'central')
            .attr('font-size', '20px')
            .attr('class', 'api-icon')
            .text(icon);

        // Label
        group.append('text')
            .attr('text-anchor', 'middle')
            .attr('y', 40)
            .attr('font-size', '11px')
            .attr('font-weight', 'bold')
            .attr('fill', '#fff')
            .style('text-shadow', '0 1px 3px rgba(0,0,0,0.8)')
            .text(this.source);

        this.element = group;

        // Spawn animation
        this.playSpawnAnimation();
    }

    /**
     * Get icon for source type
     */
    getSourceIcon() {
        const icons = {
            'arXiv': '📚',
            'PubMed': '🏥',
            'Wikipedia': '📖',
            'Google Scholar': '🎓',
            'Semantic Scholar': '🔬',
            'API': '🌐',
            'Database': '💾',
            'File': '📄'
        };

        return icons[this.source] || '🌐';
    }

    /**
     * Play spawn animation
     */
    playSpawnAnimation() {
        this.element
            .style('opacity', 0)
            .transition()
            .duration(500)
            .style('opacity', 1);

        this.element.select('.api-body')
            .attr('r', 0)
            .transition()
            .duration(500)
            .attr('r', 25);
    }

    /**
     * Update status
     */
    updateStatus(status) {
        this.status = status;

        const colors = {
            'idle': '#00BCD4',
            'requesting': '#FFC107',
            'success': '#4CAF50',
            'error': '#F44336',
            'rate_limited': '#FF5722'
        };

        const color = colors[status] || '#00BCD4';

        this.element.select('.api-body')
            .transition()
            .duration(300)
            .attr('fill', color);

        this.element.select('.api-ring')
            .attr('stroke', color);

        // Pulse effect for active states
        if (status === 'requesting') {
            this.startPulse();
        } else {
            this.stopPulse();
        }
    }

    /**
     * Start pulsing animation
     */
    startPulse() {
        const ring = this.element.select('.api-ring');

        const pulse = () => {
            ring.transition()
                .duration(1000)
                .attr('r', 40)
                .style('opacity', 0.2)
                .transition()
                .duration(1000)
                .attr('r', 35)
                .style('opacity', 0.5)
                .on('end', pulse);
        };

        pulse();
    }

    /**
     * Stop pulsing animation
     */
    stopPulse() {
        this.element.select('.api-ring')
            .interrupt()
            .transition()
            .duration(300)
            .attr('r', 35)
            .style('opacity', 0.5);
    }

    /**
     * Show rate limit warning
     */
    showRateLimitWarning() {
        this.updateStatus('rate_limited');

        // Warning icon
        const warning = this.element.append('text')
            .attr('x', 15)
            .attr('y', -15)
            .attr('font-size', '16px')
            .text('⚠️')
            .style('opacity', 0);

        warning.transition()
            .duration(300)
            .style('opacity', 1);

        // Remove after delay
        setTimeout(() => {
            warning.transition()
                .duration(300)
                .style('opacity', 0)
                .remove();
        }, 3000);
    }

    /**
     * Destroy the API node
     */
    destroy() {
        if (this.element) {
            this.element.transition()
                .duration(500)
                .style('opacity', 0)
                .remove();
        }
    }
}

/**
 * API Request - Represents an active API call
 */
class APIRequest {
    constructor(config) {
        this.id = config.id;
        this.apiNodeId = config.apiNodeId;
        this.targetNodeId = config.targetNodeId;
        this.query = config.query;
        this.status = config.status;
        this.apiSystem = config.apiSystem;
        this.graphRenderer = config.graphRenderer;

        this.element = null;
        this.particles = [];
    }

    /**
     * Start the request animation
     */
    start() {
        const apiNode = this.apiSystem.apiNodes.get(this.apiNodeId);
        if (!apiNode) return;

        // Update API node status
        apiNode.updateStatus('requesting');

        // Create data packets traveling from API to target
        if (this.targetNodeId) {
            this.createDataPackets(apiNode);
        }

        // Create loading indicator
        this.createLoadingIndicator(apiNode);
    }

    /**
     * Create animated data packets
     */
    createDataPackets(apiNode) {
        const targetNode = this.graphRenderer.currentGraphData.nodes.find(n => n.id === this.targetNodeId);
        if (!targetNode) return;

        const particlesLayer = d3.select('.particles-layer');

        // Create multiple packets
        for (let i = 0; i < 5; i++) {
            setTimeout(() => {
                const packet = particlesLayer.append('circle')
                    .attr('class', 'data-packet')
                    .attr('cx', apiNode.position.x)
                    .attr('cy', apiNode.position.y)
                    .attr('r', 4)
                    .attr('fill', '#00BCD4')
                    .style('opacity', 0.8);

                // Animate to target
                packet.transition()
                    .duration(1500)
                    .ease(d3.easeCubicInOut)
                    .attr('cx', targetNode.x)
                    .attr('cy', targetNode.y)
                    .style('opacity', 0)
                    .remove();

                this.particles.push(packet);
            }, i * 200);
        }
    }

    /**
     * Create loading indicator at API node
     */
    createLoadingIndicator(apiNode) {
        const group = apiNode.element.append('g')
            .attr('class', 'loading-indicator');

        // Spinning arc
        const arc = d3.arc()
            .innerRadius(28)
            .outerRadius(32)
            .startAngle(0)
            .endAngle(Math.PI * 1.5);

        const spinner = group.append('path')
            .attr('d', arc)
            .attr('fill', '#FFC107')
            .style('opacity', 0.8);

        // Rotate animation
        const rotate = () => {
            spinner.transition()
                .duration(1000)
                .ease(d3.easeLinear)
                .attrTween('transform', () => {
                    return d3.interpolateString('rotate(0)', 'rotate(360)');
                })
                .on('end', rotate);
        };

        rotate();

        this.element = group;
    }

    /**
     * Complete the request
     */
    complete(success = true) {
        const apiNode = this.apiSystem.apiNodes.get(this.apiNodeId);
        if (apiNode) {
            apiNode.updateStatus(success ? 'success' : 'error');

            // Reset to idle after delay
            setTimeout(() => {
                apiNode.updateStatus('idle');
            }, 2000);
        }

        // Remove loading indicator
        if (this.element) {
            this.element.transition()
                .duration(300)
                .style('opacity', 0)
                .remove();
        }
    }

    /**
     * Cancel the request
     */
    cancel() {
        this.complete(false);

        // Remove particles
        this.particles.forEach(p => {
            p.interrupt().remove();
        });
    }
}

// Export to global scope
window.APIVisualizationSystem = APIVisualizationSystem;
window.APINode = APINode;
window.APIRequest = APIRequest;
