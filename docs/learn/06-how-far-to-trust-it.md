# 6. How far to trust it

> **Learning path:** [1. The problem](01-the-problem.md) · [2. Key ideas](02-key-ideas.md) · [3. How the model works](03-how-the-model-works.md) · [4. The experiment](04-the-experiment.md) · [5. Results](05-results.md) · **6. How far to trust it** · [7. Try it yourself](07-try-it-yourself.md) · [Glossary](glossary.md)

"All models are wrong, but some are useful," as the statistician George Box put it. This chapter is about which parts of this one are useful, and where it is blind.

## Step 1: make it reproduce 2024

Before asking the model about 2030, I ran it on 2024 (fleet and demand fixed, only the hourly operation decided) and **calibrated** it until it reproduced the official statistics ([`results/validation.csv`](../../results/validation.csv)). Be clear about what that means: several lines below match *because I made them match*.

| 2024 | Model | Official | Difference | What it shows |
|---|---|---|---|---|
| Gas power plants (MW) | 5,644 | 5,644 | 0% | Set by calibration (the official fleet is an input) |
| Peak demand (MW) | 4,901 | 4,888 | +0.3% | Set by calibration (demand reshaped to the official load factor) |
| Average efficiency of the gas fleet | 49% | 49% | 0% | Set by calibration (one fitted factor) |
| Gas burnt for electricity (TWh, thermal) | 37.0 | 36.8 | +0.4% | Consistency check: two ONEM tables agree with the fitted fleet |
| Share of generation from gas | 93.6% | 94.5% | −1.0% | Close, partly because gas fills whatever renewables leave |
| Wind generation (TWh) | 0.48 | 0.34 | +43% | Not calibrated, too high |
| Solar generation (TWh) | 0.75 | 0.63 | +20% | Not calibrated, too high |

So the calibration gets the **gas side** of 2024 right: the right plants, the right peak, the right fuel use. That matters, because gas drives every result here. What it does **not** test:

- how output is split between combined cycles and gas turbines (ONEM does not publish it), which decides how much gas a saved MWh avoids;
- the **hour** of the daily peak (see limit 3 below);
- wind and solar, which come out too high: the model has a little more wind capacity than other published figures, part of the real wind fleet was not producing at full capacity in 2024, the model uses 2013 weather, and its solar includes rooftop systems. Together that is about 1% of generation.

The full story, gap by gap, is in the [Phase 3 write-up](../project-history/phase3-validation.md).

## Step 2: does every 2030 run obey the rules?

After each of the 11 solves, the pipeline checks, and stops if anything fails:

- supply equals demand over the year (to 0.01%);
- renewables are at least 35% of domestic generation;
- no demand is left unserved;
- every existing plant and committed project is kept;
- firm capacity is at least 10% above the peak.

All 11 runs pass. On top of that, the code has 100 automated tests, most of them on a small two-day test network where the right answer is known.

## What the model cannot see

Each limit comes with the way I expect it would push the results. None of these were tested with extra runs.

1. **No speed limit on building.** The base case adds about 6 GW of solar and wind by 2030, far above Tunisia's recent pace (about 1 GW of projects under way). Read the 56% renewable share as "what least cost would do", not a forecast. *Likely effect:* with a build limit, more gas runs, so a saved MWh avoids more gas and CO2.
2. **Saving and shifting are free in the model.** The study values a saved or shifted MWh; it does not price the appliances, insulation, smart controls or programmes needed. Read 60 EUR/MWh as the most a saving programme could cost and still pay off for the power system, and 22 M EUR a year as the gross value of 300 MW of shifting. *Pushes the other way for shifting:* it gets no credit for lowering the peak, which is conservative.
3. **The model's daily peak comes about two hours late.** The model's summer peaks fall around 17:00 UTC; STEG's real peaks were at 14:41 UTC. That changes how much load can move into solar hours and when cooling savings land. *Likely effect:* could push the cooling and shifting results either way.
4. **One weather year, one hour at a time.** 2013 weather, 8,760 steps. A test at 3-hour steps built 2.7% more solar and 3.9% more wind; another weather year would shift numbers a little too.
5. **No unit commitment and no operating reserves.** Gas plants can run at any level, with no start-up costs or minimum output (in the peak-week figure, combined cycles drop to about 0.1 GW at midday). *Likely effect:* real plants are less flexible, so more gas would run.
6. **Plant outages are not modelled.** The fitted efficiency factor partly stands in for them. *Likely effect:* peaking gas turbines would run more, and a saved MWh would avoid more gas.
7. **Imports are fixed** at their 2024 level every hour, so every MWh saved falls on Tunisian plants. The planned ELMED link to Italy is not modelled.
8. **The reserve rule is simple and conservative.** One national capacity rule, not a reliability study, and solar gets no firm credit even though the real peak falls on summer afternoons. A 15% margin (the top of STEG's range) would likely make the base case build more gas turbines; giving solar some credit would build fewer.
9. **The 660 MW of steam units stay in 2030.** STEG has planned to retire them, but not committed to it. *Likely effect:* retiring them would raise the need for new gas turbines, and the value of saving.
10. **Losses are not modelled.** A MWh saved at the meter saves a bit more than one MWh at the power plant, because the grid loses some on the way. *Likely effect:* the real value per MWh saved is slightly higher.
11. **Second-hand forecasts.** Demand growth and the 2030 peak are STEG's forecast as reported by JICA (2022), not a STEG document.
12. **Absolute costs.** The system cost includes plants that already exist. Differences between scenarios are meaningful; the absolute level is not the bill of the real system.

## So what can you take away?

- **Robust:** saving electricity avoids gas, CO2 and new plants, and the gas price changes what a saved MWh displaces. These follow from the structure of the system, not from one setting.
- **Plausible, with caveats:** the extra value of saving at cooling time and of shifting demand. Both depend on the hour of the peak (limit 3), and shifting is free in the model (limit 2).
- **The sizes** (60 EUR, 0.18 t, 423 MW) belong to this setup. Treat them as well-founded estimates, not forecasts; most limits above would push the gas and CO2 savings up, not down.

---

**Next:** [7. Try it yourself](07-try-it-yourself.md): run the model and change a scenario.
