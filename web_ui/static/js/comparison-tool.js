/**
 * Document Comparison Tool
 *
 * Provides comprehensive document comparison features:
 * - Side-by-side document viewing
 * - Claim alignment and similarity detection
 * - Consensus analysis across multiple documents
 * - Visual highlighting of differences
 * - Export comparison reports
 */

class ComparisonTool {
    static documents = [];
    static alignedClaims = [];
    static consensusData = null;
    static viewMode = 'side-by-side';
    static options = {
        showUnique: true,
        showShared: true,
        showSimilar: true,
        alignClaims: true
    };

    /**
     * Open the comparison modal
     */
    static async open() {
        const modal = document.getElementById('document-comparison-modal');
        if (!modal) {
            console.error('Comparison modal not found');
            return;
        }

        // Load available documents
        await this.loadAvailableDocuments();

        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    }

    /**
     * Close the comparison modal
     */
    static close() {
        const modal = document.getElementById('document-comparison-modal');
        if (modal) {
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }

        // Reset state
        this.documents = [];
        this.alignedClaims = [];
        this.consensusData = null;
    }

    /**
     * Load available documents into selector dropdowns
     */
    static async loadAvailableDocuments() {
        try {
            const response = await fetch('/api/full-graph');
            const data = await response.json();

            const documents = data.documents || [];

            // Populate all document selectors
            const selectors = document.querySelectorAll('.document-selector select');
            selectors.forEach(select => {
                select.innerHTML = '<option value="">Select document...</option>';
                documents.forEach(doc => {
                    const option = document.createElement('option');
                    option.value = doc.id;
                    option.textContent = doc.title || `Document ${doc.id}`;
                    select.appendChild(option);
                });
            });

        } catch (error) {
            console.error('Failed to load documents:', error);
            this.showError('Failed to load documents');
        }
    }

    /**
     * Load a document for comparison
     */
    static async loadDocument(panelIndex, docId) {
        if (!docId) {
            // Remove document if empty selection
            this.documents = this.documents.filter((_, i) => i !== panelIndex - 1);
            this.renderPanels();
            return;
        }

        try {
            const response = await fetch(`/api/nodes/${docId}/full-details`);
            const doc = await response.json();

            // Extract claims from document
            const claims = await this.extractDocumentClaims(docId);

            const documentData = {
                id: docId,
                title: doc.title || `Document ${docId}`,
                claims: claims,
                content: doc.content || '',
                metadata: doc
            };

            // Add or update document at the panel index
            this.documents[panelIndex - 1] = documentData;
            this.documents = this.documents.filter(d => d); // Remove nulls

            // Re-render panels
            await this.renderPanels();

            // Auto-align claims if option enabled
            if (this.options.alignClaims && this.documents.length >= 2) {
                await this.alignClaims();
            }

        } catch (error) {
            console.error(`Failed to load document ${docId}:`, error);
            this.showError(`Failed to load document: ${error.message}`);
        }
    }

    /**
     * Extract all claims from a document
     */
    static async extractDocumentClaims(docId) {
        try {
            // Query for all claims related to this document
            const response = await fetch('/api/full-graph');
            const data = await response.json();

            const claims = [];

            // Find claims that belong to this document
            if (data.super_claims) {
                data.super_claims.forEach(superClaim => {
                    if (superClaim.document_id === docId ||
                        (superClaim.documents && superClaim.documents.includes(docId))) {
                        claims.push({
                            id: superClaim.id,
                            text: superClaim.text,
                            type: 'super_claim',
                            confidence: superClaim.confidence || 50,
                            source: superClaim.source || docId,
                            children: []
                        });
                    }
                });
            }

            if (data.sub_claims) {
                data.sub_claims.forEach(subClaim => {
                    if (subClaim.document_id === docId ||
                        (subClaim.documents && subClaim.documents.includes(docId))) {
                        claims.push({
                            id: subClaim.id,
                            text: subClaim.text,
                            type: 'sub_claim',
                            confidence: subClaim.confidence || 50,
                            source: subClaim.source || docId,
                            parent_id: subClaim.parent_id
                        });
                    }
                });
            }

            // Build hierarchy
            const topLevelClaims = claims.filter(c => c.type === 'super_claim');
            topLevelClaims.forEach(parent => {
                parent.children = claims.filter(c => c.parent_id === parent.id);
            });

            return topLevelClaims;

        } catch (error) {
            console.error('Failed to extract claims:', error);
            return [];
        }
    }

