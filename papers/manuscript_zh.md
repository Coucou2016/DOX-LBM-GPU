# 面向可审计纤维化–折返协议的波长感知二维单域基准

中文稿与英文投稿稿分离。英文见 `papers/manuscript_draft.md`。

---

## 标题

**面向可审计纤维化–折返协议的波长感知二维单域基准**

（对应英文：*A wavelength-aware 2D monodomain benchmark for auditable fibrosis–reentry protocols*）

---

## 摘要

**背景。** 阿霉素相关弥漫纤维化可构成致心律失常基质。个性化三维左室模型将 λ 修正 Mitchell–Schaeffer 与 GPU 格子 Boltzmann 单域求解器结合以扫描诱发性。细胞模型/参数/样例解剖可公开对照，但生产用 LBM–GPU 求解器仍为专有，独立组难以在封闭孪生管线上审计协议与终点。

**方法。** 本文提供开放的 CPU 二维有限差分单域**协议/基准**：实现同一 λ 修正 MS、守恒扩散 \(\nabla\cdot(D\nabla u)\)、合成三相纤维化，以及与文献耦合间期对齐的 S1–S2。均匀 CV 标定至约 **0.70 mm/ms**。时间推进为**加性显式欧拉**（非算子分裂）。默认刺激为电流注入。报告三重 VA 终点：`VA_paper`（persist≥1000 ms **仅此**，Villar-Valero）、`VA_recurrence`（要求再兴奋；默认 `label`）、`VA_strict`（persist≥1000 **且** 再入循环）。可选二维相位奇点计数仅为辅助指标。名义健康波长远大于小圆盘，故采用按波长设计的钉扎环作为**验证几何**（非生物学发现）。三维“不是孪生复现”的边界写在摘要与局限，不写入标题。

**结果。** 环网格三重终点计数由再生 CSV 锁定（见英文 Results 表；勿手填）。0D APD₉₀ 黄金回归为 **256.6 ms**。

**结论。** 本工作是方法与验证资源，**不是**三维 DOX 孪生，也**不**声称 LBM–GPU 性能或临床 ICD 适应证。

**关键词：** 心脏电生理；Mitchell–Schaeffer；单域；纤维化；折返；可重复性；阿霉素（协议对齐）

---

## 表型文献靶值（Villar-Valero）

| 表型 | 健康 APD (ms) | 纤维化 APD (ms) | CV (mm/ms) |
|------|--------------:|----------------:|-----------:|
| CONTROL | 309 | — | 0.710 |
| DOX1 | 269 | 276 | 0.410 |
| DOX2 | 210 | 184 | 0.4389 |

DOX 相对 CONTROL 为 **APD 缩短**（非延长）。`LITERATURE_TARGET` 与 `CALIBRATED_MODEL` / `BENCHMARK_BASELINE` 分离；±10% 匹配见 `data/phenotype_calibration.json`。

## 协议 extras

- CONTROL：无异位 extras（空列表）
- DOX1：240 / 200 / 190 ms
- DOX2：250 / 250 / 250 / 250 ms

过渡区协议（如 260/220/200/180）**未**在本仓库发明或默认启用。

## 代码与数据

公开仓库：https://github.com/Coucou2016/DOX-LBM-GPU  
相图 CSV：`papers/data/phase_diagram.csv`  
假设与单位：`docs/ASSUMPTIONS.md`
