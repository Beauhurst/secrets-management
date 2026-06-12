# Secrets Management Utility

This project can be pip installed into other projects as a Python package to have access to the secrets management classes and helpers for integrating AWS Secrets Manager.

## Adding into a project

You can `pip` install it manually via `pip install git+https://github.com/Beauhurst/secrets-management.git`

Or add `git+https://github.com/Beauhurst/secrets-management.git` to your `requirements.txt` file.

## Usage

Most operations stem from the `SecretManager` object which you import as:
```python
from secrets_management import SecretsManager
```

### Simple use case

```python
secrets_manager = SecretsManager(region_name="eu-west-2")
secret = secrets_manager.retrieve_secret("name/of/secret")

SOME_API_KEY = secret.get("SOME_API_KEY")
ANOTHER_API_KEY = secret.get("ANOTHER_API_KEY", default="a-sensible-default")
```

### Falling back on `.env` file

If you want to enable falling back on a local `.env` file:

```python
env = environ.Env()
secrets_manager = SecretsManager(region_name="eu-west-2")
secret = secrets_manager.retrieve_secret("name/of/secret")
secret.set_fallback_env(env)

# will try and access `SOME_API_KEY` from environment file if not found in secret
SOME_API_KEY = secret.get("SOME_API_KEY", allow_env_fallback=True)

# will try and access `ANOTHER_API_KEY` from environment file if not found in secret
# if not in the environment file, then use the `default` value
ANOTHER_API_KEY = secret.get("ANOTHER_API_KEY", allow_env_fallback=True, default="a-sensible-default")
```

Ideally, you should combine both approaches and read the secret name and the corresponding region from an env file to avoid hardcoding this in your settings.

### Casting

If you want to store a data type other than a string you can make use of the `cast_type` kwarg by passing any callable. The callable is applied to the retrieved value:

```python
SOME_SECRET_NUMBER = secret.get("SOME_SECRET_NUMBER", cast_type=int)
```

This works with any callable, so you can perform arbitrary conversions, for example parsing JSON or dates:

```python
import json
from datetime import date

CONFIG = secret.get("CONFIG", cast_type=json.loads)
START_DATE = secret.get("START_DATE", cast_type=date.fromisoformat)
```

For boolean values, a helper that understands common `"yes"`/`"no"`/`"on"`/`"off"` style inputs is provided:

```python
from secrets_management.util import bool_converter

DEBUG = secret.get("DEBUG", cast_type=bool_converter)
```

> **Deprecated:** passing a string (`"int"`, `"float"` or `"bool"`) is still supported for backwards compatibility but is deprecated and will emit a `DeprecationWarning`. Pass the corresponding callable instead (`int`, `float`, or `bool_converter`).

## Development

For local development, install the package in editable mode together with the test dependencies:

```bash
pip install -e ".[test]"
```

### Running the test suite

Run the full test suite locally with:

```bash
pytest
```

### Continuous integration

The test suite also runs automatically in GitHub Actions for pushes and pull requests via `.github/workflows/tests.yml`.

