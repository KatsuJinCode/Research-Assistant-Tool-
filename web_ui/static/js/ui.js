/**
 * UI Module - User interface interactions and components
 */

const UI = {
    /**
     * Show claim details in modal with visual metrics dashboard
     */
    async showClaimDetails(claimId) {
        try {
            console.log('🔍 Fetching details for claim:', claimId);
            const claim = await API.fetchClaim(claimId);
            console.log('✓ Claim data loaded:', claim);

            // Use the sidebar detail panel, not a modal
            const detailPanel = document.getElementById('detail-panel');
            const detailTitle = document.getElementById('detail-claim-text');

            // Calculate metrics that drive visual encoding
            const hasRealConfidence = claim.confidence !== undefined && claim.confidence !== null;
            const confidence = hasRealConfidence ? claim.confidence : (claim.quality_score || null);
            const childCount = claim.children ? claim.children.length : 0;
            const evidenceCount = claim.evidence ? claim.evidence.length : 0;
            const supportingEvidence = claim.evidence ? claim.evidence.filter(e => e.type === 'SUPPORTS').length : 0;
            const contradictingEvidence = claim.evidence ? claim.evidence.filter(e => e.type === 'CONTRADICTS').length : 0;
            const hasRealSpecificity = claim.specificity !== undefined && claim.specificity !== null;
            const specificity = hasRealSpecificity ? claim.specificity : null;
            const hasRealStrength = claim.strength !== undefined && claim.strength !== null;
            const strength = hasRealStrength ? claim.strength : null;

            // Pre-calculate formatted values
            const nodeSize = this.calculateNodeSize(childCount);
            const specificityLabel = specificity !== null ? this.getSpecificityLabel(specificity) : 'Not analyzed';

            // Get real values from claim data
            const qualityScore = claim.quality_score || 0;
            const timestamp = claim.created_at || claim.timestamp || null;
            const formattedTime = timestamp ? new Date(timestamp).toLocaleString() : null;
            const investigationValue = claim.investigation_priority || claim.investigation_value || null;

            // Build clean detail panel
            let detailsHTML = `
                <div style="margin-bottom: 12px;">
                    <!-- Summary (only shown once, at top) -->
                    <h3 style="margin-bottom: 10px; line-height: 1.3; font-size: 16px;">${claim.summary || claim.text || 'Claim'}</h3>

                    <!-- Metrics Dashboard (User-Friendly) -->
                    <div style="background: #f5f5f5; padding: 8px; border-radius: 6px; margin-bottom: 10px;">
                        <h4 style="margin-top: 0; margin-bottom: 8px; color: #555; font-size: 13px;">Assessment</h4>

                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px;">
                            <!-- Confidence -->
                            <div style="background: white; padding: 8px; border-radius: 4px; border-left: 3px solid #2196F3;">
                                <div style="font-size: 10px; color: #666; text-transform: uppercase; margin-bottom: 3px;">Confidence</div>
                                <div style="font-size: 18px; font-weight: bold; color: ${confidence !== null ? '#333' : '#999'};">
                                    ${confidence !== null ? (confidence * 100).toFixed(0) + '%' : '<span style="font-size: 14px;">Not yet assessed</span>'}
                                </div>
                                <div style="font-size: 9px; color: #888; margin-top: 2px;">
                                    ${confidence !== null ? 'How certain the AI is' : '→ Upload document to assess'}
                                </div>
                                <button class="override-toggle-btn" data-field="confidence" style="margin-top: 6px; font-size: 9px; color: #2196F3; background: none; border: none; cursor: pointer; padding: 0; text-align: left;">✎ Adjust</button>
                                <div class="override-controls" data-field="confidence" style="display: none; margin-top: 6px; padding-top: 6px; border-top: 1px solid #eee;">
                                    <input type="range" class="override-slider" data-field="confidence" min="0" max="100" value="${confidence !== null ? (confidence * 100).toFixed(0) : 50}" style="width: 100%; height: 4px;">
                                    <div style="display: flex; justify-content: space-between; margin-top: 3px;">
                                        <button class="apply-override-btn" data-field="confidence" style="flex: 1; background: #2196F3; color: white; border: none; padding: 4px; font-size: 9px; border-radius: 3px; cursor: pointer; margin-right: 3px;">Apply</button>
                                        <button class="reset-override-btn" data-field="confidence" style="flex: 1; background: #999; color: white; border: none; padding: 4px; font-size: 9px; border-radius: 3px; cursor: pointer; display: none;">Reset</button>
                                    </div>
                                </div>
                            </div>

                            <!-- Quality Score -->
                            <div style="background: white; padding: 8px; border-radius: 4px; border-left: 3px solid #4CAF50;">
                                <div style="font-size: 10px; color: #666; text-transform: uppercase; margin-bottom: 3px;">Quality Score</div>
                                <div style="font-size: 18px; font-weight: bold; color: ${qualityScore > 0 ? '#333' : '#999'};">
                                    ${qualityScore > 0 ? (qualityScore * 100).toFixed(0) + '%' : '<span style="font-size: 14px;">Not yet assessed</span>'}
                                </div>
                                <div style="font-size: 9px; color: #888; margin-top: 2px;">
                                    ${qualityScore > 0 ? 'Overall quality rating' : '→ Upload document to assess'}
                                </div>
                                <button class="override-toggle-btn" data-field="quality-score" style="margin-top: 6px; font-size: 9px; color: #4CAF50; background: none; border: none; cursor: pointer; padding: 0; text-align: left;">✎ Adjust</button>
                                <div class="override-controls" data-field="quality-score" style="display: none; margin-top: 6px; padding-top: 6px; border-top: 1px solid #eee;">
                                    <input type="range" class="override-slider" data-field="quality-score" min="0" max="100" value="${qualityScore > 0 ? (qualityScore * 100).toFixed(0) : 50}" style="width: 100%; height: 4px;">
                                    <div style="display: flex; justify-content: space-between; margin-top: 3px;">
                                        <button class="apply-override-btn" data-field="quality-score" style="flex: 1; background: #4CAF50; color: white; border: none; padding: 4px; font-size: 9px; border-radius: 3px; cursor: pointer; margin-right: 3px;">Apply</button>
                                        <button class="reset-override-btn" data-field="quality-score" style="flex: 1; background: #999; color: white; border: none; padding: 4px; font-size: 9px; border-radius: 3px; cursor: pointer; display: none;">Reset</button>
                                    </div>
                                </div>
                            </div>

                            <!-- Specificity -->
                            <div style="background: white; padding: 8px; border-radius: 4px; border-left: 3px solid #9C27B0;">
                                <div style="font-size: 10px; color: #666; text-transform: uppercase; margin-bottom: 3px;">Specificity</div>
                                <div style="font-size: 18px; font-weight: bold; color: ${specificity !== null ? '#333' : '#999'};">
                                    ${specificity !== null ? (specificity * 100).toFixed(0) + '%' : '<span style="font-size: 14px;">Not analyzed</span>'}
                                </div>
                                <div style="font-size: 9px; color: #888; margin-top: 2px;">
                                    ${specificity !== null ? 'How specific vs general' : '→ Run analysis to calculate'}
                                </div>
                                <button class="override-toggle-btn" data-field="specificity" style="margin-top: 6px; font-size: 9px; color: #9C27B0; background: none; border: none; cursor: pointer; padding: 0; text-align: left;">✎ Adjust</button>
                                <div class="override-controls" data-field="specificity" style="display: none; margin-top: 6px; padding-top: 6px; border-top: 1px solid #eee;">
                                    <input type="range" class="override-slider" data-field="specificity" min="0" max="100" value="${specificity !== null ? (specificity * 100).toFixed(0) : 50}" style="width: 100%; height: 4px;">
                                    <div style="display: flex; justify-content: space-between; margin-top: 3px;">
                                        <button class="apply-override-btn" data-field="specificity" style="flex: 1; background: #9C27B0; color: white; border: none; padding: 4px; font-size: 9px; border-radius: 3px; cursor: pointer; margin-right: 3px;">Apply</button>
                                        <button class="reset-override-btn" data-field="specificity" style="flex: 1; background: #999; color: white; border: none; padding: 4px; font-size: 9px; border-radius: 3px; cursor: pointer; display: none;">Reset</button>
                                    </div>
                                </div>
                            </div>

                            <!-- Strength -->
                            <div style="background: white; padding: 8px; border-radius: 4px; border-left: 3px solid #FF9800;">
                                <div style="font-size: 10px; color: #666; text-transform: uppercase; margin-bottom: 3px;">Strength</div>
                                <div style="font-size: 18px; font-weight: bold; color: ${strength !== null ? '#333' : '#999'};">
                                    ${strength !== null ? (strength * 100).toFixed(0) + '%' : '<span style="font-size: 14px;">Not analyzed</span>'}
                                </div>
                                <div style="font-size: 9px; color: #888; margin-top: 2px;">
                                    ${strength !== null ? 'Claim assertiveness' : '→ Run analysis to calculate'}
                                </div>
                                <button class="override-toggle-btn" data-field="strength" style="margin-top: 6px; font-size: 9px; color: #FF9800; background: none; border: none; cursor: pointer; padding: 0; text-align: left;">✎ Adjust</button>
                                <div class="override-controls" data-field="strength" style="display: none; margin-top: 6px; padding-top: 6px; border-top: 1px solid #eee;">
                                    <input type="range" class="override-slider" data-field="strength" min="0" max="100" value="${strength !== null ? (strength * 100).toFixed(0) : 50}" style="width: 100%; height: 4px;">
                                    <div style="display: flex; justify-content: space-between; margin-top: 3px;">
                                        <button class="apply-override-btn" data-field="strength" style="flex: 1; background: #FF9800; color: white; border: none; padding: 4px; font-size: 9px; border-radius: 3px; cursor: pointer; margin-right: 3px;">Apply</button>
                                        <button class="reset-override-btn" data-field="strength" style="flex: 1; background: #999; color: white; border: none; padding: 4px; font-size: 9px; border-radius: 3px; cursor: pointer; display: none;">Reset</button>
                                    </div>
                                </div>
                            </div>

                            <!-- Sub-Claims -->
                            <div style="background: white; padding: 8px; border-radius: 4px; border-left: 3px solid #3F51B5;">
                                <div style="font-size: 10px; color: #666; text-transform: uppercase; margin-bottom: 3px;">Sub-Claims</div>
                                <div style="font-size: 18px; font-weight: bold; color: #333;">${childCount}</div>
                                <div style="font-size: 9px; color: #888; margin-top: 2px;">
                                    More specific derived claims
                                </div>
                            </div>

                            <!-- Evidence -->
                            <div style="background: white; padding: 8px; border-radius: 4px; border-left: 3px solid #00BCD4;">
                                <div style="font-size: 10px; color: #666; text-transform: uppercase; margin-bottom: 3px;">Evidence</div>
                                <div style="font-size: 18px; font-weight: bold; color: #333;">${evidenceCount}</div>
                                <div style="font-size: 9px; color: #888; margin-top: 2px;">
                                    <span style="color: #4CAF50;">✓${supportingEvidence}</span> / <span style="color: #F44336;">✗${contradictingEvidence}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Full Original Text -->
                    ${claim.text ? `
                        <div style="background: #fff3cd; padding: 6px; border-radius: 3px; margin-bottom: 8px; border-left: 3px solid #ff9800;">
                            <strong style="color: #856404; font-size: 10px;">Full Original Text:</strong>
                            <div style="margin-top: 3px; color: #856404; font-size: 12px; line-height: 1.3;">${claim.text}</div>
                        </div>
                    ` : `
                        <div style="background: #f5f5f5; padding: 6px; border-radius: 3px; margin-bottom: 8px; border-left: 3px solid #999;">
                            <strong style="color: #666; font-size: 10px;">Full Original Text:</strong>
                            <div style="margin-top: 3px; color: #999; font-size: 11px; font-style: italic;">
                                Not available - this claim may have been derived or summarized without preserving the original text
                            </div>
                        </div>
                    `}

                    <!-- Metadata -->
                    <div style="font-size: 10px; color: #666; margin-bottom: 8px; line-height: 1.4;">
                        <div style="margin-bottom: 3px;">
                            <strong>Timestamp:</strong> ${formattedTime || '<span style="color: #999; font-style: italic;">Not recorded</span>'}
                        </div>
                        <div style="margin-bottom: 3px;">
                            <strong>Investigation Value:</strong> ${investigationValue || '<span style="color: #999; font-style: italic;">Not yet prioritized → Run investigation</span>'}
                            <button class="override-toggle-btn" data-field="investigation-value" style="margin-left: 8px; font-size: 9px; color: #FF5722; background: none; border: none; cursor: pointer; padding: 0;">✎ Adjust</button>
                            <div class="override-controls" data-field="investigation-value" style="display: none; margin-top: 6px; padding: 6px; background: #f9f9f9; border-radius: 3px;">
                                <input type="range" class="override-slider" data-field="investigation-value" min="0" max="100" value="${investigationValue ? (investigationValue * 100).toFixed(0) : 50}" style="width: 100%; height: 4px;">
                                <div style="display: flex; justify-content: space-between; margin-top: 3px;">
                                    <button class="apply-override-btn" data-field="investigation-value" style="flex: 1; background: #FF5722; color: white; border: none; padding: 4px; font-size: 9px; border-radius: 3px; cursor: pointer; margin-right: 3px;">Apply</button>
                                    <button class="reset-override-btn" data-field="investigation-value" style="flex: 1; background: #999; color: white; border: none; padding: 4px; font-size: 9px; border-radius: 3px; cursor: pointer; display: none;">Reset</button>
                                </div>
                            </div>
                        </div>
                        ${claim.disposition ? `
                            <div title="Status or categorization of this claim">
                                <strong>Status:</strong> <span style="color: #2196F3;">${claim.disposition}</span>
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;

            // Child Claims
            if (claim.children && claim.children.length > 0) {
                detailsHTML += `
                    <div style="margin-bottom: 10px;">
                        <h4 style="margin-bottom: 5px; font-size: 13px;">Child Claims (${claim.children.length})</h4>
                        <ul style="margin: 0; padding-left: 15px;">
                `;
                claim.children.forEach(child => {
                    detailsHTML += `<li style="margin-bottom: 3px; font-size: 12px;">${child.summary || child.text}</li>`;
                });
                detailsHTML += `</ul></div>`;
            }

            // Evidence Details
            if (claim.evidence && claim.evidence.length > 0) {
                detailsHTML += `
                    <div style="margin-bottom: 10px;">
                        <h4 style="margin-bottom: 5px; font-size: 13px;">Evidence (${claim.evidence.length})</h4>
                `;

                // Supporting Evidence
                const supporting = claim.evidence.filter(e => e.type === 'SUPPORTS');
                if (supporting.length > 0) {
                    detailsHTML += `
                        <div style="margin-bottom: 6px;">
                            <strong style="color: #4CAF50; font-size: 11px;">Supporting (${supporting.length}):</strong>
                            <ul style="margin: 3px 0 0 15px; padding: 0; list-style: none;">
                    `;
                    supporting.forEach(ev => {
                        detailsHTML += `
                            <li style="margin-bottom: 6px; display: flex; align-items: center; gap: 8px;">
                                <span style="flex: 1;">${ev.title || 'Unknown Evidence'}</span>
                                <button onclick="UI.removeEvidence('${claimId}', '${ev.id}', '${ev.title || 'this evidence'}')"
                                        style="background: #f44336; color: white; border: none; padding: 2px 8px; border-radius: 3px; cursor: pointer; font-size: 11px;">
                                    Remove
                                </button>
                            </li>
                        `;
                    });
                    detailsHTML += `</ul></div>`;
                }

                // Contradicting Evidence
                const contradicting = claim.evidence.filter(e => e.type === 'CONTRADICTS');
                if (contradicting.length > 0) {
                    detailsHTML += `
                        <div>
                            <strong style="color: #F44336; font-size: 11px;">Contradicting (${contradicting.length}):</strong>
                            <ul style="margin: 3px 0 0 15px; padding: 0; list-style: none;">
                    `;
                    contradicting.forEach(ev => {
                        detailsHTML += `
                            <li style="margin-bottom: 6px; display: flex; align-items: center; gap: 8px;">
                                <span style="flex: 1;">${ev.title || 'Unknown Evidence'}</span>
                                <button onclick="UI.removeEvidence('${claimId}', '${ev.id}', '${ev.title || 'this evidence'}')"
                                        style="background: #f44336; color: white; border: none; padding: 2px 8px; border-radius: 3px; cursor: pointer; font-size: 11px;">
                                    Remove
                                </button>
                            </li>
                        `;
                    });
                    detailsHTML += `</ul></div>`;
                }
                detailsHTML += `</div>`;
            }

            // Source Locations
            if (claim.sources && claim.sources.length > 0) {
                detailsHTML += `
                    <div>
                        <h4 style="margin-bottom: 8px;">Source Locations (${claim.sources.length})</h4>
                        <ul style="margin: 0; padding-left: 20px;">
                `;
                claim.sources.forEach(src => {
                    if (src.page) {
                        detailsHTML += `
                            <li style="margin-bottom: 5px; font-size: 12px;">
                                <strong>Page ${src.page}, Line ${src.line}</strong>
                                <div style="color: #666; margin-top: 2px;">${src.sentence}</div>
                            </li>
                        `;
                    }
                });
                detailsHTML += `</ul></div>`;
            }

            detailTitle.innerHTML = detailsHTML;
            detailPanel.style.display = 'block';
            detailPanel.classList.add('visible');

            // Store claim ID for override operations
            detailPanel.dataset.claimId = claimId;

            // Fetch and display provenance information
            this.fetchAndDisplayProvenance(claimId);

            // Initialize confidence override slider
            const confidenceSlider = document.getElementById('confidence-override-slider');
            const confidenceValue = document.getElementById('confidence-override-value');
            const overrideIndicator = document.getElementById('confidence-override-indicator');
            const resetBtn = document.getElementById('reset-confidence-override-btn');

            if (confidenceSlider && confidenceValue) {
                // Determine which confidence to use (user override or AI)
                const effectiveConfidence = claim.user_confidence_override !== undefined
                    ? claim.user_confidence_override
                    : confidence;

                // Set slider to current effective confidence
                const confidencePercent = Math.round(effectiveConfidence * 100);
                confidenceSlider.value = confidencePercent;
                confidenceValue.textContent = confidencePercent + '%';

                // Show override indicator if user has overridden
                if (claim.user_confidence_override !== undefined) {
                    if (overrideIndicator) overrideIndicator.style.display = 'block';
                    if (resetBtn) resetBtn.style.display = 'block';
                } else {
                    if (overrideIndicator) overrideIndicator.style.display = 'none';
                    if (resetBtn) resetBtn.style.display = 'none';
                }
            }

            console.log('✓ Detail panel shown');
        } catch (error) {
            console.error('❌ Failed to load claim details:', error);
            alert(`Failed to load claim: ${error.message}`);
        }
    },

    /**
     * Calculate visual node size description
     */
    calculateNodeSize(childCount) {
        const baseRadius = 20;
        const scaleFactor = Math.log(childCount + 1) * 3;
        const totalRadius = Math.min(baseRadius + scaleFactor, 40);
        return totalRadius.toFixed(0) + 'px radius';
    },

    /**
     * Get human-readable specificity label
     */
    getSpecificityLabel(specificity) {
        if (specificity >= 0.8) return 'Very Specific';
        if (specificity >= 0.6) return 'Specific';
        if (specificity >= 0.4) return 'Moderate';
        if (specificity >= 0.2) return 'General';
        return 'Very General';
    },

    /**
     * Show document details
     */
    showDocumentDetails(docNode) {
        const detailPanel = document.getElementById('detail-panel');
        const detailTitle = document.getElementById('detail-claim-text');

        const doc = docNode.fullData;
        const detailsHTML = `
            <div style="margin-bottom: 20px;">
                <h3 style="margin-bottom: 15px; color: #4CAF50;">📄 ${doc.title || docNode.label}</h3>

                <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                    <h4 style="margin-top: 0; margin-bottom: 12px; color: #555;">Document Information</h4>
                    <p><strong>Status:</strong> ${doc.status || 'Unknown'}</p>
                    <p><strong>ID:</strong> <span style="font-family: monospace; font-size: 11px;">${doc.id || docNode.id}</span></p>
                </div>

                <p><em>Click on claims in the graph to see detailed analysis.</em></p>
            </div>
        `;

        detailTitle.innerHTML = detailsHTML;
        detailPanel.style.display = 'block';
    },

    /**
     * Show evidence details
     */
    showEvidenceDetails(evidenceNode) {
        const detailPanel = document.getElementById('detail-panel');
        const detailTitle = document.getElementById('detail-claim-text');

        const ev = evidenceNode.fullData;
        const detailsHTML = `
            <div style="margin-bottom: 20px;">
                <h3 style="margin-bottom: 15px; color: #FF9800;">📚 ${ev.title || evidenceNode.label}</h3>

                <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                    <h4 style="margin-top: 0; margin-bottom: 12px; color: #555;">Evidence Information</h4>
                    <p><strong>Type:</strong> ${ev.type || 'Unknown'}</p>
                    ${ev.url ? `<p><strong>URL:</strong> <a href="${ev.url}" target="_blank" style="color: #2196F3;">${ev.url}</a></p>` : ''}
                    <p><strong>ID:</strong> <span style="font-family: monospace; font-size: 11px;">${ev.id || evidenceNode.id}</span></p>
                </div>
            </div>
        `;

        detailTitle.innerHTML = detailsHTML;
        detailPanel.style.display = 'block';
    },

    /**
     * Close claim details panel
     */
    closeClaimModal() {
        const detailPanel = document.getElementById('detail-panel');
        if (detailPanel) {
            detailPanel.style.display = 'none';
        }
    },

    /**
     * Update statistics display
     */
    updateStats(stats) {
        const statNodes = document.getElementById('stat-nodes');
        const statClaims = document.getElementById('stat-claims');
        const statEvidence = document.getElementById('stat-evidence');
        const statResearch = document.getElementById('stat-research');

        // stats.nodes = total node count from API
        // stats.node_types = object with counts by label (Document, Claim, Evidence, etc.)
        if (statNodes) statNodes.textContent = stats.nodes || 0;

        // Get specific counts from node_types object
        const claimCount = (stats.node_types && stats.node_types['Claim']) || 0;
        const evidenceCount = (stats.node_types && stats.node_types['Evidence']) || 0;
        const researchCount = (stats.research && stats.research.total_results) || 0;

        if (statClaims) statClaims.textContent = claimCount;
        if (statEvidence) statEvidence.textContent = evidenceCount;
        if (statResearch) statResearch.textContent = researchCount;

        if (!statNodes || !statClaims || !statEvidence || !statResearch) {
            console.warn('Stats elements not found in DOM:', {statNodes, statClaims, statEvidence, statResearch});
        }
    },

    /**
     * Update processing status with scrolling log
     */
    updateProcessingStatus(message, progress) {
        const statusText = document.getElementById('status-text');
        const progressBar = document.getElementById('progress-bar');

        if (statusText) {
            // Append new message with timestamp instead of replacing
            const timestamp = new Date().toLocaleTimeString();
            const logEntry = document.createElement('div');
            logEntry.style.cssText = 'margin-bottom: 4px; color: #999;';
            logEntry.textContent = `[${timestamp}] ${message}`;
            statusText.appendChild(logEntry);

            // Auto-scroll to bottom
            statusText.scrollTop = statusText.scrollHeight;

            // Keep only last 50 messages to prevent memory issues
            while (statusText.children.length > 50) {
                statusText.removeChild(statusText.firstChild);
            }
        }

        if (progressBar) {
            // NEVER GO BACKWARDS - only update if new progress is higher
            const currentWidth = parseFloat(progressBar.style.width) || 0;
            if (progress > currentWidth) {
                progressBar.style.width = progress + '%';
            }
        }

        if (!statusText || !progressBar) {
            console.warn('Processing status elements not found:', {statusText, progressBar});
        }
    },

    /**
     * Update queue status display
     */
    updateQueueStatus(processing, queueSize) {
        const queuePanel = document.getElementById('queue-status');
        const queueCount = document.getElementById('queue-count');
        const queueProcessing = document.getElementById('queue-processing');

        if (!queuePanel || !queueCount || !queueProcessing) {
            console.warn('Queue status elements not found');
            return;
        }

        // Show/hide queue panel
        if (queueSize > 0 || processing) {
            queuePanel.style.display = 'block';
        } else {
            queuePanel.style.display = 'none';
        }

        // Update queue count
        const plural = queueSize === 1 ? '' : 's';
        queueCount.textContent = `${queueSize} document${plural} waiting`;

        // Update currently processing file
        if (processing) {
            queueProcessing.textContent = `Processing: ${processing}`;
        } else {
            queueProcessing.textContent = '';
        }
    },

    /**
     * Handle file upload
     */
    async handleFileUpload(fileOrFiles) {
        // Support both single file and FileList (multiple files)
        const files = fileOrFiles instanceof FileList ? Array.from(fileOrFiles) : [fileOrFiles];
        console.log(`handleFileUpload called with ${files.length} file(s):`, files.map(f => f.name));

        const processingPanel = document.getElementById('processing-status');
        if (processingPanel) {
            processingPanel.style.display = 'block';
        } else {
            console.warn('processing-status element not found');
        }

        // Upload files sequentially (could be parallel, but sequential is safer)
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            const fileNum = files.length > 1 ? ` (${i+1}/${files.length})` : '';

            this.updateProcessingStatus(`Uploading ${file.name}${fileNum}...`, (i / files.length) * 5);

            try {
                console.log(`Uploading file ${i+1}/${files.length}: ${file.name}`);
                await API.uploadDocument(file);
                console.log(`Upload ${i+1}/${files.length} successful!`);
                this.updateProcessingStatus(`Uploaded ${file.name}${fileNum}! Processing...`, ((i+1) / files.length) * 10);

                // Dispatch document uploaded event for tutorial
                document.dispatchEvent(new CustomEvent('documentUploaded', {
                    detail: { fileName: file.name }
                }));

                // Brief delay between uploads to avoid overwhelming the server
                if (i < files.length - 1) {
                    await new Promise(resolve => setTimeout(resolve, 500));
                }
            } catch (error) {
                console.error(`Upload ${i+1}/${files.length} failed:`, error);
                const msg = `Failed to upload ${file.name}: ${error.message}`;
                this.updateProcessingStatus(msg, 0);

                // Ask if user wants to continue with remaining files
                if (i < files.length - 1) {
                    const continueUploading = confirm(`${msg}\n\nContinue with remaining ${files.length - i - 1} file(s)?`);
                    if (!continueUploading) {
                        break;
                    }
                } else {
                    alert(msg);
                }
            }
        }

        if (files.length > 1) {
            this.updateProcessingStatus(`Uploaded ${files.length} documents. Processing...`, 10);
        }
    },

    /**
     * Confirm and clear all data
     */
    async confirmClearAll() {
        if (!confirm('Are you sure you want to clear ALL data? This cannot be undone.')) {
            return;
        }

        try {
            await API.clearAll();
            alert('All data cleared successfully');
            location.reload();
        } catch (error) {
            console.error('Clear failed:', error);
            alert(`Failed to clear data: ${error.message}`);
        }
    },

    /**
     * Remove evidence link from a claim
     * @param {string} claimId - Claim ID
     * @param {string} evidenceId - Evidence ID to remove
     * @param {string} evidenceTitle - Evidence title for confirmation dialog
     */
    async removeEvidence(claimId, evidenceId, evidenceTitle) {
        const confirmed = confirm(
            `Remove evidence "${evidenceTitle}"?\n\n` +
            `This will permanently remove this evidence link from the claim. ` +
            `The claim's confidence may be recalculated.`
        );

        if (!confirmed) return;

        try {
            const response = await fetch(`/api/claim/${claimId}/evidence/${evidenceId}`, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' }
            });

            if (!response.ok) {
                throw new Error('Failed to remove evidence');
            }

            const data = await response.json();

            // Show success notification
            this.showNotification(
                `Evidence removed. Confidence updated to ${(data.new_confidence * 100).toFixed(1)}%`,
                'success',
                5000
            );

            // Reload claim details to show updated evidence list
            await this.showClaimDetails(claimId);

            // Reload graph to reflect any confidence changes
            await App.loadGraph();

        } catch (error) {
            console.error('Error removing evidence:', error);
            this.showNotification('Failed to remove evidence', 'error', 5000);
        }
    },

    /**
     * Show notification to user
     * @param {string} message - Notification message
     * @param {string} type - Notification type ('info', 'success', 'warning', 'error')
     */
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;

        // Style notification
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            padding: '15px 20px',
            borderRadius: '8px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
            zIndex: '10000',
            maxWidth: '400px',
            fontSize: '14px',
            fontWeight: '500',
            animation: 'slideIn 0.3s ease-out',
            transition: 'all 0.3s ease'
        });

        // Set colors based on type
        const colors = {
            'info': { bg: '#2196F3', fg: 'white' },
            'success': { bg: '#4CAF50', fg: 'white' },
            'warning': { bg: '#FF9800', fg: 'white' },
            'error': { bg: '#F44336', fg: 'white' }
        };
        const color = colors[type] || colors['info'];
        notification.style.backgroundColor = color.bg;
        notification.style.color = color.fg;

        // Add to page
        document.body.appendChild(notification);

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(400px)';
            setTimeout(() => notification.remove(), 300);
        }, 5000);
    },

    /**
     * Fetch and display provenance information for a node
     */
    async fetchAndDisplayProvenance(nodeId) {
        try {
            console.log('🔍 Fetching provenance for node:', nodeId);
            const response = await fetch(`/api/nodes/${nodeId}/provenance`);

            if (!response.ok) {
                // Node might not have provenance, hide the section
                document.getElementById('provenance-section').style.display = 'none';
                return;
            }

            const provenance = await response.json();
            console.log('✓ Provenance data:', provenance);

            // Show provenance section
            const provenanceSection = document.getElementById('provenance-section');
            provenanceSection.style.display = 'block';

            // Display creator info
            const creatorSpan = document.getElementById('provenance-creator');
            if (provenance.created_by && provenance.created_by.actor) {
                let creatorHTML = `<span style="color: #2196F3; font-weight: bold;">${provenance.created_by.actor}</span>`;

                // Add timestamp if available
                if (provenance.created_by.timestamp) {
                    const createdDate = new Date(provenance.created_by.timestamp);
                    creatorHTML += `<span style="font-size: 10px; color: #666; margin-left: 6px;">(${createdDate.toLocaleString()})</span>`;
                }

                // Add clickable agent link if available
                if (provenance.created_by.agent_id && provenance.created_by.agent_transcript_available) {
                    creatorHTML += ` <a href="#" onclick="UI.showAgentTranscript('${provenance.created_by.agent_id}'); return false;"
                                     style="color: #4CAF50; font-size: 11px; margin-left: 4px;">
                                     [View Transcript]
                                   </a>`;

                    // Add agent description if available
                    if (provenance.created_by.agent_description) {
                        creatorHTML += `<br><span style="font-size: 11px; color: #999;">${provenance.created_by.agent_description}</span>`;
                    }
                }

                creatorSpan.innerHTML = creatorHTML;
            }

            // Display discoverer info if present
            const discoveredByDiv = document.getElementById('provenance-discovered-by');
            if (provenance.discovered_by) {
                discoveredByDiv.style.display = 'block';
                const discovererSpan = document.getElementById('provenance-discoverer');

                let discovererHTML = `<span style="color: #FF9800; font-weight: bold;">${provenance.discovered_by.actor}</span>`;

                // Add timestamp if available
                if (provenance.discovered_by.timestamp) {
                    const discoveredDate = new Date(provenance.discovered_by.timestamp);
                    discovererHTML += `<span style="font-size: 10px; color: #666; margin-left: 6px;">(${discoveredDate.toLocaleString()})</span>`;
                }

                // Add clickable agent link if available
                if (provenance.discovered_by.agent_id && provenance.discovered_by.agent_transcript_available) {
                    discovererHTML += ` <a href="#" onclick="UI.showAgentTranscript('${provenance.discovered_by.agent_id}'); return false;"
                                        style="color: #4CAF50; font-size: 11px; margin-left: 4px;">
                                        [View Transcript]
                                      </a>`;

                    // Add agent description if available
                    if (provenance.discovered_by.agent_description) {
                        discovererHTML += `<br><span style="font-size: 11px; color: #999;">${provenance.discovered_by.agent_description}</span>`;
                    }
                }

                discovererSpan.innerHTML = discovererHTML;
            } else {
                discoveredByDiv.style.display = 'none';
            }

            // Display lineage chain if present
            if (provenance.lineage_chain && provenance.lineage_chain.length > 0) {
                const lineageDiv = document.getElementById('provenance-lineage');
                const lineageList = document.getElementById('provenance-lineage-list');
                lineageDiv.style.display = 'block';

                let lineageHTML = '<div style="display: flex; flex-direction: column; gap: 8px;">';

                provenance.lineage_chain.forEach((step, index) => {
                    const isLast = index === provenance.lineage_chain.length - 1;
                    const arrow = isLast ? '' : '<div style="text-align: center; color: #666;">↓</div>';

                    lineageHTML += `
                        <div style="background: #f5f5f5; padding: 8px; border-radius: 4px; border-left: 3px solid ${index === 0 ? '#FF9800' : '#2196F3'};">
                            <strong>${step.action}</strong> by ${step.actor}
                            ${step.agent_id ? `<br><span style="font-size: 10px; color: #666; font-family: monospace;">${step.agent_id}</span>` : ''}
                        </div>
                        ${arrow}
                    `;
                });

                lineageHTML += '</div>';
                lineageList.innerHTML = lineageHTML;
            }

        } catch (error) {
            console.error('Error fetching provenance:', error);
            // Hide section if error
            document.getElementById('provenance-section').style.display = 'none';
        }
    },

    /**
     * Show agent transcript in a modal or panel
     */
    async showAgentTranscript(agentId) {
        try {
            console.log('🔍 Fetching transcript for agent:', agentId);
            const response = await fetch(`/api/agents/${agentId}/transcript`);

            if (!response.ok) {
                this.showNotification('Agent transcript not found', 'error');
                return;
            }

            const transcript = await response.json();
            console.log('✓ Agent transcript:', transcript);

            // Create modal to display transcript
            let modalHTML = `
                <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 10000; display: flex; align-items: center; justify-content: center;"
                     onclick="this.remove()">
                    <div style="background: white; width: 80%; max-width: 800px; max-height: 80%; border-radius: 8px; padding: 24px; overflow-y: auto;"
                         onclick="event.stopPropagation();">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                            <h2 style="margin: 0; color: #333;">Agent Transcript</h2>
                            <button onclick="this.closest('[onclick*=remove]').remove()"
                                    style="background: #f44336; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                                Close
                            </button>
                        </div>

                        <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                            <p><strong>Agent:</strong> ${transcript.agent_type}</p>
                            <p><strong>Description:</strong> ${transcript.description}</p>
                            <p><strong>Status:</strong> <span style="color: ${transcript.status === 'completed' ? '#4CAF50' : transcript.status === 'failed' ? '#f44336' : '#FF9800'}; font-weight: bold;">${transcript.status.toUpperCase()}</span></p>
                            <p><strong>Duration:</strong> ${transcript.duration_seconds ? transcript.duration_seconds.toFixed(2) + 's' : 'In progress...'}</p>
                        </div>

                        <h3 style="margin: 20px 0 10px 0;">Activity Log (${transcript.entry_count} entries)</h3>
                        <div style="max-height: 400px; overflow-y: auto; border: 1px solid #ddd; border-radius: 4px; padding: 10px; background: #fafafa;">
            `;

            // Display log entries
            transcript.entries.forEach((entry, index) => {
                const levelColors = {
                    'info': '#2196F3',
                    'success': '#4CAF50',
                    'warning': '#FF9800',
                    'error': '#f44336'
                };

                const levelColor = levelColors[entry.level] || '#666';

                modalHTML += `
                    <div style="margin-bottom: 12px; padding: 10px; background: white; border-left: 4px solid ${levelColor}; border-radius: 4px;">
                        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 4px;">
                            <strong style="color: ${levelColor}; text-transform: uppercase; font-size: 11px;">${entry.level}</strong>
                            <span style="font-size: 10px; color: #999;">${new Date(entry.timestamp).toLocaleString()}</span>
                        </div>
                        <div style="font-size: 13px; color: #333;">${entry.message}</div>
                        ${entry.data && Object.keys(entry.data).length > 0 ? `
                            <details style="margin-top: 6px;">
                                <summary style="cursor: pointer; font-size: 11px; color: #666;">View data</summary>
                                <pre style="font-size: 10px; color: #666; margin: 4px 0 0 0; overflow-x: auto; white-space: pre-wrap;">${JSON.stringify(entry.data, null, 2)}</pre>
                            </details>
                        ` : ''}
                    </div>
                `;
            });

            modalHTML += `
                        </div>

                        ${transcript.result ? `
                            <div style="margin-top: 20px; padding: 15px; background: #e8f5e9; border-radius: 5px; border-left: 4px solid #4CAF50;">
                                <strong>Result:</strong>
                                <pre style="margin: 8px 0 0 0; font-size: 12px; overflow-x: auto; white-space: pre-wrap;">${JSON.stringify(transcript.result, null, 2)}</pre>
                            </div>
                        ` : ''}

                        ${transcript.error ? `
                            <div style="margin-top: 20px; padding: 15px; background: #ffebee; border-radius: 5px; border-left: 4px solid #f44336;">
                                <strong>Error:</strong>
                                <div style="margin-top: 8px; color: #c62828;">${transcript.error}</div>
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;

            // Add modal to page
            const modalDiv = document.createElement('div');
            modalDiv.innerHTML = modalHTML;
            document.body.appendChild(modalDiv);

        } catch (error) {
            console.error('Error fetching agent transcript:', error);
            this.showNotification('Failed to load agent transcript', 'error');
        }
    }
};

// Make showClaimDetails globally accessible for graph clicks
window.showClaimDetails = UI.showClaimDetails.bind(UI);
