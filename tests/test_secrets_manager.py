import json
import warnings
from unittest.mock import MagicMock

import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws

from secrets_management import Secret, SecretsManager


# ---------------------------------------------------------------------------
# Secret
# ---------------------------------------------------------------------------


class TestSecretGet:
    """Tests for Secret.get()"""

    def _make_secret(self, data=None):
        return Secret(data or {"KEY": "value", "NUMBER": "42", "FLAG": "true"})

    def test_get_existing_key(self):
        secret = self._make_secret()
        assert secret.get("KEY") == "value"

    def test_get_missing_key_with_default(self):
        secret = self._make_secret()
        assert secret.get("MISSING", default="fallback") == "fallback"

    def test_get_missing_key_without_default_raises_key_error(self):
        secret = self._make_secret()
        with pytest.raises(KeyError):
            secret.get("MISSING")

    def test_get_cast_to_int(self):
        secret = self._make_secret()
        with pytest.warns(DeprecationWarning):
            assert secret.get("NUMBER", cast_type="int") == 42

    def test_get_cast_to_float(self):
        secret = self._make_secret({"PRICE": "3.14"})
        with pytest.warns(DeprecationWarning):
            assert secret.get("PRICE", cast_type="float") == pytest.approx(3.14)

    def test_get_cast_to_bool_true(self):
        secret = self._make_secret()
        with pytest.warns(DeprecationWarning):
            assert secret.get("FLAG", cast_type="bool") is True

    def test_get_cast_to_bool_false(self):
        secret = self._make_secret({"FLAG": "false"})
        with pytest.warns(DeprecationWarning):
            assert secret.get("FLAG", cast_type="bool") is False

    def test_get_invalid_cast_type_raises_value_error(self):
        secret = self._make_secret()
        with pytest.raises(ValueError):
            secret.get("KEY", cast_type="list")

    def test_get_cast_to_bool_via_get(self):
        secret = self._make_secret({"FLAG": "on"})
        with pytest.warns(DeprecationWarning):
            assert secret.get("FLAG", cast_type="bool") is True

    def test_get_cast_failure_raises_value_error(self):
        """Casting a non-numeric value to int should raise ValueError."""
        secret = self._make_secret()
        with pytest.warns(DeprecationWarning), pytest.raises(ValueError):
            secret.get("KEY", cast_type="int")

    def test_get_cast_applied_to_env_fallback_value(self):
        """The cast is applied to a value retrieved via env fallback."""
        secret = self._make_secret()
        mock_env = MagicMock(return_value="7")
        secret.set_fallback_env(mock_env)
        with pytest.warns(DeprecationWarning):
            assert secret.get("MISSING", allow_env_fallback=True, cast_type="int") == 7

    def test_get_string_cast_type_emits_deprecation_warning(self):
        """Using a string cast_type should emit a DeprecationWarning."""
        secret = self._make_secret()
        with pytest.warns(DeprecationWarning, match="deprecated"):
            secret.get("NUMBER", cast_type="int")

    def test_get_cast_with_callable_int(self):
        """A callable (the builtin int) can be passed as cast_type."""
        secret = self._make_secret()
        assert secret.get("NUMBER", cast_type=int) == 42

    def test_get_cast_with_callable_does_not_warn(self):
        """Passing a callable should not emit a DeprecationWarning."""
        secret = self._make_secret()
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            assert secret.get("NUMBER", cast_type=int) == 42

    def test_get_cast_with_custom_callable(self):
        """An arbitrary callable, e.g. json.loads, can be used for conversion."""
        secret = self._make_secret({"DATA": '{"a": 1, "b": [2, 3]}'})
        assert secret.get("DATA", cast_type=json.loads) == {"a": 1, "b": [2, 3]}

    def test_get_cast_with_lambda(self):
        """A lambda can be used as a custom converter."""
        secret = self._make_secret()
        assert secret.get("KEY", cast_type=lambda v: v.upper()) == "VALUE"

    def test_get_cast_callable_applied_to_env_fallback_value(self):
        """A callable cast is applied to a value retrieved via env fallback."""
        secret = self._make_secret()
        mock_env = MagicMock(return_value="7")
        secret.set_fallback_env(mock_env)
        assert secret.get("MISSING", allow_env_fallback=True, cast_type=int) == 7

    def test_get_cast_callable_failure_propagates(self):
        """Errors raised by the callable propagate to the caller."""
        secret = self._make_secret()
        with pytest.raises(ValueError):
            secret.get("KEY", cast_type=int)

    def test_init_with_fallback_env_uses_it(self):
        """A fallback_env passed via the constructor is used directly."""
        mock_env = MagicMock(return_value="env_value")
        secret = Secret({"KEY": "value"}, fallback_env=mock_env)
        assert secret.get("MISSING", allow_env_fallback=True) == "env_value"
        mock_env.assert_called_once_with("MISSING")

    def test_get_with_env_fallback_key_present_in_secret(self):
        """When the key exists in the secret, env fallback is not consulted."""
        secret = self._make_secret()
        mock_env = MagicMock()
        secret.set_fallback_env(mock_env)
        assert secret.get("KEY", allow_env_fallback=True) == "value"
        mock_env.assert_not_called()

    def test_get_with_env_fallback_key_missing_uses_env(self):
        """When the key is absent, env fallback is used."""
        secret = self._make_secret()
        mock_env = MagicMock(return_value="env_value")
        secret.set_fallback_env(mock_env)
        assert secret.get("MISSING", allow_env_fallback=True) == "env_value"
        mock_env.assert_called_once_with("MISSING")

    def test_get_with_env_fallback_key_missing_uses_default(self):
        """When the key is absent and a default is given, pass it to the env callable."""
        secret = self._make_secret()
        mock_env = MagicMock(return_value="env_default")
        secret.set_fallback_env(mock_env)
        result = secret.get("MISSING", allow_env_fallback=True, default="my_default")
        assert result == "env_default"
        mock_env.assert_called_once_with("MISSING", default="my_default")

    def test_get_with_env_fallback_but_no_fallback_env_set_raises_attribute_error(self):
        """Calling allow_env_fallback without setting fallback_env raises AttributeError."""
        secret = self._make_secret()
        with pytest.raises(AttributeError, match="`fallback_env` not set"):
            secret.get("MISSING", allow_env_fallback=True)


