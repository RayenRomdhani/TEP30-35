"""Demand flexibility: shiftable load modelled as a free, lossless "virtual battery" (spec D5, §5.3).

Charging = postponing load (consumers use less now), discharging = consuming the postponed load later.
The virtual battery must be empty at the end of every day, so no energy is saved, only moved in time.
"""

import numpy as np
import pandas as pd
import pypsa

CARRIER = "demand_shift"


def add_shiftable_load(n: pypsa.Network, p_max_mw: float, max_hours: float) -> None:
    """Add one StorageUnit "demand_shift <bus>" per load bus.

    - Power p_max_mw, split between buses by their share of annual load (weighted by snapshot hours).
    - Energy limit p_nom x max_hours: at full power, load moves by at most max_hours.
    - No cost and no losses: shifting is limited only by these two caps.
    - State of charge forced to 0 at the last snapshot of each calendar day (also a partial last day).
    """
    w = n.snapshot_weightings.generators
    load = n.get_switchable_as_dense("Load", "p_set")  # works for constant and time-varying loads
    annual = load.mul(w, axis=0).sum().groupby(n.loads.bus).sum()  # MWh per bus
    share = annual / annual.sum()

    day = pd.Series(n.snapshots.normalize(), index=n.snapshots)
    last_of_day = day != day.shift(-1)  # True on the last snapshot of each day, including the final one
    soc_set = pd.Series(np.where(last_of_day, 0.0, np.nan), index=n.snapshots)

    if CARRIER not in n.carriers.index:
        n.add("Carrier", CARRIER)
    for bus, s in share.items():
        n.add("StorageUnit", f"{CARRIER} {bus}", bus=bus, carrier=CARRIER, p_nom=p_max_mw * s,
              p_nom_extendable=False, max_hours=max_hours, efficiency_store=1.0, efficiency_dispatch=1.0,
              capital_cost=0.0, marginal_cost=0.0, cyclic_state_of_charge=False, state_of_charge_initial=0.0,
              state_of_charge_set=soc_set)
