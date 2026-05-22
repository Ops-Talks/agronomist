"""Tests for Bitbucket client."""

from unittest.mock import MagicMock, patch

import pytest

from agronomist.bitbucket import BitbucketClient
from agronomist.exceptions import AuthenticationError, NetworkError


class TestBitbucketClient:
    """Test BitbucketClient class."""

    def test_bitbucket_client_initialization_with_token(self):
        """Test initializing BitbucketClient with token."""
        client = BitbucketClient(token="test-token")
        assert client.token == "test-token"
        assert client.base_url == "https://api.bitbucket.org/2.0"

    def test_bitbucket_client_initialization_without_token(self):
        """Test initializing BitbucketClient without token."""
        client = BitbucketClient()
        assert client.token is None
        assert client.username is None

    def test_bitbucket_client_initialization_with_username(self):
        """Test initializing BitbucketClient with username + token."""
        client = BitbucketClient(token="apppw", username="alice")
        assert client.username == "alice"
        assert client.token == "apppw"

    def test_bitbucket_client_default_timeout(self):
        """Test BitbucketClient has default timeout."""
        client = BitbucketClient()
        assert client.timeout == 20

    @patch("requests.Session.get")
    def test_validate_token_no_token(self, mock_get):
        """Test validate_token returns True when no token configured."""
        client = BitbucketClient()
        result = client.validate_token()

        assert result is True
        mock_get.assert_not_called()

    @patch("requests.Session.get")
    def test_validate_token_success_bearer(self, mock_get):
        """Test validate_token with Bearer authentication."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        client = BitbucketClient(token="valid-token")
        result = client.validate_token()

        assert result is True
        # Bearer mode: auth should be None
        kwargs = mock_get.call_args.kwargs
        assert kwargs["auth"] is None
        assert kwargs["headers"]["Authorization"] == "Bearer valid-token"

    @patch("requests.Session.get")
    def test_validate_token_success_basic(self, mock_get):
        """Test validate_token with HTTP Basic (App Password) auth."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        client = BitbucketClient(token="apppw", username="alice")
        result = client.validate_token()

        assert result is True
        kwargs = mock_get.call_args.kwargs
        assert kwargs["auth"] == ("alice", "apppw")
        assert "Authorization" not in kwargs["headers"]

    @patch("requests.Session.get")
    def test_validate_token_401_raises(self, mock_get):
        """Test that 401 raises AuthenticationError."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        client = BitbucketClient(token="bad")

        with pytest.raises(AuthenticationError, match="invalid"):
            client.validate_token()

    @patch("requests.Session.get")
    def test_validate_token_403_raises(self, mock_get):
        """Test that 403 raises AuthenticationError."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response

        client = BitbucketClient(token="bad")

        with pytest.raises(AuthenticationError, match="permissions"):
            client.validate_token()

    @patch("requests.Session.get")
    def test_validate_token_request_exception_raises(self, mock_get):
        """Test that a request exception raises AuthenticationError."""
        import requests

        mock_get.side_effect = requests.RequestException("Connection refused")

        client = BitbucketClient(token="some")

        with pytest.raises(AuthenticationError):
            client.validate_token()

    @patch("requests.Session.get")
    def test_latest_tag_success(self, mock_get):
        """Test successfully retrieving latest tag."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"values": [{"name": "v1.2.3"}]}
        mock_get.return_value = mock_response

        client = BitbucketClient()
        result = client.latest_tag("myworkspace", "myrepo")

        assert result == "v1.2.3"
        mock_get.assert_called_once()

    @patch("requests.Session.get")
    def test_latest_tag_404_returns_none(self, mock_get):
        """Test handling 404 response returns None."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        client = BitbucketClient()
        result = client.latest_tag("myworkspace", "missing")

        assert result is None

    @patch("requests.Session.get")
    def test_latest_tag_401_returns_none(self, mock_get):
        """Test handling 401 response returns None."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        client = BitbucketClient()
        result = client.latest_tag("myworkspace", "myrepo")

        assert result is None

    @patch("requests.Session.get")
    def test_latest_tag_403_returns_none(self, mock_get):
        """Test handling 403 response returns None."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response

        client = BitbucketClient()
        result = client.latest_tag("myworkspace", "myrepo")

        assert result is None

    @patch("requests.Session.get")
    def test_latest_tag_empty_values_returns_none(self, mock_get):
        """Test handling empty 'values' returns None."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"values": []}
        mock_get.return_value = mock_response

        client = BitbucketClient()
        result = client.latest_tag("myworkspace", "myrepo")

        assert result is None

    @patch("requests.Session.get")
    def test_latest_tag_request_exception_raises_network_error(self, mock_get):
        """Test that a RequestException raises NetworkError."""
        import requests

        mock_get.side_effect = requests.RequestException("Timeout")

        client = BitbucketClient()

        with pytest.raises(NetworkError):
            client.latest_tag("myworkspace", "myrepo")

    @patch("requests.Session.get")
    def test_latest_ref_success(self, mock_get):
        """Test latest_ref delegates to latest_tag and returns name."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"values": [{"name": "v2.0.0"}]}
        mock_get.return_value = mock_response

        client = BitbucketClient()
        result = client.latest_ref("https://bitbucket.org/myworkspace/myrepo")

        assert result == "v2.0.0"

    @patch("requests.Session.get")
    def test_latest_ref_with_git_suffix(self, mock_get):
        """Test latest_ref strips trailing .git suffix."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"values": [{"name": "v3.1.0"}]}
        mock_get.return_value = mock_response

        client = BitbucketClient()
        result = client.latest_ref("https://bitbucket.org/myworkspace/myrepo.git")

        assert result == "v3.1.0"
        # Ensure the URL passed in has the slug without .git
        url_called = mock_get.call_args.args[0]
        assert "myworkspace/myrepo/refs/tags" in url_called

    def test_latest_ref_invalid_url_returns_none(self):
        """Test latest_ref returns None when URL lacks workspace/repo."""
        client = BitbucketClient()
        result = client.latest_ref("https://bitbucket.org/onlyworkspace")

        assert result is None

    def test_latest_ref_exception_returns_none(self):
        """Test latest_ref returns None on unexpected exception."""
        client = BitbucketClient()
        # Passing a non-string triggers exception inside urlparse usage
        result = client.latest_ref(12345)  # type: ignore[arg-type]

        assert result is None

    def test_detect_bitbucket_host_cloud(self):
        """Test detecting Bitbucket Cloud host."""
        url = "https://bitbucket.org/workspace/repo.git"
        result = BitbucketClient.detect_bitbucket_host(url)

        assert result == "https://bitbucket.org"

    def test_detect_bitbucket_host_non_bitbucket(self):
        """Test that non-Bitbucket URLs return None."""
        url = "https://github.com/org/repo.git"
        result = BitbucketClient.detect_bitbucket_host(url)

        assert result is None

    def test_detect_bitbucket_host_invalid_url(self):
        """Test that invalid URLs return None."""
        result = BitbucketClient.detect_bitbucket_host("not-a-url")

        assert result is None

    def test_headers_with_bearer(self):
        """Test _headers includes Bearer Authorization when token only."""
        client = BitbucketClient(token="my-token")
        headers = client._headers()

        assert headers["Accept"] == "application/json"
        assert headers["Authorization"] == "Bearer my-token"

    def test_headers_with_basic_no_authorization_header(self):
        """Test _headers omits Authorization when using Basic auth."""
        client = BitbucketClient(token="apppw", username="alice")
        headers = client._headers()

        assert headers["Accept"] == "application/json"
        assert "Authorization" not in headers

    def test_headers_without_token(self):
        """Test _headers only contains Accept when no token."""
        client = BitbucketClient()
        headers = client._headers()

        assert headers == {"Accept": "application/json"}

    def test_auth_returns_tuple_when_both_set(self):
        """Test _auth returns (username, token) tuple."""
        client = BitbucketClient(token="apppw", username="alice")
        assert client._auth() == ("alice", "apppw")

    def test_auth_returns_none_otherwise(self):
        """Test _auth returns None when username or token missing."""
        assert BitbucketClient()._auth() is None
        assert BitbucketClient(token="t")._auth() is None
        assert BitbucketClient(username="u")._auth() is None
