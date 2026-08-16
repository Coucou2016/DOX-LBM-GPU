# An open 2D monodomain scaffold for doxorubicin-fibrosis reentry protocols
# 面向阿霉素纤维化折返协议的开放二维单域脚手架

> **nature-writing axes:** `task=manuscript` · `paper_type=methods` · `sections=abstract,intro,related-work,method,experiments,discussion` · `language=zh-to-en (working draft ZH + EN)` · `journal=generic` (methods / computational physiology)  
> **One-sentence argument:** When the original 3D LBM–GPU doxorubicin (DOX) twin solver is unavailable, an open CPU 2D monodomain λ-Mitchell–Schaeffer scaffold with cycle-required ventricular-arrhythmia (VA) metrics and wavelength-aware geometry recovers paper-aligned conduction velocity and a mixed VA/Non-VA inducibility map, without claiming a 3D DOX digital twin.  
> **Draft status:** content-matured working draft (2026-08-16) — Results locked to regenerated pytest / validation / full 4×3 phase diagram; English prose expanded; References with DOIs. Journal lock and full bilingual polish still「待补充」.

---

## Title (EN)

**An open, wavelength-aware 2D monodomain Mitchell–Schaeffer scaffold for reproducible fibrosis–reentry protocols when 3D LBM–GPU digital-twin code is unavailable**

## 标题（中）

**在三维 LBM–GPU 数字孪生源码不可用时：面向纤维化–折返协议复现的波长感知二维单域 Mitchell–Schaeffer 开放脚手架**

---

## Abstract (EN)

**Background.** Doxorubicin (DOX)–associated diffuse fibrosis can create an arrhythmogenic substrate. Personalized 3D MRI-based left-ventricular digital twins that couple a λ-modified Mitchell–Schaeffer (MS) ionic law to a GPU Lattice–Boltzmann (LBM) monodomain solver have mapped inducibility under fibrotic excitability and conduction changes. When that solver is not publicly available, independent groups cannot reproduce the computational protocol or audit the arrhythmia endpoint.

**Methods.** We release an open CPU 2D finite-difference monodomain scaffold that implements the same λ-modified MS law, conservative diffusion \(\nabla\cdot(D\nabla u)\), three-class synthetic fibrosis tissue, and an S1–S2 stimulation train aligned with published coupling intervals. Homogeneous conduction velocity (CV) is calibrated to **0.703 mm/ms** (target 0.70; acceptance band 0.55–0.85) at \(D=0.0465\,\mathrm{mm}^2/\mathrm{ms}\). Time steps respect a diffusion CFL bound and an ionic upper limit of \(0.1\,\mathrm{ms}\). A **cycle-required** ventricular-arrhythmia (VA) classifier rejects plateau persistence and single-lap activations as false positives. Because a nominal healthy wavelength (\(\mathrm{CV}\times\mathrm{APD}\approx0.70\times250\approx175\,\mathrm{mm}\)) exceeds small disc domains (~24 mm), we use a pinned annulus whose path length (~107 mm) sits between healthy and strongly slowed wavelengths.

**Results.** On the full 4×3 annulus grid (\(\lambda\in\{0.01,0.1,0.2,0.3\}\times\) D reductions 30/70/90%) at healthy \(\tau_{\mathrm{close}}=150\,\mathrm{ms}\), we obtain **VA 3 / Non-VA 9**. Two VA cells have \(\mathrm{persist}<1000\,\mathrm{ms}\), confirming that the cycle criterion does not collapse to a persist threshold. Zero-dimensional APD₉₀ equals **256.6 ms** under the classical MS golden regression.

**Conclusions.** The scaffold is a methods and verification resource for protocol alignment and endpoint audit. It is **not** a 3D DOX twin, does **not** claim LBM–GPU performance or clinical ICD utility, and does **not** equate synthetic fibrosis with porcine DOX myocardium or ischemic MI scar.

**Keywords:** cardiac electrophysiology; Mitchell–Schaeffer; monodomain; fibrosis; reentry; reproducibility; doxorubicin (protocol alignment)

