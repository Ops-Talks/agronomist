"""Tests for config module."""

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from agronomist.config import Blacklist, CategoryRule, load_config


class TestCategoryRule:
    """Test CategoryRule dataclass."""

    def test_category_rule_creation(self):
        """Test creating a category rule."""
        rule = CategoryRule(
            name="internal",
            repo_patterns=["github.com/myorg/*"],
            module_patterns=["modules/*"],
        )

        assert rule.name == "internal"
        assert rule.repo_patterns == ["github.com/myorg/*"]
        assert rule.module_patterns == ["modules/*"]

    def test_category_rule_is_frozen(self):
        """Test that category rule is immutable."""
        rule = CategoryRule(
            name="test",
            repo_patterns=[],
            module_patterns=[],
        )
        with pytest.raises(AttributeError):
            rule.name = "changed"


class TestBlacklist:
    """Test Blacklist dataclass."""

    def test_blacklist_creation(self):
        """Test creating a blacklist."""
        blacklist = Blacklist(
            repos=["deprecated/*"],
            modules=["legacy/*"],
            files=["**/test/**"],
        )

        assert blacklist.repos == ["deprecated/*"]
        assert blacklist.modules == ["legacy/*"]
        assert blacklist.files == ["**/test/**"]

    def test_blacklist_empty_lists(self):
        """Test blacklist with empty lists."""
        blacklist = Blacklist(repos=[], modules=[], files=[])

        assert blacklist.repos == []
        assert blacklist.modules == []
        assert blacklist.files == []


class TestLoadConfigYAML:
    """Test loading YAML configuration."""

    def test_load_valid_yaml_config(self):
        """Test loading valid YAML configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.yaml"
            config_content = {
                "categories": [
                    {
                        "name": "internal",
                        "repo_patterns": ["github.com/myorg/*"],
                        "module_patterns": ["modules/*"],
                    }
                ],
                "blacklist": {
                    "repos": ["deprecated/*"],
                    "modules": [],
                    "files": ["**/test/**"],
                },
            }
            config_file.write_text(yaml.dump(config_content))

            config = load_config("config.yaml", temp_dir)

            assert len(config.categories) == 1
            assert config.categories[0].name == "internal"
            assert config.blacklist.repos == ["deprecated/*"]

    def test_load_nonexistent_yaml_returns_empty(self):
        """Test loading non-existent YAML returns empty config."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = load_config("missing.yaml", temp_dir)

            assert config.categories == []
            assert config.blacklist.repos == []
            assert config.blacklist.modules == []
            assert config.blacklist.files == []

    def test_load_yaml_with_empty_categories(self):
        """Test loading YAML with empty categories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.yaml"
            config_file.write_text("categories: []\nblacklist:\n  repos: []")

            config = load_config("config.yaml", temp_dir)

            assert config.categories == []

    def test_load_yaml_skips_invalid_categories(self):
        """Test that categories without name are skipped."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.yaml"
            config_content = {
                "categories": [
                    {"repo_patterns": ["*"], "module_patterns": []},  # No name
                    {"name": "valid", "repo_patterns": [], "module_patterns": []},
                ],
                "blacklist": {"repos": [], "modules": [], "files": []},
            }
            config_file.write_text(yaml.dump(config_content))

            config = load_config("config.yaml", temp_dir)

            assert len(config.categories) == 1
            assert config.categories[0].name == "valid"


class TestLoadConfigJSON:
    """Test loading JSON configuration."""

    def test_load_valid_json_config(self):
        """Test loading valid JSON configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.json"
            config_content = {
                "categories": [
                    {
                        "name": "external",
                        "repo_patterns": ["github.com/hashicorp/*"],
                        "module_patterns": ["*"],
                    }
                ],
                "blacklist": {
                    "repos": [],
                    "modules": ["test_*"],
                    "files": [],
                },
            }
            config_file.write_text(json.dumps(config_content))

            config = load_config("config.json", temp_dir)

            assert len(config.categories) == 1
            assert config.categories[0].name == "external"
            assert config.blacklist.modules == ["test_*"]

    def test_load_json_with_multiple_categories(self):
        """Test loading JSON with multiple categories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.json"
            config_content = {
                "categories": [
                    {"name": "internal", "repo_patterns": ["internal/*"], "module_patterns": []},
                    {"name": "external", "repo_patterns": ["external/*"], "module_patterns": []},
                    {"name": "deprecated", "repo_patterns": ["old/*"], "module_patterns": []},
                ],
                "blacklist": {"repos": [], "modules": [], "files": []},
            }
            config_file.write_text(json.dumps(config_content))

            config = load_config("config.json", temp_dir)

            assert len(config.categories) == 3
            assert [c.name for c in config.categories] == ["internal", "external", "deprecated"]


class TestLoadConfigAbsolutePath:
    """Test loading configuration with absolute paths."""

    def test_load_config_with_absolute_path(self):
        """Test loading config with absolute path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.yaml"
            config_content = {
                "categories": [{"name": "test", "repo_patterns": [], "module_patterns": []}],
                "blacklist": {"repos": [], "modules": [], "files": []},
            }
            config_file.write_text(yaml.dump(config_content))

            # Use absolute path
            config = load_config(str(config_file), "")

            assert len(config.categories) == 1


class TestLoadConfigEdgeCases:
    """Test edge cases for config loading."""

    def test_load_empty_config(self):
        """Test loading empty config string."""
        config = load_config("", "/some/path")

        assert config.categories == []
        assert config.blacklist.repos == []

    def test_load_config_with_null_values(self):
        """Test loading config with null values in YAML."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.yaml"
            config_content = {
                "categories": [
                    {
                        "name": "test",
                        "repo_patterns": None,
                        "module_patterns": None,
                    }
                ],
                "blacklist": {"repos": [], "modules": [], "files": []},
            }
            config_file.write_text(yaml.dump(config_content))

            config = load_config("config.yaml", temp_dir)

            assert len(config.categories) == 1
            assert config.categories[0].repo_patterns == []
            assert config.categories[0].module_patterns == []
