import numpy as np
import pandas as pd
import pytest

from tn2030.efficiency import cooling_component, cooling_weighted_cut, uniform_cut

IDX = pd.date_range("2030-01-01", "2030-12-31 23:00", freq="h")
JULY_PEAK = (IDX.month == 7) & (IDX.hour >= 12) & (IDX.hour <= 17)  # afternoons in July


@pytest.fixture
def p():
    """Flat 1000 MW all year, +500 MW on July afternoons: the cooling load."""
    return pd.Series(1000.0, index=IDX) + 500.0 * JULY_PEAK


@pytest.fixture
def w():
    return pd.Series(1.0, index=IDX)


def test_uniform_cut_scales_every_hour(p):
    assert np.allclose(uniform_cut(p, 0.15), p * 0.85)


def test_cooling_component_only_in_summer_excess(p):
    c = cooling_component(p)
    assert c[JULY_PEAK].eq(500).all() and c[~JULY_PEAK].eq(0).all()


def test_cooling_component_needs_shoulder_months(p):  # the baseline comes from April, May, October, November
    with pytest.raises(ValueError, match="shoulder"):
        cooling_component(p[p.index.month == 7])


def test_cooling_weighted_cut_keeps_annual_saving(p, w):
    out, frac = cooling_weighted_cut(p, w, 0.15)
    assert ((p - out) * w).sum() == pytest.approx(0.15 * (p * w).sum())


def test_cooling_weighted_cut_reports_share_on_cooling(p, w):  # cooling energy is smaller than the saving here
    out, frac = cooling_weighted_cut(p, w, 0.15)
    cooling_mwh = (cooling_component(p) * w).sum()
    assert frac == pytest.approx(cooling_mwh / (0.15 * (p * w).sum()))


def test_cooling_weighted_cut_never_negative(p, w):
    out, _ = cooling_weighted_cut(p, w, 0.15)
    assert (out >= 0).all()


def test_cooling_weighted_cut_flat_profile_falls_back_to_uniform(w):
    flat = pd.Series(1000.0, index=IDX)
    out, frac = cooling_weighted_cut(flat, w, 0.15)
    assert frac == 0.0 and np.allclose(out, flat * 0.85)


def test_cooling_weighted_cut_zero_share_is_no_change(p, w):
    out, frac = cooling_weighted_cut(p, w, 0.0)
    assert frac == 0.0 and np.allclose(out, p)