---

## 摘要（中，工作稿）

**背景。** 阿霉素相关弥漫纤维化可构成致心律失常基质。近期数字孪生研究用 MRI 个性化三维左室、修正 Mitchell–Schaeffer（含 λ）与 GPU 格子 Boltzmann（LBM）单域求解器，在纤维化兴奋性与传导改变下扫描诱发性。当该求解器源码不可用时，独立组难以复现协议并审计心律失常终点。

**方法。** 本文提供开放的 CPU 二维有限差分单域脚手架：实现同一 λ 修正 MS、守恒扩散 \(\nabla\cdot(D\nabla u)\)、合成三相纤维化组织，以及与文献耦合间期对齐的 S1–S2 方案。均匀组织传导速度标定至 **0.703 mm/ms**（目标 0.70；带 0.55–0.85），时间步受 CFL 与离子上限约束，并引入**要求再兴奋周期**的 VA 分类器，以排除平台期滞留与单圈假阳性。名义健康波长（约 175 mm）远大于小圆盘域（约 24 mm），故默认采用钉扎环（路径约 107 mm）。

**结果。** 完整 4×3 环网格得到 **VA 3 / Non-VA 9**（\(\tau_{\mathrm{close}}=150\,\mathrm{ms}\)）。其中两格 VA 的 persist&lt;1000 ms，说明周期准则不退化为 persist 阈值。0D APD₉₀ 黄金回归为 **256.6 ms**。

**结论。** 本工作是方法与验证资源，**不是**三维 DOX 孪生，也**不**声称 LBM–GPU 性能或临床 ICD 适应证；合成纤维化 **≠** 猪 DOX 心肌 **≠** 缺血性 MI。

---

## 1. Introduction

Chemotherapy-related cardiotoxicity is often framed through declines in ejection fraction, yet tissue remodeling can also create a substrate for ventricular arrhythmia (VA). Anthracycline agents such as doxorubicin (DOX) promote reactive diffuse fibrosis; in silico twins that combine image-derived anatomy with monodomain electrophysiology are attractive tools for probing how excitability and conduction interact with that substrate.

Villar-Valero et al. constructed personalized porcine left-ventricular (LV) models from MRI / late gadolinium enhancement and electro-anatomical mapping, coupled a λ-modified Mitchell–Schaeffer (MS) ionic model to a GPU Lattice–Boltzmann (LBM) monodomain solver, and performed a parametric inducibility scan (reported as 96 parameter combinations) under fibrotic excitability and conductivity changes (STACOM 2024; *J Physiol* 2025, doi:10.1113/jp288819). The associated commentary by Chabiniok and Zaha (*J Physiol*, doi:10.1113/jp290313) argues that clinical translation requires methods that can be “opened”: reproducible, runnable outside a closed pipeline, and usable by clinical scientists—not only by the original modeling team. A companion perspective further describes DOX-damaged ventricles as a “maze-like” electrical substrate (doi:10.1113/jp290582).

**Gap.** Three practical blockers currently limit independent protocol audit. First, the LBM–GPU solver used in the twin is not publicly available as source. Second, a nominal healthy wavelength \(\lambda_{\mathrm{wave}}\approx\mathrm{CV}\times\mathrm{APD}\approx0.70\,\mathrm{mm}/\mathrm{ms}\times250\,\mathrm{ms}\approx175\,\mathrm{mm}\) cannot fit inside a small 2D disc (~24 mm diameter), so disc-only inducibility grids collapse to all Non-VA for geometric—not physiological—reasons. Third, a persist≥1000 ms rule alone can label plateau retention after a premature stimulus as VA, inflating false positives.

**Approach.** We build a testable 2D monodomain scaffold that (i) aligns the ionic law and S1–S2 extras schedule with the published protocol choices, (ii) hardens the reentry endpoint with a cycle-required VA classifier, and (iii) adopts a wavelength-aware pinned annulus so that a full λ×D phase diagram can contain both VA and Non-VA cells. The deliverable is an open verification layer—not a substitute for a personalized 3D twin.

