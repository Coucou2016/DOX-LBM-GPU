# ChatGPT 任务书（待投递）

**标题**：DOX-LBM_GPU：对抗性审查 + 最小修复补丁（折返判定/测试/文档一致性）

**附件**：`E:\Projects\20260522-DOX-LBM_GPU\outputs\dox_lbm_gpu_review_pack.zip`  
**SHA-256**：`A33AC7C66DD4D0B8D103FED6C4087F479EAC8D2EF4515649ECD5923CA4B78986`  
**Git baseline**：无 git 仓库  
**注**：ZIP **不含** `MonoAlg3D_C-master/`（体积大且本任务无关；仓库内仅作第三方指针）。本包已含本地新增的单 CI 平台负对照测试与 ASSUMPTIONS 共存说明。

---

## 背景与目标

本仓库是 Villar-Valero（STACOM 2024 / J Physiol 2025）路径下的 **CPU 2D 单域 + 修正 Mitchell–Schaeffer（含 λ）** 研究脚手架，**不是**论文 LBM–GPU 源码复现，也 **不是** 临床/动物 DOX 预测系统。

请对 ZIP 内源码做 **对抗性科学+工程审查**，交付 **unified diff 最小补丁** + 简短报告。Cursor 将独立跑测试验收。

## 架构与不可谈判边界

- 单位：t=ms，dx=mm，D=mm²/ms，CV=mm/ms。
- 默认折返分类 **`require_cycle=True`**：仅 `persist≥1000` **不算 VA**；单圈（各探针一次升支）**不算 VA**。VA 需 `n_extra_cycles≥1` **或** `n_probes_relapped≥3`。
- 健康 λ=0.01；标定 D=`0.0465` mm²/ms → 均匀 CV≈0.70 mm/ms。
- 默认相图几何：**钉扎环**；小圆盘仅作阴性对照。
- **禁止声称**：已实现 LBM–GPU、临床预测能力、DOX 动物数据复现、可替代论文 3D 结果。
- **禁止操作**：要求下载多 GB Zenodo、强行 Windows CUDA 全编 MonoAlg3D、修改折返语义为「仅 persist」而不说明。

## 范围

1. 审查剩余科学/工程缺陷（平台期假阳性、文档与代码不一致、坏导入、脆弱测试、扩散/CFL/门控错误等）。
2. 若有缺陷：给出 **最小完整** unified diff（相对 ZIP 根目录路径）。
3. 给出应跑的测试命令（pytest / smoke / phase_diagram）。
4. 可选（低优先级）：Niederer/openCARP **指针级**文档；扩散算子说明。勿拉大数据。

已知已修复（请核实，勿重复「发现」为新阻塞）：λ-MS、`div(D∇u)`、h×dt、require_cycle、环相图 1VA/3Non-VA、论文 extras 240/200/190。

## 交付物

1. 审查报告（中英文均可）：按严重度列问题；区分已确认缺陷 vs 推测。
2. 补丁：`*.patch` 或完整 unified diff；无问题时明确写「无代码变更」。
3. 测试清单与期望结果。
4. 明确写出 **未验证项**。

## 验收标准（Cursor 侧）

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/ -q` 全绿。
- 默认 `python scripts/run_phase_diagram.py` 仍同时含 VA 与 Non-VA（环、fast）。
- `require_cycle` 语义不被削弱。
- 无 LBM/临床/DOX 数据夸大声明。

## 请先确认

收到 ZIP 后请先列出将重点阅读的文件，再给补丁；若上传失败，告知需要粘贴的关键文件路径。
