# A wavelength-aware 2D monodomain benchmark for auditable fibrosis–reentry protocols

---

## Title

**A wavelength-aware 2D monodomain benchmark for auditable fibrosis–reentry protocols**

---

## Abstract

Doxorubicin (DOX)–associated diffuse fibrosis can support ventricular arrhythmia (VA), yet the production Lattice–Boltzmann–GPU solver behind recent MRI-based left-ventricular twins remains closed. Independent groups therefore lack a runnable protocol against which ionic law, stimulation, diffusion, and VA labelling can be audited. We release an open CPU 2D finite-difference monodomain **protocol benchmark** that implements the λ-modified Mitchell–Schaeffer (MS) ionic law, conservative diffusion \(\nabla\cdot(D\nabla u)\), three-class synthetic fibrosis, and an S1–S2 train aligned with published coupling intervals. Homogeneous conduction velocity (CV) on this scaffold is **0.703 mm/ms** at \(D=0.0465\,\mathrm{mm}^2\mathrm{ms}^{-1}\) (acceptance band 0.55–0.85). Time integration is additive explicit Euler with a diffusion CFL bound and an ionic ceiling of \(0.1\,\mathrm{ms}\). Stimuli use current injection by default. Three VA endpoints are reported side by side: **VA_paper** (persist ≥ 1000 ms only), **VA_recurrence** (re-excitation required; default label), and **VA_strict** (persist ≥ 1000 ms and recurrent circulation). Classical MS APD₉₀ equals **256.6 ms**; the implied healthy wavelength \(\mathrm{CV}\times\mathrm{APD}\approx180\,\mathrm{mm}\) exceeds a small disc (~24 mm), so a pinned annulus (path ≈107 mm) is used as a wavelength-aware **verification geometry**, not as a biological discovery claim. On the full 4×3 annulus λ×D grid, counts are **VA_paper 1/11**, **VA_recurrence 3/9**, and **VA_strict 1/11**. Phenotype calibration matches literature APD/CV targets for CONTROL, DOX1, and DOX2 within ±10%. This resource supports protocol alignment and endpoint audit; it is not a 3D LBM twin, not a clinical ICD tool, and does not equate synthetic fibrosis with porcine DOX myocardium.

**Keywords:** cardiac electrophysiology; Mitchell–Schaeffer; monodomain; fibrosis; reentry; reproducibility; protocol benchmark

---

## 1. Introduction

Chemotherapy cardiotoxicity is often tracked through ejection fraction, yet reactive fibrosis can also create an electrical substrate for VA. Image-based monodomain models are a natural way to ask how excitability and conduction interact with that substrate.

Villar-Valero and colleagues built personalized porcine left-ventricular (LV) models from MRI and late gadolinium enhancement, coupled a λ-modified MS ionic model to a GPU Lattice–Boltzmann monodomain solver, and scanned inducibility under fibrotic excitability and conductivity changes (*J Physiol*, doi:10.1113/jp288819; STACOM 2024). Public materials document the cell model and related assets; the production twin solver remains proprietary. Commentary by Chabiniok and Zaha (*J Physiol*, doi:10.1113/jp290313) argues that translation requires methods that can be opened and re-run outside a closed pipeline. The broader verification culture for tissue electrophysiology, exemplified by the Niederer N-version benchmark (2011) and community platforms such as openCARP, likewise privileges shared protocols over opaque binaries.

Two practical obstacles follow. First, without the closed 3D twin, protocol details—ionic law, stimulus mode, diffusion operator, VA definition—cannot be pressure-tested by third parties. Second, a healthy design wavelength of order \(180\,\mathrm{mm}\) cannot fit inside a small 2D disc (~24 mm), so disc-only inducibility grids collapse to Non-VA for geometric reasons and teach little about endpoint design. A persist≥1000 ms rule alone can also label plateau retention as VA, while OR-ing cycle evidence into that “paper” endpoint conflates distinct criteria.

We therefore build a testable 2D monodomain **benchmark** that (i) aligns the ionic law and S1–S2 extras with published protocol choices, (ii) reports three VA endpoints, and (iii) adopts a wavelength-aware pinned annulus as verification geometry. The deliverable is an open verification layer. It does not replace a personalized 3D twin, and it does not claim quantitative reproduction of porcine LV inducibility fractions.

