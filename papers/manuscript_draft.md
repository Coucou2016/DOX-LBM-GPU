# A wavelength-aware 2D monodomain benchmark for auditable fibrosis–reentry protocols

English submission manuscript. Chinese draft: `papers/manuscript_zh.md`.

---

## Title

**A wavelength-aware 2D monodomain benchmark for auditable fibrosis–reentry protocols**

*(Dimensional / twin-reproduction boundary is stated in the Abstract and Limitations—not in the title.)*

---

## Abstract

**Background.** Doxorubicin (DOX)–associated diffuse fibrosis can create an arrhythmogenic substrate. Personalized 3D MRI-based left-ventricular models that couple a λ-modified Mitchell–Schaeffer (MS) ionic law to a GPU Lattice–Boltzmann (LBM) monodomain solver have mapped inducibility under fibrotic excitability and conduction changes. The cell model, parameters, and sample anatomy are publicly documented (e.g. `javilva/doxorubicin_fibrosis_model`), while the production LBM–GPU solver remains proprietary—blocking independent protocol audit on the closed twin pipeline.

**Methods.** We release an open CPU 2D finite-difference monodomain **protocol/benchmark** that implements the same λ-modified MS law, conservative diffusion \(\nabla\cdot(D\nabla u)\), three-class synthetic fibrosis tissue, and an S1–S2 stimulation train aligned with published coupling intervals. Homogeneous conduction velocity (CV) is calibrated to **≈0.70 mm/ms** (acceptance band 0.55–0.85) at \(D=0.0465\,\mathrm{mm}^2/\mathrm{ms}\). Time steps use **additive explicit Euler** (ionic + diffusion in one step; not operator splitting) with a diffusion CFL bound and an ionic upper limit of \(0.1\,\mathrm{ms}\). Default stimulus is **current injection** (`STIM_CURRENT_AMP`; voltage-clamp `STIM_VOLTAGE_CLAMP_U` remains available). We report **three VA endpoints**: `VA_paper` = persist ≥ 1000 ms **only** (Villar-Valero; never OR cycle); `VA_recurrence` (default `label`) = require re-excitation (extra≥1 or relapped≥3); `VA_strict` = persist ≥ 1000 **and** recurrent circulation. Optional 2D phase-singularity tip counts are auxiliary (not 3D filaments). Using classical MS APD₉₀ ≈256.6 ms, a design wavelength \(\mathrm{CV}\times\mathrm{APD}\approx0.70\times257\approx180\,\mathrm{mm}\) already exceeds small disc domains (~24 mm); literature CONTROL APD 309 ms implies an even larger wavelength (~219 mm). We therefore use a pinned annulus as a **verification geometry** designed via wavelength (path ≈107 mm), not as a biological discovery claim. This work is **not** a 3D LBM–GPU twin reproduction (Abstract / Limitations; not the title).

**Results.** Triple-endpoint counts on the annulus λ×D grid are reported from regenerated CSV (see Results tables; no hand-filled counts). Zero-dimensional APD₉₀ equals **256.6 ms** under the classical MS golden regression. The annulus is a wavelength-designed verification circuit; disc geometry remains a negative control.

**Conclusions.** The deliverable is an open methods and verification resource for protocol alignment and endpoint audit. It is **not** a 3D DOX twin, does **not** claim LBM–GPU performance or clinical ICD utility, and does **not** equate synthetic fibrosis with porcine DOX myocardium or ischemic MI.

**Keywords:** cardiac electrophysiology; Mitchell–Schaeffer; monodomain; fibrosis; reentry; reproducibility; doxorubicin (protocol alignment)

---

## 1. Introduction

Chemotherapy-related cardiotoxicity is often framed through declines in ejection fraction, yet tissue remodeling can also create a substrate for ventricular arrhythmia (VA). Anthracycline agents such as doxorubicin (DOX) promote reactive diffuse fibrosis; in silico models that combine image-derived anatomy with monodomain electrophysiology are attractive tools for probing how excitability and conduction interact with that substrate.

Villar-Valero et al. constructed personalized porcine left-ventricular (LV) models from MRI / late gadolinium enhancement and electro-anatomical mapping, coupled a λ-modified Mitchell–Schaeffer (MS) ionic model to a GPU Lattice–Boltzmann (LBM) monodomain solver, and performed a parametric inducibility scan under fibrotic excitability and conductivity changes (STACOM 2024; *J Physiol* 2026, doi:10.1113/jp288819). Public materials document the cell model and related assets (`javilva/doxorubicin_fibrosis_model`); the production solver used in the twin remains proprietary. Commentary by Chabiniok and Zaha (*J Physiol*, doi:10.1113/jp290313) argues that clinical translation requires methods that can be opened: reproducible and runnable outside a closed pipeline.

