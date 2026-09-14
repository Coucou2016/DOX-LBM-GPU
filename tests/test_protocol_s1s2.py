"""S1–S2 protocol, reentry classifier, and paper-aligned controls."""

from cardiac_ms.protocol_s1s2 import (
    classify_reentry,
    run_annulus_s1s2,
    run_reentry_positive_control,
    run_s1s2,
    triple_va_labels,
)
from cardiac_ms.tissue_classes import disk_fibrosis_three_class


def test_classify_reentry_paper_threshold():
    # VA_paper: persist ONLY — cycle evidence must NOT flip paper label
    assert classify_reentry(999.0, threshold_ms=1000, require_cycle=False) == "Non-VA"
    assert classify_reentry(1000.0, threshold_ms=1000, require_cycle=False) == "VA"
    assert (
        classify_reentry(
            999.0, threshold_ms=1000, require_cycle=False, n_extra_cycles=1
        )
        == "Non-VA"
    )
    # VA_recurrence (default require_cycle=True)
    assert classify_reentry(200.0, threshold_ms=1000, n_extra_cycles=1) == "VA"
    assert classify_reentry(200.0, threshold_ms=1000, n_extra_cycles=0) == "Non-VA"
    # Plateau persist without a second upstroke is not VA under recurrence
    assert classify_reentry(1000.0, threshold_ms=1000, n_extra_cycles=0) == "Non-VA"
    assert (
        classify_reentry(
            1000.0, threshold_ms=1000, n_extra_cycles=0, n_probes_relapped=3
        )
        == "VA"
    )
    # One lap around the ring (3 sites fire once) is not reentry
    assert (
        classify_reentry(
            400.0, threshold_ms=1000, n_extra_cycles=0, n_probes_activated=3
        )
        == "Non-VA"
    )


def test_triple_va_endpoints():
    """P0 triple endpoints: paper persist-only; strict = persist AND cycle."""
    # persist=999, cycle=1 → VA_paper=Non-VA
    d0 = triple_va_labels(999.0, n_extra_cycles=1, n_probes_relapped=0)
    assert d0["VA_paper"] == "Non-VA"
    assert d0["VA_recurrence"] == "VA"
    assert d0["VA_strict"] == "Non-VA"

    # persist=1000, cycle=0 → VA_paper=VA ; VA_strict=Non-VA
    d1 = triple_va_labels(1000.0, n_extra_cycles=0, n_probes_relapped=0)
    assert d1["VA_paper"] == "VA"
    assert d1["VA_recurrence"] == "Non-VA"
    assert d1["VA_strict"] == "Non-VA"
    assert d1["VA_cycle"] == "Non-VA"  # alias
    assert d1["label"] == "Non-VA"

    # persist=1000, cycle>=1 → VA_strict=VA
    d2 = triple_va_labels(1000.0, n_extra_cycles=1, n_probes_relapped=0)
    assert d2["VA_paper"] == "VA"
    assert d2["VA_recurrence"] == "VA"
    assert d2["VA_strict"] == "VA"


def test_control_d_reduction_exactly_zero():
    """CONTROL d_reduction=0.0 must not be coerced via truthiness to 0.30."""
    from cardiac_ms.phenotypes import get_phenotype

    ph = get_phenotype("CONTROL")
    assert float(ph["d_reduction"]) == 0.0
    # Bug was: ``float(ph["d_reduction"]) if ph["d_reduction"] else 0.30``
    buggy = float(ph["d_reduction"]) if ph["d_reduction"] else 0.30
    assert buggy == 0.30  # documents the falsy-zero trap
    fixed = float(ph.get("d_reduction", 0.0))
    assert fixed == 0.0
    assert tuple(ph["extra_cis_ms"]) == ()
    assert ph["targets"]["apd_ms_target"] == 309.0


def test_dox_protocols_and_shorter_apd_targets():
    from cardiac_ms.phenotypes import PROTOCOL_EXTRAS, LITERATURE_TARGETS

    assert PROTOCOL_EXTRAS["CONTROL"] == ()
    assert PROTOCOL_EXTRAS["DOX1"] == (240.0, 200.0, 190.0)
    assert PROTOCOL_EXTRAS["DOX2"] == (250.0, 250.0, 250.0, 250.0)
    assert LITERATURE_TARGETS["DOX1"]["apd_ms_target"] < LITERATURE_TARGETS["CONTROL"]["apd_ms_target"]
    assert LITERATURE_TARGETS["DOX2"]["apd_ms_target"] < LITERATURE_TARGETS["CONTROL"]["apd_ms_target"]
    assert LITERATURE_TARGETS["DOX1"]["apd_fibrosis_ms_target"] == 276.0
    assert LITERATURE_TARGETS["DOX2"]["apd_fibrosis_ms_target"] == 184.0
    assert LITERATURE_TARGETS["DOX2"]["cv_mm_per_ms_target"] == 0.4389