class TestSecretSetFallbackEnv:
    def test_set_fallback_env_returns_self(self):
        secret = Secret({"KEY": "value"})
        mock_env = MagicMock()
        result = secret.set_fallback_env(mock_env)
        assert result is secret

    def test_set_fallback_env_stores_env(self):
        secret = Secret({"KEY": "value"})
        mock_env = MagicMock()
        secret.set_fallback_env(mock_env)
        assert secret.fallback_env is mock_env


# ---------------------------------------------------------------------------
# SecretsManager
# ---------------------------------------------------------------------------


class TestSecretsManagerRetrieveSecret:
    region = "eu-west-2"

    def _create_secret(self, name, payload):
        client = boto3.client("secretsmanager", region_name=self.region)
        client.create_secret(Name=name, SecretString=json.dumps(payload))

    @mock_aws
    def test_retrieve_secret_returns_secret_instance(self):
        payload = {"DB_PASSWORD": "supersecret", "API_KEY": "abc123"}
        self._create_secret("my/secret/name", payload)

        manager = SecretsManager(region_name=self.region)
        secret = manager.retrieve_secret("my/secret/name")

        assert isinstance(secret, Secret)
        assert secret.get("DB_PASSWORD") == "supersecret"
        assert secret.get("API_KEY") == "abc123"

    @mock_aws
    def test_retrieve_missing_secret_raises_client_error(self):
        manager = SecretsManager(region_name=self.region)
        with pytest.raises(ClientError):
            manager.retrieve_secret("does/not/exist")

    @mock_aws
    def test_retrieve_binary_secret_raises_value_error(self):
        client = boto3.client("secretsmanager", region_name=self.region)
        client.create_secret(Name="binary/secret", SecretBinary=b"\x00\x01\x02")

        manager = SecretsManager(region_name=self.region)
        with pytest.raises(ValueError, match="does not contain a SecretString"):
            manager.retrieve_secret("binary/secret")
