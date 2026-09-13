"""Unit tests for 2D phase singularity / rotor tip detection."""

import numpy as np

from cardiac_ms.phase_singularity import (
    detect_phase_singularities,
    phase_from_uh,
    synthesize_rotating_phase,
    synthesize_uh_from_phase,
    topological_charge_map,
)


def test_synthetic_spiral_detects_singularity():
    phase = synthesize_rotating_phase(40, 40, charge=1)
    u, h = synthesize_uh_from_phase(phase)
    out = detect_phase_singularities(u, h, method="uh")
    assert out["rotor_detected"] is True
    assert out["n_singularities"] >= 1
    # Charge near the geometric center
    assert any(abs(int(c)) >= 1 for c in out["charges"])


def test_flat_field_no_singularity():
    u = np.full((32, 32), 0.2)
    h = np.full((32, 32), 0.9)
    out = detect_phase_singularities(u, h, method="uh")
    assert out["n_singularities"] == 0
    assert out["rotor_detected"] is False


def test_plane_wave_phase_no_charge():
    """Monotonic plane-wave phase should have zero topological charge."""
    yy, xx = np.mgrid[0:24, 0:24]
    phase = 0.2 * xx  # no singularity
    charge = topological_charge_map(phase)
    assert int(np.count_nonzero(charge)) == 0


def test_phase_from_uh_range():
    u = np.array([[0.1, 0.9], [0.5, 0.5]])
    h = np.array([[0.2, 0.8], [0.1, 0.9]])
    ph = phase_from_uh(u, h)
    assert ph.shape == (2, 2)
    assert np.all(ph >= -np.pi - 1e-12) and np.all(ph <= np.pi + 1e-12)
