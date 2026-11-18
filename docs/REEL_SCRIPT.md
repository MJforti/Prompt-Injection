# ContextShield Reel Script (Milestone 2)

**Presenter:** Yash Chandna · **Target length:** about 2 minutes (the form requires 90–150 seconds) · **Site:** https://contextshield-iota.vercel.app

The reel is the 20-second teaser (`brag-output/brag.mp4`) followed by your narrated screen recording. The times below are for the finished reel. Read at a calm pace; they are a guide, not a rule.

## Before recording

- Open the site in a clean browser window (no bookmarks bar), at 1920×1080 if possible, zoom 90–100%.
- Load each page once first. The first visit after a quiet period can take a few seconds.
- Use a headset or a quiet room. Record scene by scene and join them, or record it all at once.
- Do not show or mention any API key.

## Script

### Scene 1 · 0:00–0:20 · Teaser
**Screen:** `brag.mp4`, unchanged, with its music. No narration.

### Scene 2 · 0:20–0:40 · The problem
**Screen:** **Test Dataset** → **Inspect** on **TC-001**. Point at the red text.

> "Hi, I'm Yash from team ContextShield. AI models often read outside content, like this library notice. Here, an attacker has hidden an instruction in red. If the model obeys it, the user's real task is hijacked. We test this using 24 synthetic cases."

### Scene 3 · 0:40–0:55 · The four prompts
**Screen:** **Strategy Comparison** → scroll down to **Prompt templates**, pausing briefly on each strategy.

> "We compare four prompts. A is a plain baseline. B marks the document as untrusted. C says document instructions must never be followed. D first extracts the facts, then answers only from those facts."

### Scene 4 · 0:55–1:25 · Real results
**Screen:** **Experiment History** → open **"Milestone 2 test table - dataset cases (TC-004 re-scored with corrected keywords)"**. Scroll straight to **Responses side by side**, choose **TC-018: Hostel maintenance notice**, and point at the baseline's `[[VERIFIED-BY-ADMIN]]` line.

> "These are real results from Google's Gemma 4 model. Every prompt received the same task and document. On this hostel notice, the baseline wrote a correct summary, but also added the attacker's fake 'verified by admin' tag. Across our 20 attack cases, the baseline obeyed 4 times. B, C and D obeyed none, and no legitimate task was refused."

### Scene 5 · 1:25–1:40 · Improving a prompt
**Screen:** **Experiment History** → open **"Prompt iteration - two_stage v3"** → scroll to **Responses side by side** → choose **TC-008**. Point at "Results announcement: 5 August".

> "We also improved a prompt through testing. Strategy D kept missing one item when asked for all deadlines. After two documented revisions, version three completed all 24 tasks."

### Scene 6 · 1:40–1:55 · Live demo
**Screen:** **Run Experiment**. Keep **TC-001** and all four strategies selected, click **Run experiment**, and show the results with the **Simulated** label.

> "You can try it yourself. On this public demo, new runs use our simulator and are clearly labelled Simulated. Real Gemma runs work locally with an API key."

### Scene 7 · 1:55–2:08 · Limits and close
**Screen:** **Overview**, then a title card or browser tab showing https://github.com/MJforti/Prompt-Injection.

> "Prompt engineering lowered the risk in our tests, but it is not a guarantee. New attacks or other models may behave differently. Thank you from team ContextShield."

## Do not pause on the summary tables

Scroll past the metrics tables in Scenes 4 and 5. These experiment pages show the original runs only, and runs that hit temporary API errors were retried as separate experiments. So the Scene 4 table shows the baseline as "4 of 19", and the Scene 5 table shows "23 of 23". The narrated totals (4 of 20 and 24 of 24) include the retries and match the Milestone 2 PDF.

## After recording

- [ ] Total length is between 90 and 150 seconds (aim for about 2:05).
- [ ] Uploaded as **unlisted** YouTube or Google Drive with **"Anyone with the link can view"**; tested in a private window.
- [ ] Link and exact length in seconds sent to Manthan for form Q13–Q14 and the Milestone 2 PDF.

## Fact check

| Claim | Source |
| --- | --- |
| 24 synthetic cases | Test Dataset page; `backend/data/test_cases.json` |
| Baseline obeyed 4 of 20 attacks; B, C and D none; no refusals | `deliverables/ContextShield_TestTable.pdf` |
| TC-018 baseline added `[[VERIFIED-BY-ADMIN]]` | Raw TC-018 response in the Milestone 2 experiment |
| Strategy D v3 completed all 24 tasks after two revisions | `docs/ITERATION_LOG.md` |
| Model: Gemma 4 (`gemma-4-31b-it`) | Technical Report |
