/**
 * Graph Module - D3.js force-directed graph rendering
 */

const GraphRenderer = {
    simulation: null,
    currentGraphData: { nodes: [], links: [] },
    selectedNodeId: null,  // Track selected node
    hoveredLinkIndices: new Set(),  // Track hovered links

    /**
     * Build unified graph from full graph data with arbitrary depth support
     */
    buildUnifiedGraph(graphData) {
        const nodes = [];
        const links = [];
        const addedNodes = new Set();

        console.log('[buildUnifiedGraph] Processing', graphData.length, 'documents');

        graphData.forEach(doc => {
            // Add document node
            const docId = doc.doc_id;
            console.log('[buildUnifiedGraph] Adding document node:', docId, doc.doc_title);
            if (!addedNodes.has(docId)) {
                nodes.push({
                    id: docId,
                    label: doc.doc_title || 'Untitled Document',
                    type: 'document',
                    fullData: doc
                });
                addedNodes.add(docId);
                console.log('[buildUnifiedGraph] Document node added to nodes array');
            }

            // Build claim map for easy lookup
            const claimMap = new Map();
            if (doc.all_claims) {
                doc.all_claims.forEach(claim => {
                    claimMap.set(claim.id, claim);
                });
            }

            // Add all claims recursively
            const addClaimRecursively = (claim, depth = 0) => {
                if (!claim || !claim.id || addedNodes.has(claim.id)) return;

                // Determine node type based on properties and depth
                let nodeType = 'sub';
                if (claim.is_super_claim) {
                    nodeType = 'super';
                } else if (depth > 1) {
                    nodeType = 'sub';
                }

                const label = claim.summary || claim.text?.substring(0, 40) || 'Claim';

                nodes.push({
                    id: claim.id,
                    label: label,
                    type: nodeType,
                    fullData: claim,
                    depth: depth
                });
                addedNodes.add(claim.id);

                // Add link from document to top-level claims
                if (depth === 0) {
                    links.push({
                        source: docId,
                        target: claim.id,
                        type: 'contains'
                    });
                }

                // Recursively add children
                if (claim.child_ids && claim.child_ids.length > 0) {
                    claim.child_ids.forEach(childId => {
                        const childClaim = claimMap.get(childId);
                        if (childClaim) {
                            // Add link from parent to child
                            links.push({
                                source: claim.id,
                                target: childId,
                                type: 'has_sub'
                            });
                            // Recursively add child
                            addClaimRecursively(childClaim, depth + 1);
                        }
                    });
                }
            };

            // Start with super-claims (top-level)
            if (doc.super_claims) {
                doc.super_claims.forEach(superClaim => {
                    addClaimRecursively(superClaim, 0);
                });
            }

            // Also add all claims that aren't already added (MVP: flat structure)
            // This ensures regular claims show up even if not marked as super-claims
            if (doc.all_claims) {
                doc.all_claims.forEach(claim => {
                    // Add the node if not already added
                    if (!addedNodes.has(claim.id)) {
                        addClaimRecursively(claim, 0);
                    }

                    // ONLY create document→claim link if one doesn't already exist
                    // (prevents duplicate overlapping links that hide connections)
                    const linkExists = links.some(link =>
                        link.source === docId &&
                        link.target === claim.id &&
                        link.type === 'contains'
                    );

                    if (!linkExists) {
                        links.push({
                            source: docId,
                            target: claim.id,
                            type: 'contains'
                        });
                    }
                });
            }

            // Add evidence
            if (doc.evidence) {
                Object.entries(doc.evidence).forEach(([claimId, evidenceList]) => {
                    evidenceList.forEach(ev => {
                        if (!ev.id) return;
                        const evId = ev.id;
                        if (!addedNodes.has(evId)) {
                            nodes.push({
                                id: evId,
                                label: ev.title || 'Evidence',
                                type: 'evidence',
                                fullData: ev
                            });
                            addedNodes.add(evId);
                        }
                        links.push({
                            source: claimId,
                            target: evId,
                            type: ev.type?.toLowerCase() || 'supports'
                        });
                    });
                });
            }
        });

        console.log('[buildUnifiedGraph] Final graph:', nodes.length, 'nodes,', links.length, 'links');
        console.log('[buildUnifiedGraph] Node types:', nodes.map(n => `${n.type}:${n.id.substring(0,8)}`));
        return { nodes, links };
    },

    /**
     * Render the force-directed graph with enhanced visuals and label collision avoidance
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

        // Calculate descendant counts for sizing
        this.calculateDescendantCounts(nodes, links);

        // Create dynamic link distances based on hierarchy
        const linkForce = d3.forceLink(links)
            .id(d => d.id)
            .distance(d => {
                // Dynamic distances: longer for parent-child, shorter for evidence
                if (d.type === 'contains') return 200;
                if (d.type === 'has_sub') return 150;
                if (d.type === 'supports' || d.type === 'contradicts') return 100;
                return 150;
            });

        const simulation = d3.forceSimulation(nodes)
            .force('link', linkForce)
            .force('charge', d3.forceManyBody().strength(-400))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collision', d3.forceCollide().radius(d => this.getNodeRadius(d.type) + 10));

        // Store simulation
        this.simulation = simulation;

        // Render links with varying styles
        const link = g.append('g')
            .selectAll('line')
            .data(links)
            .enter().append('line')
            .attr('stroke', d => this.getLinkColor(d.type))
            .attr('stroke-width', d => this.getLinkWidth(d.type))
            .attr('stroke-opacity', 0.6)
            .attr('stroke-dasharray', d => this.getLinkDashArray(d.type));

        // Render nodes
        const node = g.append('g')
            .selectAll('g')
            .data(nodes)
            .enter().append('g')
            .call(d3.drag()
                .on('start', (event, d) => this.dragStarted(event, d, simulation))
                .on('drag', (event, d) => this.dragged(event, d))
                .on('end', (event, d) => this.dragEnded(event, d, simulation))
            );

        // Node circles with enhanced visual encoding
        node.append('circle')
            .attr('r', d => this.getNodeRadius(d.type, d))
            .attr('fill', d => this.getNodeColor(d.type, d))
            .attr('stroke', '#fff')
            .attr('stroke-width', d => this.getNodeBorderWidth(d))
            .attr('class', 'graph-node')
            .style('cursor', 'pointer')
            .style('transition', 'all 0.3s ease');

        // Initialize label positions (offset from nodes to reduce overlap)
        nodes.forEach((d, i) => {
            d.labelX = d.x || 0;
            d.labelY = (d.y || 0) + 30;  // Start labels below nodes
            d.labelVx = 0;
            d.labelVy = 0;
        });

        // Add text labels as separate elements with better contrast
        const labels = g.append('g')
            .selectAll('text')
            .data(nodes)
            .enter().append('text')
            .attr('data-node-id', d => d.id)  // For finding later (e.g., title updates)
            .attr('text-anchor', 'middle')
            .attr('font-size', '12px')
            .attr('fill', '#ffffff')  // White text for high contrast
            .attr('font-weight', '600')
            .attr('pointer-events', 'none')
            .style('text-shadow', '0 0 3px rgba(0,0,0,0.8), 0 0 5px rgba(0,0,0,0.6)')  // Black glow for readability
            .text(d => {
                // REQUIRE summary - no fallbacks hiding bugs!
                const summary = d.fullData?.summary;
                if (!summary && d.type !== 'document') {
                    console.error('MISSING SUMMARY for claim:', d.id, d.fullData);
                    return '[NO SUMMARY - BUG!]';
                }
                const displayText = summary || d.label;  // Documents use label (title)
                return displayText.length > 35 ? displayText.substring(0, 35) + '...' : displayText;
            });

        // Calculate label bounding boxes
        labels.each(function(d) {
            const bbox = this.getBBox();
            d.labelWidth = bbox.width;
            d.labelHeight = bbox.height;
        });

        // Add hover effects to nodes
        node.on('mouseover', (event, d) => {
            // Highlight connected links
            link
                .style('stroke-opacity', l => {
                    const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
                    const targetId = typeof l.target === 'object' ? l.target.id : l.target;
                    return (sourceId === d.id || targetId === d.id) ? 1.0 : 0.2;
                })
                .style('stroke-width', l => {
                    const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
                    const targetId = typeof l.target === 'object' ? l.target.id : l.target;
                    const baseWidth = this.getLinkWidth(l.type);
                    return (sourceId === d.id || targetId === d.id) ? baseWidth * 1.5 : baseWidth;
                });

            // Brighten hovered node
            d3.select(event.currentTarget).select('circle')
                .attr('stroke-width', 4)
                .style('filter', 'brightness(1.3)');
        });

        node.on('mouseout', (event, d) => {
            // Reset link opacity (unless a node is selected)
            if (!this.selectedNodeId) {
                link
                    .style('stroke-opacity', 0.6)
                    .style('stroke-width', l => this.getLinkWidth(l.type));
            }

            // Reset node appearance (unless it's selected)
            if (this.selectedNodeId !== d.id) {
                d3.select(event.currentTarget).select('circle')
                    .attr('stroke-width', this.getNodeBorderWidth(d))
                    .style('filter', 'none');
            }
        });

        node.on('click', (event, d) => {
            event.stopPropagation();

            // Update selected node
            const previouslySelected = this.selectedNodeId;
            this.selectedNodeId = d.id;

            // Remove selection from all nodes
            node.selectAll('circle')
                .attr('stroke', '#fff')
                .attr('stroke-width', n => this.getNodeBorderWidth(n))
                .style('filter', 'none');

            // Highlight selected node with gold glow
            d3.select(event.currentTarget).select('circle')
                .attr('stroke', '#FFD700')  // Gold
                .attr('stroke-width', 5)
                .style('filter', 'drop-shadow(0 0 8px #FFD700)');

            // Highlight connected links
            link
                .style('stroke-opacity', l => {
                    const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
                    const targetId = typeof l.target === 'object' ? l.target.id : l.target;
                    return (sourceId === d.id || targetId === d.id) ? 1.0 : 0.3;
                })
                .style('stroke-width', l => {
                    const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
                    const targetId = typeof l.target === 'object' ? l.target.id : l.target;
                    const baseWidth = this.getLinkWidth(l.type);
                    return (sourceId === d.id || targetId === d.id) ? baseWidth * 1.5 : baseWidth;
                });

            // Show details for all clickable nodes
            if (d.type === 'super' || d.type === 'sub') {
                window.showClaimDetails(d.id);
            } else if (d.type === 'document') {
                UI.showDocumentDetails(d);
            } else if (d.type === 'evidence') {
                UI.showEvidenceDetails(d);
            }
        });

        // Click on background to deselect
        svg.on('click', () => {
            this.selectedNodeId = null;
            node.selectAll('circle')
                .attr('stroke', '#fff')
                .attr('stroke-width', d => this.getNodeBorderWidth(d))
                .style('filter', 'none');
            link
                .style('stroke-opacity', 0.6)
                .style('stroke-width', l => this.getLinkWidth(l.type));
        });

        // Enhanced tick function with label collision avoidance
        simulation.on('tick', () => {
            // Apply label repulsion forces
            this.applyLabelCollisionForces(nodes);

            // Update link positions
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            // Update node positions
            node.attr('transform', d => `translate(${d.x},${d.y})`);

            // Update label positions with elastic behavior
            labels
                .attr('x', d => {
                    // Labels prefer to be near their node but will move to avoid overlap
                    d.labelX += d.labelVx;
                    d.labelVx *= 0.85;  // Damping
                    return d.labelX;
                })
                .attr('y', d => {
                    d.labelY += d.labelVy;
                    d.labelVy *= 0.85;  // Damping
                    return d.labelY;
                });
        });

        // Store current graph data
        this.currentGraphData = { nodes, links };
    },

    /**
     * Calculate descendant counts for all nodes
     */
    calculateDescendantCounts(nodes, links) {
        const nodeMap = new Map(nodes.map(n => [n.id, n]));

        nodes.forEach(node => {
            node.descendantCount = 0;
        });

        // Count children recursively
        const countDescendants = (nodeId, visited = new Set()) => {
            if (visited.has(nodeId)) return 0;
            visited.add(nodeId);

            let count = 0;
            links.forEach(link => {
                const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
                if (sourceId === nodeId) {
                    const targetId = typeof link.target === 'object' ? link.target.id : link.target;
                    count += 1 + countDescendants(targetId, visited);
                }
            });
            return count;
        };

        nodes.forEach(node => {
            node.descendantCount = countDescendants(node.id);
        });
    },

    /**
     * Apply repulsion forces between overlapping labels
     */
    applyLabelCollisionForces(nodes) {
        const REPULSION_STRENGTH = 0.5;
        const ANCHOR_STRENGTH = 0.05;

        for (let i = 0; i < nodes.length; i++) {
            for (let j = i + 1; j < nodes.length; j++) {
                const a = nodes[i];
                const b = nodes[j];

                // Check if labels overlap
                const dx = b.labelX - a.labelX;
                const dy = b.labelY - a.labelY;
                const distance = Math.sqrt(dx * dx + dy * dy);

                const minDistance = (a.labelWidth + b.labelWidth) / 2 + 10;  // 10px padding

                if (distance < minDistance && distance > 0) {
                    // Labels overlap - apply repulsion
                    const force = (minDistance - distance) / distance * REPULSION_STRENGTH;
                    const fx = dx * force;
                    const fy = dy * force;

                    a.labelVx -= fx;
                    a.labelVy -= fy;
                    b.labelVx += fx;
                    b.labelVy += fy;
                }
            }

            // Pull labels back toward their nodes (elastic anchor)
            const node = nodes[i];
            const targetY = node.y + 30;  // Prefer position below node
            const anchorDx = node.x - node.labelX;
            const anchorDy = targetY - node.labelY;

            node.labelVx += anchorDx * ANCHOR_STRENGTH;
            node.labelVy += anchorDy * ANCHOR_STRENGTH;
        }
    },

    /**
     * Get link width based on type
     */
    getLinkWidth(type) {
        const widths = {
            'contains': 3,
            'has_sub': 2,
            'supports': 2.5,
            'contradicts': 2.5
        };
        return widths[type] || 2;
    },

    /**
     * Get link dash array for styling (solid vs dashed)
     */
    getLinkDashArray(type) {
        if (type === 'contradicts') {
            return '5,5';  // Dashed line for contradictions
        }
        return 'none';  // Solid line for everything else
    },

    /**
     * Get node border width based on confidence
     */
    getNodeBorderWidth(node) {
        // Use confidence from node data if available
        const confidence = node.fullData?.confidence || 0.5;
        return 2 + (confidence * 3);  // 2-5px border based on confidence
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
     * Add a single node incrementally with gentle growth animation
     * @param {Object} nodeData - The node data including id, type, label, fullData
     * @param {String} parentId - Optional parent node ID to position near
     */
    addNodeIncremental(nodeData, parentId = null) {
        console.log(`[addNodeIncremental] Adding node: ${nodeData.id} (${nodeData.type}), parent: ${parentId || 'none'}`);

        // Check if node already exists
        const existingNode = this.currentGraphData.nodes.find(n => n.id === nodeData.id);
        if (existingNode) {
            console.log('[addNodeIncremental] Node already exists:', nodeData.id);
            return;
        }

        // Position new node near parent or center
        const svg = d3.select('#graph-svg');
        const width = svg.node().getBoundingClientRect().width;
        const height = svg.node().getBoundingClientRect().height;

        let startX = width / 2;
        let startY = height / 2;

        if (parentId) {
            const parentNode = this.currentGraphData.nodes.find(n => n.id === parentId);
            if (parentNode && parentNode.x !== undefined) {
                // Position near parent with small random offset
                startX = parentNode.x + (Math.random() - 0.5) * 100;
                startY = parentNode.y + (Math.random() - 0.5) * 100;
            }
        }

        // Initialize node position
        nodeData.x = startX;
        nodeData.y = startY;
        nodeData.vx = 0;
        nodeData.vy = 0;

        // Add to current graph data
        this.currentGraphData.nodes.push(nodeData);

        // Create link if parent exists
        if (parentId) {
            // Determine link type based on PARENT type, not child type
            const parentNode = this.currentGraphData.nodes.find(n => n.id === parentId);
            const linkType = (parentNode && parentNode.type === 'document') ? 'contains' : 'has_sub';

            console.log(`[addNodeIncremental] Creating ${linkType} link from ${parentNode?.type || 'unknown'} to ${nodeData.type}`);

            this.currentGraphData.links.push({
                source: parentId,
                target: nodeData.id,
                type: linkType
            });
        }

        // SIMPLE APPROACH: Just re-render the entire graph
        // This ensures all nodes and links are properly registered with the simulation
        console.log(`[addNodeIncremental] Re-rendering graph with ${this.currentGraphData.nodes.length} nodes`);
        this.renderGraph(this.currentGraphData.nodes, this.currentGraphData.links);
    },

    /**
     * Update node label (e.g., when document title is extracted)
     * @param {String} nodeId - Node ID to update
     * @param {String} newLabel - New label text
     */
    updateNodeLabel(nodeId, newLabel) {
        console.log('Updating node label:', nodeId, newLabel);

        // Update in-memory data
        const node = this.currentGraphData.nodes.find(n => n.id === nodeId);
        if (node) {
            node.label = newLabel;
            if (node.fullData) {
                node.fullData.title = newLabel;
            }
        }

        // Update SVG label
        const svg = d3.select('#graph-svg');
        svg.select(`text[data-node-id="${nodeId}"]`)
            .transition()
            .duration(500)
            .style('opacity', 0)
            .transition()
            .duration(500)
            .text(newLabel.length > 35 ? newLabel.substring(0, 35) + '...' : newLabel)
            .style('opacity', 1);

        console.log('✓ Node label updated');
    },

    /**
     * Update a claim node after processing completes
     * Transitions from "skeleton" state to "complete" state with visual feedback
     * @param {String} claimId - Claim node ID
     * @param {Object} updates - Updated node properties
     */
    updateClaimNode(claimId, updates) {
        console.log('Updating claim node:', claimId, updates);

        // Update in-memory data
        const node = this.currentGraphData.nodes.find(n => n.id === claimId);
        if (node) {
            Object.assign(node, updates);
            if (node.fullData) {
                Object.assign(node.fullData, updates);
            }
            node.label = updates.summary || updates.text;
        }

        // Update SVG appearance with quality-based color
        const svg = d3.select('#graph-svg');

        // Color map based on disposition (quality assessment)
        const colorMap = {
            'central': '#4CAF50',      // Green - important claims
            'child': '#2196F3',         // Blue - supporting claims
            'review': '#FF9800',        // Orange - needs review
            'discard': '#F44336'        // Red - low quality
        };
        const newColor = colorMap[updates.disposition] || '#2196F3';

        // Update circle with smooth color transition
        svg.select(`circle[data-node-id="${claimId}"]`)
            .transition()
            .duration(1000)
            .attr('fill', newColor)
            .attr('stroke-width', 3)
            .attr('stroke', '#fff')
            .style('opacity', 1.0);  // Fully opaque (no longer processing)

        // Update text label with fade-out/fade-in transition
        const displayText = updates.summary || updates.text;
        const truncated = displayText.length > 35
            ? displayText.substring(0, 35) + '...'
            : displayText;

        svg.select(`text[data-node-id="${claimId}"]`)
            .transition()
            .duration(500)
            .style('opacity', 0)
            .transition()
            .duration(500)
            .text(truncated)
            .style('opacity', 1)
            .style('font-weight', '700');  // Bold when complete

        console.log('✓ Claim node updated to complete state');
    },

    /**
     * Update document processing progress with circular indicator
     * @param {String} docId - Document node ID
     * @param {Number} progress - Progress percentage (0-100)
     */
    updateDocumentProgress(docId, progress) {
        const svg = d3.select('#graph-svg');
        const progressArc = svg.selectAll(`g`).filter(d => d && d.id === docId)
            .select('.progress-arc');

        if (progressArc.empty()) return;

        const node = this.currentGraphData.nodes.find(n => n.id === docId);
        if (!node) return;

        const radius = this.getNodeRadius('document', node);
        const arc = d3.arc()
            .innerRadius(radius + 2)
            .outerRadius(radius + 5)
            .startAngle(0)
            .endAngle((progress / 100) * 2 * Math.PI);

        progressArc.transition()
            .duration(300)
            .attrTween('d', function() {
                const interpolate = d3.interpolate(this._current || 0, (progress / 100) * 2 * Math.PI);
                this._current = (progress / 100) * 2 * Math.PI;
                return (t) => arc({endAngle: interpolate(t)});
            });
    },

    /**
     * Mark document as complete and remove processing indicator
     * @param {String} docId - Document node ID
     */
    markDocumentComplete(docId) {
        const svg = d3.select('#graph-svg');
        const progressArc = svg.selectAll(`g`).filter(d => d && d.id === docId)
            .select('.progress-arc');

        if (!progressArc.empty()) {
            progressArc.transition()
                .duration(500)
                .attr('opacity', 0)
                .remove();
        }

        // Update node data
        const node = this.currentGraphData.nodes.find(n => n.id === docId);
        if (node) {
            node.processing = false;
        }
    },

    /**
     * Clear fresh flags from all nodes and stop pulsing animation
     */
    clearFreshFlags() {
        const svg = d3.select('#graph-svg');

        svg.selectAll('circle.graph-node').each(function(d) {
            if (d && d.fresh) {
                // Stop all transitions on this element
                d3.select(this).interrupt();
                // Remove the glow
                d3.select(this).transition()
                    .duration(1000)
                    .style('filter', 'none');
                // Clear fresh flag
                d.fresh = false;
            }
        });
    },

    /**
     * Get node color based on type and data attributes
     * Color encodes confidence and quality
     */
    getNodeColor(type, node) {
        // Check for disposition-based coloring first (NEW schema)
        const disposition = node?.fullData?.disposition || node?.disposition;
        if (disposition) {
            const dispositionColors = {
                'central': '#4CAF50',      // Green - important/central claims
                'child': '#2196F3',         // Blue - supporting/child claims
                'review': '#FF9800',        // Orange - needs review
                'discard': '#F44336'        // Red - low quality/discard
            };
            if (dispositionColors[disposition]) {
                return dispositionColors[disposition];
            }
        }

        // Fall back to type-based coloring (OLD schema compatibility)
        const baseColors = {
            'document': { r: 76, g: 175, b: 80 },    // Green
            'super': { r: 33, g: 150, b: 243 },       // Blue
            'sub': { r: 156, g: 39, b: 176 },         // Purple
            'evidence': { r: 255, g: 152, b: 0 }      // Orange
        };

        const base = baseColors[type] || { r: 153, g: 153, b: 153 };

        // Modulate brightness based on confidence/quality
        const quality = node?.fullData?.quality_score || node?.fullData?.confidence || 0.7;
        const brightness = 0.6 + (quality * 0.4);  // 60-100% brightness

        const r = Math.round(base.r * brightness);
        const g = Math.round(base.g * brightness);
        const b = Math.round(base.b * brightness);

        return `rgb(${r},${g},${b})`;
    },

    /**
     * Get node radius based on type and descendant count
     * Size encodes number of children
     */
    getNodeRadius(type, node) {
        const baseRadii = {
            'document': 25,
            'super': 20,
            'sub': 15,
            'evidence': 12
        };

        let baseRadius = baseRadii[type] || 15;

        // Scale based on descendant count
        if (node && node.descendantCount !== undefined) {
            const scaleFactor = Math.log(node.descendantCount + 1) * 3;
            baseRadius += scaleFactor;
        }

        return Math.min(baseRadius, 40);  // Cap at 40px
    },

    /**
     * Get link color based on type
     */
    getLinkColor(type) {
        const colors = {
            'contains': '#9C27B0',      // Purple - document contains claims
            'has_sub': '#2196F3',       // Blue - claim has sub-claims
            'supports': '#4CAF50',      // Green - supports
            'contradicts': '#F44336'    // Red - contradicts
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
