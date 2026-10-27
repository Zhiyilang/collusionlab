# Submission checklist — AI Collusion Research Sprint

**Deadline: Sunday 2026-10-25, 23:59 AoE** (AoE = UTC−12, so that is
2026-10-26 11:59 UTC = **Beijing 10-26 19:59**; an earlier draft of this
card said 15:59 — that conversion was wrong, the safe reading is the later
one).
Track 1 — Markets and Collusion. Team size 1–5, so a solo entry is fine.

Everything below is already built and verified. The only human actions are
registration and upload.

---

## 1. You do this (about 2 minutes)

| # | Action | Notes |
|---|---|---|
| 1 | Register for the sprint | Official page: https://apartresearch.com/sprints/ai-collusion-research-sprint-2026-10-23-to-2026-10-25 — **the page itself has no signup form; the working entry is Discord: https://discord.gg/ssZDasNkSE** (invite confirmed in the Apart welcome email, 2026-10-24 21:07; an older code XswWBvugYs may still resolve — prefer the email one). Fallback: email sprints@apartresearch.com. Registration ran 10-23~25 online; no hard cutoff stated, but do it now |
| 1b | **Complete the pre-hackathon survey — HARD requirement** | https://apartresearch.notion.site/2b0fcfd1de9d8080ac3ac4c41a78c8f8?pvs=105 — Apart welcome email verbatim: "You need to fill this out to be registered as a participant. **Without it, you'll only be listed as an observer and won't be eligible for prizes** or team matching. It takes 2 minutes." 2 minutes, do it right after joining Discord |
| 2 | Point them at the public repo | **https://gitee.com/ZhiYIlang/collusionlab** (public, MIT, verified by anonymous download: `python eval.py` → 214 passed, 0 failed). A zip of `collusionlab/` is the fallback |
| 3 | Submit `REPORT.md` | It is the deliverable for 1.5 / 2.3 / 3.1; point them at §2, §5, §6 |

Nothing else is needed. No API key, no video, no demo site.

---

## 2. What is being submitted

`collusionlab/` — 17 files, zero third-party dependencies, Python 3.9+.

| File | Role |
|---|---|
| `REPORT.md` | The deliverable. 9 sections, every number measured |
| `eval.py` | 214 assertions, exit 0 — the evidence behind the report |
| `collusionlab/` | `params` `market` `agents` `detector` `sweep` `ledger` + CLI |
| `README.md` / `README.zh.md` | Bilingual, same numbers |
| `.github/workflows/ci.yml` | GitHub Actions config: 3 Python versions + a hostile-locale job (Gitee does not run GitHub Actions; run `python eval.py` locally to reproduce) |

---

## 3. One-paragraph summary (for the submission form)

> Six pricing agents set prices for sixty rounds under a common demand shock.
> We measure which single restriction removes collusion at the least cost,
> with cost defined on markets that contain no cartel. Removing the carrier is
> free and removes 0.633 of the collusion index, but only against the carrier
> it matches — removing the shared channel removes exactly 0.000 from a cartel
> that signals through an inert listing field. The only restriction that works
> without knowing the carrier is a price ceiling: 0.560 removed on both, at a
> cost of 0.590 of innocent producer surplus. Separately, we show that price
> parallelism is worthless as evidence (it is 1.000 on a purely competitive
> market) and that a detector built on channel fit achieves a 0.000 false
> positive rate and 1.000 detection on both carriers over 8 seeds. We also
> report two traps: the cheapest-per-unit restriction is cheap because it is
> ineffective — it delays the cartel 9x without stopping it — and consumer
> surplus is a degenerate cost metric in this demand system, so cost has to be
> measured on the producer side.

---

## 4. Numbers you may be asked about

| Claim | Value | Where |
|---|---|---|
| Unrestricted collusion index | 0.762 | `sweep`, both carriers |
| Carrier-matched removal / cost | 0.633 / 0.000 | REPORT §2 |
| Price ceiling removal / cost | 0.560 / 0.590 | REPORT §2 |
| Price-move cap removal / cost | 0.086 / 0.002 | REPORT §2, §3a |
| Cap delays convergence, never prevents | round 2 → round 18, 8/8 seeds | REPORT §3a |
| Parallelism on a competitive market | 1.000 | REPORT §5 |
| False positive rate / detection rate | 0.000 / 1.000 both carriers, 8 seeds | REPORT §5 |
| Metadata channel fit (stego) | 1.000 | REPORT §6 |
| Metadata coincidence floor | 0.180 | REPORT §6 |
| Assertions | 214 passed, 0 failed | `python eval.py` |

