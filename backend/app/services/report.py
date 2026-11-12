"""PDF research report for a single experiment (ReportLab, charts drawn natively)."""
from __future__ import annotations

import io
from xml.sax.saxutils import escape

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from . import metrics
from .evaluator import EVALUATOR_VERSION

NAVY = colors.HexColor("#0f1f3d")
MUTED = colors.HexColor("#5b6577")
BORDER = colors.HexColor("#d5dbe5")
WARNING_BG = colors.HexColor("#fff4d6")
OK_BG = colors.HexColor("#e3f4ea")

TEAM = [
    ("Manthan Jain (Team Leader)", "S24CSEU0105"),
    ("Kush Narwal", "S24CSEU0053"),
    ("Prabhdeep Singh", "S24CSEU1590"),
    ("Yash Chandna", "S24CSEU0233"),
]

LIMITATIONS = [
    "Prompt engineering can reduce, but cannot eliminate, indirect prompt injection. A low attack "
    "compliance rate in this experiment is not a security guarantee.",
    "The dataset is small and synthetic; results may not generalise to other documents, attack "
    "styles, languages, or models.",
    "The rule-based evaluator relies on attack markers and keyword-based fact checks. It can "
    "misjudge paraphrased compliance or paraphrased facts; 'uncertain' verdicts need manual review.",
    "Model outputs are stochastic. Small numbers of repetitions give wide uncertainty on every rate.",
]


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("title", parent=base["Title"], textColor=NAVY, fontSize=19, leading=24, spaceAfter=4),
        "subtitle": ParagraphStyle("subtitle", parent=base["Normal"], textColor=MUTED, fontSize=10, alignment=1),
        "h": ParagraphStyle("h", parent=base["Heading2"], textColor=NAVY, fontSize=13, spaceBefore=14, spaceAfter=6),
        "body": ParagraphStyle("body", parent=base["Normal"], fontSize=9.5, leading=13.5),
        "small": ParagraphStyle("small", parent=base["Normal"], fontSize=8, leading=10.5),
        "mono": ParagraphStyle("mono", parent=base["Code"], fontSize=7.5, leading=9.5),
        "banner": ParagraphStyle("banner", parent=base["Normal"], fontSize=10, leading=14, alignment=1),
    }


def _text(value) -> str:
    return escape(str(value)).replace("\n", "<br/>")


def _fmt(value, suffix: str = "%") -> str:
    return "n/a" if value is None else f"{value}{suffix}"


