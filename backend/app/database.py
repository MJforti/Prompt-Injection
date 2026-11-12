"""SQLite persistence layer (standard-library sqlite3, one connection per operation)."""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator

from .config import DEFAULT_DATASET_PATH, get_settings
from .defaults import default_strategies

SCHEMA = """
CREATE TABLE IF NOT EXISTS test_cases (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    user_task TEXT NOT NULL,
    document TEXT NOT NULL,
    attack_type TEXT,
    injection_text TEXT,
    attack_markers TEXT NOT NULL DEFAULT '[]',
    expected_facts TEXT NOT NULL DEFAULT '[]',
    expected_behavior TEXT NOT NULL DEFAULT '',
    evaluation_criteria TEXT NOT NULL DEFAULT '',
    pass_threshold REAL NOT NULL DEFAULT 0.67,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS strategies (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    short_label TEXT NOT NULL,
    kind TEXT NOT NULL,
    description TEXT NOT NULL,
    templates TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    sort_order INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS experiments (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    mode TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    simulated INTEGER NOT NULL,
    repetitions INTEGER NOT NULL,
    temperature REAL NOT NULL,
    use_llm_judge INTEGER NOT NULL DEFAULT 0,
    strategy_snapshot TEXT NOT NULL,
    cases_snapshot TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL,
    total_runs INTEGER NOT NULL,
    completed_runs INTEGER NOT NULL DEFAULT 0,
    error TEXT,
    created_at TEXT NOT NULL,
    finished_at TEXT
);

CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id TEXT NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    test_case_id TEXT NOT NULL,
    category TEXT NOT NULL,
    strategy_id TEXT NOT NULL,
    strategy_version INTEGER NOT NULL,
    repetition INTEGER NOT NULL,
    prompt TEXT NOT NULL,
    stage1_output TEXT,
    response TEXT,
    status TEXT NOT NULL,
    error_type TEXT,
    error TEXT,
    latency_ms REAL,
    attack_status TEXT,
    task_status TEXT,
    fact_coverage REAL,
    refused INTEGER,
    evaluation TEXT,
    llm_judge TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_runs_experiment ON runs(experiment_id);
CREATE INDEX IF NOT EXISTS idx_runs_strategy ON runs(strategy_id);
"""

JSON_COLUMNS = {
    "attack_markers", "expected_facts", "templates", "strategy_snapshot", "cases_snapshot",
    "prompt", "evaluation", "llm_judge",
}
BOOL_COLUMNS = {"simulated", "use_llm_judge", "refused"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    settings = get_settings()
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(settings.db_path, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    """Convert a row to a dict, decoding JSON and boolean columns."""
    if row is None:
        return None
    record = dict(row)
    for key, value in record.items():
        if key in JSON_COLUMNS and isinstance(value, str):
            record[key] = json.loads(value)
        elif key in BOOL_COLUMNS and value is not None:
            record[key] = bool(value)
    return record


def encode(record: dict[str, Any]) -> dict[str, Any]:
    """Prepare a dict for insertion: JSON-encode structured columns."""
    encoded = {}
    for key, value in record.items():
        if key in JSON_COLUMNS and value is not None:
            encoded[key] = json.dumps(value, ensure_ascii=False)
        elif isinstance(value, bool):
            encoded[key] = int(value)
        else:
            encoded[key] = value
    return encoded


def insert(connection: sqlite3.Connection, table: str, record: dict[str, Any]) -> int:
    encoded = encode(record)
    columns = ", ".join(encoded)
    placeholders = ", ".join(f":{key}" for key in encoded)
    cursor = connection.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", encoded)
    return cursor.lastrowid


def update(connection: sqlite3.Connection, table: str, key_value: Any, record: dict[str, Any]) -> None:
    encoded = encode(record)
    assignments = ", ".join(f"{key} = :{key}" for key in encoded)
    connection.execute(f"UPDATE {table} SET {assignments} WHERE id = :_id", {**encoded, "_id": key_value})


def init_db() -> None:
    """Create tables and seed default strategies and the bundled synthetic dataset."""
    with connect() as connection:
        connection.executescript(SCHEMA)
        if connection.execute("SELECT COUNT(*) FROM strategies").fetchone()[0] == 0:
            for order, strategy in enumerate(default_strategies()):
                insert(connection, "strategies", {**strategy, "version": 1, "sort_order": order,
                                                  "updated_at": utc_now()})
        if connection.execute("SELECT COUNT(*) FROM test_cases").fetchone()[0] == 0:
            seed_default_dataset(connection)


def seed_default_dataset(connection: sqlite3.Connection) -> int:
    cases = json.loads(DEFAULT_DATASET_PATH.read_text(encoding="utf-8"))
    now = utc_now()
    for case in cases:
        insert(connection, "test_cases", {**case, "created_at": now, "updated_at": now})
    return len(cases)
