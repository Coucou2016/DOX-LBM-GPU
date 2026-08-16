# §十九 双代理进度报告（中文）

**日期：** 2026-08-16  
**角色：** Cursor 主执行；ChatGPT 外部顾问（仅文本粘贴；本轮浏览器会话未建立）  
**工作区：** `E:\Projects\20260522-DOX-LBM_GPU`  
**Git：** 无 `.git`；未 commit / push / PR / deploy  

---

## 1. 本轮目标完成度

| 要求 | 状态 |
|------|------|
| 检查进度并继续推进 | ✅ P0/P1 已稳；本轮聚焦图件字体、论文框架、自包含研究报告 |
| 咨询 ChatGPT（web search）并保存对话 URL | ⚠️ **未完成 URL**：Cursor 内置浏览器无法维持标签（`No browser tab available` / 创建后消失）；非登录墙/验证码。任务书已更新供人工粘贴 |
| 本地 WebSearch 文献补位 | ✅ 已检索并写入 `papers/outline.md` / 手稿 Related work |
| SciencePlots + TNR + CJK | ✅ 重绘；相图中文轴标正确（SimHei/.ttf 优先路径；YaHei 亦可用） |
| nature-skills 写作 | ✅ 按 `nature-writing` methods 轴更新 `papers/manuscript_draft.md`、`outline.md` |
| `papers/` 文稿 | ✅ 已有并增强 Related work |
| 自包含 HTML + MD + PDF 研究报告 | ✅ 见下方路径 |

---

## 2. 独立验证

| 检查 | 结果 |
|------|------|
| `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/ -q` | **42 passed**（≈65 s） |
| `python scripts/plot_science.py` | 20 个 PNG/PDF；CJK 烟测通过 |
| `python scripts/build_research_report.py` | HTML 含 `<!DOCTYPE html>` 与 `data:image`；PDF 成功 |
| 相图 CSV | 钉扎环 4 行：**VA 1 / Non-VA 3**（仅 λ=0.01 × D↓90%） |
| 字体 | Times New Roman ✅；SimHei/YaHei/SimSun ✅ |

---

## 3. ChatGPT / 文献顾问

| 项 | 内容 |
|----|------|
| 对话 URL | **无** |
| 阻塞 | `browser_tabs` new 后 `browser_navigate` / lock 报 *No browser tab available* / *Browser view not found*（与 2026-08-15 同类） |
| 是否 captcha | 否（未到页面） |
| 任务书 | `docs/chatgpt/2026-08-16_paper_framework_task.md`（请用户在已登录 ChatGPT 粘贴，开启 web search） |
| Cursor 独立文献判断（可采纳） | (1) Villar-Valero *J Physiol* 2025 doi:10.1113/jp288819 — 主对照；(2) Chabiniok & Zaha doi:10.1113/jp290313 — “打开方法”；(3) Campos *Front Physiol* 2024 — 纤维化表示与诱发阶梯；(4) CardioMat *Comput Biol Med* 2024 — 工具箱 methods 结构；(5) openCARP/验证文化 — 复现专节 |
| 写作架构建议 | Title/Abstract → Intro（缺口=闭源 LBM+波长）→ Related → Methods（λ-MS、守恒扩散、周期 VA、环几何）→ Results（APD/CV/相图/对照）→ Discussion（诚实边界）→ Code availability |
| 诚实创新 | 开放可测脚手架；周期必需 VA；波长感知环；守恒扩散对照。**禁止**：首个 DOX 孪生；3D LBM 性能；合成纤维化=猪 DOX |

---

## 4. 关键交付物路径

### 研究报告（本轮关键新增）

| 文件 | 路径 | 备注 |
|------|------|------|
| HTML（自包含） | `reports/research_report.html` | Base64 图 + 内联 CSS + HTML 表 |
| HTML 副本 | `reports/report.html` | 同内容拷贝 |
| Markdown | `reports/research_report.md` | 对应正文 |
| PDF | `reports/research_report.pdf` | **方法：Edge headless `--print-to-pdf`** |
| 构建元数据 | `reports/research_report_build.json` | 含 pdf_method |
| PDF 方法记录 | `reports/PDF_METHOD.txt` | `headless browser print-to-pdf (msedge.exe)` |

### 论文与图件

| 文件 | 路径 |
|------|------|
| 手稿草稿 | `papers/manuscript_draft.md` |
| 大纲/框架 | `papers/outline.md` |
| 图件 | `papers/figures/fig_*.png` 与 `.pdf`（镜像 `outputs/figures/`） |

### 脚本与绘图

| 文件 | 路径 |
|------|------|
| 报告生成器 | `scripts/build_research_report.py` |
| SciencePlots 重绘 | `scripts/plot_science.py` |
| 字体模块 | `cardiac_ms/plotting.py`（TNR + CJK；`text_fontproperties`） |

### 其他报告

| 文件 | 路径 |
|------|------|
| 本文件（§十九） | `reports/2026-08-16_research_report_deliverable.md` |
| 此前论文框架进度 | `reports/2026-08-16_paper_framework_progress.md` |

---

## 5. 科学要点（写入报告正文，此处摘要）

- **波长：** 健康 ≈175 mm；小圆盘 ≈24 mm（阴性对照）；钉扎环路径 ≈107 mm（主相图）。  
- **VA 准则：** 要求再兴奋（extra≥1 或 relapped≥3）；拒绝平台期 / 单圈假阳性。  
- **相图：** 1 VA / 3 Non-VA；唯一 VA = λ=0.01 × D↓90%。  
- **CV：** 标定目标 0.70 mm/ms（带宽 0.55–0.85）。  
- **边界：** 非 3D LBM；非猪 DOX 数据；合成纤维化 ≠ MI。

---

## 6. P2 开放项（待补充）

- 完整 4×3 相图强制归档  
- 各向异性守恒实现  
- Niederer / openCARP / MonoAlg3D 交叉验证  
- Zenodo 大数据（注意 MI≠DOX）  
- ChatGPT 人工会话 URL 回填  

---

## 7. 提交状态

**仅本地文件变更；未执行 git commit / push / PR / deploy。**
