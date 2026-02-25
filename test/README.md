# Multi-PR Workflow Tests

## Overview

This directory contains comprehensive tests for the multi-PR functionality in Agronomist workflows (GitHub Actions and GitLab CI).

## Quick Start

```bash
# Install test dependencies
make install-test-deps

# Run all tests
make test-workflows

# Run only unit tests
make test-unit

# Run only integration tests
make test-integration
```

## Structure

```
test/
├── unit/
│   └── test_multi_pr.bats          # BATS unit tests for bash functions
├── integration/
│   └── test_multi_pr_flow.sh       # End-to-end workflow simulation
└── fixtures/
    ├── report_single_module.json   # Single module update scenario
    ├── report_multiple_modules.json # Multiple modules scenario
    └── report_empty.json            # Empty report scenario
```

## Test Coverage

### Unit Tests (`test/unit/test_multi_pr.bats`)

Tests individual bash functions and jq queries:

- ✅ Extract unique modules from report.json
- ✅ Create valid branch names from module paths
- ✅ Extract files for specific modules
- ✅ Handle empty modules list
- ✅ Handle malformed JSON gracefully
- ✅ Validate report.json structure
- ✅ Handle special characters in module names

### Integration Tests (`test/integration/test_multi_pr_flow.sh`)

Tests complete workflow end-to-end:

- ✅ Multi-module scenario (3 modules → 3 PRs/MRs)
- ✅ Single-module scenario
- ✅ Empty report scenario
- ✅ Git branch creation and management
- ✅ Cherry-picking files per module
- ✅ Commit message validation

## Fixtures

### `report_single_module.json`
Simulates a single module update:
- Module: `weyderfs/terraform-aws-modules//vpc/security-group`
- Version: v1.2.0 → v1.3.0
- Files: 2

### `report_multiple_modules.json`
Simulates multiple module updates:
- 3 different modules
- Different categories (aws, database)
- Multiple files

### `report_empty.json`
Simulates no updates available.

## CI Integration

Tests run automatically via `.github/workflows/test-workflows.yml`:

**Jobs:**
1. **unit-tests**: BATS unit tests
2. **integration-tests**: Integration test suite
3. **workflow-validation**: YAML syntax validation
4. **shellcheck**: Shell script linting

## Running Tests Locally

### Prerequisites
```bash
# Ubuntu/Debian
sudo apt-get install -y bats jq git shellcheck

# macOS
brew install bats-core jq shellcheck

# Or use Makefile
make install-test-deps
```

### Run Tests
```bash
# All tests
make test-workflows

# Unit only
bats test/unit/*.bats

# Integration only
bash test/integration/test_multi_pr_flow.sh

# With verbose output
bats --verbose-run test/unit/test_multi_pr.bats
bash -x test/integration/test_multi_pr_flow.sh
```

## Writing Tests

### Add Unit Test

```bash
# In test/unit/test_multi_pr.bats

@test "your test description" {
    # Setup
    expected="value"
    
    # Execute
    actual=$(your_command)
    
    # Assert
    [ "$actual" = "$expected" ]
}
```

### Add Integration Test

```bash
# In test/integration/test_multi_pr_flow.sh

test_your_scenario() {
    log_info "Testing your scenario"
    
    # Test logic here
    
    if [ condition ]; then
        log_error "Failed"
        return 1
    fi
    
    log_info "Passed"
    return 0
}

# Add to main()
if ! test_your_scenario; then
    exit 1
fi
```

## Debugging

### Keep test artifacts
```bash
# Edit cleanup() in integration test
cleanup() {
    echo "Test dir: $TEST_DIR"
    # rm -rf "$TEST_DIR"  # Comment this out
}
```

### Verbose output
```bash
bats -t test/unit/test_multi_pr.bats
bash -x test/integration/test_multi_pr_flow.sh
```

## Documentation

For comprehensive testing guide, see [docs/testing.md](../docs/testing.md).
