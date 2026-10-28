import pandas as pd
import pytest

from tn2030.results import avoided_per_mwh, summarize

BASE = pd.Series({"system_cost_meur": 100.0, "co2_mt": 2.0, "gas_use_twh_th": 5.0, "new_cap_total_mw": 1000.0,
                  "demand_twh": 10.0})
SCEN = pd.Series({"system_cost_meur": 90.0, "co2_mt": 1.8, "gas_use_twh_th": 4.5, "new_cap_total_mw": 900.0,
                  "demand_twh": 9.0})


def test_summary_uses_snapshot_weightings(solved_toy):  # 3 h steps: a raw sum would be 3x too small
    s = summarize(solved_toy)
    w = solved_toy.snapshot_weightings.generators
    assert s["demand_twh"] == pytest.approx((solved_toy.loads_t.p_set.sum(axis=1) * w).sum() / 1e6)


def test_gas_use_and_co2_follow_efficiency(solved_toy, reg):
    s = summarize(solved_toy)
    w = solved_toy.snapshot_weightings.generators
    gen = (solved_toy.generators_t.p["CCGT"] * w).sum() / 1e6
    assert s["gas_use_twh_th"] == pytest.approx(gen / reg["toy_ccgt_efficiency"])
    assert s["co2_mt"] == pytest.approx(s["gas_use_twh_th"] * reg["toy_gas_co2_intensity"])


def test_summary_has_capacity_and_new_capacity(solved_toy):
    s = summarize(solved_toy)
    assert s["cap_CCGT_mw"] == pytest.approx(solved_toy.generators.at["CCGT", "p_nom_opt"])
    assert s["new_cap_total_mw"] == pytest.approx(s.filter(like="new_cap_").drop("new_cap_total_mw").sum())


def test_avoided_per_mwh_values():
    a = avoided_per_mwh(BASE, SCEN)
    assert a["cost_eur_per_mwh"] == pytest.approx(10.0)
    assert a["co2_t_per_mwh"] == pytest.approx(0.2)
    assert a["gas_mwh_th_per_mwh"] == pytest.approx(0.5)
    assert a["capacity_mw_per_twh"] == pytest.approx(100.0)


def test_avoided_per_mwh_raises_on_zero_saving():
    with pytest.raises(ValueError, match="zero saving"):
        avoided_per_mwh(BASE, BASE)
