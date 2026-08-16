"""Wavelength bookkeeping and annulus masks."""

import numpy as np

from cardiac_ms.geometries import (
    annulus_conducting_mask,
    annulus_mean_path_mm,
    annulus_stim_regions,
    cv_for_reentry,
    expected_cv_from_d_reduction,
    wavelength_mm,
)


def test_healthy_wavelength_is_about_175_mm():
    lam = wavelength_mm(0.70, 250.0)
    assert abs(lam - 175.0) < 1e-9
    assert cv_for_reentry(106.8, 250.0) < 0.5
    assert expected_cv_from_d_reduction(0.90, 0.70) < 0.25


def test_annulus_path_between_fast_and_slow_wavelengths():
    path = annulus_mean_path_mm(14.0, 20.0)
    lam_h = wavelength_mm(0.70, 250.0)
    lam_slow = wavelength_mm(expected_cv_from_d_reduction(0.90, 0.70), 250.0)
    assert 50.0 < lam_slow < path < lam_h


def test_annulus_mask_and_stim_on_conducting_cells():
    nx = ny = 32
    dx = 1.0
    cond = annulus_conducting_mask(nx, ny, dx, r_in_mm=8.0, r_out_mm=12.0)
    assert cond.any()
    assert not cond.all()
    s1, s2, probe, probes = annulus_stim_regions(cond)
    assert cond[probe]
    sl_y, sl_x = s1
    assert cond[sl_y, sl_x].any()
    assert len(probes) == 4
    assert all(cond[p] for p in probes)
