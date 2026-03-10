"""Tests for GitLab client."""

from unittest.mock import MagicMock, patch

import pytest

from agronomist.exceptions import AuthenticationError, NetworkError
from agronomist.gitlab import GitLabClient


class TestGitLabClient:
    """Test GitLabClient class."""

    def test_gitlab_client_initialization_with_token(self):
        """Test initializing GitLabClient with token."""
        client = GitLabClient(base_url="https://gitlab.com", token="test-token")
        assert client.token == "test-token"
        assert client.base_url == "https://gitlab.com"

    def test_gitlab_client_initialization_without_token(self):
        """Test initializing GitLabClient without token."""
        client = GitLabClient(base_url="https://gitlab.com")
        assert client.token is None

    def test_gitlab_client_default_timeout(self):
        """Test GitLabClient has default timeout."""
        client = GitLabClient(base_url="https://gitlab.com")
        assert client.timeout == 20

    @patch("requests.Session.get")
    def test_latest_tag_success(self, mock_get):
        """Test successfully retrieving latest tag."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"name": "v1.2.3"}]
        mock_get.return_value = mock_response

        client = GitLabClient(base_url="https://gitlab.com")
        result = client.latest_tag("mygroup%2Fmyproject")

        assert result == "v1.2.3"
        mock_get.assert_called_once()

    @patch("requests.Session.get")
    def test_latest_tag_not_found(self, mock_get):
        """Test handling 404 response."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        client = GitLabClient(base_url="https://gitlab.com")
        result = client.latest_tag("nonexistent%2Fproject")

        assert result is None

    @patch("requests.Session.get")
    def test_latest_tag_unauthorized(self, mock_get):
        """Test handling 401 unauthorized."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        client = GitLabClient(base_url="https://gitlab.com")
        result = client.latest_tag("mygroup%2Fmyproject")

        assert result is None

    @patch("requests.Session.get")
    def test_latest_tag_empty_response(self, mock_get):
        """Test handling empty response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        client = GitLabClient(base_url="https://gitlab.com")
        result = client.latest_tag("mygroup%2Fmyproject")

        assert result is None

    @patch("requests.Session.get")
    def test_validate_token_success(self, mock_get):
        """Test token validation succeeds."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        client = GitLabClient(base_url="https://gitlab.com", token="valid-token")
        result = client.validate_token()

        assert result is True

    @patch("requests.Session.get")
    def test_validate_token_invalid(self, mock_get):
        """Test invalid token raises AuthenticationError."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        client = GitLabClient(
            base_url="https://gitlab.com",
            token="invalid-token",
        )

        with pytest.raises(
            AuthenticationError,
            match="invalid",
        ):
            client.validate_token()

    @patch("requests.Session.get")
    def test_validate_token_without_token(self, mock_get):
        """Test token validation returns true when no token."""
        client = GitLabClient(base_url="https://gitlab.com")
        result = client.validate_token()

        # Should return true if no token
        assert result is True
        # Should not make any requests
        mock_get.assert_not_called()

    def test_detect_gitlab_host_success(self):
        """Test detecting GitLab host from URL."""
        url = "https://gitlab.example.com/group/project.git"
        result = GitLabClient.detect_gitlab_host(url)

        assert result == "https://gitlab.example.com"

    def test_detect_gitlab_host_no_gitlab(self):
        """Test that non-GitLab URLs return None."""
        url = "https://github.com/group/project.git"
        result = GitLabClient.detect_gitlab_host(url)

        assert result is None

    def test_detect_gitlab_host_invalid_url(self):
        """Test that invalid URLs return None."""
        result = GitLabClient.detect_gitlab_host("not-a-url")

        assert result is None

    @patch("requests.Session.get")
    def test_latest_ref_success(self, mock_get):
        """Test latest_ref delegates to latest_tag."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"name": "v2.0.0"}]
        mock_get.return_value = mock_response

        client = GitLabClient(base_url="https://gitlab.com")
        result = client.latest_ref("https://gitlab.com/mygroup/myproject.git")

        assert result == "v2.0.0"

    @patch("requests.Session.get")
    def test_validate_token_forbidden(self, mock_get):
        """Test forbidden token raises AuthenticationError."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response

        client = GitLabClient(
            base_url="https://gitlab.com",
            token="bad-token",
        )

        with pytest.raises(
            AuthenticationError,
            match="permissions",
        ):
            client.validate_token()

    @patch("requests.Session.get")
    def test_validate_token_request_exception(self, mock_get):
        """Test request exception raises AuthenticationError."""
        import requests

        mock_get.side_effect = requests.RequestException(
            "Connection refused",
        )

        client = GitLabClient(
            base_url="https://gitlab.com",
            token="some-token",
        )

        with pytest.raises(AuthenticationError):
            client.validate_token()

    @patch("requests.Session.get")
    def test_latest_tag_forbidden(self, mock_get):
        """Test handling 403 forbidden response for tags."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response

        client = GitLabClient(base_url="https://gitlab.com")
        result = client.latest_tag("mygroup%2Fmyproject")

        assert result is None

    @patch("requests.Session.get")
    def test_latest_tag_request_exception(self, mock_get):
        """Test request exception raises NetworkError."""
        import requests

        mock_get.side_effect = requests.RequestException("Timeout")

        client = GitLabClient(base_url="https://gitlab.com")

        with pytest.raises(NetworkError):
            client.latest_tag("mygroup%2Fmyproject")

    def test_latest_ref_invalid_url(self):
        """Test latest_ref with an invalid URL returns None."""
        client = GitLabClient(base_url="https://gitlab.com")
        result = client.latest_ref("not-a-url")

        assert result is None

    def test_headers_without_token(self):
        """Test _headers returns empty dict without token."""
        client = GitLabClient(base_url="https://gitlab.com")
        headers = client._headers()

        assert headers == {}

    def test_headers_with_token(self):
        """Test _headers includes PRIVATE-TOKEN with token."""
        client = GitLabClient(base_url="https://gitlab.com", token="my-token")
        headers = client._headers()

        assert "PRIVATE-TOKEN" in headers
        assert headers["PRIVATE-TOKEN"] == "my-token"
