/**
 * Comparison Report Generator
 *
 * Generates exportable comparison reports in multiple formats:
 * - Markdown
 * - HTML
 * - JSON
 */

class ComparisonReportGenerator {
    /**
     * Generate report in specified format
     */
    static async generateReport(format, documents, alignedClaims, consensusData) {
        const data = {
            documents: documents,
            alignedClaims: alignedClaims,
            consensus: consensusData,
            timestamp: new Date().toISOString(),
            metadata: {
                generatedBy: 'Research Assistant Tool - Document Comparison',
                version: '1.0.0',
                documentCount: documents.length,
                claimGroupCount: alignedClaims.length
            }
        };

        switch (format) {
            case 'markdown':
                return this.generateMarkdown(data);
            case 'html':
                return this.generateHTML(data);
            case 'json':
                return this.generateJSON(data);
            default:
                throw new Error(`Unsupported format: ${format}`);
        }
    }

    /**
     * Generate Markdown report
     */
    static generateMarkdown(data) {
        let md = '';

        // Header
        md += '# Document Comparison Report\n\n';
        md += `**Generated**: ${new Date(data.timestamp).toLocaleString()}\n\n`;
        md += `**Tool**: ${data.metadata.generatedBy}\n\n`;
        md += '---\n\n';

        // Documents section
        md += '## Documents Compared\n\n';
        data.documents.forEach((doc, i) => {
            md += `${i + 1}. **${doc.title}**\n`;
            md += `   - Claims: ${doc.claims.length}\n`;
            md += `   - ID: \`${doc.id}\`\n`;
            if (doc.metadata && doc.metadata.author) {
                md += `   - Author: ${doc.metadata.author}\n`;
            }
            md += '\n';
        });

        // Consensus section
        if (data.consensus) {
            md += '## Consensus Analysis\n\n';
            md += `**Overall Consensus Score**: ${Math.round(data.consensus.overallConsensus * 100)}%\n\n`;

            // Agreements
            if (data.consensus.agreements.length > 0) {
                md += `### ✓ Agreements (${data.consensus.agreements.length})\n\n`;
                md += 'These claims appear in all documents with high similarity:\n\n';
                data.consensus.agreements.forEach((a, i) => {
                    md += `${i + 1}. **${a.claim}**\n`;
                    md += `   - Confidence: ${a.confidence}%\n`;
                    md += `   - Sources: ${a.sources.join(', ')}\n`;
                    if (a.variants) {
                        md += `   - Variants: ${a.variants.length} textual variations\n`;
                    }
                    md += '\n';
                });
                md += '\n';
            }

            // Disagreements
            if (data.consensus.disagreements.length > 0) {
                md += `### ⚠ Disagreements (${data.consensus.disagreements.length})\n\n`;
                md += 'These topics show contradictory claims across documents:\n\n';
                data.consensus.disagreements.forEach((d, i) => {
                    md += `${i + 1}. **Topic**: ${d.topic}\n`;
                    md += `   - Type: ${d.contradictionType}\n`;
                    md += `   - Severity: ${this.formatSeverity(d.severity)}\n`;
                    md += `   - Variants:\n`;
                    d.variants.forEach(v => {
                        md += `     - **[${v.source}]**: "${v.text}" *(${v.confidence}% confidence)*\n`;
                    });
                    md += '\n';
                });
                md += '\n';
            }

            // Partial Agreements
            if (data.consensus.partialAgreements.length > 0) {
                md += `### ≈ Partial Agreements (${data.consensus.partialAgreements.length})\n\n`;
                md += 'These claims appear in some but not all documents:\n\n';
                data.consensus.partialAgreements.forEach((p, i) => {
                    md += `${i + 1}. **${p.claim}**\n`;
                    md += `   - Support: ${p.support}\n`;
                    md += `   - Confidence: ${p.confidence}%\n`;
                    md += `   - Supporting documents: ${p.supportingDocs.join(', ')}\n`;
                    if (p.missingSources.length > 0) {
                        md += `   - Not found in: ${p.missingSources.join(', ')}\n`;
                    }
                    md += '\n';
                });
                md += '\n';
            }

            // Unique Positions
            if (data.consensus.uniquePositions.length > 0) {
                md += `### ⭐ Unique Positions (${data.consensus.uniquePositions.length})\n\n`;
                md += 'These claims appear in only one document:\n\n';
                data.consensus.uniquePositions.forEach((u, i) => {
                    md += `${i + 1}. **[${u.source}]** ${u.claim}\n`;
                    md += `   - Confidence: ${u.confidence}%\n`;
                    if (u.significance) {
                        md += `   - Significance: ${Math.round(u.significance * 100)}%\n`;
                    }
                    md += '\n';
                });
                md += '\n';
            }

            // Metrics
            if (data.consensus.metrics) {
                md += '## Metrics\n\n';
                const m = data.consensus.metrics;
                md += `- **Agreement Rate**: ${Math.round(m.agreementRate * 100)}%\n`;
                md += `- **Disagreement Rate**: ${Math.round(m.disagreementRate * 100)}%\n`;
                md += `- **Partial Agreement Rate**: ${Math.round(m.partialAgreementRate * 100)}%\n`;
                md += `- **Unique Position Rate**: ${Math.round(m.uniqueRate * 100)}%\n`;
                md += `- **Average Confidence**: ${m.avgConfidence}%\n`;
                md += `- **Total Items**: ${m.totalItems}\n`;
                md += '\n';
            }
        }

        // Claim Groups section
        md += '## Aligned Claim Groups\n\n';
        md += `Total groups: ${data.alignedClaims.length}\n\n`;

        data.alignedClaims.forEach((group, i) => {
            md += `### Group ${i + 1}: ${group.type.toUpperCase()}\n\n`;
            md += `- **Similarity**: ${Math.round(group.similarity * 100)}%\n`;
            md += `- **Claims**:\n`;
            group.claims.forEach(claim => {
                md += `  - **[${claim.docTitle || claim.source}]**: ${claim.text}\n`;
            });
            md += '\n';
        });

        // Footer
        md += '---\n\n';
        md += '*This report was automatically generated by the Research Assistant Tool.*\n';

        return md;
    }

