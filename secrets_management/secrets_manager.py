import json
import warnings
from typing import Any, Callable, Dict, Optional, Union

import boto3
import environ

from .util import bool_converter

_not_set = object()


class Secret:
    def __init__(self, secret: Dict[str, str], fallback_env: Optional[environ.Env] = None):
        self.secret = secret
        self.fallback_env = fallback_env

    def get(
        self,
        key: str,
        allow_env_fallback: bool = False,
        default: Any = _not_set,
        cast_type: Optional[Union[str, Callable[[Any], Any]]] = None,
    ) -> Any:
        """
        Retrieve a specific value from the secret (with optional fallback retrieval from .env file)

        ``cast_type`` may be any callable (e.g. the builtin ``int``, ``json.loads`` or a
        custom function) which will be applied to the retrieved value.

        Passing a string (one of ``"int"``, ``"float"`` or ``"bool"``) is also supported for
        backwards compatibility, but is deprecated; pass the corresponding callable instead.
        """

        value = self._get(key, allow_env_fallback, default)

        if cast_type:
            value = self._cast(value, cast_type)

        return value

    def _get(self, key: str, allow_env_fallback: bool, default: Any) -> Any:

        try:
            return self.secret[key]
        except KeyError:
            if allow_env_fallback:
                if self.fallback_env is None:
                    raise AttributeError("`fallback_env` not set for this secret")
                if default is _not_set:
                    return self.fallback_env(key)
                return self.fallback_env(key, default=default)
            elif default is _not_set:
                raise
            return default

    def _cast(self, value: str, cast_type: Union[str, Callable[[Any], Any]]):
        """Cast a value using a callable, or a deprecated string alias."""

        if callable(cast_type):
            return cast_type(value)

        cast_map = {
            "int": int,
            "float": float,
            "bool": bool_converter,
        }

        if cast_type not in cast_map.keys():
            raise ValueError(
                f"`cast_type` must be a callable or one of {list(cast_map.keys())}"
            )

        warnings.warn(
            "Passing a string to `cast_type` is deprecated; pass a callable instead "
            f"(e.g. `cast_type={cast_map[cast_type].__name__}`).",
            DeprecationWarning,
            stacklevel=3,
        )

        return cast_map[cast_type](value)

    def set_fallback_env(self, fallback_env: environ.Env):
        """Set a fallback environment object for retrieving missing keys"""
        self.fallback_env = fallback_env
        return self


class SecretsManager:
    def __init__(self, region_name: str):
        self.region_name = region_name

    def retrieve_secret(self, secret_name: str) -> Secret:
        """
        Retrieve a secret from AWS Secrets Manager

        Assumes that we are just storing text, not binary data (for now)
        """
        client = boto3.client("secretsmanager", region_name=self.region_name)
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)

        if "SecretString" not in get_secret_value_response:
            raise ValueError(
                f"Secret '{secret_name}' does not contain a SecretString (binary secrets are not supported)"
            )

        return Secret(json.loads(get_secret_value_response["SecretString"]))
