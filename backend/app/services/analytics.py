"""Cross-experiment analytics computed from stored runs, with filters."""
from __future__ import annotations

from .. import database as db
from . import metrics


def query_runs(strategy: str | None = None, category: str | None = None, provider: str | None = None,
               simulated: bool | None = None, date_from: str | None = None,
               date_to: str | None = None) -> list[dict]:
    """Return run rows joined with experiment metadata, filtered. Dates are YYYY-MM-DD (UTC)."""
    clauses, parameters = [], []
    if strategy:
        clauses.append("r.strategy_id = ?"); parameters.append(strategy)
    if category:
        clauses.append("r.category = ?"); parameters.append(category)
    if provider:
        clauses.append("e.provider = ?"); parameters.append(provider)
    if simulated is not None:
        clauses.append("e.simulated = ?"); parameters.append(int(simulated))
    if date_from:
        clauses.append("substr(e.created_at, 1, 10) >= ?"); parameters.append(date_from)
    if date_to:
        clauses.append("substr(e.created_at, 1, 10) <= ?"); parameters.append(date_to)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    query = (
        "SELECT r.experiment_id, r.test_case_id, r.category, r.strategy_id, r.status, r.attack_status, "
        "r.task_status, r.refused, r.latency_ms, e.created_at AS experiment_created_at, "
        "e.name AS experiment_name, e.provider, e.model, e.simulated "
        f"FROM runs r JOIN experiments e ON e.id = r.experiment_id {where} ORDER BY r.id"
    )
    with db.connect() as connection:
        return [dict(row) for row in connection.execute(query, parameters).fetchall()]


def build_analytics(**filters) -> dict:
    runs = query_runs(**filters)
    with db.connect() as connection:
        real_runs, simulated_runs = (connection.execute(
            "SELECT COUNT(*) FROM runs r JOIN experiments e ON e.id = r.experiment_id WHERE e.simulated = ?",
            (flag,)).fetchone()[0] for flag in (0, 1))
        test_case_count = connection.execute("SELECT COUNT(*) FROM test_cases").fetchone()[0]
        strategies = [dict(row) for row in connection.execute(
            "SELECT id, name, short_label FROM strategies ORDER BY sort_order").fetchall()]
        providers = [row[0] for row in connection.execute("SELECT DISTINCT provider FROM experiments").fetchall()]

    strategy_metrics = metrics.by_strategy(runs)
    timeline: dict[str, dict] = {}
    for run in runs:
        entry = timeline.setdefault(run["experiment_id"], {
            "experiment_id": run["experiment_id"], "name": run["experiment_name"],
            "created_at": run["experiment_created_at"], "simulated": bool(run["simulated"]), "runs": []})
        entry["runs"].append(run)
    timeline_points = []
    for entry in sorted(timeline.values(), key=lambda item: item["created_at"]):
        entry_runs = entry.pop("runs")
        timeline_points.append({**entry, "metrics": metrics.aggregate(entry_runs),
                                "by_strategy": metrics.by_strategy(entry_runs)})

    return {
        "available": {"real_runs": real_runs, "simulated_runs": simulated_runs},
        "test_case_count": test_case_count,
        "experiment_count": len(timeline_points),
        "strategies": strategies,
        "providers": providers,
        "overall": metrics.aggregate(runs),
        "by_strategy": strategy_metrics,
        "by_category": metrics.by_category(runs),
        "by_category_and_strategy": metrics.by_strategy_and_category(runs),
        "most_effective_strategy": metrics.most_effective_strategy(strategy_metrics),
        "most_effective_rule": metrics.MOST_EFFECTIVE_RULE,
        "timeline": timeline_points,
    }
