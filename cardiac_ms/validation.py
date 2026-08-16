"""
Reference checks for Mitchell–Schaeffer 0D/2D against published defaults and golden runs.

Golden numbers were recorded on Windows/Python 3.13 with
``finitewave-model-mitchell-schaeffer==0.6.0`` (see ``requirements.txt``).
"""

from __future__ import annotations

from typing import Any

import numpy as np

from cardiac_ms.ms_0d import measure_apd, simulate_ms_0d
from cardiac_ms.ms_2d import (
    check_cfl,
    diffusion_div_D_grad_neumann,
    laplacian_neumann,
    simulate_mono2d,
    suggest_dt_cfl,
)
from cardiac_ms.ms_modified import get_modified_parameters, ionic_rhs_modified
from cardiac_ms.constants import (
    CV_CALIBRATION_BAND,
    CV_TARGET_MM_PER_MS,
    D_HEALTHY_MM2_PER_MS,
    LAMBDA_HEALTHY,
)
from mitchell_schaeffer.ops import get_parameters, ionic_step

# finitewave-model-mitchell-schaeffer 0.6.0 defaults (Mitchell & Schaeffer 2003, via package)
REFERENCE_MS_PARAMS: dict[str, float] = {
    "tau_close": 150.0,
    "tau_open": 120.0,
    "tau_out": 6.0,
    "tau_in": 0.3,
    "u_gate": 0.13,
}

# 0D golden: simulate_ms_0d(n_steps=5000, dt=0.1, seed=42), default pacing
GOLDEN_0D_SEED42: dict[str, float] = {
    "apd_ms": 256.6,
    "peak_u": 0.945,
    "apd_tol_ms": 8.0,
    "peak_u_tol": 0.03,
}

# Physiological band for default params (any seed with successful AP)
APD_MS_RANGE_DEFAULT: tuple[float, float] = (200.0, 320.0)

# 2D homogeneous plane-wave CV: paper healthy fiber-direction target 0.7 m/s
# = 0.7 mm/ms. Band is the calibration acceptance window.
CV_MM_PER_MS_HOMO_RANGE: tuple[float, float] = CV_CALIBRATION_BAND
GOLDEN_2D_HOMO_SEED0: dict[str, float] = {
    "cv_mm_per_ms": 0.703,
    "cv_tol": 0.12,
    "u_max": 0.875,
    "u_max_tol": 0.10,
    "D_mm2_per_ms": D_HEALTHY_MM2_PER_MS,
}

# Analytical CFL: dt <= dx^2 / (4 D)  =>  r = D*dt/(dx^2/4) <= 1
CFL_R_MAX_STABLE = 0.51


def validate_ms_default_parameters(tol: float = 1e-9) -> dict[str, Any]:
    """Package parameters must match documented MS defaults."""
    got = get_parameters()
    mismatches = {
        k: (got[k], REFERENCE_MS_PARAMS[k])
        for k in REFERENCE_MS_PARAMS
        if abs(float(got[k]) - REFERENCE_MS_PARAMS[k]) > tol
    }
    ok = len(mismatches) == 0
    return {"ok": ok, "mismatches": mismatches, "params": dict(got)}


def validate_ionic_step_one_dt(dt: float = 0.1, tol: float = 1e-12) -> dict[str, Any]:
    """
    One explicit Euler ionic step must match finitewave ``ionic_step`` + clip.
    """
    p = get_parameters()
    u0, h0 = 0.2, 0.95
    rhs, h1_pkg = ionic_step(dt, u0, h0, **p)
    u1_pkg = float(np.clip(u0 + dt * rhs, 0.0, 1.2))
    h1_pkg = float(h1_pkg)

    from cardiac_ms.ms_2d import ionic_rhs_vectorized

    u_arr = np.array([[u0]])
    h_arr = np.array([[h0]])
    rhs_v, dh_v = ionic_rhs_vectorized(u_arr, h_arr, dict(p))
    u1_v = float(np.clip(u0 + dt * float(rhs_v[0, 0]), 0.0, 1.2))
    h1_v = float(np.clip(h0 + dt * float(dh_v[0, 0]), 0.0, 1.0))

    ok = (
        abs(u1_pkg - u1_v) < tol
        and abs(h1_pkg - h1_v) < tol
        and abs(h1_pkg - float(np.clip(h0 + dt * (dh_v[0, 0]), 0.0, 1.0))) < tol
    )
    return {
        "ok": ok,
        "u_pkg": u1_pkg,
        "u_vec": u1_v,
        "h_pkg": h1_pkg,
        "h_vec": h1_v,
    }