**Boundary.** Synthetic three-class fibrosis ≠ porcine DOX myocardium ≠ ischemic myocardial infarction (MI) scar. 2D finite differences ≠ 3D LBM. This scaffold does **not** reproduce quantitative 3D pig-LV inducibility fractions, does **not** claim ICD decision support, and does **not** claim to be “the first DOX twin.”

---

## 2. Related work

**DOX fibrosis twins and commentary.** Villar-Valero et al. (doi:10.1113/jp288819; STACOM precursor doi:10.1007/978-3-031-87756-8_7) provide the scientific target: parametric λ×D scans, S1–S2 logic, and a VA endpoint on image-based LV geometries with modified MS + LBM–GPU. Chabiniok & Zaha (doi:10.1113/jp290313) supply the translational framing—personalizable MS, mesh-free LBM, GPU accessibility—while stressing that ICD utility is not yet guideline-established and that the swine 9-week fibrosis burden may exceed typical patient DOX toxicity. The maze-substrate commentary (doi:10.1113/jp290582) offers mechanism language we borrow carefully without equating our 2D annulus map to porcine LV corridors.

**Fibrosis representation and inducibility protocols.** Campos et al. (*Front Physiol* 2024, doi:10.3389/fphys.2024.1370795) show that cleft versus core/border fibrosis representations change VA morphology in openCARP monodomain studies—an architectural reminder that tissue class choices are scientific decisions, not cosmetics. Systematic fibrosis–reentry work (*Sci. Rep.* 2024, doi:10.1038/s41598-024-62002-5) separates induction and observation windows; we adopt the same protocol split. CinC 2025 ventricular-twin abstracts that define reentry as multi-cycle closed-loop propagation align with our cycle-required endpoint language.

**Phenomenological MS lineage.** Classical MS (Mitchell & Schaeffer, 2003) remains a standard reduced ionic model. Djabella and colleagues introduced the excitability threshold λ used in the DOX twin. We emphasize that Corrado-style complete modified MS formulations (λ as a gate variable with outward-current gating) are **not** identical to the λ-inward-current form implemented here; claims of “mMS equivalence” are therefore out of scope.

**Verification culture and open toolboxes.** Niederer et al. (2011, doi:10.1098/rsta.2011.0139) established N-version verification for tissue electrophysiology simulators; openCARP / MonoAlg3D serve as community solvers against which a future P2 cross-check could be run. CardioMat-style methods papers (*Comput Biol Med* 2024) illustrate the pipeline → verification → application-bounds structure we imitate. Our contribution sits in that methods niche: an open, pytest-gated protocol scaffold when the closed LBM twin cannot be re-run.

---

## 3. Methods

### 3.1 Task formulation

**Input.** Grid `(nx, ny, dx)`, healthy/fibrotic diffusion \(D\) and excitability \(\lambda\), S1–S2 timetable, tissue mask.  
**Output.** Transmembrane field \(u\), activation times, CV, VA / Non-VA label, phase-diagram CSV.  
**Scope.** 2D monodomain on CPU. Out of scope: bidomain, Purkinje network, patient fiber fields, 3D LV, LBM, clinical GUI.

### 3.2 Modified Mitchell–Schaeffer with λ

Membrane voltage \(u\) and recovery gate \(h\) obey

\[
\partial_t u = \nabla\cdot(D\nabla u) + \frac{h\,u(u-\lambda)(u_{\max}-u)}{\tau_{\mathrm{in}}} - \frac{u}{\tau_{\mathrm{out}}} + J_{\mathrm{stim}},
\]

\[
\partial_t h = \begin{cases}(1-h)/\tau_{\mathrm{open}} & u < u_{\mathrm{gate}} \\ -h/\tau_{\mathrm{close}} & \text{otherwise.}\end{cases}
\]

