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
    ROOT / "reports" / "figures",
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
        "caption": "seed=42 的 0D 仿真；虚线标出激活时刻与 APD 终点。本机 APD₉₀=256.6 ms。",
    },
    {
        "stem": "fig_validation_summary",
        "num": "图2",
        "title": "验证汇总：0D APD、均匀 2D CV、三重 VA 终点计数",
        "caption": "灰带为预设可接受带宽；CV 目标线 0.70 mm/ms；右栏为 VA_paper / VA_recurrence / VA_strict（1 / 3 / 1，分母 12）。",
    },
    {
        "stem": "fig_dx_dt_convergence",
        "num": "图3",
        "title": "均匀组织 CV 的空间/时间收敛",
        "caption": "左：Δx∈{0.75,0.5,0.25} mm；右：Δt∈{0.1,0.05,0.025} ms。灰带 0.55–0.85 mm/ms。数值来自本仓库 dx/dt 收敛表（均匀片 CV，不重标 VA）。",
    },
    {
        "stem": "fig_phenotype_calibration",
        "num": "图4",
        "title": "CONTROL/DOX1/DOX2 表型标定：文献目标 vs 本机实测",
        "caption": "灰色=文献 APD/CV 目标（Villar-Valero 锚点）；彩色=本机标定测量。匹配容差 ±10%。",
    },
    {
        "stem": "fig_phase_diagram",
        "num": "图5",
        "title": "钉扎环 λ_fib × D_fib 诱发性相图（默认 VA_recurrence）",
        "caption": "暖色=VA，冷色=Non-VA；完整 4×3 为 VA_recurrence 3 / Non-VA 9。",
    },
    {
        "stem": "fig_diffusion_compare",
        "num": "图6",
        "title": "扩散算子对照：∇·(D∇u) 与 D∇²u 的激活持续",
        "caption": "异质 D 下捷径算子可改变 persist（本协议约差 65 ms），标签未必翻转。",
    },
    {
        "stem": "fig_mono2d_u",
        "num": "图7",
        "title": "均匀二维单域膜电位场快照",
        "caption": "修正 MS、无纤维化短时程仿真终态 u 场（烟雾测试，非折返证据）。",
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
        return "<p><em>phase_diagram.csv 缺失；请运行 scripts/run_phase_diagram.py --full。</em></p>"
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
    expl = explanations.get(stem, "（详见 papers/manuscript_draft.md Results。）")
    if png is None:
        img_html = f"<p class='warn'>图像缺失：{html.escape(stem)}.png（请运行 scripts/plot_science.py）</p>"
        img_md = f"*图像缺失：`{stem}.png`（请运行 scripts/plot_science.py）*\n"
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
<p><strong>故事从哪里来：</strong>在读 Villar-Valero 等（doi:10.1113/jp288819）的三维 LBM 数字孪生之前，
必须先确认“细胞级离子核”是否站得住。他们与本脚手架都采用修正 Mitchell–Schaeffer
（MS；Mitchell &amp; Schaeffer 2003；Djabella 引入的兴奋性参数 λ）。
零维（0D，zero-dimensional，无空间耦合）仿真把扩散关掉，只看刺激→去极→复极这条时间线，
因此是整条管线最便宜、也最硬的黄金回归点——任何后续 CV / 波长 / 折返争论，若 0D 漂了就失去共同坐标系。</p>
<p><strong>为何画这张图：</strong>动作电位时程 APD<sub>90</sub>
（action potential duration to 90% recovery）直接进入波长设计式
λ<sub>wave</sub>≈CV×APD。几何节用名义 APD=250 ms 估算健康波长≈175 mm；
本图给出<strong>可回归的实测 0D APD</strong>（256.6 ms），两者必须分开报告，不能混用。</p>
<p><strong>面板怎么读（教师逐步）：</strong></p>
<ul>
<li>横轴：时间（ms）；纵轴：归一化膜电位 u（无量纲，<em>不是</em> mV，也不是实验贴附电位）。</li>
<li>上升沿：刺激激活；平台与复极：共同决定 APD<sub>90</sub>。</li>
<li>虚线：激活时刻与 APD 终点标记；本机黄金回归 <strong>256.6 ms</strong>（容差 ±8 ms）。</li>
<li>seed=42：保证演示可复现，<em>不是</em>生物学重复，也不是蒙特卡洛置信区间。</li>
<li>与 λ 扫描的关系：本图是经典 MS（λ=0 对照族）时程；纤维化格子上的 λ&gt;0 会抬高内向电流阈值，
但不改变“先钉死 0D 核再谈空间”的验证顺序。</li>
</ul>
<p><strong>常见误读：</strong>(1) 把这条曲线当成“已经证明折返”——0D 没有空间，谈不上折返；
(2) 把 256.6 ms 直接代入三维猪 LV 声称“复现论文 APD”——论文用成像校准，本图只锁脚手架离子核。</p>
<p><strong>与论文/评述的对话：</strong>Chabiniok &amp; Zaha（doi:10.1113/jp290313）强调 MS 便于个性化；
我们这里先做的是更低一层的<strong>可测一致性</strong>：与 finitewave MS 包单步对齐，再进入二维。</p>
<p><strong>结论：</strong>0D 端与参考 MS 包一致，为后续二维 CV 标定、波长估计与折返协议提供可信离子核。</p>
""",
        "fig_validation_summary": """
<p><strong>故事从哪里来：</strong>方法学论文的可信度不来自单点“好看”，而来自<strong>多闸门同时闭合</strong>。
对本脚手架，至少需要三块独立证据：(1) 离子时程（0D APD）；(2) 健康传导速度量级（均匀 2D CV）；
(3) 相图能同时给出 VA 与 Non-VA（说明终点+几何没有塌缩成全阴/全阳）。
任何一块单独通过都不够——例如 CV 对了但终点过松，仍会把平台期算成 VA。</p>
<p><strong>为何画这张图：</strong>把三项验证压成一眼可读的总览，方便答辩/组会先回答
“脚手架有没有跑通到量级正确”，再进入单张机制图与 CSV 细表。它对应 Niederer 2011
（doi:10.1098/rsta.2011.0139）所倡导的验证文化的<strong>轻量本地版</strong>：不是 N-version 组织基准，
而是协议局部闸门。</p>
<p><strong>面板怎么读（教师逐步）：</strong></p>
<ul>
<li><strong>左栏（0D APD）：</strong>灰带为预设可接受带宽；点应落在带内（<strong>256.6 ms</strong>）。</li>
<li><strong>中栏（均匀 2D CV）：</strong>灰带 0.55–0.85 mm/ms；虚线目标 <strong>0.70 mm/ms</strong>
（数值上对应论文健康纤维向量级 ≈0.7 m/s）。标定实测 <strong>0.703125 mm/ms</strong> @
D=0.0465 mm²/ms。</li>
<li><strong>右栏（三重终点）：</strong>同一 12 格上并列
<strong>VA_paper=1</strong>、<strong>VA_recurrence=3</strong>、<strong>VA_strict=1</strong>
（分母均为 12；表为 VA/Non-VA = 1/11、3/9、1/11）。
若只看 persist≥1000，会漏掉两格“再入但未满 1000 ms”的 recurrence 阳性；
若把周期 OR 进 paper 终点，则会把不同准则混成一个数。</li>
</ul>
<p><strong>常见误读：</strong>把“灰带内”理解成临床精度或猪心拟合优度。这里是方法学量级锚定，
服务协议复现，不是影像–模型个性化误差条。</p>
<p><strong>结论：</strong>离子时程、健康纤维向量级 CV、以及可区分的三重终点计数三者同屏成立；
随后各图是对这三闸门的展开说明。</p>
""",
        "fig_dx_dt_convergence": """
<p><strong>故事从哪里来：</strong>CV 是波长估计 λ<sub>wave</sub>≈CV×APD 的一半输入。
若 CV 随网格/时间步剧烈漂移，后续“环路径能否放下一个波长”的论证就失去数值根基。
因此在宣称环验证几何之前，必须先展示均匀组织 CV 对 Δx、Δt 的敏感性——这是验证文化（Niederer 2011；openCARP 分辨率例程）的本地轻量版。</p>
<p><strong>为何画这张图：</strong>把 <code>dx_convergence.csv</code> 与 <code>dt_convergence.csv</code> 变成可审阅面板，
明确告诉读者：相图默认用 Δx=0.75 mm，而标定常用 Δx=0.5 mm；两者 CV 都落在 0.55–0.85 带内，
但数值并不逐位相同，不能混用。</p>
<p><strong>面板怎么读（教师逐步）：</strong></p>
<ul>
<li><strong>左栏（空间）：</strong>Δx=0.75/0.5/0.25 mm → CV≈<strong>0.662 / 0.709 / 0.726</strong> mm/ms。
加密网格 CV 略升，符合显式 FD 常见趋势；三条均在灰带内。</li>
<li><strong>右栏（时间）：</strong>固定 Δx=0.5 mm，Δt=0.1/0.05/0.025 ms → CV≈<strong>0.709 / 0.709 / 0.696</strong> mm/ms。
时间细化未推出带外。</li>
<li>灰带=方法学接受带；虚线=0.70 mm/ms 标称目标。</li>
<li><strong>本扫不做 VA 重分类</strong>：CSV 注释写明 VA 标签仍以默认环相图（dx=0.75）为准。</li>
</ul>
<p><strong>常见误读：</strong>“CV 变了 = 相图假”。相图在固定协议网格上自洽；收敛图回答的是数值敏感性，不是生物学剂量反应。</p>
<p><strong>结论：</strong>均匀 CV 在所测 Δx/Δt 范围内保持量级正确，支持用 CV×APD 做波长–几何审计。</p>
""",
        "fig_phenotype_calibration": """
<p><strong>故事从哪里来：</strong>Villar-Valero 报告 CONTROL/DOX1/DOX2 的健康 APD 与纤维方向 CV 作为成像校准锚点
（例如 CONTROL APD 309 ms、CV 0.71 mm/ms）。本脚手架若要对齐“协议要素”，
需要证明：在修正 MS 参数空间内，可以把 τ_close 与 D 拟合到这些<strong>文献目标</strong>附近——
同时诚实声明：拟合出的参数是<strong>模型参数</strong>，不是论文常数抄录。</p>
<p><strong>为何画这张图：</strong>把“目标 vs 实测”并排，避免读者把预设 tau_close=150（环相图常用）
误当成 CONTROL 文献 APD。环相图与表型标定是两条相关但不同的实验轨。</p>
<p><strong>面板怎么读（教师逐步）：</strong></p>
<ul>
<li>左：APD——灰柱=文献目标，蓝柱=本机 0D 实测。CONTROL 309.0、DOX1 269.0、DOX2 210.1 ms。</li>
<li>右：CV——灰柱=文献目标，橙柱=本机均匀 2D 实测。CONTROL 0.709、DOX1 0.417、DOX2 0.441 mm/ms。</li>
<li>接受规则：±10% 且 CFL 稳定；JSON 中 <code>apd_matched_0d</code> / <code>cv_matched</code> 均为 true。</li>
<li><strong>禁止</strong>把这些柱高写成“我们复现了三维猪 LV 诱发性比例”——那是另一篇论文的结果表，本仓库从未运行其 LBM。</li>
</ul>
<p><strong>结论：</strong>表型锚点可在本开放 FD 脚手架上标定到容差内；文献数字只作目标，本机数字来自 <code>phenotype_calibration.json</code>。</p>
""",
        "fig_phase_diagram": """
<p><strong>故事从哪里来：</strong>Villar-Valero 在三维个性化左室上对 λ 与传导做参数扫描（约 96 组）。
本图是同一科学问题在<strong>开放二维脚手架</strong>上的最小可解释对应物：不是复现猪 LV 定量诱发比例，
而是检验“终点 + 几何 + 离子/扩散参数”能否给出机制可讲的混合相图，从而让第三方审计协议。</p>
<p><strong>为何默认是钉扎环而不是论文式小圆盘：</strong>
健康 λ<sub>wave</sub>≈0.70×250≈<strong>175 mm</strong>；48²×0.5 mm 圆盘直径约 <strong>24 mm</strong>，
几何上几乎必然全 Non-VA（作为阴性对照有用，但不适合当主相图）。钉扎环平均路径约 <strong>107 mm</strong>
（CSV 中 path_mm≈106.8），夹在健康波长与强减速波长之间，才可能出现混合标签。
这是波长–几何一致性问题，不是“调参出阳性”。</p>
<p><strong>面板怎么读（教师逐步）：</strong></p>
<ul>
<li>横轴：纤维化区扩散降幅 D<sub>fib</sub> reduction（传导变慢；0.3/0.7/0.9 对应降 30/70/90%）。</li>
<li>纵轴：兴奋性参数 λ<sub>fib</sub>（抬高内向电流阈值；健康 0.01，0.3 近功能阻滞）。</li>
<li>暖色=VA，冷色=Non-VA；热图默认标签=<strong>VA_recurrence</strong>：完整 4×3 为 <strong>3 / 9</strong>。</li>
<li>三重终点对照（同 12 格）：VA_paper=<strong>1</strong>，VA_recurrence=<strong>3</strong>，VA_strict=<strong>1</strong>。</li>
<li>VA 格点（务必对照表1）：λ=0.01×D↓70%（persist 666.6 ms，extra=1，relapped=5）→ recurrence 阳、paper 阴；
λ=0.01×D↓90%（persist 1000 ms，extra=2，relapped=9）→ 三者皆阳；
λ=0.1×D↓30%（persist 632.5 ms，extra=1，relapped=4）→ 仅 recurrence 阳。</li>
<li>λ≥0.2 全 Non-VA——可作机制讨论素材，<strong>禁止</strong>外推为猪 LV 或临床 DOX 的定量规律。</li>
</ul>
<p><strong>与表1 对照：</strong>读图必须同时看 <code>n_extra_cycles</code> /
<code>n_probes_relapped</code> 与三列终点。仅 persist≥1000 ms 会把平台滞留判成 VA。
本环相图只证明二维协议可审计，不是 3D maze 走廊的定量复现。</p>
<p><strong>结论：</strong>在要求再兴奋周期的 VA 准则下，完整相图是机制可解释的混合结果（recurrence 3/9），
而终点审计显示 paper/strict 更严（1/11）；创新点在终点与几何硬化，不在“发现新致心律失常药物机制”。</p>
""",
        "fig_diffusion_compare": """
<p><strong>故事从哪里来：</strong>单域方程的扩散项在数学上应是守恒形式 ∇·(D∇u)。
许多原型代码在均匀 D 时写 D∇²u 没问题（此时两者等价），但一旦 D 空间变化（纤维化降导），
捷径算子会引入非守恒误差，可能改变局部电紧张电流与激活持续。纤维化相图正好是异质 D 场景，
因此必须把算子选择写成方法学声明，而不是实现细节。</p>
<p><strong>为何画这张图：</strong>把“数值诚实性”做成可看证据：异质 D 下两算子的 persist 是否一致；
标签会不会翻转。这不是炫技，而是告诉审稿人/合作者：我们默认用守恒格式，并量化捷径风险。
它与 CV 标定、VA 终点并列，属于 reproducibility 证据链的一环。</p>
<p><strong>面板怎么读（教师逐步）：</strong></p>
<ul>
<li>分组柱：不同耦合间期 CI（coupling interval）——早搏越早，传导越脆弱，算子误差更容易被放大。</li>
<li>比较量：激活持续时长 persist（ms），不是 L2 空间误差范数；选择 persist 是因为下游 VA 规则会读它。</li>
<li>观察：本协议 persist 可差约 <strong>65 ms</strong>；标签未翻转——说明终点有时对算子误差不敏感，
<strong>但不能</strong>据此声称捷径永远安全。</li>
<li>与 CFL 的关系：显式格式还受 Δt≤Δx²/(4D_max) 与离子上限 0.1 ms 约束；算子错误与稳定条件是两件不同的事。</li>
</ul>
<p><strong>常见误读：</strong>“标签没翻 = 两算子等价”。不等价；只是本网格/本终点下未跨过分类阈值。
换观察窗、换几何或换 require_cycle 规则后，差异可能变成标签翻转。</p>
<p><strong>结论：</strong>脚手架默认守恒扩散；对照实验保留为异质介质下的数值诚实性证据，并写入 ASSUMPTIONS。</p>
""",
        "fig_mono2d_u": """
<p><strong>故事从哪里来：</strong>读者在看完 0D 与相图后，仍可能怀疑“二维求解器是否真的在空间上传波”，
或者误以为相图只是标量脚本。本快照给出最短的视觉确认：均匀组织、无纤维化、短时程终态的膜电位场。</p>
<p><strong>为何画这张图：</strong>它是管线烟雾测试（smoke test）的空间证据，
证明 <code>ms_2d</code> 求解器在跑，而不是只输出 CSV 标量。对 methods 论文而言，
“能看见场”降低了审稿人对黑箱指标的不信任，但<strong>不能</strong>单独承担科学结论。</p>
<p><strong>面板怎么读（教师逐步）：</strong></p>
<ul>
<li>颜色：归一化膜电位 u∈[0,1]（与 0D 图同一无量纲约定）。</li>
<li>几何：均匀二维单域；本图<strong>无</strong>纤维化掩膜、无钉扎孔——因此看不到环上折返结构是正常的。</li>
<li>时相：短时程终态快照——用于可视检查，不是 S1–S2 诱发协议的观察窗截图。</li>
<li>与相图的分工：相图回答“参数格子上 VA 是否发生”；本图只回答“空间求解器是否在传波”。</li>
</ul>
<p><strong>严禁过度解读：</strong>本图<strong>不是</strong>折返阳性证据，也<strong>不能</strong>替代 S1–S2 + 周期准则 + 相图。
若只展示漂亮的 u 场却不做终点硬化，会重复早期“平台期假阳性”陷阱，也会与 Chabiniok–Zaha
“打开方法”的精神相反——打开方法要求终点可审计，而不是图像好看。</p>
<p><strong>结论：</strong>2D 求解器可运行；折返结论必须以协议分类与相图（表1 + 图5）为准。</p>
""",
    }


def prose_sections() -> dict[str, str]:
    """Major Chinese sections as HTML."""
    today = date.today().isoformat()
    return {
        "cover_meta": f"生成日期：{today} · 仓库：Fibrosis-Reentry-MS2D (DOX-LBM-GPU) · 性质：2D 协议/基准研究报告（非临床决策工具）",
        "abstract": """
<p>阿霉素（DOX，doxorubicin）相关弥漫纤维化可构成室性心律失常（VA）基质。
Villar-Valero 等（STACOM 2024 / <em>J Physiol</em> 2026，doi:10.1113/jp288819）用 MRI 个性化三维左室、
修正 Mitchell–Schaeffer（含 λ）与 GPU LBM 单域求解器扫描诱发性。细胞模型/参数/样例解剖公开
（<code>javilva/doxorubicin_fibrosis_model</code>），生产求解器仍专有。Chabiniok &amp; Zaha（doi:10.1113/jp290313）呼吁打开方法。</p>
<p>本仓库提供开放的 <strong>CPU 二维有限差分单域协议/基准</strong>：对齐修正 MS、守恒扩散
∇·(D∇u)、合成三相纤维化、S1–S2（extras 240/200/190 ms），标定健康 CV≈<strong>0.70 mm/ms</strong>
（本机均匀片 <strong>0.703 mm/ms</strong>），
并报告三重 VA 终点（<code>VA_paper</code> / <code>VA_recurrence</code> / <code>VA_strict</code>）。钉扎环为波长设计的<strong>验证几何</strong>（路径≈107 mm）。
完整 4×3 环相图：VA_paper <strong>1/11</strong>，VA_recurrence <strong>3/9</strong>，VA_strict <strong>1/11</strong>。
0D APD<sub>90</sub> 黄金回归 <strong>256.6 ms</strong>。
<strong>不是</strong>三维 DOX 孪生复现，也<strong>不</strong>声称 ICD 临床效用。</p>
""",
        "background": """
<p><strong>研究动机。</strong>化疗心毒性传统关注射血分数下降；组织纤维化与电重构亦可形成折返基质。
个性化心脏数字孪生（digital twin）把影像解剖与电生理方程结合，用于虚拟诱发试验，从而在参数空间上追问：
兴奋性、传导与纤维化几何如何共同决定 VA 可诱发性。</p>
<p><strong>Villar-Valero 做了什么。</strong>猪 DOX 模型 + MRI/LGE 三维左室；修正 MS（Djabella λ）；
LBM–GPU 单域；对 λ 与扩散做参数扫描（报道约 96 组），报告纤维化底物可诱发恶性 VA。
细胞模型/参数/样例解剖见公开仓库 <code>javilva/doxorubicin_fibrosis_model</code>；生产求解器仍为专有。</p>
<p><strong>Chabiniok–Zaha 强调什么。</strong>孪生潜力大，但建模方法与临床落地之间仍有鸿沟；下一步应开放方法、
降低使用门槛，并推进更大规模验证。评述亦指出猪模型 9 周纤维化可能重于典型患者 DOX 毒性——这限制跨物种外推。
ICD 患者选择的临床效用“尚未确立”。</p>
<p><strong>本脚手架的定位。</strong>开放<strong>二维协议/基准</strong>（Fibrosis-Reentry-MS2D）：离子律、刺激协议、
三重 VA 终点（<code>VA_paper</code>/<code>VA_recurrence</code>/<code>VA_strict</code>）、波长–几何一致性与扩散算子诚实性。它回答“协议能否在开放 2D 上被压力测试”，
而不是“能否复现猪 LV 的 LBM 定量结果”。</p>
<p><strong>文献写作架构：</strong>
(1) Villar-Valero 2025——参数扫描与 VA 终点主叙事；
(2) Chabiniok &amp; Zaha 评述——转化框架；
(3) Campos 等 <em>Front Physiol</em> 2024（doi:10.3389/fphys.2024.1370795）——纤维化表示→VA 形态；
(4) <em>Sci. Rep.</em> 2024（doi:10.1038/s41598-024-62002-5）——诱导窗/观察窗拆分；
(5) Niederer 2011（doi:10.1098/rsta.2011.0139）——验证文化指针；
(6) 公开细胞模型材料——协议对齐对照。
目标期刊宜偏 methods / 计算生理。</p>
""",
        "aims": """
<ol>
<li>实现并验证含 λ 的修正 MS 与守恒二维单域（∇·(D∇u)）。</li>
<li>将均匀组织 CV 标定到论文健康纤维向量级（本机 ≈0.703 mm/ms @ D=0.0465）。</li>
<li>对齐 S1–S2 与 extras；并列报告三重 VA 终点（paper / recurrence / strict）。</li>
<li>用波长感知<strong>验证几何</strong>（环路径≈107 mm vs 健康波长≈175–180 mm）获得可解释的混合相图。</li>
<li>用 SciencePlots 输出可嵌入报告的出版风格图，并生成自包含 HTML/MD/PDF；另附 AUDIT_EVIDENCE 证明数字为本机计算。</li>
</ol>
""",
        "data_methods": """
<p><strong>数据。</strong>本阶段以合成几何与合成三相纤维化为主；未下载 Zenodo 多 GB 猪 MI 数据
（且 MI≠DOX）。外部求解器 MonoAlg3D 仅作指针。公开仓库：
<a href="https://github.com/Coucou2016/DOX-LBM-GPU">github.com/Coucou2016/DOX-LBM-GPU</a>（展示名 Fibrosis-Reentry-MS2D）。</p>
<p><strong>方程。</strong>单域反应–扩散：
∂t u = ∇·(D∇u) + [h u (u−λ)(u_max−u)]/τ_in − u/τ_out + J_stim；
门控 h 在 u&lt;u_gate 时按 τ_open 开放，否则按 τ_close 关闭。健康 λ=0.01；
纤维化扫描 λ∈{0.01,0.1,0.2,0.3}；环相图 τ_close=150 ms。单位：时间 ms，长度 mm，u/h/λ 无量纲。</p>
<p><strong>数值。</strong>显式欧拉 + 面平均 D 的五点守恒扩散（含 Neumann 角点）；CFL：Δt≤Δx²/(4D_max)，另离子上限 0.1 ms。
诱导脚本默认 <code>stimulus_mode=current</code>（亦可 voltage_clamp）。</p>
<p><strong>协议。</strong>S1 BCL=400 ms，n=3；extras 默认 240/200/190 ms；诱导窗与观察窗（默认 1000 ms）分离。
<code>VA_paper</code>：persist≥1000 ms <strong>仅此</strong>（从不 OR 周期）；<code>VA_recurrence</code>（默认 label）：需 n_extra_cycles≥1 或 n_probes_relapped≥3；<code>VA_strict</code>：persist≥1000 <strong>且</strong> 再入循环。</p>
<p><strong>几何。</strong>圆盘阴性对照（直径≈24 mm ≪ 175 mm）vs 钉扎环<strong>验证几何</strong>（路径≈106.8 mm）。
完整网格：λ×D 共 12 格，nx=ny=64，dx=0.75 mm。</p>
""",
        "process": """
<ol>
<li>P0：修复门控 dt、引入 λ-MS、CV 标定、守恒扩散、S1–S2。</li>
<li>发现小圆盘相图全 Non-VA → 波长审计（≈175–180 mm vs 24 mm）。</li>
<li>改默认钉扎环；发现平台期假阳性 → 周期必需准则 + 单 CI 负对照测试。</li>
<li>Round-2/3：三重 VA 终点（paper persist-only / recurrence / strict）；完整 4×3 环相图
VA_paper 1、VA_recurrence 3、VA_strict 1；pytest 57 passed；表型标定 JSON；dx/dt 收敛表。</li>
<li>SciencePlots 重绘（含收敛与表型面板）；手稿定位为开放 2D 协议/基准；生成自包含 HTML/MD/PDF 与 AUDIT_EVIDENCE。</li>
</ol>
""",
        "analysis": """
<p><strong>与 Villar-Valero 的关系。</strong>共享：修正 MS+λ、单域思想、纤维化参数扫描、S1–S2 诱发逻辑。
不共享：3D 猪 LV、LBM–GPU、真实 LGE 纤维化分布。因此创新点应表述为
<strong>开放可测的协议基准与终点/几何硬化</strong>，而非“首个 DOX 孪生”。</p>
<p><strong>与 Chabiniok–Zaha 的关系。</strong>评述呼吁打开方法；本仓库以 CPU、pytest、文档化假设、公开 GitHub
响应“可复现入口”，但尚未提供临床 GUI。猪 9 周纤维化偏重的提醒，
进一步禁止把二维环相图写成患者风险工具。</p>
<p><strong>为何二维不应复现三维诱发性图。</strong>健康波长≈175 mm；D↓90% 波长≈55 mm；λ=0.2/0.3 近阻滞。
环路径≈107 mm 上的混合标签由波长–几何决定，而非 3D maze 走廊——差异是维度与几何边界，不是标定失败。</p>
<p><strong>平台期 vs 真折返。</strong>完整 CSV 中，VA 格点可有 persist&lt;1000 但 extra≥1；
反之，平台滞留可 persist≥1000 而 extra=0 → <code>VA_recurrence</code>=Non-VA / <code>VA_paper</code>=VA；
再入而 persist&lt;1000 → <code>VA_recurrence</code>=VA / <code>VA_paper</code>=Non-VA。终点定义必须写进方法学。</p>
""",
        "conclusions": """
<ol>
<li>开放 2D 修正 MS 单域协议/基准可在无生产 LBM 求解器时对齐关键协议要素。</li>
<li>CV≈0.70 mm/ms 与 0D APD=256.6 ms 黄金回归提供量级锚定。</li>
<li>三重 VA 终点使文献 persist-only、再入循环与严格合取规则可并列审计。</li>
<li>波长感知环验证几何恢复混合相图（VA_recurrence 3 / Non-VA 9；VA_paper 1；VA_strict 1）。</li>
<li>工作边界清晰：非 3D LBM、非猪 DOX 数据复现、非临床 ICD 工具。</li>
</ol>
""",
        "limitations": """
<ul>
<li>二维 FD ≠ 三维 LBM；无真实纤维场 / Purkinje / 双向域。</li>
<li>合成纤维化 ≠ DOX 猪心肌 ≠ 缺血性 MI（公开 MI 数据亦不能直接当作 DOX）。</li>
<li>Niederer/openCARP/MonoAlg3D 交叉验证仍为后续工作；圆盘几何完整定量 CSV 可按需再生。</li>
<li>DOX 表型 1D CV 尚未在本 FD 脚手架上完全匹配文献目标（已在 phenotypes 中注明）。</li>
<li>各向异性传导仍为原型实现。</li>
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
    <p><strong>表1. 钉扎环相图原始记录（优先完整 4×3）。</strong>
    标签列 label 为协议输出；va=1 表示周期必需准则下的 VA。</p>
    {table_html}
    <p class="caption"><strong>表注：</strong>path_mm≈107 为环平均路径；tau_close=150 ms 保持健康复极时程设定。
    观察窗 observe_ms=1000。勿将 persist 单独等同于 VA。</p>
    <div class="explain">
      <h4>来龙去脉与读表说明</h4>
      <p>完整网格为 λ∈{{0.01,0.1,0.2,0.3}} × D↓∈{{30%,70%,90%}}（12 行）。请同时看
      <code>n_extra_cycles</code> 与 <code>n_probes_relapped</code>：VA 行应显示再兴奋证据
      （可出现 persist&lt;1000 ms）；Non-VA 行即使 persist 较长也可能是平台期。
      这是本脚手架相对“仅 persist≥1000”论文式简化终点的关键硬化。</p>
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
    <p>展望：各向异性精化、openCARP/MonoAlg3D 交叉、圆盘全表 CSV、在获得授权数据后的影像驱动几何。完整 4×3 环扫描已完成并嵌入表1。</p>
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

    n_va = summary.get("n_va", "N/A")
    n_non = summary.get("n_non_va", "N/A")
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
        return "_phase_diagram.csv 缺失；请运行 scripts/run_phase_diagram.py --full_\n"
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
    report_pdf = args.out_dir / "report.pdf"

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

    def _rel(p: Path) -> str:
        try:
            return p.resolve().relative_to(ROOT).as_posix()
        except ValueError:
            return p.as_posix()

    meta = {
        "html": _rel(html_path),
        "report_html": _rel(report_html),
        "md": _rel(md_path),
        "pdf": _rel(pdf_path) if pdf_path.is_file() else None,
        "pdf_method": pdf_method,
        "html_bytes": html_path.stat().st_size,
        "md_bytes": md_path.stat().st_size,
        "pdf_bytes": pdf_path.stat().st_size if pdf_path.is_file() else 0,
        "n_phase_rows": len(rows),
        "missing_figures": missing,
        "has_data_uri": "data:image" in html_doc,
    }
    if pdf_path.is_file():
        shutil.copy2(pdf_path, report_pdf)
        (args.out_dir / "PDF_METHOD.txt").write_text(pdf_method + "\n", encoding="utf-8")
        meta["report_pdf"] = _rel(report_pdf)
    (args.out_dir / "research_report_build.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(meta, indent=2, ensure_ascii=False))
    return 0 if meta["has_data_uri"] and meta["md_bytes"] > 1000 else 1


if __name__ == "__main__":
    raise SystemExit(main())
