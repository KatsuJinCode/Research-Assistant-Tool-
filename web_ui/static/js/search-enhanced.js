/**
 * Enhanced Search System for Research Assistant Tool
 *
 * Features:
 * - Semantic search with embeddings
 * - Natural language queries with LLM
 * - Faceted filters (type, date, confidence, etc.)
 * - Search history and saved searches
 * - Real-time search with previews
 * - Relevance scoring visualization
 */

const SEARCH_HISTORY = 'research_search_history';
const SAVED_SEARCHES = 'research_saved_searches';

class EnhancedSearch {
    static currentFilters = {
        types: ['claim', 'document', 'evidence'],
        dateFrom: '',
        dateTo: '',
        confidenceMin: 0,
        investigationMin: 0,
        authors: []
    };

    static searchHistory = [];
    static savedSearches = [];
    static currentQuery = '';
    static currentResults = [];
    static lastResultCount = 0;
    static currentMode = 'simple'; // 'simple', 'advanced', 'semantic', 'natural'
    static debounceTimer = null;

    /**
     * Initialize the enhanced search system
     */
    static init() {
        console.log('[EnhancedSearch] Initializing...');

        // Load saved data from localStorage
        this.loadHistory();
        this.loadSavedSearches();

        // Setup event listeners
        this.setupEventListeners();

        // Populate author filter
        this.populateAuthorFilter();

        console.log('[EnhancedSearch] ✓ Initialized');
    }