**Units.** Time in ms, length in mm; \(u\), \(h\), and \(\lambda\) are dimensionless. Healthy default \(\lambda=0.01\); fibrotic scan \(\lambda\in\{0.01,0.1,0.2,0.3\}\). Healthy \(\tau_{\mathrm{close}}=150\,\mathrm{ms}\) on the annulus phase diagram. When \(\lambda=0\) and \(u_{\max}=1\), a single ionic step matches the `finitewave-model-mitchell-schaeffer` reference (unit-tested). We do **not** claim identity with Corrado-complete mMS.

### 3.3 Conservative diffusion and CFL

Spatial diffusion uses a five-point stencil with face-averaged \(D\) so that the discrete operator approximates \(\nabla\cdot(D\nabla u)\). For spatially constant \(D\) the scheme reduces to \(D\nabla^2 u\) (verified to machine-precision absolute error \(\sim10^{-15}\)). Explicit time steps satisfy the diffusion CFL

\[
\Delta t \le \frac{\Delta x^2}{4\,D_{\max}}
\]

and an ionic ceiling \(\Delta t\le 0.1\,\mathrm{ms}\) so that upstroke resolution is not lost when \(D\) is small.

### 3.4 Tissue classes and stimuli

Tissue is labeled healthy / border (morphological dilation of dense fibrosis) / dense fibrosis. Stimuli are regional voltage-clamp windows (documented departure from current-pulse stimulation in the twin paper; see `docs/ASSUMPTIONS.md`). Default S1: basic cycle length BCL = 400 ms, \(n=3\). Default extras: 240 / 200 / 190 ms (aligned with the published DOX1 train). Each run separates an **induction window** from a post-last-stimulus **observation window** (default 1000 ms).

### 3.5 Cycle-required VA classification

With `require_cycle=True` (default), a cell is labeled VA **if and only if** probe metric `n_extra_cycles ≥ 1` **or** `n_probes_relapped ≥ 3`. Plateau persistence `activation_persists_ms ≥ 1000` alone is **insufficient**; under this mode, persist is also **not** necessary (full-grid VA cells exist with persist 666.7 ms and 632.9 ms). Setting `require_cycle=False` restores a literature-style persist≥1000 ms rule for ablation. A single-extras plateau negative control is locked in regression tests.

### 3.6 Wavelength-aware geometry

Design wavelength uses nominal APD = 250 ms:

\[
\lambda_{\mathrm{wave}} \approx \mathrm{CV}\times\mathrm{APD} \approx 0.70\times250 = 175\,\mathrm{mm}.
\]

Independent 0D golden regression yields APD₉₀ = **256.6 ms** (report separately from the design nominal). A \(48^2\times0.5\,\mathrm{mm}\) disc has diameter ~24 mm and serves only as a negative control. The default pinned annulus has path length ≈107 mm, so that strongly slowed wavelengths can reenter while healthy wavelengths cannot.

### 3.7 Verification suite

Session gates: `pytest` **42 passed**; 0D APD golden regression; homogeneous 2D CV band; diffusion-operator consistency; fibrosis-free Non-VA; annulus phase diagram containing both VA and Non-VA.

### 3.8 Figure generation

All paper/report figures are redrawn with SciencePlots (`science` + `no-latex`) plus Times New Roman / CJK fallbacks (SimHei or Microsoft YaHei). Script: `scripts/plot_science.py`; module: `cardiac_ms/plotting.py`.

---

## 4. Results

### 4.1 0D action potential and APD

Classical MS (seed = 42) yields APD₉₀ = **256.6 ms** (tolerance ±8 ms; golden value 256.6). Figure: `papers/figures/fig_ms_0d_ap.pdf`.

![0D AP](figures/fig_ms_0d_ap.png)

### 4.2 Homogeneous 2D conduction velocity

After calibrating \(D=0.0465\,\mathrm{mm}^2/\mathrm{ms}\), two-point CV on a homogeneous sheet equals **0.703125 mm/ms** (inside 0.55–0.85; target 0.70). `scripts/calibrate_cv.py` interpolates \(D^\star\approx0.046501\,\mathrm{mm}^2/\mathrm{ms}\). Summary: `fig_validation_summary`.

![Validation](figures/fig_validation_summary.png)

