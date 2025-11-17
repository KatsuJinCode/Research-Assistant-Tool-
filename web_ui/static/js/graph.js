/**
 * Graph Module - D3.js force-directed graph rendering
 */

const GraphRenderer = {
    simulation: null,
    currentGraphData: { nodes: [], links: [] },

    /**
     * Build unified graph from full graph data
     */
    buildUnifiedGraph(graphData) {
        const nodes = [];
        const links = [];

        graphData.forEach(doc => {
            // Add document node
            nodes.push({
                id: doc.doc_id,
                label: doc.doc_title || 'Untitled Document',
                type: 'document',
                fullData: doc
            });

            doc.super_claims.forEach(super_claim => {
                if (!super_claim.id) return;
                const superLabel = super_claim.summary || super_claim.text.substring(0, 40);
                nodes.push({
                    id: super_claim.id,
                    label: superLabel,
                    type: 'super',
                    fullData: super_claim
                });
                links.push({
                    source: doc.doc_id,
                    target: super_claim.id,
                    type: 'contains'
                });

                doc.sub_claims.forEach(sub => {
                    if (!sub.id || sub.parent_id !== super_claim.id) return;
                    const subLabel = sub.summary || sub.text.substring(0, 40);
                    nodes.push({
                        id: sub.id,
                        label: subLabel,
                        type: 'sub',
                        fullData: sub
                    });
                    links.push({
                        source: super_claim.id,
                        target: sub.id,
                        type: 'has_sub'
                    });
                });
            });

            doc.evidence.forEach(ev => {
                if (!ev.id || !ev.claim_id) return;
                nodes.push({
                    id: ev.id,
                    label: ev.title || 'Evidence',
                    type: 'evidence',
                    fullData: ev
                });
                links.push({
                    source: ev.claim_id,
                    target: ev.id,
                    type: ev.type || 'supports'
                });
            });
        });

        return { nodes, links };
    },

    /**
     * Render the force-directed graph
     */
    renderGraph(nodes, links) {
        const svg = d3.select('#graph-svg');
        svg.selectAll('*').remove();

        const width = svg.node().getBoundingClientRect().width;
        const height = svg.node().getBoundingClientRect().height;

        const g = svg.append('g');

        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => {
                g.attr('transform', event.transform);
            });

        svg.call(zoom);

        const simulation = d3.forceSimulation(nodes)
            .force('link', d3.forceLink(links).id(d => d.id).distance(150))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collision', d3.forceCollide().radius(40));

        // Store simulation
        this.simulation = simulation;

        const link = g.append('g')
            .selectAll('line')
            .data(links)
            .enter().append('line')
            .attr('stroke', d => this.getLinkColor(d.type))
            .attr('stroke-width', 2)
            .attr('stroke-opacity', 0.6);

        const node = g.append('g')
            .selectAll('g')
            .data(nodes)
            .enter().append('g')
            .call(d3.drag()
                .on('start', (event, d) => this.dragStarted(event, d, simulation))
                .on('drag', (event, d) => this.dragged(event, d))
                .on('end', (event, d) => this.dragEnded(event, d, simulation))
            );

        node.append('circle')
            .attr('r', d => this.getNodeRadius(d.type))
            .attr('fill', d => this.getNodeColor(d.type))
            .attr('stroke', '#fff')
            .attr('stroke-width', 2);

        node.append('text')
            .attr('dy', 25)
            .attr('text-anchor', 'middle')
            .attr('font-size', '10px')
            .attr('fill', '#333')
            .text(d => d.label.length > 30 ? d.label.substring(0, 30) + '...' : d.label);

        node.on('click', (event, d) => {
            event.stopPropagation();
            if (d.type === 'super' || d.type === 'sub') {
                window.showClaimDetails(d.id);
            }
        });

        simulation.on('tick', () => {
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            node.attr('transform', d => `translate(${d.x},${d.y})`);
        });

        // Store current graph data
        this.currentGraphData = { nodes, links };
    },

    /**
     * Smooth graph update with new data
     */
    updateGraphSmooth(graphData) {
        // If no existing graph, build from scratch
        if (!this.simulation || this.currentGraphData.nodes.length === 0) {
            const { nodes, links } = this.buildUnifiedGraph(graphData);
            this.renderGraph(nodes, links);
            return;
        }

        // Build new graph structure
        const { nodes: newNodes, links: newLinks } = this.buildUnifiedGraph(graphData);

        // Update existing nodes and add new ones
        const existingNodeIds = new Set(this.currentGraphData.nodes.map(n => n.id));
        const nodesToAdd = newNodes.filter(n => !existingNodeIds.has(n.id));

        if (nodesToAdd.length > 0) {
            // Add new nodes to simulation
            this.currentGraphData.nodes.push(...nodesToAdd);
            this.currentGraphData.links.push(...newLinks.filter(l => {
                const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
                const targetId = typeof l.target === 'object' ? l.target.id : l.target;
                return nodesToAdd.some(n => n.id === sourceId || n.id === targetId);
            }));

            this.updateGraphVisuals();
        }
    },

    /**
     * Update graph visuals with current data
     */
    updateGraphVisuals() {
        const svg = d3.select('#graph-svg');
        const g = svg.select('g');

        // Update simulation with new nodes
        if (this.simulation) {
            this.simulation.nodes(this.currentGraphData.nodes);
            this.simulation.force('link').links(this.currentGraphData.links);
            this.simulation.alpha(0.3).restart();
        }

        // Rerender (simple approach for now)
        this.renderGraph(this.currentGraphData.nodes, this.currentGraphData.links);
    },

    /**
     * Get node color based on type
     */
    getNodeColor(type) {
        const colors = {
            'document': '#4CAF50',
            'super': '#2196F3',
            'sub': '#9C27B0',
            'evidence': '#FF9800'
        };
        return colors[type] || '#999';
    },

    /**
     * Get node radius based on type
     */
    getNodeRadius(type) {
        const radii = {
            'document': 25,
            'super': 20,
            'sub': 15,
            'evidence': 12
        };
        return radii[type] || 15;
    },

    /**
     * Get link color based on type
     */
    getLinkColor(type) {
        const colors = {
            'contains': '#888',
            'has_sub': '#666',
            'supports': '#4CAF50',
            'contradicts': '#F44336'
        };
        return colors[type] || '#999';
    },

    // Drag handlers
    dragStarted(event, d, simulation) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    },

    dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    },

    dragEnded(event, d, simulation) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }
};
