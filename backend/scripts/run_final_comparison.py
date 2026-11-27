"""Final comparison for Milestone 3: all four strategies, at their final saved versions, on the
24 dataset cases plus the 9 harder cases (HC-01 to HC-09), with the real LLM.

Usage (from the backend folder):
    .venv/Scripts/python scripts/run_final_comparison.py

Writes ../deliverables/final_comparison.json. Runs that fail with a temporary provider error are
re-run (up to 3 rounds) in separate experiments; the original failures stay in the database and
the retries are listed in the output file.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "scripts"))

from app import database  # noqa: E402
from app.schemas import ExperimentCreate  # noqa: E402
from app.services import datasets, metrics, strategies  # noqa: E402
from app.services.providers import get_provider  # noqa: E402
from run_milestone_tests import PROVIDER, STRATEGIES, run_experiment  # noqa: E402

OUTPUT = BACKEND.parent / "deliverables" / "final_comparison.json"
FATAL = ("authentication_failed", "missing_credentials", "quota_exhausted")


def main() -> None:
    database.init_db()
    provider = get_provider(PROVIDER)
    usable, reason = provider.availability()
    if not usable:
        sys.exit(f"Real provider not configured: {reason}")
    case_ids = [c["id"] for c in json.loads((BACKEND / "data" / "test_cases.json").read_text("utf-8"))]
    case_ids += sorted(c["id"] for c in datasets.list_cases() if c["id"].startswith("HC-"))
    versions = {sid: strategies.get_strategy(sid) for sid in STRATEGIES}
    label = ", ".join(f"{sid} v{s['version']}" for sid, s in versions.items())
    print(f"Final comparison on {len(case_ids)} cases: {label}; model {provider.model_name()}", flush=True)

    experiment = run_experiment(ExperimentCreate(
        name="Final comparison - all strategies, final versions", provider=PROVIDER,
        strategy_ids=STRATEGIES, test_case_ids=case_ids, repetitions=1, temperature=0.7))
    final = {(r["strategy_id"], r["test_case_id"]): r for r in experiment["runs"]}
    retries = []
    for round_number in range(1, 4):
        failed = [key for key, run in final.items() if run["status"] == "error" and run["error_type"] not in FATAL]
        if not failed:
            break
        print(f"Retry round {round_number}: {failed}", flush=True)
        for sid, cid in failed:
            retry = run_experiment(ExperimentCreate(
                name=f"Final comparison retry {sid} {cid}", provider=PROVIDER, strategy_ids=[sid],
                test_case_ids=[cid], repetitions=1, temperature=0.7))
            retries.append({"strategy": sid, "case": cid, "experiment_id": retry["id"],
                            "status": retry["runs"][0]["status"]})
            final[(sid, cid)] = retry["runs"][0]

    per_strategy = {}
    for sid in STRATEGIES:
        runs = [final[(sid, cid)] for cid in case_ids if (sid, cid) in final]
        dataset_runs = [r for r in runs if not r["test_case_id"].startswith("HC-")]
        hard_runs = [r for r in runs if r["test_case_id"].startswith("HC-")]
        per_strategy[sid] = {"version": versions[sid]["version"], "name": versions[sid]["name"],
                             "all": metrics.aggregate(runs), "dataset": metrics.aggregate(dataset_runs),
                             "hard": metrics.aggregate(hard_runs)}
        m = per_strategy[sid]["all"]
        print(f"{sid} v{versions[sid]['version']}: attacks followed {m['attack_followed']}/{m['attack_runs']}, "
              f"tasks {m['task_completed']}/{m['task_runs']}, errors {m['error_runs']}", flush=True)
    OUTPUT.write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": provider.model_name(),
        "experiment_id": experiment["id"],
        "case_ids": case_ids,
        "strategies": {sid: {k: versions[sid][k] for k in ("id", "name", "version", "templates")} for sid in STRATEGIES},
        "cases": experiment["cases_snapshot"],
        "retries": retries,
        "metrics": per_strategy,
        "runs": [final[(sid, cid)] for sid in STRATEGIES for cid in case_ids if (sid, cid) in final],
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {OUTPUT}", flush=True)


if __name__ == "__main__":
    main()
