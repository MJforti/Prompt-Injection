"""Experiment execution engine.

Pipeline: validate -> snapshot config -> for each (case, repetition, strategy)
render prompt -> call provider -> store raw response -> evaluate -> store.
Every strategy receives the same task, document, provider, model and
temperature. Provider failures are recorded on the run; they are never replaced
with simulated output.
"""
from __future__ import annotations

import secrets
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from .. import database as db
from ..config import get_settings
from ..schemas import ExperimentCreate
from . import metrics, prompts
from .evaluator import evaluate_response
from .llm_judge import judge_response
from .providers import Provider, ProviderError, SimulationContext, get_provider

CUSTOM_CASE_ID = "CUSTOM"


class ExperimentValidationError(ValueError):
    """Raised when an experiment request cannot be run as specified."""


# --------------------------------------------------------------------------- creation
def create_experiment(request: ExperimentCreate) -> dict:
    """Validate the request and persist the experiment configuration (status: pending)."""
    try:
        provider = get_provider(request.provider)
    except KeyError as error:
        raise ExperimentValidationError(str(error)) from error
    usable, reason = provider.availability()
    if not usable:
        raise ExperimentValidationError(
            f"Provider '{provider.id}' is not configured. {reason}. "
            "Set the variables and restart the backend, or choose the mock simulator.")
    if request.use_llm_judge and provider.simulated:
        raise ExperimentValidationError("The LLM judge requires a real provider; the mock simulator cannot judge.")

    with db.connect() as connection:
        strategies = []
        for strategy_id in request.strategy_ids:
            row = db.row_to_dict(connection.execute(
                "SELECT * FROM strategies WHERE id = ?", (strategy_id,)).fetchone())
            if row is None:
                raise ExperimentValidationError(f"unknown strategy: {strategy_id}")
            try:
                prompts.validate_templates(row["kind"], row["templates"])
            except prompts.TemplateError as error:
                raise ExperimentValidationError(f"strategy '{strategy_id}': {error}") from error
            strategies.append({key: row[key] for key in
                               ("id", "name", "short_label", "kind", "description", "templates", "version")})

        if request.custom_case is not None:
            custom = request.custom_case.model_dump()
            cases = [{
                "id": CUSTOM_CASE_ID, "title": "Custom input", "category": "custom",
                "user_task": custom["user_task"], "document": custom["document"],
                "attack_type": "custom" if custom["attack_markers"] else None,
                "injection_text": custom["injection_text"],
                "attack_markers": custom["attack_markers"],
                "expected_facts": custom["expected_facts"],
                "expected_behavior": "", "evaluation_criteria": "", "pass_threshold": 0.67,
            }]
        else:
            cases = []
            for case_id in dict.fromkeys(request.test_case_ids):
                row = db.row_to_dict(connection.execute(
                    "SELECT * FROM test_cases WHERE id = ?", (case_id,)).fetchone())
                if row is None:
                    raise ExperimentValidationError(f"unknown test case: {case_id}")
                row.pop("created_at", None)
                row.pop("updated_at", None)
                cases.append(row)

        now = datetime.now(timezone.utc)
        experiment_id = f"EXP-{now:%Y%m%d-%H%M%S}-{secrets.token_hex(2).upper()}"
        mode = "single" if len(cases) == 1 else "batch"
        default_name = cases[0]["title"] if mode == "single" else f"Batch of {len(cases)} test cases"
        record = {
            "id": experiment_id,
            "name": (request.name or "").strip() or default_name,
            "mode": mode,
            "provider": provider.id,
            "model": provider.model_name(),
            "simulated": provider.simulated,
            "repetitions": request.repetitions,
            "temperature": request.temperature,
            "use_llm_judge": request.use_llm_judge,
            "strategy_snapshot": strategies,
            "cases_snapshot": cases,
            "status": "pending",
            "total_runs": len(cases) * len(strategies) * request.repetitions,
            "completed_runs": 0,
            "created_at": db.utc_now(),
        }
        db.insert(connection, "experiments", record)
    return record


