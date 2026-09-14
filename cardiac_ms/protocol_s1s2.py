"""Standard S1–S2 pacing and paper reentry classifier.

Paper protocol (Villar-Valero J Physiol 2026):
    S1 train: BCL = 400 ms, n_s1 = 3
    Extra-stimuli: shorter coupling intervals (phenotype-specific)
    Triple VA endpoints (see ``triple_va_labels``):
      VA_paper      — persist ≥ 1000 ms ONLY (never OR cycle)
      VA_recurrence — confirmed extra cycle / ordered circulation
      VA_strict     — persist ≥ 1000 AND recurrent circulation

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
    STIM_CURRENT,
    STIM_DURATION_MS,
    STIM_VOLTAGE,
)
from cardiac_ms.metrics import summarize_lat_cv
from cardiac_ms.ms_2d import simulate_mono2d
from cardiac_ms.phase_singularity import detect_phase_singularities


@dataclass
class Stimulus:
    t_start_ms: float
    t_end_ms: float
    region: tuple[slice, slice]
    stim_u: float = STIM_VOLTAGE
    stim_amp: float | None = None

    def __post_init__(self) -> None:
        if self.stim_amp is None:
            self.stim_amp = float(STIM_CURRENT if self.stim_u == STIM_VOLTAGE else self.stim_u)


def has_recurrent_circulation(
    n_extra_cycles: int = 0,
    *,
    extra_cycle_min: int = 1,
    n_probes_relapped: int = 0,
    min_probes_for_circulation: int = 3,
) -> bool:
    """True if probe evidence shows a second excitation (not a single pass)."""
    return int(n_extra_cycles) >= int(extra_cycle_min) or int(
        n_probes_relapped
    ) >= int(min_probes_for_circulation)


def classify_reentry(
    activation_persists_ms: float,
    threshold_ms: float = REENTRY_SUSTAIN_MS,
    n_extra_cycles: int = 0,
    extra_cycle_min: int = 1,
    n_probes_activated: int = 0,
    min_probes_for_circulation: int = 3,
    n_probes_relapped: int = 0,
    require_cycle: bool = True,
    *,
    mode: str | None = None,
    n_ordered_laps: int | None = None,
    min_ordered_laps_strict: int = 1,
) -> str:
    """
    Return ``\"VA\"`` or ``\"Non-VA\"``.

    Modes (prefer ``triple_va_labels`` for all three endpoints):

    - ``require_cycle=True`` / ``mode=\"recurrence\"`` (``VA_recurrence``):
      persist alone is **not** VA; need ≥1 extra probe cycle **or** ≥3 sites
      with ≥2 post-stimulus upstrokes (``n_probes_relapped``).
      A single ordered lap is **not** recurrence.
    - ``require_cycle=False`` / ``mode=\"paper\"`` (``VA_paper``):
      persist ≥ threshold **only** — never OR cycle evidence.
    - ``mode=\"strict\"`` (``VA_strict``): persist ≥ threshold **and** recurrence;
      when ``n_ordered_laps`` is provided, also require ≥``min_ordered_laps_strict``
      ordered laps (default 1 = conjunction only; set 2 for ordered hardening).
    """
    _ = n_probes_activated
    has_cycle = has_recurrent_circulation(
        n_extra_cycles,
        extra_cycle_min=extra_cycle_min,
        n_probes_relapped=n_probes_relapped,
        min_probes_for_circulation=min_probes_for_circulation,
    )
    persist_ok = float(activation_persists_ms) >= float(threshold_ms)
    if mode is None:
        mode = "recurrence" if require_cycle else "paper"
    mode = str(mode).lower().strip()
    if mode in ("paper", "va_paper", "persist"):
        return "VA" if persist_ok else "Non-VA"
    if mode in ("strict", "va_strict"):
        laps_ok = True
        if n_ordered_laps is not None:
            laps_ok = int(n_ordered_laps) >= int(min_ordered_laps_strict)
        return "VA" if (persist_ok and has_cycle and laps_ok) else "Non-VA"
    # recurrence / VA_cycle alias
    return "VA" if has_cycle else "Non-VA"


def triple_va_labels(
    activation_persists_ms: float,
    *,
    threshold_ms: float = REENTRY_SUSTAIN_MS,
    n_extra_cycles: int = 0,
    extra_cycle_min: int = 1,
    n_probes_activated: int = 0,
    min_probes_for_circulation: int = 3,
    n_probes_relapped: int = 0,
    n_ordered_laps: int | None = None,
    min_ordered_laps_strict: int = 1,
) -> dict[str, str | bool]:
    """
    Report three VA endpoints (Round-2 major revision).

    - ``VA_paper``: persist ≥ 1000 ms ONLY (Villar-Valero); never OR cycle.
    - ``VA_recurrence``: confirmed extra cycle (extra≥1 or relapped≥3).
    - ``VA_strict``: persist ≥ 1000 **and** recurrence.
      Optional ordered-lap hardening via ``n_ordered_laps`` / ``min_ordered_laps_strict``.

    ``label`` / ``VA_cycle`` alias ``VA_recurrence`` for scaffold default.
    """
    kw = dict(
        activation_persists_ms=activation_persists_ms,
        threshold_ms=threshold_ms,
        n_extra_cycles=n_extra_cycles,
        extra_cycle_min=extra_cycle_min,
        n_probes_activated=n_probes_activated,
        min_probes_for_circulation=min_probes_for_circulation,
        n_probes_relapped=n_probes_relapped,
        n_ordered_laps=n_ordered_laps,
        min_ordered_laps_strict=min_ordered_laps_strict,
    )
    label_paper = classify_reentry(**kw, mode="paper")
    label_rec = classify_reentry(**kw, mode="recurrence")
    label_strict = classify_reentry(**kw, mode="strict")
    return {
        "VA_paper": label_paper,
        "VA_recurrence": label_rec,
        "VA_strict": label_strict,
        "VA_cycle": label_rec,  # backward-compat alias
        "label": label_rec,
        "va_paper": label_paper == "VA",
        "va_recurrence": label_rec == "VA",
        "va_strict": label_strict == "VA",
        "va_cycle": label_rec == "VA",
    }


def dual_va_labels(
    activation_persists_ms: float,
    *,
    threshold_ms: float = REENTRY_SUSTAIN_MS,
    n_extra_cycles: int = 0,
    extra_cycle_min: int = 1,
    n_probes_activated: int = 0,
    min_probes_for_circulation: int = 3,
    n_probes_relapped: int = 0,
    n_ordered_laps: int | None = None,
    min_ordered_laps_strict: int = 1,
) -> dict[str, str | bool]:
    """Deprecated name: returns ``triple_va_labels`` (includes VA_strict)."""
    return triple_va_labels(
        activation_persists_ms,
        threshold_ms=threshold_ms,
        n_extra_cycles=n_extra_cycles,
        extra_cycle_min=extra_cycle_min,
        n_probes_activated=n_probes_activated,
        min_probes_for_circulation=min_probes_for_circulation,
        n_probes_relapped=n_probes_relapped,
        n_ordered_laps=n_ordered_laps,
        min_ordered_laps_strict=min_ordered_laps_strict,
    )


def build_s1s2_stimuli(
    *,
    ny: int,
    nx: int,
    bcl_ms: float = BCL_S1_MS,
    n_s1: int = N_S1_DEFAULT,
    extra_cis_ms: Sequence[float] = (240.0,),
    stim_duration_ms: float = STIM_DURATION_MS,
    stim_u: float = STIM_VOLTAGE,
    stim_amp: float | None = None,
    s1_region: tuple[slice, slice] | None = None,
    s2_region: tuple[slice, slice] | None = None,
) -> list[Stimulus]:
    """
    S1 at 0, BCL, 2*BCL, … then extras whose coupling is relative to the
    previous beat (DOX1: S2=240, S3=200, S4=190 ms). Empty ``extra_cis_ms``
    yields S1-only (CONTROL: no ectopic extras).
    """
    if s1_region is None:
        s1_region = (slice(0, max(2, ny // 6)), slice(0, max(3, nx // 5)))
    if s2_region is None:
        s2_region = s1_region
    amp = float(STIM_CURRENT if stim_amp is None else stim_amp)

    stimuli: list[Stimulus] = []
    t = 0.0
    for _ in range(int(n_s1)):
        stimuli.append(
            Stimulus(t, t + stim_duration_ms, s1_region, stim_u=stim_u, stim_amp=amp)
        )
        t += bcl_ms
    t_beat = (int(n_s1) - 1) * bcl_ms if int(n_s1) > 0 else 0.0
    for ci in extra_cis_ms:
        t_beat = t_beat + float(ci)
        stimuli.append(
            Stimulus(
                t_beat, t_beat + stim_duration_ms, s2_region, stim_u=stim_u, stim_amp=amp
            )
        )
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
    stim_u: float = STIM_VOLTAGE,
    stim_amp: float | None = None,
    params: dict[str, float] | None = None,
    diffusion_mode: str = "auto",
    stimulus_mode: str = "current",
    detect_singularities: bool = True,
    min_ordered_laps_strict: int = 1,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Run S1–S2 on the 2D monodomain and classify VA / Non-VA.

    Default ``stimulus_mode=\"current\"`` (J_stim = ``STIM_CURRENT`` during windows).
    Use ``voltage_clamp`` (``STIM_VOLTAGE``) for legacy regression.
    Extra kwargs go to ``simulate_mono2d``.

    When ``detect_singularities=True`` (default), appends auxiliary 2D tip metrics
    ``n_singularities`` / ``rotor_detected`` from the final (u, h) snapshot
    (not 3D filament tracking; see ``docs/ASSUMPTIONS.md``).

    ``min_ordered_laps_strict``: if >1, ``VA_strict`` additionally requires that
    many ordered angular laps (optional hardening; default 1 = P0 conjunction only).
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
        stim_amp=stim_amp,
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
        stimulus_mode=stimulus_mode,
        **kwargs,
    )

    persist = float(meta.get("activation_persists_ms") or 0.0)
    n_extra = int(meta.get("n_extra_cycles") or 0)
    n_probes = int(meta.get("n_probes_activated") or 0)
    extra_up = meta.get("extra_upstrokes") or []
    n_relap = int(meta.get("n_probes_relapped") or 0)
    if not n_relap and extra_up:
        n_relap = int(sum(1 for k in extra_up if int(k) >= 2))
    n_ordered = int(meta.get("n_ordered_laps") or meta.get("n_rotations_est") or 0)
    circ = meta.get("circulation") or {}
    dual = triple_va_labels(
        persist,
        threshold_ms=reentry_threshold_ms,
        n_extra_cycles=n_extra,
        n_probes_activated=n_probes,
        n_probes_relapped=n_relap,
        n_ordered_laps=(
            n_ordered if (int(min_ordered_laps_strict) > 1 and n_ordered > 0) else None
        ),
        min_ordered_laps_strict=min_ordered_laps_strict,
    )
    label = str(dual["label"])
    lat_stats = summarize_lat_cv(meta["activation_ms"], dx)

    n_sing = 0
    rotor = False
    sing_meta: dict[str, Any] | None = None
    if detect_singularities:
        mask = None
        if tissue is not None and getattr(tissue, "conducting", None) is not None:
            mask = np.asarray(tissue.conducting, dtype=bool)
        sing_meta = detect_phase_singularities(u, h, mask=mask, method="uh")
        n_sing = int(sing_meta["n_singularities"])
        rotor = bool(sing_meta["rotor_detected"])

    return {
        "label": label,
        "VA_paper": dual["VA_paper"],
        "VA_recurrence": dual["VA_recurrence"],
        "VA_strict": dual["VA_strict"],
        "VA_cycle": dual["VA_cycle"],
        "va_paper": bool(dual["va_paper"]),
        "va_recurrence": bool(dual["va_recurrence"]),
        "va_strict": bool(dual["va_strict"]),
        "va_cycle": bool(dual["va_cycle"]),
        "activation_persists_ms": persist,
        "n_extra_cycles": n_extra,
        "n_probes_activated": n_probes,
        "n_probes_relapped": n_relap,
        "n_ordered_laps": n_ordered,
        "circulation_direction": circ.get("direction"),
        "lap_period_ms": circ.get("lap_period_ms"),
        "extra_upstrokes": list(extra_up),
        "n_upstrokes_post_stim": int(meta.get("n_upstrokes_post_stim") or 0),
        "excited_fraction": float(meta.get("excited_fraction") or 0.0),
        "last_stim_end_ms": float(meta.get("last_stim_end_ms") or last_stimulus_end_ms(stimuli)),
        "t_end_ms": t_end,
        "reentry_threshold_ms": reentry_threshold_ms,
        "stimulus_mode": stimulus_mode,
        "n_singularities": n_sing,
        "rotor_detected": rotor,
        "singularity": sing_meta,
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
