"""Runtime configuration, read from environment variables only.

Settings are re-read on every call so tests (and a restarted server) always see
the current environment. API credentials are never written to disk or logged.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_DIR / "data"
DEFAULT_DATASET_PATH = DATA_DIR / "test_cases.json"

# A local .env file is optional; real environment variables take precedence.
load_dotenv(BACKEND_DIR / ".env", override=False)


@dataclass(frozen=True)
class Settings:
    db_path: Path
    llm_base_url: str
    llm_api_key: str
    llm_model: str
    llm_timeout_seconds: float
    llm_min_interval_seconds: float
    llm_concurrency: int
    sync_execution: bool
    demo_seed_path: Path | None
    cors_origins: list[str]

    @property
    def llm_configured(self) -> bool:
        return bool(self.llm_api_key and self.llm_model)


def _backend_path(value: str) -> Path:
    """Resolve a relative path against the backend folder, not the process working directory."""
    path = Path(value)
    return path if path.is_absolute() else BACKEND_DIR / path


def get_settings() -> Settings:
    origins = os.environ.get(
        "CONTEXTSHIELD_CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    )
    return Settings(
        db_path=Path(os.environ.get("CONTEXTSHIELD_DB_PATH", DATA_DIR / "contextshield.db")),
        llm_base_url=os.environ.get("CONTEXTSHIELD_LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
        llm_api_key=os.environ.get("CONTEXTSHIELD_LLM_API_KEY", "") or os.environ.get("OPENAI_API_KEY", ""),
        llm_model=os.environ.get("CONTEXTSHIELD_LLM_MODEL", ""),
        llm_timeout_seconds=float(os.environ.get("CONTEXTSHIELD_LLM_TIMEOUT", "60")),
        # Minimum seconds between consecutive LLM calls (0 = no pacing). Useful for free-tier
        # per-minute quotas, e.g. 6.5 keeps a 10-requests-per-minute limit.
        llm_min_interval_seconds=float(os.environ.get("CONTEXTSHIELD_LLM_MIN_INTERVAL", "0")),
        # Number of real-LLM calls an experiment may have in flight at once (1 = sequential).
        llm_concurrency=max(1, int(os.environ.get("CONTEXTSHIELD_LLM_CONCURRENCY", "1"))),
        # Run experiments inside the POST request instead of a background task. Needed on
        # serverless hosts (e.g. Vercel), which may freeze a function once it has responded.
        sync_execution=os.environ.get("CONTEXTSHIELD_SYNC_EXECUTION", "0").lower() in ("1", "true", "yes"),
        # Optional JSON file of stored experiments to load into an empty database (public demo).
        demo_seed_path=_backend_path(os.environ["CONTEXTSHIELD_DEMO_SEED"]) if os.environ.get("CONTEXTSHIELD_DEMO_SEED") else None,
        cors_origins=[origin.strip() for origin in origins.split(",") if origin.strip()],
    )
