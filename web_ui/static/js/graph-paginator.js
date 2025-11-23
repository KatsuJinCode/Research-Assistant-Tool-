/**
 * Graph Paginator - Virtual Scrolling and Lazy Loading for Large Graphs
 *
 * Handles efficient rendering of large graphs (1000+ nodes) using:
 * - Virtual scrolling (only render visible nodes)
 * - Viewport-based rendering
 * - Level-of-detail (LOD) system
 * - Incremental layout updates
 * - On-demand loading (100 nodes at a time)
 */

class GraphPaginator {
    constructor(options = {}) {
        this.pageSize = options.pageSize || 100;
        this.visibleNodes = new Set();
        this.visibleLinks = new Set();
        this.allNodes = [];
        this.allLinks = [];
        this.currentPage = 0;
        this.totalPages = 0;
        this.viewport = {
            x: 0,
            y: 0,
            width: window.innerWidth,
            height: window.innerHeight,
            scale: 1
        };

        // LOD settings
        this.lodLevels = {
            high: { minScale: 0.8, nodeRadius: 8, showLabels: true, showDetails: true },
            medium: { minScale: 0.4, nodeRadius: 5, showLabels: true, showDetails: false },
            low: { minScale: 0.1, nodeRadius: 3, showLabels: false, showDetails: false },
            minimal: { minScale: 0, nodeRadius: 1, showLabels: false, showDetails: false }
        };

        // Performance settings
        this.maxVisibleNodes = options.maxVisibleNodes || 500;
        this.loadingThreshold = options.loadingThreshold || 0.7; // Load more when 70% scrolled
        this.cullDistance = options.cullDistance || 1000; // Cull nodes outside viewport + buffer

        // Spatial indexing for fast viewport queries
        this.spatialIndex = new QuadTree({
            x: -5000,
            y: -5000,
            width: 10000,
            height: 10000
        });

        // Loading state
        this.isLoading = false;
        this.hasMore = true;

        // Callbacks
        this.onLoadMore = options.onLoadMore || (() => {});
        this.onViewportChange = options.onViewportChange || (() => {});
        this.onNodeVisibilityChange = options.onNodeVisibilityChange || (() => {});
    }

    /**
     * Initialize paginator with full dataset
     */
    initialize(nodes, links) {
        console.log('[GraphPaginator] Initializing with', nodes.length, 'nodes and', links.length, 'links');

        this.allNodes = nodes;
        this.allLinks = links;
        this.totalPages = Math.ceil(nodes.length / this.pageSize);
        this.currentPage = 0;

        // Build spatial index for fast viewport queries
        this.rebuildSpatialIndex();

        // Load first page
        this.loadPage(0);
    }

    /**
     * Load a specific page of nodes
     */
    loadPage(pageNum) {
        if (pageNum < 0 || pageNum >= this.totalPages) {
            console.warn('[GraphPaginator] Invalid page number:', pageNum);
            return;
        }

        const startIdx = pageNum * this.pageSize;
        const endIdx = Math.min(startIdx + this.pageSize, this.allNodes.length);

        console.log('[GraphPaginator] Loading page', pageNum, 'nodes', startIdx, '-', endIdx);

        // Add nodes to visible set
        for (let i = startIdx; i < endIdx; i++) {
            const node = this.allNodes[i];
            this.visibleNodes.add(node.id);

            // Add node to spatial index if it has position
            if (node.x !== undefined && node.y !== undefined) {
                this.spatialIndex.insert({
                    x: node.x,
                    y: node.y,
                    width: 1,
                    height: 1,
                    node: node
                });
            }
        }

        // Add links connected to visible nodes
        this.updateVisibleLinks();

        this.currentPage = pageNum;
        this.hasMore = pageNum < this.totalPages - 1;

        // Notify listeners
        this.onNodeVisibilityChange(Array.from(this.visibleNodes), Array.from(this.visibleLinks));
    }

    /**
     * Load next page of nodes
     */
    loadNextPage() {
        if (this.isLoading || !this.hasMore) {
            return false;
        }

        this.isLoading = true;
        this.loadPage(this.currentPage + 1);
        this.isLoading = false;

        return true;
    }

