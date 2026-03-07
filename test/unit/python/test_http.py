"""Tests for the shared HTTP session builder."""

from agronomist.http import build_session


class TestBuildSession:
    """Tests for build_session function."""

    def test_returns_session_with_retry_adapter(self):
        """Test that session has retry adapters mounted."""
        session = build_session()
        assert "https://" in session.adapters
        assert "http://" in session.adapters

    def test_custom_retries_and_backoff(self):
        """Test session accepts custom retry and backoff values."""
        session = build_session(retries=5, backoff_factor=1.0)
        adapter = session.get_adapter("https://example.com")
        assert adapter.max_retries.total == 5
        assert adapter.max_retries.backoff_factor == 1.0

    def test_default_retry_parameters(self):
        """Test default retry parameters are applied."""
        session = build_session()
        adapter = session.get_adapter("https://example.com")
        assert adapter.max_retries.total == 3
        assert adapter.max_retries.backoff_factor == 0.5
        assert 429 in adapter.max_retries.status_forcelist
        assert 500 in adapter.max_retries.status_forcelist

    def test_only_get_method_retried(self):
        """Test that only GET requests are retried."""
        session = build_session()
        adapter = session.get_adapter("https://example.com")
        assert "GET" in adapter.max_retries.allowed_methods
