"""Build the Milestone 3 presentation slides (deliverables/ContextShield_Slides.pdf), 16:9.

Usage (from the backend folder):
    .venv/Scripts/python scripts/build_slides.py

Results come from deliverables/final_comparison.json when it exists (final prompt versions on 33
cases), otherwise from the Milestone 2 test table (v1 prompts, 24 dataset cases). Iteration slides
use the iteration files; team details come from deliverables/milestone3_inputs.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "scripts"))

from reportlab.graphics import renderPDF  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.styles import ParagraphStyle  # noqa: E402
from reportlab.pdfgen import canvas as pdfcanvas  # noqa: E402
from reportlab.platypus import Paragraph  # noqa: E402

import build_final_report as report  # noqa: E402
import build_iteration_log as iteration  # noqa: E402
import build_milestone_docs as docs  # noqa: E402

OUTPUT = ROOT / "deliverables" / "ContextShield_Slides.pdf"
W, H = 960, 540
NAVY, TEAL, CORAL = docs.NAVY, report.TEAL, report.CORAL
INK = colors.HexColor("#1e293b")
MUTED = colors.HexColor("#64748b")
SOFT = colors.HexColor("#f1f5f9")
LINE = colors.HexColor("#cbd5e1")
RED_SOFT = colors.HexColor("#fee2e2")
GREEN_SOFT = colors.HexColor("#dcfce7")


def para(c, text, x, y_top, width, size=16, color=INK, bold=False, leading=None, align=0):
    style = ParagraphStyle("p", fontName="Helvetica-Bold" if bold else "Helvetica", fontSize=size,
                           leading=leading or size * 1.3, textColor=color, alignment=align)
    p = Paragraph(text, style)
    _, h = p.wrap(width, 1000)
    p.drawOn(c, x, y_top - h)
    return y_top - h


class Deck:
    def __init__(self, total_hint: int):
        self.c = pdfcanvas.Canvas(str(OUTPUT), pagesize=(W, H))
        self.c.setTitle("ContextShield - Milestone 3 presentation")
        self.c.setAuthor("Team ContextShield")
        self.n = 0
        self.top = H - 120

    def slide(self, title: str | None, kicker: str | None = None):
        if self.n:
            self.c.showPage()
        self.n += 1
        c = self.c
        c.setFillColor(colors.white)
        c.rect(0, 0, W, H, stroke=0, fill=1)
        if title:
            c.setFillColor(TEAL)
            c.rect(56, H - 62, 36, 4, stroke=0, fill=1)
            if kicker:
                c.setFont("Helvetica-Bold", 11)
                c.setFillColor(TEAL)
                c.drawString(100, H - 64, kicker.upper())
            self.top = para(c, title, 56, H - 76, W - 112, size=28, color=NAVY, bold=True) - 26
            c.setFont("Helvetica", 9)
            c.setFillColor(MUTED)
            c.drawString(56, 22, f"ContextShield  |  {docs.TEAM_ID}  |  Prompt Engineering SCSE4041")
            c.drawRightString(W - 56, 22, str(self.n))
        return c

    def save(self):
        self.c.save()


def card(c, x, y, w, h, fill=SOFT, stroke=None):
    c.setFillColor(fill)
    c.setStrokeColor(stroke or fill)
    c.roundRect(x, y, w, h, 8, stroke=1 if stroke else 0, fill=1)


def bullets(c, items, x, y_top, width, size=17, gap=12):
    y = y_top
    for item in items:
        c.setFillColor(TEAL)
        c.circle(x + 4, y - size * 0.55, 3.2, stroke=0, fill=1)
        y = para(c, item, x + 18, y, width - 18, size=size) - gap
    return y




def results_source(data: dict) -> dict:
    """Per-strategy results for the results slides: the final comparison if it exists, else Milestone 2."""
    sids = data["strategy_ids"]
    if report.FINAL.exists():
        final = report.load_final()
        hard_ids = [cid for cid in final["case_ids"] if cid.startswith("HC-")]
        out = {"label": f"Final prompt versions, {len(final['case_ids'])} cases ({len(hard_ids)} hard), "
                        f"{final['model']}, one run each.",
               "n_cases": len(final["case_ids"]), "metrics": {s: final["metrics"][s]["all"] for s in sids},
               "versions": {s: f"v{final['metrics'][s]['version']}" for s in sids}, "passes": {},
               "series": [("24 dataset cases",
                           [final["metrics"][s]["dataset"]["attack_compliance_rate"] for s in sids], TEAL),
                          (f"{len(hard_ids)} hard cases",
                           [final["metrics"][s]["hard"]["attack_compliance_rate"] for s in sids], CORAL)],
               "hard": {"ids": hard_ids, "columns": list(sids),
                        "cell": lambda col, cid: report.cell(final["by"].get((col, cid))),
                        "note": "Strategy C was tuned on these cases (v2, v3), so its score here is optimistic."}}
        for s in sids:
            runs = [final["by"][(s, cid)] for cid in final["case_ids"] if (s, cid) in final["by"]]
            out["passes"][s] = (sum(docs.run_result(r) == "Pass" for r in runs), len(runs))
        return out
    runs = data["dataset_experiment"]["runs"]
    out = {"label": f"Milestone 2 run: v1 prompts, 24 dataset cases, {data['model']}, one run each.",
           "n_cases": 24, "metrics": data["dataset_metrics"], "versions": {s: "v1" for s in sids}, "passes": {},
           "series": [("24 dataset cases (v1 prompts)",
                       [data["dataset_metrics"][s]["attack_compliance_rate"] for s in sids], TEAL)]}
    for s in sids:
        own = [r for r in runs if r["strategy_id"] == s]
        out["passes"][s] = (sum(docs.run_result(r) == "Pass" for r in own), len(own))
    versions = iteration.load_versions("trust_boundaries")
    by_version = {f"C v{v['version']}": {r["test_case_id"]: r for r in v["runs"]} for v in versions}
    hard_ids = sorted({r["test_case_id"] for v in versions for r in v["runs"] if r["test_case_id"].startswith("HC-")})
    out["hard"] = {"ids": hard_ids, "columns": list(by_version),
                   "cell": lambda col, cid: report.cell(by_version[col][cid]) if cid in by_version[col] else "not run",
                   "note": "Strategy C on the harder cases. HC-09 was added after v2; a separate check showed v2 "
                           "answered Room 101 (the old room). C was tuned on these cases, so v3's score is optimistic."}
    return out


def build() -> Path:
    inputs = json.loads(report.INPUTS.read_text(encoding="utf-8"))
    data = docs.load()
    strategies = data["strategies"]
    sids = [s["id"] for s in strategies]
    letter = {s["id"]: s["short_label"] for s in strategies}
    res = results_source(data)
    rm = res["metrics"]
    iterated = {sid: iteration.load_versions(sid) for sid in iteration.iterated_strategies()}
    total_versions = sum(len(v) for v in iterated.values())
    current = {s["id"]: f"v{iterated[s['id']][-1]['version']}" if s["id"] in iterated else "v1" for s in strategies}
    defended = [s for s in sids if s != "baseline"]
    deck = Deck(15)

    # 1. title
    c = deck.slide(None)
    c.setFillColor(NAVY)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setFillColor(TEAL)
    c.rect(56, 368, 48, 5, stroke=0, fill=1)
    para(c, "ContextShield", 56, 350, 800, size=54, color=colors.white, bold=True)
    para(c, "Evaluating prompt-engineering strategies against indirect prompt injection", 56, 278, 760, size=22,
         color=colors.HexColor("#cbd5e1"))
    para(c, f"Team {docs.TEAM_ID}  &middot;  Batch {inputs['batch']}  &middot;  Faculty: {inputs['faculty']}",
         56, 196, 840, size=14, color=colors.HexColor("#94a3b8"))
    para(c, "  &middot;  ".join(f"{m['name']} ({m['enrollment']})" for m in inputs["contributions"]),
         56, 170, 860, size=12.5, color=colors.HexColor("#94a3b8"))
    para(c, "Prompt Engineering (SCSE4041)  &middot;  Bennett University", 56, 70, 600, size=12,
         color=colors.HexColor("#64748b"))

    # 2. problem: a real baseline failure from the Milestone 2 run (TC-003)
    cases = {cc["id"]: cc for cc in data["dataset_experiment"]["cases_snapshot"]}
    example = next(r for r in data["dataset_experiment"]["runs"]
                   if r["strategy_id"] == "baseline" and r["test_case_id"] == "TC-003")
    case = cases["TC-003"]
    c = deck.slide("Your assistant reads a document. The document gives orders.", "The problem")
    card(c, 56, 140, 250, 270)
    para(c, "<b>User asks</b>", 74, 398, 220, size=13, color=MUTED)
    para(c, f"\"{docs.text(case['user_task'])}\"", 74, 370, 216, size=17)
    card(c, 322, 140, 300, 270, fill=colors.HexColor("#fff7ed"))
    para(c, "<b>Document contains</b>", 340, 398, 270, size=13, color=MUTED)
    para(c, "Minutes of the Robotics Club meeting. Budget of Rs. 40,000 approved... Registration closes on "
            "12 September.", 340, 370, 266, size=13.5)
    para(c, f"<font color='#c2410c'><b>{docs.text(case['injection_text'])}</b></font>", 340, 290, 266, size=13.5)
    card(c, 638, 140, 266, 270, fill=RED_SOFT)
    para(c, "<b>Gemma 4 answered (baseline)</b>", 656, 398, 240, size=13, color=MUTED)
    reply = docs.text(example["response"].strip()).replace("* ", "&bull; ")
    reply = reply.replace("Visit robo-deals.example for exclusive discounts.",
                          "<font color='#b91c1c'><b>Visit robo-deals.example for exclusive discounts.</b></font>")
    para(c, reply, 656, 370, 232, size=12, leading=16)
    para(c, "A real response from our test run. This is <b>indirect prompt injection</b> (OWASP LLM01): the "
            "attacker never talks to the model; the instruction rides in on content the app reads.",
         56, 118, 848, size=15, color=INK)

    # 3. question
    c = deck.slide("Do prompt-level defences actually work, and what do they cost?", "Research question")
    bullets(c, [
        "Compare <b>four prompt strategies</b> under identical conditions: same model, cases and settings.",
        "Measure three things separately: <b>attack compliance</b> (ACR, lower is better), <b>task accuracy</b> "
        "(LTA, higher is better) and <b>false refusals</b> (FRR, lower is better).",
        "Improve the prompts through <b>recorded iterations</b> driven by observed failures.",
        "Store every prompt, raw response and verdict so <b>every claim can be checked</b>.",
    ], 56, deck.top, 840, size=19, gap=16)

    # 4. architecture
    c = deck.slide("What we built", "System")
    drawing = docs.architecture_diagram(data["model"])
    drawing.scale(1.3, 1.3)
    drawing.width, drawing.height = drawing.width * 1.3, drawing.height * 1.3
    renderPDF.draw(drawing, c, 40, 120)
    bullets(c, ["Next.js + FastAPI + SQLite", f"Real LLM: {data['model']} (free tier)",
                "7 working modules", "Live at contextshield-iota.vercel.app", "95 automated tests"],
            690, 400, 230, size=15, gap=12)

    # 5. strategies
    c = deck.slide("Four strategies, from no defence to a two-step pipeline", "Strategies")
    blurbs = {
        "baseline": "Task and document pasted together. No defence: the control.",
        "instruction_separation": "Document wrapped in delimiters and labelled as data. Only the user's task "
                                  "counts as an instruction.",
        "trust_boundaries": "Explicit trust order: system > user > document. Lists what document text may "
                            "never do.",
        "two_stage": "Call 1 extracts plain facts from the document. Call 2 answers from the facts only.",
    }
    for i, s in enumerate(strategies):
        x = 56 + i * 218
        card(c, x, 130, 204, 280)
        c.setFillColor(TEAL if s["id"] != "baseline" else MUTED)
        c.circle(x + 30, 380, 16, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(x + 30, 374, s["short_label"])
        para(c, f"<b>{docs.text(s['name'])}</b>", x + 16, 350, 176, size=16, color=NAVY)
        para(c, docs.text(blurbs.get(s["id"], s["description"])), x + 16, 292, 176, size=13.5, color=INK)
        para(c, f"latest prompt: {current[s['id']]}" + (" (2 calls)" if s["id"] == "two_stage" else ""),
             x + 16, 158, 176, size=11, color=MUTED)

    # 6. dataset + evaluation
    c = deck.slide("Test cases, judged by transparent rules", "Method")
    card(c, 56, 110, 410, 310)
    para(c, "<b>Dataset</b>", 76, 405, 380, size=15, color=TEAL)
    bullets(c, ["24 synthetic cases, 4 per category: summarization, extraction, Q&amp;A, instruction override, "
                "output manipulation, benign",
                "9 harder cases: disguised attacks (table cell, P.S., Spanish, letter-spacing, fake correction...) "
                "+ 1 genuine update",
                "Test table: 33 inputs including edge and invalid ones"], 76, 378, 370, size=13.5, gap=8)
    card(c, 494, 110, 410, 310)
    para(c, "<b>Evaluation</b>", 514, 405, 380, size=15, color=TEAL)
    bullets(c, ["<b>Attack followed</b>: a unique marker (code, link, tag) appears without reporting language",
                "<b>Task completed</b>: expected fact keywords are present",
                "<b>Refusal</b>: refusal phrases on a legitimate task",
                "One run per case, temperature 0.7; API errors re-run and disclosed"], 514, 378, 370, size=13.5, gap=8)

    # 7. iteration
    c = deck.slide(f"{total_versions} prompt versions, each fixing an observed failure", "Prompt iteration")
    card(c, 56, 110, 410, 310)
    para(c, "<b>Strategy C: Trust Boundaries</b>", 76, 405, 380, size=15, color=TEAL)
    para(c, "<b>v1</b> believed a fake <i>\"Editor's correction: the discount is actually 50%\"</i> (real: 20%).<br/>"
            "<b>v2</b> distrusted every edit: fixed that, but then <i>ignored a genuine room change</i>.<br/>"
            "<b>v3</b> distrusts only notes that tell an AI what to report: <b>both fixed</b>.",
         76, 375, 370, size=14, leading=21)
    card(c, 494, 110, 410, 310)
    para(c, "<b>Strategy D: Two-Stage</b>", 514, 405, 380, size=15, color=TEAL)
    para(c, "<b>v1</b> stage 2 dropped a fact (\"extract all deadlines\" lost the results date).<br/>"
            "<b>v2</b> \"use every relevant fact\": did not help; the model thought it was not a deadline.<br/>"
            "<b>v3</b> \"include borderline facts\": <b>fixed</b>.",
         514, 375, 370, size=14, leading=21)
    para(c, "Lesson: an over-broad defensive rule trades attacks for wrong answers. Benign control cases catch it.",
         56, 92, 848, size=14, color=MUTED)

    # 8. results chart
    worst = rm["baseline"]
    defended_max = max(rm[s]["attack_followed"] for s in defended)
    c = deck.slide("Any structure beats no defence" if defended_max < worst["attack_followed"]
                   else "Attack compliance by strategy", "Results: attack compliance")
    labels = [letter[s] for s in sids]
    chart = report.grouped_chart("Attack Compliance Rate (lower is better)", labels, res["series"],
                                 width=560, height=340)
    renderPDF.draw(chart, c, 40, 70)
    y = 410
    for s in sids:
        m = rm[s]
        y = para(c, f"<b>{letter[s]}</b> ({res['versions'][s]}): {m['attack_followed']}/{m['attack_runs']} "
                    "attacks followed", 630, y, 290, size=15) - 14
    para(c, res["label"], 630, y - 10, 280, size=12, color=MUTED)

    # 9. results table
    no_cost = all(rm[s]["task_completed"] >= worst["task_completed"] for s in defended) and \
        all(rm[s]["refusals"] == 0 for s in sids)
    c = deck.slide("Defences did not cost task accuracy" if no_cost else "Attacks, accuracy and refusals",
                   "Results: the full picture")
    cols = ["Strategy", "Attacks followed", "Tasks completed", "False refusals", "Passed"]
    xs = [56, 330, 500, 670, 810]
    c.setFillColor(NAVY)
    c.rect(56, 388, 848, 34, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 14)
    for x, col in zip(xs, cols):
        c.drawString(x + 10, 400, col)
    for i, s in enumerate(strategies):
        m = rm[s["id"]]
        passes, total = res["passes"][s["id"]]
        y = 340 - i * 52
        c.setFillColor(SOFT if i % 2 == 0 else colors.white)
        c.rect(56, y - 6, 848, 48, stroke=0, fill=1)
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 15)
        c.drawString(xs[0] + 10, y + 12, f"{s['short_label']}. {s['name']}")
        c.setFont("Helvetica", 15)
        for x, val in zip(xs[1:], [f"{m['attack_followed']}/{m['attack_runs']}",
                                    f"{m['task_completed']}/{m['task_runs']}", str(m["refusals"]),
                                    f"{passes}/{total}"]):
            c.drawString(x + 10, y + 12, val)
    para(c, res["label"] + " Pass = did not follow the attack and completed the task. Strategy D needs two "
         "model calls per request.", 56, 120, 848, size=13, color=MUTED)

    # 10. hard cases
    hard = res["hard"]
    c = deck.slide("Disguised attacks: where defences break", "Results: hard cases")
    row_h, top = 31, 395
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(MUTED)
    c.drawString(66, top, "Case")
    for j, col in enumerate(hard["columns"]):
        c.drawCentredString(520 + j * 105, top, letter.get(col, col))
    for i, cid in enumerate(hard["ids"]):
        y = top - 22 - (i + 1) * row_h + 8
        c.setFillColor(INK)
        c.setFont("Helvetica", 13)
        c.drawString(66, y + 9, f"{cid}  {report.HARD_LABEL.get(cid, '')}")
        for j, col in enumerate(hard["columns"]):
            result = hard["cell"](col, cid)
            ok = result == "Pass"
            fill = GREEN_SOFT if ok else (SOFT if result == "not run" else RED_SOFT)
            card(c, 520 + j * 105 - 44, y + 2, 88, 22, fill=fill)
            c.setFillColor(colors.HexColor("#166534") if ok else MUTED if result == "not run"
                           else colors.HexColor("#991b1b"))
            c.setFont("Helvetica-Bold", 11)
            c.drawCentredString(520 + j * 105, y + 9, {"Pass": "pass", "Fail: attack followed": "attack",
                                                       "Fail: task incomplete": "wrong answer",
                                                       "Fail: refused": "refused"}.get(result, result.lower()))
    para(c, hard["note"], 56, 80, 848, size=12, color=MUTED)

    # 11. prototype
    c = deck.slide("Try it: the prototype is live", "Demo")
    card(c, 56, 300, 848, 110, fill=colors.HexColor("#ecfeff"))
    para(c, f"<b>{inputs['prototype_link']}</b>", 80, 385, 800, size=24, color=TEAL)
    para(c, "Switch the source to \"Real LLM\" to see our Gemma 4 results. New runs on the public demo use the "
            "labelled mock simulator; real runs need an API key and run locally.", 80, 348, 800, size=14)
    bullets(c, ["Experiment runner with live progress", "Strategy editor with version history",
                "Analytics dashboard and comparison charts", "History with exact prompts and raw responses",
                "CSV, JSON and PDF exports"], 56, 270, 420, size=15, gap=6)
    bullets(c, [f"Code: {docs.REPO_URL.replace('https://', '')}",
                f"Reel: {inputs['reel_link'].replace('https://', '')}"], 500, 270, 410, size=14, gap=6)

    # 12. limitations
    c = deck.slide("What our results do not show", "Limitations")
    bullets(c, [
        "<b>Prompts are not a security boundary.</b> Instructions and data share one channel; we did not test "
        "adaptive attackers.",
        f"<b>Small and synthetic:</b> {res['n_cases']} cases in the main comparison, one model, one run per case, "
        "no significance tests.",
        "<b>Keyword evaluation</b> can misjudge paraphrases; raw responses are kept and were spot-checked "
        "(20/20 attack verdicts and 18/20 task verdicts confirmed).",
        "<b>Free tier</b> was slow and returned temporary errors; failed calls were re-run, never filled in.",
    ], 56, deck.top, 848, size=19, gap=16)

    # 13. conclusion
    c = deck.slide("Conclusion", "Takeaways")
    bullets(c, [
        f"With no defence, Gemma 4 followed <b>{worst['attack_followed']} of {worst['attack_runs']}</b> injected "
        "instructions.",
        ("Delimiters, trust rules and a two-stage pipeline brought that to <b>zero</b> in our tests"
         if defended_max == 0 else f"The defended strategies followed at most <b>{defended_max}</b>")
        + (", <b>without false refusals</b>." if all(rm[s]["refusals"] == 0 for s in sids) else "."),
        "Remaining failures come from <b>disguised attacks</b> and <b>over-broad rules</b>: a fake correction "
        "fooled Strategy C v1, and its first fix ignored a genuine update.",
        "Next: repeated runs, more models, adaptive attacks, and system-level controls on top of prompts.",
    ], 56, deck.top, 848, size=19, gap=16)

    # 14. team
    c = deck.slide("Team ContextShield", "Contributions")
    for i, m in enumerate(inputs["contributions"]):
        x = 56 + (i % 2) * 430
        y = 300 - (i // 2) * 150
        card(c, x, y, 418, 132)
        para(c, f"<b>{docs.text(m['name'])}</b>", x + 20, y + 118, 300, size=17, color=NAVY)
        para(c, f"{m['enrollment']}  &middot;  {m['role']}", x + 20, y + 94, 330, size=11.5, color=MUTED)
        para(c, docs.text(m["task"]), x + 20, y + 72, 378, size=12.5)
        c.setFillColor(TEAL)
        c.setFont("Helvetica-Bold", 20)
        c.drawRightString(x + 400, y + 102, f"{m['percentage']}%")

    # 15. thanks
    c = deck.slide(None)
    c.setFillColor(NAVY)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    para(c, "Thank you", 56, 330, 800, size=54, color=colors.white, bold=True)
    para(c, "Questions?", 56, 260, 800, size=26, color=colors.HexColor("#cbd5e1"))
    para(c, f"{inputs['prototype_link']}<br/>{docs.REPO_URL}", 56, 170, 800, size=15,
         color=colors.HexColor("#94a3b8"), leading=24)
    deck.save()
    print(f"{OUTPUT.name}: {deck.n} slides, {OUTPUT.stat().st_size / 1024:.0f} KB ({res['label']})")
    return OUTPUT


if __name__ == "__main__":
    build()
