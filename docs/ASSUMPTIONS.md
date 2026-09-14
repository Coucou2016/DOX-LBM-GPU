# 建模假设与单位（cardiac_ms）

本文档说明当前 CPU 脚手架的物理简化、单位与 **未** 实现项，便于判断结果可信度边界。

## 单位

| 量 | 符号 | 单位 | 备注 |
|----|------|------|------|
| 时间 | t | ms | 与 finitewave MS 包及论文一致 |
| 空间步长 | dx | mm | 2D 网格均匀；标定协议用 dx=0.5 mm |
| 电导率 | D | mm²/ms | 单域标量或张量分量 |
| 膜电位（归一化） | u | 无量纲 [0,1] 附近 | Mitchell–Schaeffer 归一化电压，**非** mV |
| 恢复门控 | h | 无量纲 | 与 MS 论文一致 |
| 兴奋性参数 | λ | 无量纲 | Djabella 2007 / Villar-Valero；健康组织默认 0.01 |
| 传导速度估计 | CV | mm/ms | 数值上等于 m/s；由激活时间图两点估计 |

论文 LBM 中写的纤维向扩散系数 d=3.5（STACOM / J Physiol）与本仓库有限差分标定值 **不是同一套单位/求解器**。本仓库用两点 CV 把均匀 2D 的 D 标定到 **≈0.7 mm/ms**（论文健康纤维向目标）。

## 修正 Mitchell–Schaeffer（含 λ）

\[
\frac{\partial u}{\partial t}=\nabla\cdot(D\nabla u)+\frac{h\,u(u-\lambda)(u_{\max}-u)}{\tau_{\mathrm{in}}}-\frac{u}{\tau_{\mathrm{out}}}+J_{\mathrm{stim}}
\]

\[
\frac{\partial h}{\partial t}=\begin{cases}(1-h)/\tau_{\mathrm{open}} & u<u_{\mathrm{gate}}\\ -h/\tau_{\mathrm{close}} & u\ge u_{\mathrm{gate}}\end{cases}
\]

- 默认健康：λ=0.01，u_max=1，τ 与 Mitchell & Schaeffer 2003 / finitewave 包相同。
- λ=0 且 u_max=1 时，J_in 与 finitewave `calc_J_in` 逐点一致（有单元测试）。
- 纤维化扫描：λ_fib ∈ {0.01, 0.1, 0.2, 0.3}；λ=0.3 接近功能阻滞。

## 时间步与 CFL

2D 显式扩散采用五点格式，稳定性条件：

\[
\Delta t \le \frac{\Delta x^2}{4 D_{\max}}
\]

实现见 `suggest_dt_cfl` / `check_cfl`；`simulate_mono2d` 在 `enforce_cfl=True` 时自动钳制 `dt`。标定后 D≈0.0465 mm²/ms、dx=0.5 mm 时，dt=0.1 ms 的 CFL 数约 0.07，远低于 0.5。

离子项与扩散在同一步内做 **加性显式欧拉**（additive forward Euler）：
`u ← u + dt * (diff_u + rhs + J_stim)`，**不是**算子分裂（operator splitting）。
扩散 CFL 在小 D 下会允许 dt≫τ_in；实现将自动 dt 上限设为 **0.1 ms**（`IONIC_DT_MAX_MS`），以免上升沿失真。

## 0D 模型

- 经典 MS：`simulate_ms_0d` 走 `finitewave-model-mitchell-schaeffer.ionic_step`（黄金 APD 回归）。
- 修正 MS：`simulate_ms_0d_modified`（含 λ）。刺激为 **电压钳** 窗口，非电流钳。
- **未** 包含：细胞异质性、电药代谢、β 受体、DOX 剂量效应。

## 2D 单域原型

已实现：

- 显式 `du/dt = div(D∇u) + f_ionic(u,h,λ)`（D 变化时守恒形式；均匀 D 时等价 `D∇²u`）
- Neumann（零通量）边界
- 三相组织：健康 / 边界（致密掩膜的形态学膨胀）/ 致密纤维化
- 标准 S1–S2（BCL=400 ms，n_s1=3）与折返判定（**需要再兴奋周期**，见下）
- 各向异性 `div(D∇u)` 桩（`fiber_conductivity_tensor` + `laplacian_anisotropic`）

**未** 实现（与 Villar-Valero / 临床管线差距）：

- **3D 猪 LV** 几何与 LGE 纤维化（本仓库是 2D 薄片）
- **双向域**、**Purkinje**、**LBM–GPU**
- 真实纤维走向场；DOX 浓度场
- 论文 96 组 3D 参数扫描的定量复现

## S1–S2 与折返

