# Paper writing framework & outline

**Axes (nature-writing):** `task=manuscript` · `paper_type=methods` · `language=zh-to-en working draft` · `journal=generic` (methods-journal target; not flagship *Nature*)  
**One-sentence argument:** In the absence of the original LBM–GPU solver, we show that a reproducible 2D monodomain λ-Mitchell–Schaeffer pipeline with cycle-required reentry metrics and wavelength-aware geometry recovers paper-aligned CV and mixed VA/Non-VA inducibility maps, without claiming a 3D DOX digital twin.

## Exemplar architectures to imitate (literature survey)

> **Advisor note:** Cursor 内置浏览器无法维持 ChatGPT 标签，对话 URL **未建立**。下表由本地 WebSearch（2026-08-16）独立检索并经判断采纳；用户仍可将 `docs/chatgpt/2026-08-16_paper_framework_task.md` 粘贴到已登录 ChatGPT（web search ON）复核。

| # | Exemplar | Why imitate |
|---|----------|-------------|
| 1 | Villar-Valero et al., *J Physiol* 2025 (doi:10.1113/jp288819) + STACOM 2024 | Primary scientific target: parametric λ×D fibrosis scan, S1–S2, VA endpoint; modified MS + LBM–GPU twin |
| 2 | Chabiniok & Zaha commentary (*J Physiol*, doi:10.1113/jp290313) | Translational framing: open the method, personalizable MS, clinical distance |
| 3 | Campos et al., *Front Physiol* 2024 (doi:10.3389/fphys.2024.1370795) | Fibrosis-representation choice → VA morphology; openCARP monodomain inducibility ladder |
| 4 | Biasi et al. CardioMat, *Comput Biol Med* 2024 (doi:10.1016/j.compbiomed.2024.109529) | Methods/toolbox paper architecture: pipeline → verification → application bounds |
| 5 | Arevalo / Zahid-style fibrosis–reentry + openCARP verification culture | Results ladder: validation → inducibility map → mechanism (wavelength) → limits |

## Recommended section map (methods + mechanism)

1. **Title / Abstract (EN)** — bounded methods claim  
2. **Introduction** — DOX fibrosis → VA; gap = closed LBM source + wavelength mismatch on small discs  
3. **Related work** — twins, LBM vs FD, phenomenological MS  
4. **Methods** — λ-MS; `div(D∇u)`; tissue classes; S1–S2; *require_cycle* VA; annulus geometry; verification suite  
5. **Results** — 0D APD; 2D CV; diffusion operator; annulus phase diagram; disc negative control  
6. **Discussion** — honest novelty; Chabiniok–Zaha “open the method”; what 2D cannot do  
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
| 3 | `fig_phase_diagram` | λ×D inducibility (annulus) |
| 4 | `fig_diffusion_compare` | div vs Laplace persist |
| 5 | `fig_mono2d_u` | 2D monodomain snapshot |

Regenerate: `python scripts/plot_science.py`
