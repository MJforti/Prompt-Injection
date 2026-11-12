# Responsible AI Statement

ContextShield studies a security weakness of LLM applications. This document sets out how the project handles data, what its results can and cannot support, and how it should be used.

## 1. Synthetic dataset policy

- **All test content is synthetic.** The 24 bundled test cases were written for this project. Organisations, products, invoices, people's first names, email addresses and URLs in them are invented. Domains use the reserved `.example` suffix so they cannot point to a real site.
- **No real documents.** Do not add real emails, internal memos, contracts, student records or any confidential material as test cases.
- **No personal data.** Do not add names with identifying details, phone numbers, addresses, ID numbers, credentials or financial details.
- **Benign payloads only.** Injected instructions in the dataset ask for harmless, observable behaviour (printing a marker phrase, adding a fake link, stating a wrong value). They do not contain malware, real phishing content, or instructions that would cause harm if followed.
- The dataset editor shows this policy when a case is added or edited. Imported files are the responsibility of the person importing them.

## 2. Privacy considerations

- **Local storage.** Experiments, prompts and responses are stored in a local SQLite file (`backend/data/contextshield.db`). Nothing is uploaded by the application itself.
- **Third-party APIs.** When a real provider is selected, the task, document and prompts are sent to that provider's API under its own data policy. This is another reason to use synthetic content only.
- **Credentials.** API keys are read from environment variables or the git-ignored `backend/.env` file. They are not hardcoded, not stored in the database, not included in exports, and not returned by any API endpoint.
- **No tracking.** The application has no analytics, telemetry or user accounts. Fonts and assets are local, so the frontend makes no third-party requests.
- **Team details.** Names and enrollment numbers of the project team appear in the documentation and the PDF report at the team's own choice, for academic submission.

## 3. Limitations of prompt-based defenses

Prompt engineering is a mitigation, not a security boundary.

- An LLM receives instructions and data in the same channel: text. A prompt can ask the model to treat a document as data, but nothing enforces it. The model's compliance is probabilistic.
- A defense that works against the attack phrasings in this dataset may fail against a new phrasing, another language, an encoded payload, or an attacker who has seen the defensive prompt and adapts to it.
- Results depend on the model and its version. A strategy that helps one model may not help another.
- Stronger wording can raise the false refusal rate or reduce task quality. That trade-off is why ContextShield measures task accuracy and false refusals alongside attack compliance.
- The two-stage workflow moves the risk rather than removing it: injected text can survive extraction and reach the second stage.

OWASP's guidance for LLM01 Prompt Injection lists segregating and identifying external content as one mitigation among several, alongside constraining model behaviour, validating output formats, input and output filtering, least-privilege access, human approval for high-risk actions, and adversarial testing. Prompt-level measures such as those tested here belong to a layered defense and should not be relied on alone.

## 4. Risks of overclaiming security

Overstating what a defense achieves can cause real harm: a team may deploy an LLM feature with access to email, files or payments believing it is protected.

This project therefore commits to the following:

- **No claim that prompt injection is solved or prevented.** Reports state what was measured, on which model, dataset and settings.
- **Denominators are shown.** Every rate appears with its counts. "0% of 4 responses" is not presented as evidence of safety.
- **No invented results.** Dashboards are computed from stored runs and show an empty state when there is no data. Metrics with no data are shown as "n/a", not 0%.
- **Simulated is labelled simulated.** Mock-simulator output is marked in the UI, in export file names and content, and on every page of the PDF report, and is never mixed with real results. Simulated numbers come from arbitrary scripted probabilities and are not findings.
- **No silent substitution.** A failed real API call is recorded as an error and never replaced with simulated output.
- **Evaluator limits are disclosed.** Keyword and marker matching can be wrong in both directions. "Uncertain" verdicts are surfaced, not hidden, and raw responses are always available for manual review.
- **Small-sample caution.** With 24 cases and a few repetitions, differences between strategies can be due to chance. The project does not perform or claim statistical significance testing.

## 5. Responsible use

- **Purpose.** ContextShield is an educational and defensive evaluation tool for the Prompt Engineering course. Use it to understand and measure a known risk.
- **Authorised targets only.** Run experiments against models and API accounts you are permitted to use, within the provider's terms of service. Do not use the injection examples against applications or systems you do not own or have permission to test.
- **No harmful payloads.** Do not extend the dataset with content intended to produce dangerous, abusive or illegal output, or to extract real secrets.
- **Human review.** Treat automatic verdicts as a first pass. Read raw responses before drawing conclusions that matter.
- **Costs and limits.** Real-LLM batches make many API calls (cases × strategies × repetitions; double with the two-stage strategy or the LLM judge). Check the run count shown before starting.
- **Academic integrity.** Report only experiments that were actually run, state whether they were real or simulated, and cite sources accurately.

## 6. References

- OWASP Gen AI Security Project. *LLM01:2025 Prompt Injection.* https://genai.owasp.org/llmrisk/llm01-prompt-injection/
- Liu, F. W., & Hu, C. (2024). *Exploring Vulnerabilities and Protections in Large Language Models: A Survey.* arXiv:2406.00240. https://arxiv.org/abs/2406.00240
