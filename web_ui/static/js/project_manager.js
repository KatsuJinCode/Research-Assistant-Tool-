/**
 * Project Manager Module
 * Handles project selection, creation, editing, deletion, and switching
 */

const ProjectManager = {
    currentProject: null,
    projects: [],

    /**
     * Initialize the project manager
     */
    async init() {
        console.log('[ProjectManager] Initializing...');

        // Load current project
        await this.loadActiveProject();

        // Load all projects
        await this.loadProjects();

        // Set up event listeners
        this.setupEventListeners();

        console.log('[ProjectManager] Initialized');
    },

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Listen for project switched events from WebSocket
        if (typeof socket !== 'undefined') {
            socket.on('project_switched', (data) => {
                console.log('[ProjectManager] Project switched via WebSocket:', data);
                this.handleProjectSwitched(data);
            });
        }
    },

    /**
     * Load the currently active project
     */
    async loadActiveProject() {
        try {
            const response = await fetch('/api/projects/active');
            const data = await response.json();

            if (data.project) {
                this.currentProject = data.project;
                this.updateHeaderDisplay();
                console.log('[ProjectManager] Active project loaded:', this.currentProject.name);
            } else {
                console.warn('[ProjectManager] No active project found');
            }
        } catch (error) {
            console.error('[ProjectManager] Error loading active project:', error);
        }
    },

    /**
     * Load all projects
     */
    async loadProjects() {
        try {
            const response = await fetch('/api/projects');
            const data = await response.json();

            if (data.projects) {
                this.projects = data.projects;
                console.log(`[ProjectManager] Loaded ${this.projects.length} projects`);
            }
        } catch (error) {
            console.error('[ProjectManager] Error loading projects:', error);
        }
    },

    /**
     * Update the header to show current project
     */
    updateHeaderDisplay() {
        const projectNameElement = document.getElementById('current-project-name');
        if (projectNameElement && this.currentProject) {
            projectNameElement.textContent = this.currentProject.name;
            projectNameElement.style.color = this.currentProject.color || '#fff';
        }

        // Also update the Projects tab selector
        const projectNameTabElement = document.getElementById('current-project-name-tab');
        if (projectNameTabElement && this.currentProject) {
            projectNameTabElement.textContent = this.currentProject.name;
            projectNameTabElement.style.color = this.currentProject.color || '#2196F3';
        }
    },

    /**
     * Open the project management modal
     */
    async openProjectModal() {
        console.log('[ProjectManager] Opening project modal');

        // Reload projects to get latest data
        await this.loadProjects();

        // Create modal if it doesn't exist
        if (!document.getElementById('project-modal')) {
            this.createProjectModal();
        }

        // Populate modal with project list
        this.renderProjectList();

        // Show modal
        const modal = document.getElementById('project-modal');
        modal.style.display = 'flex';
    },

    /**
     * Close the project management modal
     */
    closeProjectModal() {
        const modal = document.getElementById('project-modal');
        if (modal) {
            modal.style.display = 'none';
        }
    },

    /**
     * Create the project management modal HTML
     */
    createProjectModal() {
        const modalHTML = `
            <div id="project-modal" class="modal-overlay" style="display: none;">
                <div class="modal-content project-modal-content">
                    <div class="modal-header">
                        <h2>🗂️ Project Management</h2>
                        <button class="modal-close" onclick="ProjectManager.closeProjectModal()">×</button>
                    </div>

                    <div class="modal-body">
                        <!-- Create New Project Section -->
                        <div class="project-create-section" id="project-create-section">
                            <h3>Create New Project</h3>
                            <div class="form-row">
                                <input type="text" id="new-project-name" placeholder="Project Name" class="form-control" />
                            </div>
                            <div class="form-row">
                                <textarea id="new-project-description" placeholder="Description (optional)" class="form-control" rows="2"></textarea>
                            </div>
                            <div class="form-row">
                                <label class="form-label">Project Color</label>
                                <input type="color" id="new-project-color" value="#2196F3" class="color-picker" />
                            </div>
                            <div class="form-row">
                                <button class="btn btn-primary" onclick="ProjectManager.createProject()">
                                    ➕ Create Project
                                </button>
                                <button class="btn btn-secondary" onclick="ProjectManager.toggleCreateForm()">
                                    Cancel
                                </button>
                            </div>
                        </div>

                        <!-- Project List Section -->
                        <div class="project-list-section">
                            <div class="section-header">
                                <h3>Your Projects</h3>
                                <button class="btn btn-sm btn-primary" onclick="ProjectManager.toggleCreateForm()">
                                    ➕ New Project
                                </button>
                            </div>
                            <div id="project-list" class="project-list">
                                <!-- Projects will be rendered here -->
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);

        // Hide create section by default
        document.getElementById('project-create-section').style.display = 'none';
    },

    /**
     * Toggle the create project form
     */
    toggleCreateForm() {
        const createSection = document.getElementById('project-create-section');
        if (createSection.style.display === 'none') {
            createSection.style.display = 'block';
        } else {
            createSection.style.display = 'none';
            // Clear form
            document.getElementById('new-project-name').value = '';
            document.getElementById('new-project-description').value = '';
            document.getElementById('new-project-color').value = '#2196F3';
        }
    },

    /**
     * Render the list of projects
     */
    renderProjectList() {
        const listContainer = document.getElementById('project-list');
        if (!listContainer) return;

        if (this.projects.length === 0) {
            listContainer.innerHTML = '<div class="empty-state">No projects found</div>';
            return;
        }

        let html = '';

        this.projects.forEach(project => {
            const isActive = project.is_active;
            const isDefault = project.id === 'default';

            html += `
                <div class="project-card ${isActive ? 'active' : ''}" style="border-left-color: ${project.color}">
                    <div class="project-header">
                        <div class="project-info">
                            <h4 style="color: ${project.color}">${project.name}</h4>
                            ${isActive ? '<span class="badge badge-success">Active</span>' : ''}
                            ${isDefault ? '<span class="badge badge-info">Default</span>' : ''}
                        </div>
                        <div class="project-actions">
                            ${!isActive ? `<button class="btn btn-xs btn-primary" onclick="ProjectManager.switchProject('${project.id}')">Switch</button>` : ''}
                            ${!isDefault && !isActive ? `<button class="btn btn-xs btn-danger" onclick="ProjectManager.deleteProject('${project.id}', '${project.name}')">Delete</button>` : ''}
                        </div>
                    </div>

                    ${project.description ? `<p class="project-description">${project.description}</p>` : ''}

                    <div class="project-stats">
                        <div class="stat-item">
                            <span class="stat-value">${project.node_count || 0}</span>
                            <span class="stat-label">Total Nodes</span>
                        </div>
                    </div>
                </div>
            `;
        });

        listContainer.innerHTML = html;
    },

    /**
     * Create a new project
     */
    async createProject() {
        const name = document.getElementById('new-project-name').value.trim();
        const description = document.getElementById('new-project-description').value.trim();
        const color = document.getElementById('new-project-color').value;

        if (!name) {
            UI.showNotification('Project name is required', 'error');
            return;
        }

        try {
            const response = await fetch('/api/projects', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, description, color })
            });

            const data = await response.json();

            if (data.success) {
                UI.showNotification(`Project "${name}" created successfully`, 'success');

                // Reload projects and update list
                await this.loadProjects();
                this.renderProjectList();

                // Hide create form
                this.toggleCreateForm();
            } else {
                UI.showNotification(`Error creating project: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('[ProjectManager] Error creating project:', error);
            UI.showNotification('Failed to create project', 'error');
        }
    },

    /**
     * Switch to a different project
     */
    async switchProject(projectId) {
        try {
            const response = await fetch(`/api/projects/${projectId}/switch`, {
                method: 'POST'
            });

            const data = await response.json();

            if (data.success) {
                this.currentProject = data.project;

                UI.showNotification(`Switched to project: ${data.project.name}`, 'success');

                // Update header
                this.updateHeaderDisplay();

                // Reload projects list
                await this.loadProjects();
                this.renderProjectList();

                // Close modal
                this.closeProjectModal();

                // Reload graph to show only nodes from this project
                if (typeof API !== 'undefined' && API.loadGraphData) {
                    API.loadGraphData();
                }
            } else {
                UI.showNotification(`Error switching project: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('[ProjectManager] Error switching project:', error);
            UI.showNotification('Failed to switch project', 'error');
        }
    },

    /**
     * Delete a project
     */
    async deleteProject(projectId, projectName) {
        // Confirm deletion
        const confirmed = confirm(
            `Are you sure you want to delete project "${projectName}"?\n\n` +
            `This will permanently delete the project's Neo4j database and ALL its data.\n\n` +
            `This action cannot be undone!`
        );

        if (!confirmed) return;

        try {
            const response = await fetch(`/api/projects/${projectId}`, {
                method: 'DELETE'
            });

            const data = await response.json();

            if (data.success) {
                UI.showNotification(
                    data.message || `Project "${projectName}" deleted successfully`,
                    'success'
                );

                // Reload projects and update list
                await this.loadProjects();
                this.renderProjectList();
            } else {
                UI.showNotification(`Error deleting project: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('[ProjectManager] Error deleting project:', error);
            UI.showNotification('Failed to delete project', 'error');
        }
    },

    /**
     * Handle project switched event from WebSocket
     */
    handleProjectSwitched(data) {
        // Reload active project
        this.loadActiveProject();

        // Reload graph if needed
        if (typeof API !== 'undefined' && API.loadGraphData) {
            API.loadGraphData();
        }

        UI.showNotification(`Project switched to: ${data.project_name}`, 'info');
    }
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => ProjectManager.init());
} else {
    ProjectManager.init();
}
