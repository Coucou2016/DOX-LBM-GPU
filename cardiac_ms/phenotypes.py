"""
Literature-aligned phenotype presets (CONTROL / DOX1 / DOX2).

APD / CV targets are from Villar-Valero et al. (J Physiol 2025 / STACOM 2024)
reporting ranges — used as calibration anchors, not invented numbers.

0D APD is tuned primarily via ``tau_close`` where feasible. 1D/2D CV for DOX
phenotypes may not yet fully match literature fiber-direction targets; see
``notes`` on each preset and ``docs/ASSUMPTIONS.md``.
"""

from __future__ import annotations

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

# Villar-Valero-reported anchors (protocol alignment; not twin reproduction).
# CONTROL ~ healthy fiber CV ≈ 0.7 m/s; APD order ~250 ms (MS τ_close=150 → 0D≈257 ms).
# DOX phenotypes: reduced excitability / slower CV / altered APD as described in paper.
LITERATURE_TARGETS: dict[str, dict[str, Any]] = {
    "CONTROL": {
        "apd_ms_target": 250.0,
        "cv_mm_per_ms_target": 0.70,
        "source": "Villar-Valero J Physiol 2025 healthy fiber-direction CV ~0.7 m/s; APD design nominal 250 ms",
    },
    "DOX1": {
        "apd_ms_target": 280.0,
        "cv_mm_per_ms_target": 0.50,
        "source": "DOX1 extras train 240/200/190 ms; slowed conduction / remodeled APD (paper phenotype)",
    },
    "DOX2": {
        "apd_ms_target": 300.0,
        "cv_mm_per_ms_target": 0.40,
        "source": "DOX2 extras train (longer premature schedule); further remodeling vs CONTROL",
    },
}

# Protocol extras (coupling intervals relative to previous beat)
PROTOCOL_EXTRAS: dict[str, tuple[float, ...]] = {
    "CONTROL": (240.0,),
    "DOX1": (240.0, 200.0, 190.0),
    "DOX2": (260.0, 220.0, 200.0, 180.0),
}


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


PHENOTYPES: dict[str, dict[str, Any]] = {
    "CONTROL": {
        "name": "CONTROL",
        "params": {**_base_ms_params(), "tau_close": 150.0, "lam": 0.01},
        "D_mm2_per_ms": D_HEALTHY_MM2_PER_MS,
        "d_reduction": 0.0,
        "extra_cis_ms": PROTOCOL_EXTRAS["CONTROL"],
        "targets": LITERATURE_TARGETS["CONTROL"],
        "notes": (
            "0D APD golden ≈256.6 ms at tau_close=150 (near 250 ms design). "
            "Homogeneous 2D CV calibrated to ≈0.70 mm/ms."
        ),
        "cv_matched": True,
        "apd_matched_0d": True,
    },
    "DOX1": {
        "name": "DOX1",
        "params": {**_base_ms_params(), "tau_close": 170.0, "lam": 0.01},
        "D_mm2_per_ms": D_HEALTHY_MM2_PER_MS * 0.10,  # 90% reduction remaining 10%
        "d_reduction": 0.90,
        "extra_cis_ms": PROTOCOL_EXTRAS["DOX1"],
        "targets": LITERATURE_TARGETS["DOX1"],
        "notes": (
            "tau_close raised toward longer APD (0D calibration feasible). "
            "Annulus D↓90% used for verification geometry; 1D fiber CV vs paper "
            "DOX1 target not yet fully matched on this FD scaffold."
        ),
        "cv_matched": False,
        "apd_matched_0d": "partial",
    },
    "DOX2": {
        "name": "DOX2",
        "params": {**_base_ms_params(), "tau_close": 190.0, "lam": 0.1},
        "D_mm2_per_ms": D_HEALTHY_MM2_PER_MS * 0.30,
        "d_reduction": 0.70,
        "extra_cis_ms": PROTOCOL_EXTRAS["DOX2"],
        "targets": LITERATURE_TARGETS["DOX2"],
        "notes": (
            "Further APD lengthening via tau_close; λ=0.1 fibrotic excitability. "
            "1D CV for DOX2 not fully matched — document-only until calibrated."
        ),
        "cv_matched": False,
        "apd_matched_0d": "partial",
    },
}


def get_phenotype(name: str) -> dict[str, Any]:
    key = name.strip().upper()
    if key not in PHENOTYPES:
        raise KeyError(f"Unknown phenotype {name!r}; choose from {sorted(PHENOTYPES)}")
    return deepcopy(PHENOTYPES[key])


def list_phenotypes() -> list[str]:
    return sorted(PHENOTYPES)
