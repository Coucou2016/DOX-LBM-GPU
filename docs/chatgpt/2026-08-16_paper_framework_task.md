# ChatGPT task pack — literature + paper framework (text only)

**Date:** 2026-08-16  
**Mode:** paste-only (NO ZIP / file upload)  
**CONTEXT 1/1**

You are an external advisor. Use **web search** if available. Do not assume access to local files.

## Background

We maintain an open CPU scaffold (`cardiac_ms`) because Villar-Valero et al. (STACOM 2024 / *J Physiol* 2025, doi:10.1113/jp288819) LBM–GPU source is unavailable. Ours is **2D finite-difference monodomain**, modified MS with λ, calibrated CV≈0.70 mm/ms, three-class synthetic fibrosis, S1–S2 with extras 240/200/190 ms, and **cycle-required** VA labels (reject plateau / single-lap). Default phase diagram uses a **pinned annulus** (path≈107 mm) because paper-like discs (≈24 mm) cannot fit healthy wavelength (≈175 mm). Fast annulus grid: **1 VA / 3 Non-VA**. Commentary: Chabiniok & Zaha (*J Physiol*, doi:10.1113/jp290313) urges opening methods toward clinical use.

## Ask (please answer all)

1. Survey 3–5 exemplar papers (cardiac digital twin / fibrosis reentry / methods journals) whose **section architecture** we should imitate for a methods+mechanism paper.
2. Propose a concrete **paper outline** (section titles + 1-line job per subsection).
3. List **defensible innovation claims** vs **overclaims** given we are 2D FD not 3D LBM, synthetic fibrosis ≠ DOX pig LV.
4. Propose a **figure plan** (which panels; SciencePlots style; Nature-ish single-column).
5. Suggest target venues (methods-friendly), not flagship Nature unless justified.

Keep answers concrete and citation-aware. No code dumps required.

## Local facts you may trust

- pytest: 42 passed  
- 0D APD≈256.6 ms  
- CV band 0.55–0.85 mm/ms  
- phase_diagram.csv: VA only at λ=0.01 & D↓90% on annulus  

## Cursor-side status (do not invent a chat URL)

Automated paste into chatgpt.com from Cursor IDE browser **failed** repeatedly (`No browser tab available` / tab vanishes after create). Please answer in the ChatGPT UI; user will paste your reply back. Prefer enabling **web search**.

END OF CONTEXT