    /**
     * Render document panels
     */
    static async renderPanels() {
        const container = document.getElementById('document-panels');
        if (!container) return;

        container.innerHTML = '';

        if (this.documents.length === 0) {
            container.innerHTML = '<div class="empty-state">Select documents to compare</div>';
            return;
        }

        // Create panels based on view mode
        if (this.viewMode === 'side-by-side') {
            this.documents.forEach((doc, index) => {
                const panel = this.createDocumentPanel(doc, index);
                container.appendChild(panel);
            });
        } else if (this.viewMode === 'unified') {
            const unifiedPanel = this.createUnifiedPanel();
            container.appendChild(unifiedPanel);
        } else if (this.viewMode === 'claims-only') {
            const claimsPanel = this.createClaimsOnlyPanel();
            container.appendChild(claimsPanel);
        }

        // Update statistics
        this.updateStatistics();
    }

    /**
     * Create a document panel for side-by-side view
     */
    static createDocumentPanel(doc, index) {
        const panel = document.createElement('div');
        panel.className = 'document-panel';
        panel.dataset.docId = doc.id;
        panel.dataset.index = index;

        // Count claim types
        const uniqueClaims = this.countClaimsByType(doc, 'unique');
        const sharedClaims = this.countClaimsByType(doc, 'shared');
        const similarClaims = this.countClaimsByType(doc, 'similar');

        panel.innerHTML = `
            <div class="panel-header">
                <h3>${this.escapeHtml(doc.title)}</h3>
                <div class="panel-stats">
                    <span class="stat-badge">${doc.claims.length} claims</span>
                    <span class="stat-badge unique">${uniqueClaims} unique</span>
                    <span class="stat-badge shared">${sharedClaims} shared</span>
                    <span class="stat-badge similar">${similarClaims} similar</span>
                </div>
            </div>
            <div class="panel-content" id="panel-content-${index}">
                ${this.renderClaimsList(doc, index)}
            </div>
        `;

        return panel;
    }