    /**
     * Generate HTML report
     */
    static generateHTML(data) {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document Comparison Report</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            border-radius: 8px;
        }

        h1 {
            color: #1976D2;
            border-bottom: 3px solid #1976D2;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }

        h2 {
            color: #2196F3;
            margin-top: 30px;
            margin-bottom: 15px;
            padding-left: 10px;
            border-left: 4px solid #2196F3;
        }

        h3 {
            color: #555;
            margin-top: 20px;
            margin-bottom: 10px;
        }

        .metadata {
            background: #f9f9f9;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            font-size: 0.9em;
        }

        .consensus-score {
            text-align: center;
            margin: 30px 0;
        }

        .score-circle {
            display: inline-block;
            width: 150px;
            height: 150px;
            border-radius: 50%;
            color: white;
            font-size: 2.5em;
            font-weight: bold;
            line-height: 150px;
            margin: 20px;
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }

        .metric-card {
            background: #f0f7ff;
            padding: 20px;
            border-radius: 5px;
            text-align: center;
            border: 1px solid #d0e7ff;
        }

        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #1976D2;
        }

        .metric-label {
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }

        .document-list {
            list-style: none;
        }

        .document-item {
            background: #fafafa;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            border-left: 4px solid #2196F3;
        }

        .consensus-item {
            background: #fff;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            border-left: 4px solid #ccc;
        }

        .consensus-item.agreement {
            border-left-color: #4CAF50;
            background: #f1f8f4;
        }

        .consensus-item.disagreement {
            border-left-color: #F44336;
            background: #fef5f5;
        }

        .consensus-item.partial {
            border-left-color: #FF9800;
            background: #fff8f0;
        }

        .consensus-item.unique {
            border-left-color: #9C27B0;
            background: #f9f5fa;
        }

