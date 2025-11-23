/**
 * Node Clustering Module
 * Provides clustering algorithms for grouping similar nodes
 */

const NodeClusterer = {
    currentMethod: 'none',
    showHulls: false,

    /**
     * Apply clustering to nodes
     */
    async clusterBySimilarity(nodes, method = 'embedding') {
        console.log(`[NodeClusterer] Clustering ${nodes.length} nodes by ${method}`);

        if (method === 'embedding') {
            return this.clusterByEmbedding(nodes);
        } else if (method === 'type') {
            return this.clusterByType(nodes);
        } else if (method === 'confidence') {
            return this.clusterByConfidence(nodes);
        }

        return this.getClusterInfo(nodes);
    },

    /**
     * Cluster by node type
     */
    clusterByType(nodes) {
        console.log('[NodeClusterer] Clustering by type');

        const clusters = new Map();
        let clusterId = 0;

        nodes.forEach(node => {
            if (!clusters.has(node.type)) {
                clusters.set(node.type, clusterId++);
            }
            node.cluster = clusters.get(node.type);
        });

        return this.getClusterInfo(nodes);
    },

    /**
     * Cluster by confidence score
     */
    clusterByConfidence(nodes) {
        console.log('[NodeClusterer] Clustering by confidence');

        // Define confidence ranges
        const ranges = [
            { min: 0, max: 0.3, id: 0, label: 'Low Confidence' },
            { min: 0.3, max: 0.6, id: 1, label: 'Medium Confidence' },
            { min: 0.6, max: 1.0, id: 2, label: 'High Confidence' }
        ];

        nodes.forEach(node => {
            const confidence = node.fullData?.confidence || 0.5;
            const range = ranges.find(r => confidence >= r.min && confidence < r.max) || ranges[1];
            node.cluster = range.id;
        });

        return this.getClusterInfo(nodes);
    },

    /**
     * Cluster by embeddings using k-means
     */
    async clusterByEmbedding(nodes) {
        console.log('[NodeClusterer] Clustering by embeddings (simulated)');

        // Since we don't have actual embeddings, we'll simulate clustering
        // based on text similarity using a simple hash-based approach

        const k = Math.min(5, Math.max(2, Math.floor(nodes.length / 10)));
        console.log(`[NodeClusterer] Using k=${k} clusters`);

        // Create pseudo-embeddings from text
        const embeddings = nodes.map(node => {
            const text = node.label || node.fullData?.summary || node.fullData?.text || '';
            return this.textToVector(text);
        });

        // Apply k-means
        const assignments = this.kmeans(embeddings, k);

        // Assign clusters
        nodes.forEach((node, i) => {
            node.cluster = assignments[i];
        });

        return this.getClusterInfo(nodes);
    },

    /**
     * Convert text to simple vector representation
     */
    textToVector(text, dimensions = 10) {
        const vector = new Array(dimensions).fill(0);
        const words = text.toLowerCase().split(/\s+/);

        words.forEach((word, i) => {
            const hash = this.simpleHash(word);
            vector[hash % dimensions] += 1;
        });

        // Normalize
        const magnitude = Math.sqrt(vector.reduce((sum, v) => sum + v * v, 0));
        return magnitude > 0 ? vector.map(v => v / magnitude) : vector;
    },

    /**
     * Simple string hash function
     */
    simpleHash(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32bit integer
        }
        return Math.abs(hash);
    },

    /**
     * K-means clustering algorithm
     */
    kmeans(data, k, maxIterations = 50) {
        if (data.length === 0) return [];
        if (k >= data.length) {
            return data.map((_, i) => i);
        }

        const dimensions = data[0].length;

        // Initialize centroids randomly
        let centroids = this.initializeCentroids(data, k);
        let assignments = new Array(data.length).fill(0);

        for (let iter = 0; iter < maxIterations; iter++) {
            let changed = false;

            // Assignment step
            data.forEach((point, i) => {
                const nearest = this.findNearestCentroid(point, centroids);
                if (assignments[i] !== nearest) {
                    assignments[i] = nearest;
                    changed = true;
                }
            });

            if (!changed) {
                console.log(`[NodeClusterer] K-means converged after ${iter} iterations`);
                break;
            }

            // Update step
            centroids = this.updateCentroids(data, assignments, k);
        }

        return assignments;
    },

    /**
     * Initialize centroids using k-means++ algorithm
     */
    initializeCentroids(data, k) {
        const centroids = [];

        // Choose first centroid randomly
        const firstIndex = Math.floor(Math.random() * data.length);
        centroids.push([...data[firstIndex]]);

        // Choose remaining centroids
        for (let i = 1; i < k; i++) {
            const distances = data.map(point => {
                const minDist = Math.min(...centroids.map(c => this.euclideanDistance(point, c)));
                return minDist * minDist;
            });

            const totalDist = distances.reduce((sum, d) => sum + d, 0);
            let random = Math.random() * totalDist;

            for (let j = 0; j < data.length; j++) {
                random -= distances[j];
                if (random <= 0) {
                    centroids.push([...data[j]]);
                    break;
                }
            }
        }

        return centroids;
    },

    /**
     * Find nearest centroid to a point
     */
    findNearestCentroid(point, centroids) {
        let minDist = Infinity;
        let nearest = 0;

        centroids.forEach((centroid, i) => {
            const dist = this.euclideanDistance(point, centroid);
            if (dist < minDist) {
                minDist = dist;
                nearest = i;
            }
        });

        return nearest;
    },

    /**
     * Calculate euclidean distance between two vectors
     */
    euclideanDistance(a, b) {
        let sum = 0;
        for (let i = 0; i < a.length; i++) {
            sum += (a[i] - b[i]) ** 2;
        }
        return Math.sqrt(sum);
    },

    /**
     * Update centroids based on current assignments
     */
    updateCentroids(data, assignments, k) {
        const centroids = [];
        const dimensions = data[0].length;

        for (let i = 0; i < k; i++) {
            const clusterPoints = data.filter((_, idx) => assignments[idx] === i);

            if (clusterPoints.length === 0) {
                // If cluster is empty, reinitialize randomly
                centroids.push([...data[Math.floor(Math.random() * data.length)]]);
            } else {
                const centroid = new Array(dimensions).fill(0);
                clusterPoints.forEach(point => {
                    point.forEach((val, dim) => {
                        centroid[dim] += val;
                    });
                });
                centroids.push(centroid.map(v => v / clusterPoints.length));
            }
        }

        return centroids;
    },

    /**
     * Get cluster information
     */
    getClusterInfo(nodes) {
        const clusters = d3.group(nodes, d => d.cluster);
        const info = Array.from(clusters.entries()).map(([clusterId, clusterNodes]) => ({
            id: clusterId,
            size: clusterNodes.length,
            nodes: clusterNodes
        }));

        console.log(`[NodeClusterer] Created ${info.length} clusters:`, info.map(c => `Cluster ${c.id}: ${c.size} nodes`));
        return info;
    }
};

