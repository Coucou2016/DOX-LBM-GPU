# A wavelength-aware 2D monodomain Mitchell–Schaeffer benchmark for DOX-inspired fibrosis–reentry protocols
# 面向 DOX 启发纤维化–折返协议的波长感知二维单域 Mitchell–Schaeffer 基准

---

## Title (EN)

**A wavelength-aware 2D monodomain Mitchell–Schaeffer protocol benchmark for doxorubicin-inspired fibrosis–reentry (not a 3D LBM–GPU twin reproduction)**

## 标题（中）

**面向阿霉素启发纤维化–折返的波长感知二维单域 Mitchell–Schaeffer 协议基准（非三维 LBM–GPU 孪生复现）**

---

## Abstract (EN)

**Background.** Doxorubicin (DOX)–associated diffuse fibrosis can create an arrhythmogenic substrate. Personalized 3D MRI-based left-ventricular models that couple a λ-modified Mitchell–Schaeffer (MS) ionic law to a GPU Lattice–Boltzmann (LBM) monodomain solver have mapped inducibility under fibrotic excitability and conduction changes. The cell model, parameters, and sample anatomy are publicly documented (e.g. `javilva/doxorubicin_fibrosis_model`), while the production LBM–GPU solver remains proprietary—blocking independent protocol audit on the closed twin pipeline.

**Methods.** We release an open CPU 2D finite-difference monodomain **protocol/benchmark** that implements the same λ-modified MS law, conservative diffusion \(\nabla\cdot(D\nabla u)\), three-class synthetic fibrosis tissue, and an S1–S2 stimulation train aligned with published coupling intervals. Homogeneous conduction velocity (CV) is calibrated to **≈0.70 mm/ms** (acceptance band 0.55–0.85) at \(D=0.0465\,\mathrm{mm}^2/\mathrm{ms}\). Time steps respect a diffusion CFL bound and an ionic upper limit of \(0.1\,\mathrm{ms}\); dx/dt convergence CSVs are numerical verification only. Default stimulus is **current injection** (`stimulus_mode="current"`). We report **dual VA endpoints** clearly: `VA_paper` = persist ≥ 1000 ms **or** cycle evidence (Villar-Valero-style); `VA_cycle` (default `label`) = require re-excitation (extra≥1 or relapped≥3). Optional 2D phase-singularity tip counts are auxiliary (not 3D filaments). Because a nominal healthy wavelength (\(\mathrm{CV}\times\mathrm{APD}\approx0.70\times250\approx175\,\mathrm{mm}\)) exceeds small disc domains (~24 mm), we use a pinned annulus as a **verification geometry** designed via wavelength (path ≈107 mm), not as a biological discovery claim.

**Results.** Dual-endpoint counts on the annulus λ×D grid are reported from regenerated CSV (see Results tables). Zero-dimensional APD₉₀ equals **256.6 ms** under the classical MS golden regression. The annulus is a wavelength-designed verification circuit; disc geometry remains a negative control.

**Conclusions.** The deliverable is an open methods and verification resource for protocol alignment and endpoint audit. It is **not** a 3D DOX twin, does **not** claim LBM–GPU performance or clinical ICD utility, and does **not** equate synthetic fibrosis with porcine DOX myocardium or ischemic MI.

**Keywords:** cardiac electrophysiology; Mitchell–Schaeffer; monodomain; fibrosis; reentry; reproducibility; doxorubicin (protocol alignment)

---

## 摘要（中）

**背景。** 阿霉素相关弥漫纤维化可构成致心律失常基质。个性化三维左室模型将 λ 修正 Mitchell–Schaeffer 与 GPU 格子 Boltzmann 单域求解器结合以扫描诱发性。细胞模型/参数/样例解剖可公开对照，但生产用 LBM–GPU 求解器仍为专有，独立组难以在封闭孪生管线上审计协议与终点。

**方法。** 本文提供开放的 CPU 二维有限差分单域**协议/基准**：实现同一 λ 修正 MS、守恒扩散 \(\nabla\cdot(D\nabla u)\)、合成三相纤维化，以及与文献耦合间期对齐的 S1–S2。均匀 CV 标定至约 **0.70 mm/ms**。默认刺激为电流注入。同时报告双重 VA 终点：`VA_paper`（persist≥1000 ms **或** 周期证据）与 `VA_cycle`（要求再兴奋；默认 `label`）。可选二维相位奇点计数仅为辅助指标。名义健康波长约 175 mm 远大于小圆盘，故采用按波长设计的钉扎环作为**验证几何**（非生物学发现）。

**结果。** 环网格双重终点计数见 Results 表（由再生 CSV 锁定）。0D APD₉₀ 黄金回归为 **256.6 ms**。

**结论。** 本工作是方法与验证资源，**不是**三维 DOX 孪生，也**不**声称 LBM–GPU 性能或临床 ICD 适应证。

---

## 1. Introduction

