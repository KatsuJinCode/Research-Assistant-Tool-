/**
 * Agent Movement System - Pathfinding and smooth movement
 *
 * Implements A* pathfinding algorithm for intelligent agent navigation
 * through the knowledge graph. Handles collision detection, queueing,
 * and smooth Bezier curve movement along edges.
 */

class AgentMovementSystem {
    constructor() {
        this.nodeOccupancy = new Map(); // nodeId -> Set of agentIds
        this.maxAgentsPerNode = 3;
        this.reservations = new Map(); // agentId -> reserved nodeId
    }

    /**
     * Find shortest path between two nodes using A* algorithm
     * @param {string} startNodeId - Starting node ID
     * @param {string} endNodeId - Target node ID
     * @param {object} graphData - Graph data (nodes, links)
     * @returns {Array} Array of node IDs representing the path
     */
    findPath(startNodeId, endNodeId, graphData) {
        if (!startNodeId || !endNodeId) {
            console.warn('[AgentMovement] Invalid start or end node');
            return [];
        }

        if (startNodeId === endNodeId) {
            return [endNodeId];
        }

        // Build adjacency list
        const adjacency = this.buildAdjacencyList(graphData);

        // A* algorithm
        const openSet = new Set([startNodeId]);
        const cameFrom = new Map();
        const gScore = new Map(); // Cost from start to node
        const fScore = new Map(); // Estimated total cost

        // Initialize scores
        gScore.set(startNodeId, 0);
        fScore.set(startNodeId, this.heuristic(startNodeId, endNodeId, graphData));

        while (openSet.size > 0) {
            // Get node with lowest fScore
            let current = null;
            let lowestF = Infinity;
            for (const nodeId of openSet) {
                const f = fScore.get(nodeId) || Infinity;
                if (f < lowestF) {
                    lowestF = f;
                    current = nodeId;
                }
            }

            if (!current) break;

            // Found the goal
            if (current === endNodeId) {
                return this.reconstructPath(cameFrom, current);
            }

            openSet.delete(current);

            // Check neighbors
            const neighbors = adjacency.get(current) || [];
            for (const neighbor of neighbors) {
                const tentativeGScore = (gScore.get(current) || 0) + 1;

                if (!gScore.has(neighbor) || tentativeGScore < gScore.get(neighbor)) {
                    cameFrom.set(neighbor, current);
                    gScore.set(neighbor, tentativeGScore);
                    fScore.set(neighbor, tentativeGScore + this.heuristic(neighbor, endNodeId, graphData));

                    if (!openSet.has(neighbor)) {
                        openSet.add(neighbor);
                    }
                }
            }
        }

        // No path found - return direct path
        console.warn('[AgentMovement] No path found, returning direct path');
        return [endNodeId];
    }

    /**
     * Build adjacency list from graph data
     */
    buildAdjacencyList(graphData) {
        const adjacency = new Map();

        // Initialize all nodes
        graphData.nodes.forEach(node => {
            adjacency.set(node.id, []);
        });

        // Add edges (bidirectional for navigation)
        graphData.links.forEach(link => {
            const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
            const targetId = typeof link.target === 'object' ? link.target.id : link.target;

            if (adjacency.has(sourceId)) {
                adjacency.get(sourceId).push(targetId);
            }
            if (adjacency.has(targetId)) {
                adjacency.get(targetId).push(sourceId);
            }
        });

        return adjacency;
    }

    /**
     * Heuristic function for A* (Euclidean distance)
     */
    heuristic(nodeId1, nodeId2, graphData) {
        const node1 = graphData.nodes.find(n => n.id === nodeId1);
        const node2 = graphData.nodes.find(n => n.id === nodeId2);

        if (!node1 || !node2 || !node1.x || !node2.x) {
            return 0; // Unknown positions
        }

        const dx = node2.x - node1.x;
        const dy = node2.y - node1.y;
        return Math.sqrt(dx * dx + dy * dy) / 100; // Normalize
    }

