"""LAT / CV heterogeneity / vulnerable-window helpers."""

import numpy as np

from cardiac_ms.metrics import (
    critical_coupling_interval,
    cv_heterogeneity,
    lat_map,
    local_cv_map,
    two_point_cv,
    vulnerable_window_width,
)


def test_two_point_cv_from_linear_lat():
    lat = np.full((10, 20), np.nan)
    # 0.5 mm/ms along +x, dx=0.5 mm => 1 ms per cell
    for x in range(20):
        lat[5, x] = 10.0 + x * 1.0
    cv = two_point_cv(lat, p0=(5, 2), p1=(5, 12), dx=0.5)
    assert cv is not None
    assert abs(cv - 0.5) < 1e-9


def test_local_cv_heterogeneity_uniform():
    lat = np.zeros((12, 12))
    for x in range(12):
        lat[:, x] = x * 2.0  # 0.25 mm/ms if dx=0.5
    loc = local_cv_map(lat, dx=0.5, min_cv=0.05, max_cv=3.0)
    het = cv_heterogeneity(loc)
    assert het["cv_mean"] is not None
    assert het["cv_std_over_mean"] is not None
    assert het["cv_std_over_mean"] < 0.15


def test_critical_ci_and_vulnerable_window():
    cis = [180, 200, 220, 240, 260]
    labels = ["Non-VA", "VA", "VA", "Non-VA", "Non-VA"]
    assert critical_coupling_interval(cis, labels) == 200
    assert vulnerable_window_width(cis, labels) == 20
    assert critical_coupling_interval(cis, ["Non-VA"] * 5) is None
    assert lat_map(np.array([[1.0, np.nan]])).shape == (1, 2)