### 4.3 Diffusion operator comparison

Under spatially varying \(D\), `div(D∇u)` versus `D∇²u` can shift activation persistence by tens of milliseconds. In the tested protocol the VA label did not flip, but the shortcut remains unsafe to assume by default in heterogeneous media. Figure: `fig_diffusion_compare`.

![Diffusion](figures/fig_diffusion_compare.png)

### 4.4 Annulus inducibility phase diagram

**Full 4×3 annulus grid** (paper extras; \(\tau_{\mathrm{close}}=150\,\mathrm{ms}\); \(n_x=n_y=64\), \(\mathrm{d}x=0.75\,\mathrm{mm}\); path ≈106.8 mm): **VA 3 / Non-VA 9** (regeneration wall time ≈158.4 s). Source: `papers/data/phase_diagram.csv` (mode=`full`).

| λ | D↓30% | D↓70% | D↓90% |
|---|:-----:|:-----:|:-----:|
| 0.01 | Non-VA | **VA** | **VA** |
| 0.1 | **VA** | Non-VA | Non-VA |
| 0.2 | Non-VA | Non-VA | Non-VA |
| 0.3 | Non-VA | Non-VA | Non-VA |

VA cell detail (from CSV; no fabricated statistics):

| λ | D reduction | persist_ms | n_extra_cycles | n_probes_relapped |
|---|-------------|------------|----------------|------------------|
| 0.01 | 0.7 | 666.7 | 1 | 1 |
| 0.01 | 0.9 | 1000.0 | 2 | 3 |
| 0.1 | 0.3 | 632.9 | 1 | 1 |

A quick 2×2 subset (\(\lambda\in\{0.01,0.3\}\times\) D↓{30%,90%}) previously returned VA 1 / Non-VA 3 and agrees with the full grid on overlapping cells.

![Phase](figures/fig_phase_diagram.png)

**Interpretation bound.** The mixed diagram shows that geometry and endpoint are auditable on this scaffold. It does **not** claim reproduction of Villar-Valero 3D inducibility proportions or quantitative DOX pig-LV mechanisms.

### 4.5 Disc negative control and mono2d snapshot

Small discs are expected to be all Non-VA (wavelength mismatch). A homogeneous 2D field snapshot is shown in `fig_mono2d_u`. A complete disc phase CSV, if not separately exported, remains「待补充」and can be regenerated with `scripts/run_phase_diagram.py --geometry disc`.

![Mono2d](figures/fig_mono2d_u.png)

---

## 5. Discussion

**What we show.** An open, pytest-gated pipeline; ionic/protocol choices aligned with the DOX twin literature; a hardened reentry endpoint; wavelength-aware geometry that yields an interpretable mixed phase diagram; and a full 4×3 scan with auditable VA/Non-VA labels.

**What we do not claim.** “First DOX twin”; quantitative 3D pig-LV reproduction; LBM–GPU acceleration; clinical ICD decision support; equivalence of synthetic fibrosis to DOX myocardium or ischemic MI.

This stance matches Chabiniok–Zaha’s call to open methods toward clinical usability: the scaffold lowers the cost of **protocol reproduction and endpoint audit**, rather than replacing personalized 3D twins. Their caution that swine 9-week fibrosis may exceed typical patient DOX toxicity further limits cross-species extrapolation from any twin—and, a fortiori, from this 2D surrogate.

Relative to 3D LBM, 2D finite differences omit transmural structure, realistic fiber anisotropy, and image-derived maze corridors. Relative to openCARP/MonoAlg3D verification culture (Niederer 2011), our gates are protocol-local (APD, CV band, operator consistency, cycle VA) rather than N-version tissue benchmarks; external cross-checks remain P2「待补充」.

**Limitations (honest).** Anisotropy remains a stub; Zenodo porcine datasets were not ingested (and public MI data would still ≠ DOX); English full polish and journal formatting remain「待补充」; synthetic three-class masks are protocol tools, not histological reconstructions.

---

## 6. Code and data availability

