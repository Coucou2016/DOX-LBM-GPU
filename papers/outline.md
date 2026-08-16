# Paper writing framework & outline

**Axes (nature-writing):** `task=manuscript` · `paper_type=methods` · `language=zh-to-en working draft` · `journal=generic` (methods-journal target; not flagship *Nature*)  
**One-sentence argument:** In the absence of the original LBM–GPU solver, we show that a reproducible 2D monodomain λ-Mitchell–Schaeffer pipeline with cycle-required reentry metrics and wavelength-aware geometry recovers paper-aligned CV and mixed VA/Non-VA inducibility maps, without claiming a 3D DOX digital twin.

## Exemplar architectures to imitate (literature survey)

> **Advisor note (2026-08-16):** Cursor 无浏览器 MCP，无法维持 ChatGPT 会话 URL。下表综合既有大纲 + Round-1 WebSearch 顾问备忘（`docs/chatgpt/round_1_notes.md`），经独立判断采纳。

| # | Exemplar | Why imitate |
|---|----------|-------------|
| 1 | Villar-Valero et al., *J Physiol* 2025 (doi:10.1113/jp288819) + STACOM 2024 | Primary scientific target: parametric λ×D fibrosis scan, S1–S2, VA endpoint; modified MS + LBM–GPU twin |
| 2 | Chabiniok & Zaha commentary (*J Physiol*, doi:10.1113/jp290313) | Translational framing: open the method, personalizable MS, clinical distance |
| 3 | Campos et al., *Front Physiol* 2024 (doi:10.3389/fphys.2024.1370795) | Fibrosis-representation choice → VA morphology; openCARP monodomain inducibility ladder |
| 4 | *Sci. Rep.* 2024 fibrosis reentry (doi:10.1038/s41598-024-62002-5) | Induction vs observation windows; explicit endpoint definitions |
| 5 | CinC 2025 ventricular twin (e.g. CinC2025-149): S1–S2; reentry = multi-cycle closed-loop | Peer language for cycle-required VA |
| 6 | Biasi et al. CardioMat, *Comput Biol Med* 2024 | Methods/toolbox: pipeline → verification → application bounds |

**Rejected as structural template:** clinical AF ablation twin depth papers (e.g. Nat Cardiovasc Res 2024) — too far from methods-scaffold claims.

## Recommended section map (methods + mechanism)

1. **Title / Abstract (EN)** — bounded methods claim  
2. **Introduction** — DOX fibrosis → VA; gap = closed LBM source + wavelength mismatch on small discs  
3. **Related work** — twins, LBM vs FD, phenomenological MS (cite λ lineage carefully)  
4. **Methods** — λ-MS; `div(D∇u)`; tissue classes; **simulation protocol & endpoints** (induction vs observation); *require_cycle* VA; annulus geometry; verification suite  
5. **Results** — 0D APD; 2D CV; diffusion operator; **full 4×3** annulus phase diagram; disc negative control  
6. **Discussion** — honest novelty; Chabiniok–Zaha “open the method”; MI≠DOX; what 2D cannot do  
7. **Methods appendix / Code availability** — pytest gates, SciencePlots figures  

## Defensible innovation claims (and forbidden claims)

**Claim (yes):**
- Open, tested CPU scaffold aligned to paper ionic/protocol choices when LBM–GPU source is unavailable  
- Cycle-required VA metric that rejects plateau / single-lap false positives  
- Wavelength-aware annulus geometry enabling mixed VA/Non-VA at healthy τ_close  
- Conservative diffusion operator with explicit shortcut comparison  

**Do not claim:**
- First DOX cardiac digital twin  
- Reproduction of 3D pig LV LBM–GPU performance or clinical ICD utility  
- Equivalence of synthetic fibrosis to DOX myocardium or ischemic MI  

## Figure plan (SciencePlots)

| Fig | File stem | Panel job |
|-----|-----------|-----------|
| 1 | `fig_ms_0d_ap` | 0D AP + APD₉₀ |
| 2 | `fig_validation_summary` | APD / CV / phase counts |
| 3 | `fig_phase_diagram` | λ×D inducibility (annulus, prefer full grid) |
| 4 | `fig_diffusion_compare` | div vs Laplace persist |
| 5 | `fig_mono2d_u` | 2D monodomain snapshot |

Regenerate: `python scripts/plot_science.py`

## Live numbers (2026-08-16 regenerate)

- pytest: 42 passed  
- APD₉₀: 256.6 ms  
- CV: 0.703125 mm/ms @ D=0.0465  
- Full phase diagram: **VA 3 / Non-VA 9** (`papers/data/phase_diagram.csv`, mode=full)
