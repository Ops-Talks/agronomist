# Local Testing Quick Reference

## Prerequisites

Ensure you have the required tools installed:

```bash
make install-test-deps
```

Or manually:
```bash
# Ubuntu/Debian
sudo apt-get install -y bats jq git shellcheck

# macOS
brew install bats-core jq shellcheck
```

## Running Tests

### Quick Test (All)
```bash
./test/run_tests.sh
# or
make test-workflows
```

### Unit Tests Only
```bash
./test/run_tests.sh unit
# or
make test-unit
# or
bats test/unit/*.bats
```

### Integration Tests Only
```bash
./test/run_tests.sh integration
# or
make test-integration
# or
bash test/integration/test_multi_pr_flow.sh
```

## Test Scenarios

### Single Module Update
```bash
# Uses: test/fixtures/report_single_module.json
# Expected: 1 branch created
# Module: weyderfs/terraform-aws-modules//vpc/security-group
```

### Multiple Modules Update
```bash
# Uses: test/fixtures/report_multiple_modules.json
# Expected: 3 branches created
# Modules:
#   - weyderfs/terraform-aws-modules//vpc/security-group
#   - hashicorp/terraform-provider-aws
#   - terraform-aws-modules/rds/aws
```

### Empty Report
```bash
# Uses: test/fixtures/report_empty.json
# Expected: No branches created
```

## Debugging

### Verbose Output
```bash
# Unit tests with verbose output
bats --verbose-run test/unit/test_multi_pr.bats

# Integration tests with debug
bash -x test/integration/test_multi_pr_flow.sh
```

### Keep Test Artifacts
Edit `test/integration/test_multi_pr_flow.sh`:
```bash
cleanup() {
    echo "Test dir: $TEST_DIR"
    # Comment out to inspect:
    # rm -rf "$TEST_DIR"
}
```

### Run Specific Test
```bash
# Run single test by name
bats test/unit/test_multi_pr.bats --filter "extract modules"
```

## Common Test Commands

### Validate JQ Queries
```bash
# Test module extraction
echo '{"updates":[{"module":"test/module"}]}' | jq -r '.updates[].module'

# Test module filtering
echo '{"updates":[{"module":"test/module","files":["a.tf"]}]}' | \
  jq -r --arg mod "test/module" '.updates[] | select(.module==$mod) | .files[]'
```

### Validate Branch Naming
```bash
# Test sed replacement
module="weyderfs/terraform-aws-modules//vpc/security-group"
echo "$module" | sed 's/\//-/g'
# Output: weyderfs-terraform-aws-modules--vpc-security-group
```

### Test Git Operations
```bash
# Initialize test repo
cd $(mktemp -d)
git init
git config user.email "test@test.com"
git config user.name "Test"

# Create test commit
echo "content" > file.txt
git add file.txt
git commit -m "Test"
commit=$(git rev-parse HEAD)

# Simulate workflow
git reset --hard HEAD~1
git checkout -b test-branch
git checkout $commit -- file.txt
git add -A
git commit -m "Cherry-picked"
```

## CI/CD Simulation

### Test GitHub Actions Locally (using act)
```bash
# Install act
brew install act  # macOS
# or
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run workflow
act workflow_dispatch \
  -W .github/workflows/test-workflows.yml \
  --secret GITHUB_TOKEN=fake_token
```

### Test GitLab CI Locally (using gitlab-runner)
```bash
# Install gitlab-runner
curl -L https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.deb.sh | sudo bash
sudo apt-get install gitlab-runner

# Run job
gitlab-runner exec docker update \
  --docker-image python:3.12 \
  --env GITLAB_TOKEN=fake_token
```

## Expected Output Examples

### Unit Test Success
```
test/unit/test_multi_pr.bats
 ✓ extract unique modules from report.json
 ✓ create valid branch name from module with slashes
 ✓ create valid branch name from simple module
 ✓ extract files for specific module using jq --arg
 ✓ handle empty modules list
 ✓ handle malformed JSON gracefully
 ✓ validate report.json structure
 ✓ handle module names with special characters
 ✓ extract multiple files from same module

9 tests, 0 failures
```

### Integration Test Success
```
[INFO] Starting multi-PR integration tests
[INFO] Setting up test repository in /tmp/tmp.xyz
[INFO] Test repository initialized
[INFO] Simulating agronomist update
[INFO] Files updated
[INFO] Testing multi-PR logic with report_multiple_modules.json
[INFO] Found 3 unique modules
[INFO] Created temporary commit: abc123
[INFO] Processing module: weyderfs/terraform-aws-modules//vpc/security-group
[INFO] Created branch: agronomist/update-weyderfs-terraform-aws-modules--vpc-security-group
[INFO] Processing module: hashicorp/terraform-provider-aws
[INFO] Created branch: agronomist/update-hashicorp-terraform-provider-aws
[INFO] Processing module: terraform-aws-modules/rds/aws
[INFO] Created branch: agronomist/update-terraform-aws-modules-rds-aws
[INFO] Processed 3 modules successfully
[INFO] All integration tests passed! ✓
```

## Troubleshooting

### BATS command not found
```bash
make install-test-deps
```

### Permission denied on test scripts
```bash
chmod +x test/run_tests.sh
chmod +x test/integration/test_multi_pr_flow.sh
```

### jq parse error
```bash
# Validate JSON syntax
jq . test/fixtures/report_single_module.json
```

### Git not configured
```bash
git config --global user.email "you@example.com"
git config --global user.name "Your Name"
```
