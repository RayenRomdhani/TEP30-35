"""The 2027-2030 pathway: one least-cost solve per year, each starting from the system the year before.

Committed plants switch on in their commissioning year; on top of them the model may add only as much as Tunisia
has shown it can build in a year (design: docs/project-history/specs/2026-10-29-pathway-2027-2030-design.md).
"""

import pandas as pd
import pypsa

from tn2030.demand import reshape_profile, scale_profile, subtract_imports
from tn2030.efficiency import cooling_weighted_cut, uniform_cut
from tn2030.flexibility import add_shiftable_load
from tn2030.scenario import HOURS_2024, _value, calibrate_base, scale_gas_cost

HISTORY = (2025, 2026)            # solved once, base case: brings the fleet from 2024 to the start of the plan
PLAN = (2027, 2028, 2029, 2030)   # where the scenarios differ


def demand_twh(d2024_twh: float, growth: float, year: int) -> float:
    """Total electricity demand in a year, growing at a constant rate from 2024."""
    return d2024_twh * (1 + growth) ** (year - 2024)


def ramp(final: float, year: int, start: int = PLAN[0], end: int = PLAN[-1]) -> float:
    """A scenario's saving (or shiftable MW) builds up in equal steps and is complete in the last year."""
    if year < start:
        return 0.0
    return final * min(1.0, (year - start + 1) / (end - start + 1))


def committed_in(committed: pd.DataFrame, year: int, only_that_year: bool = False) -> pd.DataFrame:
    """Committed projects in operation by a year (or switching on in that year). Undated projects never enter."""
    cod = pd.to_numeric(committed["cod_expected"], errors="coerce")
    keep = (cod == year) if only_that_year else (cod <= year)
    return committed[keep.fillna(False)]


def carry_over(n: pypsa.Network, prev: pypsa.Network) -> None:
    """What was built last year stays: last year's optimal size becomes this year's minimum."""
    for comp, size in (("generators", "p_nom"), ("links", "p_nom"), ("stores", "e_nom"), ("lines", "s_nom")):
        df, built = getattr(n, comp), getattr(prev, comp)
        ext = df.index[df[f"{size}_extendable"]].intersection(built.index)
        df.loc[ext, f"{size}_min"] = df.loc[ext, f"{size}_min"].combine(built.loc[ext, f"{size}_opt"], max)
        df.loc[ext, size] = df.loc[ext, size].combine(df.loc[ext, f"{size}_min"], max)


def _spread(df: pd.DataFrame, idx: pd.Index, total: float) -> pd.Series:
    """Split a yearly allowance over buses by each one's existing size, or evenly if there is none yet."""
    base = df.loc[idx, "p_nom_min"]
    return base / base.sum() * total if base.sum() > 0 else pd.Series(total / len(idx), index=idx)


def limit_builds(n: pypsa.Network, year: int, limits: dict) -> None:
    """Cap this year's new solar, wind and batteries at Tunisia's demonstrated building pace."""
    g = n.generators
    for carrier, allowance in (("solar", limits["solar_mw"]),
                               ("onwind", limits["wind_mw"] if year >= limits["wind_first_year"] else 0.0)):
        idx = g.index[(g.carrier == carrier) & g.p_nom_extendable]
        if len(idx):
            g.loc[idx, "p_nom_max"] = g.loc[idx, "p_nom_min"] + _spread(g, idx, allowance)
    battery = limits["battery_mw"] if year >= limits["battery_first_year"] else 0.0
    l = n.links
    dis = l.index[(l.carrier == "battery discharger") & l.p_nom_extendable]
    if len(dis):  # the most battery power in place by this year (one project's worth), on top of what exists
        l.loc[dis, "p_nom_max"] = l.loc[dis, "p_nom_min"] + battery / len(dis)
    s = n.stores
    st = s.index[(s.carrier == "battery") & s.e_nom_extendable]
    if len(st) and "battery_mwh" in limits:
        s.loc[st, "e_nom_max"] = s.loc[st, "e_nom_min"] + (limits["battery_mwh"] if battery else 0.0) / len(st)


def apply_committed_year(n: pypsa.Network, committed: pd.DataFrame, year: int) -> None:
    """Projects switching on this year add to the minimum size of the matching extendable generator."""
    g = n.generators
    for _, row in committed_in(committed, year, only_that_year=True).iterrows():
        name = g.index[(g.carrier == row.carrier) & (g.bus == row.bus) & g.p_nom_extendable][0]
        g.at[name, "p_nom_min"] += row.p_nom_mw
        g.at[name, "p_nom"] = max(g.at[name, "p_nom"], g.at[name, "p_nom_min"])


def build_year(n_base: pypsa.Network, scenario: dict, register: dict, committed: pd.DataFrame, year: int,
               prev: pypsa.Network | None, limits: dict) -> pypsa.Network:
    """The network for one year: calibrated base, that year's demand and saving, last year's fleet, the year's
    committed plants, and the building limits."""
    r = register
    n = calibrate_base(n_base, r)
    w = n.snapshot_weightings.generators
    base_load = n.loads_t.p_set
    load_factor = r["demand_2024_twh"] * 1e6 / HOURS_2024 / r["peak_2024_mw"]
    total = reshape_profile(base_load.sum(axis=1), w, load_factor, r["min_to_peak_2030"])
    total = scale_profile(total, w, demand_twh(r["demand_2024_twh"], r["demand_growth"], year) * 1e6)
    share = ramp(scenario["efficiency"]["share"], year)
    if scenario["efficiency"]["mode"] == "uniform" or share == 0:
        total, n.meta["cooling_share"] = uniform_cut(total, share), 0.0
    else:
        total, n.meta["cooling_share"] = cooling_weighted_cut(total, w, share)
    domestic = subtract_imports(total, w, r["imports_2024_twh"] * 1e6)
    n.loads_t.p_set = base_load.div(base_load.sum(axis=1), axis=0).mul(domestic, axis=0)

    if prev is not None:
        carry_over(n, prev)
    else:  # the first year starts from 2024: add everything commissioned before it
        for y in range(2000, year):
            apply_committed_year(n, committed, y)
    apply_committed_year(n, committed, year)
    limit_builds(n, year, limits)
    if year >= PLAN[0]:
        scale_gas_cost(n, _value(scenario["gas_price_factor"], r), r["gas_price_eur_per_mwh_th"])
        p_max = ramp(_value(scenario["flexibility"]["p_max_mw"], r), year)
        if p_max > 0:
            add_shiftable_load(n, p_max, r["flex_max_hours"])
    n.meta["year"] = year
    return n


def limits_from_register(r: dict) -> dict:
    return {"solar_mw": r["pathway_solar_extra_mw_per_year"], "wind_mw": r["pathway_wind_extra_mw_per_year"],
            "wind_first_year": int(r["pathway_wind_first_year"]), "battery_mw": r["pathway_battery_mw"],
            "battery_first_year": int(r["pathway_battery_first_year"]), "battery_mwh": r["pathway_battery_mwh"]}


def peak_reference(r: dict, year: int, hours: float) -> float:
    """STEG's 2030 peak forecast scaled to the year's demand, on the model's domestic basis (for a warning only)."""
    scale = demand_twh(r["demand_2024_twh"], r["demand_growth"], year) / demand_twh(r["demand_2024_twh"], r["demand_growth"], 2030)
    return r["peak_ref_2030_mw"] * scale - r["imports_2024_twh"] * 1e6 / hours
