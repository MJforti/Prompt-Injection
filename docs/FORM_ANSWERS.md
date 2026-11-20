# Milestone 2 Form Answers (Prompt Engineering SCSE4041)

Final answers for the Milestone 2 submission form. Items marked **⏳ PENDING** depend on team work that is still in progress; update them before submitting. Every number below matches the documents in `deliverables/`.

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

**16. Upload:** `deliverables/ContextShield_TechnicalReport.pdf`. Use the latest version, whose Limitations section mentions the 3-version iteration log. If you uploaded an earlier copy, remove it and upload this one.

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
S24CSEU0105 – Manthan Jain – Built the ContextShield application (backend, frontend, rule-based evaluator) with AI-assisted coding; ran the Gemma 4 experiments and the Strategy D prompt iterations; deployed the public prototype
S24CSEU0053 – Kush Narwal – Manual validation of the evaluator: comparing a sample of 20 real Gemma 4 responses with the automatic verdicts and recording agreement
S24CSEU1590 – Prabhdeep Singh – Prompt iteration of Strategy C (Explicit Trust Boundaries): revising, testing and logging new prompt versions on the dataset
S24CSEU0233 – Yash Chandna – Reel scripting, recording and editing; testing the public prototype on phone and laptop
```
These lines must stay true: each member must actually have done their task by the time you submit. If anyone's work changes (for example, part of the reel is produced another way), update their line and Section 7 of the Milestone 2 PDF to match.

**23. Anything the evaluator should know? (optional)**
```
Public demo: https://contextshield-iota.vercel.app shows our real Gemma 4 experiment results (switch the source to "Real LLM"); new runs on the public demo use the built-in mock simulator and are labelled "Simulated". To run real experiments locally, follow the GitHub README and put a Google AI Studio API key in backend/.env (model gemma-4-31b-it).
```

## ⏳ Pending: fill in when the team's work is done

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

**18. Number of prompt versions in the iteration log.** Currently **3** (Strategy D v1–v3). When Prabhdeep's Strategy C versions are added, this becomes 3 + his number of versions. Use the total shown at the top of `docs/ITERATION_LOG.md` after the log is rebuilt, which also appears in Section 4 of the Milestone 2 PDF.
```
⏳ PENDING (currently 3)
```

**21. Upload the Milestone 2 PDF:** `deliverables/ContextShield_Milestone2.pdf`. Upload it only after it has been rebuilt with the reel link, Kush's review result (Section 5) and Prabhdeep's iterations (Section 4). Before then it still says "TO BE FILLED" for the reel.

**24. Confirmation:** tick **I confirm** only after Kush, Prabhdeep and Yash have read their lines in Q22 and Section 7 of the Milestone 2 PDF and agree with them.

## Final checklist before submitting

- [x] Reel uploaded and viewable by link (115 s); Q13 and Q14 filled in.
- [ ] Kush's review sheet is scored; Section 5 of the Milestone 2 PDF shows the result.
- [ ] Prabhdeep's Strategy C versions are logged; Q18 matches the total in the iteration log and PDF Section 4.
- [ ] Milestone 2 PDF rebuilt with no "TO BE FILLED" left; uploaded for Q21.
- [ ] Latest Technical Report uploaded for Q16.
- [ ] Public prototype and GitHub links open in a private/incognito window.
- [ ] All four members have agreed to Q22 and Section 7; then tick Q24.
