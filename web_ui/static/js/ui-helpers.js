/**
 * UI Helper Functions
 *
 * Extracted from index.html inline scripts for better maintainability.
 * Contains UI toggle functions, resize handlers, settings modal, etc.
 */

// Agent monitor toggle
function toggleAgentMonitor() {
    const panel = document.getElementById('agent-monitor-panel');
    const toggle = document.getElementById('agent-monitor-toggle');
    panel.classList.toggle('collapsed');
    toggle.textContent = panel.classList.contains('collapsed') ? '▼' : '▲';
}

// Toggle AI Assistant at bottom of sidebar
function toggleAIAssistant() {
    const panel = document.getElementById('ai-assistant-bottom');
    const toggle = document.getElementById('ai-assistant-toggle');
    panel.classList.toggle('collapsed');
    toggle.textContent = panel.classList.contains('collapsed') ? '▲' : '▼';
}

// Sidebar resize functionality
(function initSidebarResize() {
    const sidebar = document.getElementById('sidebar');
    const handle = document.getElementById('sidebar-resize-handle');
    if (!sidebar || !handle) return;

    let isResizing = false;

    handle.addEventListener('mousedown', (e) => {
        isResizing = true;
        handle.classList.add('resizing');
        document.body.style.cursor = 'ew-resize';
        document.body.style.userSelect = 'none';
        e.preventDefault();
    });

    document.addEventListener('mousemove', (e) => {
        if (!isResizing) return;

        const newWidth = e.clientX;
        const minWidth = 250;
        const maxWidth = 600;

        if (newWidth >= minWidth && newWidth <= maxWidth) {
            sidebar.style.width = newWidth + 'px';
        }
    });

    document.addEventListener('mouseup', () => {
        if (isResizing) {
            isResizing = false;
            handle.classList.remove('resizing');
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        }
    });
})();

// AI Assistant Vertical Resize
(function initAIAssistantResize() {
    const aiAssistant = document.getElementById('ai-assistant-bottom');
    const handle = document.getElementById('ai-assistant-resize-handle');
    if (!aiAssistant || !handle) return;

    let isResizing = false;
    let startY = 0;
    let startHeight = 0;

    handle.addEventListener('mousedown', (e) => {
        isResizing = true;
        startY = e.clientY;
        startHeight = aiAssistant.offsetHeight;
        handle.classList.add('resizing');
        document.body.style.cursor = 'ns-resize';
        document.body.style.userSelect = 'none';
        e.preventDefault();
        e.stopPropagation();
    });

    document.addEventListener('mousemove', (e) => {
        if (!isResizing) return;

        const deltaY = startY - e.clientY;
        const newHeight = startHeight + deltaY;
        const minHeight = 100;
        const maxHeight = 600;

        if (newHeight >= minHeight && newHeight <= maxHeight) {
            aiAssistant.style.height = newHeight + 'px';
        }
    });

    document.addEventListener('mouseup', () => {
        if (isResizing) {
            isResizing = false;
            handle.classList.remove('resizing');
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        }
    });
})();

// Visualization controls toggle
function toggleVizControls() {
    const panel = document.getElementById('visualization-controls');
    const toggle = panel.querySelector('.viz-toggle-btn');
    panel.classList.toggle('collapsed');
    toggle.textContent = panel.classList.contains('collapsed') ? '+' : '−';
}

// Graph thumbnail preview functions
function refreshGraphThumbnail() {
    const canvas = document.getElementById('thumbnail-canvas');
    const loading = document.getElementById('thumbnail-loading');

    if (!canvas || !window.Graph) {
        if (loading) loading.textContent = 'Preview unavailable';
        return;
    }

    try {
        if (loading) loading.textContent = 'Generating preview...';

        // Get graph data
        const nodes = window.Graph.nodes || [];
        const links = window.Graph.links || [];

        if (nodes.length === 0) {
            if (loading) loading.textContent = 'No graph data yet';
            return;
        }

        const ctx = canvas.getContext('2d');
        canvas.width = canvas.offsetWidth;
        canvas.height = canvas.offsetHeight;

        // Calculate bounds
        let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
        nodes.forEach(n => {
            if (n.x < minX) minX = n.x;
            if (n.x > maxX) maxX = n.x;
            if (n.y < minY) minY = n.y;
            if (n.y > maxY) maxY = n.y;
        });

        const width = maxX - minX || 1;
        const height = maxY - minY || 1;
        const padding = 10;
        const scale = Math.min(
            (canvas.width - padding * 2) / width,
            (canvas.height - padding * 2) / height
        );

        // Transform coordinates
        const tx = (x) => (x - minX) * scale + padding;
        const ty = (y) => (y - minY) * scale + padding;

        // Clear
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Draw links
        ctx.strokeStyle = '#555';
        ctx.lineWidth = 1;
        links.forEach(link => {
            const source = typeof link.source === 'object' ? link.source : nodes.find(n => n.id === link.source);
            const target = typeof link.target === 'object' ? link.target : nodes.find(n => n.id === link.target);
            if (source && target && source.x != null && target.x != null) {
                ctx.beginPath();
                ctx.moveTo(tx(source.x), ty(source.y));
                ctx.lineTo(tx(target.x), ty(target.y));
                ctx.stroke();
            }
        });

        // Draw nodes
        nodes.forEach(node => {
            if (node.x == null || node.y == null) return;
            ctx.fillStyle = node.type === 'document' ? '#9C27B0' : '#2196F3';
            ctx.beginPath();
            ctx.arc(tx(node.x), ty(node.y), 3, 0, Math.PI * 2);
            ctx.fill();
        });

        if (loading) loading.style.display = 'none';

    } catch (error) {
        console.error('Thumbnail generation failed:', error);
        if (loading) loading.textContent = 'Preview unavailable';
    }
}

