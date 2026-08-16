# Round 1 — Scope & journal fit

**Date:** 2026-08-16  
**GitHub for advisor:** https://github.com/Coucou2016/DOX-LBM-GPU  
**HEAD at round start:** `1a9b12f`  
**ChatGPT conversation URL:** **无**（见下：浏览器 MCP 不可用）

## Round question (sent / would-send)

Paste outline + GitHub URL; ask for 3–5 exemplar papers, section map, innovation boundaries, venue suggestions.

Task pack: `docs/chatgpt/2026-08-16_paper_framework_task.md`

## Browser / ChatGPT status

| Attempt | Result |
|---------|--------|
| MCP catalog | Only `cursor-app-control` — **no browser lock/snapshot/navigate tools** |
| `open_resource` → chatgpt.com | Failed: `unknown agent` |
| Prior session notes | Same blocker documented in §十九 旧稿 |

**Label:** ChatGPT live rounds **failed**. This round uses **WebSearch + Cursor structured advisor memo** (fallback), clearly not a ChatGPT chat transcript.

## Advisor memo (fallback synthesis — independently verified)

### Exemplars to imitate (accepted after local judgment)

| # | Paper | Section lesson | Accept? |
|---|-------|----------------|---------|
| 1 | Villar-Valero et al., *J Physiol* 2025 (doi:10.1113/jp288819) | Pipeline fig → calibration → parametric inducibility → mechanism | **Yes** (primary target) |
| 2 | Chabiniok & Zaha, *J Physiol* (doi:10.1113/jp290313) | Translational “open the method” framing | **Yes** |
| 3 | Campos et al., *Front Physiol* 2024 (doi:10.3389/fphys.2024.1370795) | Fibrosis representation → VA morphology ladder | **Yes** (outline already) |
| 4 | Sci. Reports 2024 fibrosis reentry systematic (doi:10.1038/s41598-024-62002-5) | Protocol = induction window + observation window; clear endpoint defs | **Yes** (new) |
| 5 | CinC 2025 ventricular twin (CinC2025-149): S1–S2; reentry = >3 cycles + closed-loop | Cycle-required VA language peers | **Yes** (new; strengthens our endpoint story) |
| — | Nat Cardiovasc Res AF twin ablation (doi:10.1038/s44161-024-00489-x) | Clinical twin depth | **Reject as structural template** (too clinical / AF / ablation; overclaims risk) |

### Section map (kept, with one addition)

Keep methods+mechanism map in `papers/outline.md`. **Add** explicit “Simulation protocol & endpoints” subsection under Methods (induction vs observation windows), mirroring Sci. Reports / CinC cycle language.

### Innovation boundaries (enforce)

**Claim:** open tested scaffold; cycle-required VA; wavelength-aware annulus; conservative diffusion audit.  
**Forbidden:** first DOX twin; 3D LBM reproduction; clinical ICD from 2D disc; MI≡DOX.

### Venue (accepted)

Methods-friendly: *Comput Biol Med*, *Front Physiol* methods, *J Physiol* methods/tech notes — **not** flagship *Nature* unless 3D cross-validation lands.

## What Cursor implemented after Round 1

- Reconfirmed exemplar table in outline (add Sci. Reports + CinC cycle peer).  
- Manuscript Methods: add protocol/endpoint window language.  
- No claim inflation.
