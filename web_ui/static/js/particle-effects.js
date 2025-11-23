/**
 * Particle Effects System
 *
 * Handles visual particle effects for the animation system including
 * sparks, glows, trails, and ambient effects.
 */

class ParticleEffectsSystem {
    constructor() {
        this.particles = [];
        this.particlePool = [];
        this.poolSize = 100;
        this.maxParticles = 500;
        this.enabled = true;

        this.initializePool();
    }

    /**
     * Initialize particle pool for performance
     */
    initializePool() {
        for (let i = 0; i < this.poolSize; i++) {
            this.particlePool.push(this.createParticleElement());
        }
    }

    /**
     * Create a particle DOM element
     */
    createParticleElement() {
        const particlesLayer = d3.select('.particles-layer');

        return particlesLayer.append('circle')
            .attr('class', 'particle')
            .attr('r', 2)
            .style('opacity', 0)
            .style('pointer-events', 'none');
    }

    /**
     * Get particle from pool or create new one
     */
    getParticle() {
        if (this.particlePool.length > 0) {
            return this.particlePool.pop();
        }
        return this.createParticleElement();
    }

    /**
     * Return particle to pool
     */
    releaseParticle(particle) {
        if (this.particlePool.length < this.poolSize) {
            particle.interrupt()
                .style('opacity', 0);
            this.particlePool.push(particle);
        } else {
            particle.remove();
        }
    }

    /**
     * Update all particles
     */
    update(deltaTime) {
        if (!this.enabled) return;

        // Update particle physics
        for (let i = this.particles.length - 1; i >= 0; i--) {
            const particle = this.particles[i];

            particle.life -= deltaTime;

            if (particle.life <= 0) {
                // Remove dead particle
                this.releaseParticle(particle.element);
                this.particles.splice(i, 1);
            } else {
                // Update position
                particle.x += particle.vx * deltaTime;
                particle.y += particle.vy * deltaTime;

                // Apply forces
                particle.vx += particle.ax * deltaTime;
                particle.vy += particle.ay * deltaTime;

                // Friction
                particle.vx *= particle.friction;
                particle.vy *= particle.friction;

                // Update visual
                particle.element
                    .attr('cx', particle.x)
                    .attr('cy', particle.y)
                    .style('opacity', particle.life / particle.maxLife);
            }
        }
    }

    /**
     * Emit burst of particles at position
     */
    emitBurst(config) {
        if (!this.enabled) return;

        const {
            x,
            y,
            count = 10,
            color = '#FFD700',
            speed = 50,
            spread = 360,
            size = 3,
            life = 1.0
        } = config;

        const angleStep = (spread * Math.PI / 180) / count;
        const startAngle = -spread / 2 * Math.PI / 180;

        for (let i = 0; i < count; i++) {
            const angle = startAngle + angleStep * i + (Math.random() - 0.5) * angleStep;
            const velocity = speed * (0.5 + Math.random() * 0.5);

            this.createParticle({
                x: x,
                y: y,
                vx: Math.cos(angle) * velocity,
                vy: Math.sin(angle) * velocity,
                color: color,
                size: size,
                life: life
            });
        }
    }

    /**
     * Emit directional stream of particles
     */
    emitStream(config) {
        if (!this.enabled) return;

        const {
            x,
            y,
            targetX,
            targetY,
            rate = 5, // Particles per second
            color = '#00BCD4',
            speed = 100,
            size = 2,
            life = 2.0
        } = config;

        // Calculate direction
        const dx = targetX - x;
        const dy = targetY - y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        const dirX = dx / distance;
        const dirY = dy / distance;

        // Emit particles
        const particlesToEmit = Math.floor(rate);
        for (let i = 0; i < particlesToEmit; i++) {
            const spread = 0.2;
            const vx = dirX * speed + (Math.random() - 0.5) * speed * spread;
            const vy = dirY * speed + (Math.random() - 0.5) * speed * spread;

            this.createParticle({
                x: x + (Math.random() - 0.5) * 10,
                y: y + (Math.random() - 0.5) * 10,
                vx: vx,
                vy: vy,
                color: color,
                size: size,
                life: life
            });
        }
    }

    /**
     * Create single particle
     */
    createParticle(config) {
        if (this.particles.length >= this.maxParticles) {
            // Remove oldest particle
            const oldest = this.particles.shift();
            this.releaseParticle(oldest.element);
        }

        const element = this.getParticle();

        const particle = {
            x: config.x || 0,
            y: config.y || 0,
            vx: config.vx || 0,
            vy: config.vy || 0,
            ax: config.ax || 0,
            ay: config.ay || 0,
            friction: config.friction || 0.98,
            color: config.color || '#FFD700',
            size: config.size || 2,
            life: config.life || 1.0,
            maxLife: config.life || 1.0,
            element: element
        };

        // Set initial visual state
        element
            .attr('cx', particle.x)
            .attr('cy', particle.y)
            .attr('r', particle.size)
            .attr('fill', particle.color)
            .style('opacity', 1);

        this.particles.push(particle);
        return particle;
    }

