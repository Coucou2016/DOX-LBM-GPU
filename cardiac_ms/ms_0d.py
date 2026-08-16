"""0D Mitchell-Schaeffer integration and APD measurement."""

from __future__ import annotations

import time
from typing import Any

import numpy as np

try:
    from mitchell_schaeffer.ops import get_parameters, get_variables, ionic_step
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "Install the MS model: pip install finitewave-model-mitchell-schaeffer"
    ) from exc


def simulate_ms_0d(
    n_steps: int = 5000,
    dt: float = 0.1,
    *,
    stim_start: int = 50,
    stim_end: int = 55,
    stim_u: float = 0.25,
    params: dict[str, float] | None = None,
    seed: int | None = None,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """
    Integrate MS in 0D with a brief voltage clamp stimulus.

    Returns (time_ms, u_trace, meta) where meta has timing and optional params.
    """
    if seed is not None:
        np.random.seed(seed)

    p = dict(get_parameters())
    if params:
        p.update(params)

    s = get_variables()
    u, h = float(s["u"]), float(s["h"])
    u_trace = np.empty(n_steps, dtype=np.float64)
    t0 = time.perf_counter()

    for i in range(n_steps):
        if stim_start < i < stim_end:
            u = stim_u
        rhs, h = ionic_step(dt, u, h, **p)
        u = float(np.clip(u + dt * rhs, 0.0, 1.2))
        u_trace[i] = u

    elapsed = time.perf_counter() - t0
    t_ms = np.arange(n_steps, dtype=np.float64) * dt
    meta = {
        "dt": dt,
        "n_steps": n_steps,
        "elapsed_s": elapsed,
        "steps_per_s": n_steps / elapsed if elapsed > 0 else float("inf"),
        "params": p,
    }
    return t_ms, u_trace, meta


def measure_apd(
    t_ms: np.ndarray,
    u: np.ndarray,
    *,
    threshold: float = 0.5,
    refractory_ms: float = 50.0,
) -> dict[str, float | None]:
    """
    Estimate APD at 50% repolarization for the first complete action potential.
    """
    above = u >= threshold
    if not np.any(above):
        return {"apd_ms": None, "activation_ms": None, "peak_u": float(np.max(u))}

    onset_idx = int(np.flatnonzero(above)[0])
    peak_idx = int(onset_idx + np.argmax(u[onset_idx:]))
    peak_u = float(u[peak_idx])

    # Repolarization: first index after peak where u drops below threshold
    repol_candidates = np.where((t_ms > t_ms[peak_idx] + refractory_ms * 0.1) & ~above)[0]
    repol_idx = None
    for idx in repol_candidates:
        if idx > peak_idx and t_ms[idx] - t_ms[onset_idx] < refractory_ms * 4:
            repol_idx = int(idx)
            break

    if repol_idx is None:
        # fallback: last crossing below threshold after peak
        after = np.where((np.arange(len(u)) > peak_idx) & ~above)[0]
        if after.size == 0:
            return {"apd_ms": None, "activation_ms": float(t_ms[onset_idx]), "peak_u": peak_u}
        repol_idx = int(after[0])

    apd_ms = float(t_ms[repol_idx] - t_ms[onset_idx])
    return {
        "apd_ms": apd_ms,
        "activation_ms": float(t_ms[onset_idx]),
        "peak_u": peak_u,
    }


def parameter_sweep_tau_out(
    tau_out_values: tuple[float, ...] = (4.0, 6.0, 8.0, 10.0),
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """Sweep tau_out and return APD summary per value."""
    results = []
    for tau_out in tau_out_values:
        t, u, meta = simulate_ms_0d(params={"tau_out": tau_out}, **kwargs)
        apd = measure_apd(t, u)
        results.append({"tau_out": tau_out, **apd, **meta})
    return results
