"""Shared look of all figures: one colour per carrier, title, unit and source footer (plan Task 17).

Also the small data helpers the figures need (hourly dispatch by carrier, annual generation, price).
"""

import matplotlib.pyplot as plt
import pandas as pd
import pypsa

# One colour per carrier, the same in every figure. The order is the stacking order (bottom to top):
# it was checked with a colour-blind simulation so that neighbours in a stack stay distinct.
PALETTE = {
    "CCGT": "#e34948",     # red
    "OCGT": "#6250d6",     # violet
    "hydro": "#1baf7a",    # aqua (dam hydro and run-of-river shown together)
    "onwind": "#2a78d6",   # blue
    "solar": "#eda100",    # yellow
    "battery": "#e87ba4",  # pink (battery discharge)
}
PALETTE["ror"] = PALETTE["hydro"]
LABELS = {"CCGT": "Gas CCGT", "OCGT": "Gas OCGT + steam", "hydro": "Hydro", "onwind": "Onshore wind",
          "solar": "Solar PV", "battery": "Battery"}
STACK_ORDER = ["CCGT", "OCGT", "hydro", "onwind", "solar", "battery"]

INK, INK_2, MUTED, GRID = "#0b0b0b", "#52514e", "#898781", "#e1e0d9"  # text and chart lines
SINGLE = "#2a78d6"  # one-series charts use one colour
SOURCE = "Source: own PyPSA-Earth model of Tunisia 2030; inputs in data/assumptions_register.xlsx"


def style_axis(ax, title: str, unit: str, grid: str = "y") -> None:
    """Title on the left, unit label, light grid along the value axis, no box."""
    ax.set_title(title, loc="left", fontsize=11, color=INK, pad=8)
    (ax.set_ylabel if grid == "y" else ax.set_xlabel)(unit, color=INK_2)
    ax.grid(axis=grid, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left" if grid == "y" else "bottom"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom" if grid == "y" else "left"].set_color("#c3c2b7")
    ax.tick_params(colors=INK_2, length=0)


def add_source(fig, source: str) -> None:
    """Source line in small print at the bottom left of the figure."""
    fig.text(0.01, 0.01, source, fontsize=7, color=MUTED, ha="left", va="bottom")


def finish_figure(fig, ax, title: str, ylabel: str, source: str) -> None:
    """Title, unit on the y axis and the source footer (one-panel figures)."""
    style_axis(ax, title, ylabel)
    add_source(fig, source)


def dispatch_by_carrier(n: pypsa.Network) -> pd.DataFrame:
    """Hourly output (MW) of each carrier: generators, dam hydro and battery discharge. Demand shifting is a
    change of load, not generation, so it is left out.

    PyPSA does not store the output of a unit that never runs, hence reindex(..., fill_value=0).
    """
    g = n.generators
    out = n.generators_t.p.reindex(columns=g.index, fill_value=0).T.groupby(g.carrier.replace({"ror": "hydro"})).sum().T
    su = n.storage_units[n.storage_units.carrier != "demand_shift"]
    if len(su):
        su_p = n.storage_units_t.p_dispatch.reindex(columns=su.index, fill_value=0)
        out = out.add(su_p.T.groupby(su.carrier).sum().T, fill_value=0)
    discharger = n.links.index[n.links.carrier == "battery discharger"]
    if len(discharger):  # PyPSA-Earth battery: power leaves the discharger at bus1, so p1 is negative
        p1 = n.links_t.p1.reindex(columns=discharger, fill_value=0)
        out["battery"] = out.get("battery", 0) - p1.sum(axis=1)
    unknown = set(out.columns) - set(STACK_ORDER)
    if unknown:  # a carrier with no colour would silently drop out of the figures
        raise ValueError(f"no colour or stack position for carriers {sorted(unknown)}")
    return out[[c for c in STACK_ORDER if c in out.columns]]


def annual_generation_twh(n: pypsa.Network) -> pd.Series:
    """Yearly output per carrier (TWh): hourly MW times the hours each snapshot stands for."""
    return dispatch_by_carrier(n).mul(n.snapshot_weightings.generators, axis=0).sum() / 1e6


def load_weighted_price(n: pypsa.Network) -> pd.Series:
    """Hourly electricity price (EUR/MWh): the bus prices weighted by each bus's load in that hour."""
    load = n.get_switchable_as_dense("Load", "p_set")
    price = n.buses_t.marginal_price[n.loads.bus].set_axis(load.columns, axis=1)
    return (price * load).sum(axis=1) / load.sum(axis=1)


def new_figure(width: float = 8, height: float = 4.5):
    """A white figure with room at the bottom for the source line."""
    fig, ax = plt.subplots(figsize=(width, height), facecolor="white")
    fig.subplots_adjust(bottom=0.18)
    return fig, ax
