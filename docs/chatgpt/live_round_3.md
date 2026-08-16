# live_round_3.md — Results (regenerated 4×3)

**Date:** 2026-08-16  
**ChatGPT URL:** **无**  
**Paste pack:** `docs/chatgpt/paste_pack_round_3.md`

## Round question

Paste full 4×3 phase diagram numbers; request Results storyboard.

## Regenerated numbers (this session — real run)

```
python scripts/run_phase_diagram.py --full
→ mode=full, VA 3 / Non-VA 9, elapsed_s≈158.4
```

| λ | D↓30% | D↓70% | D↓90% |
|---|:-----:|:-----:|:-----:|
| 0.01 | Non-VA | **VA** | **VA** |
| 0.1 | **VA** | Non-VA | Non-VA |
| 0.2 | Non-VA | Non-VA | Non-VA |
| 0.3 | Non-VA | Non-VA | Non-VA |

VA detail: (0.01,0.7) persist=666.7 extra=1 relap=1; (0.01,0.9) 1000.0/2/3; (0.1,0.3) 632.9/1/1.

## Advisor synthesis (fallback)

Storyboard: 0D APD → CV calibration → diffusion operator audit → annulus phase diagram → disc negative control. **Do not** claim match to Villar-Valero 96-run 3D inducibility fractions. Emphasize cycle-required explains persist&lt;1000 VA cells.

## Cursor actions

- Synced `papers/data/phase_diagram.csv` + summary.  
- `scripts/run_phase_diagram.py` now also writes curated mirror under `papers/data/`.  
- Regenerated SciencePlots + research/manuscript HTML.
