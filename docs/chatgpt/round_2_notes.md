# Round 2 — Methods accuracy (λ-MS, classify_reentry, wavelength)

**Date:** 2026-08-16  
**GitHub:** https://github.com/Coucou2016/DOX-LBM-GPU  
**ChatGPT URL:** **无**（浏览器 MCP 不可用；本轮为 WebSearch + 本地代码核对后的顾问备忘）

## Round question

Paste λ-MS equation, `classify_reentry`, wavelength assumptions; ask factual/equation review.

Critical excerpts (local):

```text
J_in = h * u * (u - λ) * (u_max - u) / τ_in
J_out = -u / τ_out
∂h/∂t = (1-h)/τ_open if u < u_gate else -h/τ_close
```

`require_cycle=True` → VA iff `n_extra_cycles≥1` OR `n_probes_relapped≥3` (persist alone never sufficient; persist **not** required either).

Wavelength: λ_wave ≈ CV × APD ≈ 0.70 × 250 ≈ 175 mm; annulus path ≈107 mm; disc ≈24 mm.

## Advisor memo (fallback) — verified against code + literature

### Accepted

1. **λ in J_in** matches the excitability parameter used in Villar-Valero / Djabella-lineage generalized MS (a=λ=0 recovers classic MS). Local `ms_modified.py` and λ=0 package match test are correct.
2. **Healthy λ=0.01** (not 0) is paper-aligned; document explicitly so readers do not assume classic MS.
3. **Cycle-required endpoint** is scientifically defensible vs persist≥1000 ms alone; peers: CinC2025-149 (“>3 cycles + closed-loop”).
4. **Wavelength bookkeeping** is the right framing for why small discs fail and annulus is a *protocol* geometry, not anatomy.

### Rejected / corrections Cursor must apply

| Advisor suggestion / risk | Decision |
|---------------------------|----------|
| Equate our model to Corrado et al. *full* mMS (λ:=v_gate + gated J_out) | **Reject.** Our J_out is ungated; λ is continuous excitability, not forced to v_gate. Cite Mitchell–Schaeffer 2003 + Djabella/Villar-Valero λ form; do **not** claim Corrado-2016 identity. |
| Wavelength using APD=250 vs measured APD₉₀=256.6 | **Clarify.** Use nominal paper-style 250 ms for geometry design; report measured APD₉₀ separately (256.6 ms). Do not invent a single fused number. |
| Imply `require_cycle` still needs persist≥1000 | **Reject wording.** Code returns VA on cycle metrics alone. Manuscript must say that accurately. |

### Equation hygiene for manuscript

- Write monodomain as \(\partial_t u = \nabla\cdot(D\nabla u) + J_{\mathrm{ion}}(u,h) + J_{\mathrm{stim}}\).  
- State units: ms, mm, \(u\) dimensionless.  
- State CFL: \(\Delta t \le \Delta x^2/(4D_{\max})\) and ionic cap 0.1 ms.

## Implementation after Round 2

- Methods text: clarify λ lineage vs Corrado mMS.  
- Methods: accurate `require_cycle` logic.  
- Wavelength: nominal 250 ms design vs measured APD₉₀.
