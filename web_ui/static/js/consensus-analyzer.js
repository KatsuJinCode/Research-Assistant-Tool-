/**
 * Consensus Analyzer
 *
 * Analyzes consensus and disagreements across multiple documents
 * Identifies:
 * - Unanimous agreements
 * - Partial agreements
 * - Contradictions
 * - Unique positions
 */

class ConsensusAnalyzer {
    /**
     * Analyze consensus across aligned claim groups
     */
    static analyze(documents, alignedClaims) {
        const consensus = {
            agreements: [],
            disagreements: [],
            partialAgreements: [],
            uniquePositions: [],
            overallConsensus: 0,
            metadata: {
                documentCount: documents.length,
                totalClaimGroups: alignedClaims.length,
                analyzedAt: new Date().toISOString()
            }
        };

        alignedClaims.forEach(group => {
            const docCount = new Set(group.claims.map(c => c.docId)).size;

            if (docCount === documents.length) {
                // All documents agree
                this.addAgreement(consensus, group, documents);
            } else if (docCount > 1) {
                // Partial agreement or disagreement
                if (this.areClaimsContradicting(group.claims)) {
                    this.addDisagreement(consensus, group, documents);
                } else {
                    this.addPartialAgreement(consensus, group, documents);
                }
            } else {
                // Unique to one document
                this.addUniquePosition(consensus, group);
            }
        });

        // Calculate overall consensus score
        consensus.overallConsensus = this.calculateOverallConsensus(consensus, alignedClaims.length);

        // Calculate additional metrics
        consensus.metrics = this.calculateMetrics(consensus);

        return consensus;
    }

    /**
     * Add an agreement to consensus
     */
    static addAgreement(consensus, group, documents) {
        consensus.agreements.push({
            claim: group.claims[0].text,
            confidence: this.calculateGroupConfidence(group.claims),
            support: 'unanimous',
            sources: group.claims.map(c => c.docTitle || c.source),
            sourceIds: group.claims.map(c => c.docId),
            claimIds: group.claims.map(c => c.id),
            similarity: group.similarity || 1.0,
            variants: this.extractVariants(group.claims)
        });
    }

    /**
     * Add a disagreement to consensus
     */
    static addDisagreement(consensus, group, documents) {
        const contradictionType = this.identifyContradictionType(group.claims);

        consensus.disagreements.push({
            topic: this.extractTopic(group.claims),
            claim: group.claims[0].text,
            contradictionType: contradictionType,
            variants: group.claims.map(c => ({
                text: c.text,
                source: c.docTitle || c.source,
                sourceId: c.docId,
                claimId: c.id,
                confidence: c.confidence || 50
            })),
            supportDistribution: this.calculateSupportDistribution(group.claims, documents),
            severity: this.assessContradictionSeverity(group.claims)
        });
    }

    /**
     * Add a partial agreement to consensus
     */
    static addPartialAgreement(consensus, group, documents) {
        const docCount = new Set(group.claims.map(c => c.docId)).size;

        consensus.partialAgreements.push({
            claim: group.claims[0].text,
            support: `${docCount}/${documents.length} documents`,
            supportRatio: docCount / documents.length,
            supportingDocs: group.claims.map(c => c.docTitle || c.source),
            supportingDocIds: group.claims.map(c => c.docId),
            confidence: this.calculateGroupConfidence(group.claims),
            missingSources: this.findMissingSources(group.claims, documents),
            claimIds: group.claims.map(c => c.id)
        });
    }

    /**
     * Add a unique position to consensus
     */
    static addUniquePosition(consensus, group) {
        const claim = group.claims[0];

        consensus.uniquePositions.push({
            claim: claim.text,
            source: claim.docTitle || claim.source,
            sourceId: claim.docId,
            claimId: claim.id,
            confidence: claim.confidence || 50,
            significance: this.assessSignificance(claim)
        });
    }