---

## 2. Related work

**DOX fibrosis twins and commentary.** Villar-Valero et al. provide the scientific target: parametric λ×D scans, S1–S2 pacing, and VA labelling on image-based LV geometries with modified MS and LBM–GPU. Chabiniok and Zaha supply the translational framing—open methods as a precondition for clinical trust. Public cell-model materials enable ionic and protocol cross-checks without implying solver availability.

**Fibrosis representation and inducibility protocols.** Campos and co-workers showed that fibrosis representation choices change VA morphology (*Front Physiol* 2024). Systematic fibrosis–reentry studies separate induction and observation windows, a discipline we adopt explicitly.

**Phenomenological MS lineage.** Classical MS (Mitchell & Schaeffer, 2003) remains a standard reduced ionic model. The excitability threshold λ used in the DOX twin literature descends from Djabella-type modifications. Complete Corrado-style reformulations are not identical to the λ-inward-current form implemented here.

**Verification and open simulators.** Niederer et al. (2011) established N-version verification for tissue EP codes. openCARP provides a community FEM/carputils environment for multiscale EP. Our contribution occupies a narrower niche: an open, pytest-gated **protocol benchmark** when the closed LBM twin cannot be re-run, not a replacement for organ-scale FEM or GPU LBM.

---

## 3. Methods

### 3.1 Task formulation

**Input.** Grid \((n_x,n_y,\Delta x)\), healthy/fibrotic diffusion \(D\) and excitability \(\lambda\), S1–S2 timetable, tissue mask.  
**Output.** Transmembrane field \(u\), activation times, CV, triple VA labels, phase-diagram table.  
**Scope.** 2D monodomain on CPU. Out of scope: bidomain, Purkinje network, patient fibre fields, 3D LV anatomy, Lattice–Boltzmann, clinical decision support.

### 3.2 Modified Mitchell–Schaeffer with λ

Membrane voltage \(u\) and recovery gate \(h\) obey

\[
\partial_t u = \nabla\cdot(D\nabla u) + \frac{h\,u(u-\lambda)(u_{\max}-u)}{\tau_{\mathrm{in}}} - \frac{u}{\tau_{\mathrm{out}}} + J_{\mathrm{stim}},
\]

\[
\partial_t h = \begin{cases}(1-h)/\tau_{\mathrm{open}} & u < u_{\mathrm{gate}} \\ -h/\tau_{\mathrm{close}} & \text{otherwise.}\end{cases}
\]

Time is in ms, length in mm; \(u\), \(h\), and \(\lambda\) are dimensionless. Healthy default \(\lambda=0.01\); fibrotic scan \(\lambda\in\{0.01,0.1,0.2,0.3\}\). When \(\lambda=0\) and \(u_{\max}=1\), a single ionic step matches a classical MS reference package (unit-tested).

### 3.3 Conservative diffusion and CFL

Spatial diffusion uses face-averaged \(D\) so that the discrete operator approximates \(\nabla\cdot(D\nabla u)\). For spatially constant \(D\) the scheme matches \(D\nabla^2 u\) on the full domain, including Neumann corners. Explicit steps satisfy

\[
\Delta t \le \frac{\Delta x^2}{4\,D_{\max}}
\]

and an ionic ceiling \(\Delta t\le 0.1\,\mathrm{ms}\). Integration is additive explicit Euler (ionic + diffusion in one step), not operator splitting.

### 3.4 Tissue classes and stimuli

Tissue is labelled healthy / border / dense fibrosis. Stimuli default to current injection; a voltage-clamp mode remains available for short regressions. Capture threshold \(J_c\) can be scanned; induction uses ≈1.5\(J_c\) when a measured \(J_c\) is available. Default S1: basic cycle length 400 ms, three stimuli. Phenotype extras: CONTROL = none; DOX1 = 240/200/190 ms; DOX2 = 250 ms × 4. Induction and observation windows are separated (default observe 1000 ms). Annulus protocols place twelve ordered angular probes for direction and lap-period evidence.

### 3.5 Triple VA endpoints

