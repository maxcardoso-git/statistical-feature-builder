"""
Configuration management for SFB service.
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Service Info
    service_name: str = "Statistical Feature Builder"
    service_version: str = "1.0.0"
    environment: str = "development"

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    reload: bool = False

    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # OAuth2
    oauth2_enabled: bool = True
    oauth2_token_url: str = "https://auth.pulse.ai/oauth/token"
    oauth2_scopes: str = "sfb.read,sfb.write"

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 500

    # Data Masking
    data_masking_enabled: bool = True
    data_masking_fields: str = "cpf,salario"

    # Logging
    log_level: str = "info"
    log_format: str = "json"

    # OpenTelemetry
    otel_enabled: bool = True
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "sfb"
    otel_traces_exporter: str = "otlp"
    otel_metrics_exporter: str = "otlp"

    # Performance
    request_timeout_ms: int = 60000
    max_request_size_mb: int = 10

    # CORS
    cors_enabled: bool = True
    cors_origins: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def masking_fields_list(self) -> List[str]:
        """Parse masking fields into a list."""
        return [field.strip() for field in self.data_masking_fields.split(",")]

    @property
    def oauth2_scopes_dict(self) -> dict:
        """Convert scopes string to dict format."""
        scopes = [scope.strip() for scope in self.oauth2_scopes.split(",")]
        return {scope: f"Access to {scope}" for scope in scopes}


# Global settings instance
settings = Settings()
