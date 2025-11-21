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

            // Get real values from claim data
            const qualityScore = claim.quality_score || 0;
            const timestamp = claim.created_at || claim.timestamp || 'Unknown';
            const formattedTime = timestamp !== 'Unknown' ? new Date(timestamp).toLocaleString() : 'Unknown';
            const investigationValue = claim.investigation_priority || claim.investigation_value || 'Not assessed';

            // Build clean detail panel
            let detailsHTML = `
                <div style="margin-bottom: 20px;">
                    <!-- Summary (only shown once, at top) -->
                    <h3 style="margin-bottom: 15px; line-height: 1.4;">${claim.summary || claim.text || 'Claim'}</h3>

                    <!-- Metrics Dashboard (User-Friendly) -->
                    <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                        <h4 style="margin-top: 0; margin-bottom: 12px; color: #555;">Assessment</h4>

                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                            <!-- Confidence -->
                            <div style="background: white; padding: 10px; border-radius: 5px; border-left: 4px solid #2196F3;">
                                <div style="font-size: 11px; color: #666; text-transform: uppercase; margin-bottom: 4px;">Confidence</div>
                                <div style="font-size: 20px; font-weight: bold; color: #333;">${(confidence * 100).toFixed(0)}%</div>
                                <div style="font-size: 10px; color: #888; margin-top: 2px;">
                                    How certain we are this claim is accurate
                                </div>
                            </div>

                            <!-- Quality Score -->
                            <div style="background: white; padding: 10px; border-radius: 5px; border-left: 4px solid #4CAF50;">
                                <div style="font-size: 11px; color: #666; text-transform: uppercase; margin-bottom: 4px;">Quality Score</div>
                                <div style="font-size: 20px; font-weight: bold; color: #333;">${(qualityScore * 100).toFixed(0)}%</div>
                                <div style="font-size: 10px; color: #888; margin-top: 2px;">
                                    Overall quality and clarity of the claim
                                </div>
                            </div>

                            <!-- Sub-Claims -->
                            <div style="background: white; padding: 10px; border-radius: 5px; border-left: 4px solid #9C27B0;">
                                <div style="font-size: 11px; color: #666; text-transform: uppercase; margin-bottom: 4px;">Sub-Claims</div>
                                <div style="font-size: 20px; font-weight: bold; color: #333;">${childCount}</div>
                                <div style="font-size: 10px; color: #888; margin-top: 2px;">
                                    More specific claims derived from this one
                                </div>
                            </div>

                            <!-- Evidence -->
                            <div style="background: white; padding: 10px; border-radius: 5px; border-left: 4px solid #FF9800;">
                                <div style="font-size: 11px; color: #666; text-transform: uppercase; margin-bottom: 4px;">Evidence</div>
                                <div style="font-size: 20px; font-weight: bold; color: #333;">${evidenceCount}</div>
                                <div style="font-size: 10px; color: #888; margin-top: 2px;">
                                    <span style="color: #4CAF50;">✓ ${supportingEvidence} support</span> /
                                    <span style="color: #F44336;">✗ ${contradictingEvidence} contradict</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Full Original Text -->
                    ${claim.text && claim.text !== claim.summary ? `
                        <div style="background: #fff3cd; padding: 12px; border-radius: 5px; margin-bottom: 15px; border-left: 4px solid #ff9800;">
                            <strong style="color: #856404;">Original Text:</strong>
                            <div style="margin-top: 6px; color: #856404; font-size: 14px;">${claim.text}</div>
                        </div>
                    ` : ''}

                    <!-- Metadata -->
                    <div style="font-size: 12px; color: #666; margin-bottom: 15px;">
                        <div style="margin-bottom: 5px;"><strong>Created:</strong> ${formattedTime}</div>
                        <div style="margin-bottom: 5px;"><strong>Investigation Priority:</strong> ${investigationValue}</div>
                        ${claim.disposition ? `<div><strong>Disposition:</strong> ${claim.disposition}</div>` : ''}
                    </div>
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

            // Store claim ID for override operations
            detailPanel.dataset.claimId = claimId;

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
    }
};

// Make showClaimDetails globally accessible for graph clicks
window.showClaimDetails = UI.showClaimDetails.bind(UI);
