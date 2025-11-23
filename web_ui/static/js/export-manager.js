/**
 * Export Manager Module
 * Exports graph visualizations as PNG, SVG, or PDF
 */

const ExportManager = {
    /**
     * Export graph as PNG image
     */
    async exportAsPNG() {
        console.log('[ExportManager] Exporting as PNG...');

        try {
            const svgElement = document.querySelector('#graph-svg');
            if (!svgElement) {
                throw new Error('Graph SVG element not found');
            }

            // Convert SVG to canvas
            const canvas = await this.svgToCanvas(svgElement);

            // Download as PNG
            const dataURL = canvas.toDataURL('image/png');
            this.downloadFile(dataURL, 'research-graph.png');

            console.log('[ExportManager] PNG export complete');
            if (window.UI && UI.showNotification) {
                UI.showNotification('Graph exported as PNG', 'success');
            }
        } catch (error) {
            console.error('[ExportManager] PNG export failed:', error);
            if (window.UI && UI.showNotification) {
                UI.showNotification('Failed to export PNG: ' + error.message, 'error');
            }
        }
    },

    /**
     * Export graph as SVG
     */
    async exportAsSVG() {
        console.log('[ExportManager] Exporting as SVG...');

        try {
            const svgElement = document.querySelector('#graph-svg');
            if (!svgElement) {
                throw new Error('Graph SVG element not found');
            }

            // Clone the SVG to avoid modifying the original
            const clonedSvg = svgElement.cloneNode(true);

            // Add XML namespace if not present
            clonedSvg.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
            clonedSvg.setAttribute('xmlns:xlink', 'http://www.w3.org/1999/xlink');

            // Serialize SVG to string
            const serializer = new XMLSerializer();
            const svgString = serializer.serializeToString(clonedSvg);

            // Add CSS styles inline
            const styledSvgString = this.inlineStyles(svgString);

            // Create blob and download
            const blob = new Blob([styledSvgString], { type: 'image/svg+xml;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            this.downloadFile(url, 'research-graph.svg');
            URL.revokeObjectURL(url);

            console.log('[ExportManager] SVG export complete');
            if (window.UI && UI.showNotification) {
                UI.showNotification('Graph exported as SVG', 'success');
            }
        } catch (error) {
            console.error('[ExportManager] SVG export failed:', error);
            if (window.UI && UI.showNotification) {
                UI.showNotification('Failed to export SVG: ' + error.message, 'error');
            }
        }
    },

    /**
     * Export graph as PDF
     */
    async exportAsPDF() {
        console.log('[ExportManager] Exporting as PDF...');

        try {
            // Check if jsPDF is available
            if (typeof jsPDF === 'undefined') {
                console.warn('[ExportManager] jsPDF not loaded, falling back to PNG');
                if (window.UI && UI.showNotification) {
                    UI.showNotification('PDF export requires jsPDF library. Exporting as PNG instead.', 'warning');
                }
                return this.exportAsPNG();
            }

            const svgElement = document.querySelector('#graph-svg');
            if (!svgElement) {
                throw new Error('Graph SVG element not found');
            }

            // Convert SVG to canvas
            const canvas = await this.svgToCanvas(svgElement);
            const imgData = canvas.toDataURL('image/png');

            // Create PDF
            const pdf = new jsPDF({
                orientation: canvas.width > canvas.height ? 'landscape' : 'portrait',
                unit: 'px',
                format: [canvas.width, canvas.height]
            });

            pdf.addImage(imgData, 'PNG', 0, 0, canvas.width, canvas.height);
            pdf.save('research-graph.pdf');

            console.log('[ExportManager] PDF export complete');
            if (window.UI && UI.showNotification) {
                UI.showNotification('Graph exported as PDF', 'success');
            }
        } catch (error) {
            console.error('[ExportManager] PDF export failed:', error);
            if (window.UI && UI.showNotification) {
                UI.showNotification('Failed to export PDF: ' + error.message, 'error');
            }
        }
    },

    /**
     * Convert SVG element to canvas
     */
    async svgToCanvas(svgElement) {
        return new Promise((resolve, reject) => {
            try {
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');

                // Get SVG dimensions
                const bbox = svgElement.getBoundingClientRect();
                canvas.width = bbox.width;
                canvas.height = bbox.height;

                // Set white background
                ctx.fillStyle = '#1a1a1a'; // Match graph background
                ctx.fillRect(0, 0, canvas.width, canvas.height);

                // Clone SVG and convert to data URL
                const clonedSvg = svgElement.cloneNode(true);
                clonedSvg.setAttribute('xmlns', 'http://www.w3.org/2000/svg');

                const serializer = new XMLSerializer();
                const svgString = serializer.serializeToString(clonedSvg);

                // Inline styles
                const styledSvgString = this.inlineStyles(svgString);

                // Create image from SVG
                const img = new Image();

                img.onload = () => {
                    ctx.drawImage(img, 0, 0);
                    resolve(canvas);
                };

                img.onerror = (error) => {
                    reject(new Error('Failed to load SVG image: ' + error));
                };

                // Create blob URL for the SVG
                const blob = new Blob([styledSvgString], { type: 'image/svg+xml;charset=utf-8' });
                const url = URL.createObjectURL(blob);
                img.src = url;

                // Clean up blob URL after image loads
                img.onload = () => {
                    ctx.drawImage(img, 0, 0);
                    URL.revokeObjectURL(url);
                    resolve(canvas);
                };
            } catch (error) {
                reject(error);
            }
        });
    },

    /**
     * Inline CSS styles into SVG string
     */
    inlineStyles(svgString) {
        // Add common styles directly into the SVG
        const styleString = `
            <style>
                .graph-node {
                    cursor: pointer;
                }
                text {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    pointer-events: none;
                }
                line {
                    stroke-opacity: 0.6;
                }
                .cluster-hull {
                    pointer-events: none;
                }
            </style>
        `;

        // Insert style after opening svg tag
        return svgString.replace('<svg', '<svg' + ' ' + styleString);
    },

    /**
     * Download file with given data URL and filename
     */
    downloadFile(dataURL, filename) {
        const a = document.createElement('a');
        a.href = dataURL;
        a.download = filename;
        a.style.display = 'none';

        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);

        console.log(`[ExportManager] Downloaded ${filename}`);
    },

    /**
     * Export current graph state as JSON data
     */
    exportAsJSON() {
        console.log('[ExportManager] Exporting as JSON...');

        try {
            const graphData = {
                nodes: GraphRenderer.currentGraphData.nodes,
                links: GraphRenderer.currentGraphData.links,
                metadata: {
                    exportedAt: new Date().toISOString(),
                    nodeCount: GraphRenderer.currentGraphData.nodes.length,
                    linkCount: GraphRenderer.currentGraphData.links.length
                }
            };

            const jsonString = JSON.stringify(graphData, null, 2);
            const blob = new Blob([jsonString], { type: 'application/json' });
            const url = URL.createObjectURL(blob);

            this.downloadFile(url, 'research-graph-data.json');
            URL.revokeObjectURL(url);

            console.log('[ExportManager] JSON export complete');
            if (window.UI && UI.showNotification) {
                UI.showNotification('Graph data exported as JSON', 'success');
            }
        } catch (error) {
            console.error('[ExportManager] JSON export failed:', error);
            if (window.UI && UI.showNotification) {
                UI.showNotification('Failed to export JSON: ' + error.message, 'error');
            }
        }
    }
};
