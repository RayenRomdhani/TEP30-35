"""Draw the result figures from results/*.csv and the solved networks (plan Task 17).

Run from the repo root after `snakemake -j 1`:  python scripts/make_figures.py
Writes 13 PNGs to results/figures/ (0_headline.png is the README's opening picture; 10-12 need the pathway results).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # this checkout's tn2030, as in the Snakefile
import matplotlib

matplotlib.use("Agg")  # write files, open no window
import matplotlib.patches
import matplotlib.pyplot as plt
import pandas as pd
import pypsa

from tn2030.plotting import (INK, INK_2, LABELS, PALETTE, SINGLE, SOURCE, STACK_ORDER, add_source,
                             annual_generation_twh, dispatch_by_carrier, finish_figure, load_weighted_price,
                             new_figure, style_axis)
from tn2030.constraints import res_share
from tn2030.register import load_register

RESULTS = Path("results")
FIGURES = RESULTS / "figures"
plt.rcParams.update({"font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 9})

# Scenario order on every axis: base-price runs first, then the two gas-price variants.
ORDER = ["S0", "S1-10", "S1-15", "S1-20", "S1-15C", "S2-300", "S2-600",
         "G-lo-S0", "G-lo-S1-15", "G-hi-S0", "G-hi-S1-15"]
LINE_COLOURS = ["#2a78d6", "#eb6834", "#1baf7a"]  # up to three compared scenarios (blue, orange, aqua)


def scenario_labels(reg: dict) -> dict[str, str]:
    """Two-line tick labels: the scenario code and what changes, with the factors read from the register."""
    lo, hi = round((reg["gas_price_factor_lo"] - 1) * 100), round((reg["gas_price_factor_hi"] - 1) * 100)
    flex, flex_hi = round(reg["flex_cap_mw"]), round(reg["flex_cap_hi_mw"])
    return {"S0": "S0\nbase", "S1-10": "S1-10\nsave 10%", "S1-15": "S1-15\nsave 15%", "S1-20": "S1-20\nsave 20%",
            "S1-15C": "S1-15C\n15% cooling", "S2-300": f"S2-300\n15% saved\n+{flex} MW shift",
            "S2-600": f"S2-600\n15% saved\n+{flex_hi} MW shift",
            "G-lo-S0": f"G-lo-S0\ngas {lo:+d}%", "G-lo-S1-15": f"G-lo-S1-15\ngas {lo:+d}%, 15%",
            "G-hi-S0": f"G-hi-S0\ngas {hi:+d}%", "G-hi-S1-15": f"G-hi-S1-15\ngas {hi:+d}%, 15%"}


def save(fig, name: str) -> None:
    fig.savefig(FIGURES / f"{name}.png", dpi=200)
    plt.close(fig)
    print("wrote", FIGURES / f"{name}.png")


def stacked_bars(table: pd.DataFrame, labels: dict, title: str, unit: str, name: str, total_fmt: str) -> None:
    """One stacked bar per scenario, one segment per carrier, the total written above each bar."""
    fig, ax = new_figure(11, 5)
    bottom = pd.Series(0.0, index=table.index)
    for carrier in [c for c in STACK_ORDER if c in table.columns]:
        ax.bar(range(len(table)), table[carrier], 0.6, bottom=bottom, color=PALETTE[carrier],
               edgecolor="white", linewidth=1, label=LABELS[carrier])
        bottom += table[carrier]
    for i, total in enumerate(bottom):
        ax.text(i, total, total_fmt.format(total), ha="center", va="bottom", fontsize=8, color=INK)
    ax.set_xticks(range(len(table)), [labels[s] for s in table.index], fontsize=7.5)
    ax.legend(ncol=6, frameon=False, loc="upper left", bbox_to_anchor=(0, -0.17), fontsize=8)
    fig.subplots_adjust(bottom=0.25, top=0.9)
    finish_figure(fig, ax, title, unit, SOURCE)
    save(fig, name)


def single_bars(values: pd.Series, labels: dict, title: str, unit: str, name: str, fmt: str) -> None:
    """One bar per scenario, all in one colour, the value written above each bar."""
    fig, ax = new_figure(11, 4.5)
    ax.bar(range(len(values)), values, 0.6, color=SINGLE)
    for i, v in enumerate(values):
        ax.text(i, v, fmt.format(v), ha="center", va="bottom", fontsize=8, color=INK)
    ax.set_xticks(range(len(values)), [labels[s] for s in values.index], fontsize=7.5)
    fig.subplots_adjust(bottom=0.2, top=0.9)
    finish_figure(fig, ax, title, unit, SOURCE)
    save(fig, name)


def capacity_mix(summary: pd.DataFrame, labels: dict) -> None:
    cap = pd.DataFrame({c: summary.get(f"cap_{c}_mw", 0.0) for c in STACK_ORDER}).fillna(0)
    cap["hydro"] += summary["cap_ror_mw"].fillna(0)  # run-of-river shown with dam hydro
    stacked_bars(cap / 1e3, labels, "Installed capacity in 2030 (existing + committed + optimised)", "GW",
                 "1_capacity_mix", "{:.1f}")


def generation_mix(networks: dict, labels: dict) -> None:
    # Battery output is left out: it re-delivers energy already counted when it was generated.
    gen = pd.DataFrame({s: annual_generation_twh(n) for s, n in networks.items()}).T.fillna(0)
    gen = gen.drop(columns="battery", errors="ignore")
    stacked_bars(gen, labels, "Domestic generation in 2030 (imports and battery output not shown)", "TWh per year",
                 "2_generation_mix", "{:.1f}")


def price_duration(networks: dict) -> None:
    fig, ax = new_figure(9, 4.5)
    for colour, s in zip(LINE_COLOURS, ["S0", "S1-15", "S2-300"]):
        n = networks[s]
        price = load_weighted_price(n).sort_values(ascending=False)
        hours = n.snapshot_weightings.generators[price.index].cumsum()  # x axis in hours, whatever the step length
        ax.plot(hours.values, price.values, color=colour, linewidth=2, label=s, drawstyle="steps-pre")
    ax.set_xlabel("Hours of the year, most expensive first", color=INK_2)
    ax.set_xlim(0, n.snapshot_weightings.generators.sum())
    ax.legend(frameon=False)
    finish_figure(fig, ax, "Price duration curves: hourly electricity price (load-weighted over both buses)",
                  "EUR/MWh", SOURCE)
    save(fig, "6_price_duration")


def dispatch_week(networks: dict) -> None:
    """S0 and S2-300 side by side, the same 7 days centred on the S0 annual peak hour."""
    s0 = networks["S0"]
    peak = s0.get_switchable_as_dense("Load", "p_set").sum(axis=1).idxmax()
    window = slice(peak - pd.Timedelta(hours=84), peak + pd.Timedelta(hours=83))
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), sharey=True, facecolor="white")
    fig.subplots_adjust(bottom=0.2, wspace=0.06)
    titles = {"S0": "S0 (base): the week around the annual peak hour",
              "S2-300": "S2-300 (15% saved + load shifting): the same week"}
    for ax, s in zip(axes, ["S0", "S2-300"]):
        n = networks[s]
        d = dispatch_by_carrier(n).loc[window] / 1e3
        d = d.loc[:, d.max() > 0.001]  # drop carriers that do not run this week (e.g. no battery built)
        ax.stackplot(d.index, [d[c] for c in d.columns], colors=[PALETTE[c] for c in d.columns],
                     labels=[LABELS[c] for c in d.columns], linewidth=0)
        load = n.get_switchable_as_dense("Load", "p_set").sum(axis=1).loc[window] / 1e3
        ax.plot(load.index, load.values, color=INK, linewidth=1.5, label="Load before shifting")
        shift = n.storage_units.index[n.storage_units.carrier == "demand_shift"]
        if len(shift):  # shift unit dispatch = load moved away from this hour
            served = load - n.storage_units_t.p[shift].sum(axis=1).loc[window] / 1e3
            ax.plot(served.index, served.values, color=INK, linewidth=1.5, linestyle=(0, (2, 1.5)),
                    label="Load after shifting")
        style_axis(ax, titles[s], "GW" if s == "S0" else "")
        ax.tick_params(axis="x", labelsize=7.5)
        ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%d %b"))
    handles, names = axes[1].get_legend_handles_labels()
    fig.legend(handles, names, ncol=8, frameon=False, loc="lower left", bbox_to_anchor=(0.01, 0.04), fontsize=8)
    add_source(fig, SOURCE + "; weather year 2013, times in UTC")
    save(fig, "7_dispatch_peak_week")


METRICS = [("cost_eur_per_mwh", "System cost", "EUR per MWh saved", "{:.0f}"),
           ("co2_t_per_mwh", "CO2", "t per MWh saved", "{:.2f}"),
           ("gas_mwh_th_per_mwh", "Gas burnt", "MWh of gas per MWh saved", "{:.2f}"),
           ("capacity_mw_per_twh", "New capacity", "MW per TWh saved", "{:.0f}")]


def avoided(avoided_df: pd.DataFrame, labels: dict) -> None:
    """The headline: what each MWh saved avoids, one panel per metric, one bar per comparison."""
    rows = [s for s in ORDER if s in avoided_df.index][::-1]  # top to bottom in ORDER
    fig, axes = plt.subplots(1, 4, figsize=(13, 5), sharey=True, facecolor="white")
    fig.subplots_adjust(left=0.16, bottom=0.14, wspace=0.12, top=0.84)
    for ax, (col, title, unit, fmt) in zip(axes, METRICS):
        v = avoided_df.loc[rows, col]
        ax.barh(range(len(rows)), v, 0.6, color=SINGLE)
        for i, x in enumerate(v):
            ax.text(x, i, " " + fmt.format(x), va="center", fontsize=8, color=INK)
        ax.set_xlim(0, v.max() * 1.25)
        style_axis(ax, title, unit, grid="x")
    axes[0].set_yticks(range(len(rows)),
                       [f"{s} vs {avoided_df.at[s, 'reference']}\n" + labels[s].split("\n", 1)[1].replace("\n", " ")
                        for s in rows],
                       fontsize=8)
    fig.suptitle("What each MWh of electricity saved avoids in 2030", x=0.01, ha="left", fontsize=13, color=INK)
    add_source(fig, SOURCE + "; each scenario is compared with its reference at the same gas price")
    save(fig, "8_avoided_per_mwh")


def headline(avoided_df: pd.DataFrame) -> None:
    """The answer in one picture: what one MWh saved avoids (S1-15 against S0), as four big numbers."""
    a = avoided_df.loc["S1-15"]
    tiles = [(f"{a['cost_eur_per_mwh']:.0f} EUR", "of power-system cost"),
             (f"{a['gas_mwh_th_per_mwh']:.2f} MWh", "of gas not burnt"),
             (f"{a['co2_t_per_mwh']:.2f} t", "of CO2 not emitted"),
             (f"{a['capacity_mw_per_twh']:.0f} MW", "less new capacity\nper TWh saved per year")]
    fig = plt.figure(figsize=(12, 4), facecolor="white")
    fig.text(0.03, 0.88, "Every MWh Tunisia does not use in 2030 saves", fontsize=18, color=INK, weight="bold")
    fig.text(0.03, 0.79, "Saving 15% of demand in every hour (scenario S1-15) against the base case (S0)",
             fontsize=11, color=INK_2)
    for i, (value, label) in enumerate(tiles):
        x = 0.03 + i * 0.24
        fig.patches.append(matplotlib.patches.FancyBboxPatch(
            (x, 0.14), 0.215, 0.56, boxstyle="round,pad=0,rounding_size=0.02", transform=fig.transFigure,
            facecolor="#eef3f4", edgecolor="none"))
        fig.text(x + 0.02, 0.48, value, fontsize=32, color=SINGLE, weight="bold")
        fig.text(x + 0.02, 0.36, label, fontsize=12, color=INK, va="top")
    add_source(fig, SOURCE + "; numbers from results/avoided.csv")
    save(fig, "0_headline")


def uniform_vs_cooling(avoided_df: pd.DataFrame) -> None:
    """The same 15% of energy saved evenly (S1-15) or from summer cooling first (S1-15C)."""
    fig, axes = plt.subplots(1, 4, figsize=(12, 4), facecolor="white")
    fig.subplots_adjust(bottom=0.16, wspace=0.35, top=0.8)
    for ax, (col, title, unit, fmt) in zip(axes, METRICS):
        v = avoided_df.loc[["S1-15", "S1-15C"], col]
        ax.bar([0, 1], v, 0.6, color=LINE_COLOURS[:2])
        for i, y in enumerate(v):
            ax.text(i, y, fmt.format(y), ha="center", va="bottom", fontsize=8, color=INK)
        ax.set_xticks([0, 1], ["Every hour\n(S1-15)", "Cooling first\n(S1-15C)"], fontsize=8)
        style_axis(ax, title, unit)
    fig.suptitle("Saving 15% evenly vs from summer cooling first (per MWh saved, vs S0)",
                 x=0.01, ha="left", fontsize=13, color=INK)
    add_source(fig, SOURCE)
    save(fig, "9_uniform_vs_cooling")


PATHWAY_LINES = [("S0", "No extra saving"), ("S1-15", "Save 15% by 2030"), ("S1-20", "Save 20% by 2030")]


def pathway_share(ps: pd.DataFrame, history: pd.DataFrame, target: float) -> None:
    """Renewable share year by year on the realistic pathway (2025-2026 shared history), against the 35% target."""
    fig, ax = new_figure(10, 4.8)
    for colour, (s, label) in zip(LINE_COLOURS, PATHWAY_LINES):
        d = pd.concat([history, ps[ps.scenario == s]]).sort_values("year")
        ax.plot(d.year, d.res_share * 100, color=colour, linewidth=2.5, marker="o", label=label)
        ax.text(d.year.iloc[-1] + 0.08, d.res_share.iloc[-1] * 100, f"{d.res_share.iloc[-1]:.0%}", va="center", fontsize=9, color=INK)
    ax.axhline(target * 100, color=INK, linewidth=1.5, linestyle=(0, (5, 4)))
    ax.text(history.year.min(), target * 100 + 0.8, f"Target: {target:.0%} by 2030", fontsize=9, color=INK)
    ax.axvspan(history.year.min() - 0.3, history.year.max() + 0.3, color="#eef3f4", zorder=0)
    ax.text(history.year.mean(), 1.5, "history (base case)", ha="center", fontsize=8, color=INK_2)
    ax.set_xticks(range(int(history.year.min()), int(ps.year.max()) + 1)); ax.set_ylim(0, target * 100 + 6)
    ax.legend(frameon=False, loc="lower right")
    finish_figure(fig, ax, "Renewable share of generation, built at Tunisia's demonstrated pace", "% of domestic generation",
                  SOURCE + "; build limits in the register (pathway_*)")
    save(fig, "10_pathway_res_share")


def pathway_capacity(ps: pd.DataFrame, scen: str = "S0") -> None:
    """How the fleet grows year by year on the pathway (installed capacity, GW)."""
    d = ps[ps.scenario == scen].sort_values("year").set_index("year")
    cap = pd.DataFrame({c: d.get(f"cap_{c}_mw", 0.0) for c in STACK_ORDER}).fillna(0)
    cap["hydro"] += d.get("cap_ror_mw", 0.0)
    fig, ax = new_figure(10, 4.8)
    bottom = pd.Series(0.0, index=cap.index)
    for c in [c for c in STACK_ORDER if cap[c].sum() > 0]:
        ax.bar(cap.index, cap[c] / 1e3, 0.55, bottom=bottom, color=PALETTE[c], edgecolor="white", linewidth=1, label=LABELS[c])
        bottom += cap[c] / 1e3
    for y, t in bottom.items():
        ax.text(y, t, f"{t:.1f}", ha="center", va="bottom", fontsize=9, color=INK)
    ax.set_xticks(cap.index)
    ax.legend(ncol=6, frameon=False, loc="upper left", bbox_to_anchor=(0, -0.1), fontsize=8)
    fig.subplots_adjust(bottom=0.24)
    finish_figure(fig, ax, f"Installed capacity year by year on the pathway ({scen}, no extra saving)", "GW", SOURCE)
    save(fig, "11_pathway_capacity")


def pathway_avoided(pa: pd.DataFrame, avoided_df: pd.DataFrame, scen: str = "S1-15") -> None:
    """What one MWh saved avoids each year on the pathway, against the unconstrained 2030 run (dashed)."""
    d = pa[(pa.scenario == scen) & (pa.year != "2027-2030")].astype({"year": int}).sort_values("year")
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.2), facecolor="white")
    fig.subplots_adjust(bottom=0.16, wspace=0.3, top=0.8)
    for ax, (col, title, unit, fmt) in zip(axes, METRICS[:3]):
        ax.plot(d.year, d[col], color=LINE_COLOURS[0], linewidth=2.5, marker="o", label="Built at Tunisia's pace")
        for x, v in zip(d.year, d[col]):
            ax.text(x, v, fmt.format(v) + "\n", ha="center", va="bottom", fontsize=8, color=INK)
        ax.axhline(avoided_df.at[scen, col], color=INK_2, linewidth=1.5, linestyle=(0, (5, 4)), label="2030 with no build limit")
        ax.set_ylim(0, max(d[col].max(), avoided_df.at[scen, col]) * 1.35)
        ax.set_xticks(d.year)
        style_axis(ax, title, unit)
    axes[0].legend(frameon=False, loc="lower left", fontsize=8)
    fig.suptitle(f"What each MWh saved avoids, year by year ({scen} against S0)", x=0.01, ha="left", fontsize=13, color=INK)
    add_source(fig, SOURCE + "; dashed: the 2030 run with no build limit (results/avoided.csv)")
    save(fig, "12_pathway_avoided")


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    reg = load_register(Path("data/assumptions_register.xlsx"))
    labels = scenario_labels(reg)
    summary = pd.read_csv(RESULTS / "summary.csv", index_col="scenario").loc[ORDER]
    avoided_df = pd.read_csv(RESULTS / "avoided.csv", index_col="scenario")
    networks = {s: pypsa.Network(str(RESULTS / "networks" / f"{s}_solved.nc")) for s in ORDER}

    headline(avoided_df)
    capacity_mix(summary, labels)
    generation_mix(networks, labels)
    single_bars(summary["gas_use_twh_th"], labels, "Gas burnt for power in 2030", "TWh of gas (thermal) per year",
                "3_gas_use", "{:.1f}")
    single_bars(summary["system_cost_meur"], labels,
                "Annual system cost in 2030, investment + operation (includes existing plants: compare differences)",
                "million EUR per year", "4_system_cost", "{:.0f}")
    single_bars(summary["co2_mt"], labels, "CO2 from power generation in 2030", "Mt CO2 per year", "5_co2", "{:.2f}")
    price_duration(networks)
    dispatch_week(networks)
    avoided(avoided_df, labels)
    uniform_vs_cooling(avoided_df)
    if (RESULTS / "pathway_summary.csv").exists():
        ps, pa = pd.read_csv(RESULTS / "pathway_summary.csv"), pd.read_csv(RESULTS / "pathway_avoided.csv")
        history = pd.DataFrame([{"year": y, "res_share": res_share(pypsa.Network(str(RESULTS / "pathway" / f"history_{y}_solved.nc")))}
                                for y in (2025, 2026)])
        pathway_share(ps, history, reg["re_target_2030"])
        pathway_capacity(ps)
        pathway_avoided(pa, avoided_df)


if __name__ == "__main__":
    main()
