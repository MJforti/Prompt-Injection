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
    cors_origins: list[str]

    @property
    def llm_configured(self) -> bool:
        return bool(self.llm_api_key and self.llm_model)


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
        cors_origins=[origin.strip() for origin in origins.split(",") if origin.strip()],
    )
