"""Replace PyPSA-Earth's existing thermal fleet with official capacities by type (Phase 3 calibration).

PyPSA-Earth labels all Tunisian gas plants "CCGT" (5,580 MW) and adds 1,409 MW of "oil"; ONEM 2024 lists
2,527 MW combined cycle, 2,457 MW gas turbines and 660 MW steam, and no oil category.
"""

import pypsa

THERMAL = ["CCGT", "OCGT", "oil"]


def rebuild_thermal_fleet(n: pypsa.Network, ccgt_mw: float, ocgt_mw: float, ccgt_eff: float, ocgt_eff: float,
                          fuel_cost: float, ccgt_vom: float, ocgt_vom: float,
                          efficiency_factor: float = 1.0) -> pypsa.Network:
    """Return a copy of n whose existing thermal plants match the official totals.

    - Existing units become fixed generators "<bus> CCGT existing" / "<bus> OCGT existing" (steam is counted with
      OCGT by the caller). Their capital cost is 0 because it is already sunk.
    - Each bus gets the same share of both types as it had of PyPSA-Earth's existing thermal MW.
    - Existing efficiencies are the technology-data values times one fitted factor (Task 10); fuel cost follows.
    - "oil" generators are removed. The old extendable CCGT/OCGT generators stay as new-build options, from 0 MW.
    """
    g = n.generators
    thermal = g[g.carrier.isin(THERMAL)]
    existing_mw = thermal.p_nom_min.where(thermal.p_nom_extendable, thermal.p_nom)  # merged units: existing = p_nom_min
    share = existing_mw.groupby(thermal.bus).sum()
    share = share / share.sum()

    m = n.copy()
    m.mremove("Generator", m.generators.index[m.generators.carrier == "oil"])  # PyPSA 0.30: mremove for several names
    new_build = m.generators.carrier.isin(["CCGT", "OCGT"]) & m.generators.p_nom_extendable
    m.generators.loc[new_build, ["p_nom", "p_nom_min"]] = 0.0

    for carrier, mw, eff, vom in (("CCGT", ccgt_mw, ccgt_eff, ccgt_vom), ("OCGT", ocgt_mw, ocgt_eff, ocgt_vom)):
        if carrier not in m.carriers.index:
            m.add("Carrier", carrier)
        e = eff * efficiency_factor
        for bus, s in share.items():
            m.add("Generator", f"{bus} {carrier} existing", bus=bus, carrier=carrier, p_nom=mw * s,
                  efficiency=e, marginal_cost=fuel_cost / e + vom, capital_cost=0.0)
    return m
