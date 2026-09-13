# Changelog

## [Unreleased] — Major Revision gap-closing (P1)

### Phase singularity / rotor tip (auxiliary)
- Added `cardiac_ms/phase_singularity.py`: 2D phase from (u,h) plane (optional Hilbert); topological-charge tip detection.
- `run_s1s2` / annulus meta now include `n_singularities` and `rotor_detected` (2D tip audit only; not 3D filaments).

### Phenotype calibration
- CONTROL/DOX1/DOX2 targets aligned to Villar-Valero healthy-tissue APD (309/269/210 ms) and CV (71/41/≈44 cm/s).
- `scripts/calibrate_phenotypes.py` → `data/phenotype_calibration.json`; `cv_matched` only within ±10% + stable CFL.

### Numerical verification
- `scripts/run_dx_convergence.py` sweeps dx and dt; writes `data/dx_convergence.csv` and `data/dt_convergence.csv`.

### API / hygiene
- `simulate_mono2d` default `stimulus_mode="current"` (was voltage_clamp).
- Abstract dual-endpoint wording clarified (`VA_paper` = persist≥1000 **or** cycle; `VA_cycle` = require cycle).
- Removed machine-local absolute paths from `data/README.md`, `phase_diagram_summary.json`, javilva JSON note.

## [Unreleased] — Major Revision (peer-review P0)

### Scientific positioning
- Repositioned as an **open 2D protocol/benchmark** (wavelength-aware monodomain), not a 3D LBM–GPU DOX digital-twin reproduction.
- Clarified: cell model / parameters / sample anatomy are public (`javilva/doxorubicin_fibrosis_model`); production solver remains proprietary.
- Display name: **Fibrosis-Reentry-MS2D** (GitHub remote name unchanged).

### Solver / metrics
- Constant-`D` path always uses `diffusion_div_D_grad_neumann`; Neumann Laplacian corners/edges fixed for full-domain equivalence.
- Dual VA endpoints: `VA_paper` (persist ≥ 1000 ms **or** cycle evidence) and `VA_cycle` (require_cycle); phase-diagram CSV reports both.
- `estimate_cv_from_activation` uses Euclidean `hypot` distance.
- Optional `stimulus_mode="current"|"voltage_clamp"` (default current).

### Packaging / tests
- MIT `LICENSE`, `CITATION.cff`, split `requirements.txt` / `requirements-dev.txt`.
- Pytest no longer blanket-ignores all warnings; restitution test asserts APD monotonic in `tau_out`.
- Full-domain diffusion tests: corners defined, constant field zero, operator equivalence.
