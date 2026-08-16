"""Standard S1–S2 pacing and paper reentry classifier.

Paper protocol (Villar-Valero J Physiol 2025):
    S1 train: BCL = 400 ms, n_s1 = 3
    Extra-stimuli: shorter coupling intervals (e.g. 180–320 ms scan)
    Reentry (VA): sustained activation ≥ 1000 ms after the last stimulus,
    or ≥ 1 full extra cycle at a probe after the captured last beat.

Negative control: no fibrosis → Non-VA under the default protocol.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np

from cardiac_ms.constants import (
    ACTIVATION_THRESHOLD,
    BCL_S1_MS,
    LAMBDA_HEALTHY,
    N_S1_DEFAULT,
    REENTRY_SUSTAIN_MS,
    STIM_DURATION_MS,
    STIM_U_PROTOCOL,
)
from cardiac_ms.metrics import summarize_lat_cv
from cardiac_ms.ms_2d import simulate_mono2d


@dataclass
class Stimulus:
    t_start_ms: float
    t_end_ms: float
    region: tuple[slice, slice]
    stim_u: float = STIM_U_PROTOCOL


def classify_reentry(
    activation_persists_ms: float,
    threshold_ms: float = REENTRY_SUSTAIN_MS,
    n_extra_cycles: int = 0,
    extra_cycle_min: int = 1,
    n_probes_activated: int = 0,
    min_probes_for_circulation: int = 3,
    n_probes_relapped: int = 0,
    require_cycle: bool = True,
) -> str:
    """
    Return ``\"VA\"`` or ``\"Non-VA\"``.

    Default ``require_cycle=True``: persist≥1000 ms alone is **not** VA, and
    a single pass around the ring (each angular probe fires once after S2)
    is also not VA. Reentry needs a **second** excitation: ≥1 extra probe
    cycle **or** ≥3 sites with ≥2 post-stimulus upstrokes (``n_probes_relapped``).

    Set ``require_cycle=False`` to recover the paper persist≥1000 ms rule.
    """
    has_cycle = int(n_extra_cycles) >= int(extra_cycle_min) or int(
        n_probes_relapped
    ) >= int(min_probes_for_circulation)
    persist_ok = float(activation_persists_ms) >= float(threshold_ms)
    if require_cycle:
        return "VA" if has_cycle else "Non-VA"
    if persist_ok or has_cycle:
        return "VA"
    return "Non-VA"


def build_s1s2_stimuli(
    *,
    ny: int,
    nx: int,
    bcl_ms: float = BCL_S1_MS,
    n_s1: int = N_S1_DEFAULT,
    extra_cis_ms: Sequence[float] = (240.0,),
    stim_duration_ms: float = STIM_DURATION_MS,
    stim_u: float = STIM_U_PROTOCOL,
    s1_region: tuple[slice, slice] | None = None,
    s2_region: tuple[slice, slice] | None = None,
) -> list[Stimulus]:
    """
    S1 at 0, BCL, 2*BCL, … then extras whose coupling is relative to the
    previous beat (paper: S2=240, S3=200, S4=190 ms).
    """
    if s1_region is None:
        s1_region = (slice(0, max(2, ny // 6)), slice(0, max(3, nx // 5)))
    if s2_region is None:
        s2_region = s1_region

    stimuli: list[Stimulus] = []
    t = 0.0
    for _ in range(int(n_s1)):
        stimuli.append(Stimulus(t, t + stim_duration_ms, s1_region, stim_u))
        t += bcl_ms
    t_beat = (int(n_s1) - 1) * bcl_ms
    for ci in extra_cis_ms:
        t_beat = t_beat + float(ci)
        stimuli.append(Stimulus(t_beat, t_beat + stim_duration_ms, s2_region, stim_u))
    return stimuli


def last_stimulus_end_ms(stimuli: Sequence[Stimulus]) -> float:
    return max(s.t_end_ms for s in stimuli)


def protocol_t_end_ms(
    stimuli: Sequence[Stimulus],
    observe_ms: float = REENTRY_SUSTAIN_MS,
) -> float:
    return last_stimulus_end_ms(stimuli) + float(observe_ms)


def run_s1s2(
    *,
    nx: int = 48,
    ny: int = 48,
    dx: float = 0.5,
    dt: float | None = 0.1,
    n_s1: int = N_S1_DEFAULT,
    bcl_ms: float = BCL_S1_MS,
    extra_cis_ms: Sequence[float] = (240.0,),
    observe_ms: float = REENTRY_SUSTAIN_MS,
    reentry_threshold_ms: float = REENTRY_SUSTAIN_MS,
    fibrosis: bool = False,
    tissue=None,
    D_field: np.ndarray | None = None,
    lam=None,
    s2_cross_field: bool = False,
    stim_u: float = STIM_U_PROTOCOL,
    params: dict[str, float] | None = None,
    diffusion_mode: str = "auto",
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Run S1–S2 on the 2D monodomain and classify VA / Non-VA.

    Extra kwargs go to ``simulate_mono2d`` (e.g. ``tau_close_field``).
    """
    s1_region = kwargs.pop("s1_region", None)
    s2_region = kwargs.pop("s2_region", None)
    if s1_region is None:
        s1_region = (slice(0, max(2, ny // 6)), slice(0, max(3, nx // 5)))
    if s2_region is None:
        if s2_cross_field:
            s2_region = (slice(ny // 2, ny), slice(0, nx // 2))
        else:
            s2_region = s1_region

    stimuli = build_s1s2_stimuli(
        ny=ny,
        nx=nx,
        bcl_ms=bcl_ms,
        n_s1=n_s1,
        extra_cis_ms=extra_cis_ms,
        stim_u=stim_u,
        s1_region=s1_region,
        s2_region=s2_region,
    )
    t_end = protocol_t_end_ms(stimuli, observe_ms=observe_ms)
    probe = kwargs.pop("probe", (ny // 2, min(nx - 2, 3 * nx // 4)))
    extra_probes = kwargs.pop("extra_probes", None)

    _, u, h, meta = simulate_mono2d(
        nx=nx,
        ny=ny,
        n_steps=None,
        dt=dt,
        dx=dx,
        fibrosis=fibrosis if tissue is None else False,
        t_end_ms=t_end,
        stimuli=stimuli,
        tissue=tissue,
        D_field=D_field,
        lam=lam,
        track_reentry=True,
        probe=probe,
        extra_probes=extra_probes,
        snapshots=False,
        params=params,
        diffusion_mode=diffusion_mode,
        **kwargs,
    )

    persist = float(meta.get("activation_persists_ms") or 0.0)
    n_extra = int(meta.get("n_extra_cycles") or 0)
    n_probes = int(meta.get("n_probes_activated") or 0)
    extra_up = meta.get("extra_upstrokes") or []
    n_relap = int(meta.get("n_probes_relapped") or 0)
    if not n_relap and extra_up:
        n_relap = int(sum(1 for k in extra_up if int(k) >= 2))
    label = classify_reentry(
        persist,
        threshold_ms=reentry_threshold_ms,
        n_extra_cycles=n_extra,
        n_probes_activated=n_probes,
        n_probes_relapped=n_relap,
        require_cycle=True,
    )
    lat_stats = summarize_lat_cv(meta["activation_ms"], dx)

    return {
        "label": label,
        "activation_persists_ms": persist,
        "n_extra_cycles": n_extra,
        "n_probes_activated": n_probes,
        "n_probes_relapped": n_relap,
        "extra_upstrokes": list(extra_up),
        "n_upstrokes_post_stim": int(meta.get("n_upstrokes_post_stim") or 0),
        "excited_fraction": float(meta.get("excited_fraction") or 0.0),
        "last_stim_end_ms": float(meta.get("last_stim_end_ms") or last_stimulus_end_ms(stimuli)),
        "t_end_ms": t_end,
        "reentry_threshold_ms": reentry_threshold_ms,
        "u_max": float(meta.get("u_peak") or u.max()),
        "u_final_max": float(u.max()),
        "h_min": float(h.min()),
        "dt": meta["dt"],
        "cfl_r": meta["cfl_r"],
        "elapsed_s": meta["elapsed_s"],
        "nx": nx,
        "ny": ny,
        "dx": dx,
        "n_s1": n_s1,
        "extra_cis_ms": list(extra_cis_ms),
        "fibrosis": bool(fibrosis) or tissue is not None,
        **lat_stats,
        "meta": meta,
        "u": u,
        "h": h,
    }


def run_reentry_positive_control(
    *,
    nx: int = 64,
    ny: int = 64,
    dx: float = 0.5,
    observe_ms: float = 1000.0,
) -> dict[str, Any]:
    """
    Cross-field S1–S2 spiral on a 64² sheet.

    Paper healthy wavelength (CV×APD ≈ 0.7 mm/ms × 250 ms ≈ 175 mm) does not
    fit in a 32 mm disk, so this control shortens ``tau_close`` to 80 ms
    (2D surrogate APD) while keeping calibrated D and λ=0.01. That is a
    numerical accommodation, not a Villar-Valero parameter.
    """
    from cardiac_ms.ms_modified import get_modified_parameters

    params = get_modified_parameters()
    params["tau_close"] = 80.0
    return run_s1s2(
        nx=nx,
        ny=ny,
        dx=dx,
        n_s1=1,
        extra_cis_ms=(210.0,),
        observe_ms=observe_ms,
        fibrosis=False,
        s2_cross_field=True,
        dt=0.1,
        params=params,
        s1_region=(slice(0, ny), slice(0, 3)),
        probe=(ny // 4, 3 * nx // 4),
    )


def run_annulus_s1s2(
    *,
    nx: int = 64,
    ny: int | None = None,
    dx: float = 0.75,
    r_in_mm: float = 14.0,
    r_out_mm: float = 20.0,
    d_reduction: float = 0.90,
    lam_ring: float = LAMBDA_HEALTHY,
    n_s1: int = N_S1_DEFAULT,
    extra_cis_ms: Sequence[float] = (240.0, 200.0, 190.0),
    observe_ms: float = REENTRY_SUSTAIN_MS,
    tau_close_ring: float | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    S1–S2 on the pinned annulus (calibrated healthy τ_close unless overridden).

    Default extras match the paper train (S2/S3/S4 = 240/200/190 ms). A single
    premature at CI≈220 ms only drives one lap then a long plateau at D↓90%
    (persist≥1000 without re-excitation); the multi-extra train induces true
    re-excitation cycles under ``require_cycle=True`` without shortening τ_close.
    """
    from cardiac_ms.constants import LAMBDA_HEALTHY, TAU_CLOSE
    from cardiac_ms.geometries import annulus_mean_path_mm, annulus_stim_regions, annulus_wavelength_report
    from cardiac_ms.tissue_classes import annulus_fibrosis_maps

    if ny is None:
        ny = nx
    tissue = annulus_fibrosis_maps(
        nx,
        ny,
        dx,
        r_in_mm=r_in_mm,
        r_out_mm=r_out_mm,
        d_reduction=d_reduction,
        lam_ring=lam_ring,
        tau_close_ring=tau_close_ring,
    )
    s1, s2, probe, probes = annulus_stim_regions(tissue.conducting)
    report = annulus_wavelength_report(r_in_mm=r_in_mm, r_out_mm=r_out_mm, nx=nx, dx=dx)
    r = run_s1s2(
        nx=nx,
        ny=ny,
        dx=dx,
        n_s1=n_s1,
        extra_cis_ms=extra_cis_ms,
        observe_ms=observe_ms,
        tissue=tissue,
        s1_region=s1,
        s2_region=s2,
        probe=probe,
        extra_probes=probes,
        dt=0.1,
        **kwargs,
    )
    r["geometry"] = "annulus"
    r["path_mm"] = annulus_mean_path_mm(r_in_mm, r_out_mm)
    r["wavelength_note"] = report.note
    r["r_in_mm"] = r_in_mm
    r["r_out_mm"] = r_out_mm
    r["d_reduction"] = d_reduction
    r["lam_ring"] = lam_ring
    r["tau_close_ring"] = tau_close_ring if tau_close_ring is not None else TAU_CLOSE
    return r


def scan_coupling_intervals(
    ci_values_ms: Sequence[float],
    **run_kwargs: Any,
) -> dict[str, Any]:
    """Sweep S2 coupling intervals (single extra-stimulus) and report VW / critical CI."""
    from cardiac_ms.metrics import critical_coupling_interval, vulnerable_window_width

    rows = []
    labels = []
    for ci in ci_values_ms:
        r = run_s1s2(extra_cis_ms=(float(ci),), **run_kwargs)
        labels.append(r["label"])
        rows.append(
            {
                "ci_ms": float(ci),
                "label": r["label"],
                "activation_persists_ms": r["activation_persists_ms"],
                "n_extra_cycles": r["n_extra_cycles"],
                "elapsed_s": r["elapsed_s"],
            }
        )
    cis = [float(c) for c in ci_values_ms]
    return {
        "rows": rows,
        "critical_ci_ms": critical_coupling_interval(cis, labels),
        "vulnerable_window_ms": vulnerable_window_width(cis, labels),
        "n_va": sum(1 for lab in labels if lab == "VA"),
    }