        .badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 500;
            margin-right: 5px;
        }

        .badge.confidence {
            background: #E3F2FD;
            color: #1976D2;
        }

        .badge.support {
            background: #FFF3E0;
            color: #F57C00;
        }

        .badge.type {
            background: #F3E5F5;
            color: #7B1FA2;
        }

        .variant-list {
            margin-left: 20px;
            margin-top: 10px;
        }

        .variant-item {
            padding: 8px;
            background: #f9f9f9;
            margin: 5px 0;
            border-radius: 3px;
        }

        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }

        @media print {
            body {
                background: white;
                padding: 0;
            }

            .container {
                box-shadow: none;
                padding: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Document Comparison Report</h1>

        <div class="metadata">
            <strong>Generated:</strong> ${new Date(data.timestamp).toLocaleString()}<br>
            <strong>Tool:</strong> ${data.metadata.generatedBy}<br>
            <strong>Documents:</strong> ${data.metadata.documentCount}<br>
            <strong>Claim Groups:</strong> ${data.metadata.claimGroupCount}
        </div>

        ${this.generateHTMLDocumentsSection(data.documents)}
        ${data.consensus ? this.generateHTMLConsensusSection(data.consensus) : ''}
        ${this.generateHTMLClaimGroupsSection(data.alignedClaims)}

        <div class="footer">
            <p>This report was automatically generated by the Research Assistant Tool.</p>
            <p>Generated on ${new Date(data.timestamp).toLocaleString()}</p>
        </div>
    </div>
</body>
</html>`;
    }

    /**
     * Generate documents section for HTML
     */
    static generateHTMLDocumentsSection(documents) {
        return `
        <h2>Documents Compared</h2>
        <ul class="document-list">
            ${documents.map((doc, i) => `
                <li class="document-item">
                    <strong>${i + 1}. ${this.escapeHtml(doc.title)}</strong><br>
                    <span class="badge confidence">${doc.claims.length} claims</span>
                    <span class="badge type">ID: ${doc.id}</span>
                </li>
            `).join('')}
        </ul>
        `;
    }

    /**
     * Generate consensus section for HTML
     */
    static generateHTMLConsensusSection(consensus) {
        const score = Math.round(consensus.overallConsensus * 100);
        const color = this.getConsensusColor(consensus.overallConsensus);

        return `
        <h2>Consensus Analysis</h2>

        <div class="consensus-score">
            <h3>Overall Consensus Score</h3>
            <div class="score-circle" style="background: ${color}">
                ${score}%
            </div>
            <p>${this.getConsensusDescription(consensus.overallConsensus)}</p>
        </div>

        ${consensus.metrics ? this.generateHTMLMetrics(consensus.metrics) : ''}

        ${consensus.agreements.length > 0 ? `
            <h3>✓ Agreements (${consensus.agreements.length})</h3>
            ${consensus.agreements.map((a, i) => `
                <div class="consensus-item agreement">
                    <strong>${i + 1}. ${this.escapeHtml(a.claim)}</strong><br>
                    <span class="badge confidence">${a.confidence}% confidence</span>
                    <span class="badge support">Unanimous</span><br>
                    <small>Sources: ${a.sources.join(', ')}</small>
                </div>
            `).join('')}
        ` : ''}

        ${consensus.disagreements.length > 0 ? `
            <h3>⚠ Disagreements (${consensus.disagreements.length})</h3>
            ${consensus.disagreements.map((d, i) => `
                <div class="consensus-item disagreement">
                    <strong>${i + 1}. Topic: ${this.escapeHtml(d.topic)}</strong><br>
                    <span class="badge type">${d.contradictionType}</span>
                    <span class="badge support">${this.formatSeverity(d.severity)} severity</span><br>
                    <ul class="variant-list">
                        ${d.variants.map(v => `
                            <li class="variant-item">
                                <strong>[${this.escapeHtml(v.source)}]:</strong>
                                "${this.escapeHtml(v.text)}"
                                <span class="badge confidence">${v.confidence}%</span>
                            </li>
                        `).join('')}
                    </ul>
                </div>
            `).join('')}
        ` : ''}

        ${consensus.partialAgreements.length > 0 ? `
            <h3>≈ Partial Agreements (${consensus.partialAgreements.length})</h3>
            ${consensus.partialAgreements.map((p, i) => `
                <div class="consensus-item partial">
                    <strong>${i + 1}. ${this.escapeHtml(p.claim)}</strong><br>
                    <span class="badge support">${p.support}</span>
                    <span class="badge confidence">${p.confidence}% confidence</span><br>
                    <small>Supporting: ${p.supportingDocs.join(', ')}</small>
                    ${p.missingSources.length > 0 ? `<br><small>Missing: ${p.missingSources.join(', ')}</small>` : ''}
                </div>
            `).join('')}
        ` : ''}

        ${consensus.uniquePositions.length > 0 ? `
            <h3>⭐ Unique Positions (${consensus.uniquePositions.length})</h3>
            ${consensus.uniquePositions.map((u, i) => `
                <div class="consensus-item unique">
                    <strong>${i + 1}. [${this.escapeHtml(u.source)}]</strong> ${this.escapeHtml(u.claim)}<br>
                    <span class="badge confidence">${u.confidence}% confidence</span>
                </div>
            `).join('')}
        ` : ''}
        `;
    }

    /**
     * Generate metrics grid for HTML
     */
    static generateHTMLMetrics(metrics) {
        return `
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value">${Math.round(metrics.agreementRate * 100)}%</div>
                <div class="metric-label">Agreement Rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">${Math.round(metrics.disagreementRate * 100)}%</div>
                <div class="metric-label">Disagreement Rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">${Math.round(metrics.partialAgreementRate * 100)}%</div>
                <div class="metric-label">Partial Agreement</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">${metrics.avgConfidence}%</div>
                <div class="metric-label">Avg Confidence</div>
            </div>
        </div>
        `;
    }

    /**
     * Generate claim groups section for HTML
     */
    static generateHTMLClaimGroupsSection(alignedClaims) {
        return `
        <h2>Aligned Claim Groups</h2>
        <p>Total groups: ${alignedClaims.length}</p>
        ${alignedClaims.map((group, i) => `
            <div class="consensus-item">
                <strong>Group ${i + 1}: ${group.type.toUpperCase()}</strong><br>
                <span class="badge confidence">${Math.round(group.similarity * 100)}% similar</span><br>
                <ul style="margin-top: 10px;">
                    ${group.claims.map(claim => `
                        <li><strong>[${this.escapeHtml(claim.docTitle || claim.source)}]:</strong> ${this.escapeHtml(claim.text)}</li>
                    `).join('')}
                </ul>
            </div>
        `).join('')}
        `;
    }

    /**
     * Generate JSON report
     */
    static generateJSON(data) {
        return JSON.stringify(data, null, 2);
    }

    /**
     * Download report
     */
    static downloadReport(content, filename, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.style.display = 'none';

        document.body.appendChild(a);
        a.click();

        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    /**
     * Get consensus color
     */
    static getConsensusColor(score) {
        if (score >= 0.8) return '#4CAF50';
        if (score >= 0.6) return '#8BC34A';
        if (score >= 0.4) return '#FFC107';
        if (score >= 0.2) return '#FF9800';
        return '#F44336';
    }

    /**
     * Get consensus description
     */
    static getConsensusDescription(score) {
        if (score >= 0.8) return 'Strong consensus - documents largely agree';
        if (score >= 0.6) return 'Moderate consensus - substantial agreement with some differences';
        if (score >= 0.4) return 'Weak consensus - mixed agreement and disagreement';
        if (score >= 0.2) return 'Low consensus - significant disagreements';
        return 'No consensus - documents largely contradict';
    }

    /**
     * Format severity
     */
    static formatSeverity(severity) {
        if (severity >= 0.7) return 'High';
        if (severity >= 0.4) return 'Medium';
        return 'Low';
    }

    /**
     * Escape HTML
     */
    static escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ComparisonReportGenerator;
}
