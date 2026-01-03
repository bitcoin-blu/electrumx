#!/bin/bash
# ElectrumX Ubuntu Installation Script
# This script installs all dependencies and sets up ElectrumX on a fresh Ubuntu system

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ELECTRUMX_DIR="${ELECTRUMX_DIR:-$(pwd)}"
VENV_DIR="${VENV_DIR:-$ELECTRUMX_DIR/venv}"
DB_DIR="${DB_DIR:-/var/lib/electrumx}"
USER="${USER:-$(whoami)}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}ElectrumX Ubuntu Installation Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo -e "${RED}Error: Do not run this script as root.${NC}"
   echo "The script will use sudo when needed for system packages."
   exit 1
fi

# Detect Ubuntu version
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VER=$VERSION_ID
    echo -e "${GREEN}Detected: $OS $VER${NC}"
else
    echo -e "${YELLOW}Warning: Could not detect OS version${NC}"
    OS="unknown"
fi

# Check Python version
echo -e "${GREEN}Checking Python version...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
        echo -e "${RED}Error: Python 3.10+ is required. Found: $PYTHON_VERSION${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
else
    echo -e "${RED}Error: Python 3 not found${NC}"
    exit 1
fi

# Update package list
echo ""
echo -e "${GREEN}Updating package list...${NC}"
sudo apt-get -qq update

# Install system dependencies
echo ""
echo -e "${GREEN}Installing system dependencies...${NC}"
sudo apt-get install -yq --no-install-recommends \
    git \
    python3 \
    python3-pip \
    python3-setuptools \
    python3-venv \
    libsnappy-dev \
    zlib1g-dev \
    libbz2-dev \
    libgflags-dev \
    liblz4-dev \
    librocksdb-dev \
    libleveldb-dev \
    libboost-all-dev \
    libsodium-dev \
    build-essential \
    curl \
    wget

echo -e "${GREEN}✓ System dependencies installed${NC}"

# Create database directory
echo ""
echo -e "${GREEN}Setting up database directory...${NC}"
if [ ! -d "$DB_DIR" ]; then
    sudo mkdir -p "$DB_DIR"
    sudo chown $USER:$USER "$DB_DIR"
    echo -e "${GREEN}✓ Created database directory: $DB_DIR${NC}"
else
    echo -e "${YELLOW}Database directory already exists: $DB_DIR${NC}"
fi

# Navigate to ElectrumX directory
if [ ! -d "$ELECTRUMX_DIR" ]; then
    echo -e "${YELLOW}ElectrumX directory not found: $ELECTRUMX_DIR${NC}"
    echo "If you haven't cloned the repository yet, run:"
    echo "  git clone https://github.com/spesmilo/electrumx.git"
    echo "  cd electrumx"
    echo "  ./install-ubuntu.sh"
    exit 1
fi

cd "$ELECTRUMX_DIR"

# Create virtual environment
echo ""
echo -e "${GREEN}Setting up Python virtual environment...${NC}"
if [ -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Virtual environment already exists. Removing old one...${NC}"
    rm -rf "$VENV_DIR"
fi

python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo ""
echo -e "${GREEN}Upgrading pip...${NC}"
pip install --upgrade pip setuptools wheel

# Install Cython for rocksdb (if needed)
echo ""
echo -e "${GREEN}Installing Cython (required for rocksdb)...${NC}"
pip install 'Cython<3.0'

# Install ElectrumX with optional dependencies
echo ""
echo -e "${GREEN}Installing ElectrumX...${NC}"
echo "This may take several minutes..."

# Install with rocksdb support (optional but recommended)
if pip install ".[rocksdb]" 2>/dev/null; then
    echo -e "${GREEN}✓ ElectrumX installed with RocksDB support${NC}"
else
    echo -e "${YELLOW}Installing without rocksdb extra...${NC}"
    pip install .
    echo -e "${GREEN}✓ ElectrumX installed (LevelDB only)${NC}"
fi

# Verify installation
echo ""
echo -e "${GREEN}Verifying installation...${NC}"
if command -v electrumx_server &> /dev/null || [ -f "$VENV_DIR/bin/electrumx_server" ]; then
    echo -e "${GREEN}✓ ElectrumX installed successfully!${NC}"
else
    echo -e "${RED}✗ Installation verification failed${NC}"
    exit 1
fi

# Create example environment file
echo ""
echo -e "${GREEN}Creating example configuration...${NC}"
if [ ! -f "$ELECTRUMX_DIR/.env.example" ]; then
    cat > "$ELECTRUMX_DIR/.env.example" << 'EOF'
# ElectrumX Server Configuration
# Copy this file to .env and fill in your actual values

# REQUIRED: Coin name (e.g., Bitcoin, BitcoinTestnet, BitcoinBlu)
COIN=Bitcoin

# REQUIRED: Network (mainnet, testnet, regtest, main-blu, etc.)
NET=mainnet

# REQUIRED: Database directory path
DB_DIRECTORY=/var/lib/electrumx

# REQUIRED: Bitcoin daemon RPC URL
# Format: http://username:password@hostname:port/
DAEMON_URL=http://rpcuser:rpcpassword@localhost:8332/

# Services to offer (comma-separated)
SERVICES=tcp://:50001,rpc://

# Database engine (leveldb or rocksdb)
DB_ENGINE=leveldb

# Cache size in MB (default: 1200, max recommended: 2000)
CACHE_MB=1200

# Optional: Log level (debug, info, warning, error)
LOG_LEVEL=info
EOF
    echo -e "${GREEN}✓ Created .env.example${NC}"
fi

# Summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Installation Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo ""
echo "1. Activate the virtual environment:"
echo "   source $VENV_DIR/bin/activate"
echo ""
echo "2. Configure ElectrumX:"
echo "   cp .env.example .env"
echo "   nano .env  # Edit with your settings"
echo ""
echo "3. For BitcoinBLU, use these settings in .env:"
echo "   COIN=BitcoinBlu"
echo "   NET=main-blu"
echo "   DAEMON_URL=http://rpcuser:rpcpassword@localhost:8342/"
echo ""
echo "4. Start the server:"
echo "   electrumx_server"
echo ""
echo "Or run in the background:"
echo "   nohup electrumx_server > electrumx.log 2>&1 &"
echo ""
echo "Database directory: $DB_DIR"
echo "Virtual environment: $VENV_DIR"
echo ""
echo -e "${YELLOW}Note: Make sure your Bitcoin/BitcoinBLU daemon is running${NC}"
echo -e "${YELLOW}      with txindex=1 in its configuration file.${NC}"
echo ""