**Gap.** Independent groups cannot re-run the closed 3D twin. Separately, a nominal healthy wavelength \(\lambda_{\mathrm{wave}}\approx\mathrm{CV}\times\mathrm{APD}\approx175\,\mathrm{mm}\) cannot fit inside a small 2D disc (~24 mm), so disc-only inducibility grids collapse to all Non-VA for geometric—not physiological—reasons. A persist≥1000 ms rule alone can label plateau retention as VA; OR-ing cycle evidence into the paper endpoint conflates distinct criteria.

**Approach.** We build a testable 2D monodomain **benchmark** that (i) aligns the ionic law and S1–S2 extras with published protocol choices, (ii) reports three VA endpoints (`VA_paper` / `VA_recurrence` / `VA_strict`), and (iii) adopts a wavelength-aware pinned annulus as verification geometry. The deliverable is an open verification layer—not a substitute for a personalized 3D twin.

**Boundary.** Synthetic three-class fibrosis ≠ porcine DOX myocardium ≠ ischemic MI scar. 2D finite differences ≠ 3D LBM. This scaffold does **not** reproduce quantitative 3D pig-LV inducibility fractions. It is **not** a 3D LBM–GPU twin reproduction.

---

## 2. Related work

**DOX fibrosis models and commentary.** Villar-Valero et al. (doi:10.1113/jp288819; STACOM doi:10.1007/978-3-031-87756-8_7) provide the scientific target: parametric λ×D scans, S1–S2, and a VA endpoint on image-based LV geometries with modified MS + LBM–GPU. Chabiniok & Zaha (doi:10.1113/jp290313) supply the translational framing. Public cell-model materials enable ionic/protocol cross-checks without implying solver availability.

**Fibrosis representation and inducibility protocols.** Campos et al. (*Front Physiol* 2024, doi:10.3389/fphys.2024.1370795) show that fibrosis representation choices change VA morphology. Systematic fibrosis–reentry work (*Sci. Rep.* 2024, doi:10.1038/s41598-024-62002-5) separates induction and observation windows.

**Phenomenological MS lineage.** Classical MS (Mitchell & Schaeffer, 2003) remains a standard reduced ionic model. Djabella and colleagues introduced the excitability threshold λ used in the DOX twin literature. Corrado-style complete modified MS formulations are **not** identical to the λ-inward-current form implemented here.

**Verification culture.** Niederer et al. (2011, doi:10.1098/rsta.2011.0139) established N-version verification for tissue electrophysiology simulators. Our contribution sits in the methods niche: an open, pytest-gated protocol benchmark when the closed LBM twin cannot be re-run.

---

## 3. Methods

### 3.1 Task formulation

**Input.** Grid `(nx, ny, dx)`, healthy/fibrotic diffusion \(D\) and excitability \(\lambda\), S1–S2 timetable, tissue mask.  
**Output.** Transmembrane field \(u\), activation times, CV, triple VA labels, phase-diagram CSV.  
**Scope.** 2D monodomain on CPU. Out of scope: bidomain, Purkinje, patient fibers, 3D LV, LBM, clinical GUI.

### 3.2 Modified Mitchell–Schaeffer with λ

Membrane voltage \(u\) and recovery gate \(h\) obey

\[
\partial_t u = \nabla\cdot(D\nabla u) + \frac{h\,u(u-\lambda)(u_{\max}-u)}{\tau_{\mathrm{in}}} - \frac{u}{\tau_{\mathrm{out}}} + J_{\mathrm{stim}},
\]

\[
\partial_t h = \begin{cases}(1-h)/\tau_{\mathrm{open}} & u < u_{\mathrm{gate}} \\ -h/\tau_{\mathrm{close}} & \text{otherwise.}\end{cases}
\]

**Units.** Time in ms, length in mm; \(u\), \(h\), and \(\lambda\) are dimensionless. Healthy default \(\lambda=0.01\); fibrotic scan \(\lambda\in\{0.01,0.1,0.2,0.3\}\). When \(\lambda=0\) and \(u_{\max}=1\), a single ionic step matches `finitewave-model-mitchell-schaeffer` (unit-tested).