    /**
     * Calculate overall consensus score
     */
    static calculateOverallConsensus(consensus, totalGroups) {
        if (totalGroups === 0) return 0;

        const agreed = consensus.agreements.length;
        const partial = consensus.partialAgreements.length;
        const disagreed = consensus.disagreements.length;

        // Weighted scoring:
        // - Full agreements: 1.0
        // - Partial agreements: 0.5
        // - Disagreements: -0.5 (penalize)
        // - Unique: 0.0 (neutral)

        const score = (
            (agreed * 1.0) +
            (partial * 0.5) +
            (disagreed * -0.5)
        ) / totalGroups;

        // Normalize to 0-1 range
        return Math.max(0, Math.min(1, (score + 0.5) / 1.5));
    }

    /**
     * Calculate group confidence (average)
     */
    static calculateGroupConfidence(claims) {
        if (claims.length === 0) return 0;
        const avgConfidence = claims.reduce((sum, c) => sum + (c.confidence || 50), 0) / claims.length;
        return Math.round(avgConfidence);
    }

    /**
     * Check if claims are contradicting
     */
    static areClaimsContradicting(claims) {
        if (claims.length < 2) return false;

        // Multiple strategies for detecting contradictions

        // 1. Keyword-based detection
        if (this.hasOpposingKeywords(claims)) return true;

        // 2. Sentiment-based detection
        if (this.hasOpposingSentiment(claims)) return true;

        // 3. Quantitative contradiction
        if (this.hasQuantitativeContradiction(claims)) return true;

        return false;
    }

