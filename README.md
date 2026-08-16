# DOX-LBM_GPU — 心肌电生理研究脚手架

**Public repo:** https://github.com/Coucou2016/DOX-LBM-GPU

本仓库在 **Villar-Valero 等**（STACOM 2024 / *J Physiol* 2025）的 LBM–GPU 源码不可用时，提供可复现的 **CPU 单域 + 修正 Mitchell–Schaeffer（含 λ）** 管线，用于把结果对齐到论文的建模选择（而非复现 3D 猪 LV 数字孪生本身）。

> **可信性**：这是 **2D 有限差分单域**，不是 3D LBM；合成纤维化 **≠** DOX 猪心肌、也 **≠** 缺血性 MI。定量目标是协议、方程与 CV 量级与论文一致。

## 快速开始

```powershell
cd E:\Projects\20260522-DOX-LBM_GPU
pip install -r requirements.txt

# 0D 动作电位 + APD（经典 MS / finitewave 包）
python demo_ms_0d.py

# 2D 单域原型（修正 MS，λ=0.01，标定 D）
python demo_mono2d.py --no-fibrosis

# 标定均匀组织两点 CV → 0.7 mm/ms
python scripts/calibrate_cv.py

# 合成三相纤维化基准
python scripts/generate_synthetic_data.py

# P1 相图（默认：钉扎环，应同时出现 VA 与 Non-VA）
python scripts/run_phase_diagram.py
# 论文式小圆盘（预期全 Non-VA，阴性对照）
python scripts/run_phase_diagram.py --geometry disc
# 完整 4×3 环网格
python scripts/run_phase_diagram.py --full

# 全套冒烟（demo + 合成数据 + 参考验证 + pytest）
python scripts/run_smoke.py

# 参考验证 JSON
python -m cardiac_ms.validation

$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -m pytest tests/ -q
```

输出默认写入 `outputs/`（已在 `.gitignore` 中忽略）。

## 与论文对齐的要点（P0）

| 项目 | 本仓库 | 论文 |
|------|--------|------|
| 离子模型 | 修正 MS：J_in = h u (u−λ)(u_max−u)/τ_in | 同（Djabella 2007） |
| 健康 λ | 0.01 | 0.01 |
| 纤维化 λ | {0.01, 0.1, 0.2, 0.3} | 同 |
| 传播 | 单域 `div(D∇u)` | 单域 LBM |
| 健康 CV | 两点标定 **≈0.70 mm/ms**（D=0.0465 mm²/ms） | 纤维向 ≈0.7 m/s |
| S1 | BCL=400 ms，n=3 | 同 |
| 折返 | 默认要求再兴奋：extra≥1 或 `n_probes_relapped`≥3（仅 persist≥1000 不算） | ≥1000 ms |
| 组织 | 健康 / 边界（膨胀）/ 致密 | 致密 + 8 voxel 过渡带 |

## 复现 P0 / P1 的命令

```powershell
cd E:\Projects\20260522-DOX-LBM_GPU
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'

python -m pytest tests/ -q
python -m cardiac_ms.validation
python scripts/calibrate_cv.py
python scripts/generate_synthetic_data.py
python scripts/run_phase_diagram.py
# 完整 4×3×2 网格（约 24 格；本机估计见 outputs/phase_diagram_summary.json）
python scripts/run_phase_diagram.py --full
python scripts/compare_diffusion_operators.py
```

## 目录结构

| 路径 | 说明 |
|------|------|
| `cardiac_ms/ms_modified.py` | 修正 MS（λ），0D 积分 |
| `cardiac_ms/ms_2d.py` | 2D 单域；CFL；`div(D∇u)`；刺激时间表 |
| `cardiac_ms/geometries.py` | 波长计算、钉扎环 / 圆盘几何 |
| `cardiac_ms/tissue_classes.py` | 三相组织 + 环状电路 |
| `cardiac_ms/protocol_s1s2.py` | S1–S2 与 `classify_reentry` |
| `cardiac_ms/metrics.py` | LAT、两点/局部 CV、临界 CI、易损窗 |
| `cardiac_ms/constants.py` | 论文默认值与标定 D |
| `cardiac_ms/validation.py` | 黄金回归 |
| `scripts/run_phase_diagram.py` | P1 相图 CSV + 热图 |
| `scripts/compare_diffusion_operators.py` | P2：`div(D∇u)` vs `D∇²u` |
| `data/README.md` | Zenodo / openCARP / MonoAlg3D 指针（不自动下载） |
| `data/synthetic/*.json` | 小型合成纤维化元数据（`.npy` 可本地重生成） |
| `docs/ASSUMPTIONS.md` | 单位、CFL、2D 波长限制 |
| `papers/` | 手稿草稿、SciencePlots 图、相图 CSV 副本、`manuscript.html` |
| `reports/` | 学术研究报告 HTML/MD/PDF |

### 可选本地依赖（不进本公开仓库）

`MonoAlg3D_C-master/` 为第三方求解器源码树，体积大且本脚手架**未集成**。若需对照实验，请自行下载到本机工作区；**勿**在弱 GPU（如 GTX 950M）上强行全量 CUDA 编译。公开 GitHub 仓库刻意排除该目录与 `*.zip`。

