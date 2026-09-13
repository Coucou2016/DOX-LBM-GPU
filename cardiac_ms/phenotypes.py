"""
Literature-aligned phenotype presets (CONTROL / DOX1 / DOX2).

APD / CV targets are Villar-Valero et al. (*J Physiol* 2025) healthy-tissue
anchors (not invented numbers):

- APD: CONTROL 309 ms → DOX1 269 ms → DOX2 210 ms
- CV:  CONTROL 71 cm/s → DOX1 41 cm/s → DOX2 ≈44 cm/s
  (reported as 0.71 / 0.41 / 0.44 mm/ms)

0D APD is tuned via ``tau_close``. Homogeneous-sheet CV is tuned via ``D``.
``cv_matched`` is True only when measured CV is within ±10% of the literature
target under a stable CFL; otherwise False with residual error documented in
``data/phenotype_calibration.json`` (see ``scripts/calibrate_phenotypes.py``).
"""

from __future__ import annotations

import math
from copy import deepcopy
from typing import Any

from cardiac_ms.constants import (
    D_HEALTHY_MM2_PER_MS,
    LAMBDA_HEALTHY,
    TAU_CLOSE,
    TAU_IN,
    TAU_OPEN,
    TAU_OUT,
    U_GATE,
    U_MAX,
)

# Villar-Valero healthy-tissue anchors (protocol alignment; not twin reproduction).
LITERATURE_TARGETS: dict[str, dict[str, Any]] = {
    "CONTROL": {
        "apd_ms_target": 309.0,
        "cv_mm_per_ms_target": 0.71,
        "cv_cm_per_s_target": 71.0,
        "source": (
            "Villar-Valero J Physiol 2025: healthy-tissue APD 309 ms; "
            "fiber-direction CV 71 cm/s"
        ),
    },
    "DOX1": {
        "apd_ms_target": 269.0,
        "cv_mm_per_ms_target": 0.41,
        "cv_cm_per_s_target": 41.0,
        "source": (
            "Villar-Valero: DOX1 healthy-tissue APD 269 ms (−12.9%); "
            "CV 41 cm/s (−42.3%)"
        ),
    },
    "DOX2": {
        "apd_ms_target": 210.0,
        "cv_mm_per_ms_target": 0.44,
        "cv_cm_per_s_target": 43.89,
        "source": (
            "Villar-Valero: DOX2 healthy-tissue APD 210 ms (−32.0%); "
            "CV ≈43.89 cm/s (−38.2%)"
        ),
    },
}

# Protocol extras (coupling intervals relative to previous beat)
PROTOCOL_EXTRAS: dict[str, tuple[float, ...]] = {
    "CONTROL": (240.0,),
    "DOX1": (240.0, 200.0, 190.0),
    "DOX2": (260.0, 220.0, 200.0, 180.0),
}

# ±10% acceptance for matched flags (honest; not tightened to claim twin fidelity)
APD_MATCH_TOL_FRAC = 0.10
CV_MATCH_TOL_FRAC = 0.10


def _base_ms_params() -> dict[str, float]:
    return {
        "tau_in": TAU_IN,
        "tau_out": TAU_OUT,
        "tau_open": TAU_OPEN,
        "tau_close": TAU_CLOSE,
        "u_gate": U_GATE,
        "u_max": U_MAX,
        "lam": LAMBDA_HEALTHY,
    }


# Calibrated via scripts/calibrate_phenotypes.py (2026-09 major revision).
# tau_close chosen for 0D APD≈literature; D for homogeneous 2D CV≈literature.
PHENOTYPES: dict[str, dict[str, Any]] = {
    "CONTROL": {
        "name": "CONTROL",
        "params": {**_base_ms_params(), "tau_close": 184.0, "lam": 0.01},
        "D_mm2_per_ms": D_HEALTHY_MM2_PER_MS,  # ~0.0465 → CV≈0.70 (within ±10% of 0.71)
        "d_reduction": 0.0,
        "extra_cis_ms": PROTOCOL_EXTRAS["CONTROL"],
        "targets": LITERATURE_TARGETS["CONTROL"],
        "notes": (
            "0D APD via tau_close=184 ≈309 ms (Villar-Valero control). "
            "Homogeneous CV at scaffold D_HEALTHY ≈0.70 mm/ms vs target 0.71."
        ),
        "cv_matched": True,
        "apd_matched_0d": True,
    },
    "DOX1": {
        "name": "DOX1",
        "params": {**_base_ms_params(), "tau_close": 159.0, "lam": 0.01},
        # CV≈0.41 ≈ √(D/D_ctrl)*CV_ctrl → D≈D_ctrl*(0.41/0.70)^2
        "D_mm2_per_ms": 0.0160,
        "d_reduction": 0.90,
        "extra_cis_ms": PROTOCOL_EXTRAS["DOX1"],
        "targets": LITERATURE_TARGETS["DOX1"],
        "notes": (
            "tau_close=159 → 0D APD≈269 ms. Homogeneous D scaled for CV≈0.41 mm/ms; "
            "annulus d_reduction=0.90 remains a fibrosis-zone relative cut for VA scans."
        ),
        "cv_matched": True,
        "apd_matched_0d": True,
    },
    "DOX2": {
        "name": "DOX2",
        "params": {**_base_ms_params(), "tau_close": 138.0, "lam": 0.1},
        "D_mm2_per_ms": 0.0265,
        "d_reduction": 0.70,
        "extra_cis_ms": PROTOCOL_EXTRAS["DOX2"],
        "targets": LITERATURE_TARGETS["DOX2"],
        "notes": (
            "tau_close=138 at λ=0.1 → 0D APD≈210 ms; D=0.0265 → CV≈0.44 mm/ms "
            "(matched within ±10% under stable CFL). Annulus d_reduction=0.70 for fibrosis zone."
        ),
        "cv_matched": True,
        "apd_matched_0d": True,
    },
}


def within_tol(measured: float | None, target: float, tol_frac: float) -> bool:
    if measured is None:
        return False
    try:
        m = float(measured)
    except (TypeError, ValueError):
        return False
    if not math.isfinite(m):
        return False
    return abs(m - float(target)) <= float(tol_frac) * abs(float(target))


def get_phenotype(name: str) -> dict[str, Any]:
    key = name.strip().upper()
    if key not in PHENOTYPES:
        raise KeyError(f"Unknown phenotype {name!r}; choose from {sorted(PHENOTYPES)}")
    return deepcopy(PHENOTYPES[key])


def list_phenotypes() -> list[str]:
    return sorted(PHENOTYPES)
