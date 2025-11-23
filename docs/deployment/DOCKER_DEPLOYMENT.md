# Docker Deployment Guide

Complete guide for deploying the Research Assistant Tool using Docker.

## Quick Start

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 10GB disk space

### One-Command Deployment

```bash
docker-compose up -d
```

The application will be available at:
- **Web UI**: http://localhost:5000
- **Neo4j Browser**: http://localhost:7474
- **Redis**: localhost:6379

## Services

### Neo4j Graph Database

- **Image**: neo4j:5.15.0
- **Ports**:
  - 7474 (HTTP/Browser)
  - 7687 (Bolt Protocol)
- **Credentials**:
  - Username: `neo4j`
  - Password: `research_assistant_pass` (change in production!)
- **Memory**: 2GB heap, 1GB pagecache

### Redis Cache

- **Image**: redis:7.2-alpine
- **Port**: 6379
- **Max Memory**: 512MB
- **Eviction**: allkeys-lru

### Research Assistant App

- **Build**: Custom Dockerfile
- **Port**: 5000
- **Environment**: Production
- **Health Check**: `/health` endpoint

## Configuration

### Environment Variables

Create a `.env` file:

```bash
# Neo4j Configuration
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_secure_password_here

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379

# Application Configuration
FLASK_ENV=production
LOG_LEVEL=INFO
SECRET_KEY=your_secret_key_here

# AI Provider API Keys (optional)
ANTHROPIC_API_KEY=your_claude_api_key
OPENAI_API_KEY=your_openai_api_key
```

Load environment:

```bash
docker-compose --env-file .env up -d
```

### Volume Mounts

**Persistent Data**:
- `neo4j_data`: Database files
- `redis_data`: Redis persistence
- `./data`: Application data
- `./logs`: Application logs
- `./backups`: Database backups

## Operations

### Start Services

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d app

# View logs
docker-compose logs -f app
docker-compose logs -f neo4j
```

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ deletes data!)
docker-compose down -v
```

### Health Checks

```bash
# Check service health
docker-compose ps

# Application health
curl http://localhost:5000/health

# Neo4j health
curl http://localhost:7474
```

### Backup Database

```bash
# Backup Neo4j
docker exec research-assistant-neo4j \
  neo4j-admin database dump neo4j --to=/data/backup.dump

# Copy backup to host
docker cp research-assistant-neo4j:/data/backup.dump ./backups/
```

### Restore Database

```bash
# Stop application
docker-compose stop app

# Copy backup to container
docker cp ./backups/backup.dump research-assistant-neo4j:/data/

# Restore database
docker exec research-assistant-neo4j \
  neo4j-admin database load neo4j --from=/data/backup.dump --force

# Restart services
docker-compose start app
```

### Update Application

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose build app
docker-compose up -d app
```

## Scaling

### Horizontal Scaling

Add multiple app instances:

```yaml
services:
  app:
    # ... existing config
    deploy:
      replicas: 3
```

Add load balancer (nginx):

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - app
```

### Resource Limits

```yaml
services:
  app:
    # ... existing config
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

## Monitoring

### Container Stats

```bash
# Real-time stats
docker stats

# Service-specific stats
docker stats research-assistant-app
```

### Logs

```bash
# Tail logs
docker-compose logs -f

# Logs since timestamp
docker-compose logs --since 2025-11-23T10:00:00

# Export logs
docker-compose logs > application.log
```

### Application Metrics

Access metrics endpoints:
- **Application**: http://localhost:5000/metrics
- **Neo4j**: http://localhost:7474/db/system/query (requires auth)

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs app

# Check service status
docker-compose ps

# Restart service
docker-compose restart app
```

### Database Connection Issues

```bash
# Test Neo4j connection
docker exec research-assistant-neo4j cypher-shell \
  -u neo4j -p research_assistant_pass \
  "RETURN 'Connection successful'"

# Check network
docker network inspect research-assistant-network
```

### Out of Memory

```bash
# Check container memory usage
docker stats

# Increase Neo4j memory in docker-compose.yml:
  environment:
    - NEO4J_server_memory_heap_max__size=4G

# Restart
docker-compose up -d neo4j
```

### Permission Errors

```bash
# Fix volume permissions
sudo chown -R 1000:1000 ./data ./logs ./backups

# Restart containers
docker-compose restart
```

## Production Deployment

### Security Checklist

- [ ] Change default passwords
- [ ] Use secrets management (Docker Swarm secrets, Kubernetes secrets)
- [ ] Enable TLS/SSL
- [ ] Configure firewall rules
- [ ] Set up monitoring and alerts
- [ ] Configure automated backups
- [ ] Limit resource usage
- [ ] Use read-only root filesystem where possible

### SSL/TLS Configuration

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./ssl/cert.pem:/etc/nginx/cert.pem
      - ./ssl/key.pem:/etc/nginx/key.pem
      - ./nginx-ssl.conf:/etc/nginx/nginx.conf
```

### Automated Backups

```yaml
services:
  backup:
    image: your-backup-image
    environment:
      - BACKUP_SCHEDULE=0 2 * * *  # Daily at 2 AM
      - S3_BUCKET=your-backup-bucket
    volumes:
      - ./backups:/backups
      - neo4j_data:/neo4j_data:ro
```

## CI/CD Integration

GitHub Actions automatically builds and pushes Docker images on version tags.

### Deployment Pipeline

1. Code pushed to `main` branch
2. Tests run via GitHub Actions
3. Docker image built and pushed to Docker Hub
4. Deployment triggered (manual or automatic)
5. Health checks verify deployment

See `.github/workflows/deploy.yml` for configuration.

## Further Reading

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Neo4j Docker Guide](https://neo4j.com/docs/operations-manual/current/docker/)
- [Redis Docker Guide](https://redis.io/docs/install/install-stack/docker/)
