"""Tests for custom exceptions."""

import pytest

from agronomist.exceptions import (
    AgronomistError,
    AuthenticationError,
    ConfigError,
    NetworkError,
    ResolverError,
)


class TestExceptionHierarchy:
    def test_agronomist_error_is_exception(self):
        assert issubclass(AgronomistError, Exception)

    def test_network_error_is_agronomist_error(self):
        assert issubclass(NetworkError, AgronomistError)

    def test_authentication_error_is_agronomist_error(self):
        assert issubclass(AuthenticationError, AgronomistError)

    def test_resolver_error_is_agronomist_error(self):
        assert issubclass(ResolverError, AgronomistError)

    def test_config_error_is_agronomist_error(self):
        assert issubclass(ConfigError, AgronomistError)


class TestExceptionRaise:
    def test_raise_agronomist_error(self):
        with pytest.raises(AgronomistError, match="base error"):
            raise AgronomistError("base error")

    def test_raise_network_error(self):
        with pytest.raises(NetworkError, match="connection refused"):
            raise NetworkError("connection refused")

    def test_raise_authentication_error(self):
        with pytest.raises(AuthenticationError, match="invalid token"):
            raise AuthenticationError("invalid token")

    def test_raise_resolver_error(self):
        with pytest.raises(ResolverError, match="cannot resolve"):
            raise ResolverError("cannot resolve")

    def test_raise_config_error(self):
        with pytest.raises(ConfigError, match="missing key"):
            raise ConfigError("missing key")

    def test_network_error_caught_as_agronomist_error(self):
        with pytest.raises(AgronomistError):
            raise NetworkError("timeout")

    def test_authentication_error_caught_as_agronomist_error(self):
        with pytest.raises(AgronomistError):
            raise AuthenticationError("401")

    def test_resolver_error_caught_as_agronomist_error(self):
        with pytest.raises(AgronomistError):
            raise ResolverError("no tags found")

    def test_config_error_caught_as_agronomist_error(self):
        with pytest.raises(AgronomistError):
            raise ConfigError("bad yaml")

    def test_exception_message_preserved(self):
        msg = "detailed error message"
        exc = NetworkError(msg)
        assert str(exc) == msg

    def test_exception_without_message(self):
        exc = AgronomistError()
        assert isinstance(exc, AgronomistError)
