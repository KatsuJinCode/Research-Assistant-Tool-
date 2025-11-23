/**
 * Graph Worker - Web Worker for CPU-Intensive Graph Operations
 *
 * Offloads heavy computation to background thread:
 * - Graph layout calculations (force-directed, hierarchical)
 * - Clustering algorithms
 * - Similarity matrix computation
 * - Text processing
 * - Search indexing
 *
 * Uses message passing for communication with main thread.
 */

// Worker state
let graphData = { nodes: [], links: [] };
let layoutEngine = null;
let searchIndex = null;

/**
 * Main message handler
 */
self.onmessage = function(event) {
    const { type, data, id } = event.data;

    try {
        let result;

        switch (type) {
            case 'init':
                result = initialize(data);
                break;

            case 'layout':
                result = calculateLayout(data);
                break;

            case 'cluster':
                result = performClustering(data);
                break;

            case 'similarity':
                result = computeSimilarityMatrix(data);
                break;

            case 'search':
                result = performSearch(data);
                break;

            case 'processText':
                result = processText(data);
                break;

            case 'updateGraph':
                result = updateGraph(data);
                break;

            case 'terminate':
                self.close();
                return;

            default:
                throw new Error(`Unknown message type: ${type}`);
        }

        // Send result back to main thread
        self.postMessage({
            id,
            type,
            success: true,
            result
        });

    } catch (error) {
        // Send error back to main thread
        self.postMessage({
            id,
            type,
            success: false,
            error: error.message
        });
    }
};

// ===========================
// INITIALIZATION
// ===========================

function initialize(data) {
    graphData = data.graph || { nodes: [], links: [] };
    searchIndex = buildSearchIndex(graphData.nodes);

    return {
        nodeCount: graphData.nodes.length,
        linkCount: graphData.links.length,
        message: 'Worker initialized'
    };
}

function updateGraph(data) {
    if (data.nodes) {
        graphData.nodes = data.nodes;
    }
    if (data.links) {
        graphData.links = data.links;
    }

    // Rebuild search index
    searchIndex = buildSearchIndex(graphData.nodes);

    return {
        nodeCount: graphData.nodes.length,
        linkCount: graphData.links.length
    };
}

// ===========================
// LAYOUT CALCULATIONS
// ===========================

function calculateLayout(data) {
    const { algorithm, iterations, width, height } = data;

    switch (algorithm) {
        case 'force':
            return calculateForceLayout(iterations, width, height);
        case 'hierarchical':
            return calculateHierarchicalLayout(width, height);
        case 'circular':
            return calculateCircularLayout(width, height);
        default:
            throw new Error(`Unknown layout algorithm: ${algorithm}`);
    }
}

/**
 * Force-directed layout calculation
 */
