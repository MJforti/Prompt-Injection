"""Test the CURRENT saved version of one prompt strategy on the whole dataset (real LLM).

Usage (from the backend folder):
    .venv/Scripts/python scripts/run_prompt_iteration.py two_stage
    .venv/Scripts/python scripts/run_prompt_iteration.py trust_boundaries --extra-cases HC-

Edit the strategy first (Strategy Comparison page in the app, or app.services.strategies),
which saves it as a new version. The results are written to
../deliverables/iterations/<strategy>_v<version>.json and the experiments appear in
Experiment History. Runs that fail with a temporary provider error are re-run (up to 3 rounds)
in separate experiments; the original failures stay in the database.
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
from run_milestone_tests import PROVIDER, run_experiment  # noqa: E402

OUTPUT_DIR = BACKEND.parent / "deliverables" / "iterations"
FATAL = ("authentication_failed", "missing_credentials", "quota_exhausted")


def main(strategy_id: str, extra_prefix: str | None = None) -> None:
    database.init_db()
    provider = get_provider(PROVIDER)
    usable, reason = provider.availability()
    if not usable:
        sys.exit(f"Real provider not configured: {reason}")
    strategy = strategies.get_strategy(strategy_id)
    if strategy is None:
        sys.exit(f"Unknown strategy: {strategy_id}")
    case_ids = [c["id"] for c in json.loads((BACKEND / "data" / "test_cases.json").read_text("utf-8"))]
    if extra_prefix:
        # Extra cases added in the app (e.g. harder attacks with IDs like HC-01) are tested too.
        extra = [c["id"] for c in datasets.list_cases() if c["id"].startswith(extra_prefix)]
        if not extra:
            sys.exit(f"No test cases with IDs starting with '{extra_prefix}' found in the app's dataset.")
        case_ids += [cid for cid in extra if cid not in case_ids]
    print(f"{strategy['name']} v{strategy['version']} on {len(case_ids)} cases, model {provider.model_name()}",
          flush=True)

    experiment = run_experiment(ExperimentCreate(
        name=f"Prompt iteration - {strategy_id} v{strategy['version']}", provider=PROVIDER,
        strategy_ids=[strategy_id], test_case_ids=case_ids, repetitions=1, temperature=0.7))
    final = {run["test_case_id"]: run for run in experiment["runs"]}
    retries = []
    for round_number in range(1, 4):
        failed = [cid for cid, run in final.items() if run["status"] == "error" and run["error_type"] not in FATAL]
        if not failed:
            break
        print(f"Retry round {round_number}: {failed}", flush=True)
        for case_id in failed:
            retry = run_experiment(ExperimentCreate(
                name=f"Prompt iteration - {strategy_id} v{strategy['version']} retry {case_id}",
                provider=PROVIDER, strategy_ids=[strategy_id], test_case_ids=[case_id],
                repetitions=1, temperature=0.7))
            retries.append({"case": case_id, "experiment_id": retry["id"], "status": retry["runs"][0]["status"]})
            final[case_id] = retry["runs"][0]

    runs = [final[cid] for cid in case_ids if cid in final]
    summary = metrics.aggregate(runs)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{strategy_id}_v{strategy['version']}.json"
    path.write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": provider.model_name(),
        "strategy": {key: strategy[key] for key in ("id", "name", "version", "templates")},
        "experiment_id": experiment["id"],
        "cases": experiment["cases_snapshot"],
        "retries": retries,
        "metrics": summary,
        "runs": runs,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"ACR {summary['attack_compliance_rate']}% ({summary['attack_followed']}/{summary['attack_runs']}), "
          f"LTA {summary['task_accuracy']}% ({summary['task_completed']}/{summary['task_runs']}), "
          f"FRR {summary['false_refusal_rate']}%, errors {summary['error_runs']}, "
          f"avg {summary['avg_latency_ms']} ms", flush=True)
    print(f"Saved {path}", flush=True)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("strategy", nargs="?", default="two_stage",
                        help="strategy id: baseline, instruction_separation, trust_boundaries or two_stage")
    parser.add_argument("--extra-cases", metavar="PREFIX",
                        help="also test app dataset cases whose ID starts with PREFIX (for example HC-)")
    args = parser.parse_args()
    main(args.strategy, args.extra_cases)
