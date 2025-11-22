/**
 * API Module - Handles all backend communication
 */

const API = {
    /**
     * Fetch full graph data (documents, super-claims, sub-claims, evidence)
     */
    async fetchGraph() {
        const response = await fetch('/api/full-graph');
        if (!response.ok) throw new Error(`API error: ${response.statusText}`);
        return await response.json();
    },

    /**
     * Fetch statistics about the graph
     */
    async fetchStats() {
        const response = await fetch('/api/graph-stats');
        if (!response.ok) throw new Error(`API error: ${response.statusText}`);
        return await response.json();
    },

    /**
     * Fetch detailed information about a specific claim
     */
    async fetchClaim(claimId) {
        const response = await fetch(`/api/claim/${claimId}`);
        if (!response.ok) throw new Error(`Claim not found: ${claimId}`);
        return await response.json();
    },

    /**
     * Upload a document for processing
     */
    async uploadDocument(file) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/api/upload-document', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error(`Upload failed: ${response.statusText}`);
        return await response.json();
    },

    /**
     * Upload a URL for processing
     */
    async uploadURL(url) {
        const response = await fetch('/api/upload-url', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });

        if (!response.ok) throw new Error(`URL upload failed: ${response.statusText}`);
        return await response.json();
    },

    /**
     * Create a manual claim
     */
    async createManualClaim(text) {
        const response = await fetch('/api/create-manual-claim', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });

        if (!response.ok) throw new Error(`Manual claim creation failed: ${response.statusText}`);
        return await response.json();
    },

    /**
     * Clear all data from the database
     */
    async clearAll() {
        const response = await fetch('/api/clear-all', {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error(`Clear failed: ${response.statusText}`);
        return await response.json();
    },

    /**
     * Launch investigation for a claim
     */
    async investigateClaim(claimId, investigationType = 'support') {
        const response = await fetch('/api/investigate-claim', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                claim_id: claimId,
                type: investigationType
            })
        });

        if (!response.ok) throw new Error(`Investigation failed: ${response.statusText}`);
        return await response.json();
    }
};
