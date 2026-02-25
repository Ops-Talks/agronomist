# Testing Guide

This guide covers the testing infrastructure for Agronomist workflows, including unit tests, integration tests, and CI/CD validation.

## Overview

The test suite ensures that the multi-PR workflow logic functions correctly across different scenarios:

- **Unit Tests**: Test individual bash functions and jq queries
- **Integration Tests**: Test the complete multi-PR flow end-to-end
- **Workflow Validation**: Validate YAML syntax and shell scripts

## Test Structure

```
test/
├── unit/                       # BATS unit tests
│   └── test_multi_pr.bats     # Multi-PR logic tests
├── integration/                # Integration tests
│   └── test_multi_pr_flow.sh  # End-to-end workflow simulation
└── fixtures/                   # Test data
    ├── report_single_module.json
    ├── report_multiple_modules.json
    └── report_empty.json
```

## Prerequisites

### Install Test Dependencies

**Using Makefile (Recommended):**
```bash
make install-test-deps
```

**Manual Installation:**

**macOS:**
```bash
brew install bats-core jq shellcheck
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y bats jq shellcheck git
```

**Windows (WSL):**
```bash
sudo apt-get update
sudo apt-get install -y bats jq shellcheck git
```

## Running Tests

### Run All Tests
```bash
make test
```

### Run Unit Tests Only
```bash
make test-unit
# or
bats test/unit/*.bats
```

### Run Integration Tests Only
```bash
make test-integration
# or
bash test/integration/test_multi_pr_flow.sh
```

### Run Linting
```bash
make lint
```

## Unit Tests

Unit tests use [BATS (Bash Automated Testing System)](https://github.com/bats-core/bats-core) to test individual components.

### Example Test Cases

**Extract modules from JSON:**
```bash
@test "extract unique modules from report.json" {
    modules=$(jq -r '.updates[].module' report.json | sort -u)
    module_count=$(echo "$modules" | wc -l)
    [ "$module_count" -eq 2 ]
}
```

**Branch naming:**
```bash
@test "create valid branch name from module with slashes" {
    module="weyderfs/terraform-aws-modules//vpc/security-group"
    branch_name="agronomist/update-$(echo "$module" | sed 's/\//-/g')"
    [ "$branch_name" = "agronomist/update-weyderfs-terraform-aws-modules--vpc-security-group" ]
}
```

### Running Individual Tests
```bash
bats test/unit/test_multi_pr.bats --filter "extract modules"
```

## Integration Tests

Integration tests simulate the complete multi-PR workflow:

1. Create test Git repository
2. Add files with old module versions
3. Simulate Agronomist updates
4. Execute multi-PR logic
5. Validate branches and commits

### Test Scenarios

- **Multiple Modules**: Creates 3 separate branches for 3 different modules
- **Single Module**: Validates single-module workflow
- **Empty Report**: Handles case with no updates

### Output Example

```bash
[INFO] Starting multi-PR integration tests
[INFO] Setting up test repository in /tmp/tmp.abc123
[INFO] Test repository initialized
[INFO] Simulating agronomist update
[INFO] Files updated
[INFO] Testing multi-PR logic with report_multiple_modules.json
[INFO] Found 3 unique modules
[INFO] Created temporary commit: a1b2c3d
[INFO] Processing module: weyderfs/terraform-aws-modules//vpc/security-group
[INFO] Created branch: agronomist/update-weyderfs-terraform-aws-modules--vpc-security-group
[INFO] Processing module: hashicorp/terraform-provider-aws
[INFO] Created branch: agronomist/update-hashicorp-terraform-provider-aws
[INFO] Processing module: terraform-aws-modules/rds/aws
[INFO] Created branch: agronomist/update-terraform-aws-modules-rds-aws
[INFO] Processed 3 modules successfully
[INFO] All integration tests passed! ✓
```

## Test Fixtures

Fixtures are located in `test/fixtures/` and provide sample `report.json` files:

### Single Module (`report_single_module.json`)
```json
{
  "updates": [
    {
      "module": "weyderfs/terraform-aws-modules//vpc/security-group",
      "current_ref": "v1.2.0",
      "latest_ref": "v1.3.0",
      "files": ["infra/main.tf"]
    }
  ]
}
```

### Multiple Modules (`report_multiple_modules.json`)
```json
{
  "updates": [
    {"module": "module-a", "files": ["file1.tf"]},
    {"module": "module-b", "files": ["file2.tf"]},
    {"module": "module-c", "files": ["file3.tf"]}
  ]
}
```

### Empty Report (`report_empty.json`)
```json
{
  "updates": []
}
```

## CI/CD Integration

Tests run automatically on GitHub Actions:

### Workflow: `.github/workflows/test-workflows.yml`

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main`
- Changes to `examples/workflows/**` or `test/**`
- Manual workflow dispatch

**Jobs:**
1. **unit-tests**: Runs BATS unit tests
2. **integration-tests**: Runs integration test suite
3. **workflow-validation**: Validates YAML syntax
4. **shellcheck**: Lints shell scripts

### View Test Results

```bash
# View latest test run
gh run list --workflow=test-workflows.yml

# View specific run
gh run view <run-id>
```

## Writing New Tests

### Adding Unit Tests

Create new test in `test/unit/test_multi_pr.bats`:

```bash
@test "describe what you're testing" {
    # Setup
    expected_value="something"
    
    # Execute
    actual_value=$(your_command_here)
    
    # Assert
    [ "$actual_value" = "$expected_value" ]
}
```

### Adding Integration Tests

Add new test function in `test/integration/test_multi_pr_flow.sh`:

```bash
test_your_scenario() {
    log_info "Testing your scenario"
    
    # Setup test data
    # Run logic
    # Validate results
    
    if [ condition ]; then
        log_error "Test failed"
        return 1
    fi
    
    log_info "Test passed"
    return 0
}
```

Call from `main()`:

```bash
if ! test_your_scenario; then
    log_error "Your scenario test failed"
    exit 1
fi
```

## Debugging Tests

### Enable Verbose Output

**BATS:**
```bash
bats --verbose-run test/unit/test_multi_pr.bats
```

**Integration:**
```bash
bash -x test/integration/test_multi_pr_flow.sh
```

### Keep Test Artifacts

Modify `cleanup()` in integration test:

```bash
cleanup() {
    log_info "Test directory: $TEST_DIR"
    # Comment out to keep artifacts:
    # rm -rf "$TEST_DIR"
}
```

## Common Issues

### BATS not found
```bash
make install-test-deps
```

### jq command not found
```bash
sudo apt-get install jq
# or
brew install jq
```

### Permission denied
```bash
chmod +x test/integration/test_multi_pr_flow.sh
```

## Best Practices

1. **Isolation**: Each test should be independent
2. **Cleanup**: Always clean up test artifacts
3. **Assertions**: Use clear, descriptive assertions
4. **Fixtures**: Use fixtures for complex test data
5. **Documentation**: Comment complex test logic

## Contributing Tests

When contributing workflow changes:

1. ✅ Add unit tests for new bash functions
2. ✅ Add integration tests for new workflows
3. ✅ Update fixtures if report structure changes
4. ✅ Run `make test` before submitting PR
5. ✅ Ensure CI passes

## Resources

- [BATS Documentation](https://bats-core.readthedocs.io/)
- [jq Manual](https://stedolan.github.io/jq/manual/)
- [ShellCheck Wiki](https://github.com/koalaman/shellcheck/wiki)
- [Bash Testing Tutorial](https://github.com/bats-core/bats-core#tutorial)