Chemotherapy-related cardiotoxicity is often framed through declines in ejection fraction, yet tissue remodeling can also create a substrate for ventricular arrhythmia (VA). Anthracycline agents such as doxorubicin (DOX) promote reactive diffuse fibrosis; in silico models that combine image-derived anatomy with monodomain electrophysiology are attractive tools for probing how excitability and conduction interact with that substrate.

Villar-Valero et al. constructed personalized porcine left-ventricular (LV) models from MRI / late gadolinium enhancement and electro-anatomical mapping, coupled a λ-modified Mitchell–Schaeffer (MS) ionic model to a GPU Lattice–Boltzmann (LBM) monodomain solver, and performed a parametric inducibility scan under fibrotic excitability and conductivity changes (STACOM 2024; *J Physiol* 2025, doi:10.1113/jp288819). Public materials document the cell model and related assets (`javilva/doxorubicin_fibrosis_model`); the production solver used in the twin remains proprietary. Commentary by Chabiniok and Zaha (*J Physiol*, doi:10.1113/jp290313) argues that clinical translation requires methods that can be opened: reproducible and runnable outside a closed pipeline.

**Gap.** Independent groups cannot re-run the closed 3D twin. Separately, a nominal healthy wavelength \(\lambda_{\mathrm{wave}}\approx\mathrm{CV}\times\mathrm{APD}\approx175\,\mathrm{mm}\) cannot fit inside a small 2D disc (~24 mm), so disc-only inducibility grids collapse to all Non-VA for geometric—not physiological—reasons. A persist≥1000 ms rule alone can label plateau retention as VA.

**Approach.** We build a testable 2D monodomain **benchmark** that (i) aligns the ionic law and S1–S2 extras with published protocol choices, (ii) reports dual VA endpoints (`VA_paper` / `VA_cycle`), and (iii) adopts a wavelength-aware pinned annulus as verification geometry. The deliverable is an open verification layer—not a substitute for a personalized 3D twin.

**Boundary.** Synthetic three-class fibrosis ≠ porcine DOX myocardium ≠ ischemic MI scar. 2D finite differences ≠ 3D LBM. This scaffold does **not** reproduce quantitative 3D pig-LV inducibility fractions.

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
**Output.** Transmembrane field \(u\), activation times, CV, dual VA labels, phase-diagram CSV.  
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

Tissue is labeled healthy / border / dense fibrosis. Stimuli default to `stimulus_mode="current"` (add \(J_{\mathrm{stim}}\)); `"voltage_clamp"` remains available for legacy short regressions. Default S1: BCL = 400 ms, \(n=3\). Default extras (DOX1-aligned): 240 / 200 / 190 ms. Induction and observation windows are separated (default observe 1000 ms).

### 3.5 Dual VA endpoints

| Endpoint | Rule |
|----------|------|
| `VA_paper` | Persist ≥ 1000 ms (or cycle evidence); Villar-Valero-style |
| `VA_cycle` | `n_extra_cycles ≥ 1` **or** `n_probes_relapped ≥ 3` (default `label`) |

Plateau persistence alone is insufficient for `VA_cycle`. A single-extras plateau negative control is locked in regression tests.

### 3.6 Wavelength-aware verification geometry

Design wavelength uses nominal APD = 250 ms:

\[
\lambda_{\mathrm{wave}} \approx \mathrm{CV}\times\mathrm{APD} \approx 0.70\times250 = 175\,\mathrm{mm}.
\]

A \(48^2\times0.5\,\mathrm{mm}\) disc (~24 mm) is a negative control. The pinned annulus (path ≈107 mm) is a **verification geometry** sized so that strongly slowed wavelengths can reenter while healthy wavelengths cannot—not a claim of biological discovery.

### 3.7 Verification suite

Gates: pytest; 0D APD golden regression; homogeneous 2D CV band; full-domain diffusion-operator consistency; fibrosis-free Non-VA; annulus dual-endpoint phase diagram. Spatial/temporal convergence tables (`data/dx_convergence.csv`, `data/dt_convergence.csv`) document numerical sensitivity of CV under dx∈{0.75,0.5,0.25} mm and dt∈{0.1,0.05,0.025} ms—verification only, not biology. Optional 2D phase-singularity / tip counts (`n_singularities`, `rotor_detected`) are auxiliary protocol metrics on the final (u,h) snapshot; they are **not** 3D filament tracking.

CONTROL/DOX1/DOX2 phenotype presets target Villar-Valero healthy-tissue APD (309/269/210 ms) and CV (71/41/≈44 cm/s); `cv_matched` is set only within ±10% under stable CFL (`scripts/calibrate_phenotypes.py` → `data/phenotype_calibration.json`).

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

**Full 4×3 annulus grid** (DOX1-aligned extras 240/200/190 ms; \(\tau_{\mathrm{close}}=150\,\mathrm{ms}\); \(n_x=n_y=64\), \(\mathrm{d}x=0.75\,\mathrm{mm}\); path ≈106.8 mm; `stimulus_mode=current`; wall time ≈172 s). Source: `papers/data/phase_diagram.csv` (mode=`full`).

