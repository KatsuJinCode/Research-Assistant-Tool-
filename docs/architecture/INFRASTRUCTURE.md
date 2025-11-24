# Infrastructure Documentation

Complete overview of the Research Assistant Tool infrastructure, error handling, logging, and DevOps practices.

## Table of Contents

1. [Error Handling](#error-handling)
2. [Logging](#logging)
3. [Testing](#testing)
4. [CI/CD Pipeline](#cicd-pipeline)
5. [Docker Deployment](#docker-deployment)
6. [Database Backups](#database-backups)
7. [Monitoring](#monitoring)
8. [Security](#security)

---

## Error Handling

### Centralized Exception System

Located in `backend/core/exceptions.py`, provides 30+ custom exceptions organized by domain:

#### Exception Hierarchy

```python
ApplicationError (base)
├── DatabaseError
│   ├── DatabaseConnectionError
│   └── DatabaseConstraintError
├── DocumentError
│   ├── DocumentNotFoundError
│   ├── DocumentUploadError
│   ├── DocumentParseError
│   ├── DocumentTooLargeError
│   └── UnsupportedFileTypeError
├── ClaimError
│   ├── ClaimNotFoundError
│   └── ClaimValidationError
├── ProjectError
│   ├── ProjectNotFoundError
│   └── ProjectAlreadyExistsError
├── AIError
│   ├── AIAPIError
│   ├── AIRateLimitError
│   └── AgentExecutionError
├── SearchError
├── ValidationError
│   ├── MissingRequiredFieldError
│   └── InvalidFormatError
└── System Errors
    ├── ServiceUnavailableError
    └── TimeoutError
```

#### Error Codes

All errors have machine-readable error codes (1000-9999):
- **1000-1999**: Database errors
- **2000-2999**: Document errors
- **3000-3999**: Claim errors
- **4000-4999**: Project errors
- **5000-5999**: AI/Agent errors
- **6000-6999**: Search errors
- **7000-7999**: Auth errors
- **8000-8999**: Validation errors
- **9000-9999**: System errors

#### Usage Example

```python
from backend.core import DocumentNotFoundError, safe_execute

# Raise custom exception
if not document:
    raise DocumentNotFoundError(document_id="doc_123")

# Safe execution wrapper
result = safe_execute(
    risky_function,
    arg1, arg2,
    error_message="Operation failed"
)
```

#### Error Response Format

All errors return consistent JSON:

```json
{
  "error": true,
  "message": "Document 'doc_123' not found",
  "error_code": 2000,
  "error_name": "DOCUMENT_NOT_FOUND",
  "status_code": 404,
  "details": {
    "document_id": "doc_123"
  }
}
```

### Error Handler Middleware

Located in `backend/core/error_handler.py`, registers Flask error handlers for:
- Custom `ApplicationError` exceptions
- HTTP exceptions (404, 405, etc.)
- Validation errors (`ValueError`)
- Unexpected exceptions (500)

Automatically logs all errors with context (path, method, user, etc.).

---

## Logging

### Structured Logging System

Located in `backend/core/logging_config.py`, provides enterprise-grade logging.

#### Features

- **Structured JSON logs** for production
- **Colored console output** for development
- **Log rotation** (10MB max, 5 backups)
- **Separate error log** (ERROR+ only)
- **Request context** (user_id, request_id)
- **Multiple log levels** per module

#### Configuration

```python
from backend.core import setup_logging, get_logger

# Setup logging (call once at startup)
setup_logging(
    app_name="research_assistant",
    log_level="INFO",
    log_dir="logs",
    enable_json=False,  # True for production
    enable_console=True,
    enable_file=True
)

# Get logger for module
logger = get_logger(__name__)

# Use logger
logger.info("Processing document", extra={"doc_id": "123"})
logger.error("Operation failed", exc_info=True)
```

#### Log Output

**Console (colored)**:
```
2025-11-23 10:30:45 | INFO     | backend.agents | Processing document
2025-11-23 10:30:46 | ERROR    | backend.agents | Upload failed
```

**File (JSON)**:
```json
{
  "timestamp": "2025-11-23T10:30:45Z",
  "level": "INFO",
  "logger": "backend.agents",
  "message": "Processing document",
  "module": "agents",
  "function": "process_document",
  "line": 123,
  "doc_id": "123"
}
```

#### Log Files

- `logs/research_assistant.log` - All logs (rotated)
- `logs/research_assistant_errors.log` - Errors only (rotated)

#### Request Context

```python
from backend.core import RequestContext

with RequestContext(user_id="user_123", request_id="req_456"):
    logger.info("Processing request")
    # All logs in this context include user_id and request_id
```

---

## Testing

### Test Coverage

**82 comprehensive tests** across 4 test files:

1. **`tests/test_agents_framework.py`** (18 tests)
   - Agent template creation and validation
   - Plugin system and discovery
   - Visual agent builder
   - Agent testing framework

2. **`tests/test_ml_features.py`** (22 tests)
   - Claim classification (6 tests)
   - Value prediction (5 tests)
   - Anomaly detection (5 tests)
   - Trend analysis (6 tests)

3. **`tests/test_commenting_activity.py`** (21 tests)
   - Comment system (9 tests)
   - Activity feed (12 tests)

4. **`tests/test_reports_performance.py`** (21 tests)
   - Report generation (8 tests)
   - Caching system (6 tests)
   - Pagination (4 tests)
   - Query optimization (3 tests)

### Running Tests

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=backend --cov=web_ui --cov-report=html

# Specific test file
pytest tests/test_agents_framework.py -v

# Specific test
pytest tests/test_agents_framework.py::TestAgentTemplate::test_create_basic_template -v
```

### Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=backend --cov-report=html
open htmlcov/index.html
```

---

## CI/CD Pipeline

Three GitHub Actions workflows in `.github/workflows/`:

### 1. Tests Workflow (`tests.yml`)

**Triggers**: Push to main/develop/claude/**, pull requests

**Jobs**:
- **Test** (multi-OS, multi-Python)
  - Runs on Ubuntu, Windows, macOS
  - Tests with Python 3.9, 3.10, 3.11
  - Runs pytest with coverage
  - Uploads to Codecov

- **Lint** (Ubuntu only)
  - flake8 (code quality)
  - black (formatting)
  - isort (import sorting)
  - mypy (type checking)

- **Security** (Ubuntu only)
  - safety (dependency vulnerabilities)
  - bandit (security issues in code)
  - Uploads security reports

### 2. Deploy Workflow (`deploy.yml`)

**Triggers**: Version tags (v*.*.*), manual dispatch

**Jobs**:
- **Build**
  - Builds Docker image
  - Pushes to Docker Hub
  - Tags with version + latest
  - Uses build cache for speed

- **Deploy Staging** (on manual dispatch)
  - Deploys to staging environment

- **Deploy Production** (on version tags)
  - Deploys to production environment

### 3. Backup Workflow (`backup.yml`)

**Triggers**: Daily at 2 AM UTC, manual dispatch

**Jobs**:
- **Backup**
  - Runs backup script
  - Uploads to S3
  - Saves artifact for 30 days

### Setup GitHub Secrets

Required secrets:
```
DOCKERHUB_USERNAME
DOCKERHUB_TOKEN
NEO4J_URI
NEO4J_USER
NEO4J_PASSWORD
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
S3_BACKUP_BUCKET
```

---

## Docker Deployment

See [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) for complete guide.

### Quick Start

```bash
docker-compose up -d
```

### Services

- **neo4j**: Graph database (ports 7474, 7687)
- **redis**: Cache (port 6379)
- **app**: Research Assistant (port 5000)

### Health Checks

All services have health checks:
- Neo4j: HTTP endpoint check
- Redis: PING command
- App: `/health` endpoint

---

## Database Backups

### Automated Backups

**Daily backups** via GitHub Actions at 2 AM UTC.

### Manual Backup

```bash
# Run backup script
python scripts/backup_database.py

# With S3 upload
python scripts/backup_database.py --upload-s3

# With cleanup
python scripts/backup_database.py --cleanup --keep-days 30
```

### Restore

```bash
python scripts/backup_database.py --restore backups/neo4j_backup_20251123.dump.gz
```

### Backup Features

- **Compression**: gzip compression
- **S3 Upload**: Automatic S3 upload
- **Cleanup**: Remove old backups
- **Logging**: Detailed operation logs

---

## Monitoring

### Application Metrics

Access via endpoints:
- `/health` - Health check
- `/metrics` - Application metrics (planned)

### Log Monitoring

Use log aggregation tools:
- **ELK Stack**: Elasticsearch, Logstash, Kibana
- **Grafana Loki**: For Kubernetes
- **CloudWatch**: For AWS
- **Datadog/New Relic**: For SaaS monitoring

### Container Monitoring

```bash
# Real-time stats
docker stats

# Service health
docker-compose ps

# Application logs
docker-compose logs -f app
```

---

## Security

### Security Scanning

Automated via GitHub Actions:
- **safety**: Checks for known vulnerabilities in dependencies
- **bandit**: Scans code for security issues

### Security Best Practices

1. **Secrets Management**
   - Never commit secrets
   - Use environment variables
   - Use Docker secrets in production

2. **Network Security**
   - Private Docker network
   - Firewall rules
   - TLS/SSL for production

3. **Access Control**
   - Strong database passwords
   - Non-root Docker user
   - Read-only file systems where possible

4. **Dependency Management**
   - Regular updates
   - Security scanning
   - Pin versions in requirements.txt

### Security Checklist

- [ ] Change default passwords
- [ ] Enable TLS/SSL
- [ ] Configure firewall
- [ ] Set up monitoring
- [ ] Regular backups
- [ ] Security scanning
- [ ] Access control
- [ ] Secrets management

---

## Performance Optimization

### Caching

Redis caching with automatic invalidation:
- Query results (1-5 min TTL)
- Graph data (10 min TTL)
- Statistics (1 hour TTL)

### Database Optimization

- 21 Neo4j indexes for fast queries
- Parameterized queries
- Query result limits
- Batch operations

### Frontend Optimization

- Graph pagination (virtual scrolling)
- Level-of-detail rendering
- Web Workers for heavy computation
- QuadTree spatial indexing

---

## Troubleshooting

### Common Issues

**Service won't start**:
```bash
docker-compose logs app
docker-compose restart app
```

**Database connection errors**:
```bash
# Test connection
docker exec research-assistant-neo4j cypher-shell -u neo4j -p password
```

**Out of memory**:
```bash
# Increase Neo4j memory in docker-compose.yml
environment:
  - NEO4J_server_memory_heap_max__size=4G
```

### Support

- GitHub Issues: [Repository Issues](https://github.com/your-repo/issues)
- Documentation: See README.md and ROADMAP.md

---

**Last Updated**: November 23, 2025