    /**
     * Reconstruct path from A* came-from map
     */
    reconstructPath(cameFrom, current) {
        const path = [current];
        while (cameFrom.has(current)) {
            current = cameFrom.get(current);
            path.unshift(current);
        }
        return path;
    }

    /**
     * Check if an agent can occupy a node (collision detection)
     */
    canOccupy(agentId, nodeId) {
        const occupants = this.nodeOccupancy.get(nodeId) || new Set();

        // Already occupied by this agent
        if (occupants.has(agentId)) {
            return true;
        }

        // Check capacity
        return occupants.size < this.maxAgentsPerNode;
    }

    /**
     * Reserve a node for an agent (prevent overcrowding)
     */
    reserveNode(agentId, nodeId) {
        if (!this.canOccupy(agentId, nodeId)) {
            return false;
        }

        // Release previous reservation
        const prevReservation = this.reservations.get(agentId);
        if (prevReservation) {
            this.releaseNode(agentId, prevReservation);
        }

        // Make new reservation
        if (!this.nodeOccupancy.has(nodeId)) {
            this.nodeOccupancy.set(nodeId, new Set());
        }
        this.nodeOccupancy.get(nodeId).add(agentId);
        this.reservations.set(agentId, nodeId);

        return true;
    }

    /**
     * Release a node reservation
     */
    releaseNode(agentId, nodeId) {
        if (this.nodeOccupancy.has(nodeId)) {
            this.nodeOccupancy.get(nodeId).delete(agentId);
        }
        if (this.reservations.get(agentId) === nodeId) {
            this.reservations.delete(agentId);
        }
    }

    /**
     * Get queue position for agent at node
     */
    getQueuePosition(agentId, nodeId) {
        const occupants = this.nodeOccupancy.get(nodeId);
        if (!occupants || !occupants.has(agentId)) {
            return -1;
        }

        return Array.from(occupants).indexOf(agentId);
    }

    /**
     * Calculate offset position for queued agents at same node
     */
    calculateQueueOffset(position, nodeId, agentId) {
        const queuePos = this.getQueuePosition(agentId, nodeId);
        if (queuePos <= 0) {
            return position;
        }

        // Circular arrangement around node
        const radius = 25;
        const angle = (queuePos / this.maxAgentsPerNode) * Math.PI * 2;

        return {
            x: position.x + Math.cos(angle) * radius,
            y: position.y + Math.sin(angle) * radius
        };
    }

    /**
     * Generate Bezier curve points for smooth movement along edge
     * @param {object} startPos - Starting position {x, y}
     * @param {object} endPos - Ending position {x, y}
     * @param {number} steps - Number of interpolation steps
     * @returns {Array} Array of {x, y} points along curve
     */
    generateBezierPath(startPos, endPos, steps = 20) {
        const points = [];

        // Calculate control points for a gentle curve
        const dx = endPos.x - startPos.x;
        const dy = endPos.y - startPos.y;
        const distance = Math.sqrt(dx * dx + dy * dy);

        // Control point offset (perpendicular to line)
        const controlOffset = distance * 0.2;
        const perpX = -dy / distance;
        const perpY = dx / distance;

        const cp1 = {
            x: startPos.x + dx * 0.33 + perpX * controlOffset,
            y: startPos.y + dy * 0.33 + perpY * controlOffset
        };

        const cp2 = {
            x: startPos.x + dx * 0.66 - perpX * controlOffset,
            y: startPos.y + dy * 0.66 - perpY * controlOffset
        };

        // Generate points along cubic Bezier curve
        for (let i = 0; i <= steps; i++) {
            const t = i / steps;
            const point = this.cubicBezier(t, startPos, cp1, cp2, endPos);
            points.push(point);
        }

        return points;
    }

    /**
     * Calculate point on cubic Bezier curve
     */
    cubicBezier(t, p0, p1, p2, p3) {
        const oneMinusT = 1 - t;
        const oneMinusT2 = oneMinusT * oneMinusT;
        const oneMinusT3 = oneMinusT2 * oneMinusT;
        const t2 = t * t;
        const t3 = t2 * t;

        return {
            x: oneMinusT3 * p0.x + 3 * oneMinusT2 * t * p1.x + 3 * oneMinusT * t2 * p2.x + t3 * p3.x,
            y: oneMinusT3 * p0.y + 3 * oneMinusT2 * t * p1.y + 3 * oneMinusT * t2 * p2.y + t3 * p3.y
        };
    }