function fitGraphToView() {
    if (window.Graph && typeof window.Graph.zoomToFit === 'function') {
        window.Graph.zoomToFit(400);
    }
}

// Investigate claim function for detail panel buttons
function investigateClaim(type) {
    // Get selected claim ID from graph renderer
    if (!GraphRenderer.selectedNodeIds || GraphRenderer.selectedNodeIds.size === 0) {
        alert('⚠️ No claim selected. Please select a claim first.');
        return;
    }

    const selectedNodes = Array.from(GraphRenderer.selectedNodeIds);
    const selectedClaimId = selectedNodes[0]; // Use first selected node

    // Get claim summary for better user feedback
    const claimNode = GraphRenderer.graph.nodes.find(n => n.id === selectedClaimId);
    const claimSummary = claimNode ? (claimNode.summary || claimNode.text || selectedClaimId) : selectedClaimId;
    const displayText = claimSummary.length > 80 ? claimSummary.substring(0, 80) + '...' : claimSummary;

    // Make API call to start investigation
    fetch('/api/investigate-claim', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            claim_id: selectedClaimId,
            type: type
        })
    })
    .then(r => r.json())
    .then(result => {
        if (result.error) {
            alert('❌ Error starting investigation: ' + result.error);
        } else {
            // Use notification instead of alert for success
            const typeLabel = type === 'support' ? 'Supporting Evidence' : 'Contradicting Evidence';
            UI.showNotification(`🔬 Investigation started: ${typeLabel}\n📋 Claim: ${displayText}`, 'success', 5000);

            // Open Background Agents tab to show visual feedback
            const agentsTabBtn = document.querySelector('[data-tab="background-agents"]');
            if (agentsTabBtn) {
                agentsTabBtn.click();
            }
        }
    })
    .catch(err => {
        alert('❌ Error starting investigation: ' + err.message);
    });
}

// Settings Modal Functions
function openSettings() {
    const modal = document.getElementById('settings-modal');
    if (!modal) return;

    // Load saved settings from localStorage
    const savedThreshold = localStorage.getItem('similarity_threshold') || '0.7';
    const savedModel = localStorage.getItem('embedding_model') || 'all-mpnet-base-v2';

    // Apply saved values to modal
    const slider = document.getElementById('similarity-threshold-slider');
    if (slider) {
        slider.value = savedThreshold;
        updateThresholdDisplay(savedThreshold);
    }

    // Set select dropdown
    const modelSelect = document.getElementById('embedding-model-select');
    if (modelSelect) {
        modelSelect.value = savedModel;
    }
    updateModelDescription();

    // Load current framework
    loadCurrentFramework();

    // Show modal
    modal.style.display = 'flex';
}

// Framework management functions
function loadCurrentFramework() {
    fetch('/api/framework/current')
        .then(r => r.json())
        .then(data => {
            if (data.success && data.framework) {
                const frameworkSelect = document.getElementById('framework-select');
                if (frameworkSelect) {
                    frameworkSelect.value = data.framework.name;
                    updateFrameworkDescription();
                }
            }
        })
        .catch(err => console.error('Error loading current framework:', err));
}

