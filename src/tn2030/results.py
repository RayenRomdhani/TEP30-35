"""Result metrics of a solved scenario, and the headline: what each MWh saved avoids (spec §5.4).

Every energy sum multiplies MW by the hours each snapshot stands for (review focus 1).
"""

import pandas as pd
import pypsa

from tn2030.constraints import NOT_GENERATION
from tn2030.fleet import GAS


def summarize(n: pypsa.Network) -> pd.Series:
    """Capacity, new capacity, generation, demand, gas, CO2, system cost and average price of a solved network."""
    w = n.snapshot_weightings.generators
    out = {}

    # Capacity (MW). New capacity = what the optimizer added above the floor (existing + committed).
    g = n.generators[~n.generators.carrier.isin(NOT_GENERATION)]
    su = n.storage_units
    for df in (g, su):
        for carrier, mw in df.p_nom_opt.groupby(df.carrier).sum().items():
            out[f"cap_{carrier}_mw"] = out.get(f"cap_{carrier}_mw", 0.0) + mw
        ext = df[df.p_nom_extendable]
        for carrier, mw in (ext.p_nom_opt - ext.p_nom_min).groupby(ext.carrier).sum().items():
            out[f"new_cap_{carrier}_mw"] = out.get(f"new_cap_{carrier}_mw", 0.0) + mw
    # PyPSA-Earth batteries are a Store (MWh) charged and discharged through Links (MW).
    discharger = n.links[n.links.carrier == "battery discharger"]
    if len(discharger):
        out["cap_battery_mw"] = out.get("cap_battery_mw", 0.0) + discharger.p_nom_opt.sum()
        ext = discharger[discharger.p_nom_extendable]
        out["new_cap_battery_mw"] = out.get("new_cap_battery_mw", 0.0) + (ext.p_nom_opt - ext.p_nom_min).sum()
        out["cap_battery_mwh"] = n.stores.e_nom_opt[n.stores.carrier == "battery"].sum()
    out["new_cap_total_mw"] = sum(v for k, v in out.items() if k.startswith("new_cap_"))

    # Energy (TWh), gas burnt (TWh of fuel) and CO2 (Mt): fuel = output / efficiency.
    gen = n.generators_t.p[g.index].mul(w, axis=0).sum()  # MWh per generator
    for carrier, mwh in gen.groupby(g.carrier).sum().items():
        out[f"gen_{carrier}_twh"] = mwh / 1e6
    fuel = gen / g.efficiency
    out["gas_use_twh_th"] = fuel[g.carrier.isin(GAS)].sum() / 1e6
    out["co2_mt"] = (fuel * g.carrier.map(n.carriers.co2_emissions).fillna(0)).sum() / 1e6  # t CO2 per MWh_th
    load = n.get_switchable_as_dense("Load", "p_set")
    out["demand_twh"] = load.mul(w, axis=0).sum().sum() / 1e6  # domestic load only; imports cancel in differences

    # Cost (M EUR) and the average bus price (the energy-balance dual, EUR/MWh), weighted by the planned
    # load p_set (before any demand shifting).
    out["system_cost_meur"] = (n.statistics.capex().sum() + n.statistics.opex().sum()) / 1e6
    price = n.buses_t.marginal_price[n.loads.bus].set_axis(load.columns, axis=1)
    out["avg_price_eur_mwh"] = (price * load).mul(w, axis=0).sum().sum() / load.mul(w, axis=0).sum().sum()
    return pd.Series(out)


def avoided_per_mwh(base: pd.Series, scen: pd.Series) -> pd.Series:
    """What each MWh of demand saved avoids, compared with the reference scenario (headline metric)."""
    saved_twh = base["demand_twh"] - scen["demand_twh"]
    if saved_twh == 0:
        raise ValueError("zero saving: this scenario has the same demand as its reference")
    return pd.Series({
        "cost_eur_per_mwh": (base["system_cost_meur"] - scen["system_cost_meur"]) / saved_twh,  # M EUR / TWh
        "co2_t_per_mwh": (base["co2_mt"] - scen["co2_mt"]) / saved_twh,  # Mt / TWh
        "gas_mwh_th_per_mwh": (base["gas_use_twh_th"] - scen["gas_use_twh_th"]) / saved_twh,
        "capacity_mw_per_twh": (base["new_cap_total_mw"] - scen["new_cap_total_mw"]) / saved_twh,
    })
