/**
 * Comment System - Manages commenting on graph nodes
 *
 * Features:
 * - Add/edit/delete comments on any node
 * - Nested reply threads
 * - Markdown support with preview
 * - Real-time updates via WebSocket
 * - Search within comments
 */

const CommentSystem = {
    currentNodeId: null,
    comments: [],
    editingCommentId: null,
    replyingToCommentId: null,

    /**
     * Initialize the comment system
     */
    init() {
        console.log('Initializing Comment System...');

        // Setup WebSocket listeners for real-time updates
        if (App.socket) {
            App.socket.on('comment_added', (data) => this.handleCommentAdded(data));
            App.socket.on('comment_updated', (data) => this.handleCommentUpdated(data));
            App.socket.on('comment_deleted', (data) => this.handleCommentDeleted(data));
        }

        // Setup UI event listeners
        this.setupEventListeners();

        console.log('✓ Comment System initialized');
    },

    /**
     * Setup event listeners for comment UI
     */
    setupEventListeners() {
        // Comment submit button
        document.addEventListener('click', (e) => {
            if (e.target.matches('#submit-comment-btn')) {
                this.submitComment();
            }
        });

        // Cancel button
        document.addEventListener('click', (e) => {
            if (e.target.matches('#cancel-comment-btn')) {
                this.cancelEdit();
            }
        });

        // Edit comment buttons
        document.addEventListener('click', (e) => {
            if (e.target.matches('.edit-comment-btn')) {
                const commentId = e.target.dataset.commentId;
                this.editComment(commentId);
            }
        });

        // Delete comment buttons
        document.addEventListener('click', (e) => {
            if (e.target.matches('.delete-comment-btn')) {
                const commentId = e.target.dataset.commentId;
                this.deleteComment(commentId);
            }
        });

        // Reply to comment buttons
        document.addEventListener('click', (e) => {
            if (e.target.matches('.reply-comment-btn')) {
                const commentId = e.target.dataset.commentId;
                this.replyToComment(commentId);
            }
        });

        // Markdown preview toggle
        document.addEventListener('click', (e) => {
            if (e.target.matches('#toggle-markdown-preview')) {
                this.toggleMarkdownPreview();
            }
        });
    },

    /**
     * Load comments for a node
     */
    async loadComments(nodeId) {
        try {
            this.currentNodeId = nodeId;

            const response = await fetch(`/api/comments/node/${nodeId}`);
            const data = await response.json();

            if (data.success) {
                this.comments = data.comments;
                this.renderComments();
            } else {
                console.error('Failed to load comments:', data.error);
                UI.showError('Failed to load comments');
            }
        } catch (error) {
            console.error('Error loading comments:', error);
            UI.showError('Error loading comments');
        }
    },

    /**
     * Render comments in the UI
     */
    renderComments() {
        const container = document.getElementById('comments-container');
        if (!container) {
            console.warn('Comments container not found');
            return;
        }

        if (this.comments.length === 0) {
            container.innerHTML = `
                <div class="no-comments">
                    <p>No comments yet. Be the first to comment!</p>
                </div>
            `;
            return;
        }

        // Render comment tree
        const html = this.comments.map(comment => this.renderCommentThread(comment)).join('');
        container.innerHTML = html;

        // Update comment count badge
        const count = this.countAllComments(this.comments);
        const badge = document.getElementById('comment-count-badge');
        if (badge) {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'inline-block' : 'none';
        }
    },

    /**
     * Render a comment and its replies recursively
     */
    renderCommentThread(comment, level = 0) {
        const indent = level * 20;
        const createdAt = new Date(comment.created_at).toLocaleString();
        const updatedAt = comment.updated_at !== comment.created_at
            ? `(edited ${new Date(comment.updated_at).toLocaleString()})`
            : '';

        // Render markdown to HTML
        const htmlContent = this.renderMarkdown(comment.text);

        let html = `
            <div class="comment" data-comment-id="${comment.id}" style="margin-left: ${indent}px">
                <div class="comment-header">
                    <span class="comment-timestamp">${createdAt} ${updatedAt}</span>
                    <div class="comment-actions">
                        <button class="btn-icon reply-comment-btn" data-comment-id="${comment.id}" title="Reply">
                            💬
                        </button>
                        <button class="btn-icon edit-comment-btn" data-comment-id="${comment.id}" title="Edit">
                            ✏️
                        </button>
                        <button class="btn-icon delete-comment-btn" data-comment-id="${comment.id}" title="Delete">
                            🗑️
                        </button>
                    </div>
                </div>
                <div class="comment-content">
                    ${htmlContent}
                </div>
            </div>
        `;

        // Render replies
        if (comment.replies && comment.replies.length > 0) {
            html += comment.replies.map(reply => this.renderCommentThread(reply, level + 1)).join('');
        }

        return html;
    },

    /**
     * Count all comments including replies
     */
    countAllComments(comments) {
        let count = comments.length;
        for (const comment of comments) {
            if (comment.replies && comment.replies.length > 0) {
                count += this.countAllComments(comment.replies);
            }
        }
        return count;
    },

    /**
     * Render markdown to HTML (simple implementation)
     */
    renderMarkdown(text) {
        // Simple markdown rendering
        // For production, use a library like marked.js
        let html = text;

        // Bold
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        // Italic
        html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
        // Code
        html = html.replace(/`(.+?)`/g, '<code>$1</code>');
        // Links
        html = html.replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" target="_blank">$1</a>');
        // Line breaks
        html = html.replace(/\n/g, '<br>');

        return html;
    },

    /**
     * Submit a new comment or edit
     */
    async submitComment() {
        const textarea = document.getElementById('comment-text');
        const text = textarea.value.trim();

        if (!text) {
            UI.showError('Comment text is required');
            return;
        }

        try {
            if (this.editingCommentId) {
                // Update existing comment
                await this.updateComment(this.editingCommentId, text);
            } else {
                // Create new comment
                const response = await fetch('/api/comments', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        node_id: this.currentNodeId,
                        text: text,
                        parent_comment_id: this.replyingToCommentId
                    })
                });

                const data = await response.json();

                if (data.success) {
                    UI.showSuccess('Comment added');
                    textarea.value = '';
                    this.replyingToCommentId = null;
                    this.updateReplyIndicator();
                    // Comments will be updated via WebSocket
                } else {
                    UI.showError(data.error || 'Failed to add comment');
                }
            }
        } catch (error) {
            console.error('Error submitting comment:', error);
            UI.showError('Error submitting comment');
        }
    },

    /**
     * Update an existing comment
     */
    async updateComment(commentId, text) {
        try {
            const response = await fetch(`/api/comments/${commentId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });

            const data = await response.json();

            if (data.success) {
                UI.showSuccess('Comment updated');
                this.cancelEdit();
                // Comments will be updated via WebSocket
            } else {
                UI.showError(data.error || 'Failed to update comment');
            }
        } catch (error) {
            console.error('Error updating comment:', error);
            UI.showError('Error updating comment');
        }
    },

    /**
     * Delete a comment
     */
    async deleteComment(commentId) {
        if (!confirm('Delete this comment and all replies?')) {
            return;
        }

        try {
            const response = await fetch(`/api/comments/${commentId}`, {
                method: 'DELETE'
            });

            const data = await response.json();

            if (data.success) {
                UI.showSuccess(`Comment deleted (${data.deleted_count} total)`);
                // Comments will be updated via WebSocket
            } else {
                UI.showError(data.error || 'Failed to delete comment');
            }
        } catch (error) {
            console.error('Error deleting comment:', error);
            UI.showError('Error deleting comment');
        }
    },

    /**
     * Start editing a comment
     */
    editComment(commentId) {
        const comment = this.findComment(this.comments, commentId);
        if (!comment) {
            console.error('Comment not found:', commentId);
            return;
        }

        this.editingCommentId = commentId;
        const textarea = document.getElementById('comment-text');
        textarea.value = comment.text;
        textarea.focus();

        // Update UI to show edit mode
        const submitBtn = document.getElementById('submit-comment-btn');
        submitBtn.textContent = 'Update Comment';

        const cancelBtn = document.getElementById('cancel-comment-btn');
        cancelBtn.style.display = 'inline-block';
    },

    /**
     * Start replying to a comment
     */
    replyToComment(commentId) {
        this.replyingToCommentId = commentId;
        const textarea = document.getElementById('comment-text');
        textarea.focus();

        this.updateReplyIndicator();
    },

    /**
     * Update reply indicator in UI
     */
    updateReplyIndicator() {
        const indicator = document.getElementById('reply-indicator');
        if (!indicator) return;

        if (this.replyingToCommentId) {
            const comment = this.findComment(this.comments, this.replyingToCommentId);
            if (comment) {
                const preview = comment.text.substring(0, 50) + '...';
                indicator.innerHTML = `
                    Replying to: "${preview}"
                    <button class="btn-icon" onclick="CommentSystem.cancelReply()">✖</button>
                `;
                indicator.style.display = 'block';
            }
        } else {
            indicator.style.display = 'none';
        }
    },

    /**
     * Cancel edit mode
     */
    cancelEdit() {
        this.editingCommentId = null;
        const textarea = document.getElementById('comment-text');
        textarea.value = '';

        const submitBtn = document.getElementById('submit-comment-btn');
        submitBtn.textContent = 'Add Comment';

        const cancelBtn = document.getElementById('cancel-comment-btn');
        cancelBtn.style.display = 'none';
    },

    /**
     * Cancel reply mode
     */
    cancelReply() {
        this.replyingToCommentId = null;
        this.updateReplyIndicator();
    },

    /**
     * Find a comment by ID in the tree
     */
    findComment(comments, commentId) {
        for (const comment of comments) {
            if (comment.id === commentId) {
                return comment;
            }
            if (comment.replies && comment.replies.length > 0) {
                const found = this.findComment(comment.replies, commentId);
                if (found) return found;
            }
        }
        return null;
    },

    /**
     * Toggle markdown preview
     */
    toggleMarkdownPreview() {
        const textarea = document.getElementById('comment-text');
        const preview = document.getElementById('markdown-preview');
        const toggle = document.getElementById('toggle-markdown-preview');

        if (preview.style.display === 'none') {
            // Show preview
            preview.innerHTML = this.renderMarkdown(textarea.value || 'Nothing to preview');
            preview.style.display = 'block';
            textarea.style.display = 'none';
            toggle.textContent = 'Edit';
        } else {
            // Show editor
            preview.style.display = 'none';
            textarea.style.display = 'block';
            toggle.textContent = 'Preview';
        }
    },

    /**
     * Search comments
     */
    async searchComments(query) {
        if (!query.trim()) {
            this.loadComments(this.currentNodeId);
            return;
        }

        try {
            const params = new URLSearchParams({
                q: query,
                node_id: this.currentNodeId
            });

            const response = await fetch(`/api/comments/search?${params}`);
            const data = await response.json();

            if (data.success) {
                // Render search results
                this.renderSearchResults(data.comments);
            } else {
                UI.showError(data.error || 'Search failed');
            }
        } catch (error) {
            console.error('Error searching comments:', error);
            UI.showError('Error searching comments');
        }
    },

    /**
     * Render search results
     */
    renderSearchResults(results) {
        const container = document.getElementById('comments-container');

        if (results.length === 0) {
            container.innerHTML = '<div class="no-results">No comments found</div>';
            return;
        }

        const html = results.map(comment => `
            <div class="comment search-result" data-comment-id="${comment.id}">
                <div class="comment-header">
                    <span class="comment-timestamp">${new Date(comment.created_at).toLocaleString()}</span>
                </div>
                <div class="comment-content">
                    ${this.renderMarkdown(comment.text)}
                </div>
                <div class="comment-snippet">
                    Snippet: ${comment.snippet}
                </div>
            </div>
        `).join('');

        container.innerHTML = html;
    },

    /**
     * WebSocket event handlers
     */
    handleCommentAdded(data) {
        if (data.node_id === this.currentNodeId) {
            this.loadComments(this.currentNodeId);
        }
    },

    handleCommentUpdated(data) {
        if (data.node_id === this.currentNodeId) {
            this.loadComments(this.currentNodeId);
        }
    },

    handleCommentDeleted(data) {
        if (data.node_id === this.currentNodeId) {
            this.loadComments(this.currentNodeId);
        }
    },

    /**
     * Export comments for current node
     */
    async exportComments(format = 'json') {
        try {
            const params = new URLSearchParams({
                node_id: this.currentNodeId,
                format: format
            });

            const response = await fetch(`/api/comments/export?${params}`);

            if (format === 'csv') {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `comments_${this.currentNodeId}_${new Date().toISOString().split('T')[0]}.csv`;
                a.click();
            } else {
                const data = await response.json();
                if (data.success) {
                    // Download as JSON
                    const blob = new Blob([JSON.stringify(data.comments, null, 2)], { type: 'application/json' });
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `comments_${this.currentNodeId}_${new Date().toISOString().split('T')[0]}.json`;
                    a.click();
                }
            }

            UI.showSuccess('Comments exported');
        } catch (error) {
            console.error('Error exporting comments:', error);
            UI.showError('Error exporting comments');
        }
    }
};

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', () => {
    CommentSystem.init();
});
