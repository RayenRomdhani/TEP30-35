"""Phase 1: solve the single-node toy model for one summer week and plot its dispatch.

Run:  python scripts/phase1_toy_model.py
Output: results/figures/phase1_toy_dispatch.png and a short printed summary.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from tn2030.register import load_register
from tn2030.toy import build_toy_network

ROOT = Path(__file__).parents[1]
FIG = ROOT / "results" / "figures" / "phase1_toy_dispatch.png"

# Fixed carrier colours (validated for colour-blind separation with the dataviz validator).
COLORS = {"CCGT": "#eb6834", "onwind": "#2a78d6", "solar": "#eda100", "battery": "#6250d6"}
LABELS = {"CCGT": "Gas (CCGT)", "onwind": "Onshore wind", "solar": "Solar PV", "battery": "Battery"}
INK, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#e1e0d9", "#fcfcfb"


def summarize(n) -> None:
    """Print built capacity, generation shares and cost for the solved week."""
    w = n.snapshot_weightings.generators
    gen = n.generators_t.p.mul(w, axis=0).sum()
    print("Built capacity (MW):")
    for name, mw in (n.generators.p_nom_opt.clip(lower=0) + 0.0).items():  # + 0.0 turns solver's -0.0 into 0.0
        print(f"  {LABELS[name]:<14}{mw:8.0f}")
    print(f"  {'Battery':<14}{n.storage_units.p_nom_opt['battery']:8.0f}  "
          f"({n.storage_units.max_hours['battery']:.0f} h)")
    print("Generation share of the week:")
    for name, mwh in gen.clip(lower=0).items():
        print(f"  {LABELS[name]:<14}{mwh / gen.sum():8.1%}")
    print(f"System cost of the week: {n.objective / 1e6:.2f} M EUR")


def _middle_of_longest_run(mask: pd.Series) -> pd.Timestamp:
    """Timestamp in the middle of the longest unbroken stretch where mask is True."""
    run_id = (mask != mask.shift()).cumsum()  # new id each time mask flips
    runs = mask[mask].groupby(run_id[mask])
    longest = max(runs, key=lambda kv: len(kv[1]))[1]
    return longest.index[len(longest) // 2]


def plot_dispatch(n, path: Path) -> None:
    """Stacked hourly dispatch with the load line; battery charging drawn below zero."""
    t = n.snapshots
    gen = n.generators_t.p
    batt = n.storage_units_t.p["battery"]
    layers = [("CCGT", gen["CCGT"]), ("onwind", gen["onwind"]),
              ("solar", gen["solar"]), ("battery", batt.clip(lower=0))]

    plt.rcParams["font.family"] = "Arial"
    fig, ax = plt.subplots(figsize=(10, 5), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)

    bottom = 0
    label_at = {}  # carrier -> (time, y): label each band on its own day so labels never collide
    label_day = {"CCGT": 0, "onwind": 1, "solar": 1, "battery": 2}
    for carrier, series in layers:
        top = bottom + series / 1000  # MW -> GW
        ax.fill_between(t, bottom, top, color=COLORS[carrier], edgecolor=SURFACE, linewidth=2,
                        label=LABELS[carrier], step="post")
        day = series.iloc[24 * label_day[carrier]: 24 * (label_day[carrier] + 1)]
        if day.max() > 50:  # skip empty bands (> 50 MW to be visible)
            when = _middle_of_longest_run(day >= 0.6 * day.max())  # inside the band, not on its edge
            label_at[carrier] = (when + pd.Timedelta(minutes=30), (bottom + top)[when] / 2)
        bottom = top
    ax.fill_between(t, 0, batt.clip(upper=0) / 1000, color=COLORS["battery"], alpha=0.5,
                    edgecolor=SURFACE, linewidth=2, label="Battery charging", step="post")
    ax.step(t, n.loads_t.p_set["TN load"] / 1000, where="post", color=INK, linewidth=2, label="Load")

    # Direct labels (solar's yellow is low-contrast on white, so colour alone is not enough).
    for carrier, (when, y) in label_at.items():
        ax.annotate(LABELS[carrier], (when, y), color=INK, fontsize=9, ha="center", va="center",
                    bbox=dict(boxstyle="round,pad=0.2", fc=SURFACE, ec="none", alpha=0.8))

    ax.set_title("Toy model: optimal dispatch over one summer week (single node, illustrative)",
                 color=INK, fontsize=12, loc="left")
    ax.set_ylabel("Power (GW)", color=MUTED)
    ax.axhline(0, color="#c3c2b7", linewidth=1)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.tick_params(colors=MUTED)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#c3c2b7")
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), frameon=False, fontsize=9)
    fig.text(0.01, 0.045, "Generation above the load line charges the battery (shown below zero). "
             "Wind availability drops to 20% on 2-3 July (low-wind spell).", color=MUTED, fontsize=8)
    fig.text(0.01, 0.01, "Illustrative load, solar and wind shapes (not measured data). "
             "Costs: PyPSA technology-data v0.15.0 (2030). Solver: HiGHS.",
             color=MUTED, fontsize=8)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, facecolor=SURFACE)
    plt.close(fig)


def main() -> None:
    reg = load_register(ROOT / "data" / "assumptions_register.xlsx")
    n = build_toy_network(reg, hours=168, step_hours=1)
    status, condition = n.optimize(solver_name="highs")
    print(f"status {status} ({condition})")
    summarize(n)
    plot_dispatch(n, FIG)
    print(f"figure: {FIG.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
