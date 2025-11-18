# Setup Guide - Research Assistant Tool

Quick guide to get the Research Assistant Tool running on your local machine.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Docker** (20.10 or higher) and **Docker Compose** (2.0 or higher)
- **Git** (2.30 or higher)
- **Python 3.11+** (for local development without Docker)
- **Node.js 18+** and **npm** (for local development without Docker)

## Quick Start with Docker (Recommended)

This is the fastest way to get started:

```bash
# 1. Clone the repository
git clone <repository-url>
cd Research-Assistant-Tool-

# 2. Copy environment file
cp .env.example .env

# 3. Edit .env file with your API keys
# At minimum, set:
# - OPENAI_API_KEY (for AI features)
# - SECRET_KEY (generate a random string)
# - JWT_SECRET_KEY (generate a random string)
nano .env  # or use your preferred editor

# 4. Start all services with Docker Compose
docker-compose up -d

# 5. Wait for services to start (check with)
docker-compose logs -f

# 6. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Documentation: http://localhost:8000/api/docs
```

### Verify Installation

```bash
# Check if all containers are running
docker-compose ps

# Test backend API
curl http://localhost:8000/health

# Check logs if something isn't working
docker-compose logs backend
docker-compose logs frontend
```

## Local Development Setup (Without Docker)

If you prefer to run services locally:

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt

# Set up environment variables
cp ../.env.example ../.env
# Edit .env with your configuration

# Start PostgreSQL and Redis (you'll need these running)
# Option 1: Use Docker for just the databases
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=research_password postgres:15
docker run -d -p 6379:6379 redis:7-alpine

# Option 2: Install and run locally
# (instructions vary by OS)

# Run database migrations (once implemented)
# alembic upgrade head

# Start the backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp ../.env.example .env.local
# Edit .env.local if needed

# Start development server
npm run dev

# Access at http://localhost:3000
```

## Configuration

### Required Environment Variables

Edit your `.env` file with these required values:

```bash
# Security (REQUIRED - generate random strings)
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here

# AI Services (REQUIRED for AI features)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Optional but recommended
ANTHROPIC_API_KEY=sk-your-anthropic-api-key-here
```

### Generate Secure Keys

```bash
# Generate random secret keys
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Running Tests

### Backend Tests

```bash
cd backend
source venv/bin/activate  # if not already activated

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_main.py
```

### Frontend Tests

```bash
cd frontend

# Run unit tests
npm test

# Run with coverage
npm run test:coverage

# Run E2E tests (requires app to be running)
npm run test:e2e
```

## Common Commands

### Docker Compose Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Rebuild services after code changes
docker-compose up -d --build

# View logs
docker-compose logs -f [service-name]

# Execute command in container
docker-compose exec backend bash
docker-compose exec frontend sh

# Reset everything (WARNING: deletes data)
docker-compose down -v
```

### Database Commands

```bash
# Access PostgreSQL
docker-compose exec postgres psql -U research_user -d research_assistant

# Create migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Rollback migration
docker-compose exec backend alembic downgrade -1
```

## Troubleshooting

### Port Already in Use

If you get "port already in use" errors:

```bash
# Check what's using the port
lsof -i :8000  # or :3000, :5432, :6379

# Stop the process or change the port in docker-compose.yml
```

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# View PostgreSQL logs
docker-compose logs postgres

# Reset database
docker-compose down
docker volume rm research-assistant-tool-_postgres_data
docker-compose up -d
```

### Frontend Build Errors

```bash
# Clear node_modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install

# Clear Next.js cache
rm -rf .next
npm run dev
```

### Backend Import Errors

```bash
# Make sure you're in the virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Check Python path
echo $PYTHONPATH
```

## Development Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes and test**
   ```bash
   # Run tests frequently
   pytest  # backend
   npm test  # frontend
   ```

3. **Format code**
   ```bash
   # Backend
   black app/
   ruff check app/

   # Frontend
   npm run format
   npm run lint
   ```

4. **Commit and push**
   ```bash
   git add .
   git commit -m "feat: description of changes"
   git push origin feature/your-feature-name
   ```

5. **Create pull request**

## Production Deployment

See [docs/deployment.md](docs/deployment.md) for production deployment instructions (coming soon).

## Getting Help

- Check [README.md](README.md) for project overview
- See [PROJECT_PLAN.md](PROJECT_PLAN.md) for detailed architecture
- See [ROADMAP.md](ROADMAP.md) for development timeline
- See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines
- Open an issue for bugs or questions

## Next Steps

Once everything is running:

1. Visit http://localhost:8000/api/docs to explore the API
2. Visit http://localhost:3000 to use the frontend
3. Read [CONTRIBUTING.md](CONTRIBUTING.md) to start contributing
4. Check [ROADMAP.md](ROADMAP.md) to see what's being built next

Happy coding! 🚀
