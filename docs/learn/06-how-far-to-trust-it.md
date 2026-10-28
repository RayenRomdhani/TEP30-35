# 6. How far to trust it

> **Learning path:** [1. The problem](01-the-problem.md) · [2. Key ideas](02-key-ideas.md) · [3. How the model works](03-how-the-model-works.md) · [4. The experiment](04-the-experiment.md) · [5. Results](05-results.md) · **6. How far to trust it** · [7. Try it yourself](07-try-it-yourself.md) · [Glossary](glossary.md)

"All models are wrong, some are useful." This chapter is about which parts of this one are useful, and where it is blind.

## Test 1: can it reproduce 2024?

Before asking the model about 2030, I ran it on 2024 (fleet and demand fixed, only the hourly operation decided) and compared it with official statistics ([`results/validation.csv`](../../results/validation.csv)):

| 2024 | Model | Official | Difference |
|---|---|---|---|
| Gas power plants (MW) | 5,644 | 5,644 | 0% |
| Gas burnt for electricity (TWh, thermal) | 37.0 | 36.8 | +0.4% |
| Average efficiency of the gas fleet | 49% | 49% | 0% |
| Peak demand (MW) | 4,901 | 4,888 | +0.3% |
| Share of generation from gas | 93.6% | 94.5% | −1.0% |
| Wind generation (TWh) | 0.48 | 0.34 | +43% |
| Solar generation (TWh) | 0.75 | 0.63 | +20% |

The gas side, which drives every result in this study, matches closely. Two honest caveats:

- The fleet efficiency was **fitted** (one factor for all existing gas plants), so matching it proves little on its own. The gas-burnt line is the real check, because it comes from a separate ONEM table that was not used in the fit.
- Wind and solar are too high. The model has a little more wind capacity than IRENA lists (283 against 245 MW), part of the real wind fleet was not producing at full capacity in 2024, the model uses 2013 weather rather than 2024's, and its solar includes rooftop systems. Together that is about 1% of generation, so it barely moves the gas numbers.

The full story, gap by gap, is in the [Phase 3 write-up](../project-history/phase3-validation.md).

## Test 2: does every 2030 run obey the rules?

After each of the 11 solves, the pipeline checks, and stops if anything fails:

- supply equals demand over the year (to 0.01%);
- renewables are at least 35% of domestic generation;
- no demand is left unserved;
- every existing plant and committed project is kept;
- firm capacity is at least 10% above the peak.

All 11 runs pass. On top of that, the code has about a hundred automated tests, most of them on a small two-day test network where the right answer is known.

## What the model cannot see

These are the limits that matter most, roughly in order of how much they could change the answer:

1. **No speed limit on building.** The base case adds about 6 GW of solar and wind by 2030, far above Tunisia's recent pace (about 1 GW of projects under way). Real projects need land, grid connections, finance and permits. So read the 56% renewable share as "what least cost would do", not a forecast. My expectation (not tested here): with a build limit, more gas would run, and each saved MWh would avoid more gas and CO2.
2. **The cost of saving is not included.** The study values a saved MWh; it does not price the air conditioners, insulation or programmes needed to save it. Read 60 EUR/MWh as the most a programme could cost and still pay off for the power system.
3. **One weather year, one hour at a time.** 2013 weather, 8,760 steps. A test at 3-hour steps built 2.7% more solar and 3.9% more wind; another weather year would shift numbers a little too.
4. **Imports are fixed.** Imports stay at their 2024 level every hour. That is why every MWh saved falls on Tunisian plants. A planned link to Italy (ELMED) is not modelled.
5. **Plant outages are not modelled.** The fitted efficiency factor partly stands in for them. With outages, peaking gas turbines would run more and a saved MWh would probably avoid more gas.
6. **The reserve rule is simple.** It is one national capacity rule, not a reliability study. A 15% margin (the top of STEG's range) would make the base case build more gas turbines and make savings worth more.
7. **Second-hand forecasts.** Demand growth and the 2030 peak are STEG's forecast as reported by JICA (2022), not a STEG document.
8. **Absolute costs.** The system cost includes plants that already exist. Differences between scenarios are meaningful; the absolute level is not the bill of the real system.

## So what can you take away?

- The **direction** of every finding is solid: saving electricity avoids gas, CO2 and new plants; timing matters; flexibility adds value; the gas price changes what a saved MWh displaces.
- The **sizes** (60 EUR, 0.18 t, 423 MW) belong to this setup. Treat them as well-founded estimates, not precise forecasts; the list above says which way each limit would likely push them.

---

**Next:** [7. Try it yourself](07-try-it-yourself.md): run the model and change a scenario.
