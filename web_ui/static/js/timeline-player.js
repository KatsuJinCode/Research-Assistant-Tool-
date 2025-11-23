/**
 * Timeline Player Module
 * Animates graph evolution over time based on node creation timestamps
 */

const TimelinePlayer = {
    isPlaying: false,
    currentTime: 0,
    minTime: 0,
    maxTime: Date.now(),
    speed: 1, // 1x speed
    animationFrame: null,
    lastFrameTime: 0,

    /**
     * Initialize timeline with node data
     */
    init(nodes, links) {
        console.log('[TimelinePlayer] Initializing with', nodes.length, 'nodes');

        // Find time range from nodes
        const timestamps = nodes
            .map(n => {
                const timestamp = n.fullData?.created_at || n.created_at;
                return timestamp ? new Date(timestamp).getTime() : null;
            })
            .filter(t => t !== null && !isNaN(t));

        if (timestamps.length === 0) {
            console.warn('[TimelinePlayer] No valid timestamps found');
            this.minTime = Date.now() - 3600000; // 1 hour ago
            this.maxTime = Date.now();
        } else {
            this.minTime = Math.min(...timestamps);
            this.maxTime = Math.max(...timestamps);
        }

        this.currentTime = this.minTime;

        console.log(`[TimelinePlayer] Time range: ${new Date(this.minTime).toLocaleString()} to ${new Date(this.maxTime).toLocaleString()}`);

        // Update UI
        this.updateSlider(this.currentTime);
        this.updateDateDisplay(this.currentTime);

        // Show timeline controls
        const controls = document.getElementById('timeline-controls');
        if (controls) {
            controls.style.display = 'flex';
        }

        // Render at start time
        this.renderAtTime(this.currentTime);
    },

    /**
     * Start playing animation
     */
    play() {
        if (this.isPlaying) return;

        console.log('[TimelinePlayer] Playing');
        this.isPlaying = true;
        this.lastFrameTime = performance.now();

        // Update play/pause button
        const playBtn = document.getElementById('timeline-play');
        const pauseBtn = document.getElementById('timeline-pause');
        if (playBtn) playBtn.style.display = 'none';
        if (pauseBtn) pauseBtn.style.display = 'inline-block';

        this.animate();
    },

    /**
     * Pause animation
     */
    pause() {
        console.log('[TimelinePlayer] Paused');
        this.isPlaying = false;

        // Update play/pause button
        const playBtn = document.getElementById('timeline-play');
        const pauseBtn = document.getElementById('timeline-pause');
        if (playBtn) playBtn.style.display = 'inline-block';
        if (pauseBtn) pauseBtn.style.display = 'none';

        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
            this.animationFrame = null;
        }
    },

    /**
     * Reset to beginning
     */
    reset() {
        this.pause();
        this.currentTime = this.minTime;
        this.renderAtTime(this.currentTime);
        this.updateSlider(this.currentTime);
        this.updateDateDisplay(this.currentTime);
    },

    /**
     * Animation loop
     */
    animate() {
        if (!this.isPlaying) return;

        const now = performance.now();
        const deltaTime = now - this.lastFrameTime;
        this.lastFrameTime = now;

        // Calculate time step based on speed
        const timeRange = this.maxTime - this.minTime;
        const timeStep = (timeRange / 10000) * this.speed * deltaTime; // 10 seconds at 1x speed

        this.currentTime = Math.min(this.currentTime + timeStep, this.maxTime);

        this.renderAtTime(this.currentTime);
        this.updateSlider(this.currentTime);
        this.updateDateDisplay(this.currentTime);

        if (this.currentTime >= this.maxTime) {
            this.pause();
            console.log('[TimelinePlayer] Reached end of timeline');
        } else {
            this.animationFrame = requestAnimationFrame(() => this.animate());
        }
    },

    /**
     * Render graph at specific timestamp
     */
    renderAtTime(timestamp) {
        const svg = d3.select('#graph-svg');

        // Filter nodes by creation time
        const visibleNodeIds = new Set();

        GraphRenderer.currentGraphData.nodes.forEach(node => {
            const nodeTime = node.fullData?.created_at || node.created_at;
            const nodeTimestamp = nodeTime ? new Date(nodeTime).getTime() : this.minTime;

            if (nodeTimestamp <= timestamp) {
                visibleNodeIds.add(node.id);
            }
        });

        // Update node visibility with smooth transitions
        svg.selectAll('g').filter(d => d && d.id)
            .transition()
            .duration(200)
            .style('opacity', d => visibleNodeIds.has(d.id) ? 1 : 0.05)
            .style('pointer-events', d => visibleNodeIds.has(d.id) ? 'all' : 'none');

        // Update link visibility
        svg.selectAll('line')
            .transition()
            .duration(200)
            .style('stroke-opacity', d => {
                const sourceId = typeof d.source === 'object' ? d.source.id : d.source;
                const targetId = typeof d.target === 'object' ? d.target.id : d.target;
                const bothVisible = visibleNodeIds.has(sourceId) && visibleNodeIds.has(targetId);
                return bothVisible ? 0.6 : 0.02;
            });

        // Count visible nodes
        const visibleCount = visibleNodeIds.size;
        console.log(`[TimelinePlayer] ${visibleCount}/${GraphRenderer.currentGraphData.nodes.length} nodes visible at ${new Date(timestamp).toLocaleString()}`);
    },

    /**
     * Set playback speed
     */
    setSpeed(multiplier) {
        this.speed = parseFloat(multiplier);
        console.log(`[TimelinePlayer] Speed set to ${this.speed}x`);

        // Update UI
        const speedSelect = document.getElementById('timeline-speed');
        if (speedSelect) {
            speedSelect.value = multiplier;
        }
    },

    /**
     * Seek to specific timestamp
     */
    seekTo(timestamp) {
        this.currentTime = Math.max(this.minTime, Math.min(timestamp, this.maxTime));
        this.renderAtTime(this.currentTime);
        this.updateSlider(this.currentTime);
        this.updateDateDisplay(this.currentTime);
    },

    /**
     * Seek to percentage (0-100)
     */
    seekToPercent(percent) {
        const timestamp = this.minTime + (this.maxTime - this.minTime) * (percent / 100);
        this.seekTo(timestamp);
    },

    /**
     * Update slider position
     */
    updateSlider(timestamp) {
        const slider = document.getElementById('timeline-slider');
        if (!slider) return;

        const percent = ((timestamp - this.minTime) / (this.maxTime - this.minTime)) * 100;
        slider.value = percent;
    },

    /**
     * Update date display
     */
    updateDateDisplay(timestamp) {
        const dateDisplay = document.getElementById('timeline-date');
        if (!dateDisplay) return;

        const date = new Date(timestamp);
        dateDisplay.textContent = date.toLocaleString();
    }
};

// Global event handlers
function initTimeline() {
    TimelinePlayer.init(GraphRenderer.currentGraphData.nodes, GraphRenderer.currentGraphData.links);
}

function playTimeline() {
    TimelinePlayer.play();
}

function pauseTimeline() {
    TimelinePlayer.pause();
}

function resetTimeline() {
    TimelinePlayer.reset();
}

function changeTimelineSpeed(select) {
    TimelinePlayer.setSpeed(select.value);
}

function seekTimelinePercent(slider) {
    TimelinePlayer.seekToPercent(slider.value);
}