### 3.3 Conservative diffusion and CFL

Spatial diffusion uses face-averaged \(D\) so that the discrete operator approximates \(\nabla\cdot(D\nabla u)\). For spatially constant \(D\) the scheme matches \(D\nabla^2 u\) on the **full domain** including Neumann corners (regression-tested). Explicit time steps satisfy

\[
\Delta t \le \frac{\Delta x^2}{4\,D_{\max}}
\]

and an ionic ceiling \(\Delta t\le 0.1\,\mathrm{ms}\).

### 3.4 Tissue classes and stimuli

Tissue is labeled healthy / border / dense fibrosis (`border_width_mm` / `radius_mm` available alongside grid counts). Stimuli default to `stimulus_mode="current"` (`STIM_CURRENT_AMP`); `"voltage_clamp"` (`STIM_VOLTAGE_CLAMP_U`) remains available for legacy short regressions. Capture threshold \(J_c\) can be scanned (`scripts/scan_capture_threshold.py`); induction uses ≈1.5\(J_c\) when a measured \(J_c\) is available. Default S1: BCL = 400 ms, \(n=3\). Phenotype extras: CONTROL = none; DOX1 = 240/200/190 ms; DOX2 = 250×4. Induction and observation windows are separated (default observe 1000 ms). Annulus protocols place 8–16 ordered angular probes for direction / lap-period evidence.

### 3.5 Triple VA endpoints

| Endpoint | Rule |
|----------|------|
| `VA_paper` | Persist ≥ 1000 ms **only** (Villar-Valero; never OR cycle) |
| `VA_recurrence` | `n_extra_cycles ≥ 1` **or** `n_probes_relapped ≥ 3` (default `label`; alias `VA_cycle`) |
| `VA_strict` | Persist ≥ 1000 **and** recurrent circulation |

Plateau persistence alone is insufficient for `VA_recurrence` / `VA_strict`. A single-extras plateau negative control is locked in regression tests (`persist≥1000`, extra=0 → `VA_paper`=VA, `VA_strict`=Non-VA).

### 3.6 Wavelength-aware verification geometry

Design wavelength uses nominal APD = 250 ms:

\[
\lambda_{\mathrm{wave}} \approx \mathrm{CV}\times\mathrm{APD} \approx 0.70\times250 = 175\,\mathrm{mm}.
\]

A \(48^2\times0.5\,\mathrm{mm}\) disc (~24 mm) is a negative control. The pinned annulus (path ≈107 mm) is a **verification geometry** sized so that strongly slowed wavelengths can reenter while healthy wavelengths cannot—not a claim of biological discovery.

### 3.7 Verification suite

Gates: pytest; 0D APD golden regression; homogeneous 2D CV band; full-domain diffusion-operator consistency; fibrosis-free Non-VA; annulus dual-endpoint phase diagram. Spatial/temporal convergence tables (`data/dx_convergence.csv`, `data/dt_convergence.csv`) document numerical sensitivity of CV under dx∈{0.75,0.5,0.25} mm and dt∈{0.1,0.05,0.025} ms—verification only, not biology. Optional 2D phase-singularity / tip counts (`n_singularities`, `rotor_detected`) are auxiliary protocol metrics on the final (u,h) snapshot; they are **not** 3D filament tracking.

CONTROL/DOX1/DOX2 **literature targets** (Villar-Valero *J Physiol* 2026): healthy APD 309/269/210 ms (DOX shorter than CONTROL), fibrosis APD DOX1 276 / DOX2 184 ms, CV 0.71/0.41/0.4389 mm/ms. Calibrated model params (`tau_close`, `D`, `lam`) are fitted separately (`scripts/calibrate_phenotypes.py` → `data/phenotype_calibration.json`); `cv_matched` only within ±10% under stable CFL. Until calibrated, use names like `DOX1_target` — presets are not “literature numbers.”

### 3.8 Figure generation

Figures use SciencePlots (`science` + `no-latex`) via `scripts/plot_science.py` / `cardiac_ms/plotting.py`.

---

## 4. Results

### 4.1 0D action potential and APD

Classical MS (seed = 42) yields APD₉₀ = **256.6 ms** (tolerance ±8 ms). Figure: `papers/figures/fig_ms_0d_ap.pdf`.

![0D AP](figures/fig_ms_0d_ap.png)

### 4.2 Homogeneous 2D conduction velocity

