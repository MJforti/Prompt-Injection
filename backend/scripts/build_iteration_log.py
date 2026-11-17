"""Build the prompt iteration log for every iterated strategy.

Usage (from the backend folder), after run_prompt_iteration.py has saved each version:
    .venv/Scripts/python scripts/build_iteration_log.py

Sources, per strategy <id>:
    deliverables/iterations/<id>_notes.json   what changed in each version and why, written by
                                              the person who made the change (required)
    deliverables/iterations/<id>_v<N>.json    the test run of version N
    deliverables/test_results.json            used as version 1 when there is no <id>_v1.json

Writes docs/ITERATION_LOG.md and deliverables/ContextShield_IterationLog.pdf.
All metrics are computed from stored runs. A version without a test run, or without notes, is
reported as such instead of being filled in.
"""
from __future__ import annotations

import difflib
import json
import statistics
import sys
from pathlib import Path
from xml.sax.saxutils import escape

BACKEND = Path(__file__).resolve().parent.parent
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "scripts"))

from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.units import cm  # noqa: E402
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer  # noqa: E402

import build_milestone_docs as docs  # noqa: E402
from app.services import metrics  # noqa: E402

ITERATIONS = ROOT / "deliverables" / "iterations"
MISSING = "(not recorded)"


def iterated_strategies() -> list[str]:
    """Strategies that have a notes file, in a stable order (Strategy D first, as it was iterated first)."""
    order = ["two_stage", "trust_boundaries", "instruction_separation", "baseline"]
    found = [path.name[: -len("_notes.json")] for path in ITERATIONS.glob("*_notes.json")]
    return sorted(found, key=lambda sid: order.index(sid) if sid in order else len(order))


def load_notes(strategy_id: str) -> dict:
    path = ITERATIONS / f"{strategy_id}_notes.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"versions": {}}


def load_versions(strategy_id: str = "two_stage") -> list[dict]:
    test_table = docs.load()  # applies retries and the TC-004 keyword correction
    files = sorted(ITERATIONS.glob(f"{strategy_id}_v*.json"), key=lambda p: int(p.stem.rsplit("v", 1)[1]))
    versions = []
    if not any(int(p.stem.rsplit("v", 1)[1]) == 1 for p in files):
        strategy = next(s for s in test_table["strategies"] if s["id"] == strategy_id)
        versions.append({
            "version": 1, "templates": strategy["templates"], "name": strategy["name"],
            "runs": [r for r in test_table["dataset_experiment"]["runs"] if r["strategy_id"] == strategy_id],
            "cases": test_table["dataset_experiment"]["cases_snapshot"],
            "experiment": test_table["dataset_experiment"]["id"], "date": test_table["generated_at"][:10],
            "model": test_table["model"]})
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        versions.append({
            "version": data["strategy"]["version"], "templates": data["strategy"]["templates"],
            "name": data["strategy"]["name"], "runs": data["runs"],
            "cases": data.get("cases") or test_table["dataset_experiment"]["cases_snapshot"],
            "experiment": data["experiment_id"], "date": data["generated_at"][:10], "model": data["model"]})
    notes = load_notes(strategy_id)
    for v in versions:
        cases = {case["id"]: case for case in v["cases"]}
        v["metrics"] = metrics.aggregate(v["runs"])
        v["case_count"] = len({run["test_case_id"] for run in v["runs"]})
        v["failing"] = sorted(run["test_case_id"] for run in v["runs"] if docs.run_result(run) != "Pass")
        v["leaks"] = None
        if strategy_id == "two_stage":
            v["leaks"] = sum(1 for run in v["runs"] if any(
                marker.lower() in (run.get("stage1_output") or "").lower()
                for marker in cases.get(run["test_case_id"], {}).get("attack_markers", [])))
        latencies = [r["latency_ms"] for r in v["runs"] if r["latency_ms"]]
        v["median_latency_s"] = round(statistics.median(latencies) / 1000, 1) if latencies else None
        highlight = notes.get("highlight_case")
        v["highlight"] = next((run.get("response") or "" for run in v["runs"]
                               if run["test_case_id"] == highlight), "") if highlight else ""
        v["note"] = notes["versions"].get(str(v["version"]), {"change": MISSING, "why": MISSING})
    return versions


def template_diff(old: dict, new: dict) -> list[str]:
    lines = []
    for key in new:
        before, after = old.get(key, ""), new[key]
        if before == after:
            continue
        if after.startswith(before.rstrip()):
            lines.append(f"{key}: + \"{after[len(before.rstrip()):].strip()}\"")
        else:
            changed = [w[2:] for w in difflib.ndiff(before.split(), after.split()) if w.startswith("+ ")]
            lines.append(f"{key}: changed words: {' '.join(changed)}")
    return lines


def outcome(v: dict, previous: dict | None) -> str:
    m = v["metrics"]
    text = (f"ACR {docs.pct(m['attack_compliance_rate'])} ({m['attack_followed']}/{m['attack_runs']}), "
            f"LTA {docs.pct(m['task_accuracy'])} ({m['task_completed']}/{m['task_runs']}), "
            f"FRR {docs.pct(m['false_refusal_rate'])} on {v['case_count']} cases")
    if v["leaks"] is not None:
        text += f", injected marker in stage-1 output: {v['leaks']}/{v['case_count']}"
    text += f". Failing cases: {', '.join(v['failing']) or 'none'}."
    if previous:
        before, after = set(previous["failing"]), set(v["failing"])
        fixed, broke = sorted(before - after), sorted(after - before)
        text += (f" Compared with v{previous['version']}: fixed {', '.join(fixed) or 'nothing'}; "
                 f"new failures {', '.join(broke) or 'none'}.")
    return text


