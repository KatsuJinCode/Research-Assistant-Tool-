/**
 * Report Generator Module
 * Comprehensive Export and Reporting System
 *
 * Features:
 * 1. PDF Report Generation (jsPDF)
 * 2. Markdown Export
 * 3. BibTeX Citation Integration
 * 4. Custom Report Templates (Handlebars.js)
 * 5. Scheduled Exports
 */

const ReportGenerator = {
    // Configuration
    config: {
        defaultTemplate: 'executive_summary',
        pdfOptions: {
            orientation: 'portrait',
            unit: 'mm',
            format: 'a4'
        },
        branding: {
            title: 'Research Assistant Report',
            logo: null,
            colors: {
                primary: '#2196F3',
                secondary: '#1976D2',
                text: '#333333'
            }
        }
    },

    // Template storage
    templates: {},

    // Report history
    reportHistory: [],

    /**
     * Initialize the Report Generator
     */
    async initialize() {
        console.log('[ReportGenerator] Initializing...');

        // Load templates from localStorage
        this.loadTemplates();

        // Initialize default templates
        this.initializeDefaultTemplates();

        // Load report history
        this.loadReportHistory();

        console.log('[ReportGenerator] Initialized');
    },

    /**
     * Generate comprehensive PDF report
     */
    async generatePDFReport(options = {}) {
        console.log('[ReportGenerator] Generating PDF report...');

        try {
            // Check if jsPDF is available
            if (typeof jsPDF === 'undefined') {
                throw new Error('jsPDF library not loaded. Please include jsPDF in your HTML.');
            }

            // Fetch report data from backend
            const reportData = await this.fetchReportData(options);

            // Create PDF document
            const doc = new jsPDF(this.config.pdfOptions);

            // Add title page
            await this.addTitlePage(doc, reportData);

            // Add table of contents
            doc.addPage();
            await this.addTableOfContents(doc, reportData);

            // Add graph summary section
            doc.addPage();
            await this.addGraphSummarySection(doc, reportData);

            // Add document list section
            doc.addPage();
            await this.addDocumentListSection(doc, reportData);

            // Add claim analysis section
            doc.addPage();
            await this.addClaimAnalysisSection(doc, reportData);

            // Add evidence quality metrics section
            doc.addPage();
            await this.addEvidenceMetricsSection(doc, reportData);

            // Add visual graph snapshot
            if (options.includeGraphSnapshot !== false) {
                doc.addPage();
                await this.addGraphSnapshot(doc, reportData);
            }

            // Add page numbers and headers
            this.addPageNumbersAndHeaders(doc, reportData);

            // Generate filename with timestamp
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const filename = `research-report-${timestamp}.pdf`;

            // Save PDF
            doc.save(filename);

            // Record in history
            this.recordReport('pdf', filename, reportData);

            console.log('[ReportGenerator] PDF report generated:', filename);

            if (window.UI && UI.showNotification) {
                UI.showNotification('PDF report generated successfully', 'success');
            }

            return { success: true, filename, data: reportData };

        } catch (error) {
            console.error('[ReportGenerator] PDF generation failed:', error);
            if (window.UI && UI.showNotification) {
                UI.showNotification('Failed to generate PDF report: ' + error.message, 'error');
            }
            throw error;
        }
    },

    /**
     * Fetch report data from backend
     */
    async fetchReportData(options = {}) {
        console.log('[ReportGenerator] Fetching report data...');

        try {
            const response = await fetch('/api/reports/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    project_id: options.projectId || window.currentProject,
                    include_documents: options.includeDocuments !== false,
                    include_claims: options.includeClaims !== false,
                    include_evidence: options.includeEvidence !== false,
                    include_statistics: options.includeStatistics !== false
                })
            });

            if (!response.ok) {
                throw new Error(`Failed to fetch report data: ${response.statusText}`);
            }

            const data = await response.json();
            console.log('[ReportGenerator] Report data fetched:', data);

            return data;

        } catch (error) {
            console.error('[ReportGenerator] Failed to fetch report data:', error);
            // Fallback to local data if backend fails
            return this.getLocalReportData(options);
        }
    },

    /**
     * Get local report data as fallback
     */
    getLocalReportData(options = {}) {
        console.log('[ReportGenerator] Using local report data...');

        const graphData = window.GraphRenderer ? window.GraphRenderer.currentGraphData : { nodes: [], links: [] };

        return {
            project: {
                id: options.projectId || window.currentProject || 'default',
                name: window.currentProjectName || 'Research Project',
                created_at: new Date().toISOString(),
                description: 'Generated from local graph data'
            },
            statistics: {
                total_documents: graphData.nodes.filter(n => n.type === 'document').length,
                total_claims: graphData.nodes.filter(n => n.type === 'claim').length,
                total_evidence: graphData.links.filter(l => l.type === 'supports' || l.type === 'contradicts').length,
                total_relationships: graphData.links.length,
                avg_confidence: this.calculateAverageConfidence(graphData)
            },
            documents: this.extractDocuments(graphData),
            claims: this.extractClaims(graphData),
            evidence: this.extractEvidence(graphData),
            generated_at: new Date().toISOString()
        };
    },

    /**
     * Calculate average confidence from graph data
     */
    calculateAverageConfidence(graphData) {
        const confidences = graphData.nodes
            .filter(n => n.confidence !== undefined)
            .map(n => n.confidence);

        if (confidences.length === 0) return 0;
        return confidences.reduce((a, b) => a + b, 0) / confidences.length;
    },

    /**
     * Extract documents from graph data
     */
    extractDocuments(graphData) {
        return graphData.nodes
            .filter(n => n.type === 'document')
            .map(n => ({
                id: n.id,
                title: n.label || n.title || 'Untitled Document',
                created_at: n.created_at || new Date().toISOString(),
                metadata: n.metadata || {}
            }));
    },

    /**
     * Extract claims from graph data
     */
    extractClaims(graphData) {
        return graphData.nodes
            .filter(n => n.type === 'claim')
            .map(n => ({
                id: n.id,
                text: n.label || n.text || 'No claim text',
                confidence: n.confidence || 0,
                created_at: n.created_at || new Date().toISOString()
            }));
    },

    /**
     * Extract evidence from graph data
     */
    extractEvidence(graphData) {
        return graphData.links.map(l => ({
            source: l.source,
            target: l.target,
            type: l.type || 'related',
            weight: l.weight || 1.0
        }));
    },

    /**
     * Add title page to PDF
     */
    async addTitlePage(doc, reportData) {
        const pageWidth = doc.internal.pageSize.getWidth();
        const pageHeight = doc.internal.pageSize.getHeight();

        // Background
        doc.setFillColor(this.config.branding.colors.primary);
        doc.rect(0, 0, pageWidth, 60, 'F');

        // Title
        doc.setTextColor(255, 255, 255);
        doc.setFontSize(28);
        doc.setFont(undefined, 'bold');
        doc.text(this.config.branding.title, pageWidth / 2, 30, { align: 'center' });

        // Project name
        doc.setFontSize(18);
        doc.setFont(undefined, 'normal');
        doc.text(reportData.project.name, pageWidth / 2, 45, { align: 'center' });

        // Date
        doc.setTextColor(this.config.branding.colors.text);
        doc.setFontSize(12);
        const date = new Date(reportData.generated_at).toLocaleString();
        doc.text(`Generated: ${date}`, pageWidth / 2, 80, { align: 'center' });

        // Summary statistics
        doc.setFontSize(14);
        doc.setFont(undefined, 'bold');
        doc.text('Overview', 20, 110);

        doc.setFontSize(11);
        doc.setFont(undefined, 'normal');
        const stats = [
            `Total Documents: ${reportData.statistics.total_documents}`,
            `Total Claims: ${reportData.statistics.total_claims}`,
            `Total Evidence: ${reportData.statistics.total_evidence}`,
            `Relationships: ${reportData.statistics.total_relationships}`,
            `Avg. Confidence: ${(reportData.statistics.avg_confidence * 100).toFixed(1)}%`
        ];

        let yPos = 125;
        stats.forEach(stat => {
            doc.text(stat, 25, yPos);
            yPos += 10;
        });

        // Footer
        doc.setFontSize(10);
        doc.setTextColor(150, 150, 150);
        doc.text('Research Assistant Tool - AI-Powered Research Analysis', pageWidth / 2, pageHeight - 20, { align: 'center' });
    },

    /**
     * Add table of contents to PDF
     */
    async addTableOfContents(doc, reportData) {
        const pageWidth = doc.internal.pageSize.getWidth();

        doc.setTextColor(this.config.branding.colors.text);
        doc.setFontSize(20);
        doc.setFont(undefined, 'bold');
        doc.text('Table of Contents', 20, 30);

        doc.setFontSize(11);
        doc.setFont(undefined, 'normal');

        const contents = [
            { title: '1. Graph Summary', page: 3 },
            { title: '2. Document List', page: 4 },
            { title: '3. Claim Analysis', page: 5 },
            { title: '4. Evidence Quality Metrics', page: 6 },
            { title: '5. Visual Graph Snapshot', page: 7 }
        ];

        let yPos = 50;
        contents.forEach(item => {
            doc.text(item.title, 25, yPos);
            doc.text(String(item.page), pageWidth - 30, yPos, { align: 'right' });
            yPos += 12;
        });
    },

    /**
     * Add graph summary section to PDF
     */
    async addGraphSummarySection(doc, reportData) {
        doc.setTextColor(this.config.branding.colors.text);
        doc.setFontSize(18);
        doc.setFont(undefined, 'bold');
        doc.text('1. Graph Summary', 20, 30);

        doc.setFontSize(11);
        doc.setFont(undefined, 'normal');

        const summary = [
            'Graph Statistics:',
            '',
            `• Total Nodes: ${reportData.statistics.total_documents + reportData.statistics.total_claims}`,
            `• Documents: ${reportData.statistics.total_documents}`,
            `• Claims: ${reportData.statistics.total_claims}`,
            `• Evidence Links: ${reportData.statistics.total_evidence}`,
            `• Total Relationships: ${reportData.statistics.total_relationships}`,
            `• Average Confidence: ${(reportData.statistics.avg_confidence * 100).toFixed(1)}%`,
            '',
            'The research graph represents the interconnected knowledge base built from',
            'analyzed documents. Each node represents either a document or an extracted claim,',
            'while edges represent relationships such as evidence support or contradictions.'
        ];

        let yPos = 50;
        summary.forEach(line => {
            doc.text(line, 20, yPos);
            yPos += 7;
        });
    },

    /**
     * Add document list section to PDF
     */
    async addDocumentListSection(doc, reportData) {
        doc.setTextColor(this.config.branding.colors.text);
        doc.setFontSize(18);
        doc.setFont(undefined, 'bold');
        doc.text('2. Document List', 20, 30);

        doc.setFontSize(11);
        doc.setFont(undefined, 'normal');

        let yPos = 50;

        reportData.documents.forEach((doc_item, index) => {
            // Check if we need a new page
            if (yPos > 270) {
                doc.addPage();
                yPos = 20;
            }

            doc.setFont(undefined, 'bold');
            doc.text(`${index + 1}. ${doc_item.title}`, 20, yPos);
            yPos += 7;

            doc.setFont(undefined, 'normal');
            doc.setFontSize(9);
            doc.text(`ID: ${doc_item.id}`, 25, yPos);
            yPos += 5;
            doc.text(`Created: ${new Date(doc_item.created_at).toLocaleString()}`, 25, yPos);
            yPos += 8;

            doc.setFontSize(11);
        });
    },

    /**
     * Add claim analysis section to PDF
     */
    async addClaimAnalysisSection(doc, reportData) {
        doc.setTextColor(this.config.branding.colors.text);
        doc.setFontSize(18);
        doc.setFont(undefined, 'bold');
        doc.text('3. Claim Analysis', 20, 30);

        doc.setFontSize(11);
        doc.setFont(undefined, 'normal');

        let yPos = 50;

        // Sort claims by confidence
        const sortedClaims = [...reportData.claims].sort((a, b) => b.confidence - a.confidence);

        sortedClaims.forEach((claim, index) => {
            // Check if we need a new page
            if (yPos > 260) {
                doc.addPage();
                yPos = 20;
            }

            doc.setFont(undefined, 'bold');
            doc.text(`Claim ${index + 1}:`, 20, yPos);
            yPos += 7;

            doc.setFont(undefined, 'normal');
            const claimLines = doc.splitTextToSize(claim.text, 170);
            doc.text(claimLines, 25, yPos);
            yPos += claimLines.length * 5 + 2;

            doc.setFontSize(9);
            doc.text(`Confidence: ${(claim.confidence * 100).toFixed(1)}%`, 25, yPos);
            yPos += 5;
            doc.text(`ID: ${claim.id}`, 25, yPos);
            yPos += 8;

            doc.setFontSize(11);
        });
    },

    /**
     * Add evidence quality metrics section to PDF
     */
    async addEvidenceMetricsSection(doc, reportData) {
        doc.setTextColor(this.config.branding.colors.text);
        doc.setFontSize(18);
        doc.setFont(undefined, 'bold');
        doc.text('4. Evidence Quality Metrics', 20, 30);

        doc.setFontSize(11);
        doc.setFont(undefined, 'normal');

        // Calculate evidence metrics
        const supportingEvidence = reportData.evidence.filter(e => e.type === 'supports').length;
        const contradictingEvidence = reportData.evidence.filter(e => e.type === 'contradicts').length;
        const otherRelationships = reportData.evidence.length - supportingEvidence - contradictingEvidence;

        const metrics = [
            'Evidence Distribution:',
            '',
            `• Supporting Evidence: ${supportingEvidence}`,
            `• Contradicting Evidence: ${contradictingEvidence}`,
            `• Other Relationships: ${otherRelationships}`,
            '',
            'Quality Indicators:',
            '',
            `• Total Evidence Links: ${reportData.evidence.length}`,
            `• Average Confidence: ${(reportData.statistics.avg_confidence * 100).toFixed(1)}%`,
            `• Evidence per Claim: ${(reportData.evidence.length / Math.max(reportData.statistics.total_claims, 1)).toFixed(2)}`
        ];

        let yPos = 50;
        metrics.forEach(line => {
            doc.text(line, 20, yPos);
            yPos += 7;
        });
    },

    /**
     * Add graph snapshot to PDF
     */
    async addGraphSnapshot(doc, reportData) {
        doc.setTextColor(this.config.branding.colors.text);
        doc.setFontSize(18);
        doc.setFont(undefined, 'bold');
        doc.text('5. Visual Graph Snapshot', 20, 30);

        try {
            // Try to capture current graph visualization
            const svgElement = document.querySelector('#graph-svg');
            if (svgElement) {
                const canvas = await this.svgToCanvas(svgElement);
                const imgData = canvas.toDataURL('image/png');

                // Add image to PDF
                const imgWidth = 170;
                const imgHeight = (canvas.height * imgWidth) / canvas.width;
                doc.addImage(imgData, 'PNG', 20, 50, imgWidth, Math.min(imgHeight, 200));
            } else {
                doc.setFontSize(11);
                doc.setFont(undefined, 'normal');
                doc.text('Graph visualization not available at this time.', 20, 50);
            }
        } catch (error) {
            console.error('[ReportGenerator] Failed to add graph snapshot:', error);
            doc.setFontSize(11);
            doc.setFont(undefined, 'normal');
            doc.text('Failed to capture graph snapshot.', 20, 50);
        }
    },

    /**
     * Convert SVG to canvas (shared with export-manager.js)
     */
    async svgToCanvas(svgElement) {
        return new Promise((resolve, reject) => {
            try {
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');

                const bbox = svgElement.getBoundingClientRect();
                canvas.width = bbox.width;
                canvas.height = bbox.height;

                ctx.fillStyle = '#1a1a1a';
                ctx.fillRect(0, 0, canvas.width, canvas.height);

                const clonedSvg = svgElement.cloneNode(true);
                clonedSvg.setAttribute('xmlns', 'http://www.w3.org/2000/svg');

                const serializer = new XMLSerializer();
                const svgString = serializer.serializeToString(clonedSvg);

                const img = new Image();
                img.onload = () => {
                    ctx.drawImage(img, 0, 0);
                    resolve(canvas);
                };
                img.onerror = reject;

                const blob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' });
                const url = URL.createObjectURL(blob);
                img.src = url;

                setTimeout(() => URL.revokeObjectURL(url), 1000);
            } catch (error) {
                reject(error);
            }
        });
    },

    /**
     * Add page numbers and headers to PDF
     */
    addPageNumbersAndHeaders(doc, reportData) {
        const pageCount = doc.internal.getNumberOfPages();
        const pageWidth = doc.internal.pageSize.getWidth();
        const pageHeight = doc.internal.pageSize.getHeight();

        for (let i = 2; i <= pageCount; i++) {
            doc.setPage(i);

            // Header
            doc.setFontSize(9);
            doc.setTextColor(150, 150, 150);
            doc.text(reportData.project.name, 20, 10);

            // Page number
            doc.text(`Page ${i} of ${pageCount}`, pageWidth - 20, pageHeight - 10, { align: 'right' });
        }
    },

    /**
     * Export as Markdown
     */
    async exportMarkdown(options = {}) {
        console.log('[ReportGenerator] Exporting as Markdown...');

        try {
            const reportData = await this.fetchReportData(options);

            let markdown = '';

            // Title and metadata
            markdown += `# ${reportData.project.name}\n\n`;
            markdown += `**Generated:** ${new Date(reportData.generated_at).toLocaleString()}\n\n`;
            markdown += `---\n\n`;

            // Overview
            markdown += `## Overview\n\n`;
            markdown += `| Metric | Count |\n`;
            markdown += `|--------|-------|\n`;
            markdown += `| Total Documents | ${reportData.statistics.total_documents} |\n`;
            markdown += `| Total Claims | ${reportData.statistics.total_claims} |\n`;
            markdown += `| Total Evidence | ${reportData.statistics.total_evidence} |\n`;
            markdown += `| Relationships | ${reportData.statistics.total_relationships} |\n`;
            markdown += `| Avg. Confidence | ${(reportData.statistics.avg_confidence * 100).toFixed(1)}% |\n\n`;

            // Documents section
            markdown += `## Documents\n\n`;
            reportData.documents.forEach((doc, index) => {
                markdown += `### ${index + 1}. ${doc.title}\n\n`;
                markdown += `- **ID:** \`${doc.id}\`\n`;
                markdown += `- **Created:** ${new Date(doc.created_at).toLocaleString()}\n\n`;
            });

            // Claims section
            markdown += `## Claims\n\n`;
            const sortedClaims = [...reportData.claims].sort((a, b) => b.confidence - a.confidence);
            sortedClaims.forEach((claim, index) => {
                markdown += `### Claim ${index + 1}\n\n`;
                markdown += `${claim.text}\n\n`;
                markdown += `- **Confidence:** ${(claim.confidence * 100).toFixed(1)}%\n`;
                markdown += `- **ID:** \`${claim.id}\`\n\n`;
            });

            // Evidence section
            markdown += `## Evidence Network\n\n`;
            markdown += `Total evidence links: ${reportData.evidence.length}\n\n`;

            const supportingEvidence = reportData.evidence.filter(e => e.type === 'supports');
            const contradictingEvidence = reportData.evidence.filter(e => e.type === 'contradicts');

            markdown += `- **Supporting:** ${supportingEvidence.length}\n`;
            markdown += `- **Contradicting:** ${contradictingEvidence.length}\n`;
            markdown += `- **Other:** ${reportData.evidence.length - supportingEvidence.length - contradictingEvidence.length}\n\n`;

            // Export relationships
            if (options.includeRelationships !== false) {
                markdown += `### Relationships\n\n`;
                reportData.evidence.slice(0, 50).forEach((evidence, index) => {
                    markdown += `${index + 1}. \`${evidence.source}\` → \`${evidence.target}\` (${evidence.type})\n`;
                });
                if (reportData.evidence.length > 50) {
                    markdown += `\n*... and ${reportData.evidence.length - 50} more relationships*\n`;
                }
            }

            // Download markdown file
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const filename = `research-report-${timestamp}.md`;

            const blob = new Blob([markdown], { type: 'text/markdown' });
            const url = URL.createObjectURL(blob);

            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.click();

            URL.revokeObjectURL(url);

            // Record in history
            this.recordReport('markdown', filename, reportData);

            console.log('[ReportGenerator] Markdown export complete:', filename);

            if (window.UI && UI.showNotification) {
                UI.showNotification('Markdown report exported successfully', 'success');
            }

            return { success: true, filename, markdown };

        } catch (error) {
            console.error('[ReportGenerator] Markdown export failed:', error);
            if (window.UI && UI.showNotification) {
                UI.showNotification('Failed to export Markdown: ' + error.message, 'error');
            }
            throw error;
        }
    },

    /**
     * Export BibTeX citations
     */
    async exportBibTeX(options = {}) {
        console.log('[ReportGenerator] Exporting BibTeX citations...');

        try {
            const reportData = await this.fetchReportData(options);

            let bibtex = '';

            // Generate BibTeX entries for each document
            reportData.documents.forEach((doc, index) => {
                const citationKey = this.generateCitationKey(doc);

                // Determine entry type
                const entryType = this.detectEntryType(doc);

                bibtex += `@${entryType}{${citationKey},\n`;
                bibtex += `  title = {${doc.title}},\n`;

                // Add metadata fields
                if (doc.metadata) {
                    if (doc.metadata.author) {
                        bibtex += `  author = {${doc.metadata.author}},\n`;
                    }
                    if (doc.metadata.year) {
                        bibtex += `  year = {${doc.metadata.year}},\n`;
                    }
                    if (doc.metadata.journal) {
                        bibtex += `  journal = {${doc.metadata.journal}},\n`;
                    }
                    if (doc.metadata.publisher) {
                        bibtex += `  publisher = {${doc.metadata.publisher}},\n`;
                    }
                    if (doc.metadata.doi) {
                        bibtex += `  doi = {${doc.metadata.doi}},\n`;
                    }
                    if (doc.metadata.url) {
                        bibtex += `  url = {${doc.metadata.url}},\n`;
                    }
                }

                // Add note with research assistant info
                bibtex += `  note = {Analyzed with Research Assistant Tool on ${new Date(doc.created_at).toLocaleDateString()}}\n`;
                bibtex += `}\n\n`;
            });

            // Download BibTeX file
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const filename = `research-citations-${timestamp}.bib`;

            const blob = new Blob([bibtex], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);

            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.click();

            URL.revokeObjectURL(url);

            // Record in history
            this.recordReport('bibtex', filename, reportData);

            console.log('[ReportGenerator] BibTeX export complete:', filename);

            if (window.UI && UI.showNotification) {
                UI.showNotification('BibTeX citations exported successfully', 'success');
            }

            return { success: true, filename, bibtex };

        } catch (error) {
            console.error('[ReportGenerator] BibTeX export failed:', error);
            if (window.UI && UI.showNotification) {
                UI.showNotification('Failed to export BibTeX: ' + error.message, 'error');
            }
            throw error;
        }
    },

    /**
     * Generate citation key from document
     */
    generateCitationKey(doc) {
        // Format: author_year_title
        let key = '';

        if (doc.metadata && doc.metadata.author) {
            const author = doc.metadata.author.split(' ')[0].toLowerCase();
            key += author;
        } else {
            key += 'unknown';
        }

        if (doc.metadata && doc.metadata.year) {
            key += doc.metadata.year;
        } else {
            key += new Date(doc.created_at).getFullYear();
        }

        // Add first word of title
        const titleWords = doc.title.split(' ');
        if (titleWords.length > 0) {
            key += titleWords[0].toLowerCase().replace(/[^a-z0-9]/g, '');
        }

        return key;
    },

    /**
     * Detect BibTeX entry type from document metadata
     */
    detectEntryType(doc) {
        if (!doc.metadata) return 'misc';

        if (doc.metadata.journal) return 'article';
        if (doc.metadata.booktitle) return 'inproceedings';
        if (doc.metadata.publisher && !doc.metadata.journal) return 'book';
        if (doc.metadata.institution) return 'techreport';
        if (doc.metadata.school) return 'phdthesis';

        return 'misc';
    },

    /**
     * Copy individual citation to clipboard
     */
    async copyCitation(documentId) {
        try {
            const reportData = await this.fetchReportData();
            const doc = reportData.documents.find(d => d.id === documentId);

            if (!doc) {
                throw new Error('Document not found');
            }

            const citationKey = this.generateCitationKey(doc);
            const entryType = this.detectEntryType(doc);

            let bibtex = `@${entryType}{${citationKey},\n`;
            bibtex += `  title = {${doc.title}},\n`;
            // ... add other fields
            bibtex += `}\n`;

            await navigator.clipboard.writeText(bibtex);

            if (window.UI && UI.showNotification) {
                UI.showNotification('Citation copied to clipboard', 'success');
            }

        } catch (error) {
            console.error('[ReportGenerator] Failed to copy citation:', error);
            if (window.UI && UI.showNotification) {
                UI.showNotification('Failed to copy citation: ' + error.message, 'error');
            }
        }
    },

    /**
     * Initialize default report templates
     */
    initializeDefaultTemplates() {
        this.templates = {
            executive_summary: {
                name: 'Executive Summary',
                description: 'High-level overview for stakeholders',
                sections: ['overview', 'key_findings', 'statistics'],
                template: `
# {{project_name}} - Executive Summary

**Generated:** {{date}}

## Overview
{{project_description}}

## Key Statistics
- Total Documents: {{document_count}}
- Total Claims: {{claim_count}}
- Average Confidence: {{avg_confidence}}%

## Key Findings
{{#each top_claims}}
- {{this.text}} ({{this.confidence}}%)
{{/each}}
                `
            },

            technical_report: {
                name: 'Technical Report',
                description: 'Detailed technical analysis',
                sections: ['all'],
                template: `
# {{project_name}} - Technical Report

## 1. Introduction
This report provides a comprehensive technical analysis of the research project.

## 2. Methodology
Documents were analyzed using AI-powered claim extraction and evidence linking.

## 3. Results
### 3.1 Documents
{{#each documents}}
- {{this.title}}
{{/each}}

### 3.2 Claims
{{#each claims}}
{{this.text}} (Confidence: {{this.confidence}}%)
{{/each}}

## 4. Conclusion
Total relationships identified: {{relationship_count}}
                `
            },

            literature_review: {
                name: 'Literature Review',
                description: 'Academic literature review format',
                sections: ['documents', 'claims', 'evidence'],
                template: `
# Literature Review: {{project_name}}

## Abstract
This literature review synthesizes findings from {{document_count}} documents.

## Sources
{{#each documents}}
### {{this.title}}
{{this.metadata}}
{{/each}}

## Thematic Analysis
{{#each claims}}
**Theme {{@index}}:** {{this.text}}
{{/each}}
                `
            },

            quick_summary: {
                name: 'Quick Summary',
                description: 'Brief one-page summary',
                sections: ['overview', 'statistics'],
                template: `
# {{project_name}} - Quick Summary

**{{document_count}}** documents | **{{claim_count}}** claims | **{{avg_confidence}}%** confidence

## Top Claims
{{#each top_claims}}
{{@index}}. {{this.text}}
{{/each}}
                `
            },

            evidence_report: {
                name: 'Evidence Report',
                description: 'Focus on evidence quality and relationships',
                sections: ['evidence', 'metrics'],
                template: `
# Evidence Quality Report: {{project_name}}

## Evidence Distribution
- Supporting: {{supporting_count}}
- Contradicting: {{contradicting_count}}
- Other: {{other_count}}

## Quality Metrics
- Average Confidence: {{avg_confidence}}%
- Evidence per Claim: {{evidence_per_claim}}
- Network Density: {{network_density}}

## Detailed Evidence
{{#each evidence}}
{{this.source}} → {{this.target}} ({{this.type}})
{{/each}}
                `
            }
        };

        console.log('[ReportGenerator] Initialized 5 default templates');
    },

    /**
     * Generate report from custom template
     */
    async generateFromTemplate(templateName, options = {}) {
        console.log('[ReportGenerator] Generating report from template:', templateName);

        try {
            const template = this.templates[templateName];
            if (!template) {
                throw new Error(`Template "${templateName}" not found`);
            }

            // Check if Handlebars is available
            if (typeof Handlebars === 'undefined') {
                console.warn('[ReportGenerator] Handlebars not loaded, using simple substitution');
                return this.generateFromTemplateSimple(templateName, options);
            }

            const reportData = await this.fetchReportData(options);

            // Prepare template data
            const templateData = this.prepareTemplateData(reportData);

            // Compile and render template
            const compiledTemplate = Handlebars.compile(template.template);
            const output = compiledTemplate(templateData);

            // Download output
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const filename = `${templateName}-${timestamp}.md`;

            const blob = new Blob([output], { type: 'text/markdown' });
            const url = URL.createObjectURL(blob);

            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.click();

            URL.revokeObjectURL(url);

            // Record in history
            this.recordReport('template', filename, reportData);

            console.log('[ReportGenerator] Template report generated:', filename);

            if (window.UI && UI.showNotification) {
                UI.showNotification(`Report generated from template: ${template.name}`, 'success');
            }

            return { success: true, filename, output };

        } catch (error) {
            console.error('[ReportGenerator] Template generation failed:', error);
            if (window.UI && UI.showNotification) {
                UI.showNotification('Failed to generate from template: ' + error.message, 'error');
            }
            throw error;
        }
    },

    /**
     * Prepare data for template rendering
     */
    prepareTemplateData(reportData) {
        return {
            project_name: reportData.project.name,
            project_description: reportData.project.description || 'No description provided',
            date: new Date(reportData.generated_at).toLocaleString(),
            document_count: reportData.statistics.total_documents,
            claim_count: reportData.statistics.total_claims,
            avg_confidence: (reportData.statistics.avg_confidence * 100).toFixed(1),
            relationship_count: reportData.statistics.total_relationships,
            documents: reportData.documents,
            claims: reportData.claims,
            evidence: reportData.evidence,
            top_claims: reportData.claims.sort((a, b) => b.confidence - a.confidence).slice(0, 5),
            supporting_count: reportData.evidence.filter(e => e.type === 'supports').length,
            contradicting_count: reportData.evidence.filter(e => e.type === 'contradicts').length,
            other_count: reportData.evidence.filter(e => e.type !== 'supports' && e.type !== 'contradicts').length,
            evidence_per_claim: (reportData.evidence.length / Math.max(reportData.statistics.total_claims, 1)).toFixed(2),
            network_density: this.calculateNetworkDensity(reportData)
        };
    },

    /**
     * Calculate network density
     */
    calculateNetworkDensity(reportData) {
        const nodeCount = reportData.statistics.total_documents + reportData.statistics.total_claims;
        const maxPossibleEdges = (nodeCount * (nodeCount - 1)) / 2;

        if (maxPossibleEdges === 0) return 0;

        const density = reportData.evidence.length / maxPossibleEdges;
        return (density * 100).toFixed(2);
    },

    /**
     * Save custom template
     */
    saveTemplate(templateName, templateData) {
        this.templates[templateName] = templateData;
        this.saveTemplates();

        console.log('[ReportGenerator] Template saved:', templateName);

        if (window.UI && UI.showNotification) {
            UI.showNotification('Template saved successfully', 'success');
        }
    },

    /**
     * Delete custom template
     */
    deleteTemplate(templateName) {
        if (this.templates[templateName]) {
            delete this.templates[templateName];
            this.saveTemplates();

            console.log('[ReportGenerator] Template deleted:', templateName);

            if (window.UI && UI.showNotification) {
                UI.showNotification('Template deleted successfully', 'success');
            }
        }
    },

    /**
     * Load templates from localStorage
     */
    loadTemplates() {
        try {
            const stored = localStorage.getItem('report_templates');
            if (stored) {
                const customTemplates = JSON.parse(stored);
                Object.assign(this.templates, customTemplates);
                console.log('[ReportGenerator] Loaded templates from localStorage');
            }
        } catch (error) {
            console.error('[ReportGenerator] Failed to load templates:', error);
        }
    },

    /**
     * Save templates to localStorage
     */
    saveTemplates() {
        try {
            // Only save custom templates (not default ones)
            const customTemplates = {};
            for (const [name, template] of Object.entries(this.templates)) {
                if (template.custom) {
                    customTemplates[name] = template;
                }
            }
            localStorage.setItem('report_templates', JSON.stringify(customTemplates));
        } catch (error) {
            console.error('[ReportGenerator] Failed to save templates:', error);
        }
    },

    /**
     * Schedule automatic report generation
     */
    async scheduleExport(scheduleConfig) {
        console.log('[ReportGenerator] Scheduling export:', scheduleConfig);

        try {
            const response = await fetch('/api/reports/schedule', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(scheduleConfig)
            });

            if (!response.ok) {
                throw new Error(`Failed to schedule export: ${response.statusText}`);
            }

            const result = await response.json();

            console.log('[ReportGenerator] Export scheduled:', result.schedule_id);

            if (window.UI && UI.showNotification) {
                UI.showNotification('Export scheduled successfully', 'success');
            }

            return result;

        } catch (error) {
            console.error('[ReportGenerator] Failed to schedule export:', error);
            if (window.UI && UI.showNotification) {
                UI.showNotification('Failed to schedule export: ' + error.message, 'error');
            }
            throw error;
        }
    },

    /**
     * Get scheduled exports
     */
    async getScheduledExports() {
        try {
            const response = await fetch('/api/reports/schedules');

            if (!response.ok) {
                throw new Error('Failed to fetch schedules');
            }

            const schedules = await response.json();
            return schedules;

        } catch (error) {
            console.error('[ReportGenerator] Failed to fetch schedules:', error);
            return [];
        }
    },

    /**
     * Cancel scheduled export
     */
    async cancelScheduledExport(scheduleId) {
        try {
            const response = await fetch(`/api/reports/schedule/${scheduleId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error('Failed to cancel schedule');
            }

            if (window.UI && UI.showNotification) {
                UI.showNotification('Scheduled export cancelled', 'success');
            }

        } catch (error) {
            console.error('[ReportGenerator] Failed to cancel schedule:', error);
            if (window.UI && UI.showNotification) {
                UI.showNotification('Failed to cancel schedule: ' + error.message, 'error');
            }
        }
    },

    /**
     * Record report in history
     */
    recordReport(type, filename, reportData) {
        const record = {
            id: Date.now().toString(),
            type,
            filename,
            timestamp: new Date().toISOString(),
            project_name: reportData.project.name,
            document_count: reportData.statistics.total_documents,
            claim_count: reportData.statistics.total_claims
        };

        this.reportHistory.unshift(record);

        // Keep only last 50 reports
        if (this.reportHistory.length > 50) {
            this.reportHistory = this.reportHistory.slice(0, 50);
        }

        this.saveReportHistory();
    },

    /**
     * Load report history from localStorage
     */
    loadReportHistory() {
        try {
            const stored = localStorage.getItem('report_history');
            if (stored) {
                this.reportHistory = JSON.parse(stored);
                console.log('[ReportGenerator] Loaded report history');
            }
        } catch (error) {
            console.error('[ReportGenerator] Failed to load report history:', error);
        }
    },

    /**
     * Save report history to localStorage
     */
    saveReportHistory() {
        try {
            localStorage.setItem('report_history', JSON.stringify(this.reportHistory));
        } catch (error) {
            console.error('[ReportGenerator] Failed to save report history:', error);
        }
    },

    /**
     * Get report history
     */
    getReportHistory() {
        return this.reportHistory;
    }
};

// Initialize on load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        ReportGenerator.initialize();
    });
} else {
    ReportGenerator.initialize();
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ReportGenerator;
}
