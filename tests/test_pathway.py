import numpy as np
import pandas as pd
import pytest

from tn2030.constraints import solve_network
from tn2030.pathway import carry_over, committed_in, demand_twh, limit_builds, ramp

LIMITS = {"solar_mw": 268.0, "wind_mw": 75.0, "wind_first_year": 2029, "battery_mw": 150.0, "battery_first_year": 2029}


def test_demand_grows_each_year():
    assert demand_twh(22.5, 0.032, 2027) == pytest.approx(22.5 * 1.032 ** 3)


def test_ramp_reaches_the_full_value_in_2030():
    assert [ramp(0.15, y) for y in (2026, 2027, 2028, 2029, 2030)] == pytest.approx([0, 0.0375, 0.075, 0.1125, 0.15])


def test_committed_in_keeps_projects_due_by_that_year():
    df = pd.DataFrame({"name": ["a", "b", "c"], "cod_expected": [2025, 2027, np.nan], "p_nom_mw": [1, 2, 3]})
    assert list(committed_in(df, 2026).name) == ["a"]
    assert list(committed_in(df, 2027, only_that_year=True).name) == ["b"]  # undated projects never enter


def test_carry_over_keeps_last_years_build(solved_toy, toy_network):
    built = solved_toy.generators.p_nom_opt["solar"]
    carry_over(toy_network, solved_toy)
    assert toy_network.generators.at["solar", "p_nom_min"] == pytest.approx(built)


def test_limit_builds_caps_new_solar_and_blocks_early_wind(toy_network):
    n = toy_network
    n.generators.loc["solar", "p_nom_min"] = 500.0
    limit_builds(n, 2027, LIMITS)
    assert n.generators.at["solar", "p_nom_max"] == pytest.approx(500.0 + 268.0)
    assert n.generators.at["onwind", "p_nom_max"] == pytest.approx(n.generators.at["onwind", "p_nom_min"])  # no wind before 2029
    limit_builds(n, 2029, LIMITS)
    assert n.generators.at["onwind", "p_nom_max"] == pytest.approx(n.generators.at["onwind", "p_nom_min"] + 75.0)


def test_limit_builds_blocks_batteries_before_their_year(pe_battery_network):
    n = pe_battery_network
    limit_builds(n, 2028, LIMITS)
    d = n.links.index[n.links.carrier == "battery discharger"]
    assert (n.links.loc[d, "p_nom_max"] == n.links.loc[d, "p_nom_min"]).all()
    limit_builds(n, 2029, LIMITS)
    assert n.links.loc[d, "p_nom_max"].sum() == pytest.approx(n.links.loc[d, "p_nom_min"].sum() + 150.0)


def test_limited_year_still_solves_without_the_target(toy_network):  # the target is reported, not enforced
    limit_builds(toy_network, 2027, LIMITS)
    solve_network(toy_network, None)
    assert toy_network.generators.p_nom_opt["solar"] <= toy_network.generators.p_nom_max["solar"] + 1e-6
