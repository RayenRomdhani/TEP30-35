import pandas as pd
import pytest

from tn2030.checks import sanity_check

NO_COMMITTED = pd.DataFrame(columns=["carrier", "bus", "p_nom_mw"])


def test_sanity_check_passes_on_solved_toy(solved_toy):
    assert isinstance(sanity_check(solved_toy, 0.35, NO_COMMITTED, peak_ref_mw=4100.0), list)


def test_sanity_check_fails_on_res_shortfall(solved_toy):
    with pytest.raises(AssertionError, match="renewable share"):
        sanity_check(solved_toy, 0.99, NO_COMMITTED, peak_ref_mw=4100.0)


def test_sanity_check_fails_on_missing_committed(solved_toy):
    committed_10gw_solar = pd.DataFrame({"carrier": ["solar"], "bus": ["TN"], "p_nom_mw": [10_000.0]})
    with pytest.raises(AssertionError, match="committed"):
        sanity_check(solved_toy, 0.0, committed_10gw_solar, peak_ref_mw=4100.0)


def test_sanity_check_fails_on_load_shedding(solved_toy):
    solved_toy.add("Generator", "TN load shedding", bus="TN", carrier="load shedding", p_nom=1e5)
    solved_toy.generators_t.p["TN load shedding"] = 1.0  # pretend 1 MW was shed every snapshot
    with pytest.raises(AssertionError, match="load shedding"):
        sanity_check(solved_toy, 0.0, NO_COMMITTED, peak_ref_mw=4100.0)


def test_sanity_check_warns_on_peak_far_from_reference(solved_toy):
    warnings = sanity_check(solved_toy, 0.35, NO_COMMITTED, peak_ref_mw=8000.0)
    assert any("peak" in w for w in warnings)
