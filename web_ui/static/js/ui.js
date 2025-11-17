/**
 * UI Module - User interface interactions and components
 */

const UI = {
    /**
     * Show claim details in modal
     */
    async showClaimDetails(claimId) {
        try {
            const claim = await API.fetchClaim(claimId);

            const modal = document.getElementById('claim-modal');
            const modalContent = document.getElementById('modal-claim-text');

            let detailsHTML = `
                <h3>${claim.text || 'Claim'}</h3>
                <p><strong>Summary:</strong> ${claim.summary || 'N/A'}</p>
            `;

            if (claim.specificity) {
                detailsHTML += `<p><strong>Specificity:</strong> ${claim.specificity.toFixed(2)}</p>`;
            }

            if (claim.children && claim.children.length > 0) {
                detailsHTML += `<h4>Child Claims (${claim.children.length}):</h4><ul>`;
                claim.children.forEach(child => {
                    detailsHTML += `<li>${child.summary || child.text}</li>`;
                });
                detailsHTML += `</ul>`;
            }

            if (claim.evidence && claim.evidence.length > 0) {
                detailsHTML += `<h4>Evidence (${claim.evidence.length}):</h4><ul>`;
                claim.evidence.forEach(ev => {
                    detailsHTML += `<li>${ev.title} (${ev.type})</li>`;
                });
                detailsHTML += `</ul>`;
            }

            if (claim.sources && claim.sources.length > 0) {
                detailsHTML += `<h4>Source Locations:</h4><ul>`;
                claim.sources.forEach(src => {
                    if (src.page) {
                        detailsHTML += `<li>Page ${src.page}, Line ${src.line}: ${src.sentence}</li>`;
                    }
                });
                detailsHTML += `</ul>`;
            }

            modalContent.innerHTML = detailsHTML;
            modal.style.display = 'flex';
        } catch (error) {
            console.error('Failed to load claim details:', error);
            alert(`Failed to load claim: ${error.message}`);
        }
    },

    /**
     * Close claim details modal
     */
    closeClaimModal() {
        const modal = document.getElementById('claim-modal');
        modal.style.display = 'none';
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
     * Show upload modal
     */
    showUploadModal() {
        document.getElementById('upload-modal').style.display = 'flex';
    },

    /**
     * Hide upload modal
     */
    hideUploadModal() {
        document.getElementById('upload-modal').style.display = 'none';
    },

    /**
     * Handle file upload
     */
    async handleFileUpload(file) {
        this.hideUploadModal();

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
