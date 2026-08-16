"""Modified Mitchell–Schaeffer (λ) unit tests."""

import numpy as np
from mitchell_schaeffer.ops import get_parameters, ionic_step

from cardiac_ms.ms_0d import measure_apd
from cardiac_ms.ms_modified import (
    get_modified_parameters,
    ionic_rhs_modified,
    simulate_ms_0d_modified,
)


def test_lambda_zero_matches_finitewave_package():
    p_pkg = dict(get_parameters())
    p_mod = get_modified_parameters(lam=0.0, u_max=1.0)
    dt, u0, h0 = 0.1, 0.22, 0.9
    rhs_pkg, h1_pkg = ionic_step(dt, u0, h0, **p_pkg)
    u1_pkg = float(np.clip(u0 + dt * rhs_pkg, 0.0, 1.2))
    rhs_m, dh_m = ionic_rhs_modified(u0, h0, p_mod, lam=0.0)
    u1_m = float(np.clip(u0 + dt * float(np.asarray(rhs_m)), 0.0, 1.2))
    h1_m = float(np.clip(h0 + dt * float(np.asarray(dh_m)), 0.0, 1.0))
    assert abs(u1_pkg - u1_m) < 1e-12
    assert abs(float(h1_pkg) - h1_m) < 1e-12


def test_lambda_increase_lowers_peak_and_can_block():
    common = dict(n_steps=4000, dt=0.1, stim_start=50, stim_end=55, stim_u=0.25)
    _, u_h, _ = simulate_ms_0d_modified(lam=0.01, **common)
    _, u_mid, _ = simulate_ms_0d_modified(lam=0.1, **common)
    _, u_block, _ = simulate_ms_0d_modified(lam=0.3, **common)
    assert u_h.max() > 0.7
    assert u_mid.max() < u_h.max() + 1e-9
    # λ=0.3 > stim_u=0.25: inward current not regenerative at clamp → no AP
    assert u_block.max() < 0.35


def test_healthy_lambda_produces_apd():
    t, u, meta = simulate_ms_0d_modified(n_steps=5000, dt=0.1, lam=0.01)
    apd = measure_apd(t, u)
    assert meta["lam"] == 0.01
    assert apd["apd_ms"] is not None
    assert 80 < apd["apd_ms"] < 400
