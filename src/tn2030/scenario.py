"""Scenario builder: base network + one scenario file -> the network to solve (spec §4, §5.1)."""

from pathlib import Path

import pandas as pd
import pypsa
import yaml

from tn2030.demand import annual_demand_2030, reshape_profile, scale_profile, subtract_imports
from tn2030.efficiency import cooling_weighted_cut, uniform_cut
from tn2030.fleet import GAS, add_ocgt_candidates, rebuild_thermal_fleet
from tn2030.flexibility import add_shiftable_load
from tn2030.toy import HOURS_PER_YEAR, annualised_capex

MODES = ("uniform", "cooling")
HOURS_2024 = 8784  # 2024 was a leap year


def load_scenario(path: Path) -> dict:
    """Read a scenario YAML and check its keys, naming the bad one if any."""
    s = yaml.safe_load(Path(path).read_text())
    for key in ("name", "reference", "efficiency", "flexibility", "gas_price_factor"):
        if key not in s:
            raise ValueError(f"{path}: missing key '{key}'")
    if "share" not in s["efficiency"]:
        raise ValueError(f"{path}: missing key 'efficiency.share'")
    if s["efficiency"].get("mode") not in MODES:
        raise ValueError(f"{path}: efficiency.mode must be one of {MODES}")
    if "p_max_mw" not in s["flexibility"]:
        raise ValueError(f"{path}: missing key 'flexibility.p_max_mw'")
    return s


def _value(x, register: dict[str, float]) -> float:
    """Scenario values are numbers or register ids, so no number lives in two places."""
    return register[x] if isinstance(x, str) else float(x)


def calibrate_base(n_base: pypsa.Network, register: dict[str, float]) -> pypsa.Network:
    """Apply the Phase 3 calibrations (docs/project-history/phase3-validation.md) to a copy of the base network."""
    r = register
    n = rebuild_thermal_fleet(
        n_base, ccgt_mw=r["cap_2024_ccgt_mw"], ocgt_mw=r["cap_2024_ocgt_mw"] + r["cap_2024_steam_mw"],
        ccgt_eff=r["ccgt_efficiency"], ocgt_eff=r["ocgt_efficiency"], fuel_cost=r["gas_price_eur_per_mwh_th"],
        ccgt_vom=r["ccgt_vom"], ocgt_vom=r["ocgt_vom"], gas_co2=r["gas_co2_intensity"],
        efficiency_factor=r["existing_gas_efficiency_factor"])
    horizon = n.snapshot_weightings.generators.sum() / HOURS_PER_YEAR  # share of a year modelled
    ocgt_capex = horizon * annualised_capex(r["ocgt_investment"] * 1000, r["ocgt_fom"], r["ocgt_lifetime"],
                                            r["discount_rate"])  # EUR/kW -> EUR/MW
    n = add_ocgt_candidates(n, capital_cost=ocgt_capex, efficiency=r["ocgt_efficiency"],
                            fuel_cost=r["gas_price_eur_per_mwh_th"], vom=r["ocgt_vom"], gas_co2=r["gas_co2_intensity"])
    # Existing 2024 wind and solar (PyPSA-Earth's estimate, incl. the IRENA top-up) stay in 2030.
    re = n.generators.carrier.isin(["solar", "onwind"]) & n.generators.p_nom_extendable
    n.generators.loc[re, "p_nom_min"] = n.generators.loc[re, "p_nom"]
    return n


def apply_committed(n: pypsa.Network, committed: pd.DataFrame) -> None:
    """Committed projects (spec D6) raise the minimum capacity of the matching extendable generator."""
    g = n.generators
    for _, row in committed.iterrows():
        match = g.index[(g.carrier == row.carrier) & (g.bus == row.bus) & g.p_nom_extendable]
        if len(match) != 1:
            raise ValueError(f"no extendable {row.carrier} generator at bus {row.bus} for a committed project"
                             if len(match) == 0 else f"several extendable {row.carrier} generators at bus {row.bus}")
        name = match[0]
        g.at[name, "p_nom_min"] += row.p_nom_mw
        g.at[name, "p_nom"] = max(g.at[name, "p_nom"], g.at[name, "p_nom_min"])


def scale_gas_cost(n: pypsa.Network, factor: float, gas_price_eur_per_mwh_th: float) -> None:
    """Gas-price sensitivity: change only the fuel part of the gas units' marginal cost."""
    gas = n.generators.carrier.isin(GAS)
    n.generators.loc[gas, "marginal_cost"] += (factor - 1) * gas_price_eur_per_mwh_th / n.generators.efficiency[gas]


def build_scenario(n_base: pypsa.Network, scenario: dict, register: dict[str, float], committed: pd.DataFrame,
                   calibrate: bool = True) -> pypsa.Network:
    """Return a copy of the base network set up for one scenario, in the order of spec §5.1."""
    r = register
    n = calibrate_base(n_base, r) if calibrate else n_base.copy()
    w = n.snapshot_weightings.generators

    # Total demand: (reshape) -> 2030 total -> efficiency -> minus flat imports; then back to buses by share.
    base_load = n.loads_t.p_set
    total = base_load.sum(axis=1)
    if calibrate:  # Phase 3 calibration of the hourly shape
        load_factor = r["demand_2024_twh"] * 1e6 / HOURS_2024 / r["peak_2024_mw"]
        total = reshape_profile(total, w, load_factor, r["min_to_peak_2030"])
    total = scale_profile(total, w, annual_demand_2030(r["demand_2024_twh"], r["demand_growth"]) * 1e6)
    share = scenario["efficiency"]["share"]
    if scenario["efficiency"]["mode"] == "uniform":
        total = uniform_cut(total, share)
        n.meta["cooling_share"] = 0.0
    else:
        total, on_cooling = cooling_weighted_cut(total, w, share)
        n.meta["cooling_share"] = on_cooling  # share of the saving that fits on the cooling load (spec §5.2)
    domestic = subtract_imports(total, w, r["imports_2024_twh"] * 1e6)
    n.loads_t.p_set = base_load.div(base_load.sum(axis=1), axis=0).mul(domestic, axis=0)

    apply_committed(n, committed)
    scale_gas_cost(n, _value(scenario["gas_price_factor"], r), r["gas_price_eur_per_mwh_th"])
    p_max = _value(scenario["flexibility"]["p_max_mw"], r)
    if p_max > 0:
        add_shiftable_load(n, p_max, r["flex_max_hours"])
    return n
