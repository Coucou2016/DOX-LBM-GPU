"""Three-class tissue maps."""

import numpy as np

from cardiac_ms.tissue_classes import (
    CLASS_BORDER,
    CLASS_DENSE,
    CLASS_HEALTHY,
    assign_three_class,
    binary_dilate8,
    disk_fibrosis_three_class,
    fibrosis_mask,
)


def test_dilation_grows_mask():
    m = np.zeros((11, 11), dtype=bool)
    m[5, 5] = True
    d1 = binary_dilate8(m, 1)
    d2 = binary_dilate8(m, 2)
    assert d1.sum() == 9
    assert d2.sum() > d1.sum()
    assert d1[5, 5] and d1[4, 4]


def test_three_class_border_shell():
    mask = fibrosis_mask(32, 32, center=(16, 16), radius=4)
    maps = assign_three_class(mask, border_width=2, D_healthy=0.08, d_reduction_dense=0.9)
    assert maps.dense_mask.sum() == mask.sum()
    assert maps.border_mask.sum() > 0
    assert np.all(maps.classes[mask] == CLASS_DENSE)
    assert CLASS_BORDER in set(maps.classes.ravel())
    assert CLASS_HEALTHY in set(maps.classes.ravel())
    assert maps.D[mask].max() < maps.D[~mask & ~maps.border_mask].min()
    assert maps.lam[mask].mean() > maps.lam[~mask & ~maps.border_mask].mean()


def test_disk_helper_shape():
    t = disk_fibrosis_three_class(24, 20, border_width=1)
    assert t.D.shape == (20, 24)
    assert t.lam.shape == (20, 24)