    /**
     * Update viewport and trigger culling/LOD
     */
    updateViewport(x, y, width, height, scale) {
        this.viewport = { x, y, width, height, scale };

        // Cull nodes outside viewport
        this.cullNodesOutsideViewport();

        // Update LOD based on scale
        const lod = this.getLODLevel(scale);

        // Notify listeners
        this.onViewportChange(this.viewport, lod);

        // Check if we need to load more
        if (this.shouldLoadMore()) {
            this.loadNextPage();
        }
    }

    /**
     * Cull nodes outside viewport to improve performance
     */
    cullNodesOutsideViewport() {
        const buffer = this.cullDistance;
        const bounds = {
            x: this.viewport.x - buffer,
            y: this.viewport.y - buffer,
            width: this.viewport.width + buffer * 2,
            height: this.viewport.height + buffer * 2
        };

        // Query spatial index for nodes in viewport
        const nodesInViewport = this.spatialIndex.retrieve(bounds);
        const visibleIds = new Set(nodesInViewport.map(item => item.node.id));

        // Update visible nodes (keep at least some nodes visible)
        if (visibleIds.size > 0) {
            this.visibleNodes = visibleIds;
            this.updateVisibleLinks();
        }
    }

    /**
     * Update visible links based on visible nodes
     */
    updateVisibleLinks() {
        this.visibleLinks.clear();

        for (const link of this.allLinks) {
            const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
            const targetId = typeof link.target === 'object' ? link.target.id : link.target;

            if (this.visibleNodes.has(sourceId) && this.visibleNodes.has(targetId)) {
                this.visibleLinks.add(link);
            }
        }
    }

    /**
     * Get LOD level based on zoom scale
     */
    getLODLevel(scale) {
        if (scale >= this.lodLevels.high.minScale) return 'high';
        if (scale >= this.lodLevels.medium.minScale) return 'medium';
        if (scale >= this.lodLevels.low.minScale) return 'low';
        return 'minimal';
    }

    /**
     * Get rendering settings for current LOD level
     */
    getLODSettings() {
        const level = this.getLODLevel(this.viewport.scale);
        return this.lodLevels[level];
    }

    /**
     * Check if we should load more nodes
     */
    shouldLoadMore() {
        if (!this.hasMore || this.isLoading) {
            return false;
        }

        // Load more if visible nodes is less than threshold
        const visibleRatio = this.visibleNodes.size / this.maxVisibleNodes;
        return visibleRatio < this.loadingThreshold;
    }

    /**
     * Rebuild spatial index (call after node positions change)
     */
    rebuildSpatialIndex() {
        this.spatialIndex.clear();

        for (const node of this.allNodes) {
            if (node.x !== undefined && node.y !== undefined) {
                this.spatialIndex.insert({
                    x: node.x,
                    y: node.y,
                    width: 1,
                    height: 1,
                    node: node
                });
            }
        }
    }

    /**
     * Get visible nodes for rendering
     */
    getVisibleNodes() {
        return this.allNodes.filter(node => this.visibleNodes.has(node.id));
    }

    /**
     * Get visible links for rendering
     */
    getVisibleLinks() {
        return Array.from(this.visibleLinks);
    }

    /**
     * Add new nodes incrementally
     */
    addNodes(newNodes, newLinks) {
        console.log('[GraphPaginator] Adding', newNodes.length, 'new nodes');

        this.allNodes.push(...newNodes);
        this.allLinks.push(...newLinks);
        this.totalPages = Math.ceil(this.allNodes.length / this.pageSize);

        // Add to spatial index
        for (const node of newNodes) {
            if (node.x !== undefined && node.y !== undefined) {
                this.spatialIndex.insert({
                    x: node.x,
                    y: node.y,
                    width: 1,
                    height: 1,
                    node: node
                });
            }
        }

        this.updateVisibleLinks();
    }

