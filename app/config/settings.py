"""
Non-secret application configuration.

API keys and other secrets are NOT stored here.
They are read from the environment (dev) or AWS Secrets Manager (prod)
via app.config.secrets.get_secret().

Settings here are safe to log, inspect, or print without security risk.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── App ───────────────────────────────────────────────────────────────────
    app_name: str = "Sunflower Health AI"
    debug: bool = False

    # Set DATABASE_URL in your .env file. Never hardcode credentials here.
    # Dev:  DATABASE_URL=sqlite:///./dev.db
    # Prod: DATABASE_URL=postgresql://user:pass@rds-host:5432/dbname
    # ── Database ──────────────────────────────────────────────────────────────

    # ── LLM ───────────────────────────────────────────────────────────────────
    llm_provider: str = "openai"       # "openai" or "claude"
    openai_model: str = "gpt-4o"
    anthropic_model: str = "claude-opus-4-6"

    # ── SuperMemory ───────────────────────────────────────────────────────────
    supermemory_container_prefix: str = "healthcare_user"

    # ── AWS / S3 ──────────────────────────────────────────────────────────────
    aws_region: str = "us-east-1"
    s3_bucket_name: str = ""
    # Name of the secret in AWS Secrets Manager that holds all API keys
    aws_secret_name: str = "healthcare-agent-secrets"

    # ── Auth (JWT) ────────────────────────────────────────────────────────────
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours

    # ── Google OAuth ──────────────────────────────────────────────────────────
    # google_client_id is public-facing (safe to store here).
    # GOOGLE_CLIENT_SECRET is a real secret — fetched via get_secret().
    google_client_id: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/auth/google/callback"
    frontend_url: str = "http://localhost:8501"

    # ── Admin ─────────────────────────────────────────────────────────────────
    admin_email: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
