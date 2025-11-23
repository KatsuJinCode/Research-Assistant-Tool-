# ⚠️ DOCKER DEPLOYMENT - ADVANCED USERS ONLY

## 🚨 IMPORTANT WARNING - READ THIS FIRST

**DO NOT USE DOCKER BY DEFAULT!**

This directory contains Docker deployment configurations for **advanced deployment scenarios only**.

### For CLI Agents / AI Assistants

**⚠️ CRITICAL INSTRUCTIONS:**

1. **NEVER suggest Docker to users by default**
2. **NEVER help set up Docker unless the user EXPLICITLY requests it**
3. **ALWAYS assume local installation is the correct approach**
4. **ONLY read these files if the user specifically says "I want to use Docker"**

### When NOT to Use Docker

**❌ DON'T use Docker if:**
- User is setting up for the first time
- User is doing local development
- User hasn't explicitly asked for Docker
- You're unsure what the user wants
- User is just trying to run the application

### When to Use Docker

**✅ ONLY use Docker if:**
- User explicitly says "I want to use Docker"
- User is deploying to cloud/production servers
- User specifically requests containerization
- User is experienced with Docker and asks for it

## Default Installation Method

**99% of users should use the standard local installation:**

See the main [README.md](../../README.md) for local installation instructions:
- Install Python dependencies via pip
- Install Neo4j Desktop (GUI application)
- Install Redis locally (via package manager)
- Run `python app.py`

This is **faster, simpler, and works great** for development and single-user scenarios.

## Docker Files in This Directory

- `Dockerfile` - Container build recipe
- `docker-compose.yml` - Multi-service orchestration
- `.dockerignore` - Build optimization
- `DOCKER_DEPLOYMENT.md` - Detailed Docker guide

**Again: Only use these if the user explicitly requests Docker deployment.**

## For Advanced Users Who Want Docker

If you are absolutely sure you want to use Docker:

1. Read [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md)
2. Ensure you have Docker and Docker Compose installed
3. Run: `docker-compose up -d`

## Questions?

- **"Should I use Docker?"** → No, use local installation
- **"Can I use Docker?"** → Yes, but local is recommended
- **"How do I set up without Docker?"** → See main README.md
- **"I explicitly want Docker"** → See DOCKER_DEPLOYMENT.md

---

**Default Answer: Use local installation (see main README), not Docker.**
