"""Checks run after every real solve: the run fails if one breaks (spec §7)."""

import pandas as pd
import pypsa

from tn2030.constraints import FIRM_CARRIERS, NOT_GENERATION, res_share


def sanity_check(n: pypsa.Network, res_share_min: float, committed: pd.DataFrame, peak_ref_mw: float,
                 reserve_margin: float | None = None, tolerance: float = 0.10) -> list[str]:
    """Raise AssertionError if the solution is broken; return warnings that need a look but are not errors.

    peak_ref_mw is compared with the model's load, so pass the reference on the same basis (domestic load).
    """
    w = n.snapshot_weightings.generators
    load = n.get_switchable_as_dense("Load", "p_set")
    demand = load.mul(w, axis=0).sum().sum()
    g = n.generators

    slack = g.index[g.carrier.isin(NOT_GENERATION)]
    shed = n.generators_t.p.reindex(columns=slack, fill_value=0.0).mul(w, axis=0).sum().sum()
    assert shed <= 1e-6, f"load shedding used: {shed:,.0f} MWh of demand not met"

    share = res_share(n)
    assert share >= res_share_min - 1e-6, f"renewable share {share:.3f} below the target {res_share_min:.3f}"

    # Committed projects: each extendable generator keeps its floor (existing + committed), and every committed
    # carrier/bus has at least the committed MW built.
    below = g.index[g.p_nom_extendable & (g.p_nom_opt < g.p_nom_min - 1e-3)]
    assert len(below) == 0, f"committed or existing capacity not kept: {list(below)}"
    for (carrier, bus), mw in committed.groupby(["carrier", "bus"]).p_nom_mw.sum().items():
        installed = sum(df.p_nom_opt[(df.carrier == carrier) & (df.bus == bus)].sum()
                        for df in (g, n.storage_units))
        assert installed >= mw - 1e-3, f"committed {carrier} at {bus}: {mw:,.0f} MW required, {installed:,.0f} MW built"

    if reserve_margin is not None:
        firm = (g.p_nom_opt[g.carrier.isin(FIRM_CARRIERS)].sum()
                + n.storage_units.p_nom_opt[n.storage_units.carrier.isin(FIRM_CARRIERS)].sum())
        need = (1 + reserve_margin) * load.sum(axis=1).max()
        assert firm >= need - 1e-3, f"reserve margin: {firm:,.0f} MW firm, {need:,.0f} MW needed"

    # Whole-system energy balance: production + storage output - link losses = demand.
    supply = (n.generators_t.p.mul(w, axis=0).sum().sum()
              + n.storage_units_t.p.mul(w, axis=0).sum().sum()
              + n.stores_t.p.mul(w, axis=0).sum().sum()
              - (n.links_t.p0 + n.links_t.p1).mul(w, axis=0).sum().sum())
    gap = abs(supply - demand) / demand
    assert gap <= 1e-4, f"energy balance gap of {gap:.2e} (relative)"

    warnings = []
    peak = load.sum(axis=1).max()
    if abs(peak - peak_ref_mw) > tolerance * peak_ref_mw:
        warnings.append(f"peak load {peak:,.0f} MW is more than {tolerance:.0%} from the reference {peak_ref_mw:,.0f} MW")
    return warnings
