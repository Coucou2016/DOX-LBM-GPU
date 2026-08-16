"""2D monodomain prototype: explicit diffusion + Mitchell-Schaeffer (CPU)."""

from __future__ import annotations

import time
import warnings
from typing import Any

import numpy as np

from cardiac_ms.constants import (
    ACTIVATION_THRESHOLD,
    D_HEALTHY_MM2_PER_MS,
    IONIC_DT_MAX_MS,
    LAMBDA_HEALTHY,
    U_MAX,
)
from cardiac_ms.ms_modified import get_modified_parameters, ionic_rhs_modified
from mitchell_schaeffer.ops import calc_J_in, calc_J_out, calc_rhs, get_parameters

# Explicit 5-point Laplacian stability: dt <= dx^2 / (4 * D_max)
_CFL_FACTOR_2D = 4.0


def suggest_dt_cfl(dx: float, D_max: float, *, safety: float = 0.45) -> float:
    """
    Suggest a stable explicit time step (ms) for 2D diffusion with D_max.

    Uses dt <= safety * dx^2 / (4 * D_max).
    """
    if dx <= 0 or D_max <= 0:
        raise ValueError(f"dx and D_max must be positive, got dx={dx}, D_max={D_max}")
    return safety * (dx * dx) / (_CFL_FACTOR_2D * D_max)


def check_cfl(dt: float, dx: float, D_max: float, *, safety: float = 0.5) -> float:
    """
    Return diffusion CFL number r = D_max * dt / (dx^2 / 4).

    Raises ValueError when r > safety (unstable explicit step).
    """
    r = D_max * dt / (dx * dx / _CFL_FACTOR_2D)
    if r > safety:
        dt_suggest = suggest_dt_cfl(dx, D_max, safety=safety * 0.9)
        raise ValueError(
            f"CFL unstable: r={r:.3f} > {safety}. "
            f"Reduce dt (suggest dt <= {dt_suggest:.4f} ms) or increase dx."
        )
    return r


def diffusion_div_D_grad_neumann(
    field: np.ndarray,
    D: np.ndarray,
    dx: float,
    out: np.ndarray | None = None,
) -> np.ndarray:
    """
    Conservative div(D grad u) for scalar nodal D (mm^2/ms).

    Face conductivities use arithmetic averages; domain edges use zero flux (Neumann).
    When D is spatially constant this matches D * laplacian_neumann(u).
    """
    if out is None:
        out = np.empty_like(field)
    inv_dx = 1.0 / dx
    u = field
    # East/north face D and fluxes (interior faces only)
    D_e = 0.5 * (D[:, 1:] + D[:, :-1])
    D_n = 0.5 * (D[1:, :] + D[:-1, :])
    flux_x = D_e * (u[:, 1:] - u[:, :-1]) * inv_dx
    flux_y = D_n * (u[1:, :] - u[:-1, :]) * inv_dx

    out.fill(0.0)
    out[:, 1:-1] += (flux_x[:, 1:] - flux_x[:, :-1]) * inv_dx
    out[1:-1, :] += (flux_y[1:, :] - flux_y[:-1, :]) * inv_dx
    # Boundaries: one-sided flux divergence (zero exterior flux)
    out[:, 0] += flux_x[:, 0] * inv_dx
    out[:, -1] += -flux_x[:, -1] * inv_dx
    out[0, :] += flux_y[0, :] * inv_dx
    out[-1, :] += -flux_y[-1, :] * inv_dx
    return out


def laplacian_neumann(field: np.ndarray, dx: float, out: np.ndarray | None = None) -> np.ndarray:
    """5-point Laplacian with zero-flux (Neumann) boundaries."""
    if out is None:
        out = np.empty_like(field)
    else:
        out.fill(0.0)
    inv_dx2 = 1.0 / (dx * dx)
    out[1:-1, 1:-1] = (
        field[:-2, 1:-1]
        + field[2:, 1:-1]
        + field[1:-1, :-2]
        + field[1:-1, 2:]
        - 4.0 * field[1:-1, 1:-1]
    ) * inv_dx2
    out[0, 1:-1] = (field[1, 1:-1] - field[0, 1:-1]) * inv_dx2
    out[-1, 1:-1] = (field[-2, 1:-1] - field[-1, 1:-1]) * inv_dx2
    out[1:-1, 0] = (field[1:-1, 1] - field[1:-1, 0]) * inv_dx2
    out[1:-1, -1] = (field[1:-1, -2] - field[1:-1, -1]) * inv_dx2
    return out