def test_no_fibrosis_is_non_va():
    """Negative control: homogeneous sheet, default extras → Non-VA."""
    r = run_s1s2(
        nx=40,
        ny=40,
        dx=0.5,
        n_s1=1,
        extra_cis_ms=(240.0,),
        observe_ms=450.0,
        reentry_threshold_ms=1000.0,
        fibrosis=False,
        dt=0.1,
    )
    assert r["label"] == "Non-VA", r
    assert r["activation_persists_ms"] < 1000.0
    assert r["n_extra_cycles"] == 0
    assert r["u_max"] > 0.5


def test_annulus_single_premature_plateau_is_non_va():
    """
    D↓90% with a single premature (CI≈220 ms): one lap then long plateau.

    Persist can exceed 1000 ms while extra=0 / relapped<3 → Non-VA under
    require_cycle. Documents coexistence of elevated residual voltage with
    Non-VA (plateau ≠ reentry).
    """
    r = run_annulus_s1s2(
        nx=64,
        dx=0.75,
        d_reduction=0.90,
        lam_ring=0.01,
        n_s1=1,
        extra_cis_ms=(220.0,),
        observe_ms=1000.0,
    )
    assert r["label"] == "Non-VA", r
    assert r["n_extra_cycles"] == 0
    assert r.get("n_probes_relapped", 0) < 3
    assert r["u_max"] > 0.5


def test_annulus_slow_circuit_is_va():
    """
    Pinned annulus at D↓90%, λ=0.01, τ_close=150 → true re-excitation (VA).

    Paper multi-extra train (240/200/190) induces extra≥1 or relapped≥3.
    Local elevated u at observe end may coexist with VA (not a counterexample).
    """
    r = run_annulus_s1s2(
        nx=64,
        dx=0.75,
        d_reduction=0.90,
        lam_ring=0.01,
        n_s1=3,
        extra_cis_ms=(240.0, 200.0, 190.0),
        observe_ms=1000.0,
    )
    assert r["n_extra_cycles"] >= 1 or r.get("n_probes_relapped", 0) >= 3, r
    assert r["label"] == "VA", r
    assert r["u_max"] > 0.5
    assert r["tau_close_ring"] == 150.0


def test_annulus_fast_or_blocked_is_non_va():
    """D↓30% under the same paper train: one lap, no second excitation → Non-VA."""
    r = run_annulus_s1s2(
        nx=64,
        dx=0.75,
        d_reduction=0.30,
        lam_ring=0.01,
        n_s1=3,
        extra_cis_ms=(240.0, 200.0, 190.0),
        observe_ms=1000.0,
        reentry_threshold_ms=1000.0,
    )
    assert r["label"] == "Non-VA", r
    assert r["n_extra_cycles"] == 0
    assert r.get("n_probes_relapped", 0) < 3
    assert r["u_max"] > 0.5


def test_paper_disc_small_domain_and_spiral_surrogate():
    """
    Paper-like fibrotic disk on 20 mm sheet: usually Non-VA (wavelength too long).
    Cross-field S2 with shortened tau_close=80 ms on 64² remains a numerical surrogate.
    """
    tissue = disk_fibrosis_three_class(
        40, 40, border_width=2, d_reduction_dense=0.90, lam_dense=0.3
    )
    disk = run_s1s2(
        nx=40,
        ny=40,
        dx=0.5,
        n_s1=1,
        extra_cis_ms=(220.0, 180.0),
        observe_ms=500.0,
        reentry_threshold_ms=1000.0,
        tissue=tissue,
        s2_cross_field=True,
        dt=0.1,
    )
    spiral = run_reentry_positive_control(nx=64, ny=64, observe_ms=900.0)
    assert spiral["label"] == "VA", spiral
    assert spiral["n_extra_cycles"] >= 1
    assert disk["label"] in ("VA", "Non-VA")
