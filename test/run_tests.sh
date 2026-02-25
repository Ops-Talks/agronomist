#!/bin/bash
# Quick test runner for Agronomist workflows

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Agronomist Workflow Test Suite${NC}"
echo ""

# Check dependencies
check_deps() {
    local missing=0
    
    if ! command -v bats &> /dev/null; then
        echo -e "${RED}✗${NC} bats not found. Run: make install-test-deps"
        missing=1
    else
        echo -e "${GREEN}✓${NC} bats found"
    fi
    
    if ! command -v jq &> /dev/null; then
        echo -e "${RED}✗${NC} jq not found. Run: make install-test-deps"
        missing=1
    else
        echo -e "${GREEN}✓${NC} jq found"
    fi
    
    if ! command -v git &> /dev/null; then
        echo -e "${RED}✗${NC} git not found"
        missing=1
    else
        echo -e "${GREEN}✓${NC} git found"
    fi
    
    echo ""
    
    if [ $missing -eq 1 ]; then
        echo -e "${YELLOW}Install missing dependencies with:${NC} make install-test-deps"
        exit 1
    fi
}

check_deps

# Run tests based on argument
case "${1:-all}" in
    unit)
        echo -e "${YELLOW}Running unit tests...${NC}"
        bats test/unit/*.bats
        ;;
    integration)
        echo -e "${YELLOW}Running integration tests...${NC}"
        bash test/integration/test_multi_pr_flow.sh
        ;;
    all|*)
        echo -e "${YELLOW}Running all tests...${NC}"
        echo ""
        bats test/unit/*.bats
        echo ""
        bash test/integration/test_multi_pr_flow.sh
        ;;
esac

echo ""
echo -e "${GREEN}✓ Tests completed successfully!${NC}"
