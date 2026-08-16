# 数据目录说明

本仓库 **不捆绑** 多 GB 动物或临床影像；提供 **可再生的合成基准** 与外部数据集指针。请勿在未确认带宽/磁盘时自动拉取 Zenodo 全包。

## 已包含（运行生成脚本后）

公开 GitHub 树默认只跟踪 **JSON 元数据**；`.npy` 数组在 `.gitignore` 中，请本地生成：

| 路径 | 内容 | 公开仓库 |
|------|------|----------|
| `synthetic/fibrosis_patch_64.json` | 几何与参数元数据 | ✅ 跟踪 |
| `synthetic/fibrosis_patch_64_mask.npy` | 64×64 布尔致密纤维化掩膜（圆盘） | 本地生成 |
| `synthetic/fibrosis_patch_64_D.npy` | 对应节点电导率 D（mm²/ms） | 本地生成 |
| `synthetic/fibrosis_patch_64_classes.npy` | 三相标签（0 健康 / 1 边界 / 2 致密） | 本地生成 |
| `synthetic/fibrosis_patch_64_lam.npy` | 节点 λ | 本地生成 |

```powershell
cd E:\Projects\20260522-DOX-LBM_GPU
python scripts/generate_synthetic_data.py
```

几何约定（默认）：`nx=ny=64`，圆心 `(32,32)`，半径 `8` 格点；健康 D 为标定值 `cardiac_ms.constants.D_HEALTHY_MM2_PER_MS`（≈0.0465 mm²/ms），致密区 90% 降低；健康 λ=0.01。

## P2 — 外部数据与求解器（仅指针，不自动下载）

### 1. Zenodo 18223187（猪 **MI** 多模态，非 DOX）

- 记录：<https://zenodo.org/records/18223187>
- DOI：<https://doi.org/10.5281/zenodo.18223187>
- 内容：CMR（cine / LGE）、光学标测、部分 EAM、ECG；配套论文 Rosales et al., *PLOS Comput Biol*（建模代码另见 Zenodo 17415591 / ELECTRA）。
- **用途**：公开几何与 CV/APD 对照的可复现管线；**不能**当作 Villar-Valero DOX 纤维化的替代金标准（MI 瘢痕 ≠ DOX 反应性纤维化）。
- 体积为大（多 GB）。确认磁盘后再用浏览器或 `zenodo_get` 下载；不要在本脚手架的默认脚本里 wget。

建议落地步骤（人工）：

1. 只取 **一个** 健康 + **一个** MI 受试者的 LGE 分割与光学标测 ROI，不要整库。
2. 重采样到与 `simulate_mono2d` 相近的 dx（0.5–1.4 mm），导出 `mask.npy` / `D.npy`。
3. 用 `tissue_classes.assign_three_class` 生成边界带，跑 `run_s1s2`。
4. 对照 OM 的 CV / APD，而不是期望复现 DOX 论文的 VA 表。

### 2. Niederer 2011 立方体（求解器验证）

- 文献：Niederer et al., *Phil. Trans. R. Soc. A* 2011, 369:4331–4351
- 开源复现：openCARP 教程 / Chaste cardiac；本仓库 **尚未** 跑该立方体。
- 建议在 **Linux/WSL** 用 openCARP 或 MonoAlg3D，不要在 Windows + 残缺 CUDA 上硬编。

### 3. openCARP

- <https://opencarp.org/>
- 用途：同一修正 MS 或十 Tusscher 模型的 3D 对照；导出激活时间与本仓库 2D 原型比 CV 量级（不能比几何）。

### 4. MonoAlg3D

- 本仓库已有源码树 `MonoAlg3D_C-master/`（C++/CUDA）。
- Windows GTX 950M + 混杂 CUDA 9.2/11.x：**不要**作为默认构建路径。见其 `guide-monoalg3d-windows.md`；优先 WSL2 + 匹配的 nvcc。

### 5. 论文原始 DOX 猪数据

Villar-Valero 使用的 LGE + CARTO **未**随论文开源。无官方包则无法做个体化 3D 复现；本仓库用合成盘片/三相场代替结构，只对齐方程与协议。

## 与仿真的关系

- **0D/2D 可信性**：`cardiac_ms/validation.py` 与 `tests/`（不依赖外部下载）。
- **2D 纤维化**：测试用内置 `fibrosis_mask`；本目录数组用于离线基准与三相场可视化。
