"""Replace PyPSA-Earth's existing thermal fleet with official capacities by type (Phase 3 calibration).

PyPSA-Earth labels all Tunisian gas plants "CCGT" (5,580 MW) and adds 1,409 MW of "oil"; ONEM 2024 lists
2,527 MW combined cycle, 2,457 MW gas turbines and 660 MW steam, and no oil category.
"""

import pypsa

GAS = ["CCGT", "OCGT"]


def _add_gas_carrier(n: pypsa.Network, carrier: str, gas_co2: float) -> None:
    if carrier not in n.carriers.index:
        n.add("Carrier", carrier, co2_emissions=gas_co2)  # same fuel as CCGT, so same t CO2 per MWh_th


def rebuild_thermal_fleet(n: pypsa.Network, ccgt_mw: float, ocgt_mw: float, ccgt_eff: float, ocgt_eff: float,
                          fuel_cost: float, ccgt_vom: float, ocgt_vom: float, gas_co2: float,
                          efficiency_factor: float = 1.0) -> pypsa.Network:
    """Return a copy of n whose existing thermal plants match the official totals.

    - Existing units become fixed generators "<bus> CCGT existing" / "<bus> OCGT existing" (steam is counted with
      OCGT by the caller). Their capital cost is 0 because it is already sunk.
    - Each bus gets the same share of both types as it had of PyPSA-Earth's existing gas MW ("oil" is ignored:
      it has no counterpart in the official statistics).
    - Existing efficiencies are the technology-data values times one fitted factor (Task 10); fuel cost follows.
    - "oil" generators are removed. PyPSA-Earth's old extendable CCGT generators stay as the CCGT new-build
      option, from 0 MW. (PyPSA-Earth adds no OCGT option for Tunisia: see add_ocgt_candidates.)
    """
    g = n.generators
    gas = g[g.carrier.isin(GAS)]
    existing_mw = gas.p_nom_min.where(gas.p_nom_extendable, gas.p_nom)  # merged units: existing = p_nom_min
    share = existing_mw.groupby(gas.bus).sum()
    if share.sum() <= 0:
        raise ValueError("no existing gas capacity to locate the official fleet on")
    share = share / share.sum()

    m = n.copy()
    m.mremove("Generator", m.generators.index[m.generators.carrier == "oil"])  # PyPSA 0.30: mremove for several names
    new_build = m.generators.carrier.isin(GAS) & m.generators.p_nom_extendable
    m.generators.loc[new_build, ["p_nom", "p_nom_min"]] = 0.0

    for carrier, mw, eff, vom in (("CCGT", ccgt_mw, ccgt_eff, ccgt_vom), ("OCGT", ocgt_mw, ocgt_eff, ocgt_vom)):
        _add_gas_carrier(m, carrier, gas_co2)
        e = eff * efficiency_factor
        for bus, s in share.items():
            m.add("Generator", f"{bus} {carrier} existing", bus=bus, carrier=carrier, p_nom=mw * s,
                  efficiency=e, marginal_cost=fuel_cost / e + vom, capital_cost=0.0)
    return m


def add_ocgt_candidates(n: pypsa.Network, capital_cost: float, efficiency: float, fuel_cost: float, vom: float,
                        gas_co2: float) -> pypsa.Network:
    """Add one extendable new-build OCGT per AC bus (spec D1). PyPSA-Earth only adds OCGT where one already exists.

    capital_cost is annualised (EUR/MW/yr, already scaled to the modelled hours); gas_co2 is only used if the
    OCGT carrier is missing.
    """
    m = n.copy()
    _add_gas_carrier(m, "OCGT", gas_co2)
    for bus in m.buses.index[m.buses.carrier == "AC"]:
        m.add("Generator", f"{bus} OCGT new", bus=bus, carrier="OCGT", p_nom=0.0, p_nom_extendable=True,
              efficiency=efficiency, marginal_cost=fuel_cost / efficiency + vom, capital_cost=capital_cost)
    return m
