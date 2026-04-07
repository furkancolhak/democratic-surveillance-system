#!/bin/bash

# Test Runner Script
# Runs all test suites with proper error handling

set -e  # Exit on error

echo "======================================================================"
echo "  🔬 SURVEILLANCE SYSTEM - TEST SUITE"
echo "======================================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -d "tests" ]; then
    echo -e "${RED}❌ Error: Must run from project root directory${NC}"
    exit 1
fi

# Function to run a test
run_test() {
    local test_name=$1
    local test_file=$2
    
    echo ""
    echo "======================================================================"
    echo "  Running: $test_name"
    echo "======================================================================"
    
    if python "$test_file"; then
        echo -e "${GREEN}✅ $test_name PASSED${NC}"
        return 0
    else
        echo -e "${RED}❌ $test_name FAILED${NC}"
        return 1
    fi
}

# Track results
TOTAL=0
PASSED=0
FAILED=0

# Quick smoke test
echo "🚀 Starting with quick smoke test..."
if run_test "Quick Smoke Test" "tests/quick_test.py"; then
    ((PASSED++))
else
    ((FAILED++))
fi
((TOTAL++))

# Comprehensive unit tests
if run_test "Comprehensive Unit Tests" "tests/test_comprehensive.py"; then
    ((PASSED++))
else
    ((FAILED++))
fi
((TOTAL++))

# Database tests (optional)
echo ""
echo "======================================================================"
echo "  Checking database availability..."
echo "======================================================================"

if python -c "import sys; sys.path.append('app/core'); from database import db_manager; session = db_manager.get_session(); session.execute('SELECT 1'); session.close()" 2>/dev/null; then
    echo -e "${GREEN}✅ Database available${NC}"
    
    if run_test "Database Integration Tests" "tests/test_with_database.py"; then
        ((PASSED++))
    else
        ((FAILED++))
    fi
    ((TOTAL++))
else
    echo -e "${YELLOW}⚠️  Database not available - skipping integration tests${NC}"
    echo "   To run database tests:"
    echo "   cd docker && docker-compose up -d postgres"
fi

# Final summary
echo ""
echo "======================================================================"
echo "  📊 FINAL SUMMARY"
echo "======================================================================"
echo "Total Tests: $TOTAL"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
    echo "✅ System is ready"
    exit 0
else
    echo -e "${RED}⚠️  SOME TESTS FAILED${NC}"
    echo "❌ Please review failures"
    exit 1
fi
