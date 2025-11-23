/**
 * Visual Agent Builder
 *
 * No-code drag-and-drop interface for building custom agents.
 * Features:
 * - Visual flow editor with canvas
 * - Pre-built blocks (Input, Process, Output, Condition, Loop)
 * - Test runner
 * - Save/export agent definitions
 * - Generate Python code from visual flow
 */

class AgentBuilder {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.canvas = null;
        this.blocks = [];
        this.connections = [];
        this.selectedBlock = null;
        this.draggedBlock = null;
        this.nextBlockId = 1;

        this.init();
    }

    init() {
        this.createUI();
        this.setupEventListeners();
    }

    createUI() {
        this.container.innerHTML = `
            <div class="agent-builder">
                <!-- Header -->
                <div class="builder-header">
                    <h2>🤖 Visual Agent Builder</h2>
                    <div class="builder-actions">
                        <button class="btn-new" onclick="agentBuilder.newAgent()">New</button>
                        <button class="btn-save" onclick="agentBuilder.saveAgent()">Save</button>
                        <button class="btn-load" onclick="agentBuilder.loadAgent()">Load</button>
                        <button class="btn-test" onclick="agentBuilder.testAgent()">Test</button>
                        <button class="btn-export-code" onclick="agentBuilder.exportPython()">Export Code</button>
                        <button class="btn-export-yaml" onclick="agentBuilder.exportYAML()">Export YAML</button>
                    </div>
                </div>

                <div class="builder-main">
                    <!-- Block Palette -->
                    <div class="block-palette">
                        <h3>Block Palette</h3>
                        <div class="palette-sections">
                            <div class="palette-section">
                                <h4>Input/Output</h4>
                                <div class="palette-block" data-type="input" draggable="true">
                                    📥 Input
                                </div>
                                <div class="palette-block" data-type="output" draggable="true">
                                    📤 Output
                                </div>
                            </div>

                            <div class="palette-section">
                                <h4>Processing</h4>
                                <div class="palette-block" data-type="ai-query" draggable="true">
                                    🤖 AI Query
                                </div>
                                <div class="palette-block" data-type="function" draggable="true">
                                    ⚙️ Function
                                </div>
                                <div class="palette-block" data-type="transform" draggable="true">
                                    🔄 Transform
                                </div>
                            </div>

                            <div class="palette-section">
                                <h4>Control Flow</h4>
                                <div class="palette-block" data-type="condition" draggable="true">
                                    ❓ Condition
                                </div>
                                <div class="palette-block" data-type="loop" draggable="true">
                                    🔁 Loop
                                </div>
                                <div class="palette-block" data-type="parallel" draggable="true">
                                    ⚡ Parallel
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Canvas Area -->
                    <div class="canvas-area">
                        <canvas id="agent-canvas" width="1200" height="800"></canvas>
                        <div class="canvas-overlay">
                            <div class="agent-info">
                                <input type="text" id="agent-name" placeholder="Agent Name" value="my_custom_agent">
                                <input type="text" id="agent-version" placeholder="Version" value="1.0.0">
                                <textarea id="agent-description" placeholder="Agent Description"></textarea>
                            </div>
                        </div>
                    </div>

                    <!-- Properties Panel -->
                    <div class="properties-panel">
                        <h3>Properties</h3>
                        <div id="properties-content">
                            <p class="no-selection">Select a block to edit properties</p>
                        </div>
                    </div>
                </div>

                <!-- Test Runner Modal -->
                <div id="test-modal" class="modal" style="display:none;">
                    <div class="modal-content">
                        <span class="close" onclick="agentBuilder.closeTestModal()">&times;</span>
                        <h3>Test Agent</h3>
                        <div class="test-inputs">
                            <label>Test Inputs (JSON):</label>
                            <textarea id="test-inputs-json" rows="10">{}</textarea>
                        </div>
                        <button onclick="agentBuilder.runTest()" class="btn-run-test">Run Test</button>
                        <div class="test-results">
                            <h4>Results:</h4>
                            <pre id="test-results-output"></pre>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Initialize canvas
        this.canvas = document.getElementById('agent-canvas');
        this.ctx = this.canvas.getContext('2d');
        this.drawGrid();
    }

    setupEventListeners() {
        // Drag and drop from palette
        const paletteBlocks = document.querySelectorAll('.palette-block');
        paletteBlocks.forEach(block => {
            block.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('blockType', e.target.dataset.type);
            });
        });

        // Canvas drop
        this.canvas.addEventListener('dragover', (e) => {
            e.preventDefault();
        });

        this.canvas.addEventListener('drop', (e) => {
            e.preventDefault();
            const blockType = e.dataTransfer.getData('blockType');
            const rect = this.canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            this.addBlock(blockType, x, y);
        });

        // Canvas click
        this.canvas.addEventListener('click', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            this.handleCanvasClick(x, y);
        });

        // Canvas drag (move blocks)
        this.canvas.addEventListener('mousedown', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            this.startDragBlock(x, y);
        });

        this.canvas.addEventListener('mousemove', (e) => {
            if (this.draggedBlock) {
                const rect = this.canvas.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                this.dragBlock(x, y);
            }
        });

        this.canvas.addEventListener('mouseup', () => {
            this.draggedBlock = null;
        });
    }

    drawGrid() {
        const ctx = this.ctx;
        ctx.strokeStyle = '#e0e0e0';
        ctx.lineWidth = 0.5;

        // Vertical lines
        for (let x = 0; x < this.canvas.width; x += 50) {
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, this.canvas.height);
            ctx.stroke();
        }

        // Horizontal lines
        for (let y = 0; y < this.canvas.height; y += 50) {
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(this.canvas.width, y);
            ctx.stroke();
        }
    }

    addBlock(type, x, y) {
        const block = {
            id: this.nextBlockId++,
            type: type,
            x: x,
            y: y,
            width: 120,
            height: 60,
            label: this.getBlockLabel(type),
            inputs: [],
            outputs: [],
            config: this.getDefaultConfig(type)
        };

        this.blocks.push(block);
        this.redraw();
    }

    getBlockLabel(type) {
        const labels = {
            'input': '📥 Input',
            'output': '📤 Output',
            'ai-query': '🤖 AI Query',
            'function': '⚙️ Function',
            'transform': '🔄 Transform',
            'condition': '❓ Condition',
            'loop': '🔁 Loop',
            'parallel': '⚡ Parallel'
        };
        return labels[type] || type;
    }

    getDefaultConfig(type) {
        const configs = {
            'input': { name: 'input1', type: 'string', description: '' },
            'output': { name: 'output1', type: 'string' },
            'ai-query': { prompt: 'Enter prompt here...', temperature: 0.5, max_tokens: 2000 },
            'function': { function_name: 'my_function' },
            'transform': { expression: 'output = input' },
            'condition': { expression: 'input > 0' },
            'loop': { iterations: 10 },
            'parallel': { branches: 2 }
        };
        return configs[type] || {};
    }

    redraw() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.drawGrid();

        // Draw connections
        this.connections.forEach(conn => {
            this.drawConnection(conn);
        });

        // Draw blocks
        this.blocks.forEach(block => {
            this.drawBlock(block, block === this.selectedBlock);
        });
    }

    drawBlock(block, selected) {
        const ctx = this.ctx;

        // Shadow
        ctx.shadowColor = 'rgba(0,0,0,0.2)';
        ctx.shadowBlur = 10;
        ctx.shadowOffsetX = 2;
        ctx.shadowOffsetY = 2;

        // Block background
        ctx.fillStyle = selected ? '#e3f2fd' : '#ffffff';
        ctx.fillRect(block.x, block.y, block.width, block.height);

        // Border
        ctx.strokeStyle = selected ? '#2196f3' : '#757575';
        ctx.lineWidth = selected ? 3 : 1;
        ctx.strokeRect(block.x, block.y, block.width, block.height);

        ctx.shadowColor = 'transparent';

        // Label
        ctx.fillStyle = '#333';
        ctx.font = '12px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(block.label, block.x + block.width / 2, block.y + block.height / 2);

        // Connection points
        const pointRadius = 5;

        // Input point (left)
        ctx.fillStyle = '#4caf50';
        ctx.beginPath();
        ctx.arc(block.x, block.y + block.height / 2, pointRadius, 0, 2 * Math.PI);
        ctx.fill();

        // Output point (right)
        ctx.fillStyle = '#f44336';
        ctx.beginPath();
        ctx.arc(block.x + block.width, block.y + block.height / 2, pointRadius, 0, 2 * Math.PI);
        ctx.fill();
    }

    drawConnection(conn) {
        const fromBlock = this.blocks.find(b => b.id === conn.from);
        const toBlock = this.blocks.find(b => b.id === conn.to);

        if (!fromBlock || !toBlock) return;

        const ctx = this.ctx;
        const fromX = fromBlock.x + fromBlock.width;
        const fromY = fromBlock.y + fromBlock.height / 2;
        const toX = toBlock.x;
        const toY = toBlock.y + toBlock.height / 2;

        // Draw curved line
        ctx.strokeStyle = '#666';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(fromX, fromY);

        const controlDist = Math.abs(toX - fromX) / 2;
        ctx.bezierCurveTo(
            fromX + controlDist, fromY,
            toX - controlDist, toY,
            toX, toY
        );
        ctx.stroke();

        // Arrow
        this.drawArrow(ctx, toX - 10, toY, toX, toY);
    }

    drawArrow(ctx, fromX, fromY, toX, toY) {
        const headlen = 10;
        const angle = Math.atan2(toY - fromY, toX - fromX);

        ctx.beginPath();
        ctx.moveTo(toX, toY);
        ctx.lineTo(toX - headlen * Math.cos(angle - Math.PI / 6), toY - headlen * Math.sin(angle - Math.PI / 6));
        ctx.moveTo(toX, toY);
        ctx.lineTo(toX - headlen * Math.cos(angle + Math.PI / 6), toY - headlen * Math.sin(angle + Math.PI / 6));
        ctx.stroke();
    }

    handleCanvasClick(x, y) {
        // Find clicked block
        const clickedBlock = this.blocks.find(block =>
            x >= block.x && x <= block.x + block.width &&
            y >= block.y && y <= block.y + block.height
        );

        if (clickedBlock) {
            this.selectedBlock = clickedBlock;
            this.showProperties(clickedBlock);
            this.redraw();
        } else {
            this.selectedBlock = null;
            this.hideProperties();
            this.redraw();
        }
    }

    startDragBlock(x, y) {
        const block = this.blocks.find(b =>
            x >= b.x && x <= b.x + b.width &&
            y >= b.y && y <= b.y + b.height
        );

        if (block) {
            this.draggedBlock = { block, offsetX: x - block.x, offsetY: y - block.y };
        }
    }

    dragBlock(x, y) {
        if (this.draggedBlock) {
            this.draggedBlock.block.x = x - this.draggedBlock.offsetX;
            this.draggedBlock.block.y = y - this.draggedBlock.offsetY;
            this.redraw();
        }
    }

    showProperties(block) {
        const panel = document.getElementById('properties-content');
        let html = `<h4>Block Properties</h4>`;
        html += `<div class="property">
            <label>Type:</label>
            <input type="text" value="${block.type}" disabled>
        </div>`;

        // Generate property fields based on block config
        for (const [key, value] of Object.entries(block.config)) {
            html += `<div class="property">
                <label>${key}:</label>
                <input type="text" id="prop-${key}" value="${value}"
                       onchange="agentBuilder.updateProperty('${key}', this.value)">
            </div>`;
        }

        html += `<button class="btn-delete" onclick="agentBuilder.deleteBlock()">Delete Block</button>`;
        panel.innerHTML = html;
    }

    hideProperties() {
        const panel = document.getElementById('properties-content');
        panel.innerHTML = '<p class="no-selection">Select a block to edit properties</p>';
    }

    updateProperty(key, value) {
        if (this.selectedBlock) {
            this.selectedBlock.config[key] = value;
        }
    }

    deleteBlock() {
        if (this.selectedBlock) {
            this.blocks = this.blocks.filter(b => b.id !== this.selectedBlock.id);
            this.connections = this.connections.filter(
                c => c.from !== this.selectedBlock.id && c.to !== this.selectedBlock.id
            );
            this.selectedBlock = null;
            this.hideProperties();
            this.redraw();
        }
    }

    newAgent() {
        if (confirm('Clear current agent?')) {
            this.blocks = [];
            this.connections = [];
            this.selectedBlock = null;
            this.redraw();
            document.getElementById('agent-name').value = 'my_custom_agent';
            document.getElementById('agent-version').value = '1.0.0';
            document.getElementById('agent-description').value = '';
        }
    }

    saveAgent() {
        const agent = this.exportAgentDefinition();
        const blob = new Blob([JSON.stringify(agent, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${agent.name}.agent.json`;
        a.click();
    }

    loadAgent() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.agent.json';
        input.onchange = (e) => {
            const file = e.target.files[0];
            const reader = new FileReader();
            reader.onload = (event) => {
                const agent = JSON.parse(event.target.result);
                this.importAgentDefinition(agent);
            };
            reader.readAsText(file);
        };
        input.click();
    }

    testAgent() {
        document.getElementById('test-modal').style.display = 'block';
    }

    closeTestModal() {
        document.getElementById('test-modal').style.display = 'none';
    }

    async runTest() {
        const inputsJson = document.getElementById('test-inputs-json').value;
        const agent = this.exportAgentDefinition();

        try {
            const inputs = JSON.parse(inputsJson);

            // Send to backend for execution
            const response = await fetch('/api/agents/test', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ agent, inputs })
            });

            const result = await response.json();
            document.getElementById('test-results-output').textContent = JSON.stringify(result, null, 2);
        } catch (error) {
            document.getElementById('test-results-output').textContent = `Error: ${error.message}`;
        }
    }

    exportPython() {
        const agent = this.exportAgentDefinition();
        const pythonCode = this.generatePythonCode(agent);

        const blob = new Blob([pythonCode], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${agent.name}.py`;
        a.click();
    }

    exportYAML() {
        const agent = this.exportAgentDefinition();
        const yamlContent = this.generateYAML(agent);

        const blob = new Blob([yamlContent], { type: 'text/yaml' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${agent.name}.yaml`;
        a.click();
    }

    exportAgentDefinition() {
        return {
            name: document.getElementById('agent-name').value,
            version: document.getElementById('agent-version').value,
            description: document.getElementById('agent-description').value,
            blocks: this.blocks,
            connections: this.connections
        };
    }

    importAgentDefinition(agent) {
        document.getElementById('agent-name').value = agent.name;
        document.getElementById('agent-version').value = agent.version;
        document.getElementById('agent-description').value = agent.description;
        this.blocks = agent.blocks;
        this.connections = agent.connections;
        this.nextBlockId = Math.max(...this.blocks.map(b => b.id)) + 1;
        this.redraw();
    }

    generatePythonCode(agent) {
        return `"""
${agent.name}
Version: ${agent.version}

${agent.description}

Auto-generated by Visual Agent Builder
"""

from backend.agents.plugin_manager import AgentPlugin
from typing import Dict, Any


class ${this.toPascalCase(agent.name)}(AgentPlugin):
    def validate(self) -> bool:
        return True

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        # TODO: Implement agent logic based on visual flow
        ${this.generateExecutionCode(agent)}

        return outputs

    def get_metadata(self) -> Dict[str, Any]:
        return {
            'name': '${agent.name}',
            'version': '${agent.version}',
            'description': '''${agent.description}''',
            'author': 'Visual Agent Builder',
            'inputs': ${JSON.stringify(this.extractInputs(agent))},
            'outputs': ${JSON.stringify(this.extractOutputs(agent))}
        }
`;
    }

    generateExecutionCode(agent) {
        let code = '# Generated execution logic\n';
        agent.blocks.forEach(block => {
            code += `        # Block: ${block.label}\n`;
            code += `        # Type: ${block.type}\n`;
            code += `        # Config: ${JSON.stringify(block.config)}\n\n`;
        });
        return code;
    }

    generateYAML(agent) {
        return `name: ${agent.name}
version: ${agent.version}
description: ${agent.description}
inputs: ${JSON.stringify(this.extractInputs(agent), null, 2)}
outputs: ${JSON.stringify(this.extractOutputs(agent), null, 2)}
configuration:
  temperature: 0.5
  max_tokens: 2000
execution:
  type: chain
  steps: []
`;
    }

    extractInputs(agent) {
        return agent.blocks
            .filter(b => b.type === 'input')
            .map(b => ({ name: b.config.name, type: b.config.type }));
    }

    extractOutputs(agent) {
        return agent.blocks
            .filter(b => b.type === 'output')
            .map(b => ({ name: b.config.name, type: b.config.type }));
    }

    toPascalCase(str) {
        return str.replace(/(?:^|_)(\w)/g, (_, c) => c.toUpperCase()).replace(/_/g, '');
    }
}

// Initialize when DOM ready
let agentBuilder;
document.addEventListener('DOMContentLoaded', () => {
    // Agent builder is initialized on demand when user opens the modal
});