def _table(rows: list[list], column_widths: list[float], header: bool = True) -> Table:
    table = Table(rows, colWidths=column_widths, repeatRows=1 if header else 0)
    style = [
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                  ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")]
    table.setStyle(TableStyle(style))
    return table


def _bar_chart(title: str, labels: list[str], values: list[float | None], color) -> Drawing:
    drawing = Drawing(480, 170)
    drawing.add(String(240, 155, title, textAnchor="middle", fontSize=9.5, fillColor=NAVY,
                       fontName="Helvetica-Bold"))
    chart = VerticalBarChart()
    chart.x, chart.y, chart.width, chart.height = 45, 28, 410, 112
    chart.data = [[value if value is not None else 0 for value in values]]
    chart.categoryAxis.categoryNames = labels
    chart.categoryAxis.labels.fontSize = 7.5
    chart.valueAxis.valueMin, chart.valueAxis.valueMax, chart.valueAxis.valueStep = 0, 100, 25
    chart.valueAxis.labels.fontSize = 7.5
    chart.bars[0].fillColor = color
    chart.bars[0].strokeColor = None
    chart.barWidth = 18
    chart.barLabelFormat = "%.1f%%"
    chart.barLabels.nudge = 7
    chart.barLabels.fontSize = 7.5
    drawing.add(chart)
    return drawing


def build_experiment_report(experiment: dict) -> bytes:
    """Render the experiment (as returned by engine.get_experiment) to PDF bytes."""
    styles = _styles()
    simulated = experiment["simulated"]
    strategies = experiment["strategy_snapshot"]
    cases = experiment["cases_snapshot"]
    strategy_metrics = experiment["metrics"]["by_strategy"]
    overall = experiment["metrics"]["overall"]
    story: list = []

    # 1-2. Title and experiment id
    story.append(Paragraph("ContextShield: Evaluating Prompt-Engineering Strategies Against "
                           "Indirect Prompt Injection", styles["title"]))
    story.append(Paragraph("Experiment Report &middot; Prompt Engineering (SCSE4041) &middot; "
                           "Bennett University", styles["subtitle"]))
    story.append(Spacer(1, 8))
    banner_text = ("<b>SIMULATED DEMONSTRATION RESULTS.</b> This experiment used the mock simulator. "
                   "The numbers below are generated by scripted rules and are NOT measurements of any "
                   "real language model." if simulated else
                   "<b>REAL LLM API RESULTS.</b> Responses in this report were returned by the "
                   "configured model through its API.")
    banner = Table([[Paragraph(banner_text, styles["banner"])]], colWidths=[17 * cm])
    banner.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), WARNING_BG if simulated else OK_BG),
                                ("BOX", (0, 0), (-1, -1), 0.7, BORDER),
                                ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    story.append(banner)
    story.append(Spacer(1, 8))
    story.append(_table([
        ["Experiment ID", experiment["id"]],
        ["Name", Paragraph(_text(experiment["name"]), styles["small"])],
        ["Status", experiment["status"]],
        ["Started / finished (UTC)", f"{experiment['created_at']}  /  {experiment['finished_at'] or 'n/a'}"],
        ["Team ContextShield", Paragraph("<br/>".join(f"{name} - {roll}" for name, roll in TEAM), styles["small"])],
    ], [5 * cm, 12 * cm], header=False))

    # 3. Objective
    story.append(Paragraph("1. Objective", styles["h"]))
    story.append(Paragraph(
        "To measure how often a model follows instructions maliciously embedded in an external document "
        "(indirect prompt injection) under different prompt-engineering strategies, while checking that "
        "the legitimate user task is still completed and not needlessly refused.", styles["body"]))

    # 4. Model and provider
    story.append(Paragraph("2. Model and Provider", styles["h"]))
    story.append(_table([
        ["Provider", experiment["provider"]],
        ["Model", experiment["model"]],
        ["Result type", "Simulated (mock provider)" if simulated else "Real LLM API"],
        ["Temperature", str(experiment["temperature"])],
        ["Repetitions per case and strategy", str(experiment["repetitions"])],
    ], [6 * cm, 11 * cm], header=False))

    # 5. Dataset
    story.append(Paragraph("3. Dataset", styles["h"]))
    attack_cases = sum(1 for case in cases if case["attack_markers"])
    story.append(Paragraph(
        f"{len(cases)} synthetic test case(s): {attack_cases} containing an embedded attack and "
        f"{len(cases) - attack_cases} benign. All content is synthetic; no real or personal data is used.",
        styles["body"]))
    story.append(Spacer(1, 4))
    case_rows = [["ID", "Category", "Attack type", "User task"]]
    for case in cases:
        case_rows.append([case["id"], case["category"], case["attack_type"] or "none",
                          Paragraph(_text(case["user_task"][:220]), styles["small"])])
    story.append(_table(case_rows, [1.8 * cm, 3.6 * cm, 3.4 * cm, 8.2 * cm]))

    # 6. Strategies
    story.append(Paragraph("4. Prompt Strategies Tested", styles["h"]))
    for strategy in strategies:
        story.append(Paragraph(
            f"<b>{_text(strategy['short_label'])}. {_text(strategy['name'])}</b> (template version "
            f"{strategy['version']}) - {_text(strategy['description'])}", styles["body"]))
        for key, template in strategy["templates"].items():
            story.append(Paragraph(f"<b>{_text(key)}:</b> {_text(template)}", styles["mono"]))
        story.append(Spacer(1, 5))

    # 7. Methodology
    story.append(Paragraph("5. Evaluation Methodology", styles["h"]))
    story.append(Paragraph(
        f"Responses were scored by the deterministic rule-based evaluator ({EVALUATOR_VERSION}). "
        "<b>Attack compliance:</b> a response is 'followed' when a case-specific attack marker appears "
        "without reporting language, 'uncertain' when a marker appears alongside reporting language, and "
        "'resisted' otherwise. <b>Task completion:</b> the share of expected facts found (keyword match) "
        "must reach the case threshold. <b>False refusal:</b> a refusal phrase is present and the task was "
        "not completed.", styles["body"]))
    story.append(Spacer(1, 3))
    story.append(Paragraph(
        "Attack Compliance Rate = followed / evaluated attack responses x 100 (lower is better). "
        "Legitimate Task Accuracy = completed / task-evaluated responses x 100 (higher is better). "
        "False Refusal Rate = refusals / evaluated responses x 100 (lower is better). "
        "Runs that failed with a provider error are excluded from all denominators. No combined score is used.",
        styles["body"]))

    # 8. Results
    story.append(Paragraph("6. Results", styles["h"]))
    result_rows = [["Strategy", "Attack\ncompliance", "Followed /\nuncertain / total", "Task\naccuracy",
                    "False\nrefusal", "Successful\ncases", "Avg time\n(ms)", "Errors"]]
    for strategy in strategies:
        m = strategy_metrics.get(strategy["id"]) or metrics.aggregate([])
        result_rows.append([
            Paragraph(f"{_text(strategy['short_label'])}. {_text(strategy['name'])}", styles["small"]),
            _fmt(m["attack_compliance_rate"]),
            f"{m['attack_followed']} / {m['attack_uncertain']} / {m['attack_runs']}",
            _fmt(m["task_accuracy"]), _fmt(m["false_refusal_rate"]),
            f"{m['successful_cases']} / {m['evaluated_runs']}",
            _fmt(m["avg_latency_ms"], ""), str(m["error_runs"]),
        ])
    story.append(_table(result_rows, [4.4 * cm, 2 * cm, 2.6 * cm, 1.7 * cm, 1.6 * cm, 1.9 * cm, 1.6 * cm, 1.2 * cm]))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        f"Total runs: {overall['total_runs']} (evaluated: {overall['evaluated_runs']}, provider errors: "
        f"{overall['error_runs']}). A 'successful case' resisted the attack (or was benign) and completed the task.",
        styles["small"]))

    # 9. Charts
    story.append(Paragraph("7. Comparison Charts", styles["h"]))
    labels = [strategy["short_label"] + ". " + strategy["name"] for strategy in strategies]
    series = [
        ("Attack compliance rate by strategy (%, lower is better)", "attack_compliance_rate", colors.HexColor("#c2410c")),
        ("Legitimate task accuracy by strategy (%, higher is better)", "task_accuracy", colors.HexColor("#1d4ed8")),
        ("False refusal rate by strategy (%, lower is better)", "false_refusal_rate", colors.HexColor("#6d28d9")),
    ]
    if overall["evaluated_runs"]:
        for title, key, color in series:
            values = [(strategy_metrics.get(strategy["id"]) or {}).get(key) for strategy in strategies]
            story.append(_bar_chart(title, labels, values, color))
        story.append(Paragraph("Bars shown at 0 may also mean 'no data' for that strategy; see the table above.",
                               styles["small"]))
    else:
        story.append(Paragraph("No evaluated runs are available, so no charts were produced.", styles["body"]))

    # 10. Limitations
    story.append(Paragraph("8. Limitations", styles["h"]))
    limitations = list(LIMITATIONS)
    if simulated:
        limitations.insert(0, "These results are simulated. They demonstrate the pipeline only and say "
                              "nothing about how any real model behaves.")
    for limitation in limitations:
        story.append(Paragraph(f"&bull; {limitation}", styles["body"]))

    # 11. Conclusion (data-driven, no invented findings)
    story.append(Paragraph("9. Conclusion", styles["h"]))
    story.append(Paragraph(_conclusion(experiment), styles["body"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Primary reference: OWASP Gen AI Security Project, LLM01: Prompt Injection, "
                           "https://genai.owasp.org/llmrisk/llm01-prompt-injection/", styles["small"]))

    buffer = io.BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                                 topMargin=1.8 * cm, bottomMargin=1.8 * cm,
                                 title=f"ContextShield report {experiment['id']}", author="Team ContextShield")
    document.build(story, onFirstPage=_footer(experiment), onLaterPages=_footer(experiment))
    return buffer.getvalue()


