from functools import lru_cache

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application configuration.

    All values are overridable via environment variables / .env so the same
    codebase can later point at a Dynamics NAV-fed database, etc. without
    code changes.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "QR Traceability Platform"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str = (
        "postgresql+psycopg2://traceuser:tracepass@localhost:5432/traceability"
    )

    # Base URL the traceability QR codes should resolve to when scanned.
    # In production this points at the deployed frontend, e.g.
    # https://trace.acme-manufacturing.com
    TRACE_PUBLIC_BASE_URL: str = "http://localhost:5173"

    # Comma-separated list, e.g. "https://trace.acme.com,https://admin.acme.com".
    # A bare JSON array also works. Kept as a plain string field (rather than
    # list[str]) because pydantic-settings otherwise requires env vars for
    # list-typed fields to be JSON-encoded, which is an easy way for an
    # unfamiliar deploy config to crash the app on startup.
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

    TRACE_ID_PREFIX: str = "TRC"

    # Feature flags reserved for future integrations (see architecture notes
    # in README). Kept here so toggling them never requires touching
    # business logic.
    ENABLE_NAV_SYNC: bool = False
    ENABLE_RBAC: bool = False
    ENABLE_APPROVAL_WORKFLOWS: bool = False

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _stringify_cors_origins(cls, v):
        # Accept a Python list too, so code (e.g. tests) can still pass one.
        return ",".join(v) if isinstance(v, list) else v

    @property
    def cors_origins_list(self) -> list[str]:
        """Effective CORS allow-list: whatever CORS_ORIGINS names, plus the
        deployed frontend's own public URL (TRACE_PUBLIC_BASE_URL) - so a
        split-origin deployment (frontend and API on different hosts) works
        the moment TRACE_PUBLIC_BASE_URL is set correctly, without also
        requiring a separately-maintained CORS_ORIGINS entry for it."""
        origins = {o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()}
        origins.add(self.TRACE_PUBLIC_BASE_URL)
        return list(origins)

    @model_validator(mode="after")
    def _guard_qr_target_in_production(self) -> "Settings":
        # QR codes bake TRACE_PUBLIC_BASE_URL into the image at generation
        # time (see qr_service.py) - once printed, a code can't be changed.
        # Refuse to boot in production with a localhost target so a
        # misconfigured deploy can't silently generate permanently-broken
        # QR codes for real data.
        if self.ENVIRONMENT == "production":
            base = self.TRACE_PUBLIC_BASE_URL.lower()
            if "localhost" in base or "127.0.0.1" in base:
                raise ValueError(
                    "TRACE_PUBLIC_BASE_URL is set to a localhost address while "
                    "ENVIRONMENT=production. QR codes encode this URL permanently "
                    "at generation time - set TRACE_PUBLIC_BASE_URL to the real "
                    "public (https://) domain of the deployed frontend before "
                    "starting the app."
                )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
