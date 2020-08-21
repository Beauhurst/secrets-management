import json
from typing import Any, Dict, Optional

import boto3
import environ
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig
from botocore.exceptions import ClientError

from .util import bool_converter


class Secret:
    def __init__(self, secret: Dict[str, str], fallback_env: Optional[environ.Env] = None):
        self.secret = secret
        self.fallback_env = fallback_env

    def get(
        self,
        key: str,
        allow_env_fallback: bool = False,
        default: Optional[Any] = None,
        cast_type: Optional[str] = None,
    ) -> Any:
        """
        Retrieve a specific value from the secret (with optional fallback retrieval from .env file)

        Supports casting to int, float or bool
        """

        value = self._get(key, allow_env_fallback, default)

        if cast_type:
            value = self._cast(value, cast_type)

        return value

    def _get(
        self,
        key: str,
        allow_env_fallback: bool,
        default: Any,
    ) -> Any:

        try:
            return self.secret[key]
        except KeyError:
            if allow_env_fallback:
                try:
                    if default is not None:
                        return self.fallback_env(key, default=default)
                    else:
                        return self.fallback_env(key)
                except TypeError:
                    raise AttributeError('`fallback_env` not set for this secret')
            if default is not None:
                return default
            raise

    def _cast(self, value: str, type_: str):
        """Cast a string value to a given type"""

        cast_map = {
            'int': int,
            'float': float,
            'bool': bool_converter,
        }

        if type_ not in cast_map.keys():
            raise ValueError(f'`cast` kwarg must be one of {list(cast_map.keys())}')

        return cast_map.get(type_)(value)

    def set_fallback_env(self, fallback_env: environ.Env):
        """Set a fallback environment object for retrieving missing keys"""
        self.fallback_env = fallback_env
        return self


class SecretsManager:

    def __init__(self, region_name: str):
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name,
        )
        cache_config = SecretCacheConfig()
        self.cache = SecretCache(config=cache_config, client=client)

    def retrieve_secret(self, secret_name: str) -> Optional[Secret]:
        """
        Retrieve a secret from the cache (or fetch from AWS if not already cached)

        Assumes that we are just storing text, not binary data (for now)
        """

        try:
            return Secret(json.loads(self.cache.get_secret_string(secret_name)))
        except ClientError as e:
            if e.response['Error']['Code'] == 'DecryptionFailureException':
                # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
                raise e
            elif e.response['Error']['Code'] == 'InternalServiceErrorException':
                # An error occurred on the server side.
                raise e
            elif e.response['Error']['Code'] == 'InvalidParameterException':
                # You provided an invalid value for a parameter.
                raise e
            elif e.response['Error']['Code'] == 'InvalidRequestException':
                # You provided a parameter value that is not valid for the current state of the resource.
                raise e
            elif e.response['Error']['Code'] == 'ResourceNotFoundException':
                # We can't find the resource that you asked for.
                raise e
