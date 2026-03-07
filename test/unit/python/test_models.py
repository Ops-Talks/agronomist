"""Tests for data models (SourceRef, Replacement, UpdateEntry)."""

from __future__ import annotations

import pytest

from agronomist.models import Replacement, SourceRef, UpdateEntry


class TestReplacement:
    """Test the Replacement dataclass."""

    def test_to_dict_uses_from_to_keys(self):
        """Test that to_dict serializes with 'from' and 'to' keys."""
        r = Replacement(old="ref=v1", new="ref=v2")
        d = r.to_dict()
        assert d == {"from": "ref=v1", "to": "ref=v2"}

    def test_replacement_is_frozen(self):
        """Test that Replacement is immutable."""
        r = Replacement(old="a", new="b")
        with pytest.raises(AttributeError):
            r.old = "c"  # type: ignore[misc]


class TestUpdateEntry:
    """Test the UpdateEntry dataclass."""

    def _mk_entry(self, **overrides) -> UpdateEntry:
        """Build a minimal UpdateEntry with optional overrides."""
        defaults = {
            "repo": "org/repo",
            "repo_host": "github.com",
            "repo_url": "https://github.com/org/repo.git",
            "module": "root@main.tf",
            "base_module": None,
            "file": "main.tf",
            "current_ref": "v1.0.0",
            "latest_ref": "v2.0.0",
            "strategy": "latest",
            "files": ["main.tf"],
            "replacements": [Replacement(old="ref=v1.0.0", new="ref=v2.0.0")],
            "category": None,
        }
        defaults.update(overrides)
        return UpdateEntry(**defaults)

    def test_to_dict_contains_all_fields(self):
        """Test that to_dict includes all required fields."""
        entry = self._mk_entry()
        d = entry.to_dict()
        assert d["repo"] == "org/repo"
        assert d["repo_host"] == "github.com"
        assert d["current_ref"] == "v1.0.0"
        assert d["latest_ref"] == "v2.0.0"
        assert d["strategy"] == "latest"
        assert d["files"] == ["main.tf"]
        assert d["replacements"] == [{"from": "ref=v1.0.0", "to": "ref=v2.0.0"}]

    def test_to_dict_includes_category_when_set(self):
        """Test that to_dict includes category when not None."""
        entry = self._mk_entry(category="network")
        d = entry.to_dict()
        assert d["category"] == "network"

    def test_to_dict_excludes_category_when_none(self):
        """Test that to_dict omits category key when None."""
        entry = self._mk_entry(category=None)
        d = entry.to_dict()
        assert "category" not in d

    def test_update_entry_is_frozen(self):
        """Test that UpdateEntry is immutable."""
        entry = self._mk_entry()
        with pytest.raises(AttributeError):
            entry.repo = "other"  # type: ignore[misc]

    def test_default_empty_lists(self):
        """Test that files and replacements default to empty lists."""
        entry = UpdateEntry(
            repo="org/repo",
            repo_host="github.com",
            repo_url="u",
            module="m",
            base_module=None,
            file="f.tf",
            current_ref="v1",
            latest_ref="v2",
            strategy="latest",
        )
        assert entry.files == []
        assert entry.replacements == []


class TestSourceRef:
    """Test the SourceRef dataclass."""

    def test_source_ref_module_defaults_to_none(self):
        """Test that module defaults to None."""
        ref = SourceRef(
            file_path="main.tf",
            raw="git::https://github.com/org/repo.git?ref=v1",
            repo="org/repo",
            repo_url="https://github.com/org/repo.git",
            repo_host="github.com",
            ref="v1",
        )
        assert ref.module is None
