"""Print a short summary of a PyPSA network: buses, carriers, capacities and load.

Run:  python scripts/inspect_base.py <network.nc>
"""

import sys

import pypsa


def summarize(path: str) -> None:
    n = pypsa.Network(path)
    w = n.snapshot_weightings.generators  # hours each snapshot stands for

    print(f"network:   {path}")
    print(f"countries: {sorted(n.buses.country.unique())} | buses: {len(n.buses)} | lines: {len(n.lines)} "
          f"| links: {len(n.links)}")
    # PyPSA-Earth uses one step length for the whole year, so the first weight stands for all.
    print(f"snapshots: {len(n.snapshots)} x {w.iloc[0]:g} h = {w.sum():,.0f} h "
          f"({n.snapshots[0]:%Y-%m-%d} to {n.snapshots[-1]:%Y-%m-%d})")

    print("\nGenerators by carrier (existing p_nom, MW / extendable?):")
    gen = n.generators.groupby("carrier").agg(p_nom=("p_nom", "sum"), extendable=("p_nom_extendable", "any"))
    for carrier, row in gen.iterrows():
        print(f"  {carrier:<14}{row.p_nom:>10,.0f} MW   {'extendable' if row.extendable else 'fixed'}")

    # StorageUnits are sized in power (p_nom, MW), Stores in energy (e_nom, MWh).
    for comp, df, size_col, unit in (("StorageUnits", n.storage_units, "p_nom", "MW"),
                                     ("Stores", n.stores, "e_nom", "MWh")):
        if len(df):
            print(f"\n{comp} by carrier:")
            for carrier, g in df.groupby("carrier"):
                extendable = g[f"{size_col}_extendable"].any()
                print(f"  {carrier:<14}{g[size_col].sum():>10,.0f} {unit}   "
                      f"{'extendable' if extendable else 'fixed'}")

    load = n.loads_t.p_set.sum(axis=1)
    print(f"\nAnnual load: {(load * w).sum() / 1e6:,.2f} TWh | peak: {load.max():,.0f} MW "
          f"at {load.idxmax():%Y-%m-%d %H:%M}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python scripts/inspect_base.py <network.nc>")
    summarize(sys.argv[1])
