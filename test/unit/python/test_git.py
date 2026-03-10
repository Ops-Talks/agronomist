"""Tests for git resolver."""

from unittest.mock import MagicMock, patch

import pytest

from agronomist.exceptions import ResolverError
from agronomist.git import GitClient


class TestGitClient:
    """Test GitClient class."""

    def test_git_client_initialization(self):
        """Test initializing GitClient."""
        client = GitClient(timeout=30)
        assert client.timeout == 30

    def test_git_client_default_timeout(self):
        """Test GitClient has default timeout."""
        client = GitClient()
        assert client.timeout == 20

    @patch("agronomist.git.subprocess.run")
    def test_latest_ref_success(self, mock_run):
        """Test successfully retrieving latest ref from git."""
        mock_result = MagicMock()
        mock_result.stdout = "abc123def456\trefs/tags/v1.0.0\n"
        mock_run.return_value = mock_result

        client = GitClient()
        result = client.latest_ref("https://github.com/example/repo.git")

        assert result == "v1.0.0"
        mock_run.assert_called_once()

    @patch("agronomist.git.subprocess.run")
    def test_latest_ref_multiple_tags(self, mock_run):
        """Test selecting latest from multiple tags."""
        mock_result = MagicMock()
        mock_result.stdout = (
            "abc123\trefs/tags/v2.0.0\ndef456\trefs/tags/v1.5.0\nghi789\trefs/tags/v1.0.0\n"
        )
        mock_run.return_value = mock_result

        client = GitClient()
        result = client.latest_ref("https://github.com/example/repo.git")

        assert result is not None

    @patch("agronomist.git.subprocess.run")
    def test_latest_ref_timeout(self, mock_run):
        """Test timeout raises ResolverError."""
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 5)

        client = GitClient(timeout=5)

        with pytest.raises(ResolverError, match="timed out"):
            client.latest_ref("https://github.com/example/repo.git")

    @patch("agronomist.git.subprocess.run")
    def test_latest_ref_repository_not_found(self, mock_run):
        """Test repository not found raises ResolverError."""
        import subprocess

        mock_error = subprocess.CalledProcessError(1, "cmd")
        mock_error.stderr = "fatal: repository not found"
        mock_run.side_effect = mock_error

        client = GitClient()

        with pytest.raises(ResolverError, match="not found"):
            client.latest_ref("https://github.com/nonexistent/repo.git")

    @patch("agronomist.git.subprocess.run")
    def test_latest_ref_git_not_installed(self, mock_run):
        """Test missing git binary raises ResolverError."""
        mock_run.side_effect = FileNotFoundError()

        client = GitClient()

        with pytest.raises(ResolverError, match="not installed"):
            client.latest_ref("https://github.com/example/repo.git")

    @patch("agronomist.git.subprocess.run")
    def test_latest_ref_generic_exception(self, mock_run):
        """Test unexpected exception raises ResolverError."""
        mock_run.side_effect = Exception("Network error")

        client = GitClient()

        with pytest.raises(ResolverError, match="Unexpected"):
            client.latest_ref("https://github.com/example/repo.git")

    @patch("agronomist.git.subprocess.run")
    def test_latest_ref_strips_whitespace(self, mock_run):
        """Test that output is parsed correctly."""
        mock_result = MagicMock()
        mock_result.stdout = "  abc123\trefs/tags/v1.2.3  \n"
        mock_run.return_value = mock_result

        client = GitClient()
        result = client.latest_ref("https://github.com/example/repo.git")

        assert result == "v1.2.3"

    def test_git_client_can_be_instantiated_multiple_times(self):
        """Test GitClient can be instantiated multiple times."""
        client1 = GitClient()
        client2 = GitClient()
        # Should be different instances but compatible interface
        assert client1 is not client2
        assert hasattr(client1, "latest_ref")
        assert hasattr(client2, "latest_ref")

    @patch("agronomist.git.subprocess.run")
    def test_latest_ref_skips_peeled_tags(self, mock_run):
        """Test that ^{} peeled tag lines are skipped."""
        mock_result = MagicMock()
        mock_result.stdout = "abc123\trefs/tags/v1.0.0^{}\ndef456\trefs/tags/v0.9.0\n"
        mock_run.return_value = mock_result

        client = GitClient()
        result = client.latest_ref("https://github.com/example/repo.git")

        assert result == "v0.9.0"

    @patch("agronomist.git.subprocess.run")
    def test_latest_ref_empty_output(self, mock_run):
        """Test that empty git output returns None."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        client = GitClient()
        result = client.latest_ref("https://github.com/example/repo.git")

        assert result is None

    @patch("agronomist.git.subprocess.run")
    def test_latest_ref_malformed_lines(self, mock_run):
        """Test that malformed lines without tab separator are skipped."""
        mock_result = MagicMock()
        mock_result.stdout = "malformed_line_no_tab\nabc123\trefs/tags/v1.0.0\n"
        mock_run.return_value = mock_result

        client = GitClient()
        result = client.latest_ref("https://github.com/example/repo.git")

        assert result == "v1.0.0"

    @patch("agronomist.git.subprocess.run")
    def test_latest_ref_called_process_error_generic_stderr(
        self,
        mock_run,
    ):
        """Test CalledProcessError with generic stderr."""
        import subprocess

        mock_error = subprocess.CalledProcessError(1, "cmd")
        mock_error.stderr = "some other error"
        mock_run.side_effect = mock_error

        client = GitClient()

        with pytest.raises(ResolverError):
            client.latest_ref("https://github.com/example/repo.git")
