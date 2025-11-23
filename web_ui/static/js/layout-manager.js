/**
 * Layout Manager - Manages multiple graph layout algorithms
 * Provides 5 layout options: Force-Directed, Hierarchical, Circular, Grid, and Radial
 */

const LayoutManager = {
    currentLayout: 'force',
    layouts: {},

    /**
     * Initialize layout manager
     */
    init() {
        this.layouts = {
            force: new ForceDirectedLayout(),
            hierarchical: new HierarchicalLayout(),
            circular: new CircularLayout(),
            grid: new GridLayout(),
            radial: new RadialLayout()
        };
        console.log('[LayoutManager] Initialized with 5 layout algorithms');
    },

    /**
     * Apply a specific layout to the graph
     */
    setLayout(layoutName) {
        if (!this.layouts[layoutName]) {
            console.error('[LayoutManager] Invalid layout:', layoutName);
            return;
        }

        console.log(`[LayoutManager] Switching to ${layoutName} layout`);
        this.currentLayout = layoutName;

        const layout = this.layouts[layoutName];
        const svg = d3.select('#graph-svg');
        const width = svg.node().getBoundingClientRect().width;
        const height = svg.node().getBoundingClientRect().height;

        layout.apply(GraphRenderer.currentGraphData.nodes, GraphRenderer.currentGraphData.links, width, height);

        // Update UI
        document.querySelectorAll('#layout-selector option').forEach(opt => {
            opt.selected = opt.value === layoutName;
        });
    }
};

/**
 * Force-Directed Layout (enhanced version of existing)
 */
class ForceDirectedLayout {
    constructor() {
        this.simulation = null;
    }

    apply(nodes, links, width, height) {
        console.log('[ForceDirectedLayout] Applying force-directed layout');

        // Stop existing simulation if any
        if (GraphRenderer.simulation) {
            GraphRenderer.simulation.stop();
        }

        // Create new force simulation
        const simulation = d3.forceSimulation(nodes)
            .force('link', d3.forceLink(links)
                .id(d => d.id)
                .distance(d => {
                    if (d.type === 'sourced_from') return 170;
                    if (d.type === 'created') return 180;
                    if (d.type === 'contains') return 200;
                    if (d.type === 'has_sub') return 150;
                    if (d.type === 'supports' || d.type === 'contradicts') return 100;
                    return 150;
                })
            )
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collision', d3.forceCollide().radius(d => GraphRenderer.getNodeRadius(d.type, d) + 10));

        // Store and start simulation
        GraphRenderer.simulation = simulation;
        simulation.alpha(1).restart();

        console.log('[ForceDirectedLayout] Force simulation started');
    }
}

/**
 * Hierarchical Tree Layout
 */
class HierarchicalLayout {
    apply(nodes, links, width, height) {
        console.log('[HierarchicalLayout] Applying hierarchical tree layout');

        // Build hierarchy structure
        const roots = this.findRootNodes(nodes, links);
        console.log(`[HierarchicalLayout] Found ${roots.length} root nodes`);

        if (roots.length === 0) {
            console.warn('[HierarchicalLayout] No root nodes found, using first node');
            roots.push(nodes[0]);
        }

        // For each root, build a tree and position it
        const treeWidth = width / roots.length;

        roots.forEach((root, index) => {
            const tree = this.buildTree(root, nodes, links);
            const treeLayout = d3.tree()
                .size([treeWidth - 100, height - 100])
                .separation((a, b) => a.parent === b.parent ? 1 : 2);

            const hierarchyRoot = d3.hierarchy(tree);
            const treeData = treeLayout(hierarchyRoot);

            // Position nodes
            treeData.descendants().forEach(d => {
                const node = nodes.find(n => n.id === d.data.id);
                if (node) {
                    node.x = d.x + (index * treeWidth) + treeWidth / 2;
                    node.y = d.y + 50;
                    node.fx = node.x; // Fix position
                    node.fy = node.y;
                }
            });
        });

        this.animateToPositions(nodes);
    }

    findRootNodes(nodes, links) {
        // Find nodes with no incoming edges (potential roots)
        const hasIncoming = new Set();
        links.forEach(l => {
            const targetId = typeof l.target === 'object' ? l.target.id : l.target;
            hasIncoming.add(targetId);
        });

        const roots = nodes.filter(n => !hasIncoming.has(n.id));

        // Prioritize document and source nodes
        return roots.filter(n => n.type === 'document' || n.type === 'source')
            .concat(roots.filter(n => n.type !== 'document' && n.type !== 'source'));
    }