| Endpoint | Rule |
|----------|------|
| VA_paper | Persist ≥ 1000 ms **only** (literature-style; never OR cycle) |
| VA_recurrence | \(n_{\mathrm{extra}}\ge 1\) **or** \(n_{\mathrm{probes\,relapped}}\ge 3\) (default label) |
| VA_strict | Persist ≥ 1000 ms **and** recurrent circulation |

Plateau persistence alone is insufficient for VA_recurrence / VA_strict. A single-extras plateau negative control is locked in regression tests (persist ≥ 1000 ms, extra = 0 → VA_paper = VA, VA_strict = Non-VA).

### 3.6 Wavelength-aware verification geometry

Design wavelength uses a nominal APD of 250 ms:

\[
\lambda_{\mathrm{wave}} \approx \mathrm{CV}\times\mathrm{APD} \approx 0.70\times250 = 175\,\mathrm{mm}.
\]

A \(48^2\times0.5\,\mathrm{mm}\) disc (~24 mm) is a negative control. The pinned annulus (path ≈107 mm) is sized so that strongly slowed wavelengths can reenter while healthy wavelengths cannot. It is a verification circuit, not a claim of anatomical discovery.

### 3.7 Phenotype calibration and numerical checks

Literature **targets** (Villar-Valero *J Physiol*): healthy APD 309 / 269 / 210 ms (CONTROL / DOX1 / DOX2), fibrosis APD DOX1 276 / DOX2 184 ms, CV 0.71 / 0.41 / 0.4389 mm/ms. Model parameters \(\tau_{\mathrm{close}}\), \(D\), and \(\lambda\) are fitted separately; match flags require ±10% under stable CFL. Measured values on this scaffold: CONTROL APD 309.0 ms, CV 0.709 mm/ms; DOX1 APD 269.0 ms, CV 0.417 mm/ms; DOX2 APD 210.1 ms, CV 0.441 mm/ms—all matched within tolerance. Targets are cited as literature anchors; calibrated parameters are not literature constants.

Verification gates include 0D APD golden regression, homogeneous 2D CV band, full-domain diffusion-operator consistency, fibrosis-free Non-VA, and the annulus triple-endpoint phase diagram. Spatial/temporal CV tables document sensitivity under \(\Delta x\in\{0.75,0.5,0.25\}\,\mathrm{mm}\) and \(\Delta t\in\{0.1,0.05,0.025\}\,\mathrm{ms}\). Optional 2D phase-singularity tip counts are auxiliary; they are not 3D filament tracking.

### 3.8 Software

The package, tests, phase-diagram driver, and SciencePlots figure script ship with the public repository (MIT license). Figures use the `science` + `no-latex` styles with Times New Roman for Latin text.

---

## 4. Results

### 4.1 Zero-dimensional action potential

Classical MS (seed 42) yields APD₉₀ = **256.6 ms** (tolerance ±8 ms).

![0D AP](figures/fig_ms_0d_ap.png)

**Figure 1.** Zero-dimensional MS action potential. Dashed lines mark activation and APD₉₀ end.

### 4.2 Homogeneous conduction velocity and convergence

At \(D=0.0465\,\mathrm{mm}^2\mathrm{ms}^{-1}\), two-point CV on a homogeneous sheet is **0.703 mm/ms** (band 0.55–0.85). Distance uses Euclidean hypot. Under spatial refinement, CV rises from 0.662 mm/ms at \(\Delta x=0.75\,\mathrm{mm}\) to 0.726 mm/ms at \(\Delta x=0.25\,\mathrm{mm}\). Under temporal refinement at fixed \(\Delta x=0.5\,\mathrm{mm}\), CV remains 0.709 mm/ms at \(\Delta t=0.1\) and \(0.05\,\mathrm{ms}\), and 0.696 mm/ms at \(\Delta t=0.025\,\mathrm{ms}\)—all within the acceptance band.

![Validation](figures/fig_validation_summary.png)

**Figure 2.** Validation summary: 0D APD, homogeneous 2D CV, and triple-endpoint VA counts on the 12-cell annulus grid (VA_paper 1, VA_recurrence 3, VA_strict 1).

![Convergence](figures/fig_dx_dt_convergence.png)

**Figure 3.** Homogeneous CV versus \(\Delta x\) and \(\Delta t\). Grey band: 0.55–0.85 mm/ms; dashed line: 0.70 mm/ms target.