def laplacian_anisotropic(
    field: np.ndarray,
    dx: float,
    Dxx: np.ndarray,
    Dyy: np.ndarray,
    Dxy: np.ndarray | None = None,
    out: np.ndarray | None = None,
) -> np.ndarray:
    """
    Face-centered ``div(D·∇u)`` with fiber tensor (mm²/ms).

    East/north face fluxes use arithmetic-averaged ``Dxx/Dyy/Dxy`` and include
    cross-derivative terms via averaged transverse differences. Domain edges
    use zero exterior flux (Neumann-like), matching ``diffusion_div_D_grad_neumann``.

    When ``Dxy≈0`` and ``Dxx≈Dyy≈D`` (scalar), this agrees with the isotropic
    conservative operator on the interior. Still a 2D prototype—not a claim of
    paper 3D anisotropic LBM accuracy.
    """
    if Dxy is None:
        Dxy = np.zeros_like(field)
    if out is None:
        out = np.empty_like(field)
    inv_dx = 1.0 / dx
    u = np.asarray(field, dtype=np.float64)
    ny, nx = u.shape

    # East faces (ny, nx-1): Fx = Dxx du/dx + Dxy du/dy
    Dxx_e = 0.5 * (Dxx[:, 1:] + Dxx[:, :-1])
    Dxy_e = 0.5 * (Dxy[:, 1:] + Dxy[:, :-1])
    dudx_e = (u[:, 1:] - u[:, :-1]) * inv_dx
    dudy_e = np.zeros((ny, nx - 1), dtype=np.float64)
    if ny >= 3:
        dudy_e[1:-1, :] = 0.25 * inv_dx * (
            (u[2:, 1:] - u[:-2, 1:]) + (u[2:, :-1] - u[:-2, :-1])
        )
    dudy_e[0, :] = 0.5 * inv_dx * (
        (u[min(1, ny - 1), 1:] - u[0, 1:]) + (u[min(1, ny - 1), :-1] - u[0, :-1])
    )
    dudy_e[-1, :] = 0.5 * inv_dx * (
        (u[-1, 1:] - u[max(0, ny - 2), 1:])
        + (u[-1, :-1] - u[max(0, ny - 2), :-1])
    )
    flux_x = Dxx_e * dudx_e + Dxy_e * dudy_e

    # North faces (ny-1, nx): Fy = Dxy du/dx + Dyy du/dy
    Dyy_n = 0.5 * (Dyy[1:, :] + Dyy[:-1, :])
    Dxy_n = 0.5 * (Dxy[1:, :] + Dxy[:-1, :])
    dudy_n = (u[1:, :] - u[:-1, :]) * inv_dx
    dudx_n = np.zeros((ny - 1, nx), dtype=np.float64)
    if nx >= 3:
        dudx_n[:, 1:-1] = 0.25 * inv_dx * (
            (u[1:, 2:] - u[1:, :-2]) + (u[:-1, 2:] - u[:-1, :-2])
        )
    dudx_n[:, 0] = 0.5 * inv_dx * (
        (u[1:, min(1, nx - 1)] - u[1:, 0]) + (u[:-1, min(1, nx - 1)] - u[:-1, 0])
    )
    dudx_n[:, -1] = 0.5 * inv_dx * (
        (u[1:, -1] - u[1:, max(0, nx - 2)])
        + (u[:-1, -1] - u[:-1, max(0, nx - 2)])
    )
    flux_y = Dxy_n * dudx_n + Dyy_n * dudy_n

    out.fill(0.0)
    out[:, 1:-1] += (flux_x[:, 1:] - flux_x[:, :-1]) * inv_dx
    out[1:-1, :] += (flux_y[1:, :] - flux_y[:-1, :]) * inv_dx
    out[:, 0] += flux_x[:, 0] * inv_dx
    out[:, -1] += -flux_x[:, -1] * inv_dx
    out[0, :] += flux_y[0, :] * inv_dx
    out[-1, :] += -flux_y[-1, :] * inv_dx
    return out


