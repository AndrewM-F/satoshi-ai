#!/bin/bash
set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
USE_DOCKER=false
KEEP_CONTAINERS=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --docker)
      USE_DOCKER=true
      shift
      ;;
    --keep-containers)
      KEEP_CONTAINERS=true
      shift
      ;;
    *)
      echo -e "${RED}❌ Unknown parameter: $1${NC}"
      exit 1
      ;;
  esac
done

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Get the project root directory (one level up from scripts/)
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT" || exit 1

echo -e "${BLUE}🔍 Project root:${NC} $PROJECT_ROOT"

# Activate virtual environment if exists
if [ -d "venv" ]; then
    echo -e "${GREEN}🔌 Activating virtual environment...${NC}"
    source venv/bin/activate
else
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating one...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    echo -e "${GREEN}✅ Created and activated virtual environment${NC}"
fi

echo -e "${BLUE}🐍 Using Python:${NC} $(which python3)"
echo -e "${BLUE}📦 Python version:${NC} $(python3 --version)"

# Upgrade pip and install build tools
echo -e "${GREEN}⬆️  Installing/upgrading build tools...${NC}"
python3 -m pip install --upgrade pip setuptools wheel

# Install the package in development mode with test dependencies
echo -e "${GREEN}📦 Installing dependencies from pyproject.toml...${NC}"
python3 -m pip install -e ".[test]"

# Set Python path
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Function to run tests with Docker Compose
run_docker_tests() {
    echo -e "${BLUE}🐳 Starting test services with Docker Compose...${NC}"
    
    # Start services in detached mode
    docker-compose -f infra/docker-compose.yml -f tests/docker-compose.test.yml up -d
    
    # Wait for services to be ready
    echo -e "${BLUE}⏳ Waiting for services to be ready...${NC}"
    sleep 10
    
    # Run tests
    echo -e "${GREEN}🚀 Running tests...${NC}"
    python3 -m pytest tests/ -v --cov=backend --cov-report=term-missing --cov-report=html
    
    # Store the exit code
    TEST_EXIT_CODE=$?
    
    if [ "$KEEP_CONTAINERS" = false ]; then
        echo -e "${BLUE}♻️  Stopping and removing containers...${NC}"
        docker-compose -f infra/docker-compose.yml -f tests/docker-compose.test.yml down
    else
        echo -e "${YELLOW}ℹ️  Containers are still running. Use 'docker-compose -f infra/docker-compose.yml -f tests/docker-compose.test.yml down' to stop them.${NC}"
    fi
    
    return $TEST_EXIT_CODE
}

# Function to run tests without Docker
run_local_tests() {
    echo -e "${GREEN}🚀 Running tests locally...${NC}"
    python3 -m pytest tests/ -v --cov=backend --cov-report=term-missing --cov-report=html
}

# Run the appropriate test command
if [ "$USE_DOCKER" = true ]; then
    run_docker_tests
    TEST_EXIT_CODE=$?
else
    run_local_tests
    TEST_EXIT_CODE=$?
fi

# Note: Virtual environment remains active after script runs
echo -e "${GREEN}✨ Test run completed!${NC}"
echo -e "💡 Virtual environment is still active. Run 'deactivate' to exit."

exit $TEST_EXIT_CODE
