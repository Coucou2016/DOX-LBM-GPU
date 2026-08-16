# An open 2D monodomain scaffold for doxorubicin-fibrosis reentry protocols
# 面向阿霉素纤维化折返协议的开放二维单域脚手架

> **nature-writing axes:** `task=manuscript` · `paper_type=methods` · `sections=abstract,intro,method,experiments,discussion` · `language=zh-to-en (working draft ZH + EN title/abstract)` · `journal=generic`  
> **Draft status:** matured working draft (2026-08-16) — Methods/Results synced to regenerated pytest/validation/phase-diagram outputs; Discussion bounded. English full polish and journal lock still「待补充」.

---

## Title (EN)

**An open, wavelength-aware 2D monodomain Mitchell–Schaeffer scaffold for reproducible fibrosis–reentry protocols when 3D LBM–GPU digital-twin code is unavailable**

## 标题（中）

**在三维 LBM–GPU 数字孪生源码不可用时：面向纤维化–折返协议复现的波长感知二维单域 Mitchell–Schaeffer 开放脚手架**

---

## Abstract (EN)

Doxorubicin (DOX)–associated diffuse fibrosis can create an arrhythmogenic substrate. Recent cardiac digital-twin work has used personalized 3D MRI-based left-ventricular models with a modified Mitchell–Schaeffer (MS) model and a GPU Lattice–Boltzmann (LBM) monodomain solver to map inducibility under fibrotic excitability and conduction changes. When that solver is not publicly available, independent groups cannot reproduce the computational protocol or audit the arrhythmia endpoint. Here we provide an open CPU 2D finite-difference monodomain scaffold that implements the same λ-modified MS ionic law, conservative diffusion \(\nabla\cdot(D\nabla u)\), three-class synthetic fibrosis tissue, and an S1–S2 stimulation train aligned with published coupling intervals. We calibrate homogeneous conduction velocity to **0.703 mm/ms** (target 0.70; band 0.55–0.85) at \(D=0.0465\,\mathrm{mm}^2/\mathrm{ms}\), enforce CFL-aware time steps, and introduce a **cycle-required** ventricular-arrhythmia (VA) classifier that rejects plateau persistence and single-lap activations as false positives. Because a nominal healthy wavelength (\(\mathrm{CV}\times\mathrm{APD}\approx0.70\times250\approx175\,\mathrm{mm}\)) exceeds small disc domains (~24 mm), we use a pinned annulus whose path length (~107 mm) sits between healthy and strongly slowed wavelengths. On the full 4×3 annulus grid (\(\lambda\in\{0.01,0.1,0.2,0.3\}\times\) D reductions 30/70/90%), we obtain **VA 3 / Non-VA 9** at healthy \(\tau_{\mathrm{close}}=150\,\mathrm{ms}\). The scaffold is a methods and verification resource, not a 3D DOX twin, and does not claim LBM–GPU performance or clinical ICD utility.

**Keywords:** cardiac electrophysiology; Mitchell–Schaeffer; monodomain; fibrosis; reentry; reproducibility; doxorubicin (protocol alignment)

---

## 摘要（中，工作稿）

阿霉素相关弥漫纤维化可构成致心律失常基质。近期数字孪生研究用 MRI 个性化三维左室、修正 Mitchell–Schaeffer（含 λ）与 GPU 格子 Boltzmann（LBM）单域求解器，在纤维化兴奋性与传导改变下扫描诱发性。当该求解器源码不可用时，独立组难以复现协议并审计心律失常终点。本文提供开放的 CPU 二维有限差分单域脚手架：实现同一 λ 修正 MS、守恒扩散 \(\nabla\cdot(D\nabla u)\)、合成三相纤维化组织，以及与文献耦合间期对齐的 S1–S2 方案。均匀组织传导速度标定至 **0.703 mm/ms**（目标 0.70；带 0.55–0.85），时间步受 CFL 约束，并引入**要求再兴奋周期**的 VA 分类器，以排除平台期滞留与单圈假阳性。名义健康波长（约 175 mm）远大于小圆盘域（约 24 mm），故默认采用钉扎环（路径约 107 mm）。完整 4×3 环网格得到 **VA 3 / Non-VA 9**（\(\tau_{\mathrm{close}}=150\,\mathrm{ms}\)）。本工作是方法与验证资源，**不是**三维 DOX 孪生，也**不**声称 LBM–GPU 性能或临床 ICD 适应证。