def validate_0d_apd_golden(seed: int = 42, **kwargs: Any) -> dict[str, Any]:
    """0D APD and peak vs stored golden (fixed seed)."""
    t, u, _ = simulate_ms_0d(n_steps=5000, dt=0.1, seed=seed, **kwargs)
    apd = measure_apd(t, u)
    apd_ms = float(apd["apd_ms"]) if apd["apd_ms"] is not None else float("nan")
    peak_u = float(apd["peak_u"])
    ok_apd = abs(apd_ms - GOLDEN_0D_SEED42["apd_ms"]) <= GOLDEN_0D_SEED42["apd_tol_ms"]
    ok_peak = abs(peak_u - GOLDEN_0D_SEED42["peak_u"]) <= GOLDEN_0D_SEED42["peak_u_tol"]
    lo, hi = APD_MS_RANGE_DEFAULT
    ok_range = lo <= apd_ms <= hi
    return {
        "ok": ok_apd and ok_peak and ok_range,
        "apd_ms": apd_ms,
        "peak_u": peak_u,
        "golden_apd_ms": GOLDEN_0D_SEED42["apd_ms"],
    }


def validate_0d_restitution_tau_out() -> dict[str, Any]:
    """Longer tau_out should not shorten APD below the shortest-case floor."""
    results = []
    for tau_out in (4.0, 6.0, 10.0):
        t, u, _ = simulate_ms_0d(n_steps=5000, dt=0.1, params={"tau_out": tau_out}, seed=0)
        apd = measure_apd(t, u)
        results.append({"tau_out": tau_out, "apd_ms": apd.get("apd_ms")})
    apds = [r["apd_ms"] for r in results if r["apd_ms"] is not None]
    ok = len(apds) == 3 and all(80 < a < 450 for a in apds)
    return {"ok": ok, "sweep": results}


def validate_modified_ms_lambda0_matches_package(dt: float = 0.1, tol: float = 1e-12) -> dict[str, Any]:
    """λ=0, u_max=1 modified RHS must match finitewave ionic_step (classic MS)."""
    p_pkg = dict(get_parameters())
    p_mod = get_modified_parameters(lam=0.0, u_max=1.0)
    u0, h0 = 0.2, 0.95
    rhs_pkg, h1_pkg = ionic_step(dt, u0, h0, **p_pkg)
    u1_pkg = float(np.clip(u0 + dt * rhs_pkg, 0.0, 1.2))
    rhs_m, dh_m = ionic_rhs_modified(u0, h0, p_mod, lam=0.0)
    u1_m = float(np.clip(u0 + dt * float(np.asarray(rhs_m)), 0.0, 1.2))
    h1_m = float(np.clip(h0 + dt * float(np.asarray(dh_m)), 0.0, 1.0))
    ok = abs(u1_pkg - u1_m) < tol and abs(float(h1_pkg) - h1_m) < tol
    return {"ok": ok, "u_pkg": u1_pkg, "u_mod": u1_m, "h_pkg": float(h1_pkg), "h_mod": h1_m}


def _cv_probe_kwargs(**overrides: Any) -> dict[str, Any]:
    defaults = dict(
        nx=48,
        ny=48,
        n_steps=2500,
        dt=0.1,
        dx=0.5,
        fibrosis=False,
        s2_window=(99999, 999999),
        s1_window=(5, 15),
        enforce_cfl=True,
        use_modified_ms=True,
        snapshots=False,
        lam=LAMBDA_HEALTHY,
    )
    defaults.update(overrides)
    return defaults


def measure_homogeneous_cv(D: float, **kwargs: Any) -> dict[str, Any]:
    """Two-point CV on the standard 48² homogeneous sheet (mm/ms)."""
    _, u, _, meta = simulate_mono2d(**_cv_probe_kwargs(D_normal=D, **kwargs))
    return {
        "cv_mm_per_ms": meta.get("cv_mm_per_ms"),
        "u_max": float(u.max()),
        "dt": meta["dt"],
        "cfl_r": meta["cfl_r"],
        "D": D,
    }


