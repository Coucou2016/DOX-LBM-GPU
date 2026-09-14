"""
Literature targets vs calibrated model parameters (CONTROL / DOX1 / DOX2).

Literature TARGETS are data-only anchors from Villar-Valero et al.
(*J Physiol* 2026). They are **not** model presets:

- CONTROL healthy APD 309 ms, CV 0.71 mm/ms
- DOX1 healthy APD 269 ms, fibrosis APD 276 ms, CV 0.41 mm/ms
- DOX2 healthy APD 210 ms, fibrosis APD 184 ms, CV 0.4389 mm/ms

DOX APD is **shorter** than CONTROL (not longer).

Calibrated ionic/diffusion parameters (``tau_close``, ``D``, ``lam``) live in
``PHENOTYPES`` after 0D/1D–2D fit via ``scripts/calibrate_phenotypes.py``.
Until a fit is written, prefer names like ``DOX1_target`` for literature-only
dicts — never claim “preset is literature.”
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

# --- Literature TARGETS (data only; Villar-Valero J Physiol 2026) ---
LITERATURE_TARGETS: dict[str, dict[str, Any]] = {
    "CONTROL": {
        "name": "CONTROL_target",
        "apd_ms_target": 309.0,
        "apd_fibrosis_ms_target": None,
        "cv_mm_per_ms_target": 0.71,
        "cv_cm_per_s_target": 71.0,
        "source": (
            "Villar-Valero J Physiol 2026: healthy-tissue APD 309 ms; "
            "fiber-direction CV 71 cm/s (0.71 mm/ms)"
        ),
    },
    "DOX1": {
        "name": "DOX1_target",
        "apd_ms_target": 269.0,
        "apd_fibrosis_ms_target": 276.0,
        "cv_mm_per_ms_target": 0.41,
        "cv_cm_per_s_target": 41.0,
        "source": (
            "Villar-Valero: DOX1 healthy APD 269 ms, fibrosis APD 276 ms; "
            "CV 41 cm/s (0.41 mm/ms)"
        ),
    },
    "DOX2": {
        "name": "DOX2_target",
        "apd_ms_target": 210.0,
        "apd_fibrosis_ms_target": 184.0,
        "cv_mm_per_ms_target": 0.4389,
        "cv_cm_per_s_target": 43.89,
        "source": (
            "Villar-Valero: DOX2 healthy APD 210 ms, fibrosis APD 184 ms; "
            "CV 43.89 cm/s (0.4389 mm/ms)"
        ),
    },
}

# Alias names for literature-only lookups (do not treat as calibrated presets).
LITERATURE_TARGET_ALIASES: dict[str, str] = {
    "CONTROL_TARGET": "CONTROL",
    "DOX1_TARGET": "DOX1",
    "DOX2_TARGET": "DOX2",
}

# Protocol extras (coupling intervals relative to previous beat).
# CONTROL: no ectopic extras. DOX2 main: four extras at 250 ms each.
# Transition-zone protocols (e.g. 260/220/200/180) are optional later — not invented here.
PROTOCOL_EXTRAS: dict[str, tuple[float, ...]] = {
    "CONTROL": (),
    "DOX1": (240.0, 200.0, 190.0),
    "DOX2": (250.0, 250.0, 250.0, 250.0),
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


# Calibrated model parameters after 0D APD / homogeneous CV fit
# (scripts/calibrate_phenotypes.py → data/phenotype_calibration.json, 2026-09-14).
PHENOTYPES: dict[str, dict[str, Any]] = {
    "CONTROL": {
        "name": "CONTROL",
        "params": {**_base_ms_params(), "tau_close": 183.90293916609704, "lam": 0.01},
        "D_mm2_per_ms": 0.04734018518518519,
        "d_reduction": 0.0,
        "extra_cis_ms": PROTOCOL_EXTRAS["CONTROL"],
        "targets": LITERATURE_TARGETS["CONTROL"],
        "notes": (
            "Calibrated model params aiming at CONTROL_target "
            "(APD 309 ms, CV 0.71 mm/ms). Not identical to literature numbers."
        ),
        "cv_matched": True,
        "apd_matched_0d": True,
        "apd_ms_measured": 309.0,
        "cv_mm_per_ms_measured": 0.7086614173228345,
    },
    "DOX1": {
        "name": "DOX1",
        "params": {**_base_ms_params(), "tau_close": 159.30541368743613, "lam": 0.01},
        "D_mm2_per_ms": 0.015493373680943508,
        "d_reduction": 0.90,
        "extra_cis_ms": PROTOCOL_EXTRAS["DOX1"],
        "targets": LITERATURE_TARGETS["DOX1"],
        "notes": (
            "Calibrated model params aiming at DOX1_target "
            "(healthy APD 269 ms, CV 0.41 mm/ms). Annulus d_reduction=0.90 is a "
            "fibrosis-zone relative cut for VA scans, not a literature constant."
        ),
        "cv_matched": True,
        "apd_matched_0d": True,
        "apd_ms_measured": 269.0,
        "cv_mm_per_ms_measured": 0.4166666666666668,
    },
    "DOX2": {
        "name": "DOX2",
        "params": {**_base_ms_params(), "tau_close": 138.0977845683728, "lam": 0.1},
        "D_mm2_per_ms": 0.02673,
        "d_reduction": 0.70,
        "extra_cis_ms": PROTOCOL_EXTRAS["DOX2"],
        "targets": LITERATURE_TARGETS["DOX2"],
        "notes": (
            "Calibrated model params aiming at DOX2_target "
            "(healthy APD 210 ms, CV 0.4389 mm/ms). DOX APD is shorter than CONTROL."
        ),
        "cv_matched": True,
        "apd_matched_0d": True,
        "apd_ms_measured": 210.1,
        "cv_mm_per_ms_measured": 0.44117647058823517,
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


def get_literature_target(name: str) -> dict[str, Any]:
    key = name.strip().upper()
    if key in LITERATURE_TARGET_ALIASES:
        key = LITERATURE_TARGET_ALIASES[key]
    if key not in LITERATURE_TARGETS:
        raise KeyError(
            f"Unknown literature target {name!r}; choose from "
            f"{sorted(LITERATURE_TARGETS) + sorted(LITERATURE_TARGET_ALIASES)}"
        )
    return deepcopy(LITERATURE_TARGETS[key])


def get_phenotype(name: str) -> dict[str, Any]:
    key = name.strip().upper()
    if key in LITERATURE_TARGET_ALIASES:
        # Explicit *_target request → literature data only (no calibrated params).
        tgt = get_literature_target(key)
        return {
            "name": tgt["name"],
            "kind": "literature_target",
            "targets": tgt,
            "params": None,
            "D_mm2_per_ms": None,
            "d_reduction": None,
            "extra_cis_ms": PROTOCOL_EXTRAS.get(
                LITERATURE_TARGET_ALIASES[key], ()
            ),
            "notes": "Literature target only — not a calibrated model preset.",
            "cv_matched": False,
            "apd_matched_0d": False,
        }
    if key not in PHENOTYPES:
        raise KeyError(f"Unknown phenotype {name!r}; choose from {sorted(PHENOTYPES)}")
    return deepcopy(PHENOTYPES[key])


def list_phenotypes() -> list[str]:
    return sorted(PHENOTYPES)


def list_literature_targets() -> list[str]:
    return sorted(LITERATURE_TARGETS)
