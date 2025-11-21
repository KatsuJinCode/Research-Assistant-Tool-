/**
 * Graph Module - D3.js force-directed graph rendering
 */

const GraphRenderer = {
    simulation: null,
    currentGraphData: { nodes: [], links: [] },
    selectedNodeId: null,  // Track selected node
    hoveredLinkIndices: new Set(),  // Track hovered links
    searchQuery: '',  // Current search query
    activeFilters: {
        documents: true,
        claims: true,
        duplicates: true,
        minQuality: 0
    },
    filteredNodes: new Set(),  // IDs of nodes matching current filters

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

            // Add semantic relationship links (cross-document claim connections)
            if (doc.semantic_links && Array.isArray(doc.semantic_links)) {
                doc.semantic_links.forEach(link => {
                    // Only add if both nodes exist
                    if (addedNodes.has(link.source_id) && addedNodes.has(link.target_id)) {
                        links.push({
                            source: link.source_id,
                            target: link.target_id,
                            type: 'semantic_similar',
                            similarity: link.similarity_score
                        });
                    }
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

        const width = svg.node().getBoundingClientRect().width;
        const height = svg.node().getBoundingClientRect().height;

        // Check if this is an incremental update (simulation already exists and running)
        const isIncrementalUpdate = this.simulation && this.currentGraphData.nodes.length > 0;

        console.log(`[renderGraph] ${isIncrementalUpdate ? 'Incremental update' : 'Initial render'} - ${nodes.length} nodes, ${links.length} links`);

        // Clear and rebuild SVG (we have to do this to update visual elements)
        svg.selectAll('*').remove();
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

        if (isIncrementalUpdate) {
            // INCREMENTAL: Update existing simulation with new nodes/links
            console.log('[renderGraph] Updating existing simulation...');

            // Update the simulation's nodes array
            this.simulation.nodes(nodes);

            // Update the link force with new links
            this.simulation.force('link').links(links);

            // Gently restart the simulation to incorporate new nodes
            this.simulation.alpha(0.3).alphaDecay(0.05).restart();

            console.log('[renderGraph] Simulation updated and restarted');
        } else {
            // INITIAL: Create new simulation
            console.log('[renderGraph] Creating new simulation...');

            const simulation = d3.forceSimulation(nodes)
                .force('link', linkForce)
                .force('charge', d3.forceManyBody().strength(-400))
                .force('center', d3.forceCenter(width / 2, height / 2))
                .force('collision', d3.forceCollide().radius(d => this.getNodeRadius(d.type) + 10));

            // Store simulation
            this.simulation = simulation;

            console.log('[renderGraph] New simulation created');
        }

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
                .on('start', (event, d) => this.dragStarted(event, d, this.simulation))
                .on('drag', (event, d) => this.dragged(event, d))
                .on('end', (event, d) => this.dragEnded(event, d, this.simulation))
            );

        // Node circles with enhanced visual encoding
        const nodeCircle = node.append('circle')
            .attr('r', d => this.getNodeRadius(d.type, d))
            .attr('fill', d => this.getNodeColor(d.type, d))
            .attr('stroke', '#fff')
            .attr('stroke-width', d => this.getNodeBorderWidth(d))
            .attr('class', 'graph-node')
            .style('cursor', 'pointer')
            .style('transition', 'all 0.3s ease');

        // Add processing state overlay (fill effect from bottom-to-top)
        node.each(function(d) {
            if (d.processing || d.fresh) {
                const radius = GraphRenderer.getNodeRadius(d.type, d);
                const group = d3.select(this);

                // Create clip path for bottom-to-top reveal
                const clipId = `clip-${d.id.substring(0, 8)}`;
                const defs = group.append('defs');
                const clipPath = defs.append('clipPath').attr('id', clipId);
                clipPath.append('circle').attr('r', radius);

                // Add semi-transparent overlay circle that will animate
                const processingColor = d.fresh ? '#FFD700' : '#FFA500'; // Gold for new, orange for processing
                group.append('circle')
                    .attr('r', radius)
                    .attr('fill', processingColor)
                    .attr('opacity', 0.4)
                    .attr('clip-path', `url(#${clipId})`)
                    .attr('class', 'processing-overlay');

                // Add processing stage label
                const stageText = d.processingStage || 'Processing...';
                group.append('text')
                    .attr('y', 0)
                    .attr('text-anchor', 'middle')
                    .attr('font-size', '10px')
                    .attr('font-weight', 'bold')
                    .attr('fill', '#FFD700')
                    .attr('pointer-events', 'none')
                    .attr('class', 'processing-stage-label')
                    .style('text-shadow', '0 0 3px rgba(0,0,0,0.9)')
                    .text(stageText);
            }
        });

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
                // Show processing state for claims without summary yet
                const summary = d.fullData?.summary;
                if (!summary && d.type !== 'document') {
                    // Check if claim is still being processed
                    if (d.processing || d.fresh) {
                        return 'Awaiting summarization...';
                    }
                    console.warn('Claim missing summary:', d.id);
                    return 'Processing...';
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
        this.simulation.on('tick', () => {
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
        if (type === 'duplicate') {
            return '3,3';  // Dashed line for duplicates
        }
        if (type === 'semantic_similar') {
            return '2,2';  // Dotted line for semantic similarity
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
     * Calculate spawn position for new document nodes (away from existing trees)
     */
    calculateDocumentSpawnPosition(docId, canvasWidth, canvasHeight) {
        const existingDocs = this.currentGraphData.nodes.filter(n => n.type === 'document' && n.id !== docId);

        if (existingDocs.length === 0) {
            // First document - center of canvas
            return { x: canvasWidth / 2, y: canvasHeight / 2 };
        }

        // Strategy: Create a grid of potential positions around the canvas
        const minDistance = 350;  // Minimum distance from other document trees

        // Try positions in strategic locations
        const candidates = [
            { x: canvasWidth * 0.20, y: canvasHeight * 0.20 },
            { x: canvasWidth * 0.80, y: canvasHeight * 0.20 },
            { x: canvasWidth * 0.20, y: canvasHeight * 0.80 },
            { x: canvasWidth * 0.80, y: canvasHeight * 0.80 },
            { x: canvasWidth * 0.50, y: canvasHeight * 0.10 },
            { x: canvasWidth * 0.50, y: canvasHeight * 0.90 },
            { x: canvasWidth * 0.10, y: canvasHeight * 0.50 },
            { x: canvasWidth * 0.90, y: canvasHeight * 0.50 },
            // Additional corners
            { x: canvasWidth * 0.35, y: canvasHeight * 0.35 },
            { x: canvasWidth * 0.65, y: canvasHeight * 0.35 },
            { x: canvasWidth * 0.35, y: canvasHeight * 0.65 },
            { x: canvasWidth * 0.65, y: canvasHeight * 0.65 }
        ];

        // Find candidate with maximum distance from all existing documents
        let bestPos = candidates[0];
        let maxMinDistance = 0;

        for (const candidate of candidates) {
            let minDistToAnyDoc = Infinity;

            for (const doc of existingDocs) {
                if (doc.x !== undefined && doc.y !== undefined) {
                    const dist = Math.sqrt(
                        Math.pow(candidate.x - doc.x, 2) +
                        Math.pow(candidate.y - doc.y, 2)
                    );
                    minDistToAnyDoc = Math.min(minDistToAnyDoc, dist);
                }
            }

            if (minDistToAnyDoc > maxMinDistance) {
                maxMinDistance = minDistToAnyDoc;
                bestPos = candidate;
            }
        }

        console.log(`[calculateDocumentSpawnPosition] Best position: (${bestPos.x.toFixed(0)}, ${bestPos.y.toFixed(0)}) with clearance ${maxMinDistance.toFixed(0)}px`);
        return bestPos;
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

        // Position new node strategically
        const svg = d3.select('#graph-svg');
        const width = svg.node().getBoundingClientRect().width;
        const height = svg.node().getBoundingClientRect().height;

        let startX = width / 2;
        let startY = height / 2;

        // DOCUMENT NODES: Spawn away from existing document trees
        if (nodeData.type === 'document') {
            const spawnPos = this.calculateDocumentSpawnPosition(nodeData.id, width, height);
            startX = spawnPos.x;
            startY = spawnPos.y;
            console.log(`[addNodeIncremental] Document spawned at strategic position: (${startX}, ${startY})`);
        }
        // CLAIM NODES: Position near parent
        else if (parentId) {
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

        console.log(`[addNodeIncremental] Initialized position: (${startX}, ${startY})`);

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
     * Update processing stage label for a claim
     */
    updateProcessingStage(claimId, stage) {
        console.log(`[updateProcessingStage] ${claimId.substring(0,8)}: ${stage}`);

        // Update in-memory data
        const node = this.currentGraphData.nodes.find(n => n.id === claimId);
        if (node) {
            node.processingStage = stage;

            // Update the stage label in the SVG
            const svg = d3.select('#graph-svg');
            const stageLabel = svg.selectAll('g').filter(d => d && d.id === claimId)
                .select('.processing-stage-label');

            if (!stageLabel.empty()) {
                stageLabel.text(stage);
            }
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
     * Mark a claim node as duplicate of an existing claim
     */
    markClaimAsDuplicate(newClaimId, existingClaimId, similarityScore, matchQuality) {
        console.log(`[markClaimAsDuplicate] ${newClaimId.substring(0,8)} → ${existingClaimId.substring(0,8)} (${similarityScore.toFixed(2)})`);

        // Update node data
        const newNode = this.currentGraphData.nodes.find(n => n.id === newClaimId);
        const existingNode = this.currentGraphData.nodes.find(n => n.id === existingClaimId);

        if (newNode) {
            newNode.isDuplicate = true;
            newNode.duplicateOf = existingClaimId;
            newNode.duplicateSimilarity = similarityScore;
            newNode.matchQuality = matchQuality;

            // Add visual indicator in SVG
            const svg = d3.select('#graph-svg');
            const nodeGroup = svg.selectAll('g').filter(d => d && d.id === newClaimId);

            if (!nodeGroup.empty()) {
                const radius = this.getNodeRadius('sub', newNode);

                // Add dashed orange border to indicate duplicate
                nodeGroup.insert('circle', ':first-child')
                    .attr('r', radius + 3)
                    .attr('fill', 'none')
                    .attr('stroke', '#FF6B35')
                    .attr('stroke-width', 2)
                    .attr('stroke-dasharray', '4,2')
                    .attr('class', 'duplicate-indicator')
                    .style('opacity', 0)
                    .transition()
                    .duration(500)
                    .style('opacity', 0.8);

                // Add small "=" icon to indicate duplicate
                nodeGroup.append('text')
                    .attr('x', radius - 5)
                    .attr('y', -radius + 8)
                    .attr('text-anchor', 'middle')
                    .attr('font-size', '14px')
                    .attr('font-weight', 'bold')
                    .attr('fill', '#FF6B35')
                    .attr('class', 'duplicate-icon')
                    .text('≈')
                    .style('opacity', 0)
                    .transition()
                    .duration(500)
                    .style('opacity', 1);
            }

            // Add duplicate link (dashed line connecting to original)
            if (existingNode) {
                this.currentGraphData.links.push({
                    source: newClaimId,
                    target: existingClaimId,
                    type: 'duplicate',
                    similarity: similarityScore
                });

                // Update simulation with new link
                this.updateGraphSmooth(this.currentGraphData);
            }
        }
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
            'contradicts': '#F44336',   // Red - contradicts
            'duplicate': '#FF6B35',     // Orange - duplicate claim
            'semantic_similar': '#9C27B0'  // Purple - semantically similar across documents
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
    },

    /**
     * Search nodes by text query
     */
    searchNodes(query) {
        this.searchQuery = query.toLowerCase().trim();
        console.log(`[searchNodes] Query: "${this.searchQuery}"`);

        if (!this.searchQuery) {
            // Clear search - show all nodes
            this.filteredNodes.clear();
            this.applyFiltersToGraph();
            return { matches: this.currentGraphData.nodes.length, total: this.currentGraphData.nodes.length };
        }

        // Search in node text, labels, and full data
        const matchedNodes = this.currentGraphData.nodes.filter(node => {
            const label = (node.label || '').toLowerCase();
            const text = (node.fullData?.text || '').toLowerCase();
            const summary = (node.fullData?.summary || '').toLowerCase();
            const original = (node.fullData?.original_text || '').toLowerCase();

            return label.includes(this.searchQuery) ||
                   text.includes(this.searchQuery) ||
                   summary.includes(this.searchQuery) ||
                   original.includes(this.searchQuery);
        });

        // Store matched node IDs
        this.filteredNodes = new Set(matchedNodes.map(n => n.id));

        console.log(`[searchNodes] Found ${matchedNodes.length} matches`);

        // Apply visual filtering
        this.applyFiltersToGraph();

        return { matches: matchedNodes.length, total: this.currentGraphData.nodes.length };
    },

    /**
     * Update active filters
     */
    updateFilters(filters) {
        this.activeFilters = { ...this.activeFilters, ...filters };
        console.log('[updateFilters]', this.activeFilters);
        this.applyFiltersToGraph();
    },

    /**
     * Apply current filters to graph visualization
     */
    applyFiltersToGraph() {
        const svg = d3.select('#graph-svg');
        const nodes = svg.selectAll('g').filter(d => d && d.id);

        nodes.each(function(d) {
            const node = d3.select(this);
            let visible = true;

            // Type filters
            if (d.type === 'document' && !GraphRenderer.activeFilters.documents) {
                visible = false;
            }
            if ((d.type === 'sub' || d.type === 'super') && !GraphRenderer.activeFilters.claims) {
                visible = false;
            }
            if (d.isDuplicate && !GraphRenderer.activeFilters.duplicates) {
                visible = false;
            }

            // Quality filter
            const quality = d.fullData?.quality_score || d.fullData?.confidence || 0;
            if (quality < GraphRenderer.activeFilters.minQuality / 100) {
                visible = false;
            }

            // Search filter
            if (GraphRenderer.searchQuery && !GraphRenderer.filteredNodes.has(d.id)) {
                visible = false;
            }

            // Apply visibility
            if (visible) {
                node.style('opacity', 1)
                    .style('pointer-events', 'all');
            } else {
                node.style('opacity', 0.1)
                    .style('pointer-events', 'none');
            }
        });

        // Also filter links
        const links = svg.selectAll('line');
        links.each(function(d) {
            const link = d3.select(this);
            const sourceVisible = svg.selectAll('g').filter(n => n && n.id === d.source.id).style('opacity') === '1';
            const targetVisible = svg.selectAll('g').filter(n => n && n.id === d.target.id).style('opacity') === '1';

            if (sourceVisible && targetVisible) {
                link.style('opacity', 0.6);
            } else {
                link.style('opacity', 0.05);
            }
        });
    },

    /**
     * Clear all filters and search
     */
    clearFilters() {
        this.searchQuery = '';
        this.filteredNodes.clear();
        this.activeFilters = {
            documents: true,
            claims: true,
            duplicates: true,
            minQuality: 0
        };
        this.applyFiltersToGraph();
        return { matches: this.currentGraphData.nodes.length, total: this.currentGraphData.nodes.length };
    },

    /**
     * Focus on filtered nodes (zoom and center)
     */
    focusFilteredNodes() {
        if (this.filteredNodes.size === 0 && !this.searchQuery) {
            console.log('[focusFilteredNodes] No active filters');
            return;
        }

        const svg = d3.select('#graph-svg');
        const visibleNodes = this.currentGraphData.nodes.filter(n => {
            if (this.searchQuery && !this.filteredNodes.has(n.id)) return false;

            // Check type filters
            if (n.type === 'document' && !this.activeFilters.documents) return false;
            if ((n.type === 'sub' || n.type === 'super') && !this.activeFilters.claims) return false;
            if (n.isDuplicate && !this.activeFilters.duplicates) return false;

            // Check quality filter
            const quality = n.fullData?.quality_score || n.fullData?.confidence || 0;
            if (quality < this.activeFilters.minQuality / 100) return false;

            return true;
        });

        if (visibleNodes.length === 0) {
            console.log('[focusFilteredNodes] No visible nodes to focus');
            return;
        }

        // Calculate bounding box of visible nodes
        const xs = visibleNodes.map(n => n.x).filter(x => x !== undefined);
        const ys = visibleNodes.map(n => n.y).filter(y => y !== undefined);

        if (xs.length === 0 || ys.length === 0) {
            console.log('[focusFilteredNodes] Nodes not yet positioned');
            return;
        }

        const minX = Math.min(...xs);
        const maxX = Math.max(...xs);
        const minY = Math.min(...ys);
        const maxY = Math.max(...ys);

        const centerX = (minX + maxX) / 2;
        const centerY = (minY + maxY) / 2;
        const width = maxX - minX;
        const height = maxY - minY;

        const svgWidth = parseInt(svg.style('width'));
        const svgHeight = parseInt(svg.style('height'));

        // Calculate zoom level (with padding)
        const padding = 100;
        const scaleX = (svgWidth - padding) / width;
        const scaleY = (svgHeight - padding) / height;
        const scale = Math.min(scaleX, scaleY, 2);  // Cap at 2x zoom

        // Pan and zoom
        const transform = d3.zoomIdentity
            .translate(svgWidth / 2, svgHeight / 2)
            .scale(scale)
            .translate(-centerX, -centerY);

        svg.transition()
            .duration(750)
            .call(d3.zoom().transform, transform);

        console.log(`[focusFilteredNodes] Focused on ${visibleNodes.length} nodes`);
    }
};
