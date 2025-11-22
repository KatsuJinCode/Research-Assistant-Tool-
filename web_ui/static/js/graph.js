/**
 * Graph Module - D3.js force-directed graph rendering
 */

const GraphRenderer = {
    simulation: null,
    currentGraphData: { nodes: [], links: [] },
    selectedNodeIds: new Set(),  // Track multiple selected nodes
    hoveredLinkIndices: new Set(),  // Track hovered links
    searchQuery: '',  // Current search query
    activeFilters: {
        documents: true,
        claims: true,
        duplicates: true,
        minQuality: 0
    },
    filteredNodes: new Set(),  // IDs of nodes matching current filters
    comparisonMode: false,  // Track if in comparison mode

    /**
     * Build unified graph from full graph data with arbitrary depth support
     * Now supports agent nodes and CREATED relationships
     */
    buildUnifiedGraph(graphData) {
        const nodes = [];
        const links = [];
        const addedNodes = new Set();

        // Handle new data structure: {documents: [], agents: [], sources: []}
        const documents = graphData.documents || graphData;  // Backward compatibility
        const agents = graphData.agents || [];
        const sources = graphData.sources || [];

        console.log('[buildUnifiedGraph] Processing', documents.length, 'documents,', agents.length, 'agents, and', sources.length, 'sources');

        // First pass: Add source nodes (data sources like URLs, papers, files)
        sources.forEach(source => {
            const sourceId = source.id;
            if (!addedNodes.has(sourceId)) {
                nodes.push({
                    id: sourceId,
                    label: source.label || source.url,
                    type: 'source',
                    fullData: source
                });
                addedNodes.add(sourceId);
                console.log('[buildUnifiedGraph] Added source node:', sourceId, `(type: ${source.type})`);
            }
        });

        // Second pass: Add agent nodes
        agents.forEach(agent => {
            const agentId = agent.id;
            if (!addedNodes.has(agentId)) {
                nodes.push({
                    id: agentId,
                    label: agent.type || 'Agent',
                    type: 'agent',
                    fullData: agent,
                    createdNodeCount: agent.created_node_ids?.length || 0
                });
                addedNodes.add(agentId);
                console.log('[buildUnifiedGraph] Added agent node:', agentId, `(created ${agent.created_node_ids?.length || 0} nodes)`);
            }
        });

        // Third pass: Add documents and create SOURCED_FROM and CREATED links
        documents.forEach(doc => {
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

            // Create SOURCED_FROM link from source to document
            const sourceId = doc.source_id;
            if (sourceId && addedNodes.has(sourceId)) {
                links.push({
                    source: sourceId,
                    target: docId,
                    type: 'sourced_from'
                });
                console.log('[buildUnifiedGraph] Added SOURCED_FROM link:', sourceId, '->', docId);
            }

            // Create CREATED link from agent to document
            const createdByAgentId = doc.created_by_agent_id;
            if (createdByAgentId && addedNodes.has(createdByAgentId)) {
                links.push({
                    source: createdByAgentId,
                    target: docId,
                    type: 'created'
                });
                console.log('[buildUnifiedGraph] Added CREATED link:', createdByAgentId, '->', docId);
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

                // Create CREATED link from agent to claim (if applicable)
                const claimCreatedByAgentId = claim.created_by_agent_id;
                if (claimCreatedByAgentId && addedNodes.has(claimCreatedByAgentId)) {
                    links.push({
                        source: claimCreatedByAgentId,
                        target: claim.id,
                        type: 'created'
                    });
                    console.log('[buildUnifiedGraph] Added CREATED link for claim:', claimCreatedByAgentId, '->', claim.id);
                }

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

            // Add SIMILAR_TO relationship links (RAG-detected similar claims)
            if (doc.similar_to_links && Array.isArray(doc.similar_to_links)) {
                doc.similar_to_links.forEach(link => {
                    // Only add if both nodes exist
                    if (addedNodes.has(link.source_id) && addedNodes.has(link.target_id)) {
                        links.push({
                            source: link.source_id,
                            target: link.target_id,
                            type: 'SIMILAR_TO',
                            similarity: link.similarity_score || link.similarity
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
                if (d.type === 'sourced_from') return 170;  // NEW - source to document
                if (d.type === 'created') return 180;  // agent to created node
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

        // Create clip paths for each node to mask labels
        const defs = svg.select('defs').empty() ? svg.append('defs') : svg.select('defs');

        nodes.forEach(d => {
            const clipId = `label-clip-${d.id.substring(0, 8)}`;
            d.clipPathId = clipId;

            // Remove existing clip path if it exists
            defs.select(`#${clipId}`).remove();

            // Create new clip path
            const clipPath = defs.append('clipPath').attr('id', clipId);
            clipPath.append('circle')
                .attr('cx', 0)
                .attr('cy', 0)
                .attr('r', this.getNodeRadius(d.type, d) - 3);  // Slightly smaller to keep text inside
        });

        // Add text labels with clipping (attached to nodes)
        const labels = g.append('g')
            .selectAll('text')
            .data(nodes)
            .enter().append('text')
            .attr('data-node-id', d => d.id)
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'middle')  // Center vertically
            .attr('font-size', '11px')
            .attr('fill', '#ffffff')
            .attr('font-weight', '600')
            .attr('pointer-events', 'none')
            .attr('clip-path', d => `url(#${d.clipPathId})`)  // Apply clipping
            .style('text-shadow', '0 0 3px rgba(0,0,0,0.9)')
            .text(d => {
                // Source nodes get appropriate icon based on type
                if (d.type === 'source') {
                    const sourceType = d.fullData?.type || 'File';
                    const sourceLabel = d.fullData?.label || 'Source';

                    // Choose icon based on source type
                    let icon = '📄';  // Default: file
                    if (sourceType === 'URL') icon = '🔗';
                    else if (sourceType === 'ArXiv') icon = '📚';

                    const displayLabel = sourceLabel.length > 20 ? sourceLabel.substring(0, 20) + '...' : sourceLabel;
                    return `${icon} ${displayLabel}`;
                }

                // Agent nodes get a robot emoji prefix
                if (d.type === 'agent') {
                    const agentType = d.fullData?.type || 'Agent';
                    return `🤖 ${agentType}`;
                }

                const summary = d.fullData?.summary;
                if (!summary && d.type !== 'document') {
                    if (d.processing || d.fresh) {
                        return 'Processing...';
                    }
                    console.warn('Claim missing summary:', d.id);
                    return 'Processing...';
                }
                const displayText = summary || d.label;
                return displayText.length > 25 ? displayText.substring(0, 25) + '...' : displayText;
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

            // Multi-selection support: Ctrl/Cmd for add/remove, Shift for range (not implemented yet)
            if (event.ctrlKey || event.metaKey) {
                // Toggle selection
                if (this.selectedNodeIds.has(d.id)) {
                    this.selectedNodeIds.delete(d.id);
                } else {
                    this.selectedNodeIds.add(d.id);
                }
            } else {
                // Single selection (clear others)
                this.selectedNodeIds.clear();
                this.selectedNodeIds.add(d.id);
            }

            // Update visual selection for all nodes
            node.selectAll('circle')
                .attr('stroke', n => this.selectedNodeIds.has(n.id) ? '#FFD700' : '#fff')
                .attr('stroke-width', n => this.selectedNodeIds.has(n.id) ? 5 : this.getNodeBorderWidth(n))
                .style('filter', n => this.selectedNodeIds.has(n.id) ? 'drop-shadow(0 0 8px #FFD700)' : 'none');

            // Toggle label clipping for selected nodes (overflow when selected)
            labels
                .attr('clip-path', n => this.selectedNodeIds.has(n.id) ? 'none' : `url(#${n.clipPathId})`)
                .attr('font-size', n => this.selectedNodeIds.has(n.id) ? '12px' : '11px');

            // Highlight connected links for all selected nodes
            link
                .style('stroke-opacity', l => {
                    const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
                    const targetId = typeof l.target === 'object' ? l.target.id : l.target;
                    const isConnected = Array.from(this.selectedNodeIds).some(selectedId =>
                        sourceId === selectedId || targetId === selectedId
                    );
                    return isConnected ? 1.0 : 0.3;
                })
                .style('stroke-width', l => {
                    const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
                    const targetId = typeof l.target === 'object' ? l.target.id : l.target;
                    const isConnected = Array.from(this.selectedNodeIds).some(selectedId =>
                        sourceId === selectedId || targetId === selectedId
                    );
                    const baseWidth = this.getLinkWidth(l.type);
                    return isConnected ? baseWidth * 1.5 : baseWidth;
                });

            // Update comparison panel if multiple nodes selected
            if (this.selectedNodeIds.size > 1) {
                this.showComparisonPanel();
            } else if (this.selectedNodeIds.size === 1) {
                // Show details for single selected node
                if (d.type === 'super' || d.type === 'sub') {
                    window.showClaimDetails(d.id);
                } else if (d.type === 'document') {
                    UI.showDocumentDetails(d);
                } else if (d.type === 'evidence') {
                    UI.showEvidenceDetails(d);
                }

                // Emit nodeSelected event for PropertyViewer
                const event = new CustomEvent('nodeSelected', {
                    detail: {
                        nodeId: d.id,
                        nodeData: d
                    }
                });
                document.dispatchEvent(event);
            }
        });

        // Click on background to deselect
        svg.on('click', () => {
            this.selectedNodeIds.clear();
            node.selectAll('circle')
                .attr('stroke', '#fff')
                .attr('stroke-width', d => this.getNodeBorderWidth(d))
                .style('filter', 'none');
            link
                .style('stroke-opacity', 0.6)
                .style('stroke-width', l => this.getLinkWidth(l.type));
            // Reset label clipping
            labels
                .attr('clip-path', d => `url(#${d.clipPathId})`)
                .attr('font-size', '11px');
            this.hideComparisonPanel();
        });

        // Simplified tick function - labels attached to nodes
        this.simulation.on('tick', () => {
            // Update link positions
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            // Update node positions
            node.attr('transform', d => `translate(${d.x},${d.y})`);

            // Update label positions (centered on nodes)
            labels
                .attr('x', d => d.x)
                .attr('y', d => d.y);
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
     * Get link width based on type
     */
    getLinkWidth(type) {
        const widths = {
            'contains': 3,
            'has_sub': 2,
            'supports': 2.5,
            'contradicts': 2.5,
            'SIMILAR_TO': 2  // RAG-detected similar claims
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
        if (type === 'SIMILAR_TO') {
            return '4,2';  // Dash-dot pattern for RAG-detected similarity
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
            'evidence': { r: 255, g: 152, b: 0 },     // Orange
            'agent': { r: 0, g: 188, b: 212 },        // Cyan/Teal
            'source': { r: 255, g: 235, b: 59 }       // Yellow/Gold - NEW
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
            'evidence': 12,
            'agent': 22,  // Slightly larger than claims
            'source': 18   // NEW - between evidence and super claims
        };

        let baseRadius = baseRadii[type] || 15;

        // For agents, scale based on number of created nodes
        if (type === 'agent' && node && node.createdNodeCount !== undefined) {
            const scaleFactor = Math.log(node.createdNodeCount + 1) * 3;
            baseRadius += scaleFactor;
        }
        // For other nodes, scale based on descendant count
        else if (node && node.descendantCount !== undefined) {
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
            'semantic_similar': '#9C27B0',  // Purple - semantically similar across documents
            'SIMILAR_TO': '#FFC107',    // Amber/Gold - RAG-detected similar claims
            'created': '#00BCD4',       // Cyan/Teal - agent created node
            'sourced_from': '#FFEB3B'   // Yellow/Gold - source to document - NEW
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
    },

    /**
     * Show comparison panel for multiple selected nodes
     */
    showComparisonPanel() {
        const selectedIds = Array.from(this.selectedNodeIds);
        const nodes = this.currentGraphData.nodes.filter(n => selectedIds.includes(n.id));

        // Create/update comparison panel in the details container
        const detailsPanel = document.getElementById('details-panel');
        if (!detailsPanel) return;

        detailsPanel.innerHTML = `
            <div class="comparison-panel">
                <div class="comparison-header">
                    <h3>Node Comparison (${nodes.length} selected)</h3>
                    <button class="btn btn-sm btn-secondary" onclick="GraphRenderer.clearSelection()">Clear Selection</button>
                </div>
                <div class="comparison-nodes">
                    ${nodes.map(n => `
                        <div class="comparison-node">
                            <span class="node-type-badge ${n.type}">${n.type}</span>
                            <strong>${n.label}</strong>
                            <button class="btn btn-xs" onclick="GraphRenderer.deselectNode('${n.id}')">×</button>
                        </div>
                    `).join('')}
                </div>
                <div class="comparison-actions">
                    <button class="btn btn-primary" onclick="GraphRenderer.compareNodes()">
                        🔍 Compare Commonality & Linkages
                    </button>
                    <button class="btn btn-info" onclick="GraphRenderer.findConnectionPath()">
                        🔗 Find Connection Path
                    </button>
                    <button class="btn btn-success" onclick="GraphRenderer.launchGapFillingAgents()">
                        🤖 Fill Knowledge Gaps
                    </button>
                </div>
                <div id="comparison-results" class="comparison-results"></div>
            </div>
        `;

        detailsPanel.style.display = 'block';
    },

    /**
     * Hide comparison panel
     */
    hideComparisonPanel() {
        const detailsPanel = document.getElementById('details-panel');
        if (detailsPanel) {
            detailsPanel.innerHTML = '';
            detailsPanel.style.display = 'none';
        }
    },

    /**
     * Clear all selections
     */
    clearSelection() {
        this.selectedNodeIds.clear();
        const svg = d3.select('#graph-svg');
        svg.selectAll('circle')
            .attr('stroke', '#fff')
            .attr('stroke-width', d => this.getNodeBorderWidth(d))
            .style('filter', 'none');
        svg.selectAll('line')
            .style('stroke-opacity', 0.6)
            .style('stroke-width', l => this.getLinkWidth(l.type));
        this.hideComparisonPanel();
    },

    /**
     * Deselect specific node
     */
    deselectNode(nodeId) {
        this.selectedNodeIds.delete(nodeId);
        if (this.selectedNodeIds.size === 0) {
            this.clearSelection();
        } else {
            this.showComparisonPanel();
            // Update visual selection
            const svg = d3.select('#graph-svg');
            svg.selectAll('circle')
                .attr('stroke', n => this.selectedNodeIds.has(n.id) ? '#FFD700' : '#fff')
                .attr('stroke-width', n => this.selectedNodeIds.has(n.id) ? 5 : this.getNodeBorderWidth(n))
                .style('filter', n => this.selectedNodeIds.has(n.id) ? 'drop-shadow(0 0 8px #FFD700)' : 'none');
        }
    },

    /**
     * Compare selected nodes to find commonality and linkages
     */
    async compareNodes() {
        const resultsDiv = document.getElementById('comparison-results');
        resultsDiv.innerHTML = '<div class="loading">Analyzing nodes...</div>';

        const selectedIds = Array.from(this.selectedNodeIds);
        const nodes = this.currentGraphData.nodes.filter(n => selectedIds.includes(n.id));
        const links = this.currentGraphData.links.filter(l => {
            const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
            const targetId = typeof l.target === 'object' ? l.target.id : l.target;
            return selectedIds.includes(sourceId) || selectedIds.includes(targetId);
        });

        // Find direct connections between selected nodes
        const directConnections = links.filter(l => {
            const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
            const targetId = typeof l.target === 'object' ? l.target.id : l.target;
            return selectedIds.includes(sourceId) && selectedIds.includes(targetId);
        });

        // Find common neighbors
        const neighbors = new Map();
        links.forEach(l => {
            const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
            const targetId = typeof l.target === 'object' ? l.target.id : l.target;

            if (selectedIds.includes(sourceId) && !selectedIds.includes(targetId)) {
                if (!neighbors.has(targetId)) neighbors.set(targetId, new Set());
                neighbors.get(targetId).add(sourceId);
            } else if (selectedIds.includes(targetId) && !selectedIds.includes(sourceId)) {
                if (!neighbors.has(sourceId)) neighbors.set(sourceId, new Set());
                neighbors.get(sourceId).add(targetId);
            }
        });

        const commonNeighbors = Array.from(neighbors.entries())
            .filter(([neighborId, connectedNodes]) => connectedNodes.size > 1)
            .map(([neighborId, connectedNodes]) => {
                const node = this.currentGraphData.nodes.find(n => n.id === neighborId);
                return {
                    id: neighborId,
                    label: node ? node.label : 'Unknown',
                    type: node ? node.type : 'unknown',
                    connectedTo: Array.from(connectedNodes)
                };
            });

        // Display results
        resultsDiv.innerHTML = `
            <div class="comparison-section">
                <h4>Direct Connections</h4>
                ${directConnections.length > 0 ? `
                    <ul>
                        ${directConnections.map(l => {
                            const sourceNode = this.currentGraphData.nodes.find(n =>
                                n.id === (typeof l.source === 'object' ? l.source.id : l.source)
                            );
                            const targetNode = this.currentGraphData.nodes.find(n =>
                                n.id === (typeof l.target === 'object' ? l.target.id : l.target)
                            );
                            return `<li><strong>${sourceNode?.label || 'Unknown'}</strong> → <em>${l.type}</em> → <strong>${targetNode?.label || 'Unknown'}</strong></li>`;
                        }).join('')}
                    </ul>
                ` : '<p>No direct connections between selected nodes.</p>'}
            </div>
            <div class="comparison-section">
                <h4>Common Neighbors (${commonNeighbors.length})</h4>
                ${commonNeighbors.length > 0 ? `
                    <ul>
                        ${commonNeighbors.map(n =>
                            `<li><span class="node-type-badge ${n.type}">${n.type}</span> ${n.label} (connected to ${n.connectedTo.length} selected nodes)</li>`
                        ).join('')}
                    </ul>
                ` : '<p>No common neighbors found.</p>'}
            </div>
            <div class="comparison-section">
                <h4>Node Details</h4>
                <ul>
                    ${nodes.map(n => `
                        <li><strong>${n.label}</strong> (${n.type})</li>
                    `).join('')}
                </ul>
            </div>
        `;
    },

    /**
     * Find shortest path between selected nodes
     */
    async findConnectionPath() {
        const resultsDiv = document.getElementById('comparison-results');
        resultsDiv.innerHTML = '<div class="loading">Finding connection paths...</div>';

        const selectedIds = Array.from(this.selectedNodeIds);

        if (selectedIds.length < 2) {
            resultsDiv.innerHTML = '<p>Please select at least 2 nodes to find paths.</p>';
            return;
        }

        // Simple BFS to find shortest path between first two nodes
        const startId = selectedIds[0];
        const endId = selectedIds[1];

        const visited = new Set();
        const queue = [[startId]];
        const maxDepth = 5;

        while (queue.length > 0) {
            const path = queue.shift();
            const currentId = path[path.length - 1];

            if (currentId === endId) {
                // Found path!
                const pathNodes = path.map(id =>
                    this.currentGraphData.nodes.find(n => n.id === id)
                ).filter(n => n);

                resultsDiv.innerHTML = `
                    <div class="comparison-section">
                        <h4>Connection Path (${pathNodes.length - 1} steps)</h4>
                        <div class="path-visualization">
                            ${pathNodes.map((n, idx) => `
                                <div class="path-node">
                                    <span class="node-type-badge ${n.type}">${n.type}</span>
                                    ${n.label}
                                    ${idx < pathNodes.length - 1 ? '<span class="path-arrow">→</span>' : ''}
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
                return;
            }

            if (path.length > maxDepth) continue;

            if (!visited.has(currentId)) {
                visited.add(currentId);

                // Find neighbors
                this.currentGraphData.links.forEach(l => {
                    const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
                    const targetId = typeof l.target === 'object' ? l.target.id : l.target;

                    if (sourceId === currentId && !visited.has(targetId)) {
                        queue.push([...path, targetId]);
                    } else if (targetId === currentId && !visited.has(sourceId)) {
                        queue.push([...path, sourceId]);
                    }
                });
            }
        }

        resultsDiv.innerHTML = '<p>No path found between selected nodes (within 5 steps).</p>';
    },

    /**
     * Launch research agents to fill knowledge gaps between nodes
     */
    async launchGapFillingAgents() {
        const resultsDiv = document.getElementById('comparison-results');
        resultsDiv.innerHTML = '<div class="loading">Launching research agents to fill knowledge gaps...</div>';

        const selectedIds = Array.from(this.selectedNodeIds);

        try {
            const response = await fetch('/api/fill-knowledge-gaps', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ node_ids: selectedIds })
            });

            if (response.ok) {
                const data = await response.json();
                resultsDiv.innerHTML = `
                    <div class="comparison-section">
                        <h4>Research Agents Launched</h4>
                        <p>${data.message || 'Research agents are analyzing connections between selected nodes...'}</p>
                        <p class="text-muted">Results will appear as new claims in the graph.</p>
                    </div>
                `;
            } else {
                throw new Error('Failed to launch research agents');
            }
        } catch (error) {
            console.error('Error launching research agents:', error);
            resultsDiv.innerHTML = `
                <div class="alert alert-warning">
                    <strong>Feature Coming Soon:</strong> Research agents for gap-filling will be implemented shortly.
                    <p class="text-muted">This will use investigation agents to find connections between selected nodes.</p>
                </div>
            `;
        }
    },

    /**
     * Highlight a specific node in the graph and focus on it
     * Used for provenance navigation: Agent → Node
     */
    highlightNode(nodeId) {
        console.log('🎯 Highlighting node in graph:', nodeId);

        // Find the node in the current graph data
        const node = this.currentGraphData.nodes.find(n => n.id === nodeId);

        if (!node) {
            console.warn('Node not found in current graph:', nodeId);
            UI.showNotification(`Node ${nodeId} not visible in current graph view`, 'warning');
            return;
        }

        // Clear previous selection
        this.clearSelection();

        // Select the node
        this.selectedNodeIds.add(nodeId);

        // Apply visual highlighting
        const svg = d3.select('#graph-svg');

        // Highlight the node with a special color for provenance navigation
        svg.selectAll('circle')
            .attr('stroke', n => n.id === nodeId ? '#FF4081' : '#fff')
            .attr('stroke-width', n => n.id === nodeId ? 6 : this.getNodeBorderWidth(n))
            .style('filter', n => n.id === nodeId ? 'drop-shadow(0 0 12px #FF4081)' : 'none');

        // Dim links that don't connect to this node
        svg.selectAll('line')
            .style('stroke-opacity', l => {
                return (l.source.id === nodeId || l.target.id === nodeId) ? 0.8 : 0.2;
            })
            .style('stroke-width', l => {
                return (l.source.id === nodeId || l.target.id === nodeId)
                    ? this.getLinkWidth(l.type) * 1.5
                    : this.getLinkWidth(l.type);
            });

        // Center the view on the node
        if (this.simulation) {
            // Get SVG element and its dimensions
            const svgElement = document.getElementById('graph-svg');
            const svgRect = svgElement.getBoundingClientRect();
            const width = svgRect.width;
            const height = svgRect.height;

            // Calculate the transform to center the node
            const scale = 1.5; // Zoom in slightly
            const x = width / 2 - node.x * scale;
            const y = height / 2 - node.y * scale;

            // Apply smooth transition
            svg.select('g')
                .transition()
                .duration(750)
                .attr('transform', `translate(${x}, ${y}) scale(${scale})`);

            // Add a temporary pulsing animation
            const highlightedNode = svg.selectAll('circle')
                .filter(n => n.id === nodeId);

            // Pulse animation
            highlightedNode
                .transition()
                .duration(300)
                .attr('r', n => this.getNodeSize(n) * 1.3)
                .transition()
                .duration(300)
                .attr('r', n => this.getNodeSize(n))
                .transition()
                .duration(300)
                .attr('r', n => this.getNodeSize(n) * 1.3)
                .transition()
                .duration(300)
                .attr('r', n => this.getNodeSize(n));
        }

        // Show node details in the detail panel
        if (node.type === 'claim') {
            // Show claim details
            if (window.showClaimDetails) {
                setTimeout(() => showClaimDetails(nodeId), 500);
            }
        } else if (node.type === 'document') {
            // Show document details
            if (window.UI && UI.showDocumentDetails) {
                setTimeout(() => UI.showDocumentDetails(node), 500);
            }
        }

        // Show notification
        UI.showNotification(`Focused on ${node.type}: ${node.label || nodeId}`, 'success');
    }
};
