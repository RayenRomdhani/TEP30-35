"""The 2030 renewable target: renewables >= 35% of domestic generation (spec D12), and a solve wrapper.

Numerator: solar, onshore wind, run-of-river and hydro-dam output. Denominator: all generators + hydro-dam output.
Batteries and the demand-shift virtual storage are left out of both sides (they move energy, they do not produce it).
Imports are not in the model (subtracted from the load), so they are excluded too.
"""

import pypsa

RES_CARRIERS = ("solar", "onwind", "ror", "hydro")  # carrier names in the Tunisia base network (Phase 2)
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


def solve_network(n: pypsa.Network, res_share: float, solver_name: str = "highs") -> None:
    """Least-cost investment and dispatch with the renewable target. Fails loudly if the solve is not optimal."""
    status, condition = n.optimize(solver_name=solver_name,
                                   extra_functionality=lambda n, snapshots: add_min_res_share(n, res_share))
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
