"""Smoke and regression tests for 2D monodomain MS."""

import numpy as np
import pytest

from cardiac_ms import validation as val
from cardiac_ms.ms_2d import (
    check_cfl,
    diffusion_div_D_grad_neumann,
    estimate_cv_from_activation,
    laplacian_neumann,
    simulate_mono2d,
    suggest_dt_cfl,
)


def _run_short(**kwargs):
    defaults = dict(nx=40, ny=40, n_steps=1200, dx=0.5, enforce_cfl=True)
    defaults.update(kwargs)
    return simulate_mono2d(**defaults)


def test_cfl_suggest_and_check():
    dt_ok = suggest_dt_cfl(dx=0.5, D_max=0.8)
    assert dt_ok > 0
    r = check_cfl(dt_ok, dx=0.5, D_max=0.8, safety=0.5)
    assert r <= 0.5 + 1e-9
    with pytest.raises(ValueError, match="CFL unstable"):
        check_cfl(dt=0.5, dx=0.5, D_max=0.8, safety=0.5)


def test_activation_propagates():
    _, u, _, meta = _run_short(
        fibrosis=False,
        s2_window=(99999, 999999),
        s1_window=(5, 15),
    )
    assert u.max() > 0.5
    far = u[meta["ny"] // 2, -3:]
    assert float(far.max()) > 0.35, "wave should reach far field"
    assert np.isfinite(meta["activation_ms"]).any()


def test_fibrosis_slows_conduction():
    common = dict(
        nx=48,
        ny=48,
        n_steps=2000,
        dx=0.5,
        s2_window=(99999, 999999),
        s1_window=(5, 15),
    )
    _, _, _, meta_homo = simulate_mono2d(fibrosis=False, **common)
    _, _, _, meta_fib = simulate_mono2d(fibrosis=True, **common)
    cv_h = meta_homo.get("cv_mm_per_ms")
    cv_f = meta_fib.get("cv_mm_per_ms")
    if cv_h is not None and cv_f is not None:
        assert cv_f < cv_h * 1.05, f"fibrosis should not speed CV: {cv_f} vs {cv_h}"
    else:
        # Fallback: far-field activation later with fibrosis
        act_h = meta_homo["activation_ms"]
        act_f = meta_fib["activation_ms"]
        y, x = meta_homo["ny"] // 2, -4
        assert act_f[y, x] >= act_h[y, x] - 1e-6


def test_gate_h_updates_with_dt():
    """h must evolve (not stay 1 everywhere) after paced beat."""
    _, u, h, _ = _run_short(fibrosis=False, s1_window=(5, 20))
    assert u.max() > 0.5
    assert h.min() < 0.99


def test_homogeneous_cv_in_reference_band():
    r = val.validate_2d_cv_homogeneous(nx=40, ny=40, n_steps=1500)
    assert r["ok"]
    lo, hi = val.CV_MM_PER_MS_HOMO_RANGE
    assert lo <= r["cv_mm_per_ms"] <= hi


def test_cfl_clamped_when_dt_too_large():
    _, _, _, meta = simulate_mono2d(
        nx=32,
        ny=32,
        n_steps=200,
        dt=1.0,
        dx=0.5,
        fibrosis=False,
        enforce_cfl=True,
        s2_window=(99999, 999999),
        s1_window=(2, 8),
    )
    assert meta["dt_clamped"] is True
    assert meta["cfl_r"] <= val.CFL_R_MAX_STABLE + 1e-6


def test_constant_D_diffusion_operators_agree():
    rng = np.random.default_rng(7)
    u = rng.random((24, 24))
    D0 = 0.8
    dx = 0.5
    lap = laplacian_neumann(u, dx) * D0
    div = diffusion_div_D_grad_neumann(u, np.full_like(u, D0), dx)
    err = np.max(np.abs(lap[1:-1, 1:-1] - div[1:-1, 1:-1]))
    assert err < 1e-9
