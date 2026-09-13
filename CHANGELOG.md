# Changelog

## [Unreleased] — Major Revision (peer-review P0)

### Scientific positioning
- Repositioned as an **open 2D protocol/benchmark** (wavelength-aware monodomain), not a 3D LBM–GPU DOX digital-twin reproduction.
- Clarified: cell model / parameters / sample anatomy are public (`javilva/doxorubicin_fibrosis_model`); production solver remains proprietary.
- Display name: **Fibrosis-Reentry-MS2D** (GitHub remote name unchanged).

### Solver / metrics
- Constant-`D` path always uses `diffusion_div_D_grad_neumann`; Neumann Laplacian corners/edges fixed for full-domain equivalence.
- Dual VA endpoints: `VA_paper` (persist ≥ 1000 ms) and `VA_cycle` (require_cycle); phase-diagram CSV reports both.
- `estimate_cv_from_activation` uses Euclidean `hypot` distance.
- Optional `stimulus_mode="current"|"voltage_clamp"` (induction scripts prefer current).

### Packaging / tests
- MIT `LICENSE`, `CITATION.cff`, split `requirements.txt` / `requirements-dev.txt`.
- Pytest no longer blanket-ignores all warnings; restitution test asserts APD monotonic in `tau_out`.
- Full-domain diffusion tests: corners defined, constant field zero, operator equivalence.
