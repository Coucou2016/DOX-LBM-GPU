# DOX-LBM_GPU 论文框架与 SciencePlots 进度报告（2026-08-16）

## 摘要

本轮完成：**进度审计**（pytest **42 passed**）、**SciencePlots + Times New Roman** 全量结果图重绘、**nature-skills**（Yuan1z0825）安装确认并按其 `nature-writing`（methods）起草 `papers/manuscript_draft.md`、论文大纲与出图脚本落盘。Cursor 内置浏览器 **无法维持 ChatGPT 标签**（创建后随即消失），故外部顾问对话 **未建立 URL**；文献框架由本地结合公开 DOI/评述元数据起草，任务书已写入 `docs/chatgpt/` 供用户手动粘贴。未执行 git commit/push/PR/deploy（无授权；且无 `.git`）。

## 基线

| 项 | 值 |
|----|-----|
| 工作区 | `E:\Projects\20260522-DOX-LBM_GPU` |
| Git | **无**（`fatal: not a git repository`） |
| Python | 3.13.x + Miniconda |
| SciencePlots | **2.2.2**（`pip install SciencePlots`） |
| nature-skills | `C:\Users\Administrator\.cursor\skills\nature-skills`（GitHub Yuan1z0825/nature-skills） |
| 相图 CSV | `outputs/phase_diagram.csv`（4 行；VA 1 / Non-VA 3） |
| 字体 | **Times New Roman 可用**（无回退） |

## 独立测试结果

| 检查 | 结果 |
|------|------|
| `$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD=1; python -m pytest tests/ -q` | **42 passed**（≈56.6 s） |
| `python scripts/plot_science.py` | styles=`['science','no-latex']`；20 个 PNG/PDF |
| 相图产物 | 仍为 annulus fast：**n_va=1, n_non_va=3** |
| LBM-GPU / Zenodo 多 GB | **未运行/未下载**（按设计） |

## 本轮实际改动（本地）

1. `cardiac_ms/plotting.py` — SciencePlots 样式 + TNR + 300 dpi 保存  
2. `scripts/plot_science.py` — 重绘相图 / 0D AP / 验证条图 / 扩散对比 / mono2d  
3. `scripts/run_phase_diagram.py` — 热图改为 SciencePlots（若可用）  
4. `requirements.txt` — 增加 `SciencePlots>=2.1.0`  
5. `papers/outline.md`, `papers/manuscript_draft.md`, `papers/figures/*`  
6. `docs/nature-skills/INSTALL.md`, `docs/chatgpt/2026-08-16_paper_framework_task.md`  
7. 本报告  

### 图件（SciencePlots）

| 图 | 路径 |
|----|------|
| 相图 | `outputs/figures/fig_phase_diagram.png` / `.pdf`（镜像 `papers/figures/`） |
| 0D AP | `fig_ms_0d_ap` |
| 验证汇总 | `fig_validation_summary` |
| 扩散算子 | `fig_diffusion_compare` |
| 2D u | `fig_mono2d_u` |

![相图](../outputs/figures/fig_phase_diagram.png)

![0D AP](../outputs/figures/fig_ms_0d_ap.png)

![验证](../outputs/figures/fig_validation_summary.png)

## ChatGPT 对话

| 项 | 状态 |
|----|------|
| 对话 URL | **无** |
| 原因 | `browser_tabs` new 可返回 viewId，随后 `browser_navigate` / `browser_lock` 报 *No browser tab available* / *Browser view not found*（与 2026-08-15 相同类故障） |
| 是否登录墙/验证码 | **未到达页面**，非 captcha |
| 任务书 | `docs/chatgpt/2026-08-16_paper_framework_task.md`（请用户在已登录 ChatGPT 中粘贴；开启 web search） |
| 系统默认浏览器 | 已 `Start-Process https://chatgpt.com/` 作为人工入口 |

## P0/P1 vs P2

| 阶段 | 状态 |
|------|------|
| P0 离子/CV/CFL/协议 | **完成** |
| P1 相图（环混合标签）+ 周期 VA 准则 | **完成** |
| P2 各向异性守恒、Niederer/openCARP、完整 4×3、3D/LBM | **开放** |
| 论文写作管线 | **大纲+Methods/Results 骨架+图** 已落盘；英文润色与投稿包未做 |

## 诚实创新框架（已写入手稿）

- **可写：** 开放可测脚手架；周期必需 VA 指标；波长感知环几何；守恒扩散对照  
- **不可写：** 首个 DOX 孪生；3D LBM 性能；合成纤维化=猪 DOX 心肌  

## 提交状态

**仅本地修改，未 git commit / push / PR / deploy。**