After calibrating \(D=0.0465\,\mathrm{mm}^2/\mathrm{ms}\), two-point CV on a homogeneous sheet is ≈**0.70 mm/ms** (band 0.55–0.85). Distance uses Euclidean `hypot`. Summary: `fig_validation_summary`. dx and dt convergence tables (`data/dx_convergence.csv`, `data/dt_convergence.csv`) confirm CV stability under grid/time refinement (numerical verification).

![Validation](figures/fig_validation_summary.png)

### 4.3 Diffusion operator comparison

Under spatially varying \(D\), `div(D∇u)` versus `D∇²u` can shift activation persistence. Constant-\(D\) operators agree on the full domain including corners. Figure: `fig_diffusion_compare`.

![Diffusion](figures/fig_diffusion_compare.png)

### 4.4 Annulus inducibility phase diagram (verification geometry)

**Full 4×3 annulus grid** (DOX1-aligned extras 240/200/190 ms; \(\tau_{\mathrm{close}}=150\,\mathrm{ms}\); \(n_x=n_y=64\), \(\mathrm{d}x=0.75\,\mathrm{mm}\); path ≈106.8 mm; 12 angular probes; `stimulus_mode=current`; wall time ≈190 s). Source: `papers/data/phase_diagram.csv` (mode=`full`).

**Triple-endpoint summary (same 12 cells; regenerated after VA_paper persist-only fix):**

| Endpoint | VA | Non-VA |
|----------|---:|-------:|
| `VA_recurrence` (default `label`) | 3 | 9 |
| `VA_paper` (persist≥1000 **only**) | 1 | 11 |
| `VA_strict` (persist≥1000 **and** recurrence) | 1 | 11 |

`VA_paper` **changed** vs the prior dual-endpoint CSV (was 3/12 when paper OR-ed cycle evidence). After persist-only relabel, only the λ=0.01 / D↓90% cell meets persist≥1000 ms. Two recurrence-positive cells have persist < 1000 ms → `VA_paper`=Non-VA, `VA_recurrence`=VA. The single-premature plateau control still shows the complementary disagreement (persist≥1000, extra=0 → `VA_paper`=VA, `VA_recurrence`/`VA_strict`=Non-VA; regression-tested).

| λ | D↓30% | D↓70% | D↓90% |
|---|:-----:|:-----:|:-----:|
| 0.01 | Non-VA | **VA** | **VA** |
| 0.1 | **VA** | Non-VA | Non-VA |
| 0.2 | Non-VA | Non-VA | Non-VA |
| 0.3 | Non-VA | Non-VA | Non-VA |

(Heatmap uses default `label` = `VA_recurrence`.)

VA cell detail (from CSV; no fabricated statistics):

| λ | D reduction | persist_ms | n_extra_cycles | n_probes_relapped | VA_recurrence | VA_paper | VA_strict |
|---|-------------|------------|----------------|-------------------|---------------|----------|-----------|
| 0.01 | 0.7 | 666.6 | 1 | 5 | VA | Non-VA | Non-VA |
| 0.01 | 0.9 | 1000.0 | 2 | 9 | VA | VA | VA |
| 0.1 | 0.3 | 632.5 | 1 | 4 | VA | Non-VA | Non-VA |

At λ∈{0.2,0.3} all D reductions are Non-VA (functional block on the verification ring)—a geometric/excitability bound that already prevents matching a richer 3D inducibility map.

![Phase](figures/fig_phase_diagram.png)

**Interpretation bound.** The mixed diagram shows that geometry and endpoints are auditable on this scaffold. It does **not** claim reproduction of Villar-Valero 3D inducibility proportions.

### 4.5 Disc negative control

Small discs are expected to be all Non-VA (wavelength mismatch). Homogeneous snapshot: `fig_mono2d_u`.

![Mono2d](figures/fig_mono2d_u.png)

---

## 5. Discussion

**What we show.** An open, pytest-gated 2D protocol/benchmark; ionic/protocol choices aligned with the DOX fibrosis literature; triple VA endpoints; wavelength-aware verification geometry.

**What we do not claim.** “First DOX twin”; quantitative 3D pig-LV reproduction; LBM–GPU acceleration; clinical ICD decision support; equivalence of synthetic fibrosis to DOX myocardium or ischemic MI. This work is **not** a 3D LBM–GPU twin reproduction (stated here and in the Abstract, not in the title).

### 5.1 Why 2D must not reproduce the 3D inducibility map

