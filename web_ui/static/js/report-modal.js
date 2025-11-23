/**
 * Report Modal UI
 * User interface for the comprehensive reporting system
 */

const ReportModal = {
    modal: null,
    currentTab: 'export',

    /**
     * Initialize the report modal
     */
    initialize() {
        console.log('[ReportModal] Initializing...');
        this.createModal();
        this.attachEventListeners();
    },

    /**
     * Create modal HTML structure
     */
    createModal() {
        const modalHTML = `
            <div id="report-modal" class="modal" style="display: none;">
                <div class="modal-content report-modal-content">
                    <div class="modal-header">
                        <h2>📄 Reports & Export</h2>
                        <button class="modal-close" onclick="ReportModal.hide()">&times;</button>
                    </div>

                    <div class="modal-tabs">
                        <button class="tab-button active" data-tab="export">Export</button>
                        <button class="tab-button" data-tab="templates">Templates</button>
                        <button class="tab-button" data-tab="schedule">Schedule</button>
                        <button class="tab-button" data-tab="history">History</button>
                    </div>

                    <div class="modal-body">
                        <!-- Export Tab -->
                        <div class="tab-content active" data-tab="export">
                            <h3>Quick Export</h3>
                            <p>Generate and download reports in various formats</p>

                            <div class="export-options">
                                <div class="export-card" onclick="ReportModal.exportPDF()">
                                    <div class="export-icon">📕</div>
                                    <h4>PDF Report</h4>
                                    <p>Professional PDF with graphs, statistics, and analysis</p>
                                    <button class="btn btn-primary">Generate PDF</button>
                                </div>

                                <div class="export-card" onclick="ReportModal.exportMarkdown()">
                                    <div class="export-icon">📝</div>
                                    <h4>Markdown</h4>
                                    <p>Markdown format for documentation and version control</p>
                                    <button class="btn btn-primary">Export Markdown</button>
                                </div>

                                <div class="export-card" onclick="ReportModal.exportBibTeX()">
                                    <div class="export-icon">📚</div>
                                    <h4>BibTeX Citations</h4>
                                    <p>BibTeX entries for all documents and references</p>
                                    <button class="btn btn-primary">Export BibTeX</button>
                                </div>

                                <div class="export-card" onclick="ReportModal.exportJSON()">
                                    <div class="export-icon">💾</div>
                                    <h4>JSON Data</h4>
                                    <p>Raw graph data in JSON format</p>
                                    <button class="btn btn-primary">Export JSON</button>
                                </div>
                            </div>

                            <div class="export-options-advanced">
                                <h4>Export Options</h4>
                                <label>
                                    <input type="checkbox" id="include-graph-snapshot" checked>
                                    Include visual graph snapshot
                                </label>
                                <label>
                                    <input type="checkbox" id="include-documents" checked>
                                    Include document list
                                </label>
                                <label>
                                    <input type="checkbox" id="include-claims" checked>
                                    Include claim analysis
                                </label>
                                <label>
                                    <input type="checkbox" id="include-evidence" checked>
                                    Include evidence metrics
                                </label>
                            </div>
                        </div>

                        <!-- Templates Tab -->
                        <div class="tab-content" data-tab="templates">
                            <h3>Report Templates</h3>
                            <p>Use pre-built templates or create your own</p>

                            <div class="template-list" id="template-list">
                                <!-- Populated dynamically -->
                            </div>

                            <button class="btn btn-secondary" onclick="ReportModal.showTemplateEditor()">
                                ➕ Create Custom Template
                            </button>

                            <!-- Template Editor (hidden by default) -->
                            <div id="template-editor" style="display: none;">
                                <h4>Template Editor</h4>
                                <input type="text" id="template-name" placeholder="Template Name" class="form-input">
                                <textarea id="template-description" placeholder="Description" class="form-input" rows="2"></textarea>
                                <textarea id="template-content" placeholder="Template content (Handlebars syntax)" class="form-input template-textarea" rows="15"></textarea>

                                <div class="template-help">
                                    <h5>Available Variables:</h5>
                                    <code>{{project_name}}, {{document_count}}, {{claim_count}}, {{avg_confidence}}</code>
                                </div>

                                <div class="button-group">
                                    <button class="btn btn-primary" onclick="ReportModal.saveTemplate()">Save Template</button>
                                    <button class="btn btn-secondary" onclick="ReportModal.hideTemplateEditor()">Cancel</button>
                                </div>
                            </div>
                        </div>

                        <!-- Schedule Tab -->
                        <div class="tab-content" data-tab="schedule">
                            <h3>Scheduled Exports</h3>
                            <p>Automate report generation on a schedule</p>

                            <div class="schedule-form">
                                <h4>Create New Schedule</h4>

                                <label>Export Format</label>
                                <select id="schedule-format" class="form-input">
                                    <option value="pdf">PDF Report</option>
                                    <option value="markdown">Markdown</option>
                                    <option value="bibtex">BibTeX</option>
                                </select>

                                <label>Schedule Type</label>
                                <select id="schedule-type" class="form-input" onchange="ReportModal.updateScheduleFields()">
                                    <option value="interval">Interval (Every X hours)</option>
                                    <option value="cron">Cron Expression</option>
                                    <option value="daily">Daily</option>
                                    <option value="weekly">Weekly</option>
                                    <option value="monthly">Monthly</option>
                                </select>

                                <div id="schedule-interval-fields" class="schedule-fields">
                                    <label>Interval (hours)</label>
                                    <input type="number" id="schedule-interval-hours" class="form-input" value="24" min="1">
                                </div>

                                <div id="schedule-cron-fields" class="schedule-fields" style="display: none;">
                                    <label>Cron Expression</label>
                                    <input type="text" id="schedule-cron-expression" class="form-input" placeholder="0 0 * * *">
                                    <small>Example: "0 0 * * *" = Daily at midnight</small>
                                </div>

                                <label>Export Destination</label>
                                <input type="text" id="schedule-export-path" class="form-input" placeholder="Optional: /path/to/export">

                                <label>Email Delivery (Optional)</label>
                                <input type="email" id="schedule-email" class="form-input" placeholder="your@email.com">

                                <button class="btn btn-primary" onclick="ReportModal.createSchedule()">Create Schedule</button>
                            </div>

                            <div class="schedule-list" id="schedule-list">
                                <h4>Active Schedules</h4>
                                <!-- Populated dynamically -->
                            </div>
                        </div>

                        <!-- History Tab -->
                        <div class="tab-content" data-tab="history">
                            <h3>Report History</h3>
                            <p>Previously generated reports</p>

                            <div class="history-list" id="history-list">
                                <!-- Populated dynamically -->
                            </div>
                        </div>
                    </div>

                    <div class="modal-footer">
                        <div class="progress-container" id="report-progress" style="display: none;">
                            <div class="progress-bar">
                                <div class="progress-fill" id="report-progress-fill"></div>
                            </div>
                            <div class="progress-text" id="report-progress-text">Generating report...</div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add to document
        document.body.insertAdjacentHTML('beforeend', modalHTML);

        // Add styles
        this.addStyles();
    },

    /**
     * Add modal styles
     */
    addStyles() {
        const styleHTML = `
            <style>
                .report-modal-content {
                    max-width: 800px;
                    max-height: 90vh;
                    overflow-y: auto;
                }

                .modal-tabs {
                    display: flex;
                    border-bottom: 2px solid #ddd;
                    gap: 10px;
                    padding: 0 20px;
                    background: #f5f5f5;
                }

                .tab-button {
                    padding: 12px 20px;
                    border: none;
                    background: transparent;
                    cursor: pointer;
                    font-size: 14px;
                    font-weight: 500;
                    color: #666;
                    border-bottom: 3px solid transparent;
                    transition: all 0.2s;
                }

                .tab-button:hover {
                    color: #2196F3;
                }

                .tab-button.active {
                    color: #2196F3;
                    border-bottom-color: #2196F3;
                }

                .tab-content {
                    display: none;
                    padding: 20px;
                }

                .tab-content.active {
                    display: block;
                }

                .export-options {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                    gap: 15px;
                    margin: 20px 0;
                }

                .export-card {
                    background: #fff;
                    border: 2px solid #e0e0e0;
                    border-radius: 8px;
                    padding: 20px;
                    text-align: center;
                    cursor: pointer;
                    transition: all 0.2s;
                }

                .export-card:hover {
                    border-color: #2196F3;
                    box-shadow: 0 4px 12px rgba(33, 150, 243, 0.2);
                    transform: translateY(-2px);
                }

                .export-icon {
                    font-size: 48px;
                    margin-bottom: 10px;
                }

                .export-card h4 {
                    margin: 10px 0 5px;
                    font-size: 16px;
                    color: #333;
                }

                .export-card p {
                    font-size: 12px;
                    color: #666;
                    margin-bottom: 15px;
                }

                .export-options-advanced {
                    background: #f5f5f5;
                    padding: 15px;
                    border-radius: 6px;
                    margin-top: 20px;
                }

                .export-options-advanced label {
                    display: block;
                    margin: 8px 0;
                    font-size: 14px;
                }

                .template-list, .schedule-list, .history-list {
                    margin: 20px 0;
                }

                .template-item, .schedule-item, .history-item {
                    background: #f9f9f9;
                    border: 1px solid #e0e0e0;
                    border-radius: 6px;
                    padding: 15px;
                    margin-bottom: 10px;
                }

                .template-item h4, .schedule-item h4, .history-item h4 {
                    margin: 0 0 5px;
                    font-size: 16px;
                }

                .template-item p, .schedule-item p, .history-item p {
                    margin: 5px 0;
                    font-size: 13px;
                    color: #666;
                }

                .template-textarea {
                    font-family: 'Courier New', monospace;
                    font-size: 13px;
                }

                .template-help {
                    background: #e3f2fd;
                    padding: 10px;
                    border-radius: 4px;
                    margin: 10px 0;
                }

                .template-help h5 {
                    margin: 0 0 5px;
                    font-size: 13px;
                }

                .template-help code {
                    font-size: 12px;
                    color: #1976D2;
                }

                .schedule-form {
                    background: #f9f9f9;
                    padding: 20px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                }

                .schedule-form label {
                    display: block;
                    margin: 15px 0 5px;
                    font-weight: 500;
                    font-size: 14px;
                }

                .schedule-fields {
                    margin: 10px 0;
                }

                .form-input {
                    width: 100%;
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    font-size: 14px;
                    margin-bottom: 10px;
                }

                .button-group {
                    display: flex;
                    gap: 10px;
                    margin-top: 15px;
                }

                .progress-container {
                    margin-top: 15px;
                }

                .progress-bar {
                    width: 100%;
                    height: 8px;
                    background: #e0e0e0;
                    border-radius: 4px;
                    overflow: hidden;
                }

                .progress-fill {
                    height: 100%;
                    background: linear-gradient(90deg, #2196F3, #1976D2);
                    transition: width 0.3s;
                    width: 0%;
                }

                .progress-text {
                    text-align: center;
                    margin-top: 8px;
                    font-size: 13px;
                    color: #666;
                }

                .btn {
                    padding: 10px 20px;
                    border: none;
                    border-radius: 4px;
                    font-size: 14px;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.2s;
                }

                .btn-primary {
                    background: #2196F3;
                    color: white;
                }

                .btn-primary:hover {
                    background: #1976D2;
                }

                .btn-secondary {
                    background: #757575;
                    color: white;
                }

                .btn-secondary:hover {
                    background: #616161;
                }

                .btn-danger {
                    background: #f44336;
                    color: white;
                }

                .btn-danger:hover {
                    background: #d32f2f;
                }
            </style>
        `;

        document.head.insertAdjacentHTML('beforeend', styleHTML);
    },

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Tab switching
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', (e) => {
                const tab = e.target.dataset.tab;
                this.switchTab(tab);
            });
        });

        // Close modal on background click
        document.getElementById('report-modal').addEventListener('click', (e) => {
            if (e.target.id === 'report-modal') {
                this.hide();
            }
        });
    },

    /**
     * Show the modal
     */
    show() {
        document.getElementById('report-modal').style.display = 'flex';
        this.refreshTemplateList();
        this.refreshScheduleList();
        this.refreshHistoryList();
    },

    /**
     * Hide the modal
     */
    hide() {
        document.getElementById('report-modal').style.display = 'none';
    },

    /**
     * Switch tab
     */
    switchTab(tabName) {
        this.currentTab = tabName;

        // Update button states
        document.querySelectorAll('.tab-button').forEach(button => {
            button.classList.toggle('active', button.dataset.tab === tabName);
        });

        // Update content visibility
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.toggle('active', content.dataset.tab === tabName);
        });

        // Refresh content for active tab
        if (tabName === 'templates') {
            this.refreshTemplateList();
        } else if (tabName === 'schedule') {
            this.refreshScheduleList();
        } else if (tabName === 'history') {
            this.refreshHistoryList();
        }
    },

    /**
     * Export PDF
     */
    async exportPDF() {
        try {
            this.showProgress('Generating PDF report...');

            const options = this.getExportOptions();
            await ReportGenerator.generatePDFReport(options);

            this.hideProgress();
        } catch (error) {
            this.hideProgress();
            console.error('[ReportModal] PDF export failed:', error);
        }
    },

    /**
     * Export Markdown
     */
    async exportMarkdown() {
        try {
            this.showProgress('Exporting Markdown...');

            const options = this.getExportOptions();
            await ReportGenerator.exportMarkdown(options);

            this.hideProgress();
        } catch (error) {
            this.hideProgress();
            console.error('[ReportModal] Markdown export failed:', error);
        }
    },

    /**
     * Export BibTeX
     */
    async exportBibTeX() {
        try {
            this.showProgress('Exporting BibTeX citations...');

            const options = this.getExportOptions();
            await ReportGenerator.exportBibTeX(options);

            this.hideProgress();
        } catch (error) {
            this.hideProgress();
            console.error('[ReportModal] BibTeX export failed:', error);
        }
    },

    /**
     * Export JSON
     */
    async exportJSON() {
        try {
            this.showProgress('Exporting JSON data...');

            if (window.ExportManager) {
                await ExportManager.exportAsJSON();
            }

            this.hideProgress();
        } catch (error) {
            this.hideProgress();
            console.error('[ReportModal] JSON export failed:', error);
        }
    },

    /**
     * Get export options from UI
     */
    getExportOptions() {
        return {
            includeGraphSnapshot: document.getElementById('include-graph-snapshot')?.checked,
            includeDocuments: document.getElementById('include-documents')?.checked,
            includeClaims: document.getElementById('include-claims')?.checked,
            includeEvidence: document.getElementById('include-evidence')?.checked,
            projectId: window.currentProject
        };
    },

    /**
     * Show progress indicator
     */
    showProgress(text) {
        const progressContainer = document.getElementById('report-progress');
        const progressText = document.getElementById('report-progress-text');
        const progressFill = document.getElementById('report-progress-fill');

        progressContainer.style.display = 'block';
        progressText.textContent = text;
        progressFill.style.width = '70%';
    },

    /**
     * Hide progress indicator
     */
    hideProgress() {
        const progressContainer = document.getElementById('report-progress');
        progressContainer.style.display = 'none';
    },

    /**
     * Refresh template list
     */
    refreshTemplateList() {
        const container = document.getElementById('template-list');
        const templates = ReportGenerator.templates;

        let html = '';

        for (const [key, template] of Object.entries(templates)) {
            html += `
                <div class="template-item">
                    <h4>${template.name}</h4>
                    <p>${template.description}</p>
                    <div class="button-group">
                        <button class="btn btn-primary" onclick="ReportModal.useTemplate('${key}')">Use Template</button>
                        ${template.custom ? `<button class="btn btn-danger" onclick="ReportModal.deleteTemplate('${key}')">Delete</button>` : ''}
                    </div>
                </div>
            `;
        }

        container.innerHTML = html || '<p>No templates available</p>';
    },

    /**
     * Use template
     */
    async useTemplate(templateName) {
        try {
            this.showProgress(`Generating report from template: ${templateName}...`);

            await ReportGenerator.generateFromTemplate(templateName, this.getExportOptions());

            this.hideProgress();
        } catch (error) {
            this.hideProgress();
            console.error('[ReportModal] Template generation failed:', error);
        }
    },

    /**
     * Show template editor
     */
    showTemplateEditor() {
        document.getElementById('template-editor').style.display = 'block';
    },

    /**
     * Hide template editor
     */
    hideTemplateEditor() {
        document.getElementById('template-editor').style.display = 'none';
        document.getElementById('template-name').value = '';
        document.getElementById('template-description').value = '';
        document.getElementById('template-content').value = '';
    },

    /**
     * Save template
     */
    saveTemplate() {
        const name = document.getElementById('template-name').value.trim();
        const description = document.getElementById('template-description').value.trim();
        const content = document.getElementById('template-content').value.trim();

        if (!name || !content) {
            alert('Please provide template name and content');
            return;
        }

        const templateData = {
            name,
            description,
            template: content,
            custom: true,
            sections: ['all']
        };

        ReportGenerator.saveTemplate(name.toLowerCase().replace(/\s+/g, '_'), templateData);

        this.hideTemplateEditor();
        this.refreshTemplateList();
    },

    /**
     * Delete template
     */
    deleteTemplate(templateName) {
        if (confirm('Are you sure you want to delete this template?')) {
            ReportGenerator.deleteTemplate(templateName);
            this.refreshTemplateList();
        }
    },

    /**
     * Update schedule fields based on type
     */
    updateScheduleFields() {
        const scheduleType = document.getElementById('schedule-type').value;

        document.getElementById('schedule-interval-fields').style.display = 'none';
        document.getElementById('schedule-cron-fields').style.display = 'none';

        if (scheduleType === 'interval') {
            document.getElementById('schedule-interval-fields').style.display = 'block';
        } else if (scheduleType === 'cron') {
            document.getElementById('schedule-cron-fields').style.display = 'block';
        }
    },

    /**
     * Create schedule
     */
    async createSchedule() {
        const format = document.getElementById('schedule-format').value;
        const scheduleType = document.getElementById('schedule-type').value;
        const email = document.getElementById('schedule-email').value;
        const exportPath = document.getElementById('schedule-export-path').value;

        let scheduleConfig = {};

        if (scheduleType === 'interval') {
            const hours = parseInt(document.getElementById('schedule-interval-hours').value);
            scheduleConfig.interval_seconds = hours * 3600;
        } else if (scheduleType === 'cron') {
            scheduleConfig.expression = document.getElementById('schedule-cron-expression').value;
        } else if (scheduleType === 'daily') {
            scheduleConfig.expression = '0 0 * * *';
            scheduleConfig = { ...scheduleConfig };
        } else if (scheduleType === 'weekly') {
            scheduleConfig.expression = '0 0 * * 0';
        } else if (scheduleType === 'monthly') {
            scheduleConfig.expression = '0 0 1 * *';
        }

        try {
            this.showProgress('Creating schedule...');

            await ReportGenerator.scheduleExport({
                schedule_type: scheduleType === 'interval' ? 'interval' : 'cron',
                schedule_config: scheduleConfig,
                export_format: format,
                email,
                export_path,
                project_id: window.currentProject
            });

            this.hideProgress();
            this.refreshScheduleList();

        } catch (error) {
            this.hideProgress();
            console.error('[ReportModal] Failed to create schedule:', error);
        }
    },

    /**
     * Refresh schedule list
     */
    async refreshScheduleList() {
        const container = document.getElementById('schedule-list');

        try {
            const schedules = await ReportGenerator.getScheduledExports();

            let html = '';

            schedules.forEach(schedule => {
                html += `
                    <div class="schedule-item">
                        <h4>${schedule.export_format.toUpperCase()} Report</h4>
                        <p>Type: ${schedule.schedule_type}</p>
                        <p>Status: ${schedule.enabled ? 'Active' : 'Disabled'}</p>
                        <div class="button-group">
                            <button class="btn btn-danger" onclick="ReportModal.cancelSchedule('${schedule.schedule_id}')">Cancel</button>
                        </div>
                    </div>
                `;
            });

            container.innerHTML = html || '<p>No scheduled exports</p>';

        } catch (error) {
            container.innerHTML = '<p>Failed to load schedules</p>';
        }
    },

    /**
     * Cancel schedule
     */
    async cancelSchedule(scheduleId) {
        if (confirm('Are you sure you want to cancel this schedule?')) {
            try {
                await ReportGenerator.cancelScheduledExport(scheduleId);
                this.refreshScheduleList();
            } catch (error) {
                console.error('[ReportModal] Failed to cancel schedule:', error);
            }
        }
    },

    /**
     * Refresh history list
     */
    refreshHistoryList() {
        const container = document.getElementById('history-list');
        const history = ReportGenerator.getReportHistory();

        let html = '';

        history.forEach(report => {
            html += `
                <div class="history-item">
                    <h4>${report.filename}</h4>
                    <p>Type: ${report.type.toUpperCase()}</p>
                    <p>Generated: ${new Date(report.timestamp).toLocaleString()}</p>
                    <p>Project: ${report.project_name}</p>
                    <p>Documents: ${report.document_count} | Claims: ${report.claim_count}</p>
                </div>
            `;
        });

        container.innerHTML = html || '<p>No report history</p>';
    }
};

// Initialize on load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        ReportModal.initialize();
    });
} else {
    ReportModal.initialize();
}
