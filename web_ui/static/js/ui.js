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
            detailPanel.classList.add('visible');
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
        const docCount = document.getElementById('doc-count');
        const claimCount = document.getElementById('claim-count');
        const evidenceCount = document.getElementById('evidence-count');

        if (docCount) docCount.textContent = stats.documents || 0;
        if (claimCount) claimCount.textContent = stats.claims || 0;
        if (evidenceCount) evidenceCount.textContent = stats.evidence || 0;

        if (!docCount || !claimCount || !evidenceCount) {
            console.warn('Stats elements not found in DOM:', {docCount, claimCount, evidenceCount});
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
     * Handle file upload
     */
    async handleFileUpload(file) {
        console.log('handleFileUpload called with:', file);

        const processingPanel = document.getElementById('processing-status');
        if (processingPanel) {
            processingPanel.style.display = 'block';
        } else {
            console.warn('processing-status element not found');
        }

        this.updateProcessingStatus('Uploading document...', 0);

        try {
            console.log('Calling API.uploadDocument...');
            await API.uploadDocument(file);
            console.log('Upload successful!');
            this.updateProcessingStatus('Upload successful! Processing started...', 10);

            // DON'T reload here - wait for WebSocket 'document_processed' event
            // Processing happens in background thread and may take several minutes
        } catch (error) {
            console.error('Upload failed:', error);
            this.updateProcessingStatus(`Error: ${error.message}`, 0);
            alert(`Upload failed: ${error.message}`);
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
