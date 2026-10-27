"""Phase 1 single-node toy model of Tunisia (illustrative inputs, real cost data)."""

import numpy as np
import pandas as pd
import pypsa

HOURS_PER_YEAR = 8760


def annuity(rate: float, lifetime_years: float) -> float:
    """Share of an investment paid back each year over its lifetime (capital recovery factor)."""
    if rate == 0:
        return 1 / lifetime_years
    return rate / (1 - (1 + rate) ** -lifetime_years)


def annualised_capex(investment: float, fom_pct: float, lifetime_years: float, rate: float) -> float:
    """Yearly cost of one unit of capacity: annuity of the investment plus fixed O&M (FOM, % of investment)."""
    return investment * (annuity(rate, lifetime_years) + fom_pct / 100)


def _illustrative_profiles(snapshots: pd.DatetimeIndex) -> pd.DataFrame:
    """Synthetic daily shapes for load (MW), solar and wind availability (p.u.).

    ILLUSTRATIVE ONLY: smooth curves chosen to look like a summer day, not measured data.
    Load peaks at 15:00 around 4.1 GW, the same order of magnitude as Tunisia's ~4 GW summer peak.
    Days 3 and 4 are a low-wind spell: real weather has multi-day lulls, which is what backup is for.
    """
    h = snapshots.hour.to_numpy()
    day = (snapshots.normalize() - snapshots[0].normalize()).days.to_numpy()
    load = 3200 + 900 * np.cos(2 * np.pi * (h - 15) / 24)
    solar = 0.85 * np.clip(np.sin(np.pi * (h - 6) / 12), 0, None)  # daylight 06:00-18:00
    wind = 0.35 + 0.10 * np.cos(2 * np.pi * (h - 3) / 24)  # a bit windier at night
    wind = np.where(np.isin(day, (2, 3)), wind * 0.2, wind)  # lull: 20% of normal wind
    return pd.DataFrame({"load": load, "solar": solar, "wind": wind}, index=snapshots)


def build_toy_network(register: dict[str, float], hours: int = 168, step_hours: int = 1) -> pypsa.Network:
    """One bus "TN" where the optimizer sizes CCGT, solar, onshore wind and a battery to meet the load.

    Costs come from technology-data v0.15.0 via the register (EUR/kW -> x1000 to EUR/MW).
    Capital costs are yearly, but the model only covers `hours`, so they are scaled by
    hours / 8760; otherwise one week of operation would carry a full year of investment.
    """
    r = register
    rate = r["discount_rate"]
    horizon = hours / HOURS_PER_YEAR

    n = pypsa.Network()
    snapshots = pd.date_range("2030-07-01 00:00", periods=hours // step_hours, freq=f"{step_hours}h")
    n.set_snapshots(snapshots)
    n.snapshot_weightings.loc[:, :] = step_hours  # each snapshot stands for step_hours hours

    profiles = _illustrative_profiles(snapshots)

    n.add("Carrier", "CCGT", co2_emissions=r["toy_gas_co2_intensity"])  # t CO2 per MWh of gas burnt
    for carrier in ("AC", "solar", "onwind", "battery"):
        n.add("Carrier", carrier)

    n.add("Bus", "TN", carrier="AC")
    n.add("Load", "TN load", bus="TN", p_set=profiles["load"])

    ccgt_eff = r["toy_ccgt_efficiency"]
    n.add("Generator", "CCGT", bus="TN", carrier="CCGT", p_nom_extendable=True,
          efficiency=ccgt_eff,
          marginal_cost=r["toy_gas_fuel"] / ccgt_eff + r["toy_ccgt_vom"],  # fuel per MWh_el + VOM
          capital_cost=horizon * annualised_capex(r["toy_ccgt_investment"] * 1000, r["toy_ccgt_fom"],
                                                  r["toy_ccgt_lifetime"], rate))
    n.add("Generator", "solar", bus="TN", carrier="solar", p_nom_extendable=True,
          p_max_pu=profiles["solar"], marginal_cost=0.0,
          capital_cost=horizon * annualised_capex(r["toy_solar_investment"] * 1000, r["toy_solar_fom"],
                                                  r["toy_solar_lifetime"], rate))
    n.add("Generator", "onwind", bus="TN", carrier="onwind", p_nom_extendable=True,
          p_max_pu=profiles["wind"], marginal_cost=r["toy_onwind_vom"],
          capital_cost=horizon * annualised_capex(r["toy_onwind_investment"] * 1000, r["toy_onwind_fom"],
                                                  r["toy_onwind_lifetime"], rate))

    # Battery = inverter (per MW) + storage (per MWh); with fixed max_hours both are paid per MW.
    max_hours = r["toy_battery_max_hours"]
    inverter = annualised_capex(r["toy_battery_inverter_investment"] * 1000, r["toy_battery_inverter_fom"],
                                r["toy_battery_inverter_lifetime"], rate)
    storage = annualised_capex(r["toy_battery_storage_investment"] * 1000, 0.0,
                               r["toy_battery_storage_lifetime"], rate)
    eff = r["toy_battery_inverter_efficiency"]
    n.add("StorageUnit", "battery", bus="TN", carrier="battery", p_nom_extendable=True,
          max_hours=max_hours, efficiency_store=eff, efficiency_dispatch=eff,
          cyclic_state_of_charge=True,  # end the period with the same charge it started with
          capital_cost=horizon * (inverter + max_hours * storage))
    return n