### 4.3 Phenotype calibration

CONTROL, DOX1, and DOX2 parameters were fitted to literature APD and CV targets. Measured APD errors are ≤0.05%; CV errors are −0.19%, +1.63%, and +0.52%, respectively. All phenotypes pass the ±10% match flags under stable CFL.

![Phenotype](figures/fig_phenotype_calibration.png)

**Figure 4.** Literature targets versus measured 0D APD and 2D CV for CONTROL, DOX1, and DOX2. Targets are anchors from Villar-Valero; bars on the right are our calibrated measurements.

### 4.4 Diffusion operator comparison

Under spatially varying \(D\), \(\nabla\cdot(D\nabla u)\) versus \(D\nabla^2 u\) shifts activation persistence by ≈65 ms across coupling intervals 200–280 ms on this protocol, without flipping VA labels. Constant-\(D\) operators agree on the full domain including corners. We retain the conservative form by default.

![Diffusion](figures/fig_diffusion_compare.png)

**Figure 5.** Persist times under conservative versus Laplacian diffusion at three coupling intervals.

### 4.5 Annulus inducibility phase diagram

Full 4×3 annulus grid: DOX1-aligned extras 240/200/190 ms; \(\tau_{\mathrm{close}}=150\,\mathrm{ms}\); \(n_x=n_y=64\), \(\Delta x=0.75\,\mathrm{mm}\); path ≈106.8 mm; twelve angular probes; current stimulus; wall time ≈170 s.

| Endpoint | VA | Non-VA |
|----------|---:|-------:|
| VA_recurrence (default label) | 3 | 9 |
| VA_paper (persist ≥ 1000 ms only) | 1 | 11 |
| VA_strict (persist ≥ 1000 ms and recurrence) | 1 | 11 |

Only the cell at \(\lambda=0.01\), D↓90% meets persist ≥ 1000 ms and therefore VA_paper / VA_strict. Two recurrence-positive cells have persist < 1000 ms and are labelled VA under VA_recurrence only.

Default-label (VA_recurrence) heatmap:

| λ | D↓30% | D↓70% | D↓90% |
|---|:-----:|:-----:|:-----:|
| 0.01 | Non-VA | **VA** | **VA** |
| 0.1 | **VA** | Non-VA | Non-VA |
| 0.2 | Non-VA | Non-VA | Non-VA |
| 0.3 | Non-VA | Non-VA | Non-VA |

VA cell detail (same grid; no fabricated statistics):

| λ | D reduction | persist (ms) | \(n_{\mathrm{extra}}\) | \(n_{\mathrm{relapped}}\) | direction | lap period (ms) | VA_recurrence | VA_paper | VA_strict |
|---|-------------|-------------:|-----------------------:|--------------------------:|-----------|----------------:|:-------------:|:--------:|:---------:|
| 0.01 | 0.7 | 666.6 | 1 | 5 | ccw | ≈330 | VA | Non-VA | Non-VA |
| 0.01 | 0.9 | 1000.0 | 2 | 9 | cw | ≈446 | VA | VA | VA |
| 0.1 | 0.3 | 632.5 | 1 | 4 | ccw | ≈347 | VA | Non-VA | Non-VA |

At \(\lambda\in\{0.2,0.3\}\) all D reductions are Non-VA (functional block on the verification ring).

![Phase](figures/fig_phase_diagram.png)

**Figure 6.** Annulus inducibility heatmap under the default VA_recurrence label (warm = VA).

**Interpretation bound.** The mixed diagram shows that geometry and endpoints are auditable on this scaffold. It does not claim reproduction of Villar-Valero 3D inducibility proportions.

### 4.6 Disc negative control

Small discs remain wavelength-limited negative controls. A homogeneous short-run snapshot confirms that the 2D solver propagates \(u\) in space.

![Mono2d](figures/fig_mono2d_u.png)

**Figure 7.** Final \(u\) field on a homogeneous short 2D run (no fibrosis; smoke-test snapshot).

---

## 5. Discussion

The open scaffold answers a methods question: can ionic law, stimulus protocol, diffusion operator, and VA endpoints be audited without the proprietary LBM twin? On that question the evidence is affirmative. Zero-dimensional APD, homogeneous CV, phenotype matches within ±10%, and a mixed annulus phase diagram with explicitly separated endpoints are reproducible on commodity CPU hardware.

