#!/usr/bin/env python
"""
Calibrate CONTROL / DOX1 / DOX2 0D APD (tau_close) and homogeneous 2D CV (D).

Literature anchors (Villar-Valero J Physiol 2025, healthy tissue):
  APD: 309 / 269 / 210 ms
  CV:  71 / 41 / 43.89 cm/s  (= 0.71 / 0.41 / 0.44 mm/ms)

Writes data/phenotype_calibration.json. Sets cv_matched / apd_matched_0d only
when measured values fall within ±10%; otherwise keeps False and records residual.
Does not invent twin fidelity.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cardiac_ms.ms_0d import measure_apd
from cardiac_ms.ms_modified import get_modified_parameters, simulate_ms_0d_modified
from cardiac_ms.phenotypes import (
    APD_MATCH_TOL_FRAC,
    CV_MATCH_TOL_FRAC,
    LITERATURE_TARGETS,
    PHENOTYPES,
    within_tol,
)
from cardiac_ms.validation import measure_homogeneous_cv


def measure_0d_apd(tau_close: float, lam: float = 0.01) -> float | None:
    p = get_modified_parameters(lam=lam)
    p["tau_close"] = float(tau_close)
    t, u, _ = simulate_ms_0d_modified(n_steps=8000, dt=0.1, params=p)
    return measure_apd(t, u).get("apd_ms")


def refine_tau_close(
    target_apd: float,
    *,
    lam: float,
    lo: float = 80.0,
    hi: float = 260.0,
    n: int = 12,
) -> dict:
    """Coarse grid + linear interp for tau_close → APD."""
    grid = np.linspace(lo, hi, n)
    rows = []
    for tc in grid:
        apd = measure_0d_apd(float(tc), lam=lam)
        rows.append({"tau_close": float(tc), "apd_ms": apd})
    xs = np.array([r["tau_close"] for r in rows if r["apd_ms"] is not None])
    ys = np.array([r["apd_ms"] for r in rows if r["apd_ms"] is not None], dtype=float)
    tau_star = None
    if xs.size >= 2:
        order = np.argsort(ys)
        tau_star = float(np.interp(target_apd, ys[order], xs[order]))
        apd_check = measure_0d_apd(tau_star, lam=lam)
        rows.append({"tau_close": tau_star, "apd_ms": apd_check, "interpolated": True})
    return {"tau_close_star": tau_star, "samples": rows}


def refine_D(
    target_cv: float,
    *,
    lam: float,
    tau_close: float,
    d_lo: float = 0.005,
    d_hi: float = 0.08,
    n: int = 7,
) -> dict:
    """Coarse grid + interp for homogeneous-sheet D → CV."""
    grid = np.linspace(d_lo, d_hi, n)
    rows = []
    for d in grid:
        r = measure_homogeneous_cv(
            float(d),
            lam=lam,
            params={"tau_close": float(tau_close), "lam": float(lam)},
            stimulus_mode="current",
            stim_u=0.8,
        )
        rows.append(
            {
                "D_mm2_per_ms": float(d),
                "cv_mm_per_ms": r.get("cv_mm_per_ms"),
                "u_max": r.get("u_max"),
                "cfl_r": r.get("cfl_r"),
                "dt": r.get("dt"),
            }
        )
    xs = np.array([r["D_mm2_per_ms"] for r in rows if r["cv_mm_per_ms"] is not None])
    ys = np.array(
        [r["cv_mm_per_ms"] for r in rows if r["cv_mm_per_ms"] is not None], dtype=float
    )
    d_star = None
    check = None
    if xs.size >= 2 and np.nanmin(ys) <= target_cv <= np.nanmax(ys):
        order = np.argsort(ys)
        d_star = float(np.interp(target_cv, ys[order], xs[order]))
        check = measure_homogeneous_cv(
            d_star,
            lam=lam,
            params={"tau_close": float(tau_close), "lam": float(lam)},
            stimulus_mode="current",
            stim_u=0.8,
        )
        rows.append(
            {
                "D_mm2_per_ms": d_star,
                "cv_mm_per_ms": check.get("cv_mm_per_ms"),
                "u_max": check.get("u_max"),
                "cfl_r": check.get("cfl_r"),
                "dt": check.get("dt"),
                "interpolated": True,
            }
        )
    elif xs.size >= 2:
        # Pick nearest grid point; cannot fully match in range
        idx = int(np.nanargmin(np.abs(ys - target_cv)))
        d_star = float(xs[idx])
        check = measure_homogeneous_cv(
            d_star,
            lam=lam,
            params={"tau_close": float(tau_close), "lam": float(lam)},
            stimulus_mode="current",
            stim_u=0.8,
        )
        rows.append({**{k: check.get(k) for k in ("cv_mm_per_ms", "u_max", "cfl_r", "dt")},
                     "D_mm2_per_ms": d_star, "nearest_grid": True})
    return {"D_star": d_star, "check": check, "samples": rows}


def calibrate_one(name: str, *, refine: bool = True) -> dict:
    ph = PHENOTYPES[name]
    tgt = LITERATURE_TARGETS[name]
    lam = float(ph["params"]["lam"])
    tau0 = float(ph["params"]["tau_close"])
    d0 = float(ph["D_mm2_per_ms"])

    if refine:
        apd_fit = refine_tau_close(float(tgt["apd_ms_target"]), lam=lam)
        tau_use = float(apd_fit["tau_close_star"] or tau0)
    else:
        apd_fit = None
        tau_use = tau0

    apd_meas = measure_0d_apd(tau_use, lam=lam)
    apd_ok = within_tol(apd_meas, float(tgt["apd_ms_target"]), APD_MATCH_TOL_FRAC)
    apd_err = None if apd_meas is None else float(apd_meas) - float(tgt["apd_ms_target"])
    apd_err_pct = (
        None
        if apd_meas is None
        else 100.0 * apd_err / float(tgt["apd_ms_target"])
    )

    if refine:
        cv_fit = refine_D(
            float(tgt["cv_mm_per_ms_target"]),
            lam=lam,
            tau_close=tau_use,
        )
        d_use = float(cv_fit["D_star"] or d0)
        cv_check = cv_fit.get("check") or measure_homogeneous_cv(
            d_use,
            lam=lam,
            params={"tau_close": tau_use, "lam": lam},
            stimulus_mode="current",
            stim_u=0.8,
        )
    else:
        cv_fit = None
        d_use = d0
        cv_check = measure_homogeneous_cv(
            d_use,
            lam=lam,
            params={"tau_close": tau_use, "lam": lam},
            stimulus_mode="current",
            stim_u=0.8,
        )

    cv_meas = cv_check.get("cv_mm_per_ms") if cv_check else None
    cfl_r = cv_check.get("cfl_r") if cv_check else None
    cv_ok = within_tol(cv_meas, float(tgt["cv_mm_per_ms_target"]), CV_MATCH_TOL_FRAC)
    # Require stable CFL to claim matched
    if cfl_r is not None and float(cfl_r) > 0.51:
        cv_ok = False
    cv_err = None if cv_meas is None else float(cv_meas) - float(tgt["cv_mm_per_ms_target"])
    cv_err_pct = (
        None
        if cv_meas is None
        else 100.0 * cv_err / float(tgt["cv_mm_per_ms_target"])
    )

    return {
        "phenotype": name,
        "literature": dict(tgt),
        "tau_close": tau_use,
        "D_mm2_per_ms": d_use,
        "lam": lam,
        "apd_ms_measured": apd_meas,
        "apd_error_ms": apd_err,
        "apd_error_pct": apd_err_pct,
        "apd_matched_0d": bool(apd_ok),
        "cv_mm_per_ms_measured": cv_meas,
        "cv_error_mm_per_ms": cv_err,
        "cv_error_pct": cv_err_pct,
        "cv_matched": bool(cv_ok),
        "cfl_r": cfl_r,
        "dt_ms": cv_check.get("dt") if cv_check else None,
        "u_max": cv_check.get("u_max") if cv_check else None,
        "preset_tau_close": tau0,
        "preset_D_mm2_per_ms": d0,
        "apd_fit": apd_fit,
        "cv_fit": {
            "D_star": cv_fit.get("D_star") if cv_fit else d_use,
            "n_samples": len(cv_fit["samples"]) if cv_fit else 1,
        },
        "match_tol_frac": {"apd": APD_MATCH_TOL_FRAC, "cv": CV_MATCH_TOL_FRAC},
        "notes": ph.get("notes"),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--no-refine",
        action="store_true",
        help="Only measure current phenotype presets (no tau/D re-fit)",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "data" / "phenotype_calibration.json",
    )
    args = ap.parse_args()

    rows = []
    for name in ("CONTROL", "DOX1", "DOX2"):
        print(f"=== {name} ===")
        row = calibrate_one(name, refine=not args.no_refine)
        rows.append(row)
        print(
            f"  APD {row['apd_ms_measured']} (target {row['literature']['apd_ms_target']}) "
            f"matched={row['apd_matched_0d']}  err%={row['apd_error_pct']}"
        )
        print(
            f"  CV  {row['cv_mm_per_ms_measured']} (target {row['literature']['cv_mm_per_ms_target']}) "
            f"matched={row['cv_matched']}  err%={row['cv_error_pct']}  "
            f"D={row['D_mm2_per_ms']}  cfl={row['cfl_r']}"
        )

    report = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source": "Villar-Valero J Physiol 2025 healthy-tissue APD/CV anchors",
        "acceptance": "±10% for apd_matched_0d / cv_matched; CFL must be stable",
        "phenotypes": rows,
        "all_apd_matched": all(r["apd_matched_0d"] for r in rows),
        "all_cv_matched": all(r["cv_matched"] for r in rows),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
