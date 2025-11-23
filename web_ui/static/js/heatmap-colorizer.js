/**
 * Heatmap Colorizer Module
 * Applies color schemes to nodes based on various metrics
 */

const HeatmapColorizer = {
    currentScheme: 'type', // Default to type-based coloring

    colorSchemes: {
        type: {
            name: 'Node Type',
            description: 'Color by node type (default)',
            getValue: (node) => node.type,
            scale: null, // Use default color mapping
            isCategory: true
        },
        confidence: {
            name: 'Confidence Score',
            description: 'Color by confidence level',
            getValue: (node) => {
                const confidence = node.fullData?.confidence || node.confidence || 0.5;
                return confidence * 100;
            },
            scale: d3.scaleSequential(d3.interpolateRdYlGn).domain([0, 100]),
            isCategory: false
        },
        investigation: {
            name: 'Investigation Value',
            description: 'Color by research priority',
            getValue: (node) => {
                const value = node.fullData?.investigation_value || node.investigation_value || 50;
                return value;
            },
            scale: d3.scaleSequential(d3.interpolateViridis).domain([0, 100]),
            isCategory: false
        },
        recency: {
            name: 'Recency',
            description: 'Color by how recently created',
            getValue: (node) => {
                const timestamp = node.fullData?.created_at || node.created_at;
                if (!timestamp) return 0;
                return this.calculateRecency(timestamp);
            },
            scale: d3.scaleSequential(d3.interpolateCool).domain([0, 1]),
            isCategory: false
        },
        connectivity: {
            name: 'Connections',
            description: 'Color by number of connections',
            getValue: (node) => {
                return node.degree || this.calculateDegree(node.id);
            },
            scale: d3.scaleSequential(d3.interpolateWarm).domain([0, 20]),
            isCategory: false
        },
        quality: {
            name: 'Quality Score',
            description: 'Color by quality assessment',
            getValue: (node) => {
                const quality = node.fullData?.quality_score || node.quality_score || 0.5;
                return quality * 100;
            },
            scale: d3.scaleSequential(d3.interpolatePlasma).domain([0, 100]),
            isCategory: false
        }
    },

    /**
     * Initialize heatmap colorizer
     */
    init() {
        console.log('[HeatmapColorizer] Initialized with', Object.keys(this.colorSchemes).length, 'color schemes');
    },

    /**
     * Apply heatmap color scheme to nodes
     */
    applyHeatmap(nodes, schemeName) {
        if (!this.colorSchemes[schemeName]) {
            console.error('[HeatmapColorizer] Invalid scheme:', schemeName);
            return;
        }

        console.log(`[HeatmapColorizer] Applying ${schemeName} color scheme to ${nodes.length} nodes`);
        this.currentScheme = schemeName;
        const scheme = this.colorSchemes[schemeName];

        // Calculate values and assign colors
        nodes.forEach(node => {
            const value = scheme.getValue(node);

            if (scheme.isCategory || schemeName === 'type') {
                // Use default type-based colors
                node.heatmapColor = null; // Will use default getNodeColor
            } else {
                // Use continuous scale
                node.heatmapColor = scheme.scale(value);
            }

            node.heatmapValue = value;
        });

        // Update node colors in graph
        this.updateNodeColors();

        // Show/update legend
        if (schemeName !== 'type') {
            this.showLegend(schemeName);
        } else {
            this.hideLegend();
        }

        // Update UI selector
        const selector = document.getElementById('heatmap-scheme');
        if (selector) {
            selector.value = schemeName;
        }
    },

    /**
     * Update node colors in the graph visualization
     */
    updateNodeColors() {
        const svg = d3.select('#graph-svg');

        svg.selectAll('circle.graph-node')
            .transition()
            .duration(500)
            .style('fill', d => {
                if (d.heatmapColor) {
                    return d.heatmapColor;
                } else {
                    // Use default color function
                    return GraphRenderer.getNodeColor(d.type, d);
                }
            });

        console.log('[HeatmapColorizer] Node colors updated');
    },

    /**
     * Calculate recency (0 = old, 1 = very recent)
     */
    calculateRecency(timestamp) {
        const now = Date.now();
        const nodeTime = new Date(timestamp).getTime();
        const age = now - nodeTime;

        const maxAge = 365 * 24 * 60 * 60 * 1000; // 1 year in milliseconds
        const recency = Math.max(0, 1 - (age / maxAge));

        return recency;
    },

    /**
     * Calculate node degree (number of connections)
     */
    calculateDegree(nodeId) {
        if (!GraphRenderer.currentGraphData) return 0;

        let degree = 0;

        GraphRenderer.currentGraphData.links.forEach(link => {
            const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
            const targetId = typeof link.target === 'object' ? link.target.id : link.target;

            if (sourceId === nodeId || targetId === nodeId) {
                degree++;
            }
        });

        return degree;
    },

    /**
     * Show color legend
     */
    showLegend(schemeName) {
        const legend = document.getElementById('heatmap-legend');
        if (!legend) {
            console.warn('[HeatmapColorizer] Legend element not found');
            return;
        }

        const scheme = this.colorSchemes[schemeName];

        // Update legend title
        const titleElement = document.getElementById('legend-scheme-name');
        if (titleElement) {
            titleElement.textContent = scheme.name;
        }

        // Create gradient
        const gradient = document.getElementById('legend-gradient');
        if (gradient && scheme.scale) {
            // Create gradient using the scale
            const gradientSteps = 10;
            const colors = [];

            for (let i = 0; i <= gradientSteps; i++) {
                const value = (i / gradientSteps) * 100;
                colors.push(scheme.scale(value));
            }

            gradient.style.background = `linear-gradient(to right, ${colors.join(', ')})`;
        }

        // Update labels
        const minLabel = legend.querySelector('.legend-min');
        const maxLabel = legend.querySelector('.legend-max');

        if (minLabel && maxLabel) {
            if (schemeName === 'recency') {
                minLabel.textContent = 'Old';
                maxLabel.textContent = 'Recent';
            } else if (schemeName === 'connectivity') {
                minLabel.textContent = 'Few';
                maxLabel.textContent = 'Many';
            } else {
                minLabel.textContent = 'Low';
                maxLabel.textContent = 'High';
            }
        }

        // Show legend
        legend.style.display = 'block';
    },

    /**
     * Hide color legend
     */
    hideLegend() {
        const legend = document.getElementById('heatmap-legend');
        if (legend) {
            legend.style.display = 'none';
        }
    },

    /**
     * Get current scheme info
     */
    getCurrentScheme() {
        return this.colorSchemes[this.currentScheme];
    }
};

// Global handler for heatmap scheme change
function handleHeatmapChange(schemeName) {
    HeatmapColorizer.applyHeatmap(GraphRenderer.currentGraphData.nodes, schemeName);
}

function toggleLegend(show) {
    if (show) {
        HeatmapColorizer.showLegend(HeatmapColorizer.currentScheme);
    } else {
        HeatmapColorizer.hideLegend();
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    HeatmapColorizer.init();
});
