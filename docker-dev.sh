#!/bin/bash
# Helper script for Docker development environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

case "${1:-}" in
  build)
    echo -e "${BLUE}Building development Docker image...${NC}"
    docker-compose build
    ;;
  start|up)
    echo -e "${BLUE}Starting development container...${NC}"
    docker-compose up -d
    echo -e "${GREEN}Container started!${NC}"
    echo -e "${BLUE}To enter the container, run: ./docker-dev.sh shell${NC}"
    ;;
  shell|bash)
    echo -e "${BLUE}Entering development container...${NC}"
    docker-compose exec electrumx-dev /bin/bash
    ;;
  stop|down)
    echo -e "${BLUE}Stopping development container...${NC}"
    docker-compose down
    ;;
  restart)
    echo -e "${BLUE}Restarting development container...${NC}"
    docker-compose restart
    ;;
  setup)
    echo -e "${BLUE}Setting up development environment in container...${NC}"
    docker-compose exec electrumx-dev bash -c "
      cd /workspace && \
      [ -d venv ] && rm -rf venv || true && \
      python3 -m venv venv && \
      source venv/bin/activate && \
      pip install --upgrade pip setuptools wheel && \
      pip install pycodestyle pytest pytest-asyncio pytest-cov Sphinx && \
      pip install 'Cython<3.0' && \
      pip install git+https://github.com/jansegre/python-rocksdb.git@314572c02e7204464a5c3e3475c79d57870a9a03 && \
      pip install -e . && \
      echo 'Development environment setup complete!'
    "
    ;;
  test)
    echo -e "${BLUE}Running tests...${NC}"
    docker-compose exec electrumx-dev bash -c "
      cd /workspace && \
      source venv/bin/activate && \
      pytest --cov=electrumx
    "
    ;;
  install)
    echo -e "${BLUE}Installing dependencies...${NC}"
    docker-compose exec electrumx-dev bash -c "
      cd /workspace && \
      source venv/bin/activate && \
      pip install \$@
    "
    ;;
  logs)
    docker-compose logs -f electrumx-dev
    ;;
  server|run)
    echo -e "${BLUE}Starting ElectrumX server...${NC}"
    if [ ! -f .env ]; then
      echo -e "${BLUE}Warning: .env file not found. Creating from .env.example...${NC}"
      if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}.env file created. Please edit it with your configuration.${NC}"
        echo -e "${BLUE}Edit .env and run './docker-dev.sh server' again.${NC}"
        exit 1
      else
        echo -e "${BLUE}Error: .env.example not found. Please create .env manually.${NC}"
        exit 1
      fi
    fi
    docker-compose exec electrumx-dev bash -c "
      cd /workspace && \
      source venv/bin/activate && \
      electrumx_server
    "
    ;;
  server-bg|run-bg)
    echo -e "${BLUE}Starting ElectrumX server in background...${NC}"
    if [ ! -f .env ]; then
      echo -e "${BLUE}Warning: .env file not found. Creating from .env.example...${NC}"
      if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}.env file created. Please edit it with your configuration.${NC}"
        echo -e "${BLUE}Edit .env and run './docker-dev.sh server-bg' again.${NC}"
        exit 1
      else
        echo -e "${BLUE}Error: .env.example not found. Please create .env manually.${NC}"
        exit 1
      fi
    fi
    docker-compose exec -d electrumx-dev bash -c "
      cd /workspace && \
      source venv/bin/activate && \
      electrumx_server
    "
    echo -e "${GREEN}Server started in background. Use './docker-dev.sh logs' to view output.${NC}"
    ;;
  clean)
    echo -e "${BLUE}Cleaning up Docker resources...${NC}"
    docker-compose down -v
    docker system prune -f
    ;;
  *)
    echo "ElectrumX Docker Development Helper"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  build      - Build the development Docker image"
    echo "  start|up   - Start the development container"
    echo "  shell|bash - Enter the container shell"
    echo "  stop|down  - Stop the development container"
    echo "  restart    - Restart the development container"
    echo "  setup      - Set up the Python environment inside the container"
    echo "  test       - Run the test suite"
    echo "  install    - Install Python packages (pass packages as arguments)"
    echo "  logs       - View container logs"
    echo "  server|run - Run ElectrumX server (foreground)"
    echo "  server-bg  - Run ElectrumX server (background)"
    echo "  clean      - Clean up Docker resources"
    echo ""
    echo "Example workflow:"
    echo "  ./docker-dev.sh build    # Build the image"
    echo "  ./docker-dev.sh start    # Start the container"
    echo "  ./docker-dev.sh setup    # Set up Python environment"
    echo "  ./docker-dev.sh shell    # Enter the container"
    echo "  ./docker-dev.sh test     # Run tests"
    ;;
esac

