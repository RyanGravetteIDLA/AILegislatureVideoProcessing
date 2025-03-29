#!/bin/bash
# Script to run tests for the Idaho Legislative Media Portal

# Enable strict error handling
set -e

# Define color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Print a header
echo -e "${YELLOW}======================================${NC}"
echo -e "${YELLOW}Idaho Legislative Media Portal Tests${NC}"
echo -e "${YELLOW}======================================${NC}"

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest is not installed.${NC}"
    echo "Installing required packages..."
    pip install -r requirements.txt
fi

# Process command line arguments
RUN_INTEGRATION=false
COVERAGE=false
VERBOSE=false

for arg in "$@"
do
    case $arg in
        --integration|-i)
        RUN_INTEGRATION=true
        shift
        ;;
        --coverage|-c)
        COVERAGE=true
        shift
        ;;
        --verbose|-v)
        VERBOSE=true
        shift
        ;;
        --help|-h)
        echo "Usage: $0 [options]"
        echo "Options:"
        echo "  --integration, -i  Run integration tests"
        echo "  --coverage, -c     Generate coverage report"
        echo "  --verbose, -v      Verbose output"
        echo "  --help, -h         Show this help message"
        exit 0
        ;;
    esac
done

# Run the tests
echo -e "${YELLOW}Running unit tests...${NC}"

PYTEST_ARGS=""

if $VERBOSE; then
    PYTEST_ARGS="-v"
fi

if $COVERAGE; then
    PYTEST_ARGS="${PYTEST_ARGS} --cov=src --cov-report=term --cov-report=html:coverage_html"
fi

# Run unit tests
python -m pytest tests/unit/ ${PYTEST_ARGS}

# Run integration tests if requested
if $RUN_INTEGRATION; then
    echo -e "\n${YELLOW}Running integration tests...${NC}"
    
    # Check if credentials are available
    if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
        echo -e "${YELLOW}Warning: GOOGLE_APPLICATION_CREDENTIALS not set. Looking for credential files...${NC}"
        
        # Look for credential files in common locations
        CRED_FILES=(
            "credentials/legislativevideoreviewswithai-80ed70b021b5.json"
            "credentials/service_account.json"
        )
        
        for cred_file in "${CRED_FILES[@]}"; do
            if [ -f "$cred_file" ]; then
                export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/$cred_file"
                echo -e "${GREEN}Using credentials: $GOOGLE_APPLICATION_CREDENTIALS${NC}"
                break
            fi
        done
        
        if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
            echo -e "${RED}No credential file found. Integration tests may fail.${NC}"
        fi
    fi
    
    # Run the integration tests
    python -m pytest tests/integration/ ${PYTEST_ARGS} || echo -e "${RED}Integration tests failed${NC}"
fi

# Print summary
echo -e "\n${GREEN}Test run completed!${NC}"
if $COVERAGE; then
    echo -e "${YELLOW}Coverage report generated in 'coverage_html' directory${NC}"
    echo -e "${YELLOW}Open 'coverage_html/index.html' in your browser to view detailed coverage${NC}"
fi