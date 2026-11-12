"""Prompt-strategy storage. Every edit bumps the version; nothing changes silently."""
from __future__ import annotations

from .. import database as db
from ..defaults import default_strategy
from . import prompts


def list_strategies() -> list[dict]:
    with db.connect() as connection:
        rows = [db.row_to_dict(row) for row in connection.execute(
            "SELECT * FROM strategies ORDER BY sort_order").fetchall()]
    for row in rows:
        default = default_strategy(row["id"])
        row["is_default"] = bool(default and default["templates"] == row["templates"])
    return rows


def get_strategy(strategy_id: str) -> dict | None:
    return next((strategy for strategy in list_strategies() if strategy["id"] == strategy_id), None)


def update_strategy(strategy_id: str, templates: dict[str, str], name: str | None = None,
                    description: str | None = None) -> dict | None:
    """Save edited templates. Raises prompts.TemplateError when invalid."""
    current = get_strategy(strategy_id)
    if current is None:
        return None
    prompts.validate_templates(current["kind"], templates)
    changes: dict = {}
    if templates != current["templates"]:
        changes["templates"] = templates
    if name and name != current["name"]:
        changes["name"] = name
    if description is not None and description != current["description"]:
        changes["description"] = description
    if changes:
        changes["version"] = current["version"] + 1
        changes["updated_at"] = db.utc_now()
        with db.connect() as connection:
            db.update(connection, "strategies", strategy_id, changes)
    return get_strategy(strategy_id)


def reset_strategy(strategy_id: str) -> dict | None:
    default = default_strategy(strategy_id)
    if default is None:
        return None
    return update_strategy(strategy_id, default["templates"], default["name"], default["description"])


def preview(strategy_id: str, task: str, document: str) -> dict | None:
    """Render the exact messages a strategy would send (stage 2 shows a placeholder)."""
    strategy = get_strategy(strategy_id)
    if strategy is None:
        return None
    templates = strategy["templates"]
    if strategy["kind"] == "two_stage":
        return {
            "stage1": prompts.render_stage1(templates, task, document),
            "stage2": prompts.render_stage2(templates, task, "[stage 1 output is inserted here at run time]"),
        }
    return {"main": prompts.render_single(templates, task, document)}
