"""
Configuration — loaded from environment variables via pydantic-settings.

Section 16.2 is the canonical reference for variable names.
Anything marked [CONFIRM] here corresponds to an open Section 12 question.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Database ─────────────────────────────────────────────────────────────
    database_url: str

    # ── Redis ─────────────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379"

    # ── Auth ─────────────────────────────────────────────────────────────────
    jwt_secret: str
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 30

    # ── Object storage ────────────────────────────────────────────────────────
    s3_bucket: str = "greencore-uploads"
    s3_region: str = "eu-west-2"
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    s3_endpoint_url: str = ""  # blank = AWS S3; set for R2 / Supabase Storage

    # ── Mapping / routing provider — [CONFIRM Section 12 Q1] ─────────────────
    maps_provider: str = "google"
    google_maps_api_key: str = ""
    route_optimization_provider: str = "google_cloud_fleet_routing"

    # ── Push notifications ────────────────────────────────────────────────────
    fcm_service_account_json_path: str = ""

    # ── Location tracking — [CONFIRM Section 12 Q3 and Q7] ───────────────────
    location_ping_interval_seconds: int = 20
    location_data_retention_days: int = 90

    # ── App environment ───────────────────────────────────────────────────────
    environment: Literal["development", "staging", "production"] = "development"
    log_level: Literal["debug", "info", "warning", "error"] = "info"

    # ── CORS ──────────────────────────────────────────────────────────────────
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton — call this everywhere rather than instantiating Settings()."""
    return Settings()
