# ChatGPT task pack — review public GitHub + literature (text paste only)

**Date:** 2026-08-16  
**Mode:** paste-only (NO ZIP / NO file upload)  
**CONTEXT 1/1**

You are an external advisor. **Web search ON.** You **can** read this public repository in the browser:

## Public GitHub (please open and review)

**https://github.com/Coucou2016/DOX-LBM-GPU**

Priority paths:
- `README.md`, `docs/ASSUMPTIONS.md`
- `cardiac_ms/` (esp. `ms_modified.py`, `ms_2d.py`, `protocol_s1s2.py`, `geometries.py`)
- `papers/manuscript_draft.md`, `papers/outline.md`, `papers/figures/`
- `reports/research_report.md` (teacher-style figure explanations)
- `tests/`, `requirements.txt`

## Background (short)

Open CPU **2D finite-difference monodomain** scaffold because Villar-Valero et al. (*J Physiol* 2025, doi:10.1113/jp288819) LBM–GPU source is unavailable. Modified MS with λ; CV≈0.70 mm/ms; three-class synthetic fibrosis; S1–S2 extras 240/200/190 ms; **cycle-required** VA labels (reject plateau / single-lap). Default phase diagram: **pinned annulus** (~107 mm) because paper-like discs (~24 mm) cannot fit healthy wavelength (~175 mm). Fast grid: **1 VA / 3 Non-VA**. Commentary: Chabiniok & Zaha (doi:10.1113/jp290313). Local pytest: **42 passed**.

## Ask (answer all)

1. After skimming the GitHub tree: what is **defensible novelty** vs **overclaim** for a methods paper?
2. Survey 3–5 exemplar papers (digital twin / fibrosis reentry / methods journals) whose **section architecture** we should imitate; cite DOIs.
3. Propose a concrete **paper outline** (section titles + 1-line job per subsection) aligned with the repo evidence.
4. Critique `papers/manuscript_draft.md` + figure set: missing panels, weak claims, review risk.
5. Target venues (methods-friendly); not flagship Nature unless justified.

Keep answers concrete and citation-aware. Prefer reading the GitHub pages over inventing local paths.

## Cursor-side note

Automated paste into chatgpt.com from Cursor IDE browser often fails (`No browser tab available`). If this message arrives via human paste, answer in the ChatGPT UI and leave a shareable conversation link if possible.

END OF CONTEXT