def calibrate_healthy_diffusion(
    target: float = CV_TARGET_MM_PER_MS,
    d_grid: tuple[float, ...] = (0.04, 0.055, 0.07, 0.09, 0.12),
) -> dict[str, Any]:
    """
    Interpolate D so two-point CV ≈ target (paper 0.7 mm/ms).

    Not run inside pytest; used to set ``D_HEALTHY_MM2_PER_MS``.
    """
    rec = []
    for d in d_grid:
        r = measure_homogeneous_cv(d)
        rec.append(r)
    ds = np.array([r["D"] for r in rec], dtype=np.float64)
    cvs = np.array(
        [r["cv_mm_per_ms"] if r["cv_mm_per_ms"] is not None else np.nan for r in rec]
    )
    finite = np.isfinite(cvs)
    d_star = None
    if finite.sum() >= 2:
        order = np.argsort(cvs[finite])
        d_star = float(np.interp(target, cvs[finite][order], ds[finite][order]))
        check = measure_homogeneous_cv(d_star)
        rec.append({**check, "interpolated": True})
    return {"D_star": d_star, "target": target, "samples": rec}


def validate_2d_cv_homogeneous(**kwargs: Any) -> dict[str, Any]:
    """Homogeneous 2D run: CV in paper calibration band, CFL respected."""
    _, u, _, meta = simulate_mono2d(**_cv_probe_kwargs(**kwargs))
    cv = meta.get("cv_mm_per_ms")
    cfl_r = float(meta["cfl_r"])
    u_max = float(u.max())
    lo, hi = CV_MM_PER_MS_HOMO_RANGE
    ok_cv = cv is not None and lo <= cv <= hi
    ok_cfl = cfl_r <= CFL_R_MAX_STABLE
    ok_u = u_max > 0.7
    return {
        "ok": ok_cv and ok_cfl and ok_u,
        "cv_mm_per_ms": cv,
        "cfl_r": cfl_r,
        "u_max": u_max,
        "dt_ms": meta["dt"],
        "D": meta["D_max"],
    }


def validate_2d_golden_regression(seed: int = 0) -> dict[str, Any]:
    """Fixed small grid regression against stored CV / u_max (calibrated D, λ=0.01)."""
    np.random.seed(seed)
    _, u, _, meta = simulate_mono2d(**_cv_probe_kwargs())
    cv = meta.get("cv_mm_per_ms")
    u_max = float(u.max())
    g = GOLDEN_2D_HOMO_SEED0
    ok = (
        cv is not None
        and abs(cv - g["cv_mm_per_ms"]) <= g["cv_tol"]
        and abs(u_max - g["u_max"]) <= g["u_max_tol"]
    )
    return {"ok": ok, "cv_mm_per_ms": cv, "u_max": u_max, "D": meta["D_max"]}


def validate_diffusion_operator_consistency(dx: float = 0.5, D0: float = 0.8) -> dict[str, Any]:
    """div(D grad u) with constant D must match D * Laplacian (Neumann)."""
    rng = np.random.default_rng(0)
    u = rng.random((32, 32))
    D = np.full_like(u, D0)
    lap = laplacian_neumann(u, dx) * D0
    div = diffusion_div_D_grad_neumann(u, D, dx)
    # laplacian_neumann leaves corners unset; compare interior only
    interior = (slice(1, -1), slice(1, -1))
    err = float(np.max(np.abs(lap[interior] - div[interior])))
    ok = err < 1e-9
    return {"ok": ok, "max_abs_err": err}


def validate_cfl_math(dx: float = 0.5, D_max: float = 0.8) -> dict[str, Any]:
    dt = suggest_dt_cfl(dx, D_max, safety=0.5)
    r = check_cfl(dt, dx, D_max, safety=0.5)
    return {"ok": r <= 0.5 + 1e-12, "dt_ms": dt, "cfl_r": r}


def run_all_validations() -> dict[str, Any]:
    """Run every check; return aggregate report for CLI / smoke."""
    checks = {
        "ms_params": validate_ms_default_parameters(),
        "ionic_step": validate_ionic_step_one_dt(),
        "modified_ms_lam0": validate_modified_ms_lambda0_matches_package(),
        "0d_golden": validate_0d_apd_golden(),
        "0d_restitution": validate_0d_restitution_tau_out(),
        "2d_cv": validate_2d_cv_homogeneous(),
        "2d_golden": validate_2d_golden_regression(),
        "diffusion_op": validate_diffusion_operator_consistency(),
        "cfl": validate_cfl_math(),
    }
    all_ok = all(c["ok"] for c in checks.values())
    return {"all_ok": all_ok, "checks": checks}


if __name__ == "__main__":
    import json
    import sys

    report = run_all_validations()
    print(json.dumps(report, indent=2, default=str))
    raise SystemExit(0 if report["all_ok"] else 1)
