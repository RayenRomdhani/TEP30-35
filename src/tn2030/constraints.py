"""The 2030 renewable target: renewables >= 35% of domestic generation (spec D12), and a solve wrapper.

Numerator: solar, onshore wind, run-of-river and hydro-dam output. Denominator: all generators + hydro-dam output.
Batteries and the demand-shift virtual storage are left out of both sides (they move energy, they do not produce it).
Imports are not in the model (subtracted from the load), so they are excluded too.
"""

import pypsa

from tn2030.flexibility import add_shift_duration_limit

RES_CARRIERS = ("solar", "onwind", "ror", "hydro")  # carrier names in the Tunisia base network (Phase 2)
FIRM_CARRIERS = ("CCGT", "OCGT", "hydro", "ror")  # dispatchable plants that count toward the reserve margin
NOT_GENERATION = ("load shedding", "unserved")  # emergency slack, if present, is not domestic generation


def _generator_index(n, carriers):
    return n.generators.index[n.generators.carrier.isin(carriers)]


def add_min_res_share(n: pypsa.Network, share: float, res_carriers: tuple[str, ...] = RES_CARRIERS) -> None:
    """Add sum(renewable output) >= share x sum(domestic output) over the year. Call inside extra_functionality."""
    res_gen = _generator_index(n, res_carriers)
    hydro = n.storage_units.index[n.storage_units.carrier.isin(res_carriers)]
    if len(res_gen) + len(hydro) == 0:
        raise ValueError(f"no generator or storage unit has a renewable carrier in {res_carriers}")
    all_gen = n.generators.index[~n.generators.carrier.isin(NOT_GENERATION)]

    w = n.snapshot_weightings.generators  # hours per snapshot: MW -> MWh
    p = n.model["Generator-p"] * w
    renewable = p.sel(Generator=list(res_gen)).sum()
    total = p.sel(Generator=list(all_gen)).sum()
    if len(hydro):
        dispatch = n.model["StorageUnit-p_dispatch"] * w
        renewable = renewable + dispatch.sel(StorageUnit=list(hydro)).sum()
        total = total + dispatch.sel(StorageUnit=list(hydro)).sum()
    n.model.add_constraints(renewable - share * total >= 0, name="res_share_min")


def add_battery_link_constraint(n: pypsa.Network) -> None:
    """PyPSA-Earth batteries: charger size = efficiency x discharger size (as its own solve_network.py, line 514).

    PyPSA-Earth puts the whole inverter cost on the charger; without this link the discharger would be free.
    """
    links = n.links[n.links.p_nom_extendable]
    chargers = links.index[links.carrier == "battery charger"]
    dischargers = links.index[links.carrier == "battery discharger"]
    if len(chargers) == 0:
        return
    p_nom = n.model["Link-p_nom"]
    for charger, discharger in zip(sorted(chargers), sorted(dischargers)):  # same bus prefix, so same order
        eff = n.links.at[discharger, "efficiency"]
        n.model.add_constraints(p_nom.sel({"Link-ext": charger}) - eff * p_nom.sel({"Link-ext": discharger}) == 0,
                                name=f"battery_charger_ratio {charger}")


def add_reserve_margin(n: pypsa.Network, margin: float, firm_carriers: tuple[str, ...] = FIRM_CARRIERS) -> None:
    """Firm capacity (gas, hydro) >= (1 + margin) x peak load: STEG's planning reserve (JICA 2022, p.5-33).

    Wind, solar, batteries and shifted load get no firm credit (conservative); the peak is before any shifting.
    """
    peak = n.get_switchable_as_dense("Load", "p_set").sum(axis=1).max()
    g, su = n.generators, n.storage_units
    fixed = (g.p_nom[g.carrier.isin(firm_carriers) & ~g.p_nom_extendable].sum()
             + su.p_nom[su.carrier.isin(firm_carriers) & ~su.p_nom_extendable].sum())
    extendable = g.index[g.carrier.isin(firm_carriers) & g.p_nom_extendable]
    new = n.model["Generator-p_nom"].sel({"Generator-ext": list(extendable)}).sum()
    n.model.add_constraints(new >= (1 + margin) * peak - fixed, name="reserve_margin")


def solve_network(n: pypsa.Network, res_share: float | None, reserve_margin: float | None = None,
                  solver_name: str = "highs") -> None:
    """Least-cost investment and dispatch with the study's extra constraints. Fails loudly if not optimal.

    Renewable share (if given; the pathway reports it instead), battery charger/discharger link, reserve margin
    (if given), 3 h shift limit (if the network has shiftable load).
    """
    def extra(n, snapshots):
        if res_share is not None:
            add_min_res_share(n, res_share)
        add_battery_link_constraint(n)
        if reserve_margin is not None:
            add_reserve_margin(n, reserve_margin)
        add_shift_duration_limit(n)

    status, condition = n.optimize(solver_name=solver_name, extra_functionality=extra)
    if status != "ok":
        raise RuntimeError(f"solve failed: {status}, {condition}")


def res_share(n: pypsa.Network, res_carriers: tuple[str, ...] = RES_CARRIERS) -> float:
    """Renewable share of a solved network, same definition as the constraint."""
    w = n.snapshot_weightings.generators
    gen = n.generators_t.p.mul(w, axis=0).sum()
    hydro = n.storage_units.index[n.storage_units.carrier.isin(res_carriers)]
    hydro_mwh = n.storage_units_t.p_dispatch[hydro].mul(w, axis=0).sum().sum() if len(hydro) else 0.0
    renewable = gen[_generator_index(n, res_carriers)].sum() + hydro_mwh
    total = gen[n.generators.index[~n.generators.carrier.isin(NOT_GENERATION)]].sum() + hydro_mwh
    return renewable / total
