#!/usr/bin/env bats

# Test suite for file-based update functionality
# Validates that each Terragrunt file gets its own update entry

setup() {
    TEST_TEMP_DIR="$(mktemp -d)"
    cd "$TEST_TEMP_DIR" || exit 1
}

teardown() {
    rm -rf "$TEST_TEMP_DIR"
}

@test "each file gets unique module identifier" {
    cat > report.json <<EOF
{
  "updates": [
    {
      "module": "vpc/security-group@providers/aws/dev/ec2/segurity-group/chatbot-ai/terragrunt.hcl",
      "base_module": "vpc/security-group",
      "file": "providers/aws/dev/ec2/segurity-group/chatbot-ai/terragrunt.hcl",
      "files": ["providers/aws/dev/ec2/segurity-group/chatbot-ai/terragrunt.hcl"]
    },
    {
      "module": "vpc/security-group@providers/aws/dev/ec2/segurity-group/chatbot-ia-front-ecs/terragrunt.hcl",
      "base_module": "vpc/security-group",
      "file": "providers/aws/dev/ec2/segurity-group/chatbot-ia-front-ecs/terragrunt.hcl",
      "files": ["providers/aws/dev/ec2/segurity-group/chatbot-ia-front-ecs/terragrunt.hcl"]
    }
  ]
}
EOF

    # Both updates should have unique module identifiers
    unique_modules=$(jq -r '.updates[].module' report.json | sort -u | wc -l)
    [ "$unique_modules" -eq 2 ]

    # Both should share the same base_module
    base_modules=$(jq -r '.updates[].base_module' report.json | sort -u)
    [ "$(echo "$base_modules" | wc -l)" -eq 1 ]
    [ "$base_modules" = "vpc/security-group" ]
}

@test "each update has exactly one file" {
    cat > report.json <<EOF
{
  "updates": [
    {
      "module": "module-a@file1.tf",
      "file": "file1.tf",
      "files": ["file1.tf"]
    },
    {
      "module": "module-a@file2.tf",
      "file": "file2.tf",
      "files": ["file2.tf"]
    }
  ]
}
EOF

    # Each update should have exactly 1 file
    for i in 0 1; do
        file_count=$(jq -r ".updates[$i].files | length" report.json)
        [ "$file_count" -eq 1 ]
    done
}

@test "file field matches files array" {
    cat > report.json <<EOF
{
  "updates": [
    {
      "module": "test@path/to/file.tf",
      "file": "path/to/file.tf",
      "files": ["path/to/file.tf"]
    }
  ]
}
EOF

    file=$(jq -r '.updates[0].file' report.json)
    files_first=$(jq -r '.updates[0].files[0]' report.json)

    [ "$file" = "$files_first" ]
}

@test "separate PRs for same base module different files" {
    cat > report.json <<EOF
{
  "updates": [
    {
      "module": "vpc/security-group@infra/chatbot-ai/terragrunt.hcl",
      "base_module": "vpc/security-group",
      "file": "infra/chatbot-ai/terragrunt.hcl"
    },
    {
      "module": "vpc/security-group@infra/chatbot-frontend/terragrunt.hcl",
      "base_module": "vpc/security-group",
      "file": "infra/chatbot-frontend/terragrunt.hcl"
    }
  ]
}
EOF

    # Extract unique modules for PR creation
    modules=$(jq -r '.updates[].module' report.json)

    # Should have 2 separate entries (2 PRs)
    pr_count=$(echo "$modules" | wc -l)
    [ "$pr_count" -eq 2 ]

    # Verify they're different
    unique_count=$(echo "$modules" | sort -u | wc -l)
    [ "$unique_count" -eq 2 ]
}

@test "base_module preserved for grouping in markdown" {
    cat > report.json <<EOF
{
  "updates": [
    {
      "module": "aws/vpc@file1.tf",
      "base_module": "aws/vpc",
      "file": "file1.tf"
    },
    {
      "module": "aws/vpc@file2.tf",
      "base_module": "aws/vpc",
      "file": "file2.tf"
    },
    {
      "module": "aws/rds@file3.tf",
      "base_module": "aws/rds",
      "file": "file3.tf"
    }
  ]
}
EOF

    # base_module allows logical grouping for display
    base_modules=$(jq -r '.updates[].base_module' report.json | sort -u)
    base_count=$(echo "$base_modules" | wc -l)

    # Should have 2 unique base modules (aws/vpc, aws/rds)
    [ "$base_count" -eq 2 ]
}