# --------------------------------------------------------------------------- execution
def execute_strategy(provider: Provider, strategy: dict, case: dict, temperature: float, seed: str) -> dict:
    """Run one strategy against one case. Returns prompt, outputs and latency.

    Raises ProviderError; the partial ``prompt`` is attached to the exception so
    the failed run can still show exactly what was sent.
    """
    simulation = SimulationContext(
        seed=seed,
        injection_text=case.get("injection_text"),
        attack_markers=case.get("attack_markers") or [],
        expected_facts=case.get("expected_facts") or [],
    )
    templates = strategy["templates"]
    prompt: dict = {}
    try:
        if strategy["kind"] == "two_stage":
            prompt["stage1"] = prompts.render_stage1(templates, case["user_task"], case["document"])
            stage1 = provider.complete(prompt["stage1"], temperature, simulation)
            prompt["stage2"] = prompts.render_stage2(templates, case["user_task"], stage1.text)
            stage2 = provider.complete(prompt["stage2"], temperature, simulation)
            return {"prompt": prompt, "stage1_output": stage1.text, "response": stage2.text,
                    "latency_ms": stage1.latency_ms + stage2.latency_ms}
        prompt["main"] = prompts.render_single(templates, case["user_task"], case["document"])
        result = provider.complete(prompt["main"], temperature, simulation)
        return {"prompt": prompt, "stage1_output": None, "response": result.text,
                "latency_ms": result.latency_ms}
    except ProviderError as error:
        error.prompt = prompt  # type: ignore[attr-defined]
        raise


def run_experiment(experiment_id: str) -> None:
    """Execute a pending experiment to completion, persisting every run as it finishes."""
    with db.connect() as connection:
        experiment = db.row_to_dict(connection.execute(
            "SELECT * FROM experiments WHERE id = ?", (experiment_id,)).fetchone())
        if experiment is None or experiment["status"] != "pending":
            return
        db.update(connection, "experiments", experiment_id, {"status": "running"})

    provider = get_provider(experiment["provider"])
    jobs = [(case, repetition, strategy)
            for case in experiment["cases_snapshot"]
            for repetition in range(1, experiment["repetitions"] + 1)
            for strategy in experiment["strategy_snapshot"]]
    state = {"completed": 0, "errors": 0, "fatal": None}
    lock = threading.Lock()

    def execute(job: tuple) -> None:
        # Once a fatal error (bad key, exhausted daily quota) occurs, remaining jobs are skipped.
        if state["fatal"] is not None:
            return
        case, repetition, strategy = job
        run = _run_once(provider, experiment, strategy, case, repetition)
        fatal = run.pop("_fatal")
        with lock:
            if run["status"] == "error":
                state["errors"] += 1
                if fatal and state["fatal"] is None:
                    state["fatal"] = f"{run['error_type']}: {run['error']}"
            state["completed"] += 1
            with db.connect() as connection:
                db.insert(connection, "runs", run)
                db.update(connection, "experiments", experiment_id, {"completed_runs": state["completed"]})

    # Concurrency only changes how many calls are in flight, never the inputs: every job still
    # gets the same task, document, model and temperature as in a sequential run.
    workers = max(1, min(get_settings().llm_concurrency, len(jobs))) if not provider.simulated else 1
    try:
        if workers == 1:
            for job in jobs:
                execute(job)
        else:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                for future in [pool.submit(execute, job) for job in jobs]:
                    future.result()
    except Exception as error:  # unexpected internal failure: surface it, never hide it
        state["fatal"] = state["fatal"] or f"internal_error: {error}"
    fatal_error, error_count = state["fatal"], state["errors"]

    if fatal_error:
        status = "failed"
    elif error_count:
        status = "completed_with_errors"
    else:
        status = "completed"
    with db.connect() as connection:
        db.update(connection, "experiments", experiment_id,
                  {"status": status, "error": fatal_error, "finished_at": db.utc_now()})


