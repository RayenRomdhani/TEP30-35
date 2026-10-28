"""Demand flexibility: shiftable load modelled as a free, lossless "virtual battery" (spec D5, §5.3).

Neutral state = half full. Above neutral: consumers used power EARLIER than planned (the unit "charged",
so load went up, and will "discharge" later, so load goes down). Below neutral: consumers POSTPONED use
(load went down now and comes back later). Every day ends back at neutral, so no energy is saved, only moved,
and add_shift_duration_limit makes every MWh come back within `max_hours` (+-3 h in the spec).
"""

import numpy as np
import pandas as pd
import pypsa
import xarray as xr

CARRIER = "demand_shift"


def add_shiftable_load(n: pypsa.Network, p_max_mw: float, max_hours: float) -> None:
    """Add one StorageUnit "demand_shift <bus>" per load bus.

    - Power p_max_mw, split between buses by their share of annual load (weighted by snapshot hours).
    - Energy room 2 x p_nom x max_hours, starting half full: up to p_nom x max_hours can be moved earlier,
      or the same amount later.
    - No cost and no losses: shifting is limited only by these caps and the 3 h duration limit.
    - Back to half full at the last snapshot of each calendar day (also a partial last day).
    """
    w = n.snapshot_weightings.generators
    load = n.get_switchable_as_dense("Load", "p_set")  # works for constant and time-varying loads
    annual = load.mul(w, axis=0).sum().groupby(n.loads.bus).sum()  # MWh per bus
    share = annual / annual.sum()

    day = pd.Series(n.snapshots.normalize(), index=n.snapshots)
    last_of_day = (day != day.shift(-1)).to_numpy()  # last snapshot of each day, including the final one

    if CARRIER not in n.carriers.index:
        n.add("Carrier", CARRIER)
    for bus, s in share.items():
        p_nom = p_max_mw * s
        neutral = p_nom * max_hours  # MWh: half of the room
        n.add("StorageUnit", f"{CARRIER} {bus}", bus=bus, carrier=CARRIER, p_nom=p_nom, p_nom_extendable=False,
              max_hours=2 * max_hours, efficiency_store=1.0, efficiency_dispatch=1.0, capital_cost=0.0,
              marginal_cost=0.0, cyclic_state_of_charge=False, state_of_charge_initial=neutral,
              state_of_charge_set=pd.Series(np.where(last_of_day, neutral, np.nan), index=n.snapshots))


def add_shift_duration_limit(n: pypsa.Network) -> None:
    """Every MWh moved must come back within max_hours (call inside extra_functionality; no-op without shift units).

    Energy owed now cannot exceed what was moved during the last max_hours:
      moved earlier:  SOC_t - neutral <= sum of charging over the last max_hours
      postponed:      neutral - SOC_t <= sum of discharging over the last max_hours
    And in each hour, load shifted up + load shifted down <= p_nom (the flexible demand can only do one at a time).
    Without that cap, charging and discharging at the same time (free, lossless) would refresh the window and
    let energy stay owed longer than max_hours.
    """
    units = n.storage_units.index[n.storage_units.carrier == CARRIER]
    if len(units) == 0:
        return
    w = n.snapshot_weightings.stores  # hours per snapshot (uniform in this study)
    shift_hours = n.storage_units.max_hours[units] / 2
    window = max(1, int(round(shift_hours.iloc[0] / w.iloc[0])))  # number of snapshots in max_hours
    neutral = xr.DataArray((n.storage_units.p_nom[units] * shift_hours).values, coords={"StorageUnit": list(units)})

    m = n.model
    soc = m["StorageUnit-state_of_charge"].sel(StorageUnit=list(units))
    store = m["StorageUnit-p_store"].sel(StorageUnit=list(units)) * w
    dispatch = m["StorageUnit-p_dispatch"].sel(StorageUnit=list(units)) * w
    recent_store = sum(store.shift(snapshot=k) for k in range(window))
    recent_dispatch = sum(dispatch.shift(snapshot=k) for k in range(window))
    m.add_constraints(soc - recent_store <= neutral, name="demand_shift-earlier_within_limit")
    m.add_constraints(-soc - recent_dispatch <= -neutral, name="demand_shift-later_within_limit")
    p_nom = xr.DataArray(n.storage_units.p_nom[units].values, coords={"StorageUnit": list(units)})
    m.add_constraints(m["StorageUnit-p_store"].sel(StorageUnit=list(units))
                      + m["StorageUnit-p_dispatch"].sel(StorageUnit=list(units)) <= p_nom,
                      name="demand_shift-one_direction_at_a_time")
