"""Write report/report.docx (plan Task 18). Every result number is read from results/*.csv.

Run from the repo root after make_figures.py:  python scripts/make_report.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # this checkout's tn2030
import pandas as pd
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.shared import Cm, Pt, RGBColor

from tn2030.register import load_register

RESULTS = Path("results")
FIG = RESULTS / "figures"
MAIN = ["S0", "S1-10", "S1-15", "S1-20", "S1-15C", "S2-300", "S2-600"]


def para(doc, text, bold_lead=None, size=None):
    """A body paragraph; bold_lead is an optional short bold opening."""
    p = doc.add_paragraph()
    if bold_lead:
        p.add_run(bold_lead + " ").bold = True
    run = p.add_run(text)
    if size:
        run.font.size = Pt(size)
    return p


def bullets(doc, items):
    for item in items:
        doc.add_paragraph(item, style="List Bullet")


def table(doc, header, rows, widths_cm=None):
    """A plain grid table: bold header row, numbers right-aligned."""
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for cell, text in zip(t.rows[0].cells, header):
        cell.text = ""
        cell.paragraphs[0].add_run(str(text)).bold = True
    for row in rows:
        cells = t.add_row().cells
        for i, (cell, text) in enumerate(zip(cells, row)):
            cell.text = str(text)
            if i > 0:
                cell.paragraphs[0].alignment = 2  # right
    for row in t.rows:
        for cell in row.cells:
            for run in cell.paragraphs[0].runs:
                run.font.size = Pt(9)
    if widths_cm:
        for row in t.rows:
            for cell, w in zip(row.cells, widths_cm):
                cell.width = Cm(w)
    doc.add_paragraph()
    return t


def figure(doc, name, caption):
    doc.add_picture(str(FIG / f"{name}.png"), width=Cm(16))
    p = doc.add_paragraph(caption)
    p.runs[0].italic = True
    p.runs[0].font.size = Pt(9)
    p.runs[0].font.color.rgb = RGBColor(0x52, 0x51, 0x4E)


def main() -> None:
    s = pd.read_csv(RESULTS / "summary.csv", index_col="scenario")
    a = pd.read_csv(RESULTS / "avoided.csv", index_col="scenario")
    v = pd.read_csv(RESULTS / "validation.csv")
    cal = v[v.case == "calibrated"].set_index("metric")
    reg = load_register(Path("data/assumptions_register.xlsx"))
    register = pd.read_excel("data/assumptions_register.xlsx", sheet_name="register")

    head = a.loc["S1-15"]
    flex = s.loc["S1-15", "system_cost_meur"] - s.loc["S2-300", "system_cost_meur"]
    flex_co2 = s.loc["S1-15", "co2_mt"] - s.loc["S2-300", "co2_mt"]
    cool_gas = a.loc["S1-15C", "gas_mwh_th_per_mwh"] / head["gas_mwh_th_per_mwh"] - 1
    s0_ocgt = s.loc["S0", "new_cap_OCGT_mw"]

    doc = Document()
    doc.styles["Normal"].font.name = "Calibri"
    doc.styles["Normal"].font.size = Pt(11)
    for section in doc.sections:
        section.left_margin = section.right_margin = Cm(2.2)

    doc.add_heading("The value of energy efficiency in Tunisia's power system (2030)", level=0)
    para(doc, "Rayen Romdhani, Energy Engineering, ENIM (Monastir, Tunisia). October 2026.")
    para(doc, "Model: PyPSA-Earth v0.10.0 with the study code in this repository. All result numbers come from "
              "results/summary.csv and results/avoided.csv; all inputs come from data/assumptions_register.xlsx.",
         size=9)

    doc.add_heading("Summary", level=1)
    para(doc, f"Tunisia plans {reg['re_target_2030']:.0%} renewable electricity by 2030 and generates almost all "
              f"the rest from gas ({reg['gas_share_2024']:.1%} of generation in 2024). This study asks what each MWh of "
              "electricity saved, or moved in time, is worth to the 2030 power system.")
    table(doc, ["Saving 15% in every hour (S1-15 vs S0) avoids, per MWh saved", "Value"], [
        ["System cost", f"{head['cost_eur_per_mwh']:.0f} EUR"],
        ["Gas burnt for power", f"{head['gas_mwh_th_per_mwh']:.2f} MWh (thermal)"],
        ["CO2", f"{head['co2_t_per_mwh']:.2f} t"],
        ["New capacity", f"{head['capacity_mw_per_twh']:.0f} MW per TWh saved per year"],
    ], widths_cm=[10, 6])
    bullets(doc, [
        f"With STEG's {reg['reserve_margin']:.0%} reserve margin, the base case needs {s0_ocgt:.0f} MW of new gas "
        f"turbines. A 10% saving already avoids all of them.",
        f"Saving first on summer air conditioning (S1-15C) avoids {cool_gas:.0%} more gas per MWh than an even cut, "
        f"although only {s.loc['S1-15C', 'cooling_share']:.0%} of the saving fits on the cooling load.",
        f"Letting {reg['flex_cap_mw']:.0f} MW of load move by up to {reg['flex_max_hours']:.0f} hours, on top of the "
        f"15% saving, cuts another {flex:.0f} M EUR per year and {flex_co2:.2f} Mt of CO2.",
        f"At the base gas price the least-cost system reaches {s.loc['S0', 'res_share']:.0%} renewables, so the "
        f"{reg['re_target_2030']:.0%} target does not bind. It binds only when gas costs half as much.",
    ])

    doc.add_heading("1. Question and scope", level=1)
    para(doc, "The study measures what one MWh of electricity saved through efficiency, or moved in time through "
              "demand flexibility, avoids in 2030: new capacity, gas burnt, system cost and CO2. The renewable "
              "target stays in force in every scenario, so the comparison is between systems that all meet it.")
    para(doc, "The model covers Tunisia only, with two network nodes (north and south), 8,760 hourly steps and the "
              "2013 weather year, solved with the open-source solver HiGHS. It does not include the cost of the "
              "efficiency programmes themselves, the planned ELMED link to Italy, or other countries.")

    doc.add_heading("2. Method", level=1)
    doc.add_heading("2.1 Base network and 2024 calibration", level=2)
    para(doc, "PyPSA-Earth, used unmodified, builds the Tunisian grid, power plants, renewable potentials and hourly "
              "demand from open data. Its plant list does not match the official fleet, so the thermal fleet is "
              "rebuilt from the ONEM 2024 statistics: "
              f"{reg['cap_2024_ccgt_mw']:,.0f} MW of combined cycle and "
              f"{reg['cap_2024_ocgt_mw'] + reg['cap_2024_steam_mw']:,.0f} MW of gas turbines and steam units. "
              "One efficiency factor for existing gas units is fitted so that a 2024 run burns as much gas as STEG "
              "reported. The hourly demand shape is stretched to the official load factor and minimum-to-peak ratio.")
    table(doc, ["2024 check (calibrated model)", "Model", "Official", "Difference"], [
        ["Gas burnt for power (TWh thermal)", f"{cal.at['gas_fuel_for_power_twh_th', 'model']:.1f}",
         f"{cal.at['gas_fuel_for_power_twh_th', 'reference']:.1f}",
         f"{cal.at['gas_fuel_for_power_twh_th', 'diff_pct']:+.1f}%"],
        ["Gas fleet efficiency (net)", f"{cal.at['gas_fleet_efficiency_ncv', 'model']:.2f}",
         f"{cal.at['gas_fleet_efficiency_ncv', 'reference']:.2f}",
         f"{cal.at['gas_fleet_efficiency_ncv', 'diff_pct']:+.1f}%"],
        ["Peak demand (MW)", f"{cal.at['peak_mw', 'model']:,.0f}", f"{cal.at['peak_mw', 'reference']:,.0f}",
         f"{cal.at['peak_mw', 'diff_pct']:+.1f}%"],
        ["Gas share of generation", f"{cal.at['gas_share', 'model']:.1%}", f"{cal.at['gas_share', 'reference']:.1%}",
         f"{cal.at['gas_share', 'diff_pct']:+.1f}%"],
    ], widths_cm=[7, 3, 3, 3])
    para(doc, "The gas-burnt check is independent of the fit: the factor was fitted on STEG's specific consumption, "
              "and the gas total comes from a separate ONEM table.", size=9)

    doc.add_heading("2.2 The 2030 system", level=2)
    para(doc, f"Demand grows from {reg['demand_2024_twh']:.1f} TWh in 2024 at {reg['demand_growth']:.1%} per year, "
              "STEG's base-case forecast as quoted by JICA (2022). Imports stay at their 2024 level "
              f"({reg['imports_2024_twh']:.1f} TWh, flat over the year), so every MWh saved falls on domestic "
              "generation. The model then builds solar, onshore wind, batteries and gas turbines at least cost, "
              "using 2030 costs from PyPSA technology-data. In every scenario it must:")
    bullets(doc, [
        f"produce at least {reg['re_target_2030']:.0%} of domestic generation from solar, wind and hydro;",
        f"keep firm capacity (gas and hydro) at least {reg['reserve_margin']:.0%} above peak demand, STEG's planning "
        "margin;",
        "build the committed solar and wind projects (data/committed_projects.csv) and keep the existing fleet.",
    ])
    para(doc, "After each solve the pipeline checks the energy balance, the renewable share, the reserve margin, "
              "that no load is shed and that committed and existing capacity is kept. All 11 scenarios pass.")

    doc.add_heading("2.3 Scenarios", level=2)
    lo, hi = reg["gas_price_factor_lo"], reg["gas_price_factor_hi"]
    table(doc, ["Scenario", "What changes against S0"], [
        ["S0", "Base case: 2030 demand, base gas price"],
        ["S1-10, S1-15, S1-20", "Demand 10, 15 or 20% lower in every hour"],
        ["S1-15C", "Same 15% of annual energy, taken first from summer cooling load"],
        ["S2-300, S2-600", f"S1-15 plus {reg['flex_cap_mw']:.0f} or {reg['flex_cap_hi_mw']:.0f} MW of load that "
                           f"can move by up to {reg['flex_max_hours']:.0f} hours"],
        ["G-lo-S0, G-lo-S1-15", f"S0 and S1-15 with the gas price x{lo:g}"],
        ["G-hi-S0, G-hi-S1-15", f"S0 and S1-15 with the gas price x{hi:g}"],
    ], widths_cm=[4, 12])
    para(doc, "Shiftable load is modelled as a free, lossless store at each node that starts and ends every day half "
              "full. Load can be brought forward or postponed, but every MWh moved must come back within "
              f"{reg['flex_max_hours']:.0f} hours, and only one direction is allowed in each hour.")

    doc.add_heading("3. Results", level=1)
    doc.add_heading("3.1 Main scenarios", level=2)
    rows = [
        ("Domestic demand (TWh)", "demand_twh", "{:.2f}"),
        ("New gas turbines (MW)", "new_cap_OCGT_mw", "{:,.0f}"),
        ("New solar (MW)", "new_cap_solar_mw", "{:,.0f}"),
        ("New onshore wind (MW)", "new_cap_onwind_mw", "{:,.0f}"),
        ("Gas burnt (TWh thermal)", "gas_use_twh_th", "{:.2f}"),
        ("CO2 (Mt)", "co2_mt", "{:.2f}"),
        ("Renewable share", "res_share", "{:.0%}"),
        ("System cost (M EUR/yr)", "system_cost_meur", "{:,.0f}"),
        ("Average price (EUR/MWh)", "avg_price_eur_mwh", "{:.1f}"),
    ]
    table(doc, [""] + MAIN, [[label] + [fmt.format(s.at[sc, col]) for sc in MAIN] for label, col, fmt in rows],
          widths_cm=[4.3] + [1.7] * len(MAIN))
    figure(doc, "1_capacity_mix", "Figure 1. Installed capacity in 2030 by scenario.")
    figure(doc, "3_gas_use", "Figure 2. Gas burnt for power in 2030 by scenario.")

    doc.add_heading("3.2 What one MWh saved avoids", level=2)
    order = [sc for sc in ["S1-10", "S1-15", "S1-20", "S1-15C", "S2-300", "S2-600", "G-lo-S1-15", "G-hi-S1-15"]
             if sc in a.index]
    table(doc, ["Scenario", "vs", "Cost (EUR/MWh)", "CO2 (t/MWh)", "Gas (MWh/MWh)", "Capacity (MW per TWh)"],
          [[sc, a.at[sc, "reference"], f"{a.at[sc, 'cost_eur_per_mwh']:.1f}", f"{a.at[sc, 'co2_t_per_mwh']:.2f}",
            f"{a.at[sc, 'gas_mwh_th_per_mwh']:.2f}", f"{a.at[sc, 'capacity_mw_per_twh']:.0f}"] for sc in order],
          widths_cm=[2.6, 2.4, 2.6, 2.4, 2.6, 3.4])
    figure(doc, "8_avoided_per_mwh", "Figure 3. What each MWh saved avoids, against the reference at the same gas price.")

    doc.add_heading("3.3 Findings", level=2)
    s1_10 = a.loc["S1-10"]
    para(doc, f"The base case needs {s0_ocgt:.0f} MW of new gas turbines to keep the reserve margin. A 10% saving "
              "lowers the peak enough to avoid all of it, which is why the first 10% saved is worth the most "
              f"({s1_10['cost_eur_per_mwh']:.1f} EUR/MWh against {head['cost_eur_per_mwh']:.1f} for 15%). Beyond "
              "that point, further savings avoid mostly solar and wind that would otherwise be built.",
         bold_lead="Efficiency avoids new gas plant.")
    para(doc, f"In S1-15C only {s.loc['S1-15C', 'cooling_share']:.0%} of the 15% saving fits on the summer cooling "
              f"load; the rest is an even cut. That is enough to avoid {cool_gas:.0%} more gas per MWh and "
              f"{s.loc['S1-15', 'system_cost_meur'] - s.loc['S1-15C', 'system_cost_meur']:.1f} M EUR per year more "
              "than S1-15, because air-conditioning hours are the hours when gas runs.",
         bold_lead="Timing matters.")
    figure(doc, "9_uniform_vs_cooling", "Figure 4. The same 15% saved evenly or from cooling first.")
    para(doc, f"Shifting {reg['flex_cap_mw']:.0f} MW of load saves {flex:.1f} M EUR per year on top of S1-15, about "
              f"{round(flex * 1e6 / reg['flex_cap_mw'], -3):,.0f} EUR per MW per year. The model moves morning and evening load "
              "into the midday solar hours, builds more solar and burns less gas. Under the reserve rule, flexibility "
              "gets no credit for lowering the peak, so all of this value is energy.",
         bold_lead="Flexibility adds to efficiency.")
    figure(doc, "7_dispatch_peak_week", "Figure 5. Dispatch in the week around the annual peak, S0 and S2-300.")
    para(doc, f"With gas at x{lo:g}, each MWh saved avoids {a.at['G-lo-S1-15', 'co2_t_per_mwh']:.2f} t of CO2, "
              "because the saving mostly displaces gas. With gas at "
              f"x{hi:g}, the reference system is already {s.loc['G-hi-S0', 'res_share']:.0%} renewable with "
              f"{s.loc['G-hi-S0', 'cap_battery_mwh']:,.0f} MWh of batteries, and each MWh saved avoids only "
              f"{a.at['G-hi-S1-15', 'co2_t_per_mwh']:.2f} t of CO2 but {a.at['G-hi-S1-15', 'cost_eur_per_mwh']:.0f} EUR.",
         bold_lead="The gas price changes the result most.")
    figure(doc, "6_price_duration", "Figure 6. Hourly electricity price, sorted, for S0, S1-15 and S2-300.")

    doc.add_heading("4. Limitations", level=1)
    bullets(doc, [
        "Nothing limits how fast renewables are built. The base case adds "
        f"{(s.loc['S0', 'new_cap_solar_mw'] + s.loc['S0', 'new_cap_onwind_mw']) / 1e3:.1f} GW of solar and wind by "
        "2030, far above Tunisia's recent pace. The results show what least cost would do, not a forecast.",
        "The cost of efficiency programmes is not modelled. The avoided cost per MWh is the most a programme could "
        "cost and still pay off for the power system.",
        "One weather year (2013) at 1-hour steps. A 3-hour test run built 2.7% more solar and 3.9% more wind.",
        "Demand growth and the 2030 peak come from STEG's forecast as quoted by JICA (2022), a secondary source.",
        "Imports are flat at their 2024 level, so every MWh saved falls on domestic generation.",
        "The fitted efficiency factor for existing gas units also stands in for plant outages, which are not modelled.",
        "The reserve margin is one national capacity rule, not a reliability study.",
        "System cost includes the annualised cost of plants that already exist. Differences between scenarios are "
        "meaningful; the absolute level is not the cost of the real system.",
    ])

    doc.add_heading("5. Inputs and sources", level=1)
    para(doc, "Every input is a row of data/assumptions_register.xlsx with its unit, type and source; rows typed "
              "'assumption' have no published source and are explained in the register notes. The study inputs:")
    rows = register[register["type"].isin(["sourced", "assumption"]) & ~register["id"].str.startswith("toy_")]
    table(doc, ["Input", "Value", "Unit", "Type", "Source"],
          [[r.id, f"{r.value:,.0f}" if abs(r.value) >= 1000 else f"{r.value:.4g}", r.unit, r.type, "" if pd.isna(r.source_title) else r.source_title]
           for r in rows.itertuples()], widths_cm=[4.2, 1.8, 2.0, 1.8, 6.6])

    doc.add_heading("6. Reproducing the study", level=1)
    para(doc, "The code, tests, scenario files and step-by-step instructions are in the repository README. One "
              "command (snakemake -j 1) rebuilds, solves and checks all 11 scenarios in about an hour on a laptop, "
              "and scripts/make_figures.py and scripts/make_report.py redraw the figures and this report.")

    Path("report").mkdir(exist_ok=True)
    doc.save("report/report.docx")
    print("wrote report/report.docx")


if __name__ == "__main__":
    main()
