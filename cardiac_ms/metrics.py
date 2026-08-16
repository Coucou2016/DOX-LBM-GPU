"""Activation-time and conduction metrics for the 2D monodomain prototype."""

from __future__ import annotations

from typing import Any, Sequence

import numpy as np

from cardiac_ms.ms_2d import estimate_cv_from_activation


def lat_map(activation_ms: np.ndarray) -> np.ndarray:
    """Copy of first-activation times (ms); NaN where never activated."""
    return np.asarray(activation_ms, dtype=np.float64).copy()


def two_point_cv(
    activation_ms: np.ndarray,
    *,
    p0: tuple[int, int],
    p1: tuple[int, int],
    dx: float,
    max_delay_ms: float = 500.0,
) -> float | None:
    """CV (mm/ms) between two nodes from the LAT map."""
    return estimate_cv_from_activation(
        activation_ms, p0=p0, p1=p1, dx=dx, max_delay_ms=max_delay_ms
    )


def local_cv_map(
    activation_ms: np.ndarray,
    dx: float,
    *,
    min_cv: float = 0.05,
    max_cv: float = 3.0,
) -> np.ndarray:
    """
    Local CV ≈ 1 / |∇T| from the LAT map (mm/ms).

    Invalid / extreme values are NaN. Spatial heterogeneity uses this field.
    """
    t = np.asarray(activation_ms, dtype=np.float64)
    gy, gx = np.gradient(t, dx)
    slowness = np.sqrt(gx * gx + gy * gy)
    with np.errstate(divide="ignore", invalid="ignore"):
        cv = 1.0 / slowness
    valid = np.isfinite(t) & np.isfinite(cv) & (cv >= min_cv) & (cv <= max_cv)
    return np.where(valid, cv, np.nan)


def cv_heterogeneity(cv_local: np.ndarray) -> dict[str, float | None]:
    """std/mean of finite local-CV samples (dimensionless)."""
    v = np.asarray(cv_local, dtype=np.float64)
    v = v[np.isfinite(v)]
    if v.size < 4:
        return {"cv_mean": None, "cv_std": None, "cv_std_over_mean": None, "n": float(v.size)}
    mean = float(v.mean())
    std = float(v.std())
    ratio = float(std / mean) if mean > 1e-12 else None
    return {"cv_mean": mean, "cv_std": std, "cv_std_over_mean": ratio, "n": float(v.size)}


def critical_coupling_interval(
    ci_ms: Sequence[float],
    labels: Sequence[str],
) -> float | None:
    """Smallest S2 coupling interval (ms) classified as VA; None if never inducible."""
    va = [float(c) for c, lab in zip(ci_ms, labels) if lab == "VA"]
    return min(va) if va else None


def vulnerable_window_width(
    ci_ms: Sequence[float],
    labels: Sequence[str],
) -> float:
    """Width (ms) of the CI range that induced VA; 0 if none."""
    va = [float(c) for c, lab in zip(ci_ms, labels) if lab == "VA"]
    if not va:
        return 0.0
    return float(max(va) - min(va))


def summarize_lat_cv(
    activation_ms: np.ndarray,
    dx: float,
    *,
    p0: tuple[int, int] | None = None,
    p1: tuple[int, int] | None = None,
) -> dict[str, Any]:
    ny, nx = activation_ms.shape
    if p0 is None:
        p0 = (ny // 2, max(1, nx // 8))
    if p1 is None:
        p1 = (ny // 2, min(nx - 2, nx // 2))
    cv2 = two_point_cv(activation_ms, p0=p0, p1=p1, dx=dx)
    loc = local_cv_map(activation_ms, dx)
    het = cv_heterogeneity(loc)
    n_act = int(np.isfinite(activation_ms).sum())
    return {
        "cv_two_point_mm_per_ms": cv2,
        "n_activated": n_act,
        "activated_fraction": n_act / float(activation_ms.size),
        **het,
    }