function updateFrameworkDescription() {
    const select = document.getElementById('framework-select');
    const descDiv = document.getElementById('framework-description');
    if (!select || !descDiv) return;

    const framework = select.value;
    const descriptions = {
        'general_research': {
            title: 'General Research Framework',
            color: '#2196F3',
            points: [
                'Flexible entity and relationship types for broad domains',
                'Entity Types: Claim, Evidence, Document, Author, Concept, Finding, etc.',
                'Suitable for: Literature review, cross-domain analysis, exploratory research'
            ]
        },
        'medical_research': {
            title: 'Medical Research Framework',
            color: '#4CAF50',
            points: [
                'Evidence-based medicine principles with clinical focus',
                'Entity Types: Disease, Treatment, Drug, Clinical_Trial, Patient_Population, etc.',
                'Relationships: TREATS, CAUSES, CONTRAINDICATES, TESTED_ON',
                'Suitable for: Clinical decision support, systematic reviews, drug safety analysis'
            ]
        },
        'legal_research': {
            title: 'Legal Research Framework',
            color: '#FF9800',
            points: [
                'Case law analysis and statutory interpretation',
                'Entity Types: Case, Statute, Legal_Principle, Jurisdiction, Precedent',
                'Relationships: CITES, OVERRULES, DISTINGUISHES, APPLIES, INTERPRETS',
                'Suitable for: Legal memoranda, case law research, brief writing'
            ]
        },
        'scientific_research': {
            title: 'Scientific Research Framework',
            color: '#9C27B0',
            points: [
                'Emphasis on methodology, reproducibility, and peer review',
                'Entity Types: Hypothesis, Experiment, Finding, Theory, Dataset, Protocol',
                'Relationships: SUPPORTS, REFUTES, REPLICATES, EXTENDS, VALIDATES',
                'Suitable for: Hypothesis testing, meta-analysis, replication studies'
            ]
        }
    };

    const desc = descriptions[framework];
    if (desc) {
        descDiv.innerHTML = `
            <strong style="color: ${desc.color};">${desc.title}</strong><br>
            ${desc.points.map(p => '• ' + p).join('<br>')}
        `;
        descDiv.style.borderColor = desc.color;
        descDiv.style.background = desc.color + '1A';
    }
}

function viewFrameworkDetails() {
    const select = document.getElementById('framework-select');
    if (!select) return;

    const frameworkName = select.value;
    fetch('/api/framework/' + frameworkName)
        .then(r => r.json())
        .then(data => {
            if (data.success && data.framework) {
                const fw = data.framework;
                const details = `
Framework: ${fw.name}
Version: ${fw.version}

Description:
${fw.description}

Entity Types (${fw.entity_types.length}):
${fw.entity_types.join(', ')}

Relationship Types (${fw.relationship_types.length}):
${fw.relationship_types.join(', ')}

Evidence Levels:
${fw.evaluation_criteria.evidence_levels.join(', ')}

Source Preferences:
Databases: ${fw.source_preferences.databases.join(', ')}
                `;
                alert(details);
            }
        })
        .catch(err => alert('Error loading framework details: ' + err.message));
}

