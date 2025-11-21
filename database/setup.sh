#!/bin/bash
# ============================================================================
# Research Verification Agent System - Database Setup Script
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DB_NAME="${DB_NAME:-research_verification}"
DB_USER="${DB_USER:-postgres}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Research Verification Agent System${NC}"
echo -e "${GREEN}Database Setup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo -e "${RED}ERROR: PostgreSQL is not installed or not in PATH${NC}"
    echo "Please install PostgreSQL 15+ first"
    exit 1
fi

echo -e "${YELLOW}Database Configuration:${NC}"
echo "  Name: $DB_NAME"
echo "  User: $DB_USER"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo ""

# Check if database exists
DB_EXISTS=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" 2>/dev/null || echo "")

if [ "$DB_EXISTS" = "1" ]; then
    echo -e "${YELLOW}Database '$DB_NAME' already exists.${NC}"
    read -p "Do you want to drop and recreate it? (yes/no): " -r
    if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo -e "${YELLOW}Dropping existing database...${NC}"
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "DROP DATABASE IF EXISTS $DB_NAME;"
    else
        echo -e "${YELLOW}Using existing database. Schema will be updated.${NC}"
    fi
fi

# Create database if it doesn't exist
if [ "$DB_EXISTS" != "1" ] || [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo -e "${GREEN}Creating database '$DB_NAME'...${NC}"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "CREATE DATABASE $DB_NAME;"
fi

# Install required extensions
echo -e "${GREEN}Installing PostgreSQL extensions...${NC}"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" <<EOF
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "ltree";
EOF

# Check if pgvector is available
if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null; then
    echo -e "${GREEN}✓ pgvector extension installed${NC}"
else
    echo -e "${YELLOW}⚠ pgvector extension not available (optional for MVP)${NC}"
    echo -e "${YELLOW}  Install later for semantic search features${NC}"
fi

# Run schema creation
echo -e "${GREEN}Creating database schema...${NC}"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$SCRIPT_DIR/schema_v1_mvp.sql"

# Verify tables were created
echo -e "${GREEN}Verifying database setup...${NC}"
TABLE_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")

if [ "$TABLE_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ Database setup complete!${NC}"
    echo -e "${GREEN}  Tables created: $TABLE_COUNT${NC}"
    echo ""
    echo -e "${GREEN}Tables:${NC}"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "\dt"
    echo ""
    echo -e "${GREEN}Views:${NC}"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "\dv"
else
    echo -e "${RED}ERROR: No tables were created${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Configure environment variables in .env"
echo "2. Run: python -m research_agent --help"
echo ""