    /**
     * Clear all data
     */
    clear() {
        this.allNodes = [];
        this.allLinks = [];
        this.visibleNodes.clear();
        this.visibleLinks.clear();
        this.spatialIndex.clear();
        this.currentPage = 0;
        this.totalPages = 0;
        this.hasMore = false;
    }

    /**
     * Get statistics
     */
    getStats() {
        return {
            totalNodes: this.allNodes.length,
            totalLinks: this.allLinks.length,
            visibleNodes: this.visibleNodes.size,
            visibleLinks: this.visibleLinks.size,
            currentPage: this.currentPage,
            totalPages: this.totalPages,
            loadProgress: (this.currentPage + 1) / this.totalPages,
            lodLevel: this.getLODLevel(this.viewport.scale)
        };
    }
}

/**
 * Simple QuadTree for spatial indexing
 */
class QuadTree {
    constructor(bounds, maxObjects = 10, maxLevels = 4, level = 0) {
        this.bounds = bounds; // {x, y, width, height}
        this.maxObjects = maxObjects;
        this.maxLevels = maxLevels;
        this.level = level;
        this.objects = [];
        this.nodes = [];
    }

    clear() {
        this.objects = [];
        for (const node of this.nodes) {
            node.clear();
        }
        this.nodes = [];
    }

    split() {
        const subWidth = this.bounds.width / 2;
        const subHeight = this.bounds.height / 2;
        const x = this.bounds.x;
        const y = this.bounds.y;

        this.nodes[0] = new QuadTree({
            x: x + subWidth,
            y: y,
            width: subWidth,
            height: subHeight
        }, this.maxObjects, this.maxLevels, this.level + 1);

        this.nodes[1] = new QuadTree({
            x: x,
            y: y,
            width: subWidth,
            height: subHeight
        }, this.maxObjects, this.maxLevels, this.level + 1);

        this.nodes[2] = new QuadTree({
            x: x,
            y: y + subHeight,
            width: subWidth,
            height: subHeight
        }, this.maxObjects, this.maxLevels, this.level + 1);

        this.nodes[3] = new QuadTree({
            x: x + subWidth,
            y: y + subHeight,
            width: subWidth,
            height: subHeight
        }, this.maxObjects, this.maxLevels, this.level + 1);
    }

    getIndex(rect) {
        const indexes = [];
        const verticalMidpoint = this.bounds.x + this.bounds.width / 2;
        const horizontalMidpoint = this.bounds.y + this.bounds.height / 2;

        const topQuadrant = rect.y < horizontalMidpoint && rect.y + rect.height < horizontalMidpoint;
        const bottomQuadrant = rect.y > horizontalMidpoint;

        if (rect.x < verticalMidpoint && rect.x + rect.width < verticalMidpoint) {
            if (topQuadrant) indexes.push(1);
            else if (bottomQuadrant) indexes.push(2);
        } else if (rect.x > verticalMidpoint) {
            if (topQuadrant) indexes.push(0);
            else if (bottomQuadrant) indexes.push(3);
        }

        return indexes;
    }

    insert(rect) {
        if (this.nodes.length > 0) {
            const indexes = this.getIndex(rect);
            for (const index of indexes) {
                this.nodes[index].insert(rect);
            }
            return;
        }

        this.objects.push(rect);

        if (this.objects.length > this.maxObjects && this.level < this.maxLevels) {
            if (this.nodes.length === 0) {
                this.split();
            }

            let i = 0;
            while (i < this.objects.length) {
                const indexes = this.getIndex(this.objects[i]);
                if (indexes.length > 0) {
                    for (const index of indexes) {
                        this.nodes[index].insert(this.objects.splice(i, 1)[0]);
                    }
                } else {
                    i++;
                }
            }
        }
    }

    retrieve(rect) {
        const indexes = this.getIndex(rect);
        let returnObjects = [...this.objects];

        if (this.nodes.length > 0) {
            for (const index of indexes) {
                returnObjects = returnObjects.concat(this.nodes[index].retrieve(rect));
            }
        }

        return returnObjects;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { GraphPaginator, QuadTree };
}
