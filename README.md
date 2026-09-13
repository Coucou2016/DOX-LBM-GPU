# Fibrosis-Reentry-MS2D

**Also known as:** DOX-LBM-GPU (GitHub repository name unchanged)  
**Public repo:** https://github.com/Coucou2016/DOX-LBM-GPU

Open **2D monodomain protocol / benchmark** for wavelength-aware fibrosis–reentry studies, inspired by Villar-Valero et al. (STACOM 2024 / *J Physiol* 2025) doxorubicin (DOX) fibrosis work. This is a **protocol-aligned verification scaffold**, not a 3D LBM–GPU reproduction and **not** a DOX digital twin.

> **Credibility bound:** CPU **2D finite-difference monodomain** ≠ 3D LBM; synthetic fibrosis ≠ porcine DOX myocardium ≠ ischemic MI. Quantitative goals are equation/protocol alignment, CV order of magnitude, and auditable VA endpoints.

### What is public vs proprietary

| Asset | Status |
|-------|--------|
| Cell model / parameters / sample anatomy | Public — see [`javilva/doxorubicin_fibrosis_model`](https://github.com/javilva/doxorubicin_fibrosis_model) |
| Production 3D LBM–GPU twin solver | Proprietary (not released as source) |
| This repo | Open 2D FD monodomain + S1–S2 + dual VA endpoints |

## Quick start

```bash
git clone https://github.com/Coucou2016/DOX-LBM-GPU.git
cd DOX-LBM-GPU
pip install -r requirements.txt
# optional figures / pytest:
# pip install -r requirements-dev.txt

python demo_ms_0d.py
python demo_mono2d.py --no-fibrosis
python scripts/calibrate_cv.py
python scripts/generate_synthetic_data.py

# Phase diagram (pinned annulus verification geometry)
python scripts/run_phase_diagram.py
python scripts/run_phase_diagram.py --geometry disc   # negative control
python scripts/run_phase_diagram.py --full            # 4×3 grid

python scripts/run_smoke.py
python -m cardiac_ms.validation

# Windows PowerShell:
# $env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/ -q
```

Outputs go to `outputs/` (gitignored).

## Protocol alignment (P0)

| Item | This scaffold | Literature target |
|------|---------------|-------------------|
| Ionic model | Modified MS: \(J_\mathrm{in}=h\,u(u-\lambda)(u_\max-u)/\tau_\mathrm{in}\) | Same lineage (Djabella 2007) |
| Healthy λ | 0.01 | 0.01 |
| Fibrotic λ scan | {0.01, 0.1, 0.2, 0.3} | Same |
| Diffusion | Conservative `div(D∇u)` | Monodomain (LBM in twin) |
| Healthy CV | Two-point ≈**0.70 mm/ms** (D=0.0465 mm²/ms) | Fiber ≈0.7 m/s |
| S1 | BCL=400 ms, n=3 | Same |
| **VA_paper** | Persist ≥ 1000 ms | Villar-Valero |
| **VA_cycle** (default `label`) | extra≥1 **or** `n_probes_relapped`≥3 | Hardened endpoint |
| Geometry | Wavelength-designed **pinned annulus** (verification), disc = negative control | 3D LV (not reproduced) |

## Dual VA endpoints

Every S1–S2 / phase-diagram cell reports both:

- `VA_paper` — literature persist ≥ 1000 ms rule  
- `VA_cycle` — cycle-required (default classification / `label`)

CSV columns include `VA_paper`, `VA_cycle`, `va_paper`, `va_cycle`.

## Reproduce checks

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/ -q
python -m cardiac_ms.validation
python scripts/calibrate_cv.py
python scripts/generate_synthetic_data.py
python scripts/run_phase_diagram.py
python scripts/run_phase_diagram.py --full
python scripts/compare_diffusion_operators.py
python scripts/run_dx_convergence.py
python scripts/run_protocol_phenotype.py DOX1
```

## Layout

| Path | Role |
|------|------|
| `cardiac_ms/` | λ-MS, 2D monodomain, geometries, tissue, protocol, metrics |
| `cardiac_ms/phenotypes.py` | CONTROL / DOX1 / DOX2 literature-target presets |
| `scripts/run_phase_diagram.py` | Inducibility CSV + heatmap (dual endpoints) |
| `scripts/run_dx_convergence.py` | Minimal dx CV report |
| `data/README.md` | Zenodo / openCARP / MonoAlg3D pointers |
| `docs/ASSUMPTIONS.md` | Units, CFL, wavelength limits |
| `papers/` | Manuscript draft + figures |
| `reports/` | Research notes / HTML reports |
| `LICENSE` | MIT |
| `CITATION.cff` | Citation metadata |

### Optional local trees (not in the public clone)

`MonoAlg3D_C-master/` may exist on some developer machines for offline comparison; it is **not** required and is excluded from the public GitHub tree.

## Environment notes

| Component | Notes |
|-----------|-------|
| Python | 3.13.x tested |
| `finitewave-model-mitchell-schaeffer` | Install from `requirements.txt` |
| Full `finitewave` | Often breaks on Windows (numpy/MSVC) — do not install |
| CUDA / LBM-GPU | Not required; production twin solver is proprietary |

## Citation

See `CITATION.cff`. Primary scientific target:

- Villar-Valero et al., *J Physiol* 2025 (doi:10.1113/jp288819); STACOM 2024  
- Djabella, Landau & Sorine (2007); Mitchell & Schaeffer (2003)  
- Public cell-model reference: `javilva/doxorubicin_fibrosis_model`