---

## 1. Introduction

**Context.** 化疗相关心毒性不仅表现为射血分数下降，组织改变也可形成室性心律失常（VA）基质。Villar-Valero 等（STACOM 2024；*J Physiol* 2025, doi:10.1113/jp288819）用猪 MRI 纤维化左室构建个性化孪生，并在 λ 与扩散参数空间做诱发扫描（报道 96 组参数模拟）。

**Gap.** Chabiniok & Zaha（*J Physiol*, doi:10.1113/jp290313）评述强调：若方法不能“打开”（可复现、可本地运行、可个性化），则临床转化受限；临床 ICD 效用亦尚未确立。当前阻塞包括：LBM–GPU 求解器源码缺失；小二维圆盘几何与波长不匹配导致全 Non-VA 假阴性；仅用 persist≥1000 ms 会把平台期误判为 VA。

**Approach.** 我们构建可测试的二维单域脚手架，对齐离子模型与刺激协议，硬化折返终点，并以波长感知几何使相图同时出现 VA 与 Non-VA，为后续三维/开源求解器对照留下接口。

**Boundary.** 合成纤维化 ≠ DOX 猪心肌 ≠ 缺血性 MI；二维 FD ≠ 三维 LBM；本脚手架**不**复现三维猪 LV 定量结果，也**不**提供 ICD 决策。

---

## 2. Related work

- Villar-Valero et al. 2025 / STACOM 2024（doi:10.1113/jp288819）：3D LGE + 修正 MS + LBM–GPU；参数扫描诱发。  
- Chabiniok & Zaha commentary（doi:10.1113/jp290313）：MS 易个性化、LBM 免网格、GPU 可临床化；下一步需**打开方法**与验证。  
- Campos et al., *Front Physiol* 2024：纤维化表示（cleft vs core/border）改变 VA 形态——写作上可仿“建模选择→诱发→形态”阶梯。  
- Systematic fibrosis–reentry（*Sci. Rep.* 2024, doi:10.1038/s41598-024-62002-5）：诱导窗 + 观察窗的协议拆分。  
- CinC 2025 ventricular twin 工作：S1–S2；折返定义为多圈闭路传播——与本仓库 cycle-required 终点同向。  
- CardioMat / toolbox 类 methods 结构：管线→验证→应用边界。  
- 经典 MS（Mitchell & Schaeffer 2003）；Djabella 等引入的 λ 兴奋性项；**注意** Corrado 等完整 mMS（λ:=v_gate、外向电流门控）与本文实现**不等同**。  
- openCARP / MonoAlg3D / Niederer 验证基准：本仓库仅作 P2 指针（「待补充」交叉）。

---

## 3. Methods

### 3.1 Task formulation

**输入：** 网格 `(nx,ny,dx)`、健康/纤维化 \(D\) 与 \(\lambda\)、S1–S2 时间表、组织掩膜。  
**输出：** 膜电位场 \(u\)、激活时间、CV、折返标签（VA / Non-VA）、相图 CSV。  
**范围：** 二维单域 CPU；不含双向域、浦肯野、真实纤维场、3D LV、LBM。

### 3.2 Modified Mitchell–Schaeffer with λ

\[
\partial_t u = \nabla\cdot(D\nabla u) + \frac{h\,u(u-\lambda)(u_{\max}-u)}{\tau_{\mathrm{in}}} - \frac{u}{\tau_{\mathrm{out}}} + J_{\mathrm{stim}}
\]

\[
\partial_t h = \begin{cases}(1-h)/\tau_{\mathrm{open}} & u < u_{\mathrm{gate}} \\ -h/\tau_{\mathrm{close}} & \text{otherwise}\end{cases}
\]

单位：时间 ms，长度 mm，\(u,h,\lambda\) 无量纲。健康默认 \(\lambda=0.01\)；纤维化扫描 \(\lambda\in\{0.01,0.1,0.2,0.3\}\)。λ=0 且 \(u_{\max}=1\) 时与 `finitewave-model-mitchell-schaeffer` 单步一致（单元测试）。本文 **不**声称与 Corrado 等“门控外向电流 + λ:=v_gate”的完整 mMS 同一。

### 3.3 Conservative diffusion and CFL

