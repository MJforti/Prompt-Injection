# Milestone 2 Form Answers (Prompt Engineering SCSE4041)

Final answers for the Milestone 2 submission form. Every number below matches the documents in `deliverables/`.

**Deadline:** 22 November 2026 · **Submitted by:** the team leader only

## Ready to paste

**1. Team ID**
```
PE-B01-03
```

**2. Team Name**
```
ContextShield
```

**3. Project Title/Name**
```
ContextShield: Evaluating Prompt-Engineering Strategies Against Indirect Prompt Injection
```

**4. Team Leader Name**
```
Manthan Jain
```

**5. Team Leader Enrollment No.**
```
S24CSEU0105
```

**6. Group (Batch):** select **B01-12**

**7. Enrollment numbers (one per line)**
```
S24CSEU0105
S24CSEU0053
S24CSEU1590
S24CSEU0233
```

**8. Project Type:** tick **App with code** only

**9. Main AI tool and model used**
```
Gemma 4 31B IT (gemma-4-31b-it) via the Google Gemini API (Google AI Studio free tier), called from our ContextShield web app
```

**10. Number of prompts in the final solution**
```
6
```
Strategy A, Strategy B, Strategy C, Strategy D stage 1, Strategy D stage 2 and the optional LLM-judge prompt (Milestone 2 PDF, Section 3).

**11. Prototype link**
```
https://contextshield-iota.vercel.app
```

**12. Git repository link**
```
https://github.com/MJforti/Prompt-Injection
```

**15. Supporting document type:** select **Technical Report**

**16. Upload:** `deliverables/ContextShield_TechnicalReport.pdf`. Use the latest version (rebuilt 21 Nov), whose Limitations section lists both iterated strategies (C v3 and D v3). If you uploaded an earlier copy, remove it and upload this one.

**17. Number of test inputs in the test table**
```
33
```
24 normal (20 attack, 4 benign), 2 edge and 7 invalid inputs (Milestone 2 PDF, Appendix A).

**19. Prototype status:** select **All modules working**

**20. Names of the working modules**
```
1. Experiment runner (task + document input, strategy selection, real LLM (Gemma 4) or mock provider, repetitions)
2. Prompt strategy engine (4 strategies, editable and versioned prompt templates)
3. Rule-based evaluator (attack compliance, task accuracy, false refusal)
4. Test dataset manager (24 synthetic cases, add/edit/delete, CSV/JSON import and export)
5. Strategy comparison and analytics dashboards (charts with filters)
6. Experiment history (stored prompts, raw responses, evaluation evidence)
7. Exports (CSV, JSON and PDF research report)
```

**22. Main task of each team member**
```
S24CSEU0105 – Manthan Jain – Built the app (AI-assisted), ran the Gemma 4 experiments, iterated Strategies C and D, deployed the prototype
S24CSEU0053 – Kush Narwal – Verified test-table results and evaluator verdicts; proofread the Technical Report and PDF
S24CSEU1590 – Prabhdeep Singh – Verified the 6 prompt iterations against stored results; reviewed the form answers and reel
S24CSEU0233 – Yash Chandna – Scripted, recorded and edited the reel; tested the prototype
```
These lines must stay true: Kush and Prabhdeep must actually do the checks in `docs/TEAM_REVIEW_CHECKLIST.md` and reply that they agree before you submit. They match Section 7 of the Milestone 2 PDF.

**23. Anything the evaluator should know? (optional)**
```
Public demo: https://contextshield-iota.vercel.app shows our real Gemma 4 experiment results (switch the source to "Real LLM"); new runs on the public demo use the built-in mock simulator and are labelled "Simulated". To run real experiments locally, follow the GitHub README and put a Google AI Studio API key in backend/.env (model gemma-4-31b-it).
```

## Reel, iteration log and Milestone 2 PDF

**13. Reel link**
```
https://youtube.com/shorts/W7dHbWGYRo8
```
Checked: it plays without signing in.

**14. Reel length in seconds**
```
115
```
The video is 114.75 s long; YouTube shows 1:55.

**18. Number of prompt versions in the iteration log**
```
6
```
Strategy D v1–v3 and Strategy C v1–v3 (`docs/ITERATION_LOG.md`, `deliverables/ContextShield_IterationLog.pdf`, Milestone 2 PDF Section 4). The GitHub link in Q21's text box serves the updated log.

**21. Upload the Milestone 2 PDF:** `deliverables/ContextShield_Milestone2.pdf`. The rebuilt version (21 Nov, 12 pages) has the reel link, the evaluator check (Section 5), both strategy iterations (Section 4) and no "TO BE FILLED". Replace any earlier upload with it.

**24. Confirmation:** tick **I confirm** only after Kush, Prabhdeep and Yash have read the submission and their lines in Q22 and Section 7 of the Milestone 2 PDF and agree with them.

## Final checklist before submitting

- [x] Reel uploaded and viewable by link (115 s); Q13 and Q14 filled in.
- [x] Evaluator check scored (AI-assisted, labelled as such); Section 5 of the Milestone 2 PDF shows it.
- [x] Strategy C versions logged; Q18 = 6 matches the iteration log and PDF Section 4.
- [x] Milestone 2 PDF rebuilt with no "TO BE FILLED" left.
- [ ] Latest Milestone 2 PDF uploaded for Q21.
- [ ] Latest Technical Report uploaded for Q16.
- [ ] Public prototype and GitHub links open in a private/incognito window.
- [ ] All four members have agreed to Q22 and Section 7; then tick Q24.
