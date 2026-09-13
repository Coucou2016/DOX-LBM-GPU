# Paper writing framework & outline

**One-sentence argument:** We provide an open, wavelength-aware 2D monodomain λ-Mitchell–Schaeffer **protocol/benchmark** with dual VA endpoints (`VA_paper` / `VA_cycle`), aligned to DOX-inspired literature choices—without claiming a 3D LBM–GPU digital-twin reproduction.

## Exemplar architectures

| # | Exemplar | Why imitate |
|---|----------|-------------|
| 1 | Villar-Valero et al., *J Physiol* 2025 (doi:10.1113/jp288819) + STACOM 2024 | Primary scientific target: parametric λ×D fibrosis scan, S1–S2, VA endpoint |
| 2 | Chabiniok & Zaha commentary (*J Physiol*, doi:10.1113/jp290313) | Translational framing: open the method |
| 3 | Campos et al., *Front Physiol* 2024 (doi:10.3389/fphys.2024.1370795) | Fibrosis-representation → VA morphology |
| 4 | *Sci. Rep.* 2024 fibrosis reentry (doi:10.1038/s41598-024-62002-5) | Induction vs observation windows |
| 5 | Niederer et al. 2011 | Verification culture |
| 6 | `javilva/doxorubicin_fibrosis_model` | Public cell model / params / sample anatomy |

## Recommended section map

1. **Title / Abstract** — protocol/benchmark claim (not twin reproduction)  
2. **Introduction** — DOX fibrosis → VA; gap = proprietary solver + wavelength mismatch on small discs  
3. **Related work** — twins, public cell model vs proprietary solver, phenomenological MS  
4. **Methods** — λ-MS; `div(D∇u)`; dual VA endpoints; annulus as **verification geometry**; verification suite  
5. **Results** — 0D APD; 2D CV; diffusion; dual-endpoint phase diagram; disc negative control  
6. **Discussion** — why 2D must not reproduce 3D inducibility (λ=0.2/0.3 + D↓90% discrepancy)  
7. **Code availability** — MIT, CITATION.cff, pytest gates  

## Defensible claims (and forbidden claims)

**Claim (yes):**
- Open 2D protocol/benchmark aligned to paper ionic/protocol choices  
- Dual VA endpoints (persist vs cycle-required)  
- Wavelength-aware annulus as verification geometry  
- Conservative diffusion with full-domain constant-D equivalence  

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
