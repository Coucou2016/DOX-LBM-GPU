"""Three-class tissue maps: healthy / border / dense fibrosis.

Villar-Valero defined a peri-fibrotic shell by 8-voxel morphological dilation
of the dense LGE mask (MRI 1.4 mm). In this 2D prototype the analog is
``border_width`` pixels (default 2–4).

Dense fibrosis may be near-block (high λ and/or very low D).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from cardiac_ms.constants import (
    BORDER_WIDTH_2D_DEFAULT,
    D_HEALTHY_MM2_PER_MS,
    LAMBDA_HEALTHY,
    TAU_CLOSE,
)


def fibrosis_mask(nx: int, ny: int, *, center: tuple[int, int], radius: int) -> np.ndarray:
    """Boolean disk (row/col grid) used as a dense-fibrosis core."""
    cx, cy = center
    yy, xx = np.ogrid[:ny, :nx]
    dist2 = (xx - cx) ** 2 + (yy - cy) ** 2
    return dist2 <= radius * radius

CLASS_HEALTHY = 0
CLASS_BORDER = 1
CLASS_DENSE = 2

CLASS_NAMES = {
    CLASS_HEALTHY: "healthy",
    CLASS_BORDER: "border",
    CLASS_DENSE: "dense",
}


def binary_dilate8(mask: np.ndarray, width: int) -> np.ndarray:
    """Morphological dilation, 8-connected, ``width`` iterations (pure numpy)."""
    out = np.asarray(mask, dtype=bool)
    if width <= 0:
        return out.copy()
    for _ in range(int(width)):
        padded = np.pad(out, 1, mode="constant", constant_values=False)
        out = (
            padded[1:-1, 1:-1]
            | padded[:-2, 1:-1]
            | padded[2:, 1:-1]
            | padded[1:-1, :-2]
            | padded[1:-1, 2:]
            | padded[:-2, :-2]
            | padded[:-2, 2:]
            | padded[2:, :-2]
            | padded[2:, 2:]
        )
    return out


@dataclass
class TissueMaps:
    """Nodal fields for monodomain + modified MS."""

    classes: np.ndarray  # int, ny x nx
    D: np.ndarray
    lam: np.ndarray
    tau_close: np.ndarray
    dense_mask: np.ndarray
    border_mask: np.ndarray
    conducting: np.ndarray | None = None

    def __post_init__(self) -> None:
        if self.conducting is None:
            self.conducting = np.ones(self.classes.shape, dtype=bool)

    @property
    def shape(self) -> tuple[int, int]:
        return tuple(self.classes.shape)  # type: ignore[return-value]


def assign_three_class(
    dense_mask: np.ndarray,
    *,
    border_width: int = BORDER_WIDTH_2D_DEFAULT,
    D_healthy: float = D_HEALTHY_MM2_PER_MS,
    D_border: float | None = None,
    D_dense: float | None = None,
    lam_healthy: float = LAMBDA_HEALTHY,
    lam_border: float = 0.1,
    lam_dense: float = 0.3,
    tau_close_healthy: float = TAU_CLOSE,
    tau_close_border: float | None = None,
    tau_close_dense: float | None = None,
    d_reduction_dense: float = 0.90,
    d_reduction_border: float = 0.50,
) -> TissueMaps:
    """
    Build D, λ, τ_close from a dense-fibrosis boolean mask.

    ``d_reduction_*`` is the fractional drop relative to healthy D
    (0.90 => D_dense = 0.10 * D_healthy) unless D_border/D_dense are given.
    """
    dense = np.asarray(dense_mask, dtype=bool)
    if D_dense is None:
        D_dense = D_healthy * (1.0 - d_reduction_dense)
    if D_border is None:
        D_border = D_healthy * (1.0 - d_reduction_border)
    if tau_close_border is None:
        tau_close_border = tau_close_healthy
    if tau_close_dense is None:
        tau_close_dense = tau_close_healthy

    dilated = binary_dilate8(dense, border_width)
    border = dilated & ~dense

    classes = np.full(dense.shape, CLASS_HEALTHY, dtype=np.int8)
    classes[border] = CLASS_BORDER
    classes[dense] = CLASS_DENSE

    D = np.full(dense.shape, float(D_healthy), dtype=np.float64)
    D[border] = float(D_border)
    D[dense] = float(D_dense)

    lam = np.full(dense.shape, float(lam_healthy), dtype=np.float64)
    lam[border] = float(lam_border)
    lam[dense] = float(lam_dense)

    tau_close = np.full(dense.shape, float(tau_close_healthy), dtype=np.float64)
    tau_close[border] = float(tau_close_border)
    tau_close[dense] = float(tau_close_dense)

    return TissueMaps(
        classes=classes,
        D=D,
        lam=lam,
        tau_close=tau_close,
        dense_mask=dense,
        border_mask=border,
        conducting=np.ones(dense.shape, dtype=bool),
    )


def disk_fibrosis_three_class(
    nx: int,
    ny: int,
    *,
    center: tuple[int, int] | None = None,
    radius: int | None = None,
    border_width: int = BORDER_WIDTH_2D_DEFAULT,
    **kwargs,
) -> TissueMaps:
    """Circular dense core (paper-like 2D analog of an LGE cluster) plus border."""
    if center is None:
        center = (nx // 2, ny // 2)
    if radius is None:
        radius = max(3, nx // 6)
    mask = fibrosis_mask(nx, ny, center=center, radius=radius)
    return assign_three_class(mask, border_width=border_width, **kwargs)


def ring_obstacle_maps(
    nx: int,
    ny: int,
    *,
    block_radius: int | None = None,
    D_healthy: float = D_HEALTHY_MM2_PER_MS,
    D_circuit: float | None = None,
    lam_healthy: float = LAMBDA_HEALTHY,
    tau_close: float = TAU_CLOSE,
) -> TissueMaps:
    """
    Central inexcitable disk; remaining tissue conducts (optionally slowed).

    Used as a 2D anatomical-reentry surrogate: path ~ π * diameter. The 2D
    sheet is much smaller than a pig LV, so ``D_circuit`` is often reduced
    so that lap time can exceed APD (see protocol tests / ASSUMPTIONS).
    """
    if block_radius is None:
        block_radius = max(6, min(nx, ny) // 5)
    dense = fibrosis_mask(nx, ny, center=(nx // 2, ny // 2), radius=block_radius)
    if D_circuit is None:
        D_circuit = D_healthy
    return assign_three_class(
        dense,
        border_width=0,
        D_healthy=D_circuit,
        D_dense=1e-12,
        lam_healthy=lam_healthy,
        lam_dense=0.3,
        tau_close_healthy=tau_close,
        tau_close_dense=tau_close,
        d_reduction_dense=1.0,
    )


def c_shape_block_mask(
    nx: int,
    ny: int,
    *,
    thickness: int = 4,
    gap: int = 6,
) -> np.ndarray:
    """C-shaped unexcitable barrier (opening on +x) for isthmus reentry tests."""
    mask = np.zeros((ny, nx), dtype=bool)
    cy, cx = ny // 2, nx // 2
    r_out = max(8, min(nx, ny) // 3)
    r_in = max(2, r_out - thickness)
    yy, xx = np.ogrid[:ny, :nx]
    dist2 = (xx - cx) ** 2 + (yy - cy) ** 2
    ring = (dist2 <= r_out * r_out) & (dist2 >= r_in * r_in)
    # Open a gap on the right
    opening = (xx >= cx) & (np.abs(yy - cy) <= gap)
    mask[ring & ~opening] = True
    return mask


def annulus_fibrosis_maps(
    nx: int,
    ny: int,
    dx: float,
    *,
    r_in_mm: float = 14.0,
    r_out_mm: float = 20.0,
    D_healthy: float = D_HEALTHY_MM2_PER_MS,
    d_reduction: float = 0.90,
    lam_healthy: float = LAMBDA_HEALTHY,
    lam_ring: float = LAMBDA_HEALTHY,
    tau_close_healthy: float = TAU_CLOSE,
    tau_close_ring: float | None = None,
) -> TissueMaps:
    """
    Pinned annular circuit: inexcitable hole + outer void, conducting ring.

    The ring is the scanned fibrotic substrate (λ_ring, D reduced). Healthy
    τ_close is kept unless ``tau_close_ring`` is set (APD heterogeneity only
    in the circuit, matching the paper's fibrotic APD scan — not a global
    τ_close=80 spiral).
    """
    from cardiac_ms.geometries import annulus_conducting_mask

    if tau_close_ring is None:
        tau_close_ring = tau_close_healthy
    cond = annulus_conducting_mask(nx, ny, dx, r_in_mm=r_in_mm, r_out_mm=r_out_mm)
    d_ring = float(D_healthy) * (1.0 - float(d_reduction))
    D = np.full((ny, nx), 1e-12, dtype=np.float64)
    D[cond] = d_ring
    lam = np.full((ny, nx), 0.3, dtype=np.float64)
    lam[cond] = float(lam_ring)
    tau = np.full((ny, nx), float(tau_close_healthy), dtype=np.float64)
    tau[cond] = float(tau_close_ring)
    classes = np.full((ny, nx), CLASS_DENSE, dtype=np.int8)
    classes[cond] = CLASS_BORDER
    return TissueMaps(
        classes=classes,
        D=D,
        lam=lam,
        tau_close=tau,
        dense_mask=~cond,
        border_mask=cond,
        conducting=cond,
    )
