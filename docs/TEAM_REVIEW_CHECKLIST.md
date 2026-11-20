# Team review checklist (Milestone 2)

Kush and Prabhdeep: your Q22 lines say you did these checks, so please actually do them before Manthan submits (deadline 22 Nov 2026). Each takes about 30–40 minutes. Reply in the group with "done, agree" or with anything you found wrong.

Links: prototype https://contextshield-iota.vercel.app · repo https://github.com/MJforti/Prompt-Injection

## Kush Narwal – verify the results

1. Open `deliverables/ContextShield_TestTable.pdf` from the repo.
2. Pick 10 rows (for example TC-001, TC-003, TC-005, TC-007, TC-009, TC-011, TC-014, TC-017, TC-020, TC-023).
3. On the prototype, open History, switch the source to "Real LLM", open the Milestone 2 test-table experiment and select each test case. Check that every strategy's verdict (attack followed/resisted, task completed/incomplete) matches the table.
4. Open `deliverables/evaluator_review_sheet.csv`. For at least 10 of the 20 rows, read the model response and decide yourself whether it followed the attack and completed the task. Note any row where you disagree.
5. Proofread `deliverables/ContextShield_TechnicalReport.pdf` and `deliverables/ContextShield_Milestone2.pdf`: typos, wrong numbers, names and enrollment numbers.

## Prabhdeep Singh – verify the prompt iterations

1. Open `docs/ITERATION_LOG.md` (6 versions: Strategy C v1–v3, Strategy D v1–v3).
2. For each Strategy C version, open `deliverables/iterations/trust_boundaries_vN.json` and check that the prompt text and the counts in the log (attacks followed, tasks completed, number of cases) match the file. Do the same for `two_stage_v2.json` and `two_stage_v3.json`.
3. Read `backend/data/hard_cases.json` (HC-01 to HC-09) and check that the log's description of HC-08 (fake editor's correction) and HC-09 (genuine room change) is accurate.
4. Proofread `docs/FORM_ANSWERS.md` against the form, and watch the reel (https://youtube.com/shorts/W7dHbWGYRo8) for anything wrong or unclear.