    /**
     * Render claims list for a document
     */
    static renderClaimsList(doc, docIndex) {
        let html = '';

        doc.claims.forEach((claim, claimIndex) => {
            const claimType = this.getClaimType(claim, doc);

            // Filter by visibility options
            if (!this.shouldShowClaim(claimType)) {
                return;
            }

            const claimId = `claim-${docIndex}-${claimIndex}`;

            html += `
                <div class="claim-item ${claimType}"
                     id="${claimId}"
                     data-claim-id="${claim.id}"
                     data-type="${claimType}">
                    <div class="claim-header">
                        <span class="claim-type-badge">${this.getClaimIcon(claimType)} ${claimType.toUpperCase()}</span>
                        <span class="confidence-badge">${Math.round(claim.confidence)}%</span>
                    </div>
                    <div class="claim-text">${this.escapeHtml(claim.text)}</div>
                    ${claim.children && claim.children.length > 0 ? `
                        <div class="sub-claims">
                            ${claim.children.map(child => `
                                <div class="sub-claim-item">
                                    <span class="sub-claim-bullet">→</span>
                                    ${this.escapeHtml(child.text)}
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>
            `;
        });

        return html || '<div class="empty-state">No claims to display</div>';
    }

    /**
     * Determine claim type (unique, shared, similar)
     */
    static getClaimType(claim, doc) {
        if (this.alignedClaims.length === 0) {
            return 'unique'; // Default before alignment
        }

        // Find this claim in aligned groups
        const group = this.alignedClaims.find(g =>
            g.claims.some(c => c.id === claim.id || c.text === claim.text)
        );

        if (!group) return 'unique';

        return group.type || 'unique';
    }

    /**
     * Count claims by type
     */
    static countClaimsByType(doc, type) {
        return doc.claims.filter(claim =>
            this.getClaimType(claim, doc) === type
        ).length;
    }

    /**
     * Check if claim should be shown based on filter options
     */
    static shouldShowClaim(claimType) {
        if (claimType === 'unique' && !this.options.showUnique) return false;
        if (claimType === 'shared' && !this.options.showShared) return false;
        if (claimType === 'similar' && !this.options.showSimilar) return false;
        return true;
    }

    /**
     * Get icon for claim type
     */
    static getClaimIcon(type) {
        const icons = {
            unique: '⭐',
            shared: '✓',
            similar: '≈',
            contradicting: '⚠'
        };
        return icons[type] || '•';
    }

    /**
     * Align claims across documents
     */
    static async alignClaims() {
        if (this.documents.length < 2) {
            this.showError('Need at least 2 documents to align claims');
            return;
        }

        try {
            this.showProgress('Aligning claims...');

            // Extract all claims from all documents
            const allClaims = [];
            this.documents.forEach((doc, docIndex) => {
                doc.claims.forEach(claim => {
                    allClaims.push({
                        ...claim,
                        docIndex,
                        docId: doc.id,
                        docTitle: doc.title
                    });
                });
            });

            // Calculate pairwise similarity matrix
            const similarityMatrix = await this.buildSimilarityMatrix(allClaims);

            // Group similar claims using hierarchical clustering
            const clusters = this.clusterClaims(allClaims, similarityMatrix, 0.75);

            // Create aligned claim groups
            this.alignedClaims = clusters.map((cluster, i) => ({
                id: `cluster-${i}`,
                claims: cluster.claims,
                similarity: cluster.avgSimilarity,
                type: this.determineClaimType(cluster.claims)
            }));

            // Re-render with alignment
            await this.renderPanels();

            // Draw connection lines if in side-by-side mode
            if (this.viewMode === 'side-by-side') {
                this.drawConnectionLines();
            }

            this.hideProgress();
            this.showSuccess(`Aligned ${this.alignedClaims.length} claim groups`);

        } catch (error) {
            console.error('Failed to align claims:', error);
            this.hideProgress();
            this.showError(`Failed to align claims: ${error.message}`);
        }
    }

    /**
     * Build similarity matrix for all claims
     */
    static async buildSimilarityMatrix(claims) {
        const n = claims.length;
        const matrix = Array(n).fill(null).map(() => Array(n).fill(0));

        for (let i = 0; i < n; i++) {
            matrix[i][i] = 1.0;

            for (let j = i + 1; j < n; j++) {
                const similarity = await this.calculateSimilarity(
                    claims[i].text,
                    claims[j].text
                );
                matrix[i][j] = similarity;
                matrix[j][i] = similarity;
            }
        }

        return matrix;
    }

    /**
     * Calculate semantic similarity between two texts
     */
    static async calculateSimilarity(text1, text2) {
        try {
            // Use simple text similarity as fallback
            const sim = this.jaccardSimilarity(text1, text2);

            // Try to use semantic search API if available
            try {
                const response = await fetch('/api/search/semantic', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        query: text1,
                        limit: 1,
                        threshold: 0.0
                    })
                });

                if (response.ok) {
                    // Note: This endpoint doesn't directly compare two texts,
                    // so we fall back to Jaccard similarity
                    return sim;
                }
            } catch (e) {
                // Fall back to Jaccard
            }

            return sim;

        } catch (error) {
            console.warn('Similarity calculation failed:', error);
            return 0;
        }
    }

    /**
     * Calculate Jaccard similarity (fallback method)
     */
    static jaccardSimilarity(text1, text2) {
        const words1 = new Set(text1.toLowerCase().split(/\s+/));
        const words2 = new Set(text2.toLowerCase().split(/\s+/));

        const intersection = new Set([...words1].filter(x => words2.has(x)));
        const union = new Set([...words1, ...words2]);

        return intersection.size / union.size;
    }

    /**
     * Cluster claims using hierarchical agglomerative clustering
     */
    static clusterClaims(claims, similarityMatrix, threshold) {
        // Initialize each claim as its own cluster
        const clusters = claims.map((claim, i) => ({
            claims: [claim],
            indices: [i],
            avgSimilarity: 1.0
        }));

        // Iteratively merge most similar clusters
        while (true) {
            let maxSim = threshold;
            let mergeI = -1;
            let mergeJ = -1;

            // Find most similar cluster pair
            for (let i = 0; i < clusters.length; i++) {
                for (let j = i + 1; j < clusters.length; j++) {
                    const sim = this.clusterSimilarity(
                        clusters[i],
                        clusters[j],
                        similarityMatrix
                    );

                    if (sim > maxSim) {
                        maxSim = sim;
                        mergeI = i;
                        mergeJ = j;
                    }
                }
            }

            // Stop if no similar pairs found
            if (mergeI === -1) break;

            // Merge clusters
            clusters[mergeI].claims.push(...clusters[mergeJ].claims);
            clusters[mergeI].indices.push(...clusters[mergeJ].indices);
            clusters[mergeI].avgSimilarity = maxSim;
            clusters.splice(mergeJ, 1);
        }

        return clusters;
    }

    /**
     * Calculate similarity between two clusters (average linkage)
     */
    static clusterSimilarity(cluster1, cluster2, similarityMatrix) {
        let totalSim = 0;
        let count = 0;

        cluster1.indices.forEach(i => {
            cluster2.indices.forEach(j => {
                totalSim += similarityMatrix[i][j];
                count++;
            });
        });

        return count > 0 ? totalSim / count : 0;
    }

    /**
     * Determine claim type based on cluster composition
     */
    static determineClaimType(claimsInCluster) {
        const uniqueDocIds = new Set(claimsInCluster.map(c => c.docId));

        // Unique: Only in one document
        if (uniqueDocIds.size === 1) {
            return 'unique';
        }

        // Shared: Present in all documents being compared
        if (uniqueDocIds.size === this.documents.length) {
            return 'shared';
        }

        // Similar: Present in some but not all documents
        return 'similar';
    }

    /**
     * Draw connection lines between aligned claims
     */
    static drawConnectionLines() {
        // Remove existing SVG if present
        let svg = document.getElementById('connection-lines-svg');
        if (svg) {
            svg.remove();
        }

        // Create new SVG overlay
        svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.id = 'connection-lines-svg';
        svg.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 10;
        `;

        const container = document.getElementById('document-panels');
        container.style.position = 'relative';
        container.appendChild(svg);

        // Draw lines for aligned claims
        this.alignedClaims.forEach(group => {
            if (group.claims.length < 2) return;

            // Get elements for each claim in group
            const elements = group.claims.map(claim =>
                document.querySelector(`[data-claim-id="${claim.id}"]`)
            ).filter(el => el !== null);

            // Draw lines between consecutive elements
            for (let i = 0; i < elements.length - 1; i++) {
                this.drawLine(svg, elements[i], elements[i + 1], group.type);
            }
        });
    }

    /**
     * Draw a connecting line between two claim elements
     */
    static drawLine(svg, el1, el2, type) {
        const rect1 = el1.getBoundingClientRect();
        const rect2 = el2.getBoundingClientRect();
        const containerRect = svg.parentElement.getBoundingClientRect();

        const x1 = rect1.right - containerRect.left;
        const y1 = rect1.top + rect1.height / 2 - containerRect.top;
        const x2 = rect2.left - containerRect.left;
        const y2 = rect2.top + rect2.height / 2 - containerRect.top;

        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', x1);
        line.setAttribute('y1', y1);
        line.setAttribute('x2', x2);
        line.setAttribute('y2', y2);

        // Color based on type
        const colors = {
            shared: '#4CAF50',
            similar: '#2196F3',
            unique: '#FF9800'
        };

        line.setAttribute('stroke', colors[type] || '#999');
        line.setAttribute('stroke-width', '2');
        line.setAttribute('stroke-dasharray', '5,5');
        line.setAttribute('opacity', '0.5');

        svg.appendChild(line);
    }

    /**
     * Analyze consensus across documents
     */
    static async analyzeConsensus() {
        if (this.documents.length < 2) {
            this.showError('Need at least 2 documents to analyze consensus');
            return;
        }

        if (this.alignedClaims.length === 0) {
            await this.alignClaims();
        }

        try {
            this.showProgress('Analyzing consensus...');

            const consensus = {
                agreements: [],
                disagreements: [],
                partialAgreements: [],
                uniquePositions: [],
                overallConsensus: 0
            };

            this.alignedClaims.forEach(group => {
                const docCount = new Set(group.claims.map(c => c.docId)).size;

                if (docCount === this.documents.length) {
                    // All documents agree
                    consensus.agreements.push({
                        claim: group.claims[0].text,
                        confidence: this.calculateGroupConfidence(group.claims),
                        support: 'unanimous',
                        sources: group.claims.map(c => c.docTitle)
                    });
                } else if (docCount > 1) {
                    // Partial agreement
                    if (this.areClaimsContradicting(group.claims)) {
                        consensus.disagreements.push({
                            claim: group.claims[0].text,
                            variants: group.claims.map(c => ({
                                text: c.text,
                                source: c.docTitle,
                                confidence: c.confidence
                            })),
                            type: 'contradiction'
                        });
                    } else {
                        consensus.partialAgreements.push({
                            claim: group.claims[0].text,
                            support: `${docCount}/${this.documents.length} documents`,
                            supportingDocs: group.claims.map(c => c.docTitle),
                            confidence: this.calculateGroupConfidence(group.claims)
                        });
                    }
                } else {
                    // Unique to one document
                    consensus.uniquePositions.push({
                        claim: group.claims[0].text,
                        source: group.claims[0].docTitle,
                        confidence: group.claims[0].confidence
                    });
                }
            });

            // Calculate overall consensus score
            const total = this.alignedClaims.length;
            const agreed = consensus.agreements.length;
            const partial = consensus.partialAgreements.length;

            consensus.overallConsensus = total > 0
                ? ((agreed * 1.0) + (partial * 0.5)) / total
                : 0;

            this.consensusData = consensus;

            // Display consensus report
            this.displayConsensusReport(consensus);

            this.hideProgress();

        } catch (error) {
            console.error('Failed to analyze consensus:', error);
            this.hideProgress();
            this.showError(`Failed to analyze consensus: ${error.message}`);
        }
    }

    /**
     * Calculate average confidence for a group of claims
     */
    static calculateGroupConfidence(claims) {
        const avgConfidence = claims.reduce((sum, c) => sum + (c.confidence || 50), 0) / claims.length;
        return Math.round(avgConfidence);
    }

    /**
     * Check if claims are contradicting
     */
    static areClaimsContradicting(claims) {
        // Simple heuristic: check for opposing keywords
        const contradictionPatterns = [
            { positive: /\b(increase|rise|grow|improve|positive)\b/i, negative: /\b(decrease|fall|decline|worsen|negative)\b/i },
            { positive: /\b(always|all|every|invariably)\b/i, negative: /\b(never|none|no|rarely)\b/i },
            { positive: /\b(true|correct|accurate|valid)\b/i, negative: /\b(false|incorrect|inaccurate|invalid)\b/i },
            { positive: /\b(support|confirm|validate)\b/i, negative: /\b(refute|contradict|reject)\b/i }
        ];

        for (let i = 0; i < claims.length; i++) {
            for (let j = i + 1; j < claims.length; j++) {
                for (const pattern of contradictionPatterns) {
                    const text1 = claims[i].text.toLowerCase();
                    const text2 = claims[j].text.toLowerCase();

                    if ((pattern.positive.test(text1) && pattern.negative.test(text2)) ||
                        (pattern.negative.test(text1) && pattern.positive.test(text2))) {
                        return true;
                    }
                }
            }
        }

        return false;
    }

    /**
     * Display consensus report in modal
     */
    static displayConsensusReport(consensus) {
        const modal = this.createConsensusModal(consensus);
        document.body.appendChild(modal);
    }

    /**
     * Create consensus modal
     */
    static createConsensusModal(consensus) {
        const modal = document.createElement('div');
        modal.className = 'consensus-modal';
        modal.innerHTML = `
            <div class="consensus-modal-content">
                <div class="consensus-header">
                    <h2>📊 Consensus Analysis</h2>
                    <button class="close-btn" onclick="this.closest('.consensus-modal').remove()">×</button>
                </div>
                <div class="consensus-body">
                    ${ConsensusAnalyzer.renderConsensusReport(consensus)}
                </div>
                <div class="consensus-footer">
                    <button onclick="this.closest('.consensus-modal').remove()">Close</button>
                </div>
            </div>
        `;

        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
        `;

        return modal;
    }

    /**
     * Export comparison report
     */
    static async exportReport() {
        if (this.documents.length === 0) {
            this.showError('No documents to export');
            return;
        }

        // Ask user for format
        const format = await this.askExportFormat();
        if (!format) return;

        try {
            this.showProgress('Generating report...');

            const report = await ComparisonReportGenerator.generateReport(
                format,
                this.documents,
                this.alignedClaims,
                this.consensusData
            );

            const filename = `comparison-report-${Date.now()}.${format}`;
            ComparisonReportGenerator.downloadReport(report, filename, this.getMimeType(format));

            this.hideProgress();
            this.showSuccess('Report exported successfully');

        } catch (error) {
            console.error('Failed to export report:', error);
            this.hideProgress();
            this.showError(`Failed to export report: ${error.message}`);
        }
    }

    /**
     * Ask user for export format
     */
    static async askExportFormat() {
        return new Promise(resolve => {
            const formats = ['markdown', 'html', 'json'];
            const choice = prompt(`Choose export format:\n${formats.join('\n')}`, 'markdown');
            resolve(formats.includes(choice) ? choice : null);
        });
    }

    /**
     * Get MIME type for format
     */
    static getMimeType(format) {
        const mimeTypes = {
            markdown: 'text/markdown',
            html: 'text/html',
            json: 'application/json'
        };
        return mimeTypes[format] || 'text/plain';
    }

    /**
     * Update statistics display
     */
    static updateStatistics() {
        const statsEl = document.getElementById('comparison-stats');
        if (!statsEl) return;

        const totalClaims = this.documents.reduce((sum, doc) => sum + doc.claims.length, 0);
        const alignedGroups = this.alignedClaims.length;

        statsEl.innerHTML = `
            <span><strong>${this.documents.length}</strong> documents</span>
            <span><strong>${totalClaims}</strong> total claims</span>
            <span><strong>${alignedGroups}</strong> aligned groups</span>
            ${this.consensusData ? `
                <span><strong>${Math.round(this.consensusData.overallConsensus * 100)}%</strong> consensus</span>
            ` : ''}
        `;
    }

    /**
     * Add another document panel
     */
    static addDocument() {
        const container = document.querySelector('.document-selector');
        const newIndex = this.documents.length + 1;

        const select = document.createElement('select');
        select.id = `doc-select-${newIndex}`;
        select.onchange = (e) => this.loadDocument(newIndex, e.target.value);

        // Populate with available documents
        this.loadAvailableDocuments();

        container.insertBefore(select, container.querySelector('button'));
    }

    /**
     * Create unified panel view
     */
    static createUnifiedPanel() {
        const panel = document.createElement('div');
        panel.className = 'unified-panel';

        let html = '<h3>Unified Comparison View</h3>';

        this.alignedClaims.forEach((group, i) => {
            html += `
                <div class="claim-group ${group.type}">
                    <div class="group-header">
                        <span class="group-number">${i + 1}</span>
                        <span class="group-type">${this.getClaimIcon(group.type)} ${group.type.toUpperCase()}</span>
                        <span class="similarity-score">${Math.round(group.similarity * 100)}% similar</span>
                    </div>
                    <div class="group-claims">
                        ${group.claims.map(claim => `
                            <div class="unified-claim">
                                <strong>[${claim.docTitle}]</strong>
                                <p>${this.escapeHtml(claim.text)}</p>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        });

        panel.innerHTML = html;
        return panel;
    }

    /**
     * Create claims-only panel view
     */
    static createClaimsOnlyPanel() {
        const panel = document.createElement('div');
        panel.className = 'claims-only-panel';

        let html = '<h3>Claims-Only View</h3>';

        // Group by document
        this.documents.forEach(doc => {
            html += `
                <div class="doc-claims-section">
                    <h4>${this.escapeHtml(doc.title)}</h4>
                    <ul class="claims-list">
                        ${doc.claims.map(claim => `
                            <li class="${this.getClaimType(claim, doc)}">
                                ${this.escapeHtml(claim.text)}
                            </li>
                        `).join('')}
                    </ul>
                </div>
            `;
        });

        panel.innerHTML = html;
        return panel;
    }

    /**
     * Utility: Escape HTML
     */
    static escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Show error message
     */
    static showError(message) {
        console.error(message);
        // TODO: Implement toast notification
        alert(`Error: ${message}`);
    }

    /**
     * Show success message
     */
    static showSuccess(message) {
        console.log(message);
        // TODO: Implement toast notification
    }

    /**
     * Show progress indicator
     */
    static showProgress(message) {
        console.log(message);
        // TODO: Implement progress indicator
    }

    /**
     * Hide progress indicator
     */
    static hideProgress() {
        // TODO: Implement
    }
}

// Initialize event listeners when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // View mode buttons
    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            ComparisonTool.viewMode = e.target.dataset.mode;
            ComparisonTool.renderPanels();
        });
    });

    // Comparison options checkboxes
    document.getElementById('show-unique')?.addEventListener('change', (e) => {
        ComparisonTool.options.showUnique = e.target.checked;
        ComparisonTool.renderPanels();
    });

    document.getElementById('show-shared')?.addEventListener('change', (e) => {
        ComparisonTool.options.showShared = e.target.checked;
        ComparisonTool.renderPanels();
    });

    document.getElementById('show-similar')?.addEventListener('change', (e) => {
        ComparisonTool.options.showSimilar = e.target.checked;
        ComparisonTool.renderPanels();
    });

    document.getElementById('align-claims')?.addEventListener('change', (e) => {
        ComparisonTool.options.alignClaims = e.target.checked;
        if (e.target.checked && ComparisonTool.documents.length >= 2) {
            ComparisonTool.alignClaims();
        }
    });
});