def strategy_lines(strategy_id: str, versions: list[dict]) -> list[str]:
    notes = load_notes(strategy_id)
    final = versions[-1]
    lines = [f"## {final['name']} ({len(versions)} versions)", ""]
    if notes.get("author"):
        lines += [f"Iterated by {notes['author']}.", ""]
    lines += ["| Version | Date | Cases | ACR (lower is better) | Task accuracy | False refusals | Failing cases | "
              "Experiment |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for v in versions:
        m = v["metrics"]
        lines.append(f"| v{v['version']} | {v['date']} | {v['case_count']} | {docs.pct(m['attack_compliance_rate'])} "
                     f"({m['attack_followed']}/{m['attack_runs']}) | {docs.pct(m['task_accuracy'])} "
                     f"({m['task_completed']}/{m['task_runs']}) | {docs.pct(m['false_refusal_rate'])} | "
                     f"{', '.join(v['failing']) or 'none'} | `{v['experiment']}` |")
    lines.append("")
    previous = None
    for v in versions:
        lines += [f"### v{v['version']}", "", f"**What changed:** {v['note']['change']}", "",
                  f"**Why:** {v['note']['why']}", ""]
        if previous:
            for diff in template_diff(previous["templates"], v["templates"]):
                lines += [f"**Text added:** `{diff}`", ""]
        lines += [f"**Result:** {outcome(v, previous)}", ""]
        if v["highlight"]:
            lines += [f"**{notes['highlight_case']} answer:** {v['highlight'].strip().replace(chr(10), ' / ')}", ""]
        previous = v
    lines += [f"**Final version (v{final['version']}) templates:**", ""]
    for key, template in final["templates"].items():
        lines += [f"- `{key}`:", "", "```", template, "```", ""]
    return lines


def build() -> None:
    strategy_ids = iterated_strategies()
    all_versions = {sid: load_versions(sid) for sid in strategy_ids}
    total = sum(len(v) for v in all_versions.values())
    model = next(iter(all_versions.values()))[-1]["model"]
    lines = [
        "# Prompt Iteration Log",
        "",
        "Team ContextShield (PE-B01-03) - Prompt Engineering (SCSE4041), Bennett University.",
        "",
        f"Every version below was saved in the application (each edit creates a new version number) and tested "
        f"with **{model}** (real LLM, Google AI Studio free tier, temperature 0.7, one run per case). Metrics come "
        f"from the stored runs; experiment IDs are listed so each result can be opened in Experiment History. Runs "
        f"that failed with a temporary provider error were re-run and the retried answer is used.",
        "",
        f"**Total prompt versions in this log: {total}** ("
        + ", ".join(f"{all_versions[sid][-1]['name']}: {len(all_versions[sid])}" for sid in strategy_ids) + ").",
        "",
    ]
    for sid in strategy_ids:
        lines += strategy_lines(sid, all_versions[sid])
    lines += [
        "## Notes",
        "",
        "- One run per case at temperature 0.7, so single-case changes between versions may be chance.",
        "- Response times depend heavily on load on the free-tier Gemma 4 servers during each run, so time "
        "differences between versions are not attributed to the prompt.",
        "- Strategies not listed here were not iterated and are still at version 1, as used in the test table.",
    ]
    (ROOT / "docs" / "ITERATION_LOG.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    build_pdf(lines)
    print(f"Total versions: {total}")
    for sid in strategy_ids:
        for v in all_versions[sid]:
            print(f"  {sid} v{v['version']}: {outcome(v, None)}")


def build_pdf(lines: list[str]) -> None:
    st = docs.styles()
    story = [Paragraph("ContextShield - Prompt Iteration Log", st["title"]),
             Paragraph("Team PE-B01-03 &middot; Prompt Engineering (SCSE4041)", st["subtitle"]), Spacer(1, 8)]
    in_code = False
    code: list[str] = []
    table: list[list[str]] = []
    for line in lines[2:]:
        if line.startswith("```"):
            if in_code:
                story.append(Paragraph(escape("\n".join(code)).replace("\n", "<br/>"), st["mono"]))
                code = []
            in_code = not in_code
            continue
        if in_code:
            code.append(line)
            continue
        if line.startswith("| ---"):
            continue
        if line.startswith("| "):
            table.append([cell.strip().strip("`") for cell in line.strip("|").split("|")])
            continue
        if table:
            header, rows = table[0], table[1:]
            story.append(docs.grid([header] + [[Paragraph(escape(c), st["tiny"]) for c in row] for row in rows],
                                   [1.4 * cm, 1.8 * cm, 1.2 * cm, 2.3 * cm, 2.3 * cm, 1.6 * cm, 2.6 * cm, 3.8 * cm]))
            table = []
        if not line.strip():
            continue
        if line.startswith("## "):
            story.append(Paragraph(escape(line[3:]), st["h1"]))
        elif line.startswith("### "):
            story.append(Paragraph(escape(line[4:]), st["h2"]))
        else:
            html = escape(line).replace("**", "").replace("`", "")
            story.append(Paragraph(("&bull; " + html[2:]) if line.startswith("- ") else html, st["body"]))
    path = ROOT / "deliverables" / "ContextShield_IterationLog.pdf"
    SimpleDocTemplate(str(path), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.7 * cm,
                      bottomMargin=1.7 * cm, title="ContextShield Prompt Iteration Log",
                      author="Team ContextShield").build(story, onFirstPage=docs.footer("Iteration Log"),
                                                         onLaterPages=docs.footer("Iteration Log"))


if __name__ == "__main__":
    build()