    buildTree(root, nodes, links) {
        const tree = {
            id: root.id,
            children: []
        };

        const visited = new Set([root.id]);
        const queue = [tree];

        while (queue.length > 0) {
            const current = queue.shift();
            const currentId = current.id;

            // Find children
            const children = links
                .filter(l => {
                    const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
                    return sourceId === currentId;
                })
                .map(l => typeof l.target === 'object' ? l.target.id : l.target)
                .filter(childId => !visited.has(childId));

            children.forEach(childId => {
                visited.add(childId);
                const childNode = {
                    id: childId,
                    children: []
                };
                current.children.push(childNode);
                queue.push(childNode);
            });
        }

        return tree;
    }

    animateToPositions(nodes) {
        const svg = d3.select('#graph-svg');

        svg.selectAll('g').filter(d => d && d.id)
            .transition()
            .duration(1000)
            .attr('transform', d => `translate(${d.x},${d.y})`);

        svg.selectAll('text').filter(d => d && d.id)
            .transition()
            .duration(1000)
            .attr('x', d => d.x)
            .attr('y', d => d.y);
    }
}

/**
 * Circular Layout
 */
class CircularLayout {
    apply(nodes, links, width, height) {
        console.log('[CircularLayout] Applying circular layout');

        const radius = Math.min(width, height) / 2.5;
        const centerX = width / 2;
        const centerY = height / 2;
        const angleStep = (2 * Math.PI) / nodes.length;

        nodes.forEach((node, i) => {
            const angle = i * angleStep;
            node.x = centerX + radius * Math.cos(angle);
            node.y = centerY + radius * Math.sin(angle);
            node.fx = node.x;
            node.fy = node.y;
        });

        this.animateToPositions(nodes);
    }

    animateToPositions(nodes) {
        const svg = d3.select('#graph-svg');

        svg.selectAll('g').filter(d => d && d.id)
            .transition()
            .duration(1000)
            .attr('transform', d => `translate(${d.x},${d.y})`);

        svg.selectAll('text').filter(d => d && d.id)
            .transition()
            .duration(1000)
            .attr('x', d => d.x)
            .attr('y', d => d.y);
    }
}

/**
 * Grid Layout
 */
class GridLayout {
    apply(nodes, links, width, height) {
        console.log('[GridLayout] Applying grid layout');

        const cols = Math.ceil(Math.sqrt(nodes.length));
        const rows = Math.ceil(nodes.length / cols);
        const cellWidth = (width - 100) / cols;
        const cellHeight = (height - 100) / rows;

        nodes.forEach((node, i) => {
            const col = i % cols;
            const row = Math.floor(i / cols);
            node.x = 50 + col * cellWidth + cellWidth / 2;
            node.y = 50 + row * cellHeight + cellHeight / 2;
            node.fx = node.x;
            node.fy = node.y;
        });

        this.animateToPositions(nodes);
    }

    animateToPositions(nodes) {
        const svg = d3.select('#graph-svg');

        svg.selectAll('g').filter(d => d && d.id)
            .transition()
            .duration(1000)
            .attr('transform', d => `translate(${d.x},${d.y})`);

        svg.selectAll('text').filter(d => d && d.id)
            .transition()
            .duration(1000)
            .attr('x', d => d.x)
            .attr('y', d => d.y);
    }
}

/**
 * Radial Layout (grouped by type)
 */
class RadialLayout {
    apply(nodes, links, width, height) {
        console.log('[RadialLayout] Applying radial layout (grouped by type)');

        const centerX = width / 2;
        const centerY = height / 2;

        // Group nodes by type
        const grouped = d3.group(nodes, d => d.type);
        const types = Array.from(grouped.keys());

        console.log(`[RadialLayout] ${types.length} node types: ${types.join(', ')}`);

        types.forEach((type, typeIndex) => {
            const typeNodes = grouped.get(type);
            const radius = 100 + (typeIndex * 120); // Increasing radius for each type
            const angleStep = (2 * Math.PI) / typeNodes.length;

            typeNodes.forEach((node, i) => {
                const angle = i * angleStep;
                node.x = centerX + radius * Math.cos(angle);
                node.y = centerY + radius * Math.sin(angle);
                node.fx = node.x;
                node.fy = node.y;
            });
        });

        this.animateToPositions(nodes);
    }

    animateToPositions(nodes) {
        const svg = d3.select('#graph-svg');

        svg.selectAll('g').filter(d => d && d.id)
            .transition()
            .duration(1000)
            .attr('transform', d => `translate(${d.x},${d.y})`);

        svg.selectAll('text').filter(d => d && d.id)
            .transition()
            .duration(1000)
            .attr('x', d => d.x)
            .attr('y', d => d.y);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    LayoutManager.init();
});