空间采用面平均 \(D\) 的守恒五点格式；常数 \(D\) 时与 \(D\nabla^2 u\) 一致（验证最大绝对误差 \(\sim10^{-15}\)）。显式时间步满足 \(\Delta t\le\Delta x^2/(4D_{\max})\)，并另设离子项上限 \(\Delta t\le 0.1\,\mathrm{ms}\)。

### 3.4 Tissue classes and stimuli

三相组织：健康 / 边界（致密掩膜膨胀）/ 致密纤维化。刺激为区域电压钳窗口。S1：BCL=400 ms，默认 n=3；后续 extras 默认 240/200/190 ms（对齐论文 DOX1 训练）。仿真拆分为**刺激/诱导窗**与末次刺激后 **观察窗**（默认 1000 ms）。

### 3.5 Cycle-required VA classification

默认 `require_cycle=True`：返回 VA **当且仅当** 探针 `n_extra_cycles≥1` **或** `n_probes_relapped≥3`。平台期 `activation_persists_ms≥1000` **单独不足**；在该模式下 persist 也**不是**必要条件（完整相图中可见 persist&lt;1000 ms 的 VA 格点）。`require_cycle=False` 可恢复文献式 persist≥1000 ms 规则。单 CI 平台期负对照写入回归测试。

### 3.6 Wavelength-aware geometry

几何设计用名义 APD=250 ms：\(\lambda_{\mathrm{wave}}\approx\mathrm{CV}\times\mathrm{APD}\approx 0.70\times250\approx175\,\mathrm{mm}\)。0D 黄金回归测得 APD₉₀=**256.6 ms**（与名义设计值分开报告）。48²×0.5 mm 圆盘直径约 24 mm → 仅作阴性对照。默认钉扎环路径 ≈107 mm，使强减速波长可落入环内而健康波长不可。

### 3.7 Verification suite

本机会话：`pytest` **42 passed**（65.61 s）；0D APD 黄金回归；均匀 2D CV 带；扩散算子一致性；无纤维化 Non-VA；环相图同时含 VA 与 Non-VA。

### 3.8 Figure generation

全部报告/论文图经 SciencePlots（`science` + `no-latex`）与 Times New Roman 重绘；脚本 `scripts/plot_science.py`，模块 `cardiac_ms/plotting.py`。

---

## 4. Results

### 4.1 0D action potential and APD

经典 MS（seed=42）APD₉₀ = **256.6 ms**（容差 ±8 ms；黄金值 256.6）。见图 `papers/figures/fig_ms_0d_ap.pdf`。

![0D AP](figures/fig_ms_0d_ap.png)

### 4.2 Homogeneous 2D conduction velocity

标定 \(D=0.0465\,\mathrm{mm}^2/\mathrm{ms}\) 后，均匀片两点 CV = **0.703125 mm/ms**（落在 0.55–0.85 mm/ms；目标 0.70）。`scripts/calibrate_cv.py` 插值推荐 \(D^\star\approx0.046501\,\mathrm{mm}^2/\mathrm{ms}\)。汇总见图 `fig_validation_summary`。

![Validation](figures/fig_validation_summary.png)

### 4.3 Diffusion operator comparison

在可变 \(D\) 场景，`div(D∇u)` 与 `D∇²u` 的激活持续可差数十毫秒；本协议下标签未翻转，但说明捷径在异质 \(D\) 下不可默认。见图 `fig_diffusion_compare`。

![Diffusion](figures/fig_diffusion_compare.png)

### 4.4 Annulus inducibility phase diagram

**完整 4×3 环网格**（论文 extras；τ_close=150 ms；nx=ny=64, dx=0.75 mm；路径 ≈106.8 mm）：**VA 3 / Non-VA 9**（耗时 ≈159.5 s）。见图 `fig_phase_diagram`。源数据：`papers/data/phase_diagram.csv`。

| λ | D↓30% | D↓70% | D↓90% |
|---|:-----:|:-----:|:-----:|
| 0.01 | Non-VA | **VA** | **VA** |
| 0.1 | **VA** | Non-VA | Non-VA |
| 0.2 | Non-VA | Non-VA | Non-VA |
| 0.3 | Non-VA | Non-VA | Non-VA |

VA 格点明细（真实 CSV）：

| λ | D reduction | persist_ms | n_extra_cycles | n_probes_relapped |
|---|-------------|------------|----------------|------------------|
| 0.01 | 0.7 | 666.7 | 1 | 1 |
| 0.01 | 0.9 | 1000.0 | 2 | 3 |
| 0.1 | 0.3 | 632.9 | 1 | 1 |