## 环境与本机限制（已实测）

| 组件 | 状态 |
|------|------|
| Python | 3.13.x（Miniconda） |
| `finitewave-model-mitchell-schaeffer` | ✅ 可单独安装 |
| 完整 `finitewave` | ❌ Windows 上易触发 numpy/MSVC 冲突，**勿**全量安装 |
| Git | 可能未在 PATH |
| CUDA / LBM-GPU | 论文求解器缺失；本脚手架 **不依赖 CUDA** |

## 验证状态（参考）

| 检查项 | 方法 | 典型结果（本机） |
|--------|------|------------------|
| MS 默认参数 | `validate_ms_default_parameters` | τ_out=6, τ_in=0.3, … 与包一致 |
| λ=0 修正 RHS | vs `ionic_step` | 误差 < 1e-12 |
| 0D APD（seed=42） | 黄金回归 | **≈256.6 ms**（容差 ±8 ms） |
| 2D CV（均匀，48²，λ=0.01） | 激活时间两点 | **≈0.70 mm/ms**（带宽 0.55–0.85） |
| 标定 D | `scripts/calibrate_cv.py` | **0.0465 mm²/ms** |
| CFL（dx=0.5, D=0.8 数学例） | `suggest_dt_cfl` | **dt ≤ 0.0391 ms**（r≤0.5） |
| 无纤维化 S1–S2 | `run_s1s2` | **Non-VA** |
| 钉扎环 D↓90%、λ=0.01 | `run_annulus_s1s2`（论文 extras 240/200/190） | **VA**（再兴奋：extra≥1 或 relapped≥3；非平台期） |
| 默认相图（环，4 格） | `scripts/run_phase_diagram.py` | **1 VA / 3 Non-VA** |
| 合成数据 | `generate_synthetic_data.py` | 64² 圆盘 + 三相场 |

## 可信性说明

**已对照/校验**

- 修正 MS 在 λ=0 时与 finitewave 经典 MS 单步一致。
- 均匀 2D CV 标定到论文健康纤维向量级（0.7 m/s）。
- 守恒扩散 `div(D∇u)`；CFL 钳制。
- 折返判定函数与负对照（无纤维化 → Non-VA）。

**尚未校验（P2/P3）**

- 论文 **LBM–GPU** 与 3D 猪 LV。
- Niederer 2011 / openCARP / MonoAlg3D 交叉验证（建议 Linux）。
- Zenodo 18223187 猪 **MI** 数据（MI ≠ DOX）。
- 无创参数反演、临床 ERP 全扫描。

详见 [docs/ASSUMPTIONS.md](docs/ASSUMPTIONS.md)。

## 审查记录（迭代）

| 严重度 | 问题 | 状态 |
|--------|------|------|
| 严重 | 2D 门控 `h` 未乘 `dt` | ✅ 已修复（历史） |
| 高 | 纤维化用 `D·∇²u` 而非 `div(D∇u)` | ✅ `diffusion_div_D_grad_neumann` |
| 高 | 无 λ 的修正 MS / CV 过快（≈2.33 mm/ms） | ✅ λ-MS + D 标定到 ≈0.70 mm/ms |
| 高 | S1–S2 非标准、无折返准则 | ✅ BCL=400；默认要求再兴奋，避免平台期 / 单圈假阳性 |
| 中 | 无三相组织 | ✅ `tissue_classes.py` |
| 中 | 无相图 | ✅ `scripts/run_phase_diagram.py` |
| 高 | 48² 圆盘相图 8/8 Non-VA（波长 175 mm ≫ 域 24 mm） | ✅ 默认改为 **钉扎环**（路径≈107 mm）；圆盘保留为 `--geometry disc` 阴性对照 |
| 高 | 环上 persist≥1000 但无再兴奋被标 VA；后又以「3 探针各兴奋一次」误判单圈为 VA | ✅ 要求 extra≥1 或 relapped≥3；单 CI 平台改用论文 240/200/190 诱发真折返 |
| 中 | 单 CI 平台 vs 多 extras 折返缺乏独立回归 | ✅ `test_annulus_single_premature_plateau_is_non_va` + ASSUMPTIONS 共存说明 |
| 低 | 各向异性仅为桩 | ⚠️ 开放 |
| 阻塞 | LBM-GPU 源码缺失 | ⚠️ 开放 |
| 阻塞 | Windows 全量 finitewave | ⚠️ 开放 |

**最近验证**：`pytest tests/` **42 passed**（含单 CI 平台负对照）；默认钉扎环相图（论文 extras，τ_close=150 ms）**VA 1 / Non-VA 3**。均匀 CV 仍在 0.55–0.85 mm/ms（dx=0.5 → 0.70；dx=0.75 → 0.72）。

## 引用

- Villar-Valero et al., *J Physiol* 2025 (doi:10.1113/jp288819); STACOM 2024
- Djabella, Landau & Sorine (2007), IEEE CDC
- Mitchell & Schaeffer (2003), *Bull. Math. Biol.*
- finitewave MS 模型包：`finitewave-model-mitchell-schaeffer`