    /**
     * Check for opposing keywords
     */
    static hasOpposingKeywords(claims) {
        const contradictionPatterns = [
            {
                positive: /\b(increase|rise|grow|improve|higher|more|positive|support|confirm|yes|true|valid)\b/i,
                negative: /\b(decrease|fall|decline|worsen|lower|less|negative|refute|contradict|no|false|invalid)\b/i
            },
            {
                positive: /\b(always|all|every|invariably|consistently|universal)\b/i,
                negative: /\b(never|none|no|rarely|seldom|exceptional)\b/i
            },
            {
                positive: /\b(effective|successful|beneficial|advantageous)\b/i,
                negative: /\b(ineffective|unsuccessful|harmful|detrimental)\b/i
            },
            {
                positive: /\b(safe|secure|stable|reliable)\b/i,
                negative: /\b(unsafe|insecure|unstable|unreliable)\b/i
            }
        ];

        for (let i = 0; i < claims.length; i++) {
            for (let j = i + 1; j < claims.length; j++) {
                const text1 = claims[i].text.toLowerCase();
                const text2 = claims[j].text.toLowerCase();

                for (const pattern of contradictionPatterns) {
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
     * Check for opposing sentiment
     */
    static hasOpposingSentiment(claims) {
        const sentiments = claims.map(c => this.analyzeSentiment(c.text));

        // Check if sentiments are opposed
        for (let i = 0; i < sentiments.length; i++) {
            for (let j = i + 1; j < sentiments.length; j++) {
                if (Math.abs(sentiments[i] - sentiments[j]) > 0.6) {
                    return true;
                }
            }
        }

        return false;
    }

    /**
     * Simple sentiment analysis (-1 to 1)
     */
    static analyzeSentiment(text) {
        const positiveWords = ['good', 'great', 'excellent', 'positive', 'beneficial', 'effective', 'successful'];
        const negativeWords = ['bad', 'poor', 'negative', 'harmful', 'ineffective', 'unsuccessful'];

        const words = text.toLowerCase().split(/\s+/);
        let score = 0;

        words.forEach(word => {
            if (positiveWords.includes(word)) score += 1;
            if (negativeWords.includes(word)) score -= 1;
        });

        return score / Math.max(1, words.length);
    }

    /**
     * Check for quantitative contradictions
     */
    static hasQuantitativeContradiction(claims) {
        // Extract numbers from each claim
        const numberPattern = /(\d+(?:\.\d+)?)\s*(%|percent|degrees?|years?)/gi;

        const claimNumbers = claims.map(c => {
            const matches = [...c.text.matchAll(numberPattern)];
            return matches.map(m => ({
                value: parseFloat(m[1]),
                unit: m[2],
                context: c.text
            }));
        });

        // Compare numbers with same units
        for (let i = 0; i < claimNumbers.length; i++) {
            for (let j = i + 1; j < claimNumbers.length; j++) {
                for (const num1 of claimNumbers[i]) {
                    for (const num2 of claimNumbers[j]) {
                        if (num1.unit.toLowerCase() === num2.unit.toLowerCase()) {
                            // If numbers differ significantly, might be contradiction
                            const diff = Math.abs(num1.value - num2.value) / Math.max(num1.value, num2.value);
                            if (diff > 0.2) { // 20% difference threshold
                                return true;
                            }
                        }
                    }
                }
            }
        }

        return false;
    }

    /**
     * Identify type of contradiction
     */
    static identifyContradictionType(claims) {
        if (this.hasQuantitativeContradiction(claims)) return 'quantitative';
        if (this.hasOpposingKeywords(claims)) return 'semantic';
        if (this.hasOpposingSentiment(claims)) return 'sentiment';
        return 'general';
    }

    /**
     * Extract common topic from claims
     */
    static extractTopic(claims) {
        // Simple: use most common non-stopword
        const stopwords = new Set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'are', 'was', 'were']);

        const wordFreq = {};
        claims.forEach(c => {
            const words = c.text.toLowerCase().split(/\s+/);
            words.forEach(word => {
                const cleaned = word.replace(/[^a-z]/g, '');
                if (cleaned.length > 3 && !stopwords.has(cleaned)) {
                    wordFreq[cleaned] = (wordFreq[cleaned] || 0) + 1;
                }
            });
        });

        const topWord = Object.entries(wordFreq)
            .sort((a, b) => b[1] - a[1])[0];

        return topWord ? topWord[0] : 'general';
    }

    /**
     * Calculate support distribution
     */
    static calculateSupportDistribution(claims, documents) {
        const distribution = {};

        claims.forEach(c => {
            const source = c.docTitle || c.source;
            if (!distribution[source]) {
                distribution[source] = {
                    count: 0,
                    position: c.text,
                    confidence: c.confidence || 50
                };
            }
            distribution[source].count++;
        });

        return distribution;
    }

    /**
     * Assess contradiction severity
     */
    static assessContradictionSeverity(claims) {
        // Based on multiple factors:
        // 1. Confidence levels
        // 2. Number of contradicting sources
        // 3. Degree of opposition

        const avgConfidence = this.calculateGroupConfidence(claims);
        const sourceCount = new Set(claims.map(c => c.docId)).size;

        let severity = 0;

        // Higher confidence = more severe
        severity += avgConfidence / 100;

        // More sources = more severe
        severity += sourceCount / 10;

        // Check degree of opposition
        if (this.hasQuantitativeContradiction(claims)) {
            severity += 0.5;
        }

        return Math.min(1, severity); // Normalize to 0-1
    }

    /**
     * Find sources that don't support a claim
     */
    static findMissingSources(claims, documents) {
        const supportingSources = new Set(claims.map(c => c.docId));
        const allSources = documents.map(d => d.id);

        return allSources.filter(id => !supportingSources.has(id))
            .map(id => {
                const doc = documents.find(d => d.id === id);
                return doc ? doc.title : id;
            });
    }

    /**
     * Assess significance of unique claim
     */
    static assessSignificance(claim) {
        // Simple heuristic based on:
        // 1. Length (longer = more detailed)
        // 2. Confidence
        // 3. Presence of specific keywords

        let score = 0;

        // Length factor
        const wordCount = claim.text.split(/\s+/).length;
        score += Math.min(0.3, wordCount / 100);

        // Confidence factor
        score += (claim.confidence || 50) / 200;

        // Keyword factor
        const significantKeywords = [
            'significant', 'important', 'crucial', 'critical', 'essential',
            'novel', 'new', 'unique', 'unprecedented', 'breakthrough'
        ];

        if (significantKeywords.some(kw => claim.text.toLowerCase().includes(kw))) {
            score += 0.3;
        }

        return Math.min(1, score);
    }

    /**
     * Extract textual variants
     */
    static extractVariants(claims) {
        // Group similar but not identical texts
        const uniqueTexts = [...new Set(claims.map(c => c.text))];

        if (uniqueTexts.length === 1) return null;

        return uniqueTexts.map(text => ({
            text: text,
            sources: claims.filter(c => c.text === text)
                .map(c => c.docTitle || c.source)
        }));
    }

    /**
     * Calculate additional metrics
     */
    static calculateMetrics(consensus) {
        const total = consensus.agreements.length +
            consensus.disagreements.length +
            consensus.partialAgreements.length +
            consensus.uniquePositions.length;

        return {
            agreementRate: total > 0 ? consensus.agreements.length / total : 0,
            disagreementRate: total > 0 ? consensus.disagreements.length / total : 0,
            partialAgreementRate: total > 0 ? consensus.partialAgreements.length / total : 0,
            uniqueRate: total > 0 ? consensus.uniquePositions.length / total : 0,
            totalItems: total,
            avgConfidence: this.calculateAverageConfidence(consensus)
        };
    }

    /**
     * Calculate average confidence across all items
     */
    static calculateAverageConfidence(consensus) {
        let totalConfidence = 0;
        let count = 0;

        consensus.agreements.forEach(a => {
            totalConfidence += a.confidence;
            count++;
        });

        consensus.partialAgreements.forEach(p => {
            totalConfidence += p.confidence;
            count++;
        });

        consensus.uniquePositions.forEach(u => {
            totalConfidence += u.confidence;
            count++;
        });

        return count > 0 ? Math.round(totalConfidence / count) : 0;
    }

    /**
     * Render consensus report as HTML
     */
    static renderConsensusReport(consensus) {
        return `
            <div class="consensus-report">
                ${this.renderConsensusScore(consensus)}
                ${this.renderMetrics(consensus)}
                ${this.renderBreakdown(consensus)}
            </div>
        `;
    }

    /**
     * Render consensus score section
     */
    static renderConsensusScore(consensus) {
        const score = Math.round(consensus.overallConsensus * 100);
        const color = this.getConsensusColor(consensus.overallConsensus);

        return `
            <div class="consensus-score-section">
                <h3>Overall Consensus Score</h3>
                <div class="score-display">
                    <div class="score-circle" style="background: ${color}">
                        <span class="score-number">${score}%</span>
                    </div>
                    <div class="score-description">
                        ${this.getConsensusDescription(consensus.overallConsensus)}
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Get color for consensus score
     */
    static getConsensusColor(score) {
        if (score >= 0.8) return '#4CAF50'; // Green
        if (score >= 0.6) return '#8BC34A'; // Light green
        if (score >= 0.4) return '#FFC107'; // Yellow
        if (score >= 0.2) return '#FF9800'; // Orange
        return '#F44336'; // Red
    }

    /**
     * Get description for consensus level
     */
    static getConsensusDescription(score) {
        if (score >= 0.8) return 'Strong consensus - documents largely agree';
        if (score >= 0.6) return 'Moderate consensus - substantial agreement with some differences';
        if (score >= 0.4) return 'Weak consensus - mixed agreement and disagreement';
        if (score >= 0.2) return 'Low consensus - significant disagreements';
        return 'No consensus - documents largely contradict';
    }

    /**
     * Render metrics section
     */
    static renderMetrics(consensus) {
        const m = consensus.metrics;

        return `
            <div class="consensus-metrics">
                <div class="metric-card">
                    <div class="metric-value">${Math.round(m.agreementRate * 100)}%</div>
                    <div class="metric-label">Agreement Rate</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${Math.round(m.disagreementRate * 100)}%</div>
                    <div class="metric-label">Disagreement Rate</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${Math.round(m.partialAgreementRate * 100)}%</div>
                    <div class="metric-label">Partial Agreement</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${m.avgConfidence}%</div>
                    <div class="metric-label">Avg Confidence</div>
                </div>
            </div>
        `;
    }

    /**
     * Render breakdown section
     */
    static renderBreakdown(consensus) {
        return `
            <div class="consensus-breakdown">
                ${this.renderAgreements(consensus.agreements)}
                ${this.renderDisagreements(consensus.disagreements)}
                ${this.renderPartialAgreements(consensus.partialAgreements)}
                ${this.renderUniquePositions(consensus.uniquePositions)}
            </div>
        `;
    }

    /**
     * Render agreements section
     */
    static renderAgreements(agreements) {
        if (agreements.length === 0) return '';

        return `
            <div class="agreement-section">
                <h4>✓ Agreements (${agreements.length})</h4>
                <ul class="consensus-list">
                    ${agreements.map((a, i) => `
                        <li class="consensus-item agreement">
                            <div class="item-header">
                                <span class="item-number">${i + 1}</span>
                                <span class="confidence-badge">${a.confidence}% confidence</span>
                            </div>
                            <div class="item-content">${this.escapeHtml(a.claim)}</div>
                            <div class="item-sources">
                                Sources: ${a.sources.join(', ')}
                            </div>
                        </li>
                    `).join('')}
                </ul>
            </div>
        `;
    }

    /**
     * Render disagreements section
     */
    static renderDisagreements(disagreements) {
        if (disagreements.length === 0) return '';

        return `
            <div class="disagreement-section">
                <h4>⚠ Disagreements (${disagreements.length})</h4>
                <ul class="consensus-list">
                    ${disagreements.map((d, i) => `
                        <li class="consensus-item disagreement">
                            <div class="item-header">
                                <span class="item-number">${i + 1}</span>
                                <span class="type-badge">${d.contradictionType}</span>
                                <span class="severity-badge">${this.formatSeverity(d.severity)}</span>
                            </div>
                            <div class="item-content">Topic: ${this.escapeHtml(d.topic)}</div>
                            <ul class="variant-list">
                                ${d.variants.map(v => `
                                    <li class="variant-item">
                                        <strong>[${this.escapeHtml(v.source)}]:</strong>
                                        "${this.escapeHtml(v.text)}"
                                        <span class="confidence-badge">${v.confidence}%</span>
                                    </li>
                                `).join('')}
                            </ul>
                        </li>
                    `).join('')}
                </ul>
            </div>
        `;
    }

    /**
     * Render partial agreements section
     */
    static renderPartialAgreements(partialAgreements) {
        if (partialAgreements.length === 0) return '';

        return `
            <div class="partial-section">
                <h4>≈ Partial Agreements (${partialAgreements.length})</h4>
                <ul class="consensus-list">
                    ${partialAgreements.map((p, i) => `
                        <li class="consensus-item partial">
                            <div class="item-header">
                                <span class="item-number">${i + 1}</span>
                                <span class="support-badge">${p.support}</span>
                                <span class="confidence-badge">${p.confidence}% confidence</span>
                            </div>
                            <div class="item-content">${this.escapeHtml(p.claim)}</div>
                            <div class="item-sources">
                                Supporting: ${p.supportingDocs.join(', ')}
                                ${p.missingSources.length > 0 ? `
                                    <br>Missing: ${p.missingSources.join(', ')}
                                ` : ''}
                            </div>
                        </li>
                    `).join('')}
                </ul>
            </div>
        `;
    }

    /**
     * Render unique positions section
     */
    static renderUniquePositions(uniquePositions) {
        if (uniquePositions.length === 0) return '';

        return `
            <div class="unique-section">
                <h4>⭐ Unique Positions (${uniquePositions.length})</h4>
                <ul class="consensus-list">
                    ${uniquePositions.map((u, i) => `
                        <li class="consensus-item unique">
                            <div class="item-header">
                                <span class="item-number">${i + 1}</span>
                                <span class="source-badge">${this.escapeHtml(u.source)}</span>
                                <span class="confidence-badge">${u.confidence}% confidence</span>
                            </div>
                            <div class="item-content">${this.escapeHtml(u.claim)}</div>
                        </li>
                    `).join('')}
                </ul>
            </div>
        `;
    }

    /**
     * Format severity level
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
    module.exports = ConsensusAnalyzer;
}
