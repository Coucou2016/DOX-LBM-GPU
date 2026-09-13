"""
2D phase singularity / rotor tip detection (auxiliary metric).

Phase is estimated from the instantaneous (u, h) state in the MS plane, or
optionally from a Hilbert transform of a scalar field. Topological charge is
computed on plaquettes via wrapped phase circulation (Gray et al.–style tip
tracking in 2D).

Limitations (see docs/ASSUMPTIONS.md): this is a 2D tip / charge detector for
protocol audit, not 3D filament tracking and not a clinical rotor diagnosis.
"""

from __future__ import annotations

from typing import Any

import numpy as np


def phase_from_uh(
    u: np.ndarray,
    h: np.ndarray,
    *,
    u_center: float = 0.5,
    h_center: float = 0.5,
) -> np.ndarray:
    """
    Instantaneous phase φ = atan2(h - h0, u - u0) on the MS state plane.

    Returns values in (-π, π].
    """
    u = np.asarray(u, dtype=np.float64)
    h = np.asarray(h, dtype=np.float64)
    return np.arctan2(h - float(h_center), u - float(u_center))


def phase_from_hilbert(signal: np.ndarray, axis: int = 0) -> np.ndarray:
    """
    Analytic-signal phase via FFT Hilbert (no SciPy dependency).

    ``signal`` is typically a time series at each spatial node, shape (T, ...)
    or (..., T) with ``axis`` selecting time. Returns phase in (-π, π].
    """
    x = np.asarray(signal, dtype=np.float64)
    n = x.shape[axis]
    X = np.fft.fft(x, n=n, axis=axis)
    h = np.zeros(n, dtype=np.float64)
    if n % 2 == 0:
        h[0] = h[n // 2] = 1.0
        h[1 : n // 2] = 2.0
    else:
        h[0] = 1.0
        h[1 : (n + 1) // 2] = 2.0
    shape = [1] * x.ndim
    shape[axis] = n
    X *= h.reshape(shape)
    analytic = np.fft.ifft(X, n=n, axis=axis)
    return np.angle(analytic)


def _wrap_to_pi(dphi: np.ndarray) -> np.ndarray:
    return (dphi + np.pi) % (2.0 * np.pi) - np.pi


def topological_charge_map(phase: np.ndarray) -> np.ndarray:
    """
    Integer topological charge on each 2×2 plaquette (ny-1, nx-1).

    Charge ≈ round(∑ Δφ / 2π) with wrapped edge differences circulating
    around the plaquette (CCW: TL→TR→BR→BL→TL).
    """
    ph = np.asarray(phase, dtype=np.float64)
    if ph.ndim != 2 or min(ph.shape) < 2:
        raise ValueError("phase must be a 2D array with shape >= (2, 2)")
    # Edges of each plaquette (bottom-left origin at [i, j])
    d_top = _wrap_to_pi(ph[:-1, 1:] - ph[:-1, :-1])  # TL → TR
    d_right = _wrap_to_pi(ph[1:, 1:] - ph[:-1, 1:])  # TR → BR
    d_bottom = _wrap_to_pi(ph[1:, :-1] - ph[1:, 1:])  # BR → BL
    d_left = _wrap_to_pi(ph[:-1, :-1] - ph[1:, :-1])  # BL → TL
    circ = d_top + d_right + d_bottom + d_left
    return np.rint(circ / (2.0 * np.pi)).astype(np.int32)


def singularity_locations(
    phase: np.ndarray,
    *,
    mask: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Return (rows, cols, charges) of non-zero plaquette charges.

    Indices refer to the top-left corner of each charged plaquette.
    If ``mask`` is given (tissue conducting), a plaquette is kept only when
    all four corners are True.
    """
    charge = topological_charge_map(phase)
    if mask is not None:
        m = np.asarray(mask, dtype=bool)
        ok = m[:-1, :-1] & m[:-1, 1:] & m[1:, :-1] & m[1:, 1:]
        charge = np.where(ok, charge, 0)
    ys, xs = np.nonzero(charge != 0)
    return ys.astype(np.int32), xs.astype(np.int32), charge[ys, xs]


def detect_phase_singularities(
    u: np.ndarray,
    h: np.ndarray | None = None,
    *,
    mask: np.ndarray | None = None,
    method: str = "uh",
    u_center: float = 0.5,
    h_center: float = 0.5,
    min_abs_charge: int = 1,
) -> dict[str, Any]:
    """
    Detect 2D phase singularities from a snapshot (or last Hilbert slice).

    Parameters
    ----------
    u :
        Voltage field, or (T, ny, nx) stack if ``method='hilbert'``.
    h :
        Gate field (required for ``method='uh'``).
    method :
        ``'uh'`` (default) or ``'hilbert'`` (analytic phase of ``u`` over time;
        uses the last time frame's phase map for tip locations).
    """
    method = str(method).lower()
    if method == "uh":
        if h is None:
            raise ValueError("h is required for method='uh'")
        phase = phase_from_uh(u, h, u_center=u_center, h_center=h_center)
    elif method == "hilbert":
        u_arr = np.asarray(u, dtype=np.float64)
        if u_arr.ndim != 3:
            raise ValueError("Hilbert method expects u shaped (T, ny, nx)")
        ph_t = phase_from_hilbert(u_arr, axis=0)
        phase = ph_t[-1]
    else:
        raise ValueError(f"Unknown method {method!r}; use 'uh' or 'hilbert'")

    ys, xs, charges = singularity_locations(phase, mask=mask)
    keep = np.abs(charges) >= int(min_abs_charge)
    ys, xs, charges = ys[keep], xs[keep], charges[keep]
    n = int(ys.size)
    return {
        "n_singularities": n,
        "rotor_detected": n > 0,
        "rows": ys,
        "cols": xs,
        "charges": charges,
        "phase": phase,
        "method": method,
    }


def synthesize_rotating_phase(
    ny: int = 48,
    nx: int = 48,
    *,
    center: tuple[float, float] | None = None,
    charge: int = 1,
) -> np.ndarray:
    """Synthetic spiral phase φ = charge * atan2(y-yc, x-xc) for unit tests."""
    if center is None:
        center = ((ny - 1) / 2.0, (nx - 1) / 2.0)
    yy, xx = np.mgrid[0:ny, 0:nx]
    return float(charge) * np.arctan2(yy - center[0], xx - center[1])


def synthesize_uh_from_phase(
    phase: np.ndarray,
    *,
    radius: float = 0.35,
    u_center: float = 0.5,
    h_center: float = 0.5,
) -> tuple[np.ndarray, np.ndarray]:
    """Map a phase field to (u, h) on a circle in state space (test helper)."""
    u = u_center + radius * np.cos(phase)
    h = h_center + radius * np.sin(phase)
    return u, h