快速 2×2 子集（λ∈{0.01,0.3}×D↓{30%,90%}）此前为 VA 1 / Non-VA 3，与完整网格在重叠格点上一致。

![Phase](figures/fig_phase_diagram.png)

**不夸大：** 该混合相图说明协议几何与终点在本脚手架上可审计，**不**声称复现 Villar-Valero 三维诱发比例或 DOX 猪 LV 机制定量。

### 4.5 Disc negative control and mono2d snapshot

小圆盘预期全 Non-VA（波长不匹配）。均匀二维场快照见 `fig_mono2d_u`。圆盘全表定量行若未单独导出，标为「待补充」并可本地用 `scripts/run_phase_diagram.py --geometry disc` 再生。

![Mono2d](figures/fig_mono2d_u.png)

---

## 5. Discussion

**我们展示的是：** 可复现开放管线；与文献对齐的离子/协议选择；对折返终点的协议硬化；波长感知几何使相图可解释；完整 4×3 扫描给出可审计的 VA/Non-VA 混合结果。

**我们不声称：** “首个 DOX 孪生”；三维猪 LV 定量复现；LBM–GPU 加速；临床 ICD 决策工具；缺血性 MI 数据等同 DOX。

这与 Chabiniok–Zaha“打开方法、靠近临床可用性”的评述一致：本脚手架降低**协议复现与终点审计**成本，而非替代个性化三维孪生。评述亦指出猪模型 9 周纤维化可能重于典型患者 DOX 毒性——这进一步限制跨物种外推。

**局限（诚实）：** 各向异性仍为桩（「待补充」）；未做 Niederer/openCARP/MonoAlg3D 交叉（P2）；未下载 Zenodo 猪数据入仓（且即便 MI 公开数据亦 ≠ DOX）；英文全文润色与期刊格式锁定「待补充」。合成三相掩膜是协议工具，不是组织学重建。

---

## 6. Code and data availability

Public repository: **https://github.com/Coucou2016/DOX-LBM-GPU**  
Local workspace (development): `E:\Projects\20260522-DOX-LBM_GPU`.

Core package `cardiac_ms/`, tests `tests/`, phase diagram `scripts/run_phase_diagram.py` (`--full` for 4×3), figures `scripts/plot_science.py`. Curated phase CSV: `papers/data/phase_diagram.csv` (mode=full, VA 3 / Non-VA 9). Synthetic JSON metadata under `data/synthetic/` (`.npy` regenerable via `scripts/generate_synthetic_data.py`). External big datasets / MonoAlg3D only as pointers in `data/README.md` (optional local; **not** in the public tree).

Self-contained HTML: `papers/manuscript.html`, `reports/research_report.html`.

---

## Claim–evidence map

| Claim | Evidence | Status |
|-------|----------|--------|
| λ-MS 与包在 λ=0 一致 | 单元测试 + validation | supported |
| 0D APD=256.6 ms | 黄金回归 + Fig.1 | supported |
| CV=0.703 mm/ms @ D=0.0465 | validation + calibrate_cv | supported |
| 完整环相图 VA 3 / Non-VA 9 | `phase_diagram.csv` (full) + Fig.3 | supported |
| 周期准则允许 persist&lt;1000 的 VA | CSV 中 666.7 / 632.9 ms 格点 | supported |
| 开放可复现优于封闭 LBM（methods） | 仓库+pytest | supported (methods) |
| 3D DOX 孪生等价 | — | **not claimed** |

## Assumptions or missing inputs

- 英文全文润色与目标期刊格式锁定：「待补充」。  
- ChatGPT 在线多轮顾问：本机 Cursor **无浏览器 MCP**（仅 `cursor-app-control`）；`open_resource` 打开 chatgpt.com 失败；五轮逻辑咨询以 WebSearch + 结构化顾问备忘完成并标注 fallback（见 `docs/chatgpt/round_*_notes.md`）。  
- 圆盘几何完整定量 CSV：「待补充」（机制预期已陈述）。  
- 各向异性守恒 / 外部求解器交叉：P2「待补充」。

## Why this structure

- methods 论文：先 Methods/Results，再回写 Introduction。  
- 创新点放在可审计终点与几何，而非“首个孪生”。  
- 图全部 SciencePlots；表与 CSV 同步，禁止编造统计量。