    /**
     * Setup all event listeners for search components
     */
    static setupEventListeners() {
        // Main search input - debounced real-time search
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.handleRealtimeSearch(e.target.value);
            });

            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.executeSearch();
                }
            });
        }

        // Search button
        const searchBtn = document.getElementById('search-btn');
        if (searchBtn) {
            searchBtn.addEventListener('click', () => this.executeSearch());
        }

        // Advanced search toggle
        const advancedBtn = document.getElementById('advanced-search-btn');
        if (advancedBtn) {
            advancedBtn.addEventListener('click', () => this.toggleAdvancedFilters());
        }

        // Apply filters button
        const applyFiltersBtn = document.getElementById('apply-filters-btn');
        if (applyFiltersBtn) {
            applyFiltersBtn.addEventListener('click', () => this.applyFilters());
        }

        // Reset filters button
        const resetFiltersBtn = document.getElementById('reset-filters-btn');
        if (resetFiltersBtn) {
            resetFiltersBtn.addEventListener('click', () => this.resetFilters());
        }

        // Confidence slider
        const confidenceSlider = document.getElementById('confidence-min');
        if (confidenceSlider) {
            confidenceSlider.addEventListener('input', (e) => {
                document.getElementById('confidence-min-value').textContent = e.target.value + '%';
            });
        }

        // Investigation value slider
        const investigationSlider = document.getElementById('investigation-min');
        if (investigationSlider) {
            investigationSlider.addEventListener('input', (e) => {
                document.getElementById('investigation-min-value').textContent = e.target.value + '%';
            });
        }

        // Semantic threshold slider
        const semanticThreshold = document.getElementById('semantic-threshold');
        if (semanticThreshold) {
            semanticThreshold.addEventListener('input', (e) => {
                document.getElementById('semantic-threshold-value').textContent = e.target.value;
            });
        }

        // Search mode toggle buttons
        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.setSearchMode(e.target.dataset.mode);
            });
        });

        // Close preview when clicking outside
        document.addEventListener('click', (e) => {
            const preview = document.getElementById('search-preview');
            const searchInput = document.getElementById('search-input');
            if (preview && !preview.contains(e.target) && e.target !== searchInput) {
                this.hidePreview();
            }
        });
    }

    /**
     * Handle debounced real-time search
     */
    static handleRealtimeSearch(query) {
        clearTimeout(this.debounceTimer);

        if (query.length < 3) {
            this.hidePreview();
            return;
        }

        this.debounceTimer = setTimeout(() => {
            this.realtimeSearch(query);
        }, 300); // Wait 300ms after typing stops
    }

    /**
     * Perform quick real-time search for preview
     */
    static async realtimeSearch(query) {
        try {
            this.showSearching();

            // Quick search with limit of 10 results
            const results = await this.quickSearch(query, 10);

            this.showPreview(results, query);
        } catch (error) {
            console.error('[EnhancedSearch] Real-time search error:', error);
            this.hidePreview();
        }
    }

    /**
     * Execute main search with current filters
     */
    static async executeSearch() {
        const query = document.getElementById('search-input').value.trim();

        if (!query) {
            this.showMessage('Please enter a search query', 'warning');
            return;
        }

        this.currentQuery = query;
        this.hidePreview();

        // Add to history
        this.addToHistory(query, { ...this.currentFilters });

        try {
            this.showLoading();

            // Determine search type based on mode and query
            let results;
            if (this.currentMode === 'semantic') {
                results = await this.semanticSearch(query);
            } else if (this.currentMode === 'natural') {
                results = await this.naturalLanguageSearch(query);
            } else {
                results = await this.keywordSearch(query);
            }

            this.currentResults = results;
            this.lastResultCount = results.length;

            // Display results
            this.displayResults(results, query);

        } catch (error) {
            console.error('[EnhancedSearch] Search error:', error);
            this.showMessage('Search failed: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    /**
     * Quick search for preview (keyword-based)
     */
    static async quickSearch(query, limit = 10) {
        const data = await API.quickSearch(query, limit, this.currentFilters);
        return data.results || [];
    }

    /**
     * Semantic search using embeddings
     */
    static async semanticSearch(query) {
        const threshold = parseFloat(document.getElementById('semantic-threshold')?.value || 0.7);
        const data = await API.semanticSearch(query, 50, threshold, this.currentFilters);
        return data.results || [];
    }

    /**
     * Natural language search with LLM parsing
     */
    static async naturalLanguageSearch(query) {
        const data = await API.naturalLanguageSearch(query, this.currentFilters);

        // Show parsed query interpretation
        if (data.parsed_query) {
            this.showParsedQuery(data.parsed_query);
        }

        return data.results || [];
    }

    /**
     * Keyword-based search (fallback/default)
     */
    static async keywordSearch(query) {
        const data = await API.keywordSearch(query, this.currentFilters);
        return data.results || [];
    }

    /**
     * Display search results with relevance scoring
     */
    static displayResults(results, query) {
        const container = document.getElementById('search-results');

        if (!results || results.length === 0) {
            container.innerHTML = `
                <div class="no-results">
                    <div style="font-size: 48px; margin-bottom: 16px;">🔍</div>
                    <div style="font-size: 18px; margin-bottom: 8px;">No results found</div>
                    <div style="color: #888;">Try different keywords or adjust your filters</div>
                </div>
            `;
            return;
        }

        // Sort by relevance score
        results.sort((a, b) => (b.relevance || 0) - (a.relevance || 0));

        // Build results HTML
        let html = `
            <div class="search-results-header">
                <div class="results-count">
                    <strong>${results.length}</strong> results for "<em>${this.escapeHtml(query)}</em>"
                </div>
                <div class="results-actions">
                    <button class="btn-small" onclick="EnhancedSearch.exportResults('json')">
                        📄 Export JSON
                    </button>
                    <button class="btn-small" onclick="EnhancedSearch.exportResults('csv')">
                        📊 Export CSV
                    </button>
                </div>
            </div>
            <div class="search-results-list">
        `;

        results.forEach((result, index) => {
            html += this.renderResultCard(result, query, index);
        });

        html += '</div>';

        container.innerHTML = html;
    }

    /**
     * Render a single result card with relevance visualization
     */
    static renderResultCard(result, query, index) {
        const relevance = result.relevance || 0;
        const relevanceColor = this.getRelevanceColor(relevance);
        const typeIcon = this.getTypeIcon(result.type);

        // Calculate score breakdown
        const scores = result.scores || {
            keyword: relevance * 0.4,
            semantic: relevance * 0.3,
            confidence: relevance * 0.15,
            recency: relevance * 0.1,
            investigation: relevance * 0.05
        };

        return `
            <div class="search-result" data-id="${result.id}" data-index="${index}">
                <div class="result-header">
                    <div class="result-type-icon">${typeIcon}</div>
                    <h4 class="result-title">${this.highlightMatches(result.title || result.text, query)}</h4>
                    <div class="relevance-badge" style="background: ${relevanceColor}">
                        ${relevance}% match
                    </div>
                </div>

                <div class="result-meta">
                    <span class="meta-item"><strong>Type:</strong> ${result.type}</span>
                    ${result.confidence ? `<span class="meta-item"><strong>Confidence:</strong> ${result.confidence}%</span>` : ''}
                    ${result.created_at ? `<span class="meta-item"><strong>Date:</strong> ${this.formatDate(result.created_at)}</span>` : ''}
                    ${result.author ? `<span class="meta-item"><strong>Author:</strong> ${result.author}</span>` : ''}
                </div>

                <div class="relevance-breakdown">
                    <div class="breakdown-bar">
                        <div class="bar-segment keyword" style="width: ${scores.keyword}%"
                             title="Keyword: ${scores.keyword.toFixed(1)}%"></div>
                        <div class="bar-segment semantic" style="width: ${scores.semantic}%"
                             title="Semantic: ${scores.semantic.toFixed(1)}%"></div>
                        <div class="bar-segment confidence" style="width: ${scores.confidence}%"
                             title="Confidence: ${scores.confidence.toFixed(1)}%"></div>
                    </div>
                    <div class="breakdown-legend">
                        <span class="legend-item keyword">Keywords</span>
                        <span class="legend-item semantic">Semantic</span>
                        <span class="legend-item confidence">Confidence</span>
                    </div>
                </div>

                <div class="result-content">
                    ${this.highlightMatches(result.snippet || result.text || '', query)}
                </div>

                <div class="result-actions">
                    <button class="btn-action" onclick="EnhancedSearch.viewResult('${result.id}')">
                        👁️ View
                    </button>
                    <button class="btn-action" onclick="EnhancedSearch.investigateResult('${result.id}')">
                        🔬 Investigate
                    </button>
                    ${result.type === 'claim' ? `
                        <button class="btn-action" onclick="EnhancedSearch.findRelated('${result.id}')">
                            🔗 Related
                        </button>
                    ` : ''}
                </div>
            </div>
        `;
    }

    /**
     * Show preview dropdown with quick results
     */
    static showPreview(results, query) {
        const preview = document.getElementById('search-preview');
        if (!preview) return;

        const count = results.length;

        let html = `
            <div class="preview-header">
                <span>Quick Results</span>
                <span id="preview-count">${count} found</span>
            </div>
            <div class="preview-results">
        `;

        if (count === 0) {
            html += '<div class="preview-empty">No quick matches</div>';
        } else {
            results.forEach(result => {
                html += this.renderPreviewCard(result, query);
            });
        }

        html += `
            </div>
            <div class="preview-footer">
                <button onclick="EnhancedSearch.showAllResults()">See All Results</button>
            </div>
        `;

        preview.innerHTML = html;
        preview.style.display = 'block';
    }

    /**
     * Render preview card (mini version)
     */
    static renderPreviewCard(result, query) {
        const typeIcon = this.getTypeIcon(result.type);
        const relevance = result.relevance || 0;

        return `
            <div class="preview-card" onclick="EnhancedSearch.selectResult('${result.id}')">
                <div class="preview-type">${typeIcon} ${result.type}</div>
                <div class="preview-title">${this.highlightMatches(result.title || result.text, query)}</div>
                <div class="preview-snippet">${this.highlightMatches(result.snippet || '', query)}</div>
                <div class="preview-meta">
                    <span class="relevance">Relevance: ${relevance}%</span>
                </div>
            </div>
        `;
    }

    /**
     * Hide preview dropdown
     */
    static hidePreview() {
        const preview = document.getElementById('search-preview');
        if (preview) {
            preview.style.display = 'none';
        }
    }

    /**
     * Show all results from preview
     */
    static showAllResults() {
        this.hidePreview();
        this.executeSearch();
    }

    /**
     * Select a result from preview
     */
    static selectResult(resultId) {
        this.hidePreview();
        this.viewResult(resultId);
    }

    /**
     * Apply faceted filters
     */
    static applyFilters() {
        this.currentFilters = {
            types: this.getCheckedTypes(),
            dateFrom: document.getElementById('date-from').value,
            dateTo: document.getElementById('date-to').value,
            confidenceMin: parseInt(document.getElementById('confidence-min').value),
            investigationMin: parseInt(document.getElementById('investigation-min').value),
            authors: this.getSelectedAuthors()
        };

        console.log('[EnhancedSearch] Filters applied:', this.currentFilters);

        // Re-run search if there's a query
        if (this.currentQuery) {
            this.executeSearch();
        }
    }

    /**
     * Reset filters to defaults
     */
    static resetFilters() {
        this.currentFilters = {
            types: ['claim', 'document', 'evidence'],
            dateFrom: '',
            dateTo: '',
            confidenceMin: 0,
            investigationMin: 0,
            authors: []
        };

        // Reset UI
        document.querySelectorAll('.filter-section input[type="checkbox"]').forEach(cb => {
            cb.checked = this.currentFilters.types.includes(cb.value);
        });

        document.getElementById('date-from').value = '';
        document.getElementById('date-to').value = '';
        document.getElementById('confidence-min').value = 0;
        document.getElementById('confidence-min-value').textContent = '0%';
        document.getElementById('investigation-min').value = 0;
        document.getElementById('investigation-min-value').textContent = '0%';

        const authorSelect = document.getElementById('author-filter');
        if (authorSelect) {
            Array.from(authorSelect.options).forEach(opt => opt.selected = false);
        }

        console.log('[EnhancedSearch] Filters reset');
    }

    /**
     * Get checked filter types
     */
    static getCheckedTypes() {
        const types = [];
        document.querySelectorAll('.filter-section input[type="checkbox"]:checked').forEach(cb => {
            types.push(cb.value);
        });
        return types;
    }

    /**
     * Get selected authors
     */
    static getSelectedAuthors() {
        const select = document.getElementById('author-filter');
        if (!select) return [];

        return Array.from(select.selectedOptions).map(opt => opt.value);
    }

    /**
     * Toggle advanced filters panel
     */
    static toggleAdvancedFilters() {
        const panel = document.getElementById('faceted-filters');
        if (panel) {
            panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
        }
    }

    /**
     * Set search mode
     */
    static setSearchMode(mode) {
        this.currentMode = mode;

        // Update active button
        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.mode === mode);
        });

        // Show/hide mode-specific UI
        const facetedFilters = document.getElementById('faceted-filters');
        const semanticOptions = document.getElementById('semantic-options');
        const nlExamples = document.getElementById('nl-examples');

        if (facetedFilters) {
            facetedFilters.style.display = mode === 'advanced' ? 'block' : 'none';
        }

        if (semanticOptions) {
            semanticOptions.style.display = mode === 'semantic' ? 'block' : 'none';
        }

        if (nlExamples) {
            nlExamples.style.display = mode === 'natural' ? 'block' : 'none';
        }

        console.log('[EnhancedSearch] Mode set to:', mode);
    }

    /**
     * Add search to history
     */
    static addToHistory(query, filters) {
        const entry = {
            query: query,
            filters: filters,
            timestamp: Date.now(),
            resultCount: this.lastResultCount,
            mode: this.currentMode
        };

        this.searchHistory.unshift(entry);

        // Keep last 50 searches
        this.searchHistory = this.searchHistory.slice(0, 50);

        localStorage.setItem(SEARCH_HISTORY, JSON.stringify(this.searchHistory));

        this.refreshHistoryUI();
    }

    /**
     * Load search history from localStorage
     */
    static loadHistory() {
        try {
            const stored = localStorage.getItem(SEARCH_HISTORY);
            this.searchHistory = stored ? JSON.parse(stored) : [];
        } catch (error) {
            console.error('[EnhancedSearch] Failed to load history:', error);
            this.searchHistory = [];
        }
    }

    /**
     * Save current search
     */
    static saveCurrentSearch() {
        const name = prompt('Name this search:');
        if (!name) return;

        const entry = {
            id: this.generateId(),
            name: name,
            query: this.currentQuery,
            filters: { ...this.currentFilters },
            mode: this.currentMode,
            createdAt: Date.now()
        };

        this.savedSearches.push(entry);
        localStorage.setItem(SAVED_SEARCHES, JSON.stringify(this.savedSearches));

        this.refreshSavedSearchesUI();
        this.showMessage('Search saved successfully', 'success');
    }

    /**
     * Load saved searches from localStorage
     */
    static loadSavedSearches() {
        try {
            const stored = localStorage.getItem(SAVED_SEARCHES);
            this.savedSearches = stored ? JSON.parse(stored) : [];
        } catch (error) {
            console.error('[EnhancedSearch] Failed to load saved searches:', error);
            this.savedSearches = [];
        }
    }

    /**
     * Load a saved search
     */
    static loadSavedSearch(id) {
        const saved = this.savedSearches.find(s => s.id === id);
        if (!saved) return;

        // Restore query and filters
        document.getElementById('search-input').value = saved.query;
        this.currentQuery = saved.query;
        this.currentFilters = { ...saved.filters };
        this.currentMode = saved.mode || 'simple';

        this.restoreFiltersToUI();
        this.setSearchMode(this.currentMode);
        this.executeSearch();
    }

    /**
     * Delete a saved search
     */
    static deleteSavedSearch(id) {
        this.savedSearches = this.savedSearches.filter(s => s.id !== id);
        localStorage.setItem(SAVED_SEARCHES, JSON.stringify(this.savedSearches));
        this.refreshSavedSearchesUI();
    }

    /**
     * Restore filters to UI controls
     */
    static restoreFiltersToUI() {
        // Type checkboxes
        document.querySelectorAll('.filter-section input[type="checkbox"]').forEach(cb => {
            cb.checked = this.currentFilters.types.includes(cb.value);
        });

        // Date range
        document.getElementById('date-from').value = this.currentFilters.dateFrom || '';
        document.getElementById('date-to').value = this.currentFilters.dateTo || '';

        // Confidence
        document.getElementById('confidence-min').value = this.currentFilters.confidenceMin || 0;
        document.getElementById('confidence-min-value').textContent = (this.currentFilters.confidenceMin || 0) + '%';

        // Investigation
        document.getElementById('investigation-min').value = this.currentFilters.investigationMin || 0;
        document.getElementById('investigation-min-value').textContent = (this.currentFilters.investigationMin || 0) + '%';

        // Authors
        const authorSelect = document.getElementById('author-filter');
        if (authorSelect && this.currentFilters.authors) {
            Array.from(authorSelect.options).forEach(opt => {
                opt.selected = this.currentFilters.authors.includes(opt.value);
            });
        }
    }

    /**
     * Refresh history UI
     */
    static refreshHistoryUI() {
        const container = document.getElementById('history-list');
        if (!container) return;

        if (this.searchHistory.length === 0) {
            container.innerHTML = '<div class="empty-state">No search history</div>';
            return;
        }

        let html = '';
        this.searchHistory.slice(0, 10).forEach(entry => {
            html += `
                <div class="history-item" onclick="EnhancedSearch.loadHistoryItem(${entry.timestamp})">
                    <div class="history-query">${this.escapeHtml(entry.query)}</div>
                    <div class="history-meta">
                        ${this.formatRelativeTime(entry.timestamp)} • ${entry.resultCount} results
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
    }

    /**
     * Load a history item
     */
    static loadHistoryItem(timestamp) {
        const entry = this.searchHistory.find(h => h.timestamp === timestamp);
        if (!entry) return;

        document.getElementById('search-input').value = entry.query;
        this.currentQuery = entry.query;
        this.currentFilters = { ...entry.filters };
        this.currentMode = entry.mode || 'simple';

        this.restoreFiltersToUI();
        this.setSearchMode(this.currentMode);
        this.executeSearch();
    }

    /**
     * Refresh saved searches UI
     */
    static refreshSavedSearchesUI() {
        const container = document.getElementById('saved-searches-list');
        if (!container) return;

        if (this.savedSearches.length === 0) {
            container.innerHTML = '<div class="empty-state">No saved searches</div>';
            return;
        }

        let html = '';
        this.savedSearches.forEach(saved => {
            html += `
                <div class="saved-search-item">
                    <div class="saved-search-name" onclick="EnhancedSearch.loadSavedSearch('${saved.id}')">
                        ⭐ ${this.escapeHtml(saved.name)}
                    </div>
                    <button class="btn-delete" onclick="EnhancedSearch.deleteSavedSearch('${saved.id}')">
                        🗑️
                    </button>
                </div>
            `;
        });

        container.innerHTML = html;
    }

    /**
     * Populate author filter dropdown
     */
    static async populateAuthorFilter() {
        try {
            const data = await API.getAuthors();
            const authors = data.authors || [];

            const select = document.getElementById('author-filter');
            if (!select) return;

            select.innerHTML = authors.map(author =>
                `<option value="${this.escapeHtml(author)}">${this.escapeHtml(author)}</option>`
            ).join('');
        } catch (error) {
            console.error('[EnhancedSearch] Failed to populate authors:', error);
        }
    }

    /**
     * Export search results
     */
    static exportResults(format = 'json') {
        if (!this.currentResults || this.currentResults.length === 0) {
            this.showMessage('No results to export', 'warning');
            return;
        }

        if (format === 'json') {
            this.downloadJSON(this.currentResults, `search-results-${Date.now()}.json`);
        } else if (format === 'csv') {
            this.downloadCSV(this.currentResults, `search-results-${Date.now()}.csv`);
        } else if (format === 'markdown') {
            this.downloadMarkdown(this.currentResults, `search-results-${Date.now()}.md`);
        }
    }

    /**
     * Download JSON file
     */
    static downloadJSON(data, filename) {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        this.downloadBlob(blob, filename);
    }

    /**
     * Download CSV file
     */
    static downloadCSV(data, filename) {
        const headers = ['ID', 'Type', 'Title', 'Relevance', 'Confidence', 'Created'];
        const rows = data.map(r => [
            r.id,
            r.type,
            (r.title || r.text || '').replace(/"/g, '""'),
            r.relevance || 0,
            r.confidence || 0,
            r.created_at || ''
        ]);

        const csv = [headers, ...rows]
            .map(row => row.map(cell => `"${cell}"`).join(','))
            .join('\n');

        const blob = new Blob([csv], { type: 'text/csv' });
        this.downloadBlob(blob, filename);
    }

    /**
     * Download Markdown file
     */
    static downloadMarkdown(data, filename) {
        let md = `# Search Results\n\n`;
        md += `**Query:** ${this.currentQuery}\n`;
        md += `**Results:** ${data.length}\n`;
        md += `**Date:** ${new Date().toLocaleString()}\n\n`;
        md += `---\n\n`;

        data.forEach((result, i) => {
            md += `## ${i + 1}. ${result.title || result.text}\n\n`;
            md += `- **Type:** ${result.type}\n`;
            md += `- **Relevance:** ${result.relevance || 0}%\n`;
            if (result.confidence) md += `- **Confidence:** ${result.confidence}%\n`;
            if (result.created_at) md += `- **Created:** ${result.created_at}\n`;
            md += `\n${result.snippet || result.text || ''}\n\n`;
            md += `---\n\n`;
        });

        const blob = new Blob([md], { type: 'text/markdown' });
        this.downloadBlob(blob, filename);
    }

    /**
     * Download blob as file
     */
    static downloadBlob(blob, filename) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    /**
     * View a search result
     */
    static viewResult(resultId) {
        // Integrate with existing property viewer
        if (window.PropertyViewer) {
            PropertyViewer.viewNode(resultId);
        } else {
            window.location.hash = `#view/${resultId}`;
        }
    }

    /**
     * Investigate a search result
     */
    static async investigateResult(resultId) {
        try {
            await API.investigateClaim(resultId);
            this.showMessage('Investigation launched', 'success');
        } catch (error) {
            this.showMessage('Investigation failed: ' + error.message, 'error');
        }
    }

    /**
     * Find related items
     */
    static async findRelated(resultId) {
        try {
            const data = await API.getRelatedItems(resultId);
            this.displayResults(data.results, 'Related items');
        } catch (error) {
            this.showMessage('Failed to find related items: ' + error.message, 'error');
        }
    }

    /**
     * Highlight query matches in text
     */
    static highlightMatches(text, query) {
        if (!text || !query) return text || '';

        const escapedText = this.escapeHtml(text);
        const queryTerms = query.split(/\s+/).filter(t => t.length > 2);

        let highlighted = escapedText;
        queryTerms.forEach(term => {
            const regex = new RegExp(`(${this.escapeRegex(term)})`, 'gi');
            highlighted = highlighted.replace(regex, '<mark>$1</mark>');
        });

        return highlighted;
    }

    /**
     * Get relevance color
     */
    static getRelevanceColor(relevance) {
        if (relevance >= 90) return '#4CAF50';  // Green - Excellent
        if (relevance >= 70) return '#2196F3';  // Blue - Good
        if (relevance >= 50) return '#FF9800';  // Orange - Fair
        return '#F44336';  // Red - Poor
    }

    /**
     * Get type icon
     */
    static getTypeIcon(type) {
        const icons = {
            'claim': '📋',
            'document': '📄',
            'evidence': '🔬',
            'super_claim': '⭐',
            'sub_claim': '📌'
        };
        return icons[type] || '📝';
    }

    /**
     * Format date
     */
    static formatDate(dateStr) {
        try {
            const date = new Date(dateStr);
            return date.toLocaleDateString();
        } catch {
            return dateStr;
        }
    }

    /**
     * Format relative time
     */
    static formatRelativeTime(timestamp) {
        const now = Date.now();
        const diff = now - timestamp;

        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);

        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        if (days < 7) return `${days}d ago`;
        return new Date(timestamp).toLocaleDateString();
    }

    /**
     * Show message
     */
    static showMessage(message, type = 'info') {
        console.log(`[EnhancedSearch] ${type.toUpperCase()}: ${message}`);
        // TODO: Integrate with existing toast/notification system
        alert(message);
    }

    /**
     * Show loading indicator
     */
    static showLoading() {
        const container = document.getElementById('search-results');
        if (container) {
            container.innerHTML = `
                <div class="loading-state">
                    <div class="spinner"></div>
                    <div>Searching...</div>
                </div>
            `;
        }
    }

    /**
     * Hide loading indicator
     */
    static hideLoading() {
        // Loading is replaced by results
    }

    /**
     * Show searching indicator in preview
     */
    static showSearching() {
        const preview = document.getElementById('search-preview');
        if (preview) {
            preview.innerHTML = '<div class="preview-loading">Searching...</div>';
            preview.style.display = 'block';
        }
    }

    /**
     * Show parsed NL query
     */
    static showParsedQuery(parsed) {
        console.log('[EnhancedSearch] Parsed query:', parsed);
        // TODO: Display parsed query interpretation in UI
    }

    /**
     * Generate unique ID
     */
    static generateId() {
        return 'search_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    /**
     * Escape HTML
     */
    static escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Escape regex
     */
    static escapeRegex(text) {
        return text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        console.log('[EnhancedSearch] DOM ready, initializing...');
        setTimeout(() => EnhancedSearch.init(), 100);
    });
} else {
    console.log('[EnhancedSearch] DOM already loaded, initializing...');
    setTimeout(() => EnhancedSearch.init(), 100);
}
