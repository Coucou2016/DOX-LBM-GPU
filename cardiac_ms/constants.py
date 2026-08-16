"""
Paper-aligned defaults for the modified Mitchell–Schaeffer monodomain pipeline.

Units (entire cardiac_ms stack):
    t          ms
    dx         mm
    D          mm^2/ms
    u, h, λ    dimensionless
    CV         mm/ms  (= m/s numerically)

References
    Villar-Valero et al., J Physiol 2025 / STACOM 2024
    Djabella, Landau & Sorine, IEEE CDC 2007 (λ in the inward current)
    Mitchell & Schaeffer, Bull. Math. Biol. 2003 (time constants)
"""

from __future__ import annotations

# --- Modified MS (Djabella / Villar-Valero) ---
LAMBDA_HEALTHY = 0.01
LAMBDA_FIBROTIC_GRID: tuple[float, ...] = (0.01, 0.1, 0.2, 0.3)
U_MAX = 1.0
U_GATE = 0.13
TAU_IN = 0.3
TAU_OUT = 6.0
TAU_OPEN = 120.0
TAU_CLOSE = 150.0

# Homogeneous 2D CV target: paper healthy fiber-direction ~0.7 m/s = 0.7 mm/ms.
# D_HEALTHY is the finite-difference value that hits this band on the 48^2, dx=0.5 mm
# protocol in validation.calibrate_healthy_diffusion (not the paper LBM d=3.5).
CV_TARGET_MM_PER_MS = 0.7
CV_CALIBRATION_BAND: tuple[float, float] = (0.55, 0.85)
D_HEALTHY_MM2_PER_MS = 0.0465  # 48², dx=0.5 mm, λ=0.01 → CV ≈ 0.70 mm/ms

# Fibrosis D as a fraction of healthy D remaining after a reduction.
# "30% reduction" => remaining 0.70; "90% reduction" => remaining 0.10.
D_REDUCTION_GRID: tuple[float, ...] = (0.30, 0.70, 0.90)
BORDER_WIDTH_2D_DEFAULT = 2
BORDER_WIDTH_GRID: tuple[int, ...] = (0, 2)

# S1–S2 / reentry (paper)
BCL_S1_MS = 400.0
N_S1_DEFAULT = 3
REENTRY_SUSTAIN_MS = 1000.0
S2_CI_SCAN_MS: tuple[int, ...] = tuple(range(180, 321, 20))

# Activation / stimulus
ACTIVATION_THRESHOLD = 0.5
STIM_U_PROTOCOL = 0.8
STIM_DURATION_MS = 2.0
# Explicit Euler: diffusion CFL may allow dt ≫ τ_in; cap for upstroke accuracy.
IONIC_DT_MAX_MS = 0.1
