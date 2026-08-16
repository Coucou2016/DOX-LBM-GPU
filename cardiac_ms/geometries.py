"""2D tissue geometries and wavelength bookkeeping for inducibility studies.

Units: mm, ms. Wavelength λ_wave ≈ CV × APD.

Healthy paper-scale: CV=0.70 mm/ms, APD≈250 ms → λ_wave≈175 mm.
A 48² × 0.5 mm disc (24 mm) cannot host that rotor; it remains a documented
negative. The default inducibility geometry is a **pinned annulus** whose
mean path (~100 mm) sits between λ(D↓30%) and λ(D↓90%) so the same S1–S2
protocol can produce both Non-VA (fast circuit) and VA (slow circuit) at
calibrated healthy τ_close.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from cardiac_ms.constants import (
    CV_TARGET_MM_PER_MS,
    TAU_CLOSE,
)

# APD90 analog for default MS (measured ~250–260 ms at τ_close=150).
APD_HEALTHY_MS = 250.0


def wavelength_mm(cv_mm_per_ms: float = CV_TARGET_MM_PER_MS, apd_ms: float = APD_HEALTHY_MS) -> float:
    """λ_wave ≈ CV × APD (mm)."""
    return float(cv_mm_per_ms) * float(apd_ms)


def min_pinned_path_mm(cv_mm_per_ms: float = CV_TARGET_MM_PER_MS, apd_ms: float = APD_HEALTHY_MS) -> float:
    """Shortest anatomical circuit that can beat the tail at this CV/APD."""
    return wavelength_mm(cv_mm_per_ms, apd_ms)


def annulus_mean_path_mm(r_in_mm: float, r_out_mm: float) -> float:
    """Mean circumference π (R_in + R_out) = 2π R_mean."""
    return float(np.pi * (r_in_mm + r_out_mm))


def cv_for_reentry(path_mm: float, apd_ms: float = APD_HEALTHY_MS) -> float:
    """Maximum CV (mm/ms) at which lap time ≥ APD."""
    if apd_ms <= 0:
        return float("inf")
    return float(path_mm) / float(apd_ms)


def expected_cv_from_d_reduction(
    d_reduction: float,
    cv_healthy: float = CV_TARGET_MM_PER_MS,
) -> float:
    """Reaction–diffusion scaling CV ∝ √D; remaining D fraction = 1 - reduction."""
    frac = max(1e-9, 1.0 - float(d_reduction))
    return float(cv_healthy) * float(np.sqrt(frac))


@dataclass(frozen=True)
class WavelengthReport:
    cv_healthy: float
    apd_ms: float
    lambda_healthy_mm: float
    r_in_mm: float
    r_out_mm: float
    path_mm: float
    cv_reentry_max: float
    domain_mm: float
    note: str


def annulus_wavelength_report(
    *,
    r_in_mm: float,
    r_out_mm: float,
    nx: int,
    dx: float,
    cv_healthy: float = CV_TARGET_MM_PER_MS,
    apd_ms: float = APD_HEALTHY_MS,
) -> WavelengthReport:
    path = annulus_mean_path_mm(r_in_mm, r_out_mm)
    lam = wavelength_mm(cv_healthy, apd_ms)
    return WavelengthReport(
        cv_healthy=cv_healthy,
        apd_ms=apd_ms,
        lambda_healthy_mm=lam,
        r_in_mm=r_in_mm,
        r_out_mm=r_out_mm,
        path_mm=path,
        cv_reentry_max=cv_for_reentry(path, apd_ms),
        domain_mm=nx * dx,
        note=(
            f"Healthy lambda_wave={lam:.1f} mm vs path={path:.1f} mm "
            f"(need CV < {cv_for_reentry(path, apd_ms):.2f} mm/ms to reenter). "
            f"Paper disc 24 mm << {lam:.0f} mm."
        ),
    )


def radial_distance_mm(nx: int, ny: int, dx: float, center: tuple[float, float] | None = None) -> np.ndarray:
    """Distance from centre in mm for each node (ny, nx)."""
    if center is None:
        center = ((nx - 1) * 0.5 * dx, (ny - 1) * 0.5 * dx)
    cx, cy = center
    yy, xx = np.ogrid[:ny, :nx]
    x_mm = xx * dx
    y_mm = yy * dx
    return np.sqrt((x_mm - cx) ** 2 + (y_mm - cy) ** 2)


def annulus_conducting_mask(
    nx: int,
    ny: int,
    dx: float,
    *,
    r_in_mm: float,
    r_out_mm: float,
) -> np.ndarray:
    """True on the myocardial ring; False in the hole and outside the outer wall."""
    r = radial_distance_mm(nx, ny, dx)
    return (r >= r_in_mm) & (r <= r_out_mm)


def disc_conducting_mask(nx: int, ny: int, dx: float, *, radius_mm: float | None = None) -> np.ndarray:
    """Filled disc of conducting tissue (paper-like 2D LGE cluster host)."""
    if radius_mm is None:
        radius_mm = 0.45 * min(nx, ny) * dx
    r = radial_distance_mm(nx, ny, dx)
    return r <= radius_mm


def obstacle_mask_mm(
    nx: int,
    ny: int,
    dx: float,
    *,
    radius_mm: float,
) -> np.ndarray:
    """Central circular obstacle (inexitable core) in mm."""
    r = radial_distance_mm(nx, ny, dx)
    return r <= radius_mm


def default_annulus_spec(nx: int = 64, dx: float = 0.75) -> dict[str, float | int]:
    """
    Default pinned annulus sized so path ≈ 107 mm:

    - Healthy / D↓30% (CV≈0.59–0.70): lap < APD → Non-VA
    - D↓90% (CV≈0.22): lap > APD → VA possible
    """
    r_in_mm = 14.0
    r_out_mm = 20.0
    return {
        "nx": nx,
        "ny": nx,
        "dx": dx,
        "r_in_mm": r_in_mm,
        "r_out_mm": r_out_mm,
        "path_mm": annulus_mean_path_mm(r_in_mm, r_out_mm),
        "domain_mm": nx * dx,
        "tau_close": TAU_CLOSE,
    }


def _compact_patch(
    y: int, x: int, ny: int, nx: int, *, half: int = 2
) -> tuple[slice, slice]:
    return (
        slice(max(0, y - half), min(ny, y + half + 1)),
        slice(max(0, x - half), min(nx, x + half + 1)),
    )


def annulus_angular_probes(conducting: np.ndarray, n: int = 4) -> list[tuple[int, int]]:
    """``n`` sites around the ring (angles equally spaced) for circulation checks."""
    ys, xs = np.where(conducting)
    if ys.size == 0:
        raise ValueError("conducting mask is empty")
    ny, nx = conducting.shape
    cy, cx = 0.5 * (ny - 1), 0.5 * (nx - 1)
    ang = np.arctan2(ys.astype(np.float64) - cy, xs.astype(np.float64) - cx)
    probes: list[tuple[int, int]] = []
    for k in range(int(n)):
        target = -np.pi + 2.0 * np.pi * k / float(n)
        delta = np.abs((ang - target + np.pi) % (2.0 * np.pi) - np.pi)
        j = int(np.argmin(delta))
        probes.append((int(ys[j]), int(xs[j])))
    return probes


def annulus_stim_regions(
    conducting: np.ndarray,
) -> tuple[tuple[slice, slice], tuple[slice, slice], tuple[int, int], list[tuple[int, int]]]:
    """
    Compact leftmost S1, same-site premature S2, opposite probe, 4 angular probes.

    A large chord stimulus can hold a long arc depolarized (persist≥1000 ms
    with zero extra upstrokes). Premature S2 at the S1 site is the classic
    ring protocol for unidirectional block.
    """
    ys, xs = np.where(conducting)
    if ys.size == 0:
        raise ValueError("conducting mask is empty")
    ny, nx = conducting.shape
    i_left = int(np.argmin(xs))
    y_s, x_s = int(ys[i_left]), int(xs[i_left])
    s1 = _compact_patch(y_s, x_s, ny, nx, half=2)
    s2 = s1
    probes = annulus_angular_probes(conducting, n=4)
    probe = probes[2] if len(probes) >= 3 else probes[0]
    return s1, s2, probe, probes
