"""Tests for GitHub client."""

from unittest.mock import MagicMock, patch

from agronomist.github import GitHubClient


class TestGitHubClient:
    """Test GitHubClient class."""

    def test_github_client_initialization_with_token(self):
        """Test initializing GitHubClient with token."""
        client = GitHubClient(base_url="https://api.github.com", token="test-token")
        assert client.token == "test-token"
        assert client.base_url == "https://api.github.com"

    def test_github_client_initialization_without_token(self):
        """Test initializing GitHubClient without token."""
        client = GitHubClient(base_url="https://api.github.com")
        assert client.token is None

    def test_github_client_default_timeout(self):
        """Test GitHubClient has default timeout."""
        client = GitHubClient(base_url="https://api.github.com")
        assert client.timeout == 20

    @patch("agronomist.github.requests.get")
    def test_latest_release_tag_success(self, mock_get):
        """Test successfully retrieving latest release."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"tag_name": "v1.2.3"}
        mock_get.return_value = mock_response

        client = GitHubClient(base_url="https://api.github.com")
        result = client.latest_release_tag("example/repo")

        assert result == "v1.2.3"
        mock_get.assert_called_once()

    @patch("agronomist.github.requests.get")
    def test_latest_release_tag_not_found(self, mock_get):
        """Test handling 404 response."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        client = GitHubClient(base_url="https://api.github.com")
        result = client.latest_release_tag("nonexistent/repo")

        assert result is None

    @patch("agronomist.github.requests.get")
    def test_latest_release_tag_unauthorized(self, mock_get):
        """Test handling 401 unauthorized."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        client = GitHubClient(base_url="https://api.github.com")
        result = client.latest_release_tag("example/repo")

        assert result is None

    @patch("agronomist.github.requests.get")
    def test_latest_release_tag_request_error(self, mock_get):
        """Test handling request errors."""
        import requests

        mock_get.side_effect = requests.RequestException("Network error")

        client = GitHubClient(base_url="https://api.github.com")
        result = client.latest_release_tag("example/repo")

        assert result is None

    @patch("agronomist.github.requests.get")
    def test_validate_token_success(self, mock_get):
        """Test token validation succeeds."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        client = GitHubClient(base_url="https://api.github.com", token="valid-token")
        result = client.validate_token()

        assert result is True

    @patch("agronomist.github.requests.get")
    def test_validate_token_invalid(self, mock_get):
        """Test token validation fails for invalid token."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        client = GitHubClient(base_url="https://api.github.com", token="invalid-token")
        result = client.validate_token()

        assert result is False

    @patch("agronomist.github.requests.get")
    def test_validate_token_without_token(self, mock_get):
        """Test token validation returns true when no token."""
        client = GitHubClient(base_url="https://api.github.com")
        result = client.validate_token()

        # Should return true if no token
        assert result is True
        # Should not make any requests
        mock_get.assert_not_called()

    @patch("agronomist.github.requests.get")
    def test_headers_with_token(self, mock_get):
        """Test that token is included in headers."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"tag_name": "v1.0.0"}
        mock_get.return_value = mock_response

        client = GitHubClient(base_url="https://api.github.com", token="my-token")
        client.latest_release_tag("example/repo")

        # Check that headers were passed
        call_kwargs = mock_get.call_args[1]
        assert "headers" in call_kwargs
        assert "Authorization" in call_kwargs["headers"]

    @patch("agronomist.github.requests.get")
    def test_latest_tag_success(self, mock_get):
        """Test successfully retrieving latest tag."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"name": "v9.9.9"}]
        mock_get.return_value = mock_response

        client = GitHubClient(base_url="https://api.github.com")
        result = client.latest_tag("example/repo")

        assert result == "v9.9.9"

    @patch("agronomist.github.requests.get")
    def test_latest_tag_empty_list(self, mock_get):
        """Test latest_tag returns None when tag list is empty."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        client = GitHubClient(base_url="https://api.github.com")
        result = client.latest_tag("example/repo")

        assert result is None

    @patch("agronomist.github.requests.get")
    def test_latest_tag_forbidden(self, mock_get):
        """Test latest_tag handles 403 response."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response

        client = GitHubClient(base_url="https://api.github.com")
        result = client.latest_tag("example/repo")

        assert result is None

    @patch("agronomist.github.requests.get")
    def test_latest_tag_request_error(self, mock_get):
        """Test latest_tag handles request exceptions."""
        import requests

        mock_get.side_effect = requests.RequestException("Network error")

        client = GitHubClient(base_url="https://api.github.com")
        result = client.latest_tag("example/repo")

        assert result is None

    @patch.object(GitHubClient, "latest_tag")
    @patch.object(GitHubClient, "latest_release_tag")
    def test_latest_ref_prefers_release_tag(self, mock_release, mock_tag):
        """Test latest_ref returns release tag when available."""
        mock_release.return_value = "v2.0.0"

        client = GitHubClient(base_url="https://api.github.com")
        result = client.latest_ref("example/repo")

        assert result == "v2.0.0"
        mock_tag.assert_not_called()

    @patch.object(GitHubClient, "latest_tag")
    @patch.object(GitHubClient, "latest_release_tag")
    def test_latest_ref_falls_back_to_latest_tag(self, mock_release, mock_tag):
        """Test latest_ref falls back to latest_tag when no release tag exists."""
        mock_release.return_value = None
        mock_tag.return_value = "v1.8.0"

        client = GitHubClient(base_url="https://api.github.com")
        result = client.latest_ref("example/repo")

        assert result == "v1.8.0"
        mock_tag.assert_called_once_with("example/repo")
