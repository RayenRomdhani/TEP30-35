"""Write report/deck.pptx, an 8-slide summary of the study (plan Task 18). Numbers are read from results/*.csv.

Run from the repo root after make_figures.py:  python scripts/make_deck.py
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # this checkout's tn2030
import pandas as pd
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from tn2030.register import load_register
from tn2030.scenario import load_scenario

AUTHOR = "Rayen Romdhani"
TITLE = "The value of energy efficiency in Tunisia's power system"
FIG = Path("results/figures")
DARK, SUN, INK, MUTED, TINT, WHITE = "17323B", "EDA100", "1F1F1F", "6B6A66", "EEF3F4", "FFFFFF"
HEAD, BODY = "Cambria", "Calibri"
SOURCE = "Source: own PyPSA-Earth model of Tunisia 2030; inputs in data/assumptions_register.xlsx"


def rgb(hex_colour):
    return RGBColor.from_string(hex_colour)


def text(slide, x, y, w, h, content, size=16, colour=INK, bold=False, font=BODY, align=PP_ALIGN.LEFT):
    """A text box; content is one string or a list of paragraphs."""
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = box.text_frame
    frame.word_wrap = True
    for i, line in enumerate([content] if isinstance(content, str) else content):
        p = frame.paragraphs[0] if i == 0 else frame.add_paragraph()
        p.alignment = align
        p.space_after = Pt(8)
        run = p.add_run()
        run.text = line
        run.font.size, run.font.bold, run.font.name = Pt(size), bold, font
        run.font.color.rgb = rgb(colour)
    return box


def background(slide, colour):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = rgb(colour)


def title(slide, words, colour=INK):
    text(slide, 0.6, 0.4, 12.1, 1.0, words, size=32, colour=colour, bold=True, font=HEAD)


def footer(slide, colour=MUTED):
    text(slide, 0.6, 7.0, 12.1, 0.35, SOURCE, size=10, colour=colour)


def stat(slide, x, y, w, value, label, value_colour=DARK, label_colour=INK):
    """A big number with a short label below it."""
    text(slide, x, y, w, 0.9, value, size=36, colour=value_colour, bold=True, font=HEAD)
    text(slide, x, y + 0.9, w, 0.9, label, size=14, colour=label_colour)


def card(slide, x, y, w, h):
    """A light tinted panel behind a group of text (no border, no stripe)."""
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.adjustments[0] = 0.06
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb(TINT)
    shape.line.fill.background()
    shape.shadow.inherit = False
    return shape


def picture(slide, name, x, y, w):
    """A figure at a given width, height from its aspect ratio; returns the height in inches."""
    path = FIG / f"{name}.png"
    with Image.open(path) as im:
        h = w * im.height / im.width
    slide.shapes.add_picture(str(path), Inches(x), Inches(y), Inches(w), Inches(h))
    return h


def main() -> None:
    s = pd.read_csv("results/summary.csv", index_col="scenario")
    a = pd.read_csv("results/avoided.csv", index_col="scenario")
    reg = load_register(Path("data/assumptions_register.xlsx"))
    head = a.loc["S1-15"]
    flex = s.loc["S1-15", "system_cost_meur"] - s.loc["S2-300", "system_cost_meur"]
    flex_co2 = s.loc["S1-15", "co2_mt"] - s.loc["S2-300", "co2_mt"]
    cool_gas = a.loc["S1-15C", "gas_mwh_th_per_mwh"] / head["gas_mwh_th_per_mwh"] - 1
    cal = pd.read_csv("results/validation.csv").query("case == 'calibrated'").set_index("metric")
    target, reserve = f"{reg['re_target_2030']:.0%}", f"{reg['reserve_margin']:.0%}"
    lo, hi = reg["gas_price_factor_lo"], reg["gas_price_factor_hi"]
    scenarios = [load_scenario(p) for p in sorted(Path("config/scenarios").glob("*.yaml"))]
    cuts = sorted({sc["efficiency"]["share"] for sc in scenarios
                   if sc["efficiency"]["mode"] == "uniform" and sc["efficiency"]["share"] > 0})
    # Slide 4's title says the smallest cut avoids all new gas turbines; stop if a re-run changes that.
    assert s.loc["S1-10", "new_cap_OCGT_mw"] < 0.5, "S1-10 builds new OCGT: rewrite slide 4"

    deck = Presentation()
    props = deck.core_properties  # otherwise the file names the python-pptx template's author
    props.author = props.last_modified_by = AUTHOR
    props.title, props.comments = TITLE, ""
    props.created = props.modified = datetime.now()
    deck.slide_width, deck.slide_height = Inches(13.333), Inches(7.5)
    blank = deck.slide_layouts[6]

    # 1. Title
    sl = deck.slides.add_slide(blank)
    background(sl, DARK)
    text(sl, 0.8, 2.0, 11.5, 1.8, TITLE, size=44, colour=WHITE, bold=True, font=HEAD)
    text(sl, 0.8, 3.9, 11.5, 0.6, f"What each MWh saved avoids in 2030, under the {target} renewable target",
         size=22, colour=SUN)
    text(sl, 0.8, 5.6, 11.5, 0.9, [f"{AUTHOR}, Energy Engineering, ENIM (Monastir, Tunisia)",
                                   "PyPSA-Earth capacity-expansion model, 2 nodes, 8,760 hours"], size=16, colour=WHITE)
    sl.notes_slide.notes_text_frame.text = (
        f"Tunisia generates almost all its electricity from gas and plans {target} renewables by 2030. "
        "This study asks what saving electricity, or moving it in time, is worth to that system.")

    # 2. Answer first
    sl = deck.slides.add_slide(blank)
    title(sl, f"Each MWh saved avoids about {head['cost_eur_per_mwh']:.0f} EUR of system cost")
    text(sl, 0.6, 1.4, 12.1, 0.6, "Saving 15% of 2030 demand in every hour (S1-15 against the base case S0), per MWh saved:",
         size=18, colour=MUTED)
    stats = [(f"{head['cost_eur_per_mwh']:.0f} EUR", "of system cost (investment + operation)"),
             (f"{head['gas_mwh_th_per_mwh']:.2f} MWh", "of gas burnt for power"),
             (f"{head['co2_t_per_mwh']:.2f} t", "of CO2"),
             (f"{head['capacity_mw_per_twh']:.0f} MW", "of new capacity per TWh saved per year")]
    for i, (value, label) in enumerate(stats):
        card(sl, 0.6 + i * 3.1, 2.5, 2.8, 2.6)
        stat(sl, 0.8 + i * 3.1, 2.8, 2.4, value, label)
    text(sl, 0.6, 5.5, 12.1, 1.2,
         f"The avoided cost is close to the average power price ({s.loc['S0', 'avg_price_eur_mwh']:.0f} EUR/MWh) plus "
         "the gas turbines the saving makes unnecessary.", size=16)
    footer(sl)
    sl.notes_slide.notes_text_frame.text = (
        f"The headline metric compares two least-cost 2030 systems that both meet the {target} target and a {reserve} "
        "reserve margin. The only difference is demand.")

    # 3. Method
    sl = deck.slides.add_slide(blank)
    title(sl, "An open model, calibrated to 2024, then solved for 2030")
    steps = [("1", "Base network", "PyPSA-Earth builds Tunisia's grid, plants, solar and wind potential and hourly "
                                   "demand from open data"),
             ("2", "2024 calibration", "Official ONEM fleet; one efficiency factor fitted so gas burnt matches "
                                       f"STEG within {abs(cal.at['gas_fuel_for_power_twh_th', 'diff_pct']):.1f}%"),
             ("3", f"{len(s)} scenarios", f"Demand cut {cuts[0]:.0%}-{cuts[-1]:.0%}, cooling-first saving, "
                                          f"shiftable load, gas price x{lo:g} and x{hi:g}"),
             ("4", "Least-cost 2030", f"New solar, wind, batteries and gas; at least {target} renewable and "
                                      f"{reserve} reserve in every run")]
    for i, (num, head_text, body) in enumerate(steps):
        x = 0.6 + i * 3.1
        circle = sl.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(1.9), Inches(0.8), Inches(0.8))
        circle.fill.solid()
        circle.fill.fore_color.rgb = rgb(DARK)
        circle.line.fill.background()
        circle.text_frame.text = num
        run = circle.text_frame.paragraphs[0].runs[0]
        run.font.size, run.font.bold, run.font.color.rgb = Pt(24), True, rgb(WHITE)
        circle.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
        text(sl, x, 2.9, 2.8, 0.6, head_text, size=20, bold=True, font=HEAD)
        text(sl, x, 3.5, 2.8, 2.4, body, size=15)
    text(sl, 0.6, 6.0, 12.1, 0.7, "Every input number has a row and a source in the assumptions register. "
                                  f"All {len(s)} runs pass the post-solve checks.", size=15, colour=MUTED)
    footer(sl)
    sl.notes_slide.notes_text_frame.text = (
        "Calibration matters because PyPSA-Earth's open plant list overstated combined-cycle capacity and missed "
        "the gas turbines. After the fix the 2024 model matches official capacity, gas burnt and peak.")

    # 4. Capacity
    sl = deck.slides.add_slide(blank)
    s0_ocgt = s.loc["S0", "new_cap_OCGT_mw"]
    title(sl, f"A {cuts[0]:.0%} saving removes the need for new gas plant")
    picture(sl, "1_capacity_mix", 0.4, 1.5, 8.6)
    card(sl, 9.3, 1.6, 3.5, 4.6)
    stat(sl, 9.5, 1.8, 3.1, f"{s0_ocgt:.0f} MW", "of new gas turbines in the base case, to keep a "
                                                  f"{reg['reserve_margin']:.0%} reserve above the peak")
    text(sl, 9.5, 3.9, 3.1, 2.2, "Every efficiency scenario avoids all of it. Further savings then avoid "
                                 "mostly solar and wind that would otherwise be built.", size=15)
    footer(sl)
    sl.notes_slide.notes_text_frame.text = (
        f"This is why the first {cuts[0]:.0%} saved is worth the most per MWh: it carries all of the avoided gas "
        "capacity.")

    # 5. Timing
    sl = deck.slides.add_slide(blank)
    title(sl, "Saving during air-conditioning hours is worth more")
    h = picture(sl, "9_uniform_vs_cooling", 0.6, 1.4, 12.1)
    text(sl, 0.6, 1.5 + h, 12.1, 1.0,
         f"Only {s.loc['S1-15C', 'cooling_share']:.0%} of the 15% saving fits on the summer cooling load, yet it "
         f"avoids {cool_gas:.0%} more gas and CO2 per MWh than an even cut: those are the hours when gas runs.",
         size=16)
    footer(sl)
    sl.notes_slide.notes_text_frame.text = (
        "Cooling load is defined as summer load above the shoulder-month average for the same hour of day.")

    # 6. Flexibility
    sl = deck.slides.add_slide(blank)
    title(sl, f"Shifting load by up to {reg['flex_max_hours']:.0f} hours adds to efficiency")
    h = picture(sl, "7_dispatch_peak_week", 1.4, 1.4, 10.5)
    text(sl, 0.6, 1.5 + h, 12.1, 1.0,
         f"{reg['flex_cap_mw']:.0f} MW of shiftable load saves another {flex:.0f} M EUR and {flex_co2:.2f} Mt of CO2 "
         "per year, by moving morning and evening load into midday solar hours.", size=16)
    footer(sl)
    sl.notes_slide.notes_text_frame.text = (
        f"That is about {round(flex * 1e6 / reg['flex_cap_mw'], -3):,.0f} EUR per MW per year. Under the reserve "
        "rule flexibility gets no capacity credit, so all of this value is energy.")

    # 7. Gas price
    sl = deck.slides.add_slide(blank)
    title(sl, "The gas price decides what a saved MWh displaces")
    h = picture(sl, "8_avoided_per_mwh", 1.1, 1.3, 11.0)
    text(sl, 0.6, 1.4 + h, 12.1, 1.0,
         f"Cheap gas: each MWh saved avoids {a.at['G-lo-S1-15', 'co2_t_per_mwh']:.2f} t of CO2. Expensive gas: "
         f"the system is already {s.loc['G-hi-S0', 'res_share']:.0%} renewable, so it avoids only "
         f"{a.at['G-hi-S1-15', 'co2_t_per_mwh']:.2f} t of CO2 but {a.at['G-hi-S1-15', 'cost_eur_per_mwh']:.0f} EUR "
         "of cost.",
         size=16)
    footer(sl)
    sl.notes_slide.notes_text_frame.text = (
        f"At the base gas price the least-cost system reaches {s.loc['S0', 'res_share']:.0%} renewables, so the "
        f"{target} target binds only in "
        f"{', '.join(sorted(s.index[s.res_share < reg['re_target_2030'] + 1e-4]))}.")

    # 8. The 2027-2030 pathway at Tunisia's demonstrated building pace
    ps = pd.read_csv("results/pathway_summary.csv").set_index(["scenario", "year"])
    whole = pd.read_csv("results/pathway_avoided.csv").set_index(["scenario", "year"]).xs("2027-2030", level="year")
    share = lambda sc: ps.loc[(sc, 2030), "res_share"]
    sl = deck.slides.add_slide(blank)
    title(sl, f"At Tunisia's real pace, {target} is out of reach")
    picture(sl, "10_pathway_res_share", 0.4, 1.5, 8.6)
    card(sl, 9.3, 1.6, 3.5, 4.6)
    stat(sl, 9.5, 1.8, 3.1, f"{share('S0'):.0%}", f"renewables in 2030 without extra saving; {share('S1-15'):.0%} "
                                                 "when saving 15%")
    text(sl, 9.5, 3.9, 3.1, 2.2, f"Each MWh saved over 2027-2030 avoids {whole.at['S1-15', 'co2_t_per_mwh']:.2f} t "
                                 f"of CO2 and {whole.at['S1-15', 'cost_eur_per_mwh']:.0f} EUR: it comes off a gas plant.",
         size=15)
    footer(sl)
    sl.notes_slide.notes_text_frame.text = (
        "Each year from 2027 starts from the year before; committed projects arrive in their year; new solar is "
        f"capped at {reg['pathway_solar_extra_mw_per_year']:.0f} MW a year (Tunisia's best year, 2024), new wind "
        f"starts in {reg['pathway_wind_first_year']:.0f} and batteries in {reg['pathway_battery_first_year']:.0f}.")

    # 9. Limits and next steps
    sl = deck.slides.add_slide(blank)
    background(sl, DARK)
    title(sl, "What the numbers mean, and what comes next", colour=WHITE)
    text(sl, 0.6, 1.6, 5.8, 0.5, "Read with care", size=20, colour=SUN, bold=True, font=HEAD)
    text(sl, 0.6, 2.2, 5.8, 4.4, [
        "Not a forecast: 2030 alone has no build limit; the pathway's limits are judgements",
        "Programme costs not modelled: the avoided cost is a ceiling on what a programme may cost",
        "One weather year; imports flat at their 2024 level",
        "Demand growth from STEG's forecast as quoted by JICA (2022)"], size=15, colour=WHITE)
    text(sl, 7.0, 1.6, 5.7, 0.5, "Next steps", size=20, colour=SUN, bold=True, font=HEAD)
    text(sl, 7.0, 2.2, 5.7, 4.4, [
        "Add the ELMED link to Italy as a scenario",
        "Test faster build rates as the 2 GW wind tenders progress",
        "Compare the avoided cost with the cost of real efficiency programmes"], size=15, colour=WHITE)
    footer(sl, colour="B8C4C7")
    sl.notes_slide.notes_text_frame.text = "Code, data sources and full results are in the GitHub repository."

    Path("report").mkdir(exist_ok=True)
    deck.save("report/deck.pptx")
    print("wrote report/deck.pptx")


if __name__ == "__main__":
    main()