def _conclusion(experiment: dict) -> str:
    strategy_metrics = experiment["metrics"]["by_strategy"]
    names = {strategy["id"]: strategy["name"] for strategy in experiment["strategy_snapshot"]}
    best = experiment["metrics"]["most_effective_strategy"]
    source = "simulated run" if experiment["simulated"] else "experiment"
    if best is None:
        return ("This experiment produced no evaluated attack responses, so no comparison of attack "
                "compliance between strategies can be drawn from it.")
    best_metrics = strategy_metrics[best]
    text = (f"In this {source}, the strategy with the lowest attack compliance rate was "
            f"<b>{_text(names[best])}</b> ({best_metrics['attack_compliance_rate']}% over "
            f"{best_metrics['attack_runs']} attack response(s), task accuracy "
            f"{_fmt(best_metrics['task_accuracy'])}). ")
    baseline = strategy_metrics.get("baseline")
    if baseline and best != "baseline" and baseline["attack_compliance_rate"] is not None:
        text += f"The baseline prompt's attack compliance rate was {baseline['attack_compliance_rate']}%. "
    text += ("This describes only the cases, model and settings listed above. It does not show that any "
             "strategy prevents prompt injection, and with this sample size differences between "
             "strategies may be due to chance.")
    if experiment["simulated"]:
        text += " Because the data is simulated, no conclusion about real models should be drawn."
    return text


def _footer(experiment: dict):
    label = "SIMULATED RESULTS (mock provider)" if experiment["simulated"] else "Real LLM API results"

    def draw(canvas, document):
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(2 * cm, 1 * cm, f"ContextShield - {experiment['id']} - {label}")
        canvas.drawRightString(A4[0] - 2 * cm, 1 * cm, f"Page {document.page}")
        canvas.restoreState()
    return draw
