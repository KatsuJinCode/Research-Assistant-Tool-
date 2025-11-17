/**
 * UI Module - User interface interactions and components
 */

const UI = {
    /**
     * Show claim details in modal with visual metrics dashboard
     */
    async showClaimDetails(claimId) {
        try {
            const claim = await API.fetchClaim(claimId);

            // Use the sidebar detail panel, not a modal
            const detailPanel = document.getElementById('detail-panel');
            const detailTitle = document.getElementById('detail-claim-text');

            // Calculate metrics that drive visual encoding
            const confidence = claim.confidence || claim.quality_score || 0.5;
            const childCount = claim.children ? claim.children.length : 0;
            const evidenceCount = claim.evidence ? claim.evidence.length : 0;
            const supportingEvidence = claim.evidence ? claim.evidence.filter(e => e.type === 'SUPPORTS').length : 0;
            const contradictingEvidence = claim.evidence ? claim.evidence.filter(e => e.type === 'CONTRADICTS').length : 0;
            const specificity = claim.specificity || 0.5;

            // Pre-calculate formatted values
            const nodeSize = this.calculateNodeSize(childCount);
            const specificityLabel = this.getSpecificityLabel(specificity);

            // Build metrics dashboard
            let detailsHTML = `
                <div style="margin-bottom: 20px;">
                    <h3 style="margin-bottom: 15px;">${claim.text || 'Claim'}</h3>

                    <!-- Visual Metrics Dashboard -->
                    <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                        <h4 style="margin-top: 0; margin-bottom: 12px; color: #555;">Visual Metrics</h4>

                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                            <!-- Confidence (Border Thickness) -->
                            <div style="background: white; padding: 10px; border-radius: 5px; border-left: 4px solid #2196F3;">
                                <div style="font-size: 11px; color: #666; text-transform: uppercase; margin-bottom: 4px;">Confidence</div>
                                <div style="font-size: 20px; font-weight: bold; color: #333;">${(confidence * 100).toFixed(0)}%</div>
                                <div style="font-size: 10px; color: #888; margin-top: 2px;">
                                    Border: ${(2 + confidence * 3).toFixed(1)}px thick
                                </div>
                            </div>

                            <!-- Size (Descendant Count) -->
                            <div style="background: white; padding: 10px; border-radius: 5px; border-left: 4px solid #9C27B0;">
                                <div style="font-size: 11px; color: #666; text-transform: uppercase; margin-bottom: 4px;">Sub-Claims</div>
                                <div style="font-size: 20px; font-weight: bold; color: #333;">${childCount}</div>
                                <div style="font-size: 10px; color: #888; margin-top: 2px;">
                                    Node size: ${nodeSize}
                                </div>
                            </div>

                            <!-- Color Brightness (Quality) -->
                            <div style="background: white; padding: 10px; border-radius: 5px; border-left: 4px solid #4CAF50;">
                                <div style="font-size: 11px; color: #666; text-transform: uppercase; margin-bottom: 4px;">Quality Score</div>
                                <div style="font-size: 20px; font-weight: bold; color: #333;">${(confidence * 100).toFixed(0)}%</div>
                                <div style="font-size: 10px; color: #888; margin-top: 2px;">
                                    Brightness: ${(60 + confidence * 40).toFixed(0)}%
                                </div>
                            </div>

                            <!-- Evidence Count -->
                            <div style="background: white; padding: 10px; border-radius: 5px; border-left: 4px solid #FF9800;">
                                <div style="font-size: 11px; color: #666; text-transform: uppercase; margin-bottom: 4px;">Evidence</div>
                                <div style="font-size: 20px; font-weight: bold; color: #333;">${evidenceCount}</div>
                                <div style="font-size: 10px; color: #888; margin-top: 2px;">
                                    <span style="color: #4CAF50;">✓ ${supportingEvidence}</span> /
                                    <span style="color: #F44336;">✗ ${contradictingEvidence}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Summary -->
                    ${claim.summary ? `<p><strong>Summary:</strong> ${claim.summary}</p>` : ''}

                    <!-- Specificity -->
                    ${claim.specificity ? `
                        <p><strong>Specificity:</strong> ${claim.specificity.toFixed(2)}
                        <span style="font-size: 11px; color: #888;">(${specificityLabel})</span>
                        </p>
                    ` : ''}
                </div>
            `;

            // Child Claims
            if (claim.children && claim.children.length > 0) {
                detailsHTML += `
                    <div style="margin-bottom: 15px;">
                        <h4 style="margin-bottom: 8px;">Child Claims (${claim.children.length})</h4>
                        <ul style="margin: 0; padding-left: 20px;">
                `;
                claim.children.forEach(child => {
                    detailsHTML += `<li style="margin-bottom: 5px;">${child.summary || child.text}</li>`;
                });
                detailsHTML += `</ul></div>`;
            }

            // Evidence Details
            if (claim.evidence && claim.evidence.length > 0) {
                detailsHTML += `
                    <div style="margin-bottom: 15px;">
                        <h4 style="margin-bottom: 8px;">Evidence (${claim.evidence.length})</h4>
                `;

                // Supporting Evidence
                const supporting = claim.evidence.filter(e => e.type === 'SUPPORTS');
                if (supporting.length > 0) {
                    detailsHTML += `
                        <div style="margin-bottom: 10px;">
                            <strong style="color: #4CAF50;">Supporting (${supporting.length}):</strong>
                            <ul style="margin: 5px 0 0 20px; padding: 0;">
                    `;
                    supporting.forEach(ev => {
                        detailsHTML += `<li style="margin-bottom: 3px;">${ev.title}</li>`;
                    });
                    detailsHTML += `</ul></div>`;
                }

                // Contradicting Evidence
                const contradicting = claim.evidence.filter(e => e.type === 'CONTRADICTS');
                if (contradicting.length > 0) {
                    detailsHTML += `
                        <div>
                            <strong style="color: #F44336;">Contradicting (${contradicting.length}):</strong>
                            <ul style="margin: 5px 0 0 20px; padding: 0;">
                    `;
                    contradicting.forEach(ev => {
                        detailsHTML += `<li style="margin-bottom: 3px;">${ev.title}</li>`;
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
        } catch (error) {
            console.error('Failed to load claim details:', error);
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
        document.getElementById('doc-count').textContent = stats.documents || 0;
        document.getElementById('claim-count').textContent = stats.claims || 0;
        document.getElementById('evidence-count').textContent = stats.evidence || 0;
    },

    /**
     * Update processing status
     */
    updateProcessingStatus(message, progress) {
        document.getElementById('status-text').textContent = message;

        // NEVER GO BACKWARDS - only update if new progress is higher
        const progressBar = document.getElementById('progress-bar');
        const currentWidth = parseFloat(progressBar.style.width) || 0;

        if (progress > currentWidth) {
            progressBar.style.width = progress + '%';
        }
    },

    /**
     * Handle file upload
     */
    async handleFileUpload(file) {

        document.getElementById('processing-panel').style.display = 'block';
        this.updateProcessingStatus('Uploading document...', 0);

        try {
            await API.uploadDocument(file);
            this.updateProcessingStatus('Processing complete!', 100);

            // Hide processing panel after 2 seconds
            setTimeout(() => {
                document.getElementById('processing-panel').style.display = 'none';
            }, 2000);
        } catch (error) {
            console.error('Upload failed:', error);
            this.updateProcessingStatus(`Error: ${error.message}`, 0);
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
    }
};

// Make showClaimDetails globally accessible for graph clicks
window.showClaimDetails = UI.showClaimDetails.bind(UI);