A healthy design wavelength \(\lambda_{\mathrm{wave}}\approx0.70\times257\approx180\,\mathrm{mm}\) (classical MS APD₉₀; literature CONTROL 309 ms ⇒ ~219 mm) already exceeds typical small 2D discs (~24 mm). On the verification annulus (path ≈107 mm), D↓90% shortens wavelength enough that geometry can admit reentry, while D↓30% remains long relative to the path—so inducibility is dominated by **wavelength vs path**, not by the 3D maze corridors of porcine LGE. At high fibrotic λ (0.2–0.3), the ring approaches functional block and collapses toward Non-VA even when D is reduced. Therefore a 2D λ×D heatmap **cannot** and **should not** be expected to match 3D twin inducibility fractions; discrepancy with the paper’s 3D map is a geometric and dimensional bound, not a calibration failure of this benchmark.

This stance matches Chabiniok–Zaha’s call to open methods: the scaffold lowers the cost of **protocol reproduction and endpoint audit**, rather than replacing personalized 3D twins.

**Limitations.** Anisotropy remains a prototype; Zenodo porcine MI datasets were not ingested (and MI ≠ DOX); 1D CV for DOX phenotypes is not fully matched on this FD scaffold (documented in `cardiac_ms/phenotypes.py`).

---

## 6. Code and data availability

Public repository: **https://github.com/Coucou2016/DOX-LBM-GPU** (display name: Fibrosis-Reentry-MS2D).

Core package `cardiac_ms/`, tests `tests/`, phase diagram `scripts/run_phase_diagram.py` (`--full` for 4×3), figures `scripts/plot_science.py`. Curated phase CSV: `papers/data/phase_diagram.csv`. Synthetic metadata under `data/synthetic/`. External large datasets / MonoAlg3D only as pointers in `data/README.md`. License: MIT (`LICENSE`). Citation: `CITATION.cff`.

---

## 7. References

1. Villar-Valero JM (Javier), et al. In silico predictions of action potential propagation in doxorubicin cardiotoxicity: A parametric study using preclinical 3D magnetic resonance imaging-based fibrotic left ventricle models. *J Physiol.* 2026. doi:10.1113/jp288819  
2. Chabiniok R, Zaha VG. Cardiac digital twins: Modelling the arrhythmic substrate of chemotherapy. *J Physiol.* doi:10.1113/jp290313  
3. Commentary / perspective. A maze-like electrical substrate: arrhythmogenic vulnerability in doxorubicin-damaged ventricles. *J Physiol.* doi:10.1113/jp290582  
4. Villar-Valero et al. Exploring chemotherapy-induced cardiotoxicity combining a 3D computational model and preclinical cardiac imaging data. STACOM 2024. doi:10.1007/978-3-031-87756-8_7  
5. Mitchell CC, Schaeffer DG. A two-current model for the dynamics of cardiac membrane. *Bull Math Biol.* 2003;65:767–793.  
6. Niederer SA, et al. Verification of cardiac tissue electrophysiology simulators using an N-version benchmark. *Philos Trans A Math Phys Eng Sci.* 2011;369:4331–4351. doi:10.1098/rsta.2011.0139  
7. Campos FO, et al. Fibrosis representation and ventricular arrhythmia morphology. *Front Physiol.* 2024. doi:10.3389/fphys.2024.1370795  
8. Scientific Reports (2024). Systematic fibrosis–reentry protocol study. doi:10.1038/s41598-024-62002-5  
9. Djabella K, et al. Modified Mitchell–Schaeffer excitability parameter λ (lineage cited via Villar-Valero 2025).  
10. Public cell-model / anatomy materials: https://github.com/javilva/doxorubicin_fibrosis_model  

---

## Claim–evidence map

| Claim | Evidence | Status |
|-------|----------|--------|
| λ-MS matches package at λ=0 | unit test + validation | supported |
| 0D APD = 256.6 ms | golden regression + Fig.1 | supported |
| CV ≈ 0.70 mm/ms @ D=0.0465 | validation + calibrate_cv | supported |
| Full-domain constant-D operator match | diffusion tests | supported |
| Triple VA endpoints reported | protocol + phase CSV | supported |
| Literature CONTROL/DOX APD/CV targets | phenotypes.py + calibration JSON | supported (targets vs ±10% matched flags) |
| Open protocol/benchmark contribution | repo + pytest | supported (methods) |
| 3D DOX twin equivalence | — | **not claimed** |