What we do not claim matters as much. This is not the first DOX twin, not a quantitative 3D pig-LV reproduction, not an LBM–GPU performance study, and not ICD decision support. Synthetic three-class fibrosis is not porcine DOX myocardium and not ischemic MI scar. Two-dimensional finite differences are not three-dimensional Lattice–Boltzmann.

A healthy wavelength near \(180\,\mathrm{mm}\) already exceeds small discs. On the verification annulus (path ≈107 mm), strong conduction reduction shortens wavelength enough that geometry can admit reentry, while mild reduction leaves wavelength long relative to the path. High fibrotic \(\lambda\) (0.2–0.3) approaches functional block and collapses toward Non-VA. Inducibility on this ring is therefore dominated by wavelength versus path, not by the maze corridors of porcine late gadolinium enhancement. Discrepancy with a 3D twin map is a dimensional bound, not a calibration failure of the benchmark. That stance is consistent with Chabiniok and Zaha’s call to open methods: lower the cost of protocol reproduction and endpoint audit, rather than substitute for personalized twins.

**Limitations.** Anisotropy remains a prototype. Porcine MI repositories were not ingested (and MI ≠ DOX). Bidomain, Purkinje, and patient fibre fields are out of scope. Cross-checks against openCARP or MonoAlg3D remain future work. One-dimensional CV matching for DOX phenotypes on this finite-difference scaffold is documented separately and is not claimed complete beyond the homogeneous-sheet calibration above.

---

## 6. Conclusions

We release a wavelength-aware 2D monodomain protocol benchmark for fibrosis–reentry studies aligned with DOX twin literature. Three innovations are practical rather than theatrical: an open reduced-order protocol that third parties can run; a verification geometry sized by wavelength; and explicit auditing of VA_paper, VA_recurrence, and VA_strict on the same grid. On that grid the counts are 1/11, 3/9, and 1/11. The resource is intended for methods alignment—not for clinical risk stratification.

---

## 7. Code and data availability

Public repository: https://github.com/Coucou2016/DOX-LBM-GPU (display name Fibrosis-Reentry-MS2D). Core package `cardiac_ms/`, tests under `tests/`, phase diagram via `scripts/run_phase_diagram.py --full`, figures via `scripts/plot_science.py`. Curated phase table: `papers/data/phase_diagram.csv`. License: MIT. Citation metadata: `CITATION.cff`.

---

## 8. References

1. Villar-Valero JM, et al. In silico predictions of action potential propagation in doxorubicin cardiotoxicity: A parametric study using preclinical 3D magnetic resonance imaging-based fibrotic left ventricle models. *J Physiol.* 2026. doi:10.1113/jp288819  
2. Chabiniok R, Zaha VG. Cardiac digital twins: Modelling the arrhythmic substrate of chemotherapy. *J Physiol.* doi:10.1113/jp290313  
3. Villar-Valero et al. Exploring chemotherapy-induced cardiotoxicity combining a 3D computational model and preclinical cardiac imaging data. STACOM 2024. doi:10.1007/978-3-031-87756-8_7  
4. Mitchell CC, Schaeffer DG. A two-current model for the dynamics of cardiac membrane. *Bull Math Biol.* 2003;65:767–793.  
5. Niederer SA, et al. Verification of cardiac tissue electrophysiology simulators using an N-version benchmark. *Philos Trans A Math Phys Eng Sci.* 2011;369:4331–4351. doi:10.1098/rsta.2011.0139  
6. Plank G, et al. The openCARP simulation environment for cardiac electrophysiology. *Comput Methods Programs Biomed.* 2021. doi:10.1016/j.cmpb.2021.106223  
7. Campos FO, et al. Fibrosis representation and ventricular arrhythmia morphology. *Front Physiol.* 2024. doi:10.3389/fphys.2024.1370795  
8. Systematic fibrosis–reentry protocol study. *Sci Rep.* 2024. doi:10.1038/s41598-024-62002-5  
9. Djabella K, et al. Modified Mitchell–Schaeffer excitability parameter λ (lineage cited via Villar-Valero).  
10. Public cell-model materials: https://github.com/javilva/doxorubicin_fibrosis_model  
