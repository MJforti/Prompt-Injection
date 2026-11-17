"""Export the real-LLM experiments from the local database into data/demo_experiments.json.

Usage (from the backend folder):
    .venv/Scripts/python scripts/export_demo_seed.py

The public demo deployment loads this file on start-up (see CONTEXTSHIELD_DEMO_SEED), so
visitors can browse the actual Milestone 2 results without the deployment needing an API key.
Only real (non-simulated) experiments that finished are exported; nothing is modified.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from app import database as db  # noqa: E402
from app.services.evaluator import evaluate_response  # noqa: E402

OUTPUT = BACKEND / "data" / "demo_experiments.json"
NAME_PATTERNS = ("Milestone 2 test table%", "Prompt iteration%")


def apply_dataset_corrections(experiment: dict) -> None:
    """Re-score runs whose case definition was later corrected in data/test_cases.json.

    This is the same documented correction the Milestone 2 PDFs apply (TC-004's fact keywords),
    so the public demo shows the same numbers. The experiment name records it.
    """
    current = {case["id"]: case for case in json.loads((BACKEND / "data" / "test_cases.json").read_text("utf-8"))}
    corrected = []
    for index, case in enumerate(experiment["cases_snapshot"]):
        fixed = current.get(case["id"])
        if not fixed or fixed["expected_facts"] == case["expected_facts"]:
            continue
        experiment["cases_snapshot"][index] = {**case, "expected_facts": fixed["expected_facts"]}
        for run in experiment["runs"]:
            if run["test_case_id"] == case["id"] and run["status"] == "ok":
                evaluation = evaluate_response(run["response"], experiment["cases_snapshot"][index])
                run.update(evaluation=evaluation, task_status=evaluation["task"]["status"],
                           fact_coverage=evaluation["task"]["coverage"],
                           attack_status=evaluation["attack"]["status"], refused=evaluation["refusal"]["refused"])
        corrected.append(case["id"])
    if corrected:
        experiment["name"] += f" ({', '.join(corrected)} re-scored with corrected keywords)"


def main() -> None:
    experiments = []
    with db.connect() as connection:
        for pattern in NAME_PATTERNS:
            rows = connection.execute(
                "SELECT * FROM experiments WHERE name LIKE ? AND simulated = 0 "
                "AND status IN ('completed', 'completed_with_errors') ORDER BY created_at", (pattern,)).fetchall()
            for row in rows:
                experiment = db.row_to_dict(row)
                experiment["runs"] = [db.row_to_dict(run) for run in connection.execute(
                    "SELECT * FROM runs WHERE experiment_id = ? ORDER BY id", (experiment["id"],)).fetchall()]
                for run in experiment["runs"]:
                    run.pop("id", None)
                apply_dataset_corrections(experiment)
                experiments.append(experiment)
    OUTPUT.write_text(json.dumps(experiments, ensure_ascii=False), encoding="utf-8")
    runs = sum(len(e["runs"]) for e in experiments)
    print(f"Exported {len(experiments)} real experiments ({runs} runs) to {OUTPUT} "
          f"({OUTPUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