def _run_once(provider: Provider, experiment: dict, strategy: dict, case: dict, repetition: int) -> dict:
    run = {
        "experiment_id": experiment["id"],
        "test_case_id": case["id"],
        "category": case["category"],
        "strategy_id": strategy["id"],
        "strategy_version": strategy["version"],
        "repetition": repetition,
        "created_at": db.utc_now(),
        "_fatal": False,
    }
    seed = f"{experiment['id']}|{case['id']}|{strategy['id']}|{repetition}"
    try:
        outcome = execute_strategy(provider, strategy, case, experiment["temperature"], seed)
    except ProviderError as error:
        run.update({
            "prompt": getattr(error, "prompt", {}),
            "status": "error", "error_type": error.error_type, "error": str(error),
            "_fatal": error.fatal,
        })
        return run

    evaluation = evaluate_response(outcome["response"], case)
    run.update({
        "prompt": outcome["prompt"],
        "stage1_output": outcome["stage1_output"],
        "response": outcome["response"],
        "status": "ok",
        "latency_ms": round(outcome["latency_ms"], 2),
        "attack_status": evaluation["attack"]["status"],
        "task_status": evaluation["task"]["status"],
        "fact_coverage": evaluation["task"]["coverage"],
        "refused": evaluation["refusal"]["refused"],
        "evaluation": evaluation,
    })
    if experiment["use_llm_judge"]:
        run["llm_judge"] = judge_response(provider, case, outcome["response"])
    return run


# --------------------------------------------------------------------------- reading
def list_experiments() -> list[dict]:
    with db.connect() as connection:
        experiments = [db.row_to_dict(row) for row in connection.execute(
            "SELECT * FROM experiments ORDER BY created_at DESC, id DESC").fetchall()]
        runs = [dict(row) for row in connection.execute(
            "SELECT experiment_id, strategy_id, category, status, attack_status, task_status, refused, "
            "latency_ms FROM runs").fetchall()]
    runs_by_experiment: dict[str, list[dict]] = {}
    for run in runs:
        runs_by_experiment.setdefault(run["experiment_id"], []).append(run)
    summaries = []
    for experiment in experiments:
        summaries.append({
            **{key: experiment[key] for key in (
                "id", "name", "mode", "provider", "model", "simulated", "repetitions", "temperature",
                "status", "total_runs", "completed_runs", "error", "created_at", "finished_at")},
            "strategy_ids": [strategy["id"] for strategy in experiment["strategy_snapshot"]],
            "test_case_count": len(experiment["cases_snapshot"]),
            "metrics": metrics.aggregate(runs_by_experiment.get(experiment["id"], [])),
        })
    return summaries


def get_experiment(experiment_id: str) -> dict | None:
    with db.connect() as connection:
        experiment = db.row_to_dict(connection.execute(
            "SELECT * FROM experiments WHERE id = ?", (experiment_id,)).fetchone())
        if experiment is None:
            return None
        runs = [db.row_to_dict(row) for row in connection.execute(
            "SELECT * FROM runs WHERE experiment_id = ? ORDER BY id", (experiment_id,)).fetchall()]
    # Parallel runs finish in any order; present them in the experiment's logical order.
    case_order = {case["id"]: index for index, case in enumerate(experiment["cases_snapshot"])}
    strategy_order = {s["id"]: index for index, s in enumerate(experiment["strategy_snapshot"])}
    runs.sort(key=lambda run: (case_order.get(run["test_case_id"], 0), run["repetition"],
                               strategy_order.get(run["strategy_id"], 0)))
    strategy_metrics = metrics.by_strategy(runs)
    experiment["runs"] = runs
    experiment["metrics"] = {
        "overall": metrics.aggregate(runs),
        "by_strategy": strategy_metrics,
        "by_category": metrics.by_category(runs),
        "most_effective_strategy": metrics.most_effective_strategy(strategy_metrics),
        "most_effective_rule": metrics.MOST_EFFECTIVE_RULE,
    }
    return experiment


def delete_experiment(experiment_id: str) -> bool:
    with db.connect() as connection:
        cursor = connection.execute("DELETE FROM experiments WHERE id = ?", (experiment_id,))
        return cursor.rowcount > 0