    /**
     * Find alternative path if primary path is blocked
     */
    findAlternativePath(startNodeId, endNodeId, graphData, blockedNodes = []) {
        // Temporarily remove blocked nodes from graph
        const filteredNodes = graphData.nodes.filter(n => !blockedNodes.includes(n.id));
        const filteredLinks = graphData.links.filter(l => {
            const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
            const targetId = typeof l.target === 'object' ? l.target.id : l.target;
            return !blockedNodes.includes(sourceId) && !blockedNodes.includes(targetId);
        });

        const filteredGraph = {
            nodes: filteredNodes,
            links: filteredLinks
        };

        return this.findPath(startNodeId, endNodeId, filteredGraph);
    }

    /**
     * Calculate movement speed based on relationship strength
     * Stronger relationships = faster movement
     */
    calculateEdgeSpeed(sourceId, targetId, graphData) {
        const link = graphData.links.find(l => {
            const sId = typeof l.source === 'object' ? l.source.id : l.source;
            const tId = typeof l.target === 'object' ? l.target.id : l.target;
            return (sId === sourceId && tId === targetId) || (sId === targetId && tId === sourceId);
        });

        if (!link) {
            return 1.0; // Default speed
        }

        // Speed modifiers based on relationship type
        const speedMap = {
            'contains': 1.0,      // Normal
            'has_sub': 1.2,       // Faster (hierarchical)
            'supports': 0.9,      // Slower (needs analysis)
            'contradicts': 0.8,   // Slowest (conflict)
            'duplicate': 1.5,     // Fastest (same content)
            'SIMILAR_TO': 1.1     // Slightly faster
        };

        return speedMap[link.type] || 1.0;
    }

    /**
     * Visualize path on graph (optional debugging/UI feature)
     */
    visualizePath(path, graphData, color = '#FFD700') {
        const pathsLayer = d3.select('.paths-layer');

        // Remove old paths
        pathsLayer.selectAll('.agent-path').remove();

        if (path.length < 2) return;

        // Draw path
        const pathGroup = pathsLayer.append('g')
            .attr('class', 'agent-path');

        for (let i = 0; i < path.length - 1; i++) {
            const startNode = graphData.nodes.find(n => n.id === path[i]);
            const endNode = graphData.nodes.find(n => n.id === path[i + 1]);

            if (!startNode || !endNode) continue;

            // Draw line
            pathGroup.append('line')
                .attr('x1', startNode.x)
                .attr('y1', startNode.y)
                .attr('x2', endNode.x)
                .attr('y2', endNode.y)
                .attr('stroke', color)
                .attr('stroke-width', 3)
                .attr('stroke-dasharray', '5,5')
                .attr('opacity', 0.5)
                .attr('class', 'path-segment');
        }

        // Fade out after 2 seconds
        pathGroup.transition()
            .delay(2000)
            .duration(1000)
            .style('opacity', 0)
            .remove();
    }

    /**
     * Clear all reservations (cleanup)
     */
    clearAll() {
        this.nodeOccupancy.clear();
        this.reservations.clear();
    }

    /**
     * Get occupancy statistics
     */
    getStats() {
        let totalOccupied = 0;
        let maxOccupancy = 0;

        this.nodeOccupancy.forEach((occupants, nodeId) => {
            if (occupants.size > 0) {
                totalOccupied++;
                maxOccupancy = Math.max(maxOccupancy, occupants.size);
            }
        });

        return {
            occupiedNodes: totalOccupied,
            totalReservations: this.reservations.size,
            maxOccupancy: maxOccupancy,
            maxAgentsPerNode: this.maxAgentsPerNode
        };
    }
}

// Global instance
window.AgentMovement = new AgentMovementSystem();
