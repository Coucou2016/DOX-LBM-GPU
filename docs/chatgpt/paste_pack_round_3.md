# Paste pack — Round 3 (Results — full 4×3 numbers)

**Same chat.** Web search ON. Paste below.

---

Results narrative review for https://github.com/Coucou2016/DOX-LBM-GPU.

**Regenerated full annulus grid (2026-08-16, mode=full):** τ_close=150 ms; nx=ny=64; dx=0.75 mm; path≈106.8 mm; extras 240/200/190 ms; observe 1000 ms. **VA 3 / Non-VA 9** (~158 s wall time).

| λ | D↓30% | D↓70% | D↓90% |
|---|-------|-------|-------|
| 0.01 | Non-VA (persist=394.7, extra=0, relap=0) | **VA** (666.7, extra=1, relap=1) | **VA** (1000.0, extra=2, relap=3) |
| 0.1 | **VA** (632.9, extra=1, relap=1) | Non-VA | Non-VA |
| 0.2 | Non-VA | Non-VA | Non-VA |
| 0.3 | Non-VA | Non-VA | Non-VA |

**Supporting gates (same session):** pytest 42 passed; validation APD90=256.6 ms; CV=0.703125 mm/ms @ D=0.0465.

**Ask:** Results storyboard (verification ladder → phase diagram → negative control); which sentences overclaim 3D inducibility; how to discuss persist&lt;1000 ms VA cells under cycle-required rule without sounding like a loophole.
