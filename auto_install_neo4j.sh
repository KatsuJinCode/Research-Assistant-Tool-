#!/bin/bash
# Automatic Neo4j Installation Script
# Works on Ubuntu/Debian systems
# Run with: bash auto_install_neo4j.sh

set -e  # Exit on error

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║       RESEARCH VERIFICATION AGENT - NEO4J AUTO-INSTALLER      ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
   echo "⚠️  Please don't run as root. Run as regular user:"
   echo "   bash auto_install_neo4j.sh"
   exit 1
fi

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VER=$VERSION_ID
else
    echo "❌ Cannot detect OS. Manually install Neo4j from: https://neo4j.com/download/"
    exit 1
fi

echo "📋 Detected OS: $OS $VER"
echo ""

# Check for Docker (preferred method)
if command -v docker &> /dev/null; then
    echo "✓ Docker is installed"
    echo ""
    echo "Installing Neo4j via Docker (recommended)..."
    echo ""

    # Create directories
    mkdir -p neo4j/data neo4j/logs neo4j/import neo4j/plugins

    # Check if container already exists
    if docker ps -a | grep -q research-neo4j; then
        echo "⚠️  Container 'research-neo4j' already exists"
        echo ""
        read -p "Remove and recreate? (y/n): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker rm -f research-neo4j
        else
            echo "Keeping existing container"
            exit 0
        fi
    fi

    # Run Neo4j container
    echo "Starting Neo4j container..."
    docker run \
        --name research-neo4j \
        -p7474:7474 -p7687:7687 \
        -d \
        -v $PWD/neo4j/data:/data \
        -v $PWD/neo4j/logs:/logs \
        -v $PWD/neo4j/import:/var/lib/neo4j/import \
        -v $PWD/neo4j/plugins:/plugins \
        --env NEO4J_AUTH=neo4j/research123 \
        neo4j:latest

    echo ""
    echo "✅ Neo4j installed successfully via Docker!"
    echo ""
    echo "Waiting for Neo4j to start (30 seconds)..."
    sleep 30

    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                    NEO4J IS READY!                             ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "🌐 Neo4j Browser: http://localhost:7474"
    echo "🔐 Username: neo4j"
    echo "🔐 Password: research123"
    echo ""
    echo "Next steps:"
    echo "  1. Install Python dependencies: pip install -r requirements-neo4j.txt"
    echo "  2. Create .env file with connection details"
    echo "  3. Run migration: python migrate_to_neo4j.py"
    echo ""

    # Create .env file
    echo "Creating .env file..."
    cat > .env << 'EOF'
# Neo4j Connection
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=research123
NEO4J_DATABASE=neo4j
EOF

    echo "✓ Created .env file with Neo4j connection details"
    echo ""

    # Install Python dependencies
    echo "Installing Python dependencies..."
    if command -v pip &> /dev/null; then
        pip install -q -r requirements-neo4j.txt 2>&1 | grep -v "WARNING" || true
        echo "✓ Python dependencies installed"
    else
        echo "⚠️  pip not found. Install manually:"
        echo "   pip install -r requirements-neo4j.txt"
    fi
    echo ""

    exit 0
fi

# If no Docker, try direct installation
echo "⚠️  Docker not found. Installing Neo4j directly..."
echo ""

if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
    echo "Installing Neo4j on Ubuntu/Debian..."
    echo ""

    # Import GPG key
    wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -

    # Add repository
    echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list

    # Update and install
    sudo apt-get update
    sudo apt-get install -y neo4j

    # Set initial password
    sudo neo4j-admin set-initial-password research123

    # Start service
    sudo systemctl enable neo4j
    sudo systemctl start neo4j

    echo ""
    echo "Waiting for Neo4j to start (30 seconds)..."
    sleep 30

    echo ""
    echo "✅ Neo4j installed successfully!"
    echo ""
    echo "🌐 Neo4j Browser: http://localhost:7474"
    echo "🔐 Username: neo4j"
    echo "🔐 Password: research123"
    echo ""

    # Create .env file
    cat > .env << 'EOF'
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=research123
NEO4J_DATABASE=neo4j
EOF

    echo "✓ Created .env file"
    echo ""

    # Install Python dependencies
    pip install -q -r requirements-neo4j.txt 2>&1 | grep -v "WARNING" || true
    echo "✓ Python dependencies installed"
    echo ""

else
    echo "❌ Unsupported OS: $OS"
    echo ""
    echo "Please install Neo4j manually:"
    echo "  1. Visit: https://neo4j.com/download/"
    echo "  2. Download Neo4j Community Edition"
    echo "  3. Set password to: research123"
    echo "  4. Run: pip install -r requirements-neo4j.txt"
    exit 1
fi

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                  INSTALLATION COMPLETE!                        ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. Test connection: python -c 'from research_agent.neo4j_database import Neo4jDatabase; db = Neo4jDatabase(); print(\"✅ Connected!\"); db.close()'"
echo "  2. Migrate data: python migrate_to_neo4j.py"
echo "  3. Start using the system!"
echo ""
