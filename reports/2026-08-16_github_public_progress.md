# Progress — paper framework + literature (Cursor local + GitHub public)

**Date:** 2026-08-16  
**GitHub (public):** https://github.com/Coucou2016/DOX-LBM-GPU  
**HEAD:** `323b657af926597a28cbcfc1cc583de18728e469`

## Dual-agent status

| Agent | Role | Status |
|-------|------|--------|
| Cursor | Implement + verify + push | Done this turn |
| ChatGPT Pro/Plus | Literature + framework advisor | **Blocked in Cursor browser**; task pack ready for human paste |

## ChatGPT task for human paste

File: `docs/chatgpt/2026-08-16_github_review_task.md`  
Tell ChatGPT: open **https://github.com/Coucou2016/DOX-LBM-GPU** (web search ON). No ZIP uploads.

## Local literature (WebSearch; Cursor-side)

1. **Villar-Valero et al., *J Physiol* 2025** — doi:10.1113/jp288819 — MRI-based 3D fibrotic LV + modified MS + GPU LBM parametric VA study.  
2. **Chabiniok & Zaha commentary** — doi:10.1113/jp290313 — open the method toward clinical translation.  
3. **Villar-Valero et al., STACOM 2024** — doi:10.1007/978-3-031-87756-8_7 — earlier DOX imaging + LBM pipeline.  
4. **Related commentary** — doi:10.1113/jp290582 — maze-like substrate framing (use carefully; not a methods template).  
5. Prior scaffold notes still apply: Campos *Front Physiol* 2024 (fibrosis representation / openCARP); CardioMat / *Comput Biol Med* 2024 toolbox-style Methods papers.

## Defensible innovation (for ChatGPT to refine)

- Open, pytest-backed **protocol scaffold** when LBM–GPU is unavailable.  
- **Cycle-required VA** endpoint hardening (plateau / single-lap rejection).  
- **Wavelength-aware** annulus geometry recovering mixed 1 VA / 3 Non-VA.  
**Not claimed:** 3D DOX twin equivalence; LBM performance; clinical decision tool.

## Deliverable paths

- Paper: `papers/manuscript_draft.md`, `papers/manuscript.html`, `papers/figures/`  
- Report: `reports/research_report.{md,html,pdf}`, `reports/report.html`  
- Tests: **42 passed**