/**
 * Cluster Visualizer
 * Renders cluster boundaries and visual indicators
 */
const ClusterVisualizer = {
    /**
     * Show cluster boundaries (convex hulls)
     */
    showClusters(nodes) {
        console.log('[ClusterVisualizer] Drawing cluster boundaries');

        const svg = d3.select('#graph-svg');
        const g = svg.select('g');

        // Remove existing hulls
        g.selectAll('.cluster-hull').remove();

        // Group by cluster
        const clusters = d3.group(nodes, d => d.cluster !== undefined ? d.cluster : -1);

        // Draw hull for each cluster
        clusters.forEach((clusterNodes, clusterId) => {
            if (clusterId === -1 || clusterNodes.length < 3) return; // Skip unclustered or too small

            const hull = this.convexHull(clusterNodes);
            if (hull) {
                this.drawHull(hull, clusterId, g);
            }
        });
    },

    /**
     * Hide cluster boundaries
     */
    hideClusters() {
        const svg = d3.select('#graph-svg');
        svg.selectAll('.cluster-hull').remove();
    },

    /**
     * Compute convex hull of points
     */
    convexHull(nodes) {
        const points = nodes
            .filter(n => n.x !== undefined && n.y !== undefined)
            .map(n => [n.x, n.y]);

        if (points.length < 3) return null;

        return d3.polygonHull(points);
    },

    /**
     * Draw cluster hull
     */
    drawHull(hull, clusterId, container) {
        if (!hull) return;

        const color = this.getClusterColor(clusterId);

        // Add padding to hull
        const paddedHull = this.expandPolygon(hull, 30);

        container.insert('path', ':first-child') // Insert at beginning so it's behind nodes
            .datum(paddedHull)
            .attr('class', 'cluster-hull')
            .attr('d', d => `M${d.join('L')}Z`)
            .style('fill', color)
            .style('fill-opacity', 0.1)
            .style('stroke', color)
            .style('stroke-width', 2)
            .style('stroke-dasharray', '5,5')
            .style('pointer-events', 'none')
            .transition()
            .duration(500)
            .style('fill-opacity', 0.15);
    },

    /**
     * Expand polygon outward by distance
     */
    expandPolygon(polygon, distance) {
        const centroid = d3.polygonCentroid(polygon);

        return polygon.map(point => {
            const dx = point[0] - centroid[0];
            const dy = point[1] - centroid[1];
            const length = Math.sqrt(dx * dx + dy * dy);
            const scale = (length + distance) / length;

            return [
                centroid[0] + dx * scale,
                centroid[1] + dy * scale
            ];
        });
    },

    /**
     * Get color for cluster
     */
    getClusterColor(clusterId) {
        const colors = [
            '#2196F3', // Blue
            '#4CAF50', // Green
            '#FF9800', // Orange
            '#9C27B0', // Purple
            '#F44336', // Red
            '#00BCD4', // Cyan
            '#FFEB3B', // Yellow
            '#E91E63', // Pink
        ];

        return colors[clusterId % colors.length];
    }
};

// Global handler for cluster method change
function handleClusterChange(method) {
    NodeClusterer.currentMethod = method;

    if (method === 'none') {
        // Clear clusters
        GraphRenderer.currentGraphData.nodes.forEach(n => delete n.cluster);
        ClusterVisualizer.hideClusters();
        console.log('[Clustering] Clustering disabled');
    } else {
        // Apply clustering
        NodeClusterer.clusterBySimilarity(GraphRenderer.currentGraphData.nodes, method)
            .then(clusterInfo => {
                console.log(`[Clustering] Applied ${method} clustering:`, clusterInfo);

                // Show hulls if checkbox is enabled
                const showHullsCheckbox = document.getElementById('show-cluster-hulls');
                if (showHullsCheckbox && showHullsCheckbox.checked) {
                    ClusterVisualizer.showClusters(GraphRenderer.currentGraphData.nodes);
                }
            });
    }
}

function toggleClusterHulls(show) {
    NodeClusterer.showHulls = show;

    if (show && NodeClusterer.currentMethod !== 'none') {
        ClusterVisualizer.showClusters(GraphRenderer.currentGraphData.nodes);
    } else {
        ClusterVisualizer.hideClusters();
    }
}
