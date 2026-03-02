"""Pytest configuration and shared fixtures."""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        "categories": [
            {
                "name": "internal",
                "repo_patterns": ["github.com/myorg/*"],
                "module_patterns": ["modules/*"],
            },
            {
                "name": "external",
                "repo_patterns": ["github.com/hashicorp/*"],
                "module_patterns": ["*"],
            },
        ],
        "blacklist": {
            "repos": ["github.com/deprecated/*"],
            "modules": ["deprecated_*"],
            "files": ["**/test/**"],
        },
    }


@pytest.fixture
def sample_terraform_file(temp_dir):
    """Create a sample Terraform file with various source patterns."""
    tf_file = Path(temp_dir) / "main.tf"
    content = """
module "vpc" {
  source = "git::https://github.com/terraform-aws-modules/terraform-aws-vpc.git?ref=v5.0.0"
}

module "internal" {
  source = "github.com/myorg/internal-modules//vpc?ref=v1.2.3"
}

module "with_submodule" {
  source = "git::https://github.com/example/repo.git//modules/test?ref=main"
}

variable "test" {
  default = "not a source"
}
"""
    tf_file.write_text(content)
    return str(tf_file)


@pytest.fixture
def sample_hcl_file(temp_dir):
    """Create a sample HCL file with terragrunt syntax."""
    hcl_file = Path(temp_dir) / "terragrunt.hcl"
    content = """
terraform {
  source = "git::https://github.com/example/modules.git//vpc?ref=v2.0.0"
}

dependency "vpc" {
  config_path = "../vpc"
}

inputs = {
  region = "us-east-1"
}
"""
    hcl_file.write_text(content)
    return str(hcl_file)
