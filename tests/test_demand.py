import numpy as np
import pandas as pd
import pytest

from tn2030.demand import annual_demand_2030, peak_check, reshape_profile, scale_profile, subtract_imports


def _day(step_hours: int = 1):
    """One day of a simple load shape and its snapshot weights."""
    idx = pd.date_range("2030-01-01", periods=24 // step_hours, freq=f"{step_hours}h")
    weights = pd.Series(float(step_hours), index=idx)
    profile = pd.Series(np.linspace(2.0, 5.0, len(idx)), index=idx)
    return profile, weights


def test_annual_demand_2030_compounds_growth():
    assert annual_demand_2030(20.0, 0.037) == pytest.approx(20.0 * 1.037**6)


def test_scale_profile_hits_annual_total_with_3h_weights():
    idx = pd.date_range("2030-01-01", periods=8, freq="3h")
    w = pd.Series(3.0, index=idx)
    p = pd.Series([1, 2, 3, 4, 4, 3, 2, 1], index=idx, dtype=float)
    out = scale_profile(p, w, 1200.0)
    assert (out * w).sum() == pytest.approx(1200.0)
    assert out.iloc[3] / out.iloc[0] == pytest.approx(4.0)


def test_subtract_imports_is_flat():  # 24 MWh over 24 h -> 1 MW every step
    p, w = _day()
    assert np.allclose(p - subtract_imports(p, w, 24.0), 1.0)


def test_subtract_imports_is_flat_with_3h_weights():  # 24 MWh over 24 h -> still 1 MW per step
    p, w = _day(step_hours=3)
    assert np.allclose(p - subtract_imports(p, w, 24.0), 1.0)


def test_subtract_imports_raises_when_load_goes_negative():
    p, w = _day()
    with pytest.raises(ValueError, match="negative"):
        subtract_imports(p, w, 1e6)


def _flat_year():
    """A deliberately flat 'year' (load factor ~0.8), like the PyPSA-Earth profile."""
    idx = pd.date_range("2030-01-01", periods=240, freq="3h")
    rng = np.random.default_rng(0)
    return pd.Series(3000 + 600 * rng.random(len(idx)), index=idx), pd.Series(3.0, index=idx)


def test_reshape_profile_hits_load_factor_min_ratio_and_energy():
    p, w = _flat_year()
    out = reshape_profile(p, w, load_factor=0.52, min_to_peak=0.34)
    assert (out * w).sum() == pytest.approx((p * w).sum())  # same energy
    assert out.min() / out.max() == pytest.approx(0.34)
    assert (out * w).sum() / w.sum() / out.max() == pytest.approx(0.52, abs=1e-4)


def test_reshape_profile_keeps_hour_ranking():  # timing of peaks and troughs comes from the input
    p, w = _flat_year()
    out = reshape_profile(p, w, load_factor=0.52, min_to_peak=0.34)
    assert (out.rank() == p.rank()).all()


def test_reshape_profile_raises_on_impossible_target():  # load factor must lie between min/peak and 1
    p, w = _flat_year()
    with pytest.raises(ValueError, match="load factor"):
        reshape_profile(p, w, load_factor=0.30, min_to_peak=0.34)


def test_peak_check_flags_outside_tolerance():
    assert peak_check(pd.Series([5000.0, 6700.0]), 6000) == (6700.0, False)
    assert peak_check(pd.Series([5000.0, 6300.0]), 6000) == (6300.0, True)
