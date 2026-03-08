#!/usr/bin/env bats

# Test suite for multi-PR functionality

setup() {
    # Create temporary test directory
    TEST_TEMP_DIR="$(mktemp -d)"
    cd "$TEST_TEMP_DIR" || exit 1
}

teardown() {
    # Clean up
    rm -rf "$TEST_TEMP_DIR"
}

@test "extract unique modules from report.json" {
    cat > report.json <<EOF
{
  "updates": [
    {"module": "weyderfs/terraform-aws-modules//vpc/security-group@main.tf", "files": ["main.tf"]},
    {"module": "hashicorp/terraform-provider-aws@versions.tf", "files": ["versions.tf"]},
    {"module": "weyderfs/terraform-aws-modules//vpc/security-group@network.tf", "files": ["network.tf"]}
  ]
}
EOF

    modules=$(jq -r '.updates[].module' report.json | sort -u)
    module_count=$(echo "$modules" | wc -l)

    # Now each file gets a unique module identifier
    [ "$module_count" -eq 3 ]
}

@test "create valid branch name from module with slashes" {
    # Full module ID (base_module@filepath) — only the base part is used in the name
    module="weyderfs/terraform-aws-modules//vpc/security-group@infra/main.tf"
    base_module_id="$(echo "$module" | cut -d'@' -f1)"
    safe_base="$(echo "$base_module_id" | sed 's/[/@]/-/g')"
    if [ "${#safe_base}" -gt 50 ]; then safe_base="${safe_base:0:50}"; fi
    module_hash="$(printf '%s' "$module" | sha256sum | cut -c1-8)"
    branch_name="agronomist/update-${safe_base}-${module_hash}"

    [ "$branch_name" = "agronomist/update-weyderfs-terraform-aws-modules--vpc-security-group-${module_hash}" ]
}

@test "create valid branch name from simple module" {
    # Full module ID with a file path suffix
    module="hashicorp/terraform@versions.tf"
    base_module_id="$(echo "$module" | cut -d'@' -f1)"
    safe_base="$(echo "$base_module_id" | sed 's/[/@]/-/g')"
    if [ "${#safe_base}" -gt 50 ]; then safe_base="${safe_base:0:50}"; fi
    module_hash="$(printf '%s' "$module" | sha256sum | cut -c1-8)"
    branch_name="agronomist/update-${safe_base}-${module_hash}"

    [ "$branch_name" = "agronomist/update-hashicorp-terraform-${module_hash}" ]
}

@test "extract files for specific module using jq --arg" {
    cat > report.json <<EOF
{
  "updates": [
    {"module": "module-a@file1.tf", "files": ["file1.tf"]},
    {"module": "module-a@file2.tf", "files": ["file2.tf"]},
    {"module": "module-b@file3.tf", "files": ["file3.tf"]}
  ]
}
EOF

    # Now each file has unique module ID, so each update has exactly 1 file
    files=$(jq -r --arg mod "module-a@file1.tf" '.updates[] | select(.module==$mod) | .files[]' report.json)
    file_count=$(echo "$files" | wc -l)

    [ "$file_count" -eq 1 ]
    echo "$files" | grep -q "file1.tf"
}

@test "handle empty modules list" {
    cat > report.json <<EOF
{
  "updates": []
}
EOF

    modules=$(jq -r '.updates[].module' report.json 2>/dev/null | sort -u)

    [ -z "$modules" ]
}

@test "handle malformed JSON gracefully" {
    echo "not valid json" > report.json

    run jq -r '.updates[].module' report.json 2>/dev/null
    [ "$status" -ne 0 ]
}

@test "validate report.json structure" {
    cat > report.json <<EOF
{
  "updates": [
    {
      "module": "test/module",
      "current_ref": "v1.0.0",
      "latest_ref": "v2.0.0",
      "files": ["main.tf"]
    }
  ]
}
EOF

    # Check required fields exist
    jq -e '.updates[0].module' report.json > /dev/null
    jq -e '.updates[0].files' report.json > /dev/null
}

@test "handle module names with special characters" {
    module="terraform-aws-modules/vpc/aws"
    safe_module="$(echo "$module" | sed 's/[/@]/-/g')"
    branch_name="agronomist/update-${safe_module}"

    # The module suffix must not contain slashes or @ symbols
    echo "$safe_module" | grep -vE '[/@]'
}

@test "long file path does not inflate branch name" {
    # The file path after @ is long, but the branch name stays short
    # because only the base module (before @) is embedded in the name
    module="cloudwatch-log-group@providers/aws/contoso_000000/dev/us-east-2/cloudwatch-log-group-lambda-app/terragrunt.hcl"
    base_module_id="$(echo "$module" | cut -d'@' -f1)"
    safe_base="$(echo "$base_module_id" | sed 's/[/@]/-/g')"
    if [ "${#safe_base}" -gt 50 ]; then safe_base="${safe_base:0:50}"; fi
    module_hash="$(printf '%s' "$module" | sha256sum | cut -c1-8)"
    branch_name="agronomist/update-${safe_base}-${module_hash}"

    # Branch stays well under 80 chars despite the very long file path
    [ "${#branch_name}" -le 80 ]

    # Must carry the expected prefix and base module name
    [[ "$branch_name" == agronomist/update-cloudwatch-log-group-* ]]

    # File path components must NOT appear in the branch name
    [[ "$branch_name" != *providers* ]]
    [[ "$branch_name" != *contoso* ]]
    [[ "$branch_name" != *terragrunt* ]]
}

@test "extract multiple files from same module" {
    cat > report.json <<EOF
{
  "updates": [
    {
      "module": "test-module@infra/main.tf",
      "files": ["infra/main.tf"]
    },
    {
      "module": "test-module@infra/network.tf",
      "files": ["infra/network.tf"]
    },
    {
      "module": "test-module@infra/security.tf",
      "files": ["infra/security.tf"]
    }
  ]
}
EOF

    # Each file now has its own update entry with unique module ID
    update_count=$(jq -r '.updates | length' report.json)

    [ "$update_count" -eq 3 ]
}