Public repository: **https://github.com/Coucou2016/DOX-LBM-GPU**  
Local workspace: `E:\Projects\20260522-DOX-LBM_GPU`.

Core package `cardiac_ms/`, tests `tests/`, phase diagram `scripts/run_phase_diagram.py` (`--full` for 4×3), figures `scripts/plot_science.py`. Curated phase CSV: `papers/data/phase_diagram.csv` (mode=full, VA 3 / Non-VA 9). Synthetic JSON metadata under `data/synthetic/` (`.npy` regenerable via `scripts/generate_synthetic_data.py`). External large datasets / MonoAlg3D only as pointers in `data/README.md` (**not** in the public tree).

Self-contained HTML: `papers/manuscript.html`, `reports/research_report.html` / `reports/report.html`.

---

## 7. References

1. Villar-Valero JM, et al. In silico predictions of action potential propagation in doxorubicin cardiotoxicity: A parametric study using preclinical 3D magnetic resonance imaging-based fibrotic left ventricle models. *J Physiol.* 2025. doi:10.1113/jp288819  
2. Chabiniok R, Zaha VG. Cardiac digital twins: Modelling the arrhythmic substrate of chemotherapy. *J Physiol.* doi:10.1113/jp290313  
3. Commentary / perspective. A maze-like electrical substrate: arrhythmogenic vulnerability in doxorubicin-damaged ventricles. *J Physiol.* doi:10.1113/jp290582  
4. Villar-Valero et al. Exploring chemotherapy-induced cardiotoxicity combining a 3D computational model and preclinical cardiac imaging data. STACOM 2024. doi:10.1007/978-3-031-87756-8_7  
5. Mitchell CC, Schaeffer DG. A two-current model for the dynamics of cardiac membrane. *Bull Math Biol.* 2003;65:767–793.  
6. Niederer SA, et al. Verification of cardiac tissue electrophysiology simulators using an N-version benchmark. *Philos Trans A Math Phys Eng Sci.* 2011;369:4331–4351. doi:10.1098/rsta.2011.0139  
7. Campos FO, et al. (Frontiers in Physiology, 2024). Fibrosis representation and ventricular arrhythmia morphology. doi:10.3389/fphys.2024.1370795  
8. Scientific Reports (2024). Systematic fibrosis–reentry protocol study. doi:10.1038/s41598-024-62002-5  
9. Djabella K, et al. Modified Mitchell–Schaeffer excitability parameter λ (lineage cited via Villar-Valero 2025).  
10. Biasi et al. CardioMat / computational cardiology toolbox methods pattern. *Comput Biol Med.* 2024.

---

## Claim–evidence map

| Claim | Evidence | Status |
|-------|----------|--------|
| λ-MS matches package at λ=0 | unit test + validation | supported |
| 0D APD = 256.6 ms | golden regression + Fig.1 | supported |
| CV = 0.703 mm/ms @ D=0.0465 | validation + calibrate_cv | supported |
| Full annulus diagram VA 3 / Non-VA 9 | `phase_diagram.csv` (full) + Fig.3 | supported |
| Cycle rule allows persist&lt;1000 VA | CSV cells 666.7 / 632.9 ms | supported |
| Open reproducibility as methods contribution | repo + pytest | supported (methods) |
| 3D DOX twin equivalence | — | **not claimed** |

## Assumptions or missing inputs

- Full English polish and target-journal format lock:「待补充」.  
- Browser MCP for ChatGPT auto-paste: unavailable in this Cursor agent tool catalog; paste packs + manuscript remain on GitHub for external reading. Fallback: WebSearch + local advisor notes under `docs/chatgpt/`.  
- Disc geometry full quantitative CSV:「待补充」.  
- Anisotropy conservation / Niederer–openCARP–MonoAlg3D cross-check: P2「待补充」.

## Why this structure

- Methods paper drafting order: Methods/Results first, then Introduction/Abstract.  
- Novelty placed on auditable endpoints and geometry, not “first twin.”  
- All figures via SciencePlots; tables synced to CSV; no fabricated statistics.
