"""Test-dataset management: CRUD plus CSV/JSON import and export."""
from __future__ import annotations

import csv
import io
import json
import re

from pydantic import ValidationError

from .. import database as db
from ..schemas import TestCaseCreate

CSV_COLUMNS = [
    "id", "title", "category", "user_task", "document", "attack_type", "injection_text",
    "attack_markers", "expected_facts", "expected_behavior", "evaluation_criteria", "pass_threshold",
]
CSV_JSON_COLUMNS = ("attack_markers", "expected_facts")


class DatasetError(ValueError):
    """Raised for invalid dataset operations (bad import file, duplicate id, ...)."""


def list_cases(category: str | None = None) -> list[dict]:
    query, parameters = "SELECT * FROM test_cases", ()
    if category:
        query, parameters = query + " WHERE category = ?", (category,)
    with db.connect() as connection:
        return [db.row_to_dict(row) for row in connection.execute(query + " ORDER BY id", parameters).fetchall()]


def get_case(case_id: str) -> dict | None:
    with db.connect() as connection:
        return db.row_to_dict(connection.execute("SELECT * FROM test_cases WHERE id = ?", (case_id,)).fetchone())


def _next_id(connection) -> str:
    numbers = [int(match.group(1)) for (case_id,) in connection.execute("SELECT id FROM test_cases")
               if (match := re.fullmatch(r"TC-(\d+)", case_id))]
    return f"TC-{max(numbers, default=0) + 1:03d}"


def create_case(case: TestCaseCreate) -> dict:
    with db.connect() as connection:
        case_id = case.id or _next_id(connection)
        if connection.execute("SELECT 1 FROM test_cases WHERE id = ?", (case_id,)).fetchone():
            raise DatasetError(f"a test case with id '{case_id}' already exists")
        now = db.utc_now()
        db.insert(connection, "test_cases", {**case.model_dump(), "id": case_id,
                                             "created_at": now, "updated_at": now})
    return get_case(case_id)


def update_case(case_id: str, case: TestCaseCreate) -> dict | None:
    with db.connect() as connection:
        if not connection.execute("SELECT 1 FROM test_cases WHERE id = ?", (case_id,)).fetchone():
            return None
        record = case.model_dump(exclude={"id"})
        db.update(connection, "test_cases", case_id, {**record, "updated_at": db.utc_now()})
    return get_case(case_id)


def delete_case(case_id: str) -> bool:
    with db.connect() as connection:
        return connection.execute("DELETE FROM test_cases WHERE id = ?", (case_id,)).rowcount > 0


def reset_to_default() -> int:
    """Replace the dataset with the bundled synthetic default dataset."""
    with db.connect() as connection:
        connection.execute("DELETE FROM test_cases")
        return db.seed_default_dataset(connection)


# --------------------------------------------------------------------------- export
def _exportable(case: dict) -> dict:
    return {column: case[column] for column in CSV_COLUMNS}


def export_json() -> str:
    return json.dumps([_exportable(case) for case in list_cases()], indent=2, ensure_ascii=False)


def export_csv() -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS, lineterminator="\n")
    writer.writeheader()
    for case in list_cases():
        row = _exportable(case)
        for column in CSV_JSON_COLUMNS:
            row[column] = json.dumps(row[column], ensure_ascii=False)
        writer.writerow({key: "" if value is None else value for key, value in row.items()})
    return buffer.getvalue()


# --------------------------------------------------------------------------- import
def parse_import(content: str, file_format: str) -> list[TestCaseCreate]:
    """Parse and validate an import file. Raises DatasetError naming the offending row."""
    try:
        if file_format == "json":
            raw_cases = json.loads(content)
            if not isinstance(raw_cases, list):
                raise DatasetError("JSON import must be a list of test cases")
        else:
            raw_cases = []
            for row in csv.DictReader(io.StringIO(content.lstrip("﻿"))):
                for column in CSV_JSON_COLUMNS:
                    row[column] = json.loads(row.get(column) or "[]")
                row["pass_threshold"] = float(row.get("pass_threshold") or 0.67)
                raw_cases.append({key: (value if value != "" else None) for key, value in row.items()
                                  if key in CSV_COLUMNS})
    except (json.JSONDecodeError, csv.Error, ValueError) as error:
        if isinstance(error, DatasetError):
            raise
        raise DatasetError(f"could not parse {file_format.upper()} file: {error}") from error

    if not raw_cases:
        raise DatasetError("the import file contains no test cases")
    cases = []
    for index, raw in enumerate(raw_cases, start=1):
        if not isinstance(raw, dict):
            raise DatasetError(f"row {index}: expected an object")
        raw = {key: value for key, value in raw.items() if value is not None}
        try:
            cases.append(TestCaseCreate(**raw))
        except ValidationError as error:
            first = error.errors()[0]
            location = ".".join(str(part) for part in first["loc"]) or "row"
            raise DatasetError(f"row {index} ({raw.get('id', 'no id')}): {location}: {first['msg']}") from error
    ids = [case.id for case in cases if case.id]
    if len(ids) != len(set(ids)):
        raise DatasetError("the import file contains duplicate test case ids")
    return cases


def import_cases(content: str, file_format: str, mode: str) -> dict:
    """Import cases. mode='merge' upserts by id; mode='replace' swaps the whole dataset."""
    cases = parse_import(content, file_format)
    created = updated = 0
    with db.connect() as connection:
        if mode == "replace":
            connection.execute("DELETE FROM test_cases")
        now = db.utc_now()
        for case in cases:
            case_id = case.id or _next_id(connection)
            record = case.model_dump(exclude={"id"})
            if connection.execute("SELECT 1 FROM test_cases WHERE id = ?", (case_id,)).fetchone():
                db.update(connection, "test_cases", case_id, {**record, "updated_at": now})
                updated += 1
            else:
                db.insert(connection, "test_cases", {**record, "id": case_id,
                                                     "created_at": now, "updated_at": now})
                created += 1
    return {"created": created, "updated": updated, "total": len(cases)}