    /**
     * Create glow effect around a position
     */
    createGlow(config) {
        if (!this.enabled) return;

        const {
            x,
            y,
            color = '#FFD700',
            radius = 30,
            duration = 1000,
            pulseCount = 1
        } = config;

        const effectsLayer = d3.select('.effects-layer');

        for (let i = 0; i < pulseCount; i++) {
            setTimeout(() => {
                const glow = effectsLayer.append('circle')
                    .attr('cx', x)
                    .attr('cy', y)
                    .attr('r', 5)
                    .attr('fill', 'none')
                    .attr('stroke', color)
                    .attr('stroke-width', 3)
                    .style('opacity', 0.8);

                glow.transition()
                    .duration(duration)
                    .attr('r', radius)
                    .attr('stroke-width', 0)
                    .style('opacity', 0)
                    .remove();
            }, i * (duration / pulseCount));
        }
    }

    /**
     * Create sparks at a node (processing effect)
     */
    createSparks(nodeId, graphRenderer) {
        if (!this.enabled) return;

        const node = graphRenderer.currentGraphData.nodes.find(n => n.id === nodeId);
        if (!node) return;

        // Emit bursts periodically
        const sparkInterval = setInterval(() => {
            this.emitBurst({
                x: node.x,
                y: node.y,
                count: 8,
                color: '#FFC107',
                speed: 40,
                spread: 360,
                size: 2,
                life: 0.5
            });
        }, 200);

        // Return cleanup function
        return () => clearInterval(sparkInterval);
    }

    /**
     * Create data flow particles along an edge
     */
    createDataFlow(sourceId, targetId, graphRenderer, config = {}) {
        if (!this.enabled) return;

        const sourceNode = graphRenderer.currentGraphData.nodes.find(n => n.id === sourceId);
        const targetNode = graphRenderer.currentGraphData.nodes.find(n => n.id === targetId);

        if (!sourceNode || !targetNode) return;

        const {
            color = '#00BCD4',
            particleCount = 5,
            speed = 100,
            interval = 200
        } = config;

        let emitCount = 0;

        const flowInterval = setInterval(() => {
            if (emitCount >= particleCount) {
                clearInterval(flowInterval);
                return;
            }

            this.emitStream({
                x: sourceNode.x,
                y: sourceNode.y,
                targetX: targetNode.x,
                targetY: targetNode.y,
                rate: 1,
                color: color,
                speed: speed,
                size: 3,
                life: 1.5
            });

            emitCount++;
        }, interval);

        return () => clearInterval(flowInterval);
    }

    /**
     * Create trail behind moving agent
     */
    createTrail(x, y, color = '#FFD700') {
        if (!this.enabled) return;

        this.createParticle({
            x: x + (Math.random() - 0.5) * 5,
            y: y + (Math.random() - 0.5) * 5,
            vx: (Math.random() - 0.5) * 10,
            vy: (Math.random() - 0.5) * 10,
            color: color,
            size: 2,
            life: 0.5,
            friction: 0.95
        });
    }

    /**
     * Create success effect (green burst + glow)
     */
    createSuccessEffect(x, y) {
        if (!this.enabled) return;

        // Burst
        this.emitBurst({
            x: x,
            y: y,
            count: 20,
            color: '#4CAF50',
            speed: 60,
            spread: 360,
            size: 3,
            life: 1.0
        });

        // Glow
        this.createGlow({
            x: x,
            y: y,
            color: '#4CAF50',
            radius: 50,
            duration: 800,
            pulseCount: 2
        });
    }

    /**
     * Create error effect (red shake + particles)
     */
    createErrorEffect(x, y) {
        if (!this.enabled) return;

        // Burst
        this.emitBurst({
            x: x,
            y: y,
            count: 15,
            color: '#F44336',
            speed: 40,
            spread: 360,
            size: 4,
            life: 0.8
        });

        // Glow
        this.createGlow({
            x: x,
            y: y,
            color: '#F44336',
            radius: 40,
            duration: 600,
            pulseCount: 3
        });
    }

    /**
     * Create ambient particles (background effect)
     */
    createAmbientParticles(bounds, count = 50) {
        if (!this.enabled) return;

        const { minX, maxX, minY, maxY } = bounds;

        for (let i = 0; i < count; i++) {
            this.createParticle({
                x: minX + Math.random() * (maxX - minX),
                y: minY + Math.random() * (maxY - minY),
                vx: (Math.random() - 0.5) * 20,
                vy: (Math.random() - 0.5) * 20,
                color: '#ffffff',
                size: 1,
                life: 5.0 + Math.random() * 5.0,
                friction: 0.99
            });
        }
    }

    /**
     * Clear all particles
     */
    clearAll() {
        this.particles.forEach(particle => {
            this.releaseParticle(particle.element);
        });
        this.particles = [];
    }

    /**
     * Enable/disable particle system
     */
    setEnabled(enabled) {
        this.enabled = enabled;
        if (!enabled) {
            this.clearAll();
        }
    }

    /**
     * Get particle system statistics
     */
    getStats() {
        return {
            activeParticles: this.particles.length,
            poolSize: this.particlePool.length,
            maxParticles: this.maxParticles,
            enabled: this.enabled
        };
    }
}

// Export to global scope
window.ParticleEffects = new ParticleEffectsSystem();
