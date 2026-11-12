"""HTTP API. All routes live under /api."""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from fastapi.responses import Response

from .. import APP_NAME, APP_VERSION
from ..schemas import (CATEGORIES, DatasetImport, ExperimentCreate, PromptPreviewRequest, StrategyUpdate,
                       TestCaseCreate)
from ..services import analytics, datasets, engine, exports, prompts, report, strategies
from ..services.evaluator import EVALUATOR_VERSION
from ..services.providers import list_providers

router = APIRouter(prefix="/api")


def _download(content: str | bytes, media_type: str, filename: str) -> Response:
    return Response(content=content, media_type=media_type,
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})


# --------------------------------------------------------------------------- system
@router.get("/health", tags=["system"])
def health() -> dict:
    return {"status": "ok", "app": APP_NAME, "version": APP_VERSION, "evaluator": EVALUATOR_VERSION}


@router.get("/providers", tags=["system"])
def providers() -> list[dict]:
    return list_providers()


@router.get("/categories", tags=["system"])
def categories() -> list[str]:
    return list(CATEGORIES)


# --------------------------------------------------------------------------- dataset
@router.get("/test-cases", tags=["dataset"])
def list_test_cases(category: str | None = None) -> list[dict]:
    return datasets.list_cases(category)


@router.get("/test-cases/export", tags=["dataset"])
def export_test_cases(format: Literal["json", "csv"] = "json") -> Response:
    if format == "csv":
        return _download(datasets.export_csv(), "text/csv; charset=utf-8", "contextshield_test_cases.csv")
    return _download(datasets.export_json(), "application/json", "contextshield_test_cases.json")


@router.post("/test-cases/import", tags=["dataset"])
def import_test_cases(payload: DatasetImport) -> dict:
    try:
        return datasets.import_cases(payload.content, payload.format, payload.mode)
    except datasets.DatasetError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/test-cases/reset", tags=["dataset"])
def reset_test_cases() -> dict:
    return {"total": datasets.reset_to_default()}


@router.post("/test-cases", status_code=201, tags=["dataset"])
def create_test_case(case: TestCaseCreate) -> dict:
    try:
        return datasets.create_case(case)
    except datasets.DatasetError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.get("/test-cases/{case_id}", tags=["dataset"])
def get_test_case(case_id: str) -> dict:
    case = datasets.get_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="test case not found")
    return case


@router.put("/test-cases/{case_id}", tags=["dataset"])
def update_test_case(case_id: str, case: TestCaseCreate) -> dict:
    updated = datasets.update_case(case_id, case)
    if updated is None:
        raise HTTPException(status_code=404, detail="test case not found")
    return updated


@router.delete("/test-cases/{case_id}", status_code=204, tags=["dataset"])
def delete_test_case(case_id: str) -> Response:
    if not datasets.delete_case(case_id):
        raise HTTPException(status_code=404, detail="test case not found")
    return Response(status_code=204)


# --------------------------------------------------------------------------- strategies
@router.get("/strategies", tags=["strategies"])
def list_strategies() -> list[dict]:
    return strategies.list_strategies()


@router.post("/strategies/preview", tags=["strategies"])
def preview_prompt(payload: PromptPreviewRequest) -> dict:
    rendered = strategies.preview(payload.strategy_id, payload.user_task, payload.document)
    if rendered is None:
        raise HTTPException(status_code=404, detail="strategy not found")
    return rendered


@router.put("/strategies/{strategy_id}", tags=["strategies"])
def update_strategy(strategy_id: str, payload: StrategyUpdate) -> dict:
    try:
        updated = strategies.update_strategy(strategy_id, payload.templates, payload.name, payload.description)
    except prompts.TemplateError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    if updated is None:
        raise HTTPException(status_code=404, detail="strategy not found")
    return updated


@router.post("/strategies/{strategy_id}/reset", tags=["strategies"])
def reset_strategy(strategy_id: str) -> dict:
    restored = strategies.reset_strategy(strategy_id)
    if restored is None:
        raise HTTPException(status_code=404, detail="strategy not found")
    return restored


# --------------------------------------------------------------------------- experiments
@router.post("/experiments", status_code=202, tags=["experiments"])
def create_experiment(payload: ExperimentCreate, background: BackgroundTasks) -> dict:
    """Validate and store the experiment, then execute it in the background.

    Poll GET /api/experiments/{id} for progress and results.
    """
    try:
        experiment = engine.create_experiment(payload)
    except engine.ExperimentValidationError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    background.add_task(engine.run_experiment, experiment["id"])
    return {"id": experiment["id"], "status": experiment["status"], "total_runs": experiment["total_runs"]}


@router.get("/experiments", tags=["experiments"])
def list_experiments() -> list[dict]:
    return engine.list_experiments()


def _experiment_or_404(experiment_id: str) -> dict:
    experiment = engine.get_experiment(experiment_id)
    if experiment is None:
        raise HTTPException(status_code=404, detail="experiment not found")
    return experiment


@router.get("/experiments/{experiment_id}", tags=["experiments"])
def get_experiment(experiment_id: str) -> dict:
    return _experiment_or_404(experiment_id)


@router.delete("/experiments/{experiment_id}", status_code=204, tags=["experiments"])
def delete_experiment(experiment_id: str) -> Response:
    if not engine.delete_experiment(experiment_id):
        raise HTTPException(status_code=404, detail="experiment not found")
    return Response(status_code=204)


@router.get("/experiments/{experiment_id}/export", tags=["experiments"])
def export_experiment(experiment_id: str, format: Literal["csv", "json", "pdf"] = "csv") -> Response:
    experiment = _experiment_or_404(experiment_id)
    suffix = "_SIMULATED" if experiment["simulated"] else ""
    name = f"contextshield_{experiment_id}{suffix}"
    if format == "csv":
        return _download(exports.experiment_to_csv(experiment), "text/csv; charset=utf-8", f"{name}.csv")
    if format == "json":
        return _download(exports.experiment_to_json(experiment), "application/json", f"{name}.json")
    return _download(report.build_experiment_report(experiment), "application/pdf", f"{name}_report.pdf")


# --------------------------------------------------------------------------- analytics
@router.get("/analytics", tags=["analytics"])
def get_analytics(
    strategy: str | None = None,
    category: str | None = None,
    provider: str | None = None,
    simulated: bool | None = None,
    date_from: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    date_to: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
) -> dict:
    return analytics.build_analytics(strategy=strategy, category=category, provider=provider,
                                     simulated=simulated, date_from=date_from, date_to=date_to)