def fiber_conductivity_tensor(
    ny: int,
    nx: int,
    *,
    D_long: float,
    D_trans: float,
    angle_rad: float | np.ndarray = 0.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Build nodal Dxx, Dyy, Dxy from fiber angle (radians) and longitudinal/transverse D.
    """
    c = np.cos(angle_rad)
    s = np.sin(angle_rad)
    if np.ndim(c) == 0:
        c = np.full((ny, nx), float(c))
        s = np.full((ny, nx), float(s))
    d_par = D_long - D_trans
    Dxx = D_trans + d_par * c * c
    Dyy = D_trans + d_par * s * s
    Dxy = d_par * c * s
    return Dxx, Dyy, Dxy


def ionic_rhs_vectorized(
    u: np.ndarray, h: np.ndarray, p: dict[str, float]
) -> tuple[np.ndarray, np.ndarray]:
    """Vectorized MS du/dt and dh/dt (same formulas as mitchell_schaeffer.ops)."""
    tau_in = p["tau_in"]
    tau_out = p["tau_out"]
    J_in = calc_J_in(u, h, tau_in)  # type: ignore[arg-type]
    J_out = calc_J_out(u, tau_out)  # type: ignore[arg-type]
    rhs = calc_rhs(J_in, J_out)  # type: ignore[arg-type]
    dh = np.where(
        u < p["u_gate"],
        (1.0 - h) / p["tau_open"],
        -h / p["tau_close"],
    )
    return rhs, dh


def fibrosis_mask(nx: int, ny: int, *, center: tuple[int, int], radius: int) -> np.ndarray:
    cx, cy = center
    yy, xx = np.ogrid[:ny, :nx]
    dist2 = (xx - cx) ** 2 + (yy - cy) ** 2
    return dist2 <= radius * radius


def estimate_cv_from_activation(
    activation_ms: np.ndarray,
    *,
    p0: tuple[int, int],
    p1: tuple[int, int],
    dx: float,
    max_delay_ms: float = 500.0,
) -> float | None:
    """
    Estimate conduction velocity (mm/ms) between two grid nodes from activation times.

    p0, p1 are (row, col). Returns None if either site never activated.
    """
    y0, x0 = p0
    y1, x1 = p1
    t0 = float(activation_ms[y0, x0])
    t1 = float(activation_ms[y1, x1])
    if not np.isfinite(t0) or not np.isfinite(t1):
        return None
    dt_act = abs(t1 - t0)
    if dt_act < 1e-6 or dt_act > max_delay_ms:
        return None
    dist = abs(x1 - x0) * dx if x0 != x1 else abs(y1 - y0) * dx
    if dist < 1e-9:
        return None
    return dist / dt_act


def _stim_time(stim: Any) -> tuple[float, float, tuple[slice, slice], float]:
    """Duck-type Stimulus or dict -> (t0, t1, region, stim_u)."""
    if isinstance(stim, dict):
        return (
            float(stim["t_start_ms"]),
            float(stim["t_end_ms"]),
            stim["region"],
            float(stim.get("stim_u", 0.8)),
        )
    return (
        float(stim.t_start_ms),
        float(stim.t_end_ms),
        stim.region,
        float(getattr(stim, "stim_u", 0.8)),
    )


def simulate_mono2d(
    nx: int = 64,
    ny: int = 64,
    n_steps: int | None = 4000,
    dt: float | None = 0.1,
    dx: float = 0.5,
    D_normal: float | None = None,
    D_fibrosis: float | None = None,
    *,
    fibrosis: bool = True,
    enforce_cfl: bool = True,
    activation_threshold: float = ACTIVATION_THRESHOLD,
    s1_region: tuple[slice, slice] | None = None,
    s1_window: tuple[int, int] = (40, 45),
    s2_coupling_ms: float = 180.0,
    s2_window: tuple[int, int] | None = None,
    s2_region: tuple[slice, slice] | None = None,
    stim_u: float = 0.25,
    params: dict[str, float] | None = None,
    anisotropy: bool = False,
    fiber_angle_rad: float = 0.0,
    D_long: float | None = None,
    D_trans: float | None = None,
    D_field: np.ndarray | None = None,
    lam: float | np.ndarray | None = None,
    lam_fibrosis: float | None = None,
    tau_close_field: np.ndarray | None = None,
    tissue: Any | None = None,
    stimuli: list | None = None,
    t_end_ms: float | None = None,
    use_modified_ms: bool = True,
    track_reentry: bool = False,
    probe: tuple[int, int] | None = None,
    extra_probes: list[tuple[int, int]] | None = None,
    snapshots: bool = True,
    diffusion_mode: str = "auto",
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    """
    2D monodomain: du/dt = div(D ∇u) + ionic_rhs; gate h with explicit Euler.

    Default ionic model is modified MS (λ). Set ``use_modified_ms=False`` for
    the classic finitewave RHS (λ=0 equivalent).

    If dt is None, picks suggest_dt_cfl from D_max. Set enforce_cfl=False to skip check.
    ``diffusion_mode``: ``auto`` (div if D varies else D*laplace), ``div``, or
    ``laplace`` (D⊙∇²u, non-conservative when D varies).
    """
    if D_normal is None:
        D_normal = float(D_HEALTHY_MM2_PER_MS)
    if D_fibrosis is None:
        D_fibrosis = float(D_normal) * 0.10

    if use_modified_ms:
        p = get_modified_parameters()
    else:
        p = dict(get_parameters())
    if params:
        p.update(params)

    u = np.zeros((ny, nx), dtype=np.float64)
    h = np.ones((ny, nx), dtype=np.float64)

    mask = np.zeros((ny, nx), dtype=bool)
    conducting = np.ones((ny, nx), dtype=bool)
    if tissue is not None:
        D = np.asarray(tissue.D, dtype=np.float64).copy()
        lam_field: float | np.ndarray = np.asarray(tissue.lam, dtype=np.float64)
        tau_close_field = np.asarray(tissue.tau_close, dtype=np.float64)
        mask = np.asarray(tissue.dense_mask, dtype=bool)
        if getattr(tissue, "conducting", None) is not None:
            conducting = np.asarray(tissue.conducting, dtype=bool)
        fibrosis = True
    elif D_field is not None:
        D = np.asarray(D_field, dtype=np.float64).copy()
        lam_field = LAMBDA_HEALTHY if lam is None else lam
    else:
        D = np.full((ny, nx), float(D_normal), dtype=np.float64)
        if fibrosis:
            mask = fibrosis_mask(nx, ny, center=(nx // 2, ny // 2), radius=max(2, nx // 8))
            D[mask] = float(D_fibrosis)
        if lam is None:
            lam_field = np.full((ny, nx), float(p.get("lam", LAMBDA_HEALTHY)), dtype=np.float64)
            if fibrosis and lam_fibrosis is not None:
                lam_field[mask] = float(lam_fibrosis)
        else:
            lam_field = lam

    D_max = float(max(float(D[conducting].max()) if conducting.any() else float(D.max()), 1e-18))
    dt_clamped = False
    dt_stable = suggest_dt_cfl(dx, D_max, safety=0.5)
    if dt is None:
        dt = min(suggest_dt_cfl(dx, D_max), IONIC_DT_MAX_MS)
        dt_clamped = True
    dt = float(dt)
    if enforce_cfl and dt > dt_stable:
        warnings.warn(
            f"dt={dt:.4f} ms exceeds CFL limit {dt_stable:.4f} ms; clamping for stability.",
            stacklevel=2,
        )
        dt = dt_stable
        dt_clamped = True
    if dt > IONIC_DT_MAX_MS * 1.5:
        warnings.warn(
            f"dt={dt:.4f} ms is coarse vs tau_in=0.3 ms; upstroke / CV may be inaccurate.",
            stacklevel=2,
        )

    cfl_r = D_max * dt / (dx * dx / _CFL_FACTOR_2D)
    if cfl_r > 0.51:
        warnings.warn(f"CFL margin low: r={cfl_r:.3f}", stacklevel=2)

    if n_steps is None:
        if t_end_ms is None:
            raise ValueError("Provide n_steps or t_end_ms")
        n_steps = int(np.ceil(float(t_end_ms) / dt))
    n_steps = int(n_steps)

    Dxx = Dyy = Dxy = None
    if anisotropy:
        d_long = D_long if D_long is not None else D_normal
        d_trans = D_trans if D_trans is not None else D_normal * 0.25
        Dxx, Dyy, Dxy = fiber_conductivity_tensor(
            ny, nx, D_long=d_long, D_trans=d_trans, angle_rad=fiber_angle_rad
        )
        if fibrosis:
            Dxx = np.where(mask, D_fibrosis if tissue is None else D, Dxx)
            Dyy = np.where(mask, D_fibrosis if tissue is None else D, Dyy)
            Dxy = np.where(mask, 0.0, Dxy)

    parsed_stim: list[tuple[float, float, tuple[slice, slice], float]] = []
    if stimuli:
        parsed_stim = [_stim_time(s) for s in stimuli]
    else:
        if s1_region is None:
            s1_region = (slice(0, ny // 6), slice(0, nx // 4))
        if s2_window is None:
            s2_start = int(s2_coupling_ms / dt)
            s2_window = (s2_start, s2_start + 5)
        if s2_region is None:
            s2_region = (slice(0, ny // 6), slice(nx // 4, nx // 2))

    last_stim_end_ms = 0.0
    if parsed_stim:
        last_stim_end_ms = max(s[1] for s in parsed_stim)
    else:
        last_stim_end_ms = max(s1_window[1], s2_window[1]) * dt  # type: ignore[index]

    if probe is None:
        probe = (ny // 2, min(nx - 2, 3 * nx // 4))
    py, px = probe
    extra = list(extra_probes) if extra_probes else []
    extra_was = [False] * len(extra)
    extra_upstrokes = np.zeros(len(extra), dtype=np.int32)

    d_uniform = bool(np.allclose(D, D[0, 0]))
    use_div = diffusion_mode == "div" or (
        diffusion_mode == "auto" and (fibrosis or not d_uniform)
    )
    use_laplace_scaled = diffusion_mode == "laplace" or (
        diffusion_mode == "auto" and not use_div
    )

    activation_ms = np.full((ny, nx), np.nan, dtype=np.float64)
    lap_u = np.zeros_like(u)
    t0 = time.perf_counter()
    snap_list: list[tuple[int, np.ndarray]] = []
    last_active_ms = 0.0
    n_upstrokes_post = 0
    probe_was_above = False
    u_peak = 0.0
    post_stim_steps = 0
    active_post_steps = 0
    excited_frac_post_sum = 0.0

    for step in range(n_steps):
        t_now = step * dt
        if parsed_stim:
            for t0s, t1s, region, su in parsed_stim:
                if t0s <= t_now < t1s:
                    sl_y, sl_x = region
                    u[sl_y, sl_x] = su
        else:
            if s1_window[0] <= step < s1_window[1]:
                sl_y, sl_x = s1_region  # type: ignore[misc]
                u[sl_y, sl_x] = stim_u
            if s2_window[0] <= step < s2_window[1]:  # type: ignore[index]
                sl_y, sl_x = s2_region  # type: ignore[misc]
                u[sl_y, sl_x] = stim_u

        if not conducting.all():
            u[~conducting] = 0.0

        if anisotropy and Dxx is not None:
            diff_u = laplacian_anisotropic(u, dx, Dxx, Dyy, Dxy, out=lap_u)  # type: ignore[arg-type]
        elif use_div:
            diff_u = diffusion_div_D_grad_neumann(u, D, dx, out=lap_u)
        elif use_laplace_scaled:
            diff_u = laplacian_neumann(u, dx, out=lap_u)
            diff_u *= D
        else:
            diff_u = laplacian_neumann(u, dx, out=lap_u)
            diff_u *= D_normal

        if use_modified_ms:
            rhs, dh = ionic_rhs_modified(
                u, h, p, lam=lam_field, tau_close=tau_close_field
            )
        else:
            rhs, dh = ionic_rhs_vectorized(u, h, p)
        u = np.clip(u + dt * (diff_u + rhs), 0.0, 1.2)
        h = np.clip(h + dt * dh, 0.0, 1.0)
        if not conducting.all():
            u[~conducting] = 0.0
            h[~conducting] = 1.0
        umax_now = float(u.max())
        if umax_now > u_peak:
            u_peak = umax_now

        t_step = (step + 1) * dt
        newly = np.isnan(activation_ms) & (u >= activation_threshold)
        if newly.any():
            activation_ms[newly] = t_step

        if track_reentry:
            active_frac = (
                float((u[conducting] >= activation_threshold).mean())
                if conducting.any()
                else float(u.max() >= activation_threshold)
            )
            if active_frac >= 0.02:
                last_active_ms = t_step
            if t_step > last_stim_end_ms:
                post_stim_steps += 1
                excited_frac_post_sum += active_frac
                if active_frac >= 0.02:
                    active_post_steps += 1
                above = bool(u[py, px] >= activation_threshold)
                if above and not probe_was_above:
                    n_upstrokes_post += 1
                probe_was_above = above
                for i, (qy, qx) in enumerate(extra):
                    a = bool(u[int(qy), int(qx)] >= activation_threshold)
                    if a and not extra_was[i]:
                        extra_upstrokes[i] += 1
                    extra_was[i] = a

        if snapshots and step in (n_steps // 4, n_steps // 2, n_steps - 1):
            snap_list.append((step, u.copy()))

    elapsed = time.perf_counter() - t0
    t_ms = np.arange(n_steps, dtype=np.float64) * dt

    cv_probe_y = ny // 2
    x_near = max(1, nx // 8)
    x_far = min(nx - 2, nx // 2)
    cv_mm_per_ms = estimate_cv_from_activation(
        activation_ms,
        p0=(cv_probe_y, x_near),
        p1=(cv_probe_y, x_far),
        dx=dx,
    )

    persist = max(0.0, last_active_ms - last_stim_end_ms) if track_reentry else None
    n_extra = max(0, n_upstrokes_post - 1) if track_reentry else None
    n_probes_activated = int((extra_upstrokes >= 1).sum()) if extra else 0
    n_rotations_est = int(extra_upstrokes.min()) if extra_upstrokes.size else (
        max(0, n_upstrokes_post - 1) if track_reentry else 0
    )
    activity_duty_cycle = (
        float(active_post_steps) / float(post_stim_steps) if post_stim_steps else 0.0
    )
    mean_excited_fraction_post = (
        float(excited_frac_post_sum) / float(post_stim_steps) if post_stim_steps else 0.0
    )
    excited_fraction = (
        float((u[conducting] >= activation_threshold).mean())
        if conducting.any()
        else float(u.max() >= activation_threshold)
    )

    lam_min = float(np.min(lam_field)) if np.ndim(lam_field) else float(lam_field)
    lam_max = float(np.max(lam_field)) if np.ndim(lam_field) else float(lam_field)

    meta = {
        "elapsed_s": elapsed,
        "ms_per_step": elapsed / n_steps * 1000.0,
        "nx": nx,
        "ny": ny,
        "dt": dt,
        "dt_clamped": dt_clamped,
        "dx": dx,
        "cfl_r": float(cfl_r),
        "fibrosis": fibrosis,
        "anisotropy": anisotropy,
        "snapshots": snap_list,
        "D_min": float(D.min()),
        "D_max": float(D.max()),
        "lam_min": lam_min,
        "lam_max": lam_max,
        "u_max_used": U_MAX,
        "use_modified_ms": use_modified_ms,
        "diffusion_mode": diffusion_mode,
        "activation_ms": activation_ms,
        "cv_mm_per_ms": cv_mm_per_ms,
        "u_peak": u_peak,
        "last_stim_end_ms": float(last_stim_end_ms),
        "activation_persists_ms": persist,
        "n_upstrokes_post_stim": n_upstrokes_post if track_reentry else None,
        "n_extra_cycles": n_extra,
        "n_probes_activated": n_probes_activated if track_reentry else None,
        "n_probes_relapped": int((extra_upstrokes >= 2).sum()) if extra else 0,
        "extra_upstrokes": extra_upstrokes.tolist() if track_reentry else None,
        "n_rotations_est": n_rotations_est if track_reentry else None,
        "activity_duty_cycle": activity_duty_cycle if track_reentry else None,
        "mean_excited_fraction_post": (
            mean_excited_fraction_post if track_reentry else None
        ),
        "excited_fraction": excited_fraction,
        "probe": probe,
        "extra_probes": extra,
    }
    return t_ms, u, h, meta
