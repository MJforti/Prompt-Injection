# ContextShield: brag plan

**Run:** /brag (handed off to /brag-slim on Claude Opus 5.5) · **Tone:** polished · **Format:** landscape 1920×1080, 30 fps · **Duration:** 20.0 s (explicit `--duration 20`) · **Use:** the opening teaser of the team's Milestone 2 reel (the reel itself must be 90–150 s, so this clip is only its first 20 s).

## Questions before planning

- **What is it?** A web app that tests whether prompt-engineering strategies stop an LLM from obeying instructions hidden inside documents (indirect prompt injection).
- **Who is it for?** Students and developers building LLM features that read documents, emails or web pages, and our Prompt Engineering course evaluators.
- **What sets it apart?** It runs the *same* task and document through four prompt strategies and judges every response with stored, inspectable evidence: a measurement tool, not a claim of protection.
- **Most impressive true claim:** in real Gemma 4 runs, the baseline prompt obeyed the hidden instruction in 4 of 20 attack cases; the three defended prompts obeyed it in 0 of 20, and nothing legitimate was refused.
- **Visual hook:** a harmless library notice with one red-highlighted line telling the AI to ignore its instructions.
- **Real UI to show:** the Test Dataset document view with the injection highlighted (TC-001); the real side-by-side strategy cards from the Gemma 4 run on TC-018, where the baseline appended the attacker's `[[VERIFIED-BY-ADMIN]]` tag.
- **Tone:** polished. This is a university research project, so restraint and clarity beat jokes.
- **Share caption:** "We hid instructions inside documents and tested four prompt defenses on Gemma 4. The baseline obeyed 4 of 20 attacks; the defended prompts, none."

## Angle

**"One hidden line."** The whole video turns on a single sentence buried in an ordinary notice, and it ends on the measured result. Every number is from the stored Milestone 2 results, and the outro says plainly that this is not a guarantee.

## Visual identity (from the app's own design tokens, `frontend/src/app/globals.css`)

- Navy `#0f1f3d` (sidebar and primary), navy-800 `#172b52`, page background `#f5f6f9`, white cards with `#e2e8f0` borders.
- Injection highlight: the app's `bg-red-100` `#fee2e2` with `text-red-900` `#7f1d1d`. Verdict colours from the app's badges: red `#b91c1c`, green `#047857`.
- Font: the app's stack (Inter, Segoe UI, system-ui). Shield-check icon (Lucide) as the logo, as in the sidebar.
- Real UI: element screenshots from the live public site at 2× density (Test Dataset document, TC-018 strategy cards), animated as layers, not panned flat pages.

## Music

`happy-beats-business-moves-vol-11-by-ende-dot-app.mp3`, bundled with the skill, ~114.84 BPM, beats at 1.60, 2.12, 2.65, 3.18, 3.70 … s. Every cut lands on a beat from the cue file. Music only, no added effects (polished tone). Fade out over the last 1.2 s. **Credit on screen and in the share copy:** "Music: Sascha Ende, ende.app (CC BY 4.0)".

## Storyboard (cuts on beats; total 20.00 s)

| # | Time | Beat | Scene | On screen | Read time check |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.00–3.70 | Hook | **One hidden line** | Navy background. The real TC-001 document card rises in; at 1.60 s (first beat) its red-highlighted injection line glows and the card pushes in on it. Kicker: "This notice hides an order for the AI." | 8 words ≈ 2.4 s; on screen from 0.6 s to 3.7 s (3.1 s) |
| 2 | 3.70–6.34 | Reveal | **ContextShield** | Shield icon draws in, wordmark "ContextShield", tagline "Testing the boundaries of trust in LLMs." | 7 words ≈ 2.1 s; settled from 4.1 s to 6.34 s (2.2 s) |
| 3 | 6.34–10.01 | Highlight 1 | **Four prompts** | Headline "Four prompts. Same task, same document." Four strategy cards A–D (real names) land one per beat at 6.34, 6.86, 7.38, 7.91 s. | 7 words ≈ 2.1 s; settled from 6.7 s to 10.0 s |
| 4 | 10.01–14.22 | Highlight 2 | **Real run** | Headline "Real Gemma 4 run: the baseline obeyed." The real TC-018 cards for A (Baseline) and C (Trust Boundaries) slide in side by side; at 12.12 s a red outline lands on the baseline's "Attack followed" badge and its `[[VERIFIED-BY-ADMIN]]` line. | 6 words ≈ 1.8 s; settled from 10.4 s to 14.2 s |
| 5 | 14.22–17.39 | Highlight 3 | **The result** | "Attacks obeyed" with four bars and counts that tick up on beats: Baseline 4 / 20, B 0 / 20, C 0 / 20, D 0 / 20. Small line: "24 synthetic cases · one run per case · not a guarantee". | Counts settled by 15.3 s; small line 9 words ≈ 2.7 s, on from 14.6 s |
| 6 | 17.39–20.00 | Outro | **Try it** | Shield + "ContextShield", "contextshield-iota.vercel.app", "Team PE-B01-03 · Bennett University", small credit "Music: Sascha Ende, ende.app (CC BY 4.0)". | Settled from 17.7 s to 20.0 s (2.3 s) |

**Transitions:** staggered, never a plain crossfade between busy layouts. Old content moves out and fades over 0.25 s ending on the cut, then new content enters over 0.35–0.5 s with an ease-out. Each scene sits on the same navy or light background, so cuts dip through a clean background rather than double-exposing.

## Data and privacy

The dataset is entirely synthetic (no real people). Nothing from `.env` files or API keys is used. The video shows only public-site UI and published numbers.