function calculateForceLayout(iterations = 100, width = 800, height = 600) {
    const nodes = graphData.nodes.map(n => ({
        ...n,
        x: n.x || Math.random() * width,
        y: n.y || Math.random() * height,
        vx: 0,
        vy: 0
    }));

    // Physics parameters
    const ATTRACTION = 0.01;
    const REPULSION = 3000;
    const DAMPING = 0.9;

    // Build link map for faster lookup
    const linkMap = new Map();
    for (const link of graphData.links) {
        const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
        const targetId = typeof link.target === 'object' ? link.target.id : link.target;

        if (!linkMap.has(sourceId)) linkMap.set(sourceId, []);
        linkMap.get(sourceId).push(targetId);
    }

    // Simulation iterations
    for (let iter = 0; iter < iterations; iter++) {
        // Apply forces
        for (let i = 0; i < nodes.length; i++) {
            const nodeA = nodes[i];

            // Repulsion between all nodes
            for (let j = i + 1; j < nodes.length; j++) {
                const nodeB = nodes[j];

                const dx = nodeB.x - nodeA.x;
                const dy = nodeB.y - nodeA.y;
                const distance = Math.sqrt(dx * dx + dy * dy) || 0.1;

                const force = REPULSION / (distance * distance);

                const fx = (dx / distance) * force;
                const fy = (dy / distance) * force;

                nodeA.vx -= fx;
                nodeA.vy -= fy;
                nodeB.vx += fx;
                nodeB.vy += fy;
            }

            // Attraction along links
            const connectedIds = linkMap.get(nodeA.id) || [];
            for (const targetId of connectedIds) {
                const nodeB = nodes.find(n => n.id === targetId);
                if (!nodeB) continue;

                const dx = nodeB.x - nodeA.x;
                const dy = nodeB.y - nodeA.y;
                const distance = Math.sqrt(dx * dx + dy * dy) || 0.1;

                const force = distance * ATTRACTION;

                const fx = (dx / distance) * force;
                const fy = (dy / distance) * force;

                nodeA.vx += fx;
                nodeA.vy += fy;
                nodeB.vx -= fx;
                nodeB.vy -= fy;
            }
        }

        // Update positions
        for (const node of nodes) {
            node.x += node.vx;
            node.y += node.vy;

            node.vx *= DAMPING;
            node.vy *= DAMPING;

            // Keep within bounds
            node.x = Math.max(50, Math.min(width - 50, node.x));
            node.y = Math.max(50, Math.min(height - 50, node.y));
        }

        // Send progress update every 10 iterations
        if (iter % 10 === 0) {
            self.postMessage({
                type: 'layoutProgress',
                progress: (iter / iterations) * 100,
                iteration: iter
            });
        }
    }

    return nodes.map(n => ({
        id: n.id,
        x: n.x,
        y: n.y
    }));
}

/**
 * Hierarchical layout calculation
 */
function calculateHierarchicalLayout(width = 800, height = 600) {
    // Build hierarchy from links
    const levels = new Map();
    const visited = new Set();

    // Find root nodes (no incoming edges)
    const hasIncoming = new Set();
    for (const link of graphData.links) {
        const targetId = typeof link.target === 'object' ? link.target.id : link.target;
        hasIncoming.add(targetId);
    }

    const roots = graphData.nodes.filter(n => !hasIncoming.has(n.id));

    // BFS to assign levels
    function assignLevel(nodeId, level) {
        if (visited.has(nodeId)) return;
        visited.add(nodeId);

        if (!levels.has(level)) levels.set(level, []);
        levels.get(level).push(nodeId);

        // Find children
        const children = graphData.links
            .filter(l => {
                const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
                return sourceId === nodeId;
            })
            .map(l => typeof l.target === 'object' ? l.target.id : l.target);

        for (const childId of children) {
            assignLevel(childId, level + 1);
        }
    }

    // Start from roots
    for (const root of roots) {
        assignLevel(root.id, 0);
    }

    // Assign unvisited nodes to level 0
    for (const node of graphData.nodes) {
        if (!visited.has(node.id)) {
            if (!levels.has(0)) levels.set(0, []);
            levels.get(0).push(node.id);
        }
    }

    // Calculate positions
    const positions = [];
    const levelHeight = height / (levels.size + 1);

    for (const [level, nodeIds] of levels.entries()) {
        const y = (level + 1) * levelHeight;
        const nodeWidth = width / (nodeIds.length + 1);

        nodeIds.forEach((nodeId, index) => {
            positions.push({
                id: nodeId,
                x: (index + 1) * nodeWidth,
                y: y
            });
        });
    }

    return positions;
}

/**
 * Circular layout calculation
 */
function calculateCircularLayout(width = 800, height = 600) {
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) / 2 - 50;

    const nodes = graphData.nodes;
    const angleStep = (2 * Math.PI) / nodes.length;

    return nodes.map((node, index) => {
        const angle = index * angleStep;
        return {
            id: node.id,
            x: centerX + radius * Math.cos(angle),
            y: centerY + radius * Math.sin(angle)
        };
    });
}

// ===========================
// CLUSTERING ALGORITHMS
// ===========================

function performClustering(data) {
    const { algorithm, k } = data;

    switch (algorithm) {
        case 'connected':
            return findConnectedComponents();
        case 'similarity':
            return clusterBySimilarity(k || 5);
        case 'louvain':
            return louvainClustering();
        default:
            throw new Error(`Unknown clustering algorithm: ${algorithm}`);
    }
}

