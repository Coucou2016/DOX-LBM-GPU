"""Modified Mitchell–Schaeffer ionic model with excitability parameter λ.

Inward current (Djabella 2007 / Villar-Valero J Physiol 2025):

    J_in  = h * u * (u - λ) * (u_max - u) / τ_in
    J_out = -u / τ_out
    ∂u/∂t = J_in + J_out + J_stim
    ∂h/∂t = (1-h)/τ_open  if u < u_gate  else  -h/τ_close

When λ=0 and u_max=1 this is identical to Mitchell & Schaeffer (2003) /
finitewave ``calc_J_in``. Healthy tissue in the paper uses λ=0.01 (not 0).

Units: t in ms, u dimensionless.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from cardiac_ms.constants import (
    LAMBDA_HEALTHY,
    TAU_CLOSE,
    TAU_IN,
    TAU_OPEN,
    TAU_OUT,
    U_GATE,
    U_MAX,
)


def get_modified_parameters(
    *,
    lam: float = LAMBDA_HEALTHY,
    u_max: float = U_MAX,
    tau_in: float = TAU_IN,
    tau_out: float = TAU_OUT,
    tau_open: float = TAU_OPEN,
    tau_close: float = TAU_CLOSE,
    u_gate: float = U_GATE,
) -> dict[str, float]:
    """Default modified-MS parameters (paper healthy λ=0.01)."""
    return {
        "tau_close": float(tau_close),
        "tau_open": float(tau_open),
        "tau_out": float(tau_out),
        "tau_in": float(tau_in),
        "u_gate": float(u_gate),
        "lam": float(lam),
        "u_max": float(u_max),
    }


def calc_J_in_modified(u, h, tau_in, lam=0.0, u_max=1.0):
    """J_in = h * u * (u-λ) * (u_max-u) / τ_in  (scalar or ndarray)."""
    return h * u * (u - lam) * (u_max - u) / tau_in


def calc_J_out_modified(u, tau_out):
    return -u / tau_out


def ionic_rhs_modified(
    u,
    h,
    p: dict[str, float] | None = None,
    *,
    lam=None,
    tau_close=None,
    u_max=None,
):
    """
    Return (du/dt ionic, dh/dt). ``lam`` and ``tau_close`` may be scalars or
    arrays broadcastable to ``u`` (three-class tissue).
    """
    if p is None:
        p = get_modified_parameters()
    tau_in = p["tau_in"]
    tau_out = p["tau_out"]
    tau_open = p["tau_open"]
    u_gate = p["u_gate"]
    if lam is None:
        lam = p.get("lam", LAMBDA_HEALTHY)
    if u_max is None:
        u_max = p.get("u_max", U_MAX)
    if tau_close is None:
        tau_close = p["tau_close"]

    j_in = calc_J_in_modified(u, h, tau_in, lam=lam, u_max=u_max)
    j_out = calc_J_out_modified(u, tau_out)
    dh = np.where(u < u_gate, (1.0 - h) / tau_open, -h / tau_close)
    return j_in + j_out, dh


def simulate_ms_0d_modified(
    n_steps: int = 5000,
    dt: float = 0.1,
    *,
    stim_start: int = 50,
    stim_end: int = 55,
    stim_u: float = 0.25,
    lam: float = LAMBDA_HEALTHY,
    params: dict[str, float] | None = None,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """0D Euler integration of modified MS. Stimulus is a brief voltage clamp."""
    p = get_modified_parameters(lam=lam)
    if params:
        p.update(params)
        if "lam" not in (params or {}) and lam != LAMBDA_HEALTHY:
            p["lam"] = lam

    u = 0.0
    h = 1.0
    u_trace = np.empty(n_steps, dtype=np.float64)
    for i in range(n_steps):
        if stim_start < i < stim_end:
            u = stim_u
        rhs, dh = ionic_rhs_modified(u, h, p)
        u = float(np.clip(u + dt * float(np.asarray(rhs)), 0.0, 1.2))
        h = float(np.clip(h + dt * float(np.asarray(dh)), 0.0, 1.0))
        u_trace[i] = u

    t_ms = np.arange(n_steps, dtype=np.float64) * dt
    return t_ms, u_trace, {"dt": dt, "n_steps": n_steps, "params": p, "lam": p["lam"]}
