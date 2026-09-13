# Major Revision 进度说明（审稿 P0/P1 映射）

**日期：** 2026-09-13  
**仓库：** https://github.com/Coucou2016/DOX-LBM-GPU（展示名 Fibrosis-Reentry-MS2D）

## 审稿意见 → 修复对照

| 优先级 | 审稿点 | 状态 | 落点 |
|--------|--------|------|------|
| P0 | 科学定位：开放 2D 协议/基准，非 3D 孪生复现 | ✅ | `README.md`、`papers/manuscript_draft.md`、`papers/outline.md` |
| P0 | 澄清公开细胞模型 vs 专有求解器（非仅“LBM 源码不可用”） | ✅ | README 表；手稿 Intro；引用 `javilva/doxorubicin_fibrosis_model` |
| P0 | 清理手稿草稿噪声（ChatGPT/待补充/本机路径等） | ✅ | 手稿重写为投稿向草稿 |
| P0 | `laplacian_neumann` 角点 + 常数 D 统一走 flux 算子 | ✅ | `cardiac_ms/ms_2d.py`；全域等价测试 |
| P0 | 双重 VA 终点 `VA_paper` / `VA_cycle` | ✅ | `dual_va_labels`；相图 CSV 双列；手稿 Results 表 |
| P0 | CV 距离改欧氏 `hypot` | ✅ | `estimate_cv_from_activation` |
| P0 | 测试质量（restitution 单调；pytest 警告策略） | ✅ | `validation.py`；`pytest.ini` |
| P0 | LICENSE / CITATION / requirements 拆分 / CHANGELOG | ✅ | MIT + `CITATION.cff` + `requirements-dev.txt` |
| P1 | `stimulus_mode=current\|voltage_clamp` | ✅ | 诱导默认 `current`（已验证环 VA 稳定） |
| P1 | CONTROL/DOX1/DOX2 表型配置 | ✅ | `cardiac_ms/phenotypes.py` + YAML；注明 DOX CV 未完全匹配 |
| P1 | javilva RHS 交叉核对 λ=0.01–0.3 | ✅ | 克隆成功；`scripts/crosscheck_javilva_rhs.py`（max\|Δ\|~1e-16） |
| P1 | dx 收敛脚本 | ✅ | `scripts/run_dx_convergence.py` → `data/dx_convergence.csv` |
| P1 | protocol_dox1/dox2 | ✅ | `scripts/run_protocol_phenotype.py` |

## 相图双重终点（full 4×3，钉扎环验证几何）

- **VA_cycle：3 / Non-VA：9**
- **VA_paper：3 / Non-VA：9**（本多 extras 训练与 cycle 逐格一致）
- 单 CI 平台对照：persist≥1000 且无再兴奋 → paper=VA、cycle=Non-VA（已测）
- λ=0.2/0.3 全 Non-VA：支持“二维不应复现三维诱发性图”讨论

## 测试

`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/ -q` → **47 passed**

## 未完成 / 后续（P2）

- 各向异性精化；Niederer / openCARP / MonoAlg3D 交叉验证  
- DOX 表型 1D CV 完整标定  
- 期刊格式双语精修  
- 圆盘几何完整定量 CSV（可按需 `--geometry disc --full`）