/**
 * Find connected components
 */
function findConnectedComponents() {
    const visited = new Set();
    const clusters = [];

    function dfs(nodeId, cluster) {
        if (visited.has(nodeId)) return;
        visited.add(nodeId);
        cluster.push(nodeId);

        // Find connected nodes
        for (const link of graphData.links) {
            const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
            const targetId = typeof link.target === 'object' ? link.target.id : link.target;

            if (sourceId === nodeId && !visited.has(targetId)) {
                dfs(targetId, cluster);
            } else if (targetId === nodeId && !visited.has(sourceId)) {
                dfs(sourceId, cluster);
            }
        }
    }

    for (const node of graphData.nodes) {
        if (!visited.has(node.id)) {
            const cluster = [];
            dfs(node.id, cluster);
            clusters.push(cluster);
        }
    }

    return {
        clusters,
        clusterCount: clusters.length
    };
}

/**
 * Cluster by text similarity
 */
function clusterBySimilarity(k = 5) {
    // Simple k-means clustering on text similarity
    const nodes = graphData.nodes.filter(n => n.label || n.text);

    if (nodes.length === 0) {
        return { clusters: [], clusterCount: 0 };
    }

    // Initialize random centroids
    const centroids = [];
    for (let i = 0; i < Math.min(k, nodes.length); i++) {
        centroids.push(nodes[Math.floor(Math.random() * nodes.length)]);
    }

    const assignments = new Array(nodes.length).fill(0);
    let changed = true;
    let iterations = 0;
    const MAX_ITERATIONS = 20;

    while (changed && iterations < MAX_ITERATIONS) {
        changed = false;

        // Assign nodes to nearest centroid
        for (let i = 0; i < nodes.length; i++) {
            let minDist = Infinity;
            let bestCluster = 0;

            for (let j = 0; j < centroids.length; j++) {
                const dist = textDistance(nodes[i], centroids[j]);
                if (dist < minDist) {
                    minDist = dist;
                    bestCluster = j;
                }
            }

            if (assignments[i] !== bestCluster) {
                assignments[i] = bestCluster;
                changed = true;
            }
        }

        // Update centroids
        for (let j = 0; j < centroids.length; j++) {
            const clusterNodes = nodes.filter((_, i) => assignments[i] === j);
            if (clusterNodes.length > 0) {
                centroids[j] = clusterNodes[Math.floor(clusterNodes.length / 2)];
            }
        }

        iterations++;
    }

    // Group by cluster
    const clusters = [];
    for (let j = 0; j < centroids.length; j++) {
        clusters.push(
            nodes.filter((_, i) => assignments[i] === j).map(n => n.id)
        );
    }

    return {
        clusters: clusters.filter(c => c.length > 0),
        clusterCount: clusters.filter(c => c.length > 0).length
    };
}

/**
 * Simple Louvain-like clustering
 */
function louvainClustering() {
    // Simplified community detection
    // Each node starts in its own community
    const communities = new Map();
    graphData.nodes.forEach((n, i) => communities.set(n.id, i));

    let improved = true;
    let iterations = 0;
    const MAX_ITERATIONS = 10;

    while (improved && iterations < MAX_ITERATIONS) {
        improved = false;

        for (const node of graphData.nodes) {
            // Find best community for this node
            const neighbors = getNeighbors(node.id);
            const communityWeights = new Map();

            for (const neighborId of neighbors) {
                const community = communities.get(neighborId);
                communityWeights.set(community, (communityWeights.get(community) || 0) + 1);
            }

            // Move to community with most connections
            if (communityWeights.size > 0) {
                const bestCommunity = [...communityWeights.entries()]
                    .reduce((a, b) => a[1] > b[1] ? a : b)[0];

                if (communities.get(node.id) !== bestCommunity) {
                    communities.set(node.id, bestCommunity);
                    improved = true;
                }
            }
        }

        iterations++;
    }

    // Group nodes by community
    const clusterMap = new Map();
    for (const [nodeId, community] of communities.entries()) {
        if (!clusterMap.has(community)) clusterMap.set(community, []);
        clusterMap.get(community).push(nodeId);
    }

    return {
        clusters: [...clusterMap.values()],
        clusterCount: clusterMap.size
    };
}

