#!/bin/bash

# Integration test for multi-PR workflow
# This script simulates the complete flow of creating multiple PRs

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_DIR="$(mktemp -d)"
FIXTURES_DIR="$SCRIPT_DIR/../fixtures"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

cleanup() {
    log_info "Cleaning up test directory: $TEST_DIR"
    rm -rf "$TEST_DIR"
}

trap cleanup EXIT

# Initialize test repository
setup_test_repo() {
    log_info "Setting up test repository in $TEST_DIR"
    cd "$TEST_DIR"
    
    git init
    git config user.email "test@agronomist.test"
    git config user.name "Agronomist Test"
    
    # Create initial structure
    mkdir -p infra/modules/networking
    
    # Create test files with old versions
    cat > infra/main.tf <<EOF
module "security_group" {
  source = "git::https://github.com/weyderfs/terraform-aws-modules.git//vpc/security-group?ref=v1.2.0"
  
  vpc_id = var.vpc_id
}
EOF

    cat > infra/modules/networking/security.tf <<EOF
module "security" {
  source = "git::https://github.com/weyderfs/terraform-aws-modules.git//vpc/security-group?ref=v1.2.0"
}
EOF

    cat > infra/versions.tf <<EOF
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0.0"
    }
  }
}
EOF

    cat > infra/database.tf <<EOF
module "rds" {
  source = "git::https://github.com/terraform-aws-modules/rds.git?ref=v3.0.0"
  
  engine = "postgres"
}
EOF

    git add -A
    git commit -m "Initial commit"
    
    log_info "Test repository initialized"
}

# Simulate agronomist update applying changes
simulate_agronomist_update() {
    log_info "Simulating agronomist update"
    
    # Apply updates from report
    sed -i 's/v1.2.0/v1.3.0/g' infra/main.tf
    sed -i 's/v1.2.0/v1.3.0/g' infra/modules/networking/security.tf
    sed -i 's/5.0.0/5.1.0/g' infra/versions.tf
    sed -i 's/v3.0.0/v3.1.0/g' infra/database.tf
    
    log_info "Files updated"
}

# Test the multi-PR logic
test_multi_pr_logic() {
    local report_file="$FIXTURES_DIR/report_multiple_modules.json"
    
    log_info "Testing multi-PR logic with $report_file"
    
    cp "$report_file" report.json
    
    # Extract unique modules
    modules=$(jq -r '.updates[].module' report.json 2>/dev/null | sort -u)
    module_count=$(echo "$modules" | wc -l)
    
    log_info "Found $module_count unique modules"
    
    if [ "$module_count" -ne 3 ]; then
        log_error "Expected 3 modules, found $module_count"
        return 1
    fi
    
    # Create temporary commit with all changes
    git add -A
    git commit -m "[agronomist] temporary commit with all module updates"
    all_changes_commit=$(git rev-parse HEAD)
    
    log_info "Created temporary commit: $all_changes_commit"
    
    # Reset to state before changes
    git reset --hard HEAD~1
    
    # Process each module
    local processed=0
    for module in $modules; do
        log_info "Processing module: $module"
        
        # Create branch name
        branch_name="agronomist/update-$(echo "$module" | sed 's/\//-/g')"
        
        # Get files for this module
        files=$(jq -r --arg mod "$module" '.updates[] | select(.module==$mod) | .files[]' report.json 2>/dev/null)
        
        if [ -z "$files" ]; then
            log_warn "No files found for module: $module"
            continue
        fi
        
        # Create branch
        git checkout -b "$branch_name"
        
        # Cherry-pick files
        echo "$files" | while IFS= read -r file; do
            if [ -n "$file" ]; then
                git checkout "$all_changes_commit" -- "$file" 2>/dev/null || true
            fi
        done
        
        # Check for changes
        if [ -z "$(git diff --cached --name-only)" ] && [ -z "$(git diff --name-only)" ]; then
            log_warn "No changes for module: $module"
            git checkout HEAD~0
            git branch -D "$branch_name" 2>/dev/null || true
            continue
        fi
        
        # Commit
        git add -A
        git commit -m "[Agronomist] There is a new Module Version"
        
        log_info "Created branch: $branch_name"
        
        # Validate branch exists
        if ! git rev-parse --verify "$branch_name" >/dev/null 2>&1; then
            log_error "Branch $branch_name does not exist"
            return 1
        fi
        
        # Count commits in branch
        commit_count=$(git rev-list --count "$branch_name")
        log_info "Branch $branch_name has $commit_count commit(s)"
        
        processed=$((processed + 1))
        
        # Reset for next iteration
        git reset --hard HEAD~1
    done
    
    log_info "Processed $processed modules successfully"
    
    if [ "$processed" -ne 3 ]; then
        log_error "Expected to process 3 modules, processed $processed"
        return 1
    fi
    
    return 0
}

# Test with single module
test_single_module() {
    log_info "Testing with single module"
    
    local report_file="$FIXTURES_DIR/report_single_module.json"
    cp "$report_file" report.json
    
    modules=$(jq -r '.updates[].module' report.json | sort -u)
    module_count=$(echo "$modules" | wc -l)
    
    if [ "$module_count" -ne 1 ]; then
        log_error "Expected 1 module, found $module_count"
        return 1
    fi
    
    log_info "Single module test passed"
    return 0
}

# Test with empty report
test_empty_report() {
    log_info "Testing with empty report"
    
    local report_file="$FIXTURES_DIR/report_empty.json"
    cp "$report_file" report.json
    
    modules=$(jq -r '.updates[].module' report.json 2>/dev/null | sort -u)
    
    if [ -n "$modules" ]; then
        log_error "Expected no modules, found: $modules"
        return 1
    fi
    
    log_info "Empty report test passed"
    return 0
}

# Main test execution
main() {
    log_info "Starting multi-PR integration tests"
    
    setup_test_repo
    simulate_agronomist_update
    
    if ! test_multi_pr_logic; then
        log_error "Multi-PR logic test failed"
        exit 1
    fi
    
    # Reset for next test
    git reset --hard HEAD
    
    if ! test_single_module; then
        log_error "Single module test failed"
        exit 1
    fi
    
    if ! test_empty_report; then
        log_error "Empty report test failed"
        exit 1
    fi
    
    log_info "All integration tests passed! ✓"
}

main "$@"
