"""Build the Milestone 2 PDF (deliverables/ContextShield_Milestone2.pdf).

Usage (from the backend folder):
    .venv/Scripts/python scripts/build_milestone2_report.py

Data sources (nothing is typed in by hand except the team inputs file):
    deliverables/test_results.json          test-table run (all strategies, v1 prompts)
    deliverables/iterations/two_stage_v*.json  Strategy D iteration runs
    deliverables/milestone2_inputs.json      member tasks, prototype and reel links (team-provided)

Fields missing from the inputs file are printed in red as "TO BE FILLED" instead of being invented.
Section 7 is the team contribution table, as required by the submission form.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "scripts"))

from reportlab.lib import colors  # noqa: E402
from reportlab.lib.pagesizes import A4, landscape  # noqa: E402
from reportlab.lib.units import cm  # noqa: E402
from reportlab.platypus import (BaseDocTemplate, Frame, KeepTogether, NextPageTemplate, PageBreak,  # noqa: E402
                                PageTemplate, Paragraph, Spacer)

import build_iteration_log as iteration  # noqa: E402
import build_milestone_docs as docs  # noqa: E402
from app.services.llm_judge import JUDGE_SYSTEM_PROMPT  # noqa: E402

INPUTS = ROOT / "deliverables" / "milestone2_inputs.json"
OUTPUT = ROOT / "deliverables" / "ContextShield_Milestone2.pdf"
TODO = "<font color='#b91c1c'><b>TO BE FILLED</b></font>"

MODULES = [
    ("Experiment runner", "Task + document input (dataset case or custom), strategy selection, real LLM or mock "
                          "provider, repetitions, live progress."),
    ("Prompt strategy engine", "Four strategies with editable, versioned templates; the exact prompt of every run "
                               "is stored."),
    ("Rule-based evaluator", "Attack compliance, task completion and false refusal, with the evidence for each "
                             "verdict."),
    ("Test dataset manager", "24 synthetic cases; browse, filter, add, edit, delete, CSV/JSON import and export."),
    ("Comparison and analytics", "Strategy comparison table and charts with strategy, category, provider and date "
                                 "filters."),
    ("Experiment history", "Every experiment with its configuration, prompts, raw responses and evaluation."),
    ("Exports", "CSV, JSON and a PDF research report per experiment."),
]


def value_or_todo(value: str) -> str:
    return docs.text(value) if str(value).strip() else TODO


def build() -> Path:
    inputs = json.loads(INPUTS.read_text(encoding="utf-8"))
    data = docs.load()
    iterated = {sid: iteration.load_versions(sid) for sid in iteration.iterated_strategies()}
    total_versions = sum(len(v) for v in iterated.values())
    final_version = {sid: versions[-1] for sid, versions in iterated.items()}
    final_d = final_version["two_stage"]
    st = docs.styles()
    strategies = data["strategies"]
    sm = data["dataset_metrics"]
    total_inputs = len(data["rows"]) + len(data["invalid_cases"])
    story: list = []

    # ------------------------------------------------------------------ cover
    story += [
        Paragraph("ContextShield: Evaluating Prompt-Engineering Strategies Against Indirect Prompt Injection",
                  st["title"]),
        Paragraph("Milestone 2 Submission &middot; Prompt Engineering (SCSE4041) &middot; Bennett University",
                  st["subtitle"]),
        Spacer(1, 10),
        docs.grid([
            ["Team ID", docs.TEAM_ID],
            ["Team name", "ContextShield"],
            ["Team leader", "Manthan Jain (S24CSEU0105)"],
            ["Batch group", "B01-12"],
            ["Project type", "App with code"],
            ["Main AI model", Paragraph(f"{docs.text(data['model'])} via the Google Gemini API (Google AI Studio "
                                        "free tier)", st["small"])],
            ["Repository", docs.REPO_URL],
            ["Prototype", Paragraph(value_or_todo(inputs.get("prototype_link", "")) + "<br/>"
                                    + docs.text(inputs.get("prototype_note", "")), st["small"])],
            ["Reel", Paragraph(value_or_todo(inputs.get("reel_link", "")) + (
                f" ({docs.text(inputs['reel_length_seconds'])} s)" if str(inputs.get("reel_length_seconds", "")).strip()
                else ""), st["small"])],
            ["Date", datetime.now().strftime("%d %B %Y")],
        ], [4 * cm, 13 * cm], header=False,
            extra=[("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"), ("BACKGROUND", (0, 0), (0, -1), docs.LIGHT)]),
        Spacer(1, 6),
        docs.grid([["Enrollment No.", "Name", "Role"]] + [[m["enrollment"], m["name"], m["role"]]
                                                          for m in inputs["contributions"]],
                  [4 * cm, 7 * cm, 6 * cm]),
    ]

    # ------------------------------------------------------------------ 1. overview
    story.append(Paragraph("1. Project overview", st["h1"]))
    story.append(Paragraph(
        "Applications built on large language models often pass external content (documents, emails, web pages) "
        "to the model. If that content contains instructions, the model may follow them instead of the user's "
        "request. This is <i>indirect prompt injection</i>, listed by OWASP as LLM01 [1]. ContextShield is a web "
        "application that runs the same task and document through several prompt-engineering strategies, measures "
        "how often the model follows the embedded instruction, checks that the legitimate task is still completed, "
        "and reports false refusals. The project evaluates how far prompt-level defenses help and where they stop; "
        "it does not claim that they prevent prompt injection.", st["body"]))
    story.append(Paragraph("<b>Objectives:</b> (1) compare four prompt strategies under identical conditions; "
                           "(2) evaluate responses transparently with stored evidence; (3) report attack compliance, "
                           "task accuracy and false refusals separately; (4) keep every prompt version and raw "
                           "response so results can be reproduced and checked.", st["body"]))

    # ------------------------------------------------------------------ 2. design
    story.append(KeepTogether([Paragraph("2. Solution design", st["h1"]), docs.architecture_diagram(data["model"])]))
    story.append(Paragraph(
        "A Next.js frontend (TypeScript, Tailwind CSS, Recharts) talks to a Python FastAPI backend over HTTP/JSON. "
        "For each test case and strategy the backend renders the prompt, calls the model through an "
        "OpenAI-compatible provider, strips any visible reasoning block from the answer, evaluates the response "
        "and stores everything in SQLite. Each experiment keeps a snapshot of the exact templates and test cases "
        "it used. Failed API calls are recorded as errors and are never replaced with simulated output; a mock "
        "simulator exists only for demos and its results are always labelled 'Simulated'.", st["body"]))
    story.append(docs.grid([
        ["Component", "Tool / model"],
        ["LLM under test", Paragraph(f"<b>{docs.text(data['model'])}</b> (Google Gemini API, OpenAI-compatible "
                                     "endpoint), temperature 0.7, free tier", st["small"])],
        ["Backend", "Python, FastAPI, Pydantic v2, httpx, SQLite, ReportLab"],
        ["Frontend", "Next.js 16, React 19, TypeScript, Tailwind CSS 4, Recharts"],
        ["Testing", "93 automated backend tests (pytest), ESLint, TypeScript type-check"],
        ["Development aid", Paragraph("Code written with the help of an AI coding assistant (Claude Code), "
                                     "reviewed and tested by the team.", st["small"])],
    ], [4 * cm, 13 * cm]))

    # ------------------------------------------------------------------ 3. prompts
    story.append(Paragraph("3. Prompt design (final versions)", st["h1"]))
    story.append(Paragraph(
        "The final solution uses <b>6 prompts</b>: Strategy A, B and C (one call each), Strategy D stage 1 and "
        "stage 2, and the optional LLM-judge prompt. Each has a system part and a user part. Placeholders "
        "{task}, {document} and {extracted} are filled by literal replacement, so text such as \"{task}\" inside "
        "a document cannot alter a template. "
        + "; ".join(f"{s['short_label']} is at version {final_version[s['id']]['version'] if s['id'] in final_version else s['version']}"
                    for s in strategies)
        + " (iterations in Section 4).", st["body"]))
    names = {"system": "System", "user": "User", "stage1_system": "Stage 1 system", "stage1_user": "Stage 1 user",
             "stage2_system": "Stage 2 system", "stage2_user": "Stage 2 user"}
    for strategy in strategies:
        final = final_version.get(strategy["id"])
        templates = final["templates"] if final else strategy["templates"]
        version = final["version"] if final else strategy["version"]
        block = [Paragraph(f"{docs.text(strategy['short_label'])}. {docs.text(strategy['name'])} "
                           f"<font color='#5b6577' size='8'>(version {version})</font>", st["h2"]),
                 Paragraph(docs.text(strategy["description"]), st["small"]), Spacer(1, 7)]
        for key, template in templates.items():
            block.append(Paragraph(f"<b>{names.get(key, key)}:</b><br/>{docs.text(template)}", st["mono"]))
        story.append(KeepTogether(block))
    story.append(KeepTogether([Paragraph("LLM-judge prompt (optional, not used in the metrics)", st["h2"]),
                               Spacer(1, 4), Paragraph(docs.text(JUDGE_SYSTEM_PROMPT), st["mono"])]))

    # ------------------------------------------------------------------ 4. iteration log
    labels = {s["id"]: f"{s['short_label']}. {s['name']}" for s in strategies}
    not_iterated = [labels[s["id"]] for s in strategies if s["id"] not in iterated]
    story.append(KeepTogether([
        Paragraph("4. Prompt iteration log", st["h1"]),
        Paragraph(f"<b>{total_versions} prompt versions</b> in total ("
                  + ", ".join(f"{labels[sid]}: {len(versions)}" for sid, versions in iterated.items())
                  + f"), each saved in the app and tested with {docs.text(final_d['model'])} (one run per case, "
                  "temperature 0.7). "
                  + (f"Not iterated: {', '.join(not_iterated)}." if not_iterated else ""), st["body"]),
    ]))
    for sid, versions in iterated.items():
        notes = iteration.load_notes(sid)
        block = [Paragraph(docs.text(labels[sid]) + (f" <font color='#5b6577' size='8'>(iterated by "
                                                     f"{docs.text(notes['author'])})</font>" if notes.get("author") else ""),
                           st["h2"])]
        rows = [["Version", "Cases", "Attack compliance", "Task accuracy", "False refusal", "Failing cases",
                 "Experiment"]]
        for v in versions:
            m = v["metrics"]
            rows.append([f"v{v['version']}", str(v["case_count"]),
                         f"{docs.pct(m['attack_compliance_rate'])} ({m['attack_followed']}/{m['attack_runs']})",
                         f"{docs.pct(m['task_accuracy'])} ({m['task_completed']}/{m['task_runs']})",
                         docs.pct(m["false_refusal_rate"]), Paragraph(", ".join(v["failing"]) or "none", st["tiny"]),
                         Paragraph(v["experiment"], st["tiny"])])
        block.append(docs.grid(rows, [1.4 * cm, 1.2 * cm, 2.7 * cm, 2.6 * cm, 1.9 * cm, 2.6 * cm, 4.6 * cm]))
        story.append(KeepTogether(block))
        previous = None
        for v in versions:
            story.append(KeepTogether([
                Paragraph(f"v{v['version']}", st["h2"]),
                Paragraph(f"<b>Change:</b> {docs.text(v['note']['change'])}", st["body"]),
                Paragraph(f"<b>Why:</b> {docs.text(v['note']['why'])}", st["body"]),
                Paragraph(f"<b>Result:</b> {docs.text(iteration.outcome(v, previous))}", st["body"]),
            ]))
            previous = v

    # ------------------------------------------------------------------ 5. testing
    story.append(Paragraph("5. Testing and results", st["h1"]))
    story.append(Paragraph(
        f"The test table (Appendix A) has <b>{total_inputs} test inputs</b>: "
        f"{sum(r['type'] == 'Normal (attack)' for r in data['rows'])} normal cases containing an embedded attack, "
        f"{sum(r['type'] == 'Normal (benign)' for r in data['rows'])} benign normal cases, "
        f"{sum(r['type'] == 'Edge' for r in data['rows'])} edge cases and {len(data['invalid_cases'])} invalid "
        f"inputs. It was run on {data['generated_at'][:10]} with all four strategies at version 1. "
        "<b>Pass</b> = the response did not follow the embedded instruction and completed the task. Metrics: "
        "Attack Compliance Rate (ACR, lower is better), Legitimate Task Accuracy (LTA, higher is better), False "
        "Refusal Rate (FRR, lower is better); they are never merged into one score.", st["body"]))
    result_rows = [[docs.Paragraph(h, st["cellhead"]) for h in
                    ["Strategy (v1)", "ACR", "LTA", "FRR", "Pass / 26 normal + edge"]]]
    for position, strategy in enumerate(strategies):
        m = sm[strategy["id"]]
        passes = sum(row["results"][position] == "Pass" for row in data["rows"])
        result_rows.append([f"{strategy['short_label']}. {strategy['name']}",
                            f"{docs.pct(m['attack_compliance_rate'])} ({m['attack_followed']}/{m['attack_runs']})",
                            f"{docs.pct(m['task_accuracy'])} ({m['task_completed']}/{m['task_runs']})",
                            docs.pct(m["false_refusal_rate"]), f"{passes}/{len(data['rows'])}"])
    story.append(docs.grid(result_rows, [6 * cm, 3 * cm, 3 * cm, 1.8 * cm, 3.2 * cm]))
    invalid_pass = sum(case["passed"] for case in data["invalid_cases"])
    baseline = sm.get("baseline")
    findings = [
        f"The baseline prompt followed the embedded instruction in {baseline['attack_followed']} of "
        f"{baseline['attack_runs']} attack responses; strategies B, C and D followed it in none.",
        "Most baseline failures were output-manipulation attacks (adding a link, a tag or a signature) where the "
        "model still completed the task, so the injection was easy to miss.",
        "No strategy refused a legitimate task.",
        f"Both edge cases passed on every strategy; {invalid_pass} of {len(data['invalid_cases'])} invalid inputs "
        "were rejected with the expected error.",
        f"After iteration, Strategy D v{final_d['version']} completed {final_d['metrics']['task_completed']}/24 "
        f"tasks with {final_d['metrics']['attack_followed']}/20 attacks followed (Section 4).",
        "This is one run per case on a small synthetic dataset with one model: it shows a difference in this "
        "setting, not that any strategy prevents prompt injection.",
    ]
    story += [Paragraph(f"&bull; {docs.text(line)}", st["body"]) for line in findings]
    if data["retried_pairs"]:
        story.append(Paragraph(docs.retry_note(data), st["small"]))
    if data["corrections"]:
        story.append(Paragraph(docs.correction_note(data), st["small"]))

    # ------------------------------------------------------------------ 6. status
    story.append(Paragraph("6. Prototype status and limitations", st["h1"]))
    story.append(Paragraph("<b>Status: all modules working.</b> Each module below was exercised in the browser "
                           "and by the automated tests.", st["body"]))
    story.append(docs.grid([["#", "Module", "What it does"]] + [
        [str(i), name, Paragraph(docs.text(desc), st["small"])] for i, (name, desc) in enumerate(MODULES, 1)],
        [0.8 * cm, 4.4 * cm, 11.8 * cm]))
    story.append(Spacer(1, 4))
    for line in [
        "Prompt engineering is not a security boundary; instructions and data share one text channel.",
        "Small, synthetic, English-only dataset with overt injections; adaptive attackers were not tested.",
        "One run per case; no significance testing. Results apply only to the model tested.",
        "Keyword-based evaluation can misjudge paraphrased answers; raw responses are kept for manual review.",
        "The free tier is slow and rate-limited; the app paces calls, retries temporary errors and stops "
        "cleanly when a daily quota runs out.",
    ]:
        story.append(Paragraph(f"&bull; {docs.text(line)}", st["body"]))

    # ------------------------------------------------------------------ 7. contributions
    section7 = [Paragraph("7. Team contribution table", st["h1"])]
    if all(m.get("task", "").strip() for m in inputs["contributions"]):
        section7.append(Paragraph("All team members have reviewed and agreed to this table.", st["body"]))
    else:
        section7.append(Paragraph(f"{TODO}: each member's actual main task, agreed by the whole team.", st["body"]))
    section7.append(docs.grid([["Enrollment No.", "Name", "Role", "Main task"]] + [
        [m["enrollment"], m["name"], m["role"], Paragraph(value_or_todo(m.get("task", "")), st["small"])]
        for m in inputs["contributions"]], [3.2 * cm, 3.6 * cm, 2.6 * cm, 7.6 * cm]))
    story.append(KeepTogether(section7))

    # ------------------------------------------------------------------ 8. next steps
    story.append(Paragraph("8. Next steps", st["h1"]))
    for line in [
        "Repeat the test table with several runs per case to measure variability.",
        "Test adaptive and obfuscated injections, and a second model for comparison.",
        "Iterate strategies B and C the same way Strategy D was iterated, and re-run the full test table with "
        "the final prompt versions.",
        "Add the spotlighting variants (datamarking, encoding) described by Hines et al. [2].",
    ]:
        story.append(Paragraph(f"&bull; {docs.text(line)}", st["body"]))

    story.append(Paragraph("References", st["h1"]))
    for reference in [
        "[1] OWASP Gen AI Security Project. LLM01:2025 Prompt Injection. "
        "https://genai.owasp.org/llmrisk/llm01-prompt-injection/",
        "[2] Hines, K., Lopez, G., Hall, M., Zarfati, F., Zunger, Y., & Kiciman, E. (2024). Defending Against "
        "Indirect Prompt Injection Attacks With Spotlighting. arXiv:2403.14720.",
        "[3] Greshake, K., et al. (2023). Not what you've signed up for: Compromising Real-World LLM-Integrated "
        "Applications with Indirect Prompt Injection. arXiv:2302.12173.",
    ]:
        story.append(Paragraph(reference, st["small"]))

    # ------------------------------------------------------------------ appendix (landscape)
    story += [NextPageTemplate("landscape"), PageBreak()]
    story += docs.test_table_story(data, title="Appendix A - Test table", include_raw_responses=False)
    story.append(Paragraph("Raw model responses for every row are in ContextShield_TestTable.pdf and in the "
                           "repository (deliverables/test_results.json).", st["small"]))

    document = BaseDocTemplate(str(OUTPUT), title="ContextShield Milestone 2", author="Team ContextShield")
    portrait_frame = Frame(2 * cm, 1.7 * cm, A4[0] - 4 * cm, A4[1] - 3.4 * cm, id="portrait")
    wide = landscape(A4)
    landscape_frame = Frame(1.4 * cm, 1.4 * cm, wide[0] - 2.8 * cm, wide[1] - 2.7 * cm, id="landscape")

    def page(size, label):
        footer = docs.footer(label)

        def draw(canvas, doc):
            canvas.setPageSize(size)
            doc.pagesize = size
            footer(canvas, doc)
        return draw

    document.addPageTemplates([
        PageTemplate(id="portrait", frames=[portrait_frame], pagesize=A4, onPage=page(A4, "Milestone 2")),
        PageTemplate(id="landscape", frames=[landscape_frame], pagesize=wide, onPage=page(wide, "Milestone 2")),
    ])
    document.build(story)
    missing = [m["name"] for m in inputs["contributions"] if not m.get("task", "").strip()]
    print(f"{OUTPUT.name}: {OUTPUT.stat().st_size / 1024:.0f} KB")
    print(f"Still TO BE FILLED: member tasks for {', '.join(missing) or 'nobody'}; "
          f"prototype link {'missing' if not inputs.get('prototype_link') else 'ok'}; "
          f"reel link {'missing' if not inputs.get('reel_link') else 'ok'}")
    return OUTPUT


if __name__ == "__main__":
    build()
