"""CSV and JSON export of a single experiment."""
from __future__ import annotations

import csv
import io
import json

RESULT_COLUMNS = [
    "experiment_id", "provider", "model", "result_type", "run_id", "test_case_id", "category",
    "strategy_id", "strategy_name", "strategy_version", "repetition", "status", "attack_status",
    "task_status", "fact_coverage", "false_refusal", "latency_ms", "error_type", "error",
    "user_task", "response", "stage1_output", "created_at",
]


def result_type(experiment: dict) -> str:
    return "SIMULATED (mock provider)" if experiment["simulated"] else "REAL LLM API"


def experiment_to_csv(experiment: dict) -> str:
    strategies = {strategy["id"]: strategy for strategy in experiment["strategy_snapshot"]}
    cases = {case["id"]: case for case in experiment["cases_snapshot"]}
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=RESULT_COLUMNS, lineterminator="\n")
    writer.writeheader()
    for run in experiment["runs"]:
        writer.writerow({
            "experiment_id": experiment["id"],
            "provider": experiment["provider"],
            "model": experiment["model"],
            "result_type": result_type(experiment),
            "run_id": run["id"],
            "test_case_id": run["test_case_id"],
            "category": run["category"],
            "strategy_id": run["strategy_id"],
            "strategy_name": strategies[run["strategy_id"]]["name"],
            "strategy_version": run["strategy_version"],
            "repetition": run["repetition"],
            "status": run["status"],
            "attack_status": run["attack_status"] or "",
            "task_status": run["task_status"] or "",
            "fact_coverage": "" if run["fact_coverage"] is None else round(run["fact_coverage"], 3),
            "false_refusal": "" if run["refused"] is None else run["refused"],
            "latency_ms": "" if run["latency_ms"] is None else run["latency_ms"],
            "error_type": run["error_type"] or "",
            "error": run["error"] or "",
            "user_task": cases[run["test_case_id"]]["user_task"],
            "response": run["response"] or "",
            "stage1_output": run["stage1_output"] or "",
            "created_at": run["created_at"],
        })
    return buffer.getvalue()


def experiment_to_json(experiment: dict) -> str:
    document = {
        "project": "ContextShield",
        "result_type": result_type(experiment),
        "notice": ("These results were produced by the mock simulator and are NOT real LLM behaviour."
                   if experiment["simulated"] else
                   "These results were produced by real LLM API calls."),
        "experiment": experiment,
    }
    return json.dumps(document, indent=2, ensure_ascii=False)
