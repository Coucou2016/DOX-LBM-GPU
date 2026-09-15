# Changelog

## [Unreleased] — Round-3: close remaining P1/P2 tails

### Phase diagram / metrics
- Per-cell `apd0d_ms` and `R_path_over_CV_APD` (= path/(CV·APD); CV from two-point or path/lap_period) in phase-diagram CSV + summary.
- Ordered circulation: event-stream direction vote + median lap period; `n_lap_periods`; VA_strict cases expect CW/CCW + ≥2 lap gaps when probes re-fire.
- Anisotropy prototype: CFL uses `max(D_long, D_trans)`; isotropic-limit tests at θ=0°/90°.
- dx/dt convergence CSV: wavelength + annulus lap estimate + VA note pointing at curated phase CSV.
- `CITATION.cff`: software author Coucou2016; preferred-citation = this software; Villar-Valero (Javier, 2026) related reference.

### Docs
- ASSUMPTIONS anisotropy documented as prototype; deferred APD/R language removed from CHANGELOG/summary.

## [Unreleased] — Round-2 major revision (P0+P1)

### Triple VA endpoints
- `VA_paper`: persist ≥ 1000 ms **ONLY** (never OR cycle).
- `VA_recurrence`: confirmed extra cycle / ordered circulation (default `label`; `VA_cycle` alias).
- `VA_strict`: persist ≥ 1000 **and** recurrent circulation.
- Phase-diagram CSV/summary report all three; manuscript wording updated.
- Unit tests lock: persist=999+cycle→paper Non-VA; persist=1000+cycle=0→paper VA / strict Non-VA; both→strict VA.

### Phenotypes / protocols
- Literature TARGETS split from calibrated model params (`LITERATURE_TARGET` vs `CALIBRATED_MODEL` / `BENCHMARK_BASELINE`).
- Villar-Valero anchors (*J Physiol* 2026; Epub 2025): APD 309/269/210 (DOX shorter); fibrosis APD 276/184; CV 0.71/0.41/0.4389.
- CONTROL: **no** ectopic extras; DOX1: 240/200/190; DOX2: 250×4. No invented 260/220/200/180.
- Fixed CONTROL `d_reduction=0.0` falsy bug in `scripts/run_protocol_phenotype.py`.

### Docs / packaging
- Title: *A wavelength-aware 2D monodomain benchmark for auditable fibrosis–reentry protocols* (3D boundary in Abstract/Limitations).
- Chinese separated to `papers/manuscript_zh.md`; English manuscript cleaned.
- ASSUMPTIONS: additive Euler (not operator splitting); `data/README.md` drops local MonoAlg3D tree claim / absolute paths.
- `CITATION.cff`: preferred-citation is this software; related ref Javier Villar-Valero, year 2026 with Epub 2025 note.
- `.github/workflows/tests.yml` + `pyproject.toml` (`pip install -e .`).

### P1
- `STIM_VOLTAGE_CLAMP_U` / `STIM_CURRENT_AMP` (+ aliases); capture scan documents Jc and ~1.5 Jc induction.
- Annulus ordered angular probes default **12** (clamped 8–16); direction / lap period / complete laps → VA evidence.
- `border_width_mm` physical API; dx/dt convergence CSV includes 0D APD tissue metric.
- javilva λ∈{0.01,0.1,0.2,0.3} RHS cross-check green (machine-local paths sanitized in JSON).
- Per-cell APD / R=L/(CV·APD) shipped in phase CSV (see Round-3).

## [Unreleased] — Major Revision gap-closing (earlier P1)

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
- Removed machine-local absolute paths from `data/README.md`, `phase_diagram_summary.json`, javilva JSON note.

## [Unreleased] — Major Revision (peer-review P0)

### Scientific positioning
- Repositioned as an **open 2D protocol/benchmark** (wavelength-aware monodomain), not a 3D LBM–GPU digital-twin reproduction.
- Clarified: cell model / parameters / sample anatomy are public (`javilva/doxorubicin_fibrosis_model`); production solver remains proprietary.
- Display name: **Fibrosis-Reentry-MS2D** (GitHub remote name unchanged).

### Solver / metrics
- Constant-`D` path always uses `diffusion_div_D_grad_neumann`; Neumann Laplacian corners/edges fixed for full-domain equivalence.
- Dual VA endpoints (superseded by Round-2 triple endpoints above).
- `estimate_cv_from_activation` uses Euclidean `hypot` distance.
- Optional `stimulus_mode="current"|"voltage_clamp"` (default current).

### Packaging / tests
- MIT `LICENSE`, `CITATION.cff`, split `requirements.txt` / `requirements-dev.txt`.
- Pytest no longer blanket-ignores all warnings; restitution test asserts APD monotonic in `tau_out`.
- Full-domain diffusion tests: corners defined, constant field zero, operator equivalence.
