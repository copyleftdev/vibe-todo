#!/bin/bash
#
# Pre-commit hook to ensure all tests pass before allowing a commit
# This enforces the rule that all Hypothesis tests must pass before any code is committed
#

# Store the current directory
REPO_ROOT=$(git rev-parse --show-toplevel)

# Set up colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Running pre-commit test validation...${NC}"
echo -e "${YELLOW}This ensures all tests pass before code can be committed.${NC}"

# Set PYTHONPATH to include the project root
export PYTHONPATH=$REPO_ROOT

# Run the unit tests
echo -e "${YELLOW}Running unit tests...${NC}"
pytest $REPO_ROOT/tests/test_unit.py
UNIT_RESULT=$?

# Run the hypothesis tests
echo -e "${YELLOW}Running hypothesis tests...${NC}"
pytest $REPO_ROOT/tests/test_hypothesis.py
HYPOTHESIS_RESULT=$?

# Run the regression tests
echo -e "${YELLOW}Running regression tests...${NC}"
pytest $REPO_ROOT/tests/test_regression.py
REGRESSION_RESULT=$?

# Only run a quick subset of benchmark tests as they can be time-consuming
echo -e "${YELLOW}Running basic benchmark tests...${NC}"
python $REPO_ROOT/tests/test_benchmark.py --quick
BENCHMARK_RESULT=$?

# Check if any tests failed
if [ $UNIT_RESULT -ne 0 ] || [ $HYPOTHESIS_RESULT -ne 0 ] || [ $REGRESSION_RESULT -ne 0 ] || [ $BENCHMARK_RESULT -ne 0 ]; then
    echo -e "${RED}Tests failed! Commit rejected.${NC}"
    echo -e "${YELLOW}Please fix the failing tests before committing.${NC}"
    
    # Report which tests failed
    [ $UNIT_RESULT -ne 0 ] && echo -e "${RED}✗ Unit tests failed${NC}"
    [ $HYPOTHESIS_RESULT -ne 0 ] && echo -e "${RED}✗ Hypothesis tests failed${NC}"
    [ $REGRESSION_RESULT -ne 0 ] && echo -e "${RED}✗ Regression tests failed${NC}"
    [ $BENCHMARK_RESULT -ne 0 ] && echo -e "${RED}✗ Benchmark tests failed${NC}"
    
    exit 1
fi

# All tests passed
echo -e "${GREEN}All tests passed! Proceeding with commit.${NC}"
exit 0
