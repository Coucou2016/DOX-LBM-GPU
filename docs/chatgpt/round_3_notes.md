# Round 3 — Results narrative

**Date:** 2026-08-16  
**GitHub:** https://github.com/Coucou2016/DOX-LBM-GPU  
**ChatGPT URL:** **无**（fallback advisor memo）

## Round question

Paste `phase_diagram.csv` numbers + figure list; ask Results structure and what not to overclaim.

## Evidence (regenerated this session)

### Validation / CV (live)

| Metric | Value | Source |
|--------|-------|--------|
| pytest | **42 passed** in 65.61 s | `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` |
| 0D APD₉₀ | **256.6 ms** | `cardiac_ms.validation` |
| Homogeneous CV | **0.703125 mm/ms** at D=0.0465 | validation + calibrate_cv |
| CV calibration D* | 0.046501 mm²/ms → CV 0.703 | `scripts/calibrate_cv.py` |
| Diffusion op max\|err\| | ~1.8e-15 (constant D) | validation |

### Fast annulus phase diagram (mode=fast, 2×2)

| λ | D reduction | label | persist_ms | n_extra_cycles | n_probes_relapped |
|---|-------------|-------|------------|----------------|-------------------|
| 0.01 | 0.3 | Non-VA | 394.7 | 0 | 0 |
| 0.01 | 0.9 | **VA** | 1000.0 | 2 | 3 |
| 0.3 | 0.3 | Non-VA | 0.0 | 0 | 0 |
| 0.3 | 0.9 | Non-VA | 0.0 | 0 | 0 |

Counts: **VA 1 / Non-VA 3**. Path ≈106.8 mm. τ_close=150 ms.

### Full 4×3 grid (completed this session)

**mode=full**, 12 cells, elapsed ≈159.5 s → **VA 3 / Non-VA 9**.

| λ | D↓30% | D↓70% | D↓90% |
|---|-------|-------|-------|
| 0.01 | Non-VA (persist 394.7; cycles 0) | **VA** (666.7; extra=1) | **VA** (1000; extra=2, relap=3) |
| 0.1 | **VA** (632.9; extra=1) | Non-VA | Non-VA |
| 0.2 | Non-VA | Non-VA | Non-VA |
| 0.3 | Non-VA | Non-VA | Non-VA |

Note: two VA cells have persist **<1000 ms** — confirms cycle-required rule (not persist-alone).

## Advisor memo (fallback)

### Results structure (accept)

1. Verification ladder first (0D APD → CV → diffusion operator).  
2. Then inducibility map (annulus).  
3. Then negative control (disc) + mechanism note (wavelength).  
4. End with what a single VA cell does **not** imply.

### Do not overclaim (enforce)

- Do **not** say “reproduces Villar-Valero inducibility fractions.”  
- Do **not** generalize one VA cell (λ=0.01, D↓90%) to DOX pig LV.  
- Do **not** call fast 2×2 “complete parametric study”; label **preliminary** until full grid lands.  
- Diffusion operator: persist can differ; if labels did not flip in the compared case, say so without claiming equivalence of operators.

## Implementation

- Results tables synced to regenerated numbers.  
- Fast vs full labeled honestly.  
- Figure captions: SciencePlots stems unchanged.
