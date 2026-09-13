# Major Revision 进度说明（审稿 P0/P1 映射）

**日期：** 2026-09-14  
**仓库：** https://github.com/Coucou2016/DOX-LBM-GPU（展示名 Fibrosis-Reentry-MS2D）

## Gap → Fix 对照（本轮）

| 优先级 | Gap | 状态 | 落点 |
|--------|-----|------|------|
| P1 | 相位奇点 / 转子 tip | ✅ | `cardiac_ms/phase_singularity.py`；`run_s1s2` → `n_singularities` / `rotor_detected`；合成螺旋/平面波测试 |
| P1 | DOX 表型 APD/CV 标定 | ✅ | Villar-Valero 309/269/210 ms 与 71/41/≈44 cm/s；`scripts/calibrate_phenotypes.py` → `data/phenotype_calibration.json`；三者均 ±10% 内 `matched=True`（诚实测量） |
| P1 | dx **与** dt 收敛 | ✅ | `scripts/run_dx_convergence.py` → `data/dx_convergence.csv` + `data/dt_convergence.csv` |
| P1 | `simulate_mono2d` 默认刺激 | ✅ | 默认 `stimulus_mode="current"` |
| P1 | 路径/摘要卫生 | ✅ | 去掉本机绝对路径；Abstract 双重终点措辞对齐代码 |
| P0 | 双重 VA 终点 | ✅（既有） | `VA_paper`=persist≥1000 **或** cycle；`VA_cycle`=require cycle |

## 表型标定实测（`--no-refine`）

| 表型 | APD (ms) | 目标 | CV (mm/ms) | 目标 | matched |
|------|----------|------|------------|------|---------|
| CONTROL | 309.1 | 309 | 0.703 | 0.71 | APD+CV |
| DOX1 | 268.5 | 269 | 0.425 | 0.41 | APD+CV |
| DOX2 | 209.9 | 210 | 0.441 | 0.44 | APD+CV（λ=0.1 下 tau_close=138） |

## 测试

`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/ -q` → **51 passed**

## 仍开放（P2）

- 各向异性精化；Niederer / openCARP / MonoAlg3D 交叉验证  
- 3D 丝状体追踪（本仓库仅 2D tip 辅助）  
- 期刊格式双语精修；圆盘几何完整定量 CSV（按需）

## Git

- **SHA:** `493217b78a8f7def97aa29511b9ccdf637081d80`
- **Push:** 本机网络无法连接 github.com:443；本地 `master` ahead 1，待网络恢复后 `git push origin master`。
