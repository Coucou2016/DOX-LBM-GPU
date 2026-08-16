"""Reference and golden regression tests (credibility layer)."""

import json
from pathlib import Path

import numpy as np
import pytest

from cardiac_ms import validation as val
from cardiac_ms.ms_0d import simulate_ms_0d, measure_apd
from cardiac_ms.ms_2d import simulate_mono2d


def test_ms_default_parameters():
    r = val.validate_ms_default_parameters()
    assert r["ok"], r.get("mismatches")


def test_ionic_step_matches_finitewave():
    r = val.validate_ionic_step_one_dt()
    assert r["ok"], r


def test_modified_ms_lambda0_matches_package():
    r = val.validate_modified_ms_lambda0_matches_package()
    assert r["ok"], r


def test_0d_apd_golden_seed42():
    r = val.validate_0d_apd_golden(seed=42)
    assert r["ok"], f"apd={r['apd_ms']}"


def test_0d_restitution_sweep():
    r = val.validate_0d_restitution_tau_out()
    assert r["ok"], r["sweep"]


def test_2d_cv_homogeneous_band():
    r = val.validate_2d_cv_homogeneous()
    assert r["ok"], r


def test_2d_golden_regression():
    r = val.validate_2d_golden_regression(seed=0)
    assert r["ok"], r


def test_diffusion_div_D_matches_D_laplacian():
    r = val.validate_diffusion_operator_consistency()
    assert r["ok"], f"err={r['max_abs_err']}"


def test_cfl_reference_math():
    r = val.validate_cfl_math()
    assert r["ok"]
    assert 0.03 < r["dt_ms"] < 0.05


def test_tau_out_changes_apd():
    """Restitution: larger tau_out lengthens APD (deterministic ODE)."""
    _, u_short, _ = simulate_ms_0d(n_steps=5000, dt=0.1, params={"tau_out": 4.0})
    _, u_long, _ = simulate_ms_0d(n_steps=5000, dt=0.1, params={"tau_out": 10.0})
    apd_short = measure_apd(np.arange(5000) * 0.1, u_short)["apd_ms"]
    apd_long = measure_apd(np.arange(5000) * 0.1, u_long)["apd_ms"]
    assert apd_short is not None and apd_long is not None
    assert apd_long > apd_short + 20.0


def test_fixed_seed_reproduces_golden_apd():
    t, u, _ = simulate_ms_0d(n_steps=5000, dt=0.1, seed=42)
    apd = measure_apd(t, u)
    assert apd["apd_ms"] is not None
    assert abs(apd["apd_ms"] - val.GOLDEN_0D_SEED42["apd_ms"]) < val.GOLDEN_0D_SEED42["apd_tol_ms"]


def test_synthetic_data_bundle_exists():
    root = Path(__file__).resolve().parents[1]
    syn = root / "data" / "synthetic"
    for name in ("fibrosis_patch_64_mask.npy", "fibrosis_patch_64_D.npy", "fibrosis_patch_64.json"):
        if not (syn / name).exists():
            pytest.skip(f"missing {syn / name}; run scripts/generate_synthetic_data.py")
    meta = json.loads((syn / "fibrosis_patch_64.json").read_text(encoding="utf-8"))
    assert meta["nx"] == 64 and meta["ny"] == 64
    D = np.load(syn / "fibrosis_patch_64_D.npy")
    assert D.shape == (64, 64)
    assert D.max() == pytest.approx(meta["conductivity"]["D_normal_mm2_per_ms"])
    assert D.min() == pytest.approx(meta["conductivity"]["D_fibrosis_mm2_per_ms"])


def test_fibrosis_uses_variable_D_diffusion():
    """With fibrosis, propagation still occurs; CV probe may be None if blocked."""
    _, u, _, meta = simulate_mono2d(
        nx=48,
        ny=48,
        n_steps=2000,
        dx=0.5,
        fibrosis=True,
        s2_window=(99999, 999999),
        s1_window=(5, 15),
    )
    assert u.max() > 0.4
    assert meta["fibrosis"] is True
    assert meta["D_min"] < meta["D_max"]