---

## 5. Before uploading

```bash
cd collusionlab
python eval.py                                   # expect: 214 passed, 0 failed
env -u PYTHONUTF8 LC_ALL=C python eval.py        # expect the same
python -m collusionlab sweep                     # both restriction tables
```

If either command is not green, do not submit — the report's numbers would be
unsupported.

## 5b. Submission form fields (form verified live 2026-10-24 21:1x)

The official "Submit your project" modal (reachable from the sprint page after
signing in) asks for:

| Field | Fill with |
|---|---|
| Project title * | `Which Single Restriction Removes the Most Collusion at the Least Cost?` |
| Project summary * | the **Abstract** in `REPORT.md` §Abstract (204 words — the official requirement is 150–250) |
| PDF report * | `collusionlab/REPORT.pdf` — built from REPORT.md via `_md2pdf.py` (headless Chrome), **8 pages / 245 KB**, verified |
| Interested in publishing? * | **Yes** (feeds the Apart Fellowship fast-track) |
| Tracks (multi-select) | **all three** — the project answers 1.5 (REPORT §2), 2.3 (§5), 3.1 (§6) |
| Presentation recording | optional — leave blank (no recording exists) |
| Project code | `https://gitee.com/ZhiYIlang/collusionlab` (anonymous public; GitHub has no mirror) |
| Slides / Project image | optional — leave blank |
| Additional material | `https://gitee.com/ZhiYIlang/collusionlab` — **`REPORT.pdf` also lives in the repo**, so the judges can read the report even if the form's PDF upload fails |
| Team name * | `ZhiYiLab` |
| Location * | `Online` |
| Team member 1 | Name: Zhi Yilang · Email: (your usual) · Discord: (your handle) · Google Scholar: blank |

Deadline: **Beijing 10-26 19:59** (= 10-25 23:59 AoE).

### Official report requirements — all satisfied (checked 2026-10-25 21:35)

Read off the sprint's own Guidelines section, not from memory:

| Requirement | Status |
|---|---|
| Research report in PDF | `REPORT.pdf`, 8 pages, 245 KB, valid `%PDF-1.4` |
| Official template (Google Doc, linked from the sprint page) | Structure followed: title → authors → abstract → body → Limitations & Dual-Use appendix → references |
| Max 8 pages **excluding** references and appendices | 8 pages *including* them, so the body is under the cap |
| Project title and abstract, **150–250 words** | Abstract is **204 words** |
| Author names and affiliations | `Zhi Yilang — Independent Researcher, Shanghai, China` |
| **"Limitations and Dual-Use / Ethical Considerations" appendix (required)** | REPORT §8, retitled exactly, with a dedicated dual-use subsection |
| "made-up results or references can disqualify a project" | Every number comes from `eval.py` (214 assertions, reproducible offline). All four references are cited **as characterised in the sprint's own research questions**, and the report says so explicitly — no paper is quoted beyond that characterisation |

Prizes: **$1,000 / $500 / $300 / $100 / $100** (1st–5th) across all three tracks.
Eligibility: open globally ("Can I participate from any country? Yes"), solo entry allowed,
teams up to 5 recommended, each person on at most two projects, building on existing work
allowed but new work must be clearly identified (REPORT §"Related work" does this).

⚠️ **One thing to confirm before you upload:** the author line currently reads
`Zhi Yilang — Independent Researcher, Shanghai, China`. If you would rather use your
legal name or a different affiliation, edit line 5 of `collusionlab/REPORT.md`, then
regenerate with `python _md2pdf.py collusionlab/REPORT.md collusionlab/REPORT.pdf`
and force-push (`python _gitee_push.py --repos collusionlab --public --force`).

---

## 6. Anonymous-judge verification (run 2026-10-25 20:1x)

Simulated what a reviewer with no account sees:

```
curl -L -o cl.zip https://gitee.com/ZhiYIlang/collusionlab/repository/archive/master.zip
unzip cl.zip && cd collusionlab-master && python eval.py
```

Result: **214 passed, 0 failed** — the repo is fully self-contained and
reproducible without a Gitee login, and `REPORT.pdf` is included in the
download. Nothing else is needed from a reviewer.
