"""
Secrets accessor — environment-aware.

Dev  (ENV=development, the default):
    Reads directly from os.environ.
    dotenv is loaded in main.py before the app starts, so .env values
    are already in os.environ by the time any code calls get_secret().

Prod (ENV=production):
    Fetches from AWS Secrets Manager.
    Secrets are expected to be stored as a single JSON blob under one
    secret name (e.g. {"OPENAI_API_KEY": "sk-...", "SECRET_KEY": "..."}).
    Results are cached in memory after the first AWS call so we don't
    hit the AWS API on every request.

Usage:
    from app.config.secrets import get_secret

    api_key = get_secret("OPENAI_API_KEY")
    jwt_secret = get_secret("SECRET_KEY")
"""
import json
import logging
import os

logger = logging.getLogger(__name__)

# Module-level cache — populated on first call, reused for the rest of the process lifetime
_cache: dict[str, str] = {}


def _fetch_all_from_aws() -> None:
    """
    Pull the entire secrets JSON blob from AWS Secrets Manager and
    populate _cache with all key/value pairs at once.
    This way a single AWS API call serves all secrets for the lifetime
    of the process.
    """
    import boto3
    from botocore.exceptions import ClientError

    secret_name = os.environ.get("AWS_SECRET_NAME", "healthcare-agent-secrets")
    region = os.environ.get("AWS_REGION", "us-east-1")

    client = boto3.client("secretsmanager", region_name=region)
    try:
        response = client.get_secret_value(SecretId=secret_name)
    except ClientError as exc:
        raise RuntimeError(
            f"Could not fetch secrets from AWS Secrets Manager "
            f"(secret: '{secret_name}', region: '{region}'). Error: {exc}"
        ) from exc

    raw = response.get("SecretString", "{}")
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            _cache.update({k: str(v) for k, v in data.items()})
            logger.info("Loaded %d secrets from AWS Secrets Manager.", len(data))
        else:
            raise ValueError("Expected a JSON object in AWS secret, got something else.")
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"AWS secret '{secret_name}' is not valid JSON. "
            "Store secrets as a JSON object: {\"KEY\": \"value\", ...}"
        ) from exc


def get_secret(key: str) -> str:
    """
    Return the value for the given secret key.

    - In development: reads from os.environ (populated by dotenv).
    - In production: fetches from AWS Secrets Manager on first call,
      then serves from the in-memory cache.
    - Returns an empty string if not found in development (so the app
      starts even with missing optional secrets).
    - Raises RuntimeError if a key is missing in production.
    """
    # Serve from cache if already loaded
    if key in _cache:
        return _cache[key]

    is_production = os.environ.get("ENV", "development").lower() == "production"

    if is_production:
        # Load all secrets from AWS in one call, then return the requested key
        _fetch_all_from_aws()
        if key not in _cache:
            raise RuntimeError(
                f"Secret '{key}' not found in AWS Secrets Manager response. "
                "Make sure it is included in the JSON blob."
            )
        return _cache[key]
    else:
        # Development: read from environment
        value = os.environ.get(key, "")
        if not value:
            logger.warning("Secret '%s' is not set in the environment.", key)
        _cache[key] = value
        return value
