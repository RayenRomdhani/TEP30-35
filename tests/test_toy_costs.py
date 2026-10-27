import pytest

from tn2030.toy import annualised_capex, annuity


def test_annuity_known_value():
    assert annuity(0.07, 25) == pytest.approx(0.08581, abs=1e-5)


def test_annuity_zero_rate_is_straight_line():
    assert annuity(0.0, 20) == pytest.approx(0.05)


def test_annualised_capex_adds_fom():
    assert annualised_capex(1000.0, 2.0, 25, 0.07) == pytest.approx(1000 * (0.08581 + 0.02), rel=1e-4)