// ===========================
// SIMILARITY COMPUTATION
// ===========================

function computeSimilarityMatrix(data) {
    const { nodes } = data;
    const matrix = [];

    for (let i = 0; i < nodes.length; i++) {
        const row = [];
        for (let j = 0; j < nodes.length; j++) {
            if (i === j) {
                row.push(1.0);
            } else {
                row.push(textSimilarity(nodes[i], nodes[j]));
            }
        }
        matrix.push(row);

        // Send progress
        if (i % 10 === 0) {
            self.postMessage({
                type: 'similarityProgress',
                progress: (i / nodes.length) * 100
            });
        }
    }

    return matrix;
}

// ===========================
// TEXT PROCESSING
// ===========================

function processText(data) {
    const { text, operations } = data;
    let result = text;

    for (const op of operations) {
        switch (op.type) {
            case 'tokenize':
                result = tokenize(result);
                break;
            case 'normalize':
                result = normalize(result);
                break;
            case 'extractKeywords':
                result = extractKeywords(result);
                break;
        }
    }

    return result;
}

function tokenize(text) {
    return text.toLowerCase()
        .split(/\W+/)
        .filter(token => token.length > 0);
}

function normalize(text) {
    return text.toLowerCase()
        .replace(/[^\w\s]/g, '')
        .trim();
}

function extractKeywords(text, count = 5) {
    const words = tokenize(text);
    const wordCount = new Map();

    for (const word of words) {
        if (word.length > 3) { // Skip short words
            wordCount.set(word, (wordCount.get(word) || 0) + 1);
        }
    }

    return [...wordCount.entries()]
        .sort((a, b) => b[1] - a[1])
        .slice(0, count)
        .map(([word]) => word);
}

// ===========================
// SEARCH INDEXING
// ===========================

function buildSearchIndex(nodes) {
    const index = new Map();

    for (const node of nodes) {
        const text = (node.label || node.text || '').toLowerCase();
        const tokens = tokenize(text);

        for (const token of tokens) {
            if (!index.has(token)) index.set(token, []);
            index.get(token).push(node.id);
        }
    }

    return index;
}

function performSearch(data) {
    const { query, limit = 50 } = data;
    const tokens = tokenize(query.toLowerCase());
    const scores = new Map();

    // Score nodes by token matches
    for (const token of tokens) {
        const nodeIds = searchIndex.get(token) || [];
        for (const nodeId of nodeIds) {
            scores.set(nodeId, (scores.get(nodeId) || 0) + 1);
        }
    }

    // Sort by score and return top results
    const results = [...scores.entries()]
        .sort((a, b) => b[1] - a[1])
        .slice(0, limit)
        .map(([nodeId, score]) => ({
            nodeId,
            score,
            node: graphData.nodes.find(n => n.id === nodeId)
        }));

    return {
        results,
        count: results.length,
        query
    };
}

// ===========================
// UTILITY FUNCTIONS
// ===========================

function getNeighbors(nodeId) {
    const neighbors = [];

    for (const link of graphData.links) {
        const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
        const targetId = typeof link.target === 'object' ? link.target.id : link.target;

        if (sourceId === nodeId) {
            neighbors.push(targetId);
        } else if (targetId === nodeId) {
            neighbors.push(sourceId);
        }
    }

    return neighbors;
}

function textSimilarity(nodeA, nodeB) {
    const textA = (nodeA.label || nodeA.text || '').toLowerCase();
    const textB = (nodeB.label || nodeB.text || '').toLowerCase();

    if (!textA || !textB) return 0;

    const tokensA = new Set(tokenize(textA));
    const tokensB = new Set(tokenize(textB));

    const intersection = new Set([...tokensA].filter(x => tokensB.has(x)));
    const union = new Set([...tokensA, ...tokensB]);

    return intersection.size / union.size; // Jaccard similarity
}

function textDistance(nodeA, nodeB) {
    return 1 - textSimilarity(nodeA, nodeB);
}