- S1：BCL 400 ms，默认 3 个（测试可用 n_s1=1 以缩短时间）。
- S2 及后续 extra：耦合间期相对前一心搏（论文 DOX1：240 / 200 / 190 ms）。
- **三重终点**：`VA_paper` = persist≥1000 ms **仅此一条**（Villar-Valero；**从不** OR 周期证据）；`VA_recurrence`（默认 `label` / 兼容别名 `VA_cycle`）要求再兴奋：extra≥1 **或** `n_probes_relapped`≥3；`VA_strict` = persist≥1000 **且** 再入循环。仅 persist≥1000 ms **不算** recurrence；单圈各探针一次升支也不算。
- 钉扎环是按波长设计的**验证几何**，不是生物学发现；二维相图**不应**复现三维诱发性比例（见手稿 Discussion §5.1）。
- 刺激：默认 **电流注入** `stimulus_mode="current"`；可选 `"voltage_clamp"`（遗留短回归）。
- **负对照**：无纤维化均匀组织在默认协议下应为 Non-VA。
- **相位奇点 / 转子尖端（辅助）**：`cardiac_ms/phase_singularity.py` 用 (u,h) 平面相位的拓扑荷检测 2D tip；`run_s1s2` 可选输出 `n_singularities` / `rotor_detected`。这是协议审计用的二维辅助指标，**不是**三维丝状体追踪，也**不是**临床转子诊断。
- **波长 vs 几何（为何小圆盘不能当 Fig.5）**：
  - λ_wave ≈ CV × APD。设计用经典 MS APD₉₀≈256.6 ms：0.70×257 ≈ **180 mm**；文献 CONTROL APD 309 ms → ≈**219 mm**（更大）。
  - 48² × 0.5 mm 盘片仅 **24 mm**，路径远小于波长 → 论文式圆盘相图只应作为 **阴性对照**（`--geometry disc`）。
  - 钉扎环（默认相图）：内径 14 mm、外径 20 mm，平均路径 π(14+20)≈**107 mm**；环上默认 **12** 个有序角向探针（8–16）。
    - D↓30%（CV≈√0.7×0.70≈0.59）：设计波长仍 ≫ 107 mm → 一圈 lap < APD → **Non-VA**
    - D↓90%（CV≈√0.1×0.70≈0.22）：设计波长可 < 107 mm → 几何上允许折返；是否判 VA 还取决于是否出现再兴奋（不是平台期滞留）。
    - λ_fib=0.3：环接近阻滞 → **Non-VA**
  - 环上保持健康 **τ_close=150 ms**（未把全局 APD 改成 80 ms）。`tau_close=80` + 交叉场仍是测试里的数值阳性对照，**不是**相图主结果。
  - **协议**：单次 prematurely CI≈220 ms 在 D↓90% 只走一圈后进入长平台（persist≥1000、extra=0）→ 新准则下 **Non-VA**。默认钉扎环与快速相图改用论文 extras **240/200/190 ms**（n_s1=3）：D↓90% λ=0.01 出现真正再兴奋（extra≥1 或 relapped≥3）→ **VA**；同协议下 D↓30% 仍为 **Non-VA**。
  - **共存说明**：VA 格点在观察窗结束时仍可出现局部高 `u`（平台残余）；这与「再兴奋折返」并不矛盾——分类只看 upstroke/extra/relapped，不因 `u_final` 高而改判。单 CI 平台假阳性与多 extras 真折返可在同一 D↓90% 细胞上对照。
- 网格：环用 64²、dx=0.75 mm（域 48 mm）。均匀片上该 dx 的两点 CV≈0.72 mm/ms，仍在 0.55–0.85 标定带；主标定仍是 dx=0.5 mm → 0.70 mm/ms。
- 默认快速相图（环，4 格，论文 extras）：预期 **1 VA / 3 Non-VA**（仅 D↓90%×λ=0.01）。

## 数值近似

- 空间：二阶中心差分 / 面平均 D 的守恒扩散
- 时间：显式欧拉（离子 + 扩散）
- 激活时间：首次 `u ≥ 0.5` 的步时间
- CV：两点直线距离 / 激活时差；局部 CV ≈ 1/|∇T|
- 刺激：默认电流注入 `J_stim`（`stimulus_mode=current`）；可选区域电压钳
- CV 两点距离：欧氏 `hypot(Δrow, Δcol) * dx`

## 参考验证（本仓库）

| 检查 | 依据 |
|------|------|
| MS 默认 τ 参数 | finitewave 包 `get_parameters()` |
| λ=0 修正 RHS | 与 `ionic_step` 一致 |
| 0D APD | 固定 seed 黄金值 + 生理带宽 |
| 2D CV | 均匀介质两点 CV ∈ [0.55, 0.85] mm/ms（目标 0.7） |
| CFL | 解析上限与 `check_cfl`（数学检查仍用 D=0.8 示例） |
| 扩散算子 | 常数 D 时 `div(D∇u)` vs `D∇²u` |
| 无纤维化 S1–S2 | Non-VA |

完整 **Niederer 2011 立方体**、openCARP / MonoAlg3D 对照，以及 Zenodo 猪 MI 几何，见 `data/README.md`（P2，需自行下载，本机未拉多 GB 数据）。

## 表型标定（CONTROL / DOX1 / DOX2）

Villar-Valero 健康组织锚点（*J Physiol* 2026）：APD CONTROL 309 / DOX1 269 / DOX2 210 ms（DOX **短于** CONTROL）；纤维化区 APD DOX1 276 / DOX2 184 ms；CV 0.71 / 0.41 / 0.4389 mm/ms。文献目标为数据字典（`CONTROL_target` / `DOX1_target` / `DOX2_target`）；`tau_close`/`D`/`lam` 为标定后的模型参数。`cv_matched` 仅在测量值落在目标 ±10% 且 CFL 稳定时为 True，否则保持 False 并在 `data/phenotype_calibration.json` 记录残差——**不**伪造 matched。

协议：CONTROL **无**异位 extras；DOX1 主协议 240/200/190；DOX2 主协议四个 250 ms 耦合（250×4）。过渡区协议另议，不发明 260/220/200/180。

## dx / dt 收敛

`scripts/run_dx_convergence.py` 写出 `data/dx_convergence.csv` 与 `data/dt_convergence.csv`。用于数值验证，不是生物学结论。