**Dual-endpoint summary (same 12 cells):**

| Endpoint | VA | Non-VA |
|----------|---:|-------:|
| `VA_cycle` (default `label`) | 3 | 9 |
| `VA_paper` (persist≥1000 **or** cycle) | 3 | 9 |

On this multi-extra train the two endpoints agree cell-wise. They **disagree** on the single-premature plateau control (persist≥1000, extra=0 → `VA_paper`=VA, `VA_cycle`=Non-VA; regression-tested).

| λ | D↓30% | D↓70% | D↓90% |
|---|:-----:|:-----:|:-----:|
| 0.01 | Non-VA | **VA** | **VA** |
| 0.1 | **VA** | Non-VA | Non-VA |
| 0.2 | Non-VA | Non-VA | Non-VA |
| 0.3 | Non-VA | Non-VA | Non-VA |

VA cell detail (from CSV; no fabricated statistics):

| λ | D reduction | persist_ms | n_extra_cycles | n_probes_relapped | VA_cycle | VA_paper |
|---|-------------|------------|----------------|-------------------|----------|----------|
| 0.01 | 0.7 | 666.6 | 1 | 1 | VA | VA |
| 0.01 | 0.9 | 1000.0 | 2 | 3 | VA | VA |
| 0.1 | 0.3 | 632.5 | 1 | 1 | VA | VA |

At λ∈{0.2,0.3} all D reductions are Non-VA (functional block on the verification ring)—a geometric/excitability bound that already prevents matching a richer 3D inducibility map.

![Phase](figures/fig_phase_diagram.png)

**Interpretation bound.** The mixed diagram shows that geometry and endpoints are auditable on this scaffold. It does **not** claim reproduction of Villar-Valero 3D inducibility proportions.

### 4.5 Disc negative control

Small discs are expected to be all Non-VA (wavelength mismatch). Homogeneous snapshot: `fig_mono2d_u`.

![Mono2d](figures/fig_mono2d_u.png)

---

## 5. Discussion

**What we show.** An open, pytest-gated 2D protocol/benchmark; ionic/protocol choices aligned with the DOX fibrosis literature; dual VA endpoints; wavelength-aware verification geometry.

**What we do not claim.** “First DOX twin”; quantitative 3D pig-LV reproduction; LBM–GPU acceleration; clinical ICD decision support; equivalence of synthetic fibrosis to DOX myocardium or ischemic MI.

### 5.1 Why 2D must not reproduce the 3D inducibility map

A healthy design wavelength \(\lambda_{\mathrm{wave}}\approx0.70\times250\approx175\,\mathrm{mm}\) already exceeds typical small 2D discs (~24 mm). On the verification annulus (path ≈107 mm), D↓90% shortens wavelength to roughly \(\sqrt{0.1}\times0.70\times250\approx55\,\mathrm{mm}\), while D↓30% remains \(\approx147\,\mathrm{mm}\)—so inducibility is dominated by **wavelength vs path**, not by the 3D maze corridors of porcine LGE. At high fibrotic λ (0.2–0.3), the ring approaches functional block and collapses toward Non-VA even when D is reduced. Therefore a 2D λ×D heatmap **cannot** and **should not** be expected to match 3D twin inducibility fractions; discrepancy with the paper’s 3D map is a geometric and dimensional bound, not a calibration failure of this benchmark.

This stance matches Chabiniok–Zaha’s call to open methods: the scaffold lowers the cost of **protocol reproduction and endpoint audit**, rather than replacing personalized 3D twins.

**Limitations.** Anisotropy remains a prototype; Zenodo porcine MI datasets were not ingested (and MI ≠ DOX); 1D CV for DOX phenotypes is not fully matched on this FD scaffold (documented in `cardiac_ms/phenotypes.py`).

---

## 6. Code and data availability

Public repository: **https://github.com/Coucou2016/DOX-LBM-GPU** (display name: Fibrosis-Reentry-MS2D).

Core package `cardiac_ms/`, tests `tests/`, phase diagram `scripts/run_phase_diagram.py` (`--full` for 4×3), figures `scripts/plot_science.py`. Curated phase CSV: `papers/data/phase_diagram.csv`. Synthetic metadata under `data/synthetic/`. External large datasets / MonoAlg3D only as pointers in `data/README.md`. License: MIT (`LICENSE`). Citation: `CITATION.cff`.

---

## 7. References

1. Villar-Valero JM, et al. In silico predictions of action potential propagation in doxorubicin cardiotoxicity: A parametric study using preclinical 3D magnetic resonance imaging-based fibrotic left ventricle models. *J Physiol.* 2025. doi:10.1113/jp288819  
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
| Dual VA endpoints reported | protocol + phase CSV | supported |
| Open protocol/benchmark contribution | repo + pytest | supported (methods) |
| 3D DOX twin equivalence | — | **not claimed** |
