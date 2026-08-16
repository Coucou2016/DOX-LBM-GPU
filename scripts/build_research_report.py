#!/usr/bin/env python
"""Build self-contained academic research report (HTML + Markdown + PDF).

HTML embeds SciencePlots PNGs as base64 data URIs and phase_diagram.csv as
an HTML table. No external CSS/JS/CDN. PDF via Edge/Chrome headless when
available; falls back to documented alternatives.
"""

from __future__ import annotations

import argparse
import base64
import csv
import html
import json
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REPORTS = ROOT / "reports"
FIG_CANDIDATES = (
    ROOT / "papers" / "figures",
    ROOT / "outputs" / "figures",
)
PHASE_CSV_CANDIDATES = (
    ROOT / "outputs" / "phase_diagram.csv",
    ROOT / "papers" / "data" / "phase_diagram.csv",
)
PHASE_SUMMARY_CANDIDATES = (
    ROOT / "outputs" / "phase_diagram_summary.json",
    ROOT / "papers" / "data" / "phase_diagram_summary.json",
)

FIGURE_SPECS = (
    {
        "stem": "fig_ms_0d_ap",
        "num": "图1",
        "title": "经典 Mitchell–Schaeffer 零维动作电位与 APD₉₀",
        "caption": "seed=42 的 0D 仿真；虚线标出激活时刻与 APD 终点。",
    },
    {
        "stem": "fig_validation_summary",
        "num": "图2",
        "title": "验证汇总：0D APD、均匀 2D CV、快速相图计数",
        "caption": "灰带为预设可接受带宽；CV 目标线 0.70 mm/ms；相图为钉扎环 2×2 快扫。",
    },
    {
        "stem": "fig_phase_diagram",
        "num": "图3",
        "title": "钉扎环 λ_fib × D_fib 诱发性相图（1 VA / 3 Non-VA）",
        "caption": "暖色=VA，冷色=Non-VA；唯一 VA 格点为 λ=0.01 且 D↓90%。",
    },
    {
        "stem": "fig_diffusion_compare",
        "num": "图4",
        "title": "扩散算子对照：∇·(D∇u) 与 D∇²u 的激活持续",
        "caption": "异质 D 下捷径算子可改变 persist，标签未必翻转。",
    },
    {
        "stem": "fig_mono2d_u",
        "num": "图5",
        "title": "均匀二维单域膜电位场快照",
        "caption": "修正 MS、无纤维化短时程仿真终态 u 场。",
    },
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build self-contained research report")
    p.add_argument("--out-dir", type=Path, default=REPORTS)
    p.add_argument("--skip-pdf", action="store_true")
    return p.parse_args()


def find_png(stem: str) -> Path | None:
    for d in FIG_CANDIDATES:
        path = d / f"{stem}.png"
        if path.is_file():
            return path
    return None


def png_data_uri(path: Path) -> str:
    raw = path.read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:image/png;base64,{b64}"


def _first_existing(paths: tuple[Path, ...]) -> Path | None:
    for p in paths:
        if p.is_file():
            return p
    return None


def load_phase_rows() -> list[dict[str, str]]:
    path = _first_existing(PHASE_CSV_CANDIDATES)
    if path is None:
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_phase_summary() -> dict:
    path = _first_existing(PHASE_SUMMARY_CANDIDATES)
    if path is None:
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def csv_to_html_table(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "<p><em>phase_diagram.csv 缺失（待补充）。</em></p>"
    # Prefer a readable subset, then full dump
    prefer = [
        "geometry",
        "lambda_fib",
        "d_reduction",
        "label",
        "va",
        "activation_persists_ms",
        "n_extra_cycles",
        "n_probes_relapped",
        "path_mm",
        "tau_close",
        "dx",
        "nx",
        "ny",
    ]
    keys = [k for k in prefer if k in rows[0]] + [
        k for k in rows[0].keys() if k not in prefer
    ]
    thead = "".join(f"<th>{html.escape(k)}</th>" for k in keys)
    body_rows = []
    for r in rows:
        tds = "".join(f"<td>{html.escape(str(r.get(k, '')))}</td>" for k in keys)
        body_rows.append(f"<tr>{tds}</tr>")
    return (
        '<table class="data"><thead><tr>'
        + thead
        + "</tr></thead><tbody>"
        + "".join(body_rows)
        + "</tbody></table>"
    )


def _html_to_plain(frag: str) -> str:
    import re

    t = re.sub(r"<br\s*/?>", "\n", frag, flags=re.I)
    t = re.sub(r"</p>", "\n\n", t, flags=re.I)
    t = re.sub(r"<[^>]+>", "", t)
    return html.unescape(t).strip()


def figure_block(spec: dict, explanations: dict[str, str]) -> tuple[str, str]:
    """Return (html_fragment, md_fragment)."""
    stem = spec["stem"]
    png = find_png(stem)
    expl = explanations.get(stem, "（待补充详细解读。）")
    if png is None:
        img_html = f"<p class='warn'>图像缺失：{html.escape(stem)}.png（待补充）</p>"
        img_md = f"*图像缺失：`{stem}.png`（待补充）*\n"
    else:
        uri = png_data_uri(png)
        img_html = (
            f'<img class="fig" src="{uri}" alt="{html.escape(spec["title"])}" />'
        )
        try:
            rel = png.relative_to(ROOT).as_posix()
            img_md = f"![{spec['title']}](../{rel})\n"
        except ValueError:
            img_md = f"![{spec['title']}]({png.as_posix()})\n"
    html_frag = f"""
<section class="figure-block" id="{html.escape(stem)}">
  <h3>{html.escape(spec['num'])}. {html.escape(spec['title'])}</h3>
  {img_html}
  <p class="caption"><strong>图注：</strong>{html.escape(spec['caption'])}</p>
  <div class="explain"><h4>来龙去脉与读图说明</h4>
  {expl}
  </div>
</section>
"""
    md_frag = f"""
### {spec['num']}. {spec['title']}

{img_md}
**图注：** {spec['caption']}

#### 来龙去脉与读图说明

{_html_to_plain(expl)}

"""
    return html_frag, md_frag


def figure_explanations_html() -> dict[str, str]:
    """Long teacher-like Chinese explanations (HTML paragraphs)."""
    return {
        "fig_ms_0d_ap": """
<p><strong>故事从哪里来：</strong>在读 Villar-Valero 的三维 LBM 数字孪生之前，必须先确认“细胞级离子核”是否站得住。
他们与本脚手架都采用修正 Mitchell–Schaeffer（MS；Mitchell &amp; Schaeffer 2003；Djabella λ 修正）。
零维（0D，zero-dimensional，无空间耦合）仿真把扩散关掉，只看刺激→去极→复极这条时间线，
因此是整条管线最便宜、也最硬的黄金回归点。</p>
<p><strong>为何画这张图：</strong>动作电位时程 APD<sub>90</sub>
（action potential duration to 90% recovery）直接进入波长
λ<sub>wave</sub>≈CV×APD。若 0D APD 漂了，后面所有“圆盘放不下波长 / 钉扎环刚好能折返”
的几何讨论都会失锚。</p>
<p><strong>面板怎么读（教师逐步）：</strong></p>
<ul>
<li>横轴：时间（ms）；纵轴：归一化膜电位 u（无量纲，<em>不是</em> mV）。</li>
<li>上升沿：刺激激活；平台与复极：决定 APD<sub>90</sub>。</li>
<li>虚线：激活时刻与 APD 终点标记；本机黄金回归约 <strong>256.6 ms</strong>（容差 ±8 ms）。</li>
<li>seed=42：保证演示可复现，不是生物学重复。</li>
</ul>
<p><strong>常见误读：</strong>把这条曲线当成“已经证明折返”。0D 没有空间，谈不上折返；
它只证明离子核与参考包一致。</p>
<p><strong>结论：</strong>0D 端与 finitewave MS 包一致，为后续二维 CV 标定、波长估计与折返协议提供可信离子核。</p>
""",
        "fig_validation_summary": """
<p><strong>故事从哪里来：</strong>协议对齐需要三块独立证据同时成立：
(1) 离子时程；(2) 健康传导速度量级；(3) 相图能同时给出 VA 与 Non-VA。
任何一块单独通过都不够——例如 CV 对了但终点定义过松，仍会把平台期算成 VA。</p>
<p><strong>为何画这张图：</strong>把三项验证压成一眼可读的总览，方便答辩/组会时先回答
“脚手架有没有跑通到量级正确”，再进入单张机制图。</p>
<p><strong>面板怎么读（教师逐步）：</strong></p>
<ul>
<li><strong>左栏（0D APD）：</strong>灰带为预设可接受带宽；点应落在带内（≈256.6 ms）。</li>
<li><strong>中栏（均匀 2D CV）：</strong>灰带 0.55–0.85 mm/ms；虚线目标 <strong>0.70 mm/ms</strong>
（数值上等于论文健康纤维向 ≈0.7 m/s）。CV 由标定扩散系数 D 得到。</li>
<li><strong>右栏（快速相图计数）：</strong>钉扎环 2×2 快扫，期望 <strong>1 VA / 3 Non-VA</strong>。
若变成 0/4，优先怀疑几何放不下波长；若变成 4/4，优先怀疑终点过松。</li>
</ul>
<p><strong>常见误读：</strong>把“灰带内”理解成临床精度。这里是方法学量级锚定，不是猪心实测拟合。</p>
<p><strong>结论：</strong>离子时程、健康纤维向量级 CV、以及可同时出现正负标签的相图三者同屏成立。</p>
""",
        "fig_phase_diagram": """
<p><strong>故事从哪里来：</strong>Villar-Valero 在三维个性化左室上对 λ 与传导做参数扫描。
本图是同一问题在<strong>开放二维脚手架</strong>上的最小可解释对应物：不是复现猪 LV 定量结果，
而是检验“终点 + 几何 + 离子/扩散参数”能否给出机制可讲的混合相图。</p>
<p><strong>为何默认是钉扎环而不是论文式小圆盘：</strong>
健康 λ<sub>wave</sub>≈0.70×250≈<strong>175 mm</strong>；48²×0.5 mm 圆盘直径约 <strong>24 mm</strong>，
几何上几乎必然全 Non-VA（阴性对照有用，但不适合当主相图）。钉扎环平均路径约 <strong>107 mm</strong>，
夹在健康波长与强减速波长之间，才可能出现混合标签。</p>
<p><strong>面板怎么读（教师逐步）：</strong></p>
<ul>
<li>横轴：纤维化区扩散降幅 D<sub>fib</sub> reduction（传导变慢）。</li>
<li>纵轴：兴奋性参数 λ<sub>fib</sub>（Djabella：抬高内向电流阈值；健康 0.01，0.3 近功能阻滞）。</li>
<li>暖色=VA，冷色=Non-VA；默认快扫仅 4 格。</li>
<li>唯一 VA：<strong>λ=0.01 × D↓90%</strong>。此时 CV≈√0.1×0.70≈0.22 mm/ms，波长≈55 mm &lt; 107 mm，几何允许折返，
且周期必需准则看到再兴奋（extra / probes）。</li>
<li>λ=0.3 两格：接近阻滞 → Non-VA；D↓30%×λ=0.01：波长仍偏长 → Non-VA。</li>
</ul>
<p><strong>与表1对照：</strong>读图时必须同时看 <code>n_extra_cycles</code> / <code>n_probes_relapped</code>。
仅 persist≥1000 ms 不够——平台滞留会被判 Non-VA。</p>
<p><strong>结论：</strong>在要求再兴奋周期的 VA 准则下，相图是机制可解释的 1/3 混合，而不是“全阴/全阳”假象。</p>
""",
        "fig_diffusion_compare": """
<p><strong>故事从哪里来：</strong>单域方程的扩散项在数学上应是守恒形式 ∇·(D∇u)。
许多原型代码在均匀 D 时写 D∇²u 没问题，但一旦 D 空间变化（纤维化降导），捷径算子会引入非守恒误差，
可能改变局部电流与激活持续。</p>
<p><strong>为何画这张图：</strong>把“数值诚实性”做成可看证据：异质 D 下两算子的 persist 是否一致；
标签会不会翻转。这不是炫技，而是告诉审稿人：我们默认用守恒格式，并量化捷径风险。</p>
<p><strong>面板怎么读（教师逐步）：</strong></p>
<ul>
<li>分组柱：不同耦合间期 CI（coupling interval）。</li>
<li>比较量：激活持续时长 persist（ms），不是直接的空间误差范数。</li>
<li>观察：persist 可差数十毫秒；在本协议下标签未必翻转——说明终点有时对算子误差不敏感，
<strong>但不能</strong>据此声称捷径永远安全。</li>
</ul>
<p><strong>常见误读：</strong>“标签没翻 = 两算子等价”。不等价；只是本网格/本终点下未跨过分类阈值。</p>
<p><strong>结论：</strong>脚手架默认守恒扩散；对照实验保留为异质介质下的数值诚实性证据。</p>
""",
        "fig_mono2d_u": """
<p><strong>故事从哪里来：</strong>读者在看完 0D 与相图后，仍可能怀疑“二维求解器是否真的在空间上传波”。
本快照给出最短的视觉确认：均匀组织、无纤维化、短时程终态的膜电位场。</p>
<p><strong>为何画这张图：</strong>它是管线烟雾测试（smoke test）的空间证据，
证明 <code>ms_2d</code> 求解器在跑，而不是只输出标量指标。</p>
<p><strong>面板怎么读（教师逐步）：</strong></p>
<ul>
<li>颜色：归一化膜电位 u∈[0,1]。</li>
<li>几何：均匀二维单域；本图<strong>无</strong>纤维化掩膜。</li>
<li>时相：短时程终态快照——用于可视检查，不是诱发协议窗口。</li>
</ul>
<p><strong>严禁过度解读：</strong>本图<strong>不是</strong>折返阳性证据，也<strong>不能</strong>替代 S1–S2 + 周期准则 + 相图。
若只展示漂亮的 u 场却不做终点硬化，会重复早期“平台期假阳性”陷阱。</p>
<p><strong>结论：</strong>2D 求解器可运行；折返结论必须以协议分类与相图为准。</p>
""",
    }


def prose_sections() -> dict[str, str]:
    """Major Chinese sections as HTML."""
    today = date.today().isoformat()
    return {
        "cover_meta": f"生成日期：{today} · 仓库：DOX-LBM_GPU · 性质：方法与验证研究报告（非临床决策工具）",
        "abstract": """
<p>阿霉素（DOX，doxorubicin，蒽环类化疗药）相关弥漫纤维化可构成室性心律失常（VA，ventricular arrhythmia）基质。
Villar-Valero 等（STACOM 2024 / <em>J Physiol</em> 2025，doi:10.1113/jp288819）用 MRI 个性化三维左室、
修正 Mitchell–Schaeffer（MS，含兴奋性参数 λ）与 GPU 格子 Boltzmann（LBM，Lattice–Boltzmann Method）单域求解器，
在纤维化兴奋性与传导参数空间扫描诱发性。Chabiniok &amp; Zaha（doi:10.1113/jp290313）评述强调：数字孪生要走向临床，
需“打开方法”（可复现、可本地运行、可让临床科学家参与）。</p>
<p>当该 LBM–GPU 源码不可用时，本仓库提供开放的 <strong>CPU 二维有限差分单域脚手架</strong>：对齐修正 MS、守恒扩散、
合成三相纤维化、S1–S2（含 extras 240/200/190 ms），标定健康 CV≈0.70 mm/ms，并引入<strong>要求再兴奋周期</strong>的 VA 分类，
以避免平台期 / 单圈假阳性。因健康波长≈175 mm 远大于小圆盘≈24 mm，默认采用钉扎环（路径≈107 mm），
快速相图得到 <strong>1 VA / 3 Non-VA</strong>。本报告汇总证据链、图件与局限；<strong>不是</strong>三维 DOX 孪生复现。</p>
""",
        "background": """
<p><strong>研究动机。</strong>化疗心毒性传统关注射血分数下降；组织纤维化与电重构亦可形成折返基质。
个性化心脏数字孪生（digital twin）把影像解剖与电生理方程结合，用于虚拟诱发试验。</p>
<p><strong>Villar-Valero 做了什么。</strong>猪 DOX 模型 + MRI/LGE 三维左室；修正 MS（Djabella λ）；
LBM–GPU 单域；对 λ 与扩散做参数扫描，报告纤维化底物可诱发恶性 VA。其贡献是<strong>成像驱动的三维个性化孪生与高通量扫描</strong>。</p>
<p><strong>Chabiniok–Zaha 强调什么。</strong>孪生潜力大，但建模方法与临床落地之间仍有鸿沟；下一步应开放方法、
降低使用门槛，并推进更大规模验证。</p>
<p><strong>本脚手架的定位。</strong>在求解器源码缺失时，提供可 pytest 的协议对齐层：离子律、刺激协议、
终点定义、波长–几何一致性与扩散算子诚实性。它回答“协议能否在开放 2D 上被压力测试”，
而不是“能否复现猪 LV 的 LBM 定量结果”。</p>
<p><strong>文献写作架构建议（独立检索，ChatGPT 浏览器会话未建立）：</strong>
(1) Villar-Valero 2025——参数扫描与 VA 终点主叙事；
(2) Chabiniok &amp; Zaha 评述——转化框架；
(3) Campos 等 Frontiers Physiol 2024（纤维化表示影响 VA 形态，openCARP）——方法对照与纤维化建模选择；
(4) CardioMat / Comput Biol Med 2024——工具箱式 methods 论文结构；
(5) 验证导向的 mono-domain / openCARP 类方法文——CFL、黄金测试、代码可用性专节。
目标期刊宜偏 methods / 计算生理，而非旗舰 <em>Nature</em>。</p>
""",
        "aims": """
<ol>
<li>实现并验证含 λ 的修正 MS 与守恒二维单域。</li>
<li>将均匀组织 CV 标定到论文健康纤维向量级（≈0.70 mm/ms）。</li>
<li>对齐 S1–S2 与 extras，硬化 VA 终点（周期必需）。</li>
<li>用波长感知几何获得可解释的混合相图。</li>
<li>用 SciencePlots + TNR/CJK 字体输出可嵌入报告的出版风格图。</li>
</ol>
""",
        "data_methods": """
<p><strong>数据。</strong>本阶段以合成几何与合成三相纤维化为主；未下载 Zenodo 多 GB 猪 MI 数据
（且 MI≠DOX）。外部求解器 MonoAlg3D 仅作指针，未在本机 CUDA 全编译。</p>
<p><strong>方程。</strong>单域反应–扩散：∂t u = ∇·(D∇u) + J_in(h,u,λ) − u/τ_out + J_stim；
门控 h 按 u 与 u_gate 在 open/close 之间切换。健康 λ=0.01；纤维化扫描 λ∈{0.01,0.1,0.2,0.3}。</p>
<p><strong>数值。</strong>显式欧拉 + 五点守恒扩散；CFL：Δt≤Δx²/(4D_max)，另离子上限 0.1 ms。
刺激为区域电压钳（非论文电流脉冲）——差异已写入 ASSUMPTIONS。</p>
<p><strong>协议。</strong>S1 BCL=400 ms，n=3；extras 默认 240/200/190 ms。VA 默认 require_cycle=True：
仅 persist≥1000 ms 不算 VA；需 extra≥1 或 n_probes_relapped≥3。</p>
<p><strong>几何。</strong>圆盘阴性对照 vs 钉扎环主相图（见结果节波长讨论）。</p>
""",
        "process": """
<ol>
<li>P0：修复门控 dt、引入 λ-MS、CV 标定、守恒扩散、S1–S2。</li>
<li>发现小圆盘相图全 Non-VA → 波长审计（175 mm vs 24 mm）。</li>
<li>改默认钉扎环；发现平台期假阳性 → 周期必需准则 + 单 CI 负对照测试。</li>
<li>默认环相图稳定为 1 VA / 3 Non-VA；pytest 42 passed。</li>
<li>SciencePlots 重绘；本脚本生成自包含 HTML/MD/PDF 研究报告。</li>
</ol>
""",
        "analysis": """
<p><strong>与 Villar-Valero 的关系。</strong>共享：修正 MS+λ、单域思想、纤维化参数扫描、S1–S2 诱发逻辑。
不共享：3D 猪 LV、LBM–GPU、真实 LGE 纤维化分布、临床级吞吐量。因此创新点应表述为
<strong>开放可测的协议脚手架与终点/几何硬化</strong>，而非“首个 DOX 孪生”。</p>
<p><strong>与 Chabiniok–Zaha 的关系。</strong>评述呼吁打开方法；本仓库以 CPU、pytest、文档化假设响应这一呼吁的
“可复现入口”，但尚未提供临床 GUI，也未缩小影像–模型鸿沟。</p>
<p><strong>平台期 vs 真折返。</strong>D↓90% 细胞上，单次早搏可出现 persist≥1000 但 extra=0（平台滞留）→ Non-VA；
论文 extras 训练可出现再兴奋 → VA。二者共存说明终点定义必须写进方法学，否则相图不可比。</p>
""",
        "conclusions": """
<ol>
<li>开放 2D 修正 MS 单域脚手架可在无 LBM 源码时对齐关键协议要素。</li>
<li>CV≈0.70 mm/ms 与 0D APD 黄金回归提供量级锚定。</li>
<li>周期必需 VA 准则消除平台/单圈假阳性。</li>
<li>波长感知环几何恢复混合相图（1 VA / 3 Non-VA）。</li>
<li>工作边界清晰：非 3D LBM、非猪 DOX 数据复现、非临床工具。</li>
</ol>
""",
        "limitations": """
<ul>
<li>二维 FD ≠ 三维 LBM；无真实纤维场 / Purkinje / 双向域。</li>
<li>合成纤维化 ≠ DOX 猪心肌 ≠ 缺血性 MI。</li>
<li>完整 4×3 相图、Niederer/openCARP/MonoAlg3D 交叉验证仍为 P2（待补充）。</li>
<li>ChatGPT 浏览器顾问会话因 Cursor 内置浏览器标签无法维持而未建立 URL（见 §十九）。</li>
<li>各向异性传导仍为桩实现。</li>
</ul>
""",
    }


def css() -> str:
    return """
:root {
  --fg: #1a1a1a;
  --muted: #444;
  --line: #c8c8c8;
  --bg: #fbfbf8;
  --card: #ffffff;
  --accent: #1f4e79;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  color: var(--fg);
  background: linear-gradient(180deg, #eef2f6 0%, var(--bg) 280px);
  font-family: "Times New Roman", "SimSun", "Microsoft YaHei", "Noto Serif CJK SC", serif;
  line-height: 1.65;
  font-size: 16px;
}
.wrap { max-width: 920px; margin: 0 auto; padding: 28px 22px 64px; }
.cover {
  background: var(--card);
  border: 1px solid var(--line);
  padding: 36px 28px;
  margin-bottom: 28px;
}
.cover h1 {
  font-size: 1.55rem;
  color: var(--accent);
  margin: 0 0 12px;
  line-height: 1.35;
}
.cover .meta { color: var(--muted); font-size: 0.95rem; }
nav.toc {
  background: var(--card);
  border: 1px solid var(--line);
  padding: 18px 22px;
  margin-bottom: 28px;
}
nav.toc ol { margin: 8px 0 0 1.2em; padding: 0; }
nav.toc a { color: var(--accent); text-decoration: none; }
nav.toc a:hover { text-decoration: underline; }
section.block {
  background: var(--card);
  border: 1px solid var(--line);
  padding: 22px 24px;
  margin-bottom: 22px;
}
section.block h2 {
  margin-top: 0;
  color: var(--accent);
  border-bottom: 1px solid var(--line);
  padding-bottom: 8px;
  font-size: 1.25rem;
}
.figure-block { margin: 22px 0; }
.figure-block h3 { font-size: 1.05rem; margin-bottom: 10px; }
img.fig {
  display: block;
  width: 100%;
  max-width: 680px;
  height: auto;
  margin: 0 auto 10px;
  border: 1px solid #ddd;
}
.caption { color: var(--muted); font-size: 0.95rem; }
.explain {
  background: #f5f7fa;
  border-left: 3px solid var(--accent);
  padding: 10px 14px;
  margin-top: 10px;
}
.explain h4 { margin: 0 0 8px; font-size: 0.98rem; }
table.data {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.82rem;
  overflow-x: auto;
  display: block;
}
table.data th, table.data td {
  border: 1px solid var(--line);
  padding: 5px 7px;
  text-align: left;
  white-space: nowrap;
}
table.data th { background: #e8eef5; }
.warn { color: #8a1f1f; }
footer {
  color: var(--muted);
  font-size: 0.9rem;
  margin-top: 28px;
  text-align: center;
}
@media print {
  body { background: #fff; }
  .wrap { max-width: 100%; padding: 0; }
  section.block, .cover, nav.toc { break-inside: avoid; }
}
"""


def build_html(
    table_html: str,
    fig_html: str,
    sections: dict[str, str],
) -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>DOX-LBM_GPU 学术研究报告</title>
<style>
{css()}
</style>
</head>
<body>
<div class="wrap">
  <header class="cover" id="cover">
    <h1>DOX 纤维化折返协议的开放二维单域脚手架：学术研究报告</h1>
    <p><strong>副标题：</strong>在三维 LBM–GPU 数字孪生源码不可用时的方法对齐、波长感知几何与周期必需 VA 终点</p>
    <p class="meta">{html.escape(sections['cover_meta'])}</p>
    <p class="meta">对照文献：Villar-Valero et al., <em>J Physiol</em> 2025 (doi:10.1113/jp288819)；
    Chabiniok &amp; Zaha (doi:10.1113/jp290313)</p>
  </header>

  <nav class="toc" id="toc">
    <strong>目录</strong>
    <ol>
      <li><a href="#abstract">摘要</a></li>
      <li><a href="#background">背景与目标</a></li>
      <li><a href="#methods">数据与方法</a></li>
      <li><a href="#process">研究过程</a></li>
      <li><a href="#results">结果</a></li>
      <li><a href="#analysis">分析与讨论</a></li>
      <li><a href="#conclusions">结论</a></li>
      <li><a href="#limitations">局限与展望</a></li>
    </ol>
  </nav>

  <section class="block" id="abstract">
    <h2>一、摘要</h2>
    {sections['abstract']}
  </section>

  <section class="block" id="background">
    <h2>二、背景与目标</h2>
    <h3>2.1 背景</h3>
    {sections['background']}
    <h3>2.2 目标</h3>
    {sections['aims']}
  </section>

  <section class="block" id="methods">
    <h2>三、数据与方法</h2>
    {sections['data_methods']}
  </section>

  <section class="block" id="process">
    <h2>四、研究过程</h2>
    {sections['process']}
  </section>

  <section class="block" id="results">
    <h2>五、结果</h2>
    <h3>5.1 相图表（嵌入自 phase_diagram.csv）</h3>
    <p><strong>表1. 钉扎环快速相图原始记录。</strong>
    标签列 label 为协议输出；va=1 表示周期必需准则下的 VA。</p>
    {table_html}
    <p class="caption"><strong>表注：</strong>path_mm≈107 为环平均路径；tau_close=150 ms 保持健康复极时程设定。
    观察窗 observe_ms=1000。勿将 persist 单独等同于 VA。</p>
    <div class="explain">
      <h4>来龙去脉与读表说明</h4>
      <p>四行对应 λ∈{{0.01,0.3}} × D↓∈{{30%,90%}}。请同时看
      <code>n_extra_cycles</code> 与 <code>n_probes_relapped</code>：VA 行应显示再兴奋证据；
      Non-VA 行即使 persist 较长也可能是平台期。这是本脚手架相对“仅 persist≥1000”论文式简化终点的关键硬化。</p>
    </div>
    <h3>5.2 图件（SciencePlots，Base64 内嵌）</h3>
    {fig_html}
  </section>

  <section class="block" id="analysis">
    <h2>六、分析与讨论</h2>
    {sections['analysis']}
  </section>

  <section class="block" id="conclusions">
    <h2>七、结论</h2>
    {sections['conclusions']}
  </section>

  <section class="block" id="limitations">
    <h2>八、局限与展望</h2>
    {sections['limitations']}
    <p>展望：完整 4×3 扫描、各向异性守恒实现、openCARP/MonoAlg3D 交叉、在获得授权数据后的影像驱动几何——均标记为<strong>待补充</strong>。</p>
  </section>

  <footer>
    自包含 HTML：无外部 CSS/CDN；图像均为 data:image/png;base64。生成脚本
    <code>scripts/build_research_report.py</code>。
  </footer>
</div>
</body>
</html>
"""


def build_markdown(
    table_md: str,
    fig_md: str,
    sections: dict[str, str],
    summary: dict,
) -> str:
    # strip tags lightly for MD body sections
    import re

    def to_md(html_frag: str) -> str:
        t = html_frag
        t = re.sub(r"<br\s*/?>", "\n", t, flags=re.I)
        t = re.sub(r"</p>", "\n\n", t, flags=re.I)
        t = re.sub(r"</li>", "\n", t, flags=re.I)
        t = re.sub(r"<li>", "- ", t, flags=re.I)
        t = re.sub(r"<[^>]+>", "", t)
        t = html.unescape(t)
        return t.strip() + "\n"

    n_va = summary.get("n_va", "待补充")
    n_non = summary.get("n_non_va", "待补充")
    return f"""# DOX 纤维化折返协议的开放二维单域脚手架：学术研究报告

{sections['cover_meta']}

对照：Villar-Valero et al., J Physiol 2025 (doi:10.1113/jp288819)；Chabiniok & Zaha (doi:10.1113/jp290313)。
相图摘要：VA={n_va} / Non-VA={n_non}。

## 目录

1. 摘要
2. 背景与目标
3. 数据与方法
4. 研究过程
5. 结果
6. 分析与讨论
7. 结论
8. 局限与展望

## 一、摘要

{to_md(sections['abstract'])}

## 二、背景与目标

### 2.1 背景

{to_md(sections['background'])}

### 2.2 目标

{to_md(sections['aims'])}

## 三、数据与方法

{to_md(sections['data_methods'])}

## 四、研究过程

{to_md(sections['process'])}

## 五、结果

### 表1. phase_diagram.csv

{table_md}

{fig_md}

## 六、分析与讨论

{to_md(sections['analysis'])}

## 七、结论

{to_md(sections['conclusions'])}

## 八、局限与展望

{to_md(sections['limitations'])}
"""


def rows_to_md_table(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "_phase_diagram.csv 缺失（待补充）_\n"
    keys = [
        "geometry",
        "lambda_fib",
        "d_reduction",
        "label",
        "va",
        "activation_persists_ms",
        "n_extra_cycles",
        "n_probes_relapped",
        "path_mm",
    ]
    keys = [k for k in keys if k in rows[0]]
    header = "| " + " | ".join(keys) + " |"
    sep = "| " + " | ".join("---" for _ in keys) + " |"
    lines = [header, sep]
    for r in rows:
        lines.append("| " + " | ".join(str(r.get(k, "")) for k in keys) + " |")
    return "\n".join(lines) + "\n"


def find_browser() -> Path | None:
    candidates = [
        Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    ]
    for c in candidates:
        if c.is_file():
            return c
    # PATH lookup
    for name in ("msedge", "chrome", "chromium"):
        which = shutil.which(name)
        if which:
            return Path(which)
    return None


def html_to_pdf(html_path: Path, pdf_path: Path) -> str:
    """Return method description that succeeded, or raise."""
    browser = find_browser()
    if browser is not None:
        # file:/// URL for Windows
        uri = html_path.resolve().as_uri()
        cmd = [
            str(browser),
            "--headless",
            "--disable-gpu",
            f"--print-to-pdf={pdf_path}",
            "--no-pdf-header-footer",
            uri,
        ]
        proc = subprocess.run(
            cmd,
            capture_output=True,
            timeout=120,
            encoding="utf-8",
            errors="replace",
        )
        if pdf_path.is_file() and pdf_path.stat().st_size > 1000:
            return f"headless browser print-to-pdf ({browser.name})"
        raise RuntimeError(
            f"Browser PDF failed rc={proc.returncode}: {proc.stderr[-500:]}"
        )

    # try weasyprint
    try:
        from weasyprint import HTML  # type: ignore

        HTML(filename=str(html_path)).write_pdf(str(pdf_path))
        if pdf_path.is_file() and pdf_path.stat().st_size > 1000:
            return "weasyprint"
    except Exception as exc:
        last = f"weasyprint: {exc}"
    else:
        last = "weasyprint produced empty file"

    # pandoc
    pandoc = shutil.which("pandoc")
    if pandoc:
        md = html_path.with_suffix(".md")
        if md.is_file():
            proc = subprocess.run(
                [pandoc, str(md), "-o", str(pdf_path)],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if pdf_path.is_file() and pdf_path.stat().st_size > 500:
                return "pandoc markdown→pdf"
            last = f"pandoc failed: {proc.stderr[-300:]}"

    raise RuntimeError(f"No PDF method succeeded. Last: {last}")


def main() -> int:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    rows = load_phase_rows()
    summary = load_phase_summary()
    sections = prose_sections()
    expl = figure_explanations_html()

    fig_html_parts = []
    fig_md_parts = []
    missing = []
    for spec in FIGURE_SPECS:
        h, m = figure_block(spec, expl)
        fig_html_parts.append(h)
        fig_md_parts.append(m)
        if find_png(spec["stem"]) is None:
            missing.append(spec["stem"])

    table_html = csv_to_html_table(rows)
    html_doc = build_html(table_html, "\n".join(fig_html_parts), sections)
    md_doc = build_markdown(
        rows_to_md_table(rows), "\n".join(fig_md_parts), sections, summary
    )

    html_path = args.out_dir / "research_report.html"
    md_path = args.out_dir / "research_report.md"
    pdf_path = args.out_dir / "research_report.pdf"
    report_html = args.out_dir / "report.html"

    html_path.write_text(html_doc, encoding="utf-8")
    md_path.write_text(md_doc, encoding="utf-8")
    shutil.copy2(html_path, report_html)

    # sanity
    assert "<!DOCTYPE html>" in html_doc
    assert "data:image" in html_doc or missing
    assert "Times New Roman" in html_doc

    pdf_method = "skipped"
    if not args.skip_pdf:
        try:
            pdf_method = html_to_pdf(html_path, pdf_path)
        except Exception as exc:
            pdf_method = f"FAILED: {exc}"
            # last-resort: write a tiny note file
            (args.out_dir / "PDF_METHOD.txt").write_text(
                pdf_method + "\n", encoding="utf-8"
            )

    meta = {
        "html": str(html_path),
        "report_html": str(report_html),
        "md": str(md_path),
        "pdf": str(pdf_path) if pdf_path.is_file() else None,
        "pdf_method": pdf_method,
        "html_bytes": html_path.stat().st_size,
        "md_bytes": md_path.stat().st_size,
        "pdf_bytes": pdf_path.stat().st_size if pdf_path.is_file() else 0,
        "n_phase_rows": len(rows),
        "missing_figures": missing,
        "has_data_uri": "data:image" in html_doc,
    }
    (args.out_dir / "research_report_build.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    if pdf_path.is_file():
        (args.out_dir / "PDF_METHOD.txt").write_text(pdf_method + "\n", encoding="utf-8")
    print(json.dumps(meta, indent=2, ensure_ascii=False))
    return 0 if meta["has_data_uri"] and meta["md_bytes"] > 1000 else 1


if __name__ == "__main__":
    raise SystemExit(main())