function uploadCustomFramework() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.yaml,.yml';
    input.onchange = function(e) {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('framework', file);

        fetch('/api/framework/upload', {
            method: 'POST',
            body: formData
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                alert('✓ ' + data.message + '\n\nFramework "' + data.framework.name + '" has been uploaded and validated.');
                // Reload framework list
                location.reload();
            } else {
                alert('Error: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(err => alert('Error uploading framework: ' + err.message));
    };
    input.click();
}

function closeSettings() {
    const modal = document.getElementById('settings-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function saveSettings() {
    // Get values
    const threshold = document.getElementById('similarity-threshold-slider').value;
    const modelSelect = document.getElementById('embedding-model-select');
    const model = modelSelect ? modelSelect.value : 'all-mpnet-base-v2';
    const frameworkSelect = document.getElementById('framework-select');
    const framework = frameworkSelect ? frameworkSelect.value : 'general_research';

    // Save to localStorage
    localStorage.setItem('similarity_threshold', threshold);
    localStorage.setItem('embedding_model', model);

    // Check if model changed
    const previousModel = localStorage.getItem('previous_embedding_model') || 'all-mpnet-base-v2';
    const modelChanged = previousModel !== model;
    localStorage.setItem('previous_embedding_model', model);

    // Check if framework changed
    const previousFramework = localStorage.getItem('current_framework') || 'general_research';
    const frameworkChanged = previousFramework !== framework;

    // Set framework if changed
    if (frameworkChanged) {
        fetch('/api/framework/set', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({framework_name: framework})
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                localStorage.setItem('current_framework', framework);
                console.log('[Settings] Framework changed to:', framework);

                // Show compatibility warnings if any
                if (data.compatibility && !data.compatibility.compatible) {
                    const warnings = data.compatibility.warnings.join('\n');
                    alert('⚠️ Framework Compatibility Warning:\n\n' + warnings + '\n\nThe framework has been changed, but some existing graph data may not be compatible.');
                }
            } else {
                alert('Error changing framework: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(err => {
            alert('Error changing framework: ' + err.message);
        });
    }

    // Close modal
    closeSettings();

    // Get model display name
    const selectedOption = modelSelect.options[modelSelect.selectedIndex];
    const modelDisplayName = selectedOption ? selectedOption.text : model;

    // Show confirmation message
    let message = '✓ Settings saved!\n\nSimilarity Threshold: ' + threshold + '\nEmbedding Model: ' + modelDisplayName;
    if (frameworkChanged) {
        message += '\nResearch Framework: ' + framework;
    }
    if (modelChanged) {
        message += '\n\n⚠️ Model changed! Type "generate embeddings" in chat to regenerate embeddings with the new model.';
    }
    alert(message);

    console.log('[Settings] Saved:', { threshold, model, framework, modelChanged, frameworkChanged });
}

function updateThresholdDisplay(value) {
    const valueDisplay = document.getElementById('threshold-value');
    const labelDisplay = document.getElementById('threshold-label');

    if (valueDisplay) {
        valueDisplay.textContent = parseFloat(value).toFixed(2);
    }

    if (labelDisplay) {
        const val = parseFloat(value);
        let label = '';
        if (val < 0.65) {
            label = 'Aggressive';
        } else if (val <= 0.8) {
            label = 'Balanced (Recommended)';
        } else {
            label = 'Conservative';
        }
        labelDisplay.textContent = label;
    }
}

function updateModelDescription() {
    const modelDescription = document.getElementById('model-description');
    const modelSelect = document.getElementById('embedding-model-select');

    if (!modelDescription || !modelSelect) return;

    const modelValue = modelSelect.value;
    const descriptions = {
        'all-MiniLM-L6-v2': {
            color: '#00BCD4',
            title: 'Maximum Speed - MiniLM-L6',
            text: '• Fastest processing (~0.5 seconds per claim)<br>• Smallest model (384 dimensions)<br>• Good accuracy for most use cases<br>• Ideal for: Large document collections, quick prototyping, real-time processing'
        },
        'all-MiniLM-L12-v2': {
            color: '#03A9F4',
            title: 'Balanced - MiniLM-L12',
            text: '• Good balance of speed and quality (~1 second per claim)<br>• Medium-sized model (384 dimensions)<br>• Better accuracy than L6, faster than MPNet<br>• Ideal for: General research, balanced workloads, moderate document collections'
        },
        'all-mpnet-base-v2': {
            color: '#4CAF50',
            title: 'High Quality - MPNet (Recommended)',
            text: '• Best semantic understanding for English research papers<br>• 768-dimensional embeddings capture rich meaning<br>• Good balance of quality and speed (~2 seconds per claim)<br>• Ideal for: Academic research, fact-checking, evidence analysis'
        },
        'all-distilroberta-v1': {
            color: '#9C27B0',
            title: 'Premium - DistilRoBERTa',
            text: '• Alternative high-quality architecture<br>• 768 dimensions with RoBERTa training<br>• Slightly slower but very accurate (~2.5 seconds per claim)<br>• Ideal for: Critical analysis, legal documents, premium research'
        },
        'paraphrase-multilingual-mpnet-base-v2': {
            color: '#FF9800',
            title: 'Multilingual - MPNet Multi',
            text: '• Supports 50+ languages<br>• 768 dimensions with multilingual training<br>• Best for non-English or mixed-language documents (~2.5 seconds per claim)<br>• Ideal for: International research, multilingual corpora, global studies'
        },
        'msmarco-distilbert-base-v4': {
            color: '#E91E63',
            title: 'Search-Optimized - MS MARCO',
            text: '• Fine-tuned for search and retrieval tasks<br>• 768 dimensions optimized for finding relevant passages<br>• Excellent for question-answering (~2 seconds per claim)<br>• Ideal for: Evidence retrieval, Q&A systems, information seeking'
        }
    };

    const desc = descriptions[modelValue] || descriptions['all-mpnet-base-v2'];
    modelDescription.style.background = 'rgba(' + parseInt(desc.color.slice(1,3), 16) + ', ' + parseInt(desc.color.slice(3,5), 16) + ', ' + parseInt(desc.color.slice(5,7), 16) + ', 0.1)';
    modelDescription.style.borderColor = desc.color;
    modelDescription.innerHTML = '<strong style="color: ' + desc.color + ';">' + desc.title + '</strong><br>' + desc.text;
}

// Load settings on page load and apply them globally
function loadGlobalSettings() {
    const threshold = localStorage.getItem('similarity_threshold') || '0.7';
    const model = localStorage.getItem('embedding_model') || 'all-mpnet-base-v2';

    // Make settings available globally
    window.USER_SETTINGS = {
        similarity_threshold: parseFloat(threshold),
        embedding_model: model
    };

    console.log('[Settings] Loaded global settings:', window.USER_SETTINGS);
}

// Initialize settings on page load
document.addEventListener('DOMContentLoaded', () => {
    loadGlobalSettings();
});
