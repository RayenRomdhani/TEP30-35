# 4. The experiment: eleven versions of 2030

> **Learning path:** [1. The problem](01-the-problem.md) · [2. Key ideas](02-key-ideas.md) · [3. How the model works](03-how-the-model-works.md) · **4. The experiment** · [5. Results](05-results.md) · [6. How far to trust it](06-how-far-to-trust-it.md) · [7. Try it yourself](07-try-it-yourself.md) · [Glossary](glossary.md)

A model on its own answers nothing. The trick is to run it twice, change exactly one thing, and look at the difference. This study runs it eleven times.

## The starting point: 2030 without extra savings (S0)

- 2024 demand: **22.5 TWh** (ONEM).
- Growth: **3.2% a year** (STEG's forecast), so 2030 demand is 22.5 × 1.032⁶ = **27.2 TWh**.
- Imports stay at their 2024 level (3.1 TWh), so power plants in Tunisia must produce **24.1 TWh**.
- The hourly shape is stretched to match the 2024 load factor (ONEM) and the minimum-to-peak ratio of STEG's 2030 forecast.
- Gas costs 28.4 EUR per MWh (thermal).

Everything else in the experiment is measured against this base case.

## The eleven scenarios

| Code | Plain name | What changes against S0 |
|---|---|---|
| **S0** | Base case | Nothing: 2030 demand, base gas price |
| **S1-10** | Save 10% | Demand 10% lower in every hour |
| **S1-15** | Save 15% | Demand 15% lower in every hour (the headline case) |
| **S1-20** | Save 20% | Demand 20% lower in every hour |
| **S1-15C** | Save 15%, cooling first | Same 15% of the year's energy, taken first from summer air-conditioning load |
| **S2-300** | Save 15% + 300 MW shift | S1-15, plus 300 MW of demand that can move up to 3 hours earlier or later |
| **S2-600** | Save 15% + 600 MW shift | The same with 600 MW |
| **G-lo-S0** | Cheap gas | S0 with gas at half price |
| **G-lo-S1-15** | Cheap gas, save 15% | S1-15 with gas at half price |
| **G-hi-S0** | Expensive gas | S0 with gas 50% more expensive |
| **G-hi-S1-15** | Expensive gas, save 15% | S1-15 with gas 50% more expensive |

The savings apply to total demand (27.2 TWh), while imports stay fixed, so the demand on Tunisian plants falls a little more: 11.3% in S1-10, for example.

Each scenario is one small text file in [`config/scenarios/`](../../config/scenarios/). Open `S1-15.yaml` and you will see the whole definition in a handful of lines.

## Why these ones

- **Three sizes of saving (10, 15, 20%)** show whether the first MWh saved is worth more than the last.
- **Cooling first** tests timing. Air conditioning is what drives Tunisia's summer peak. The model defines "cooling load" as summer demand above the spring and autumn average for the same hour of the day. In 2030 that adds up to 1.6 TWh, so only 39% of a 15% saving (4.1 TWh) can come from it; the rest is taken evenly.
- **300 MW of shifting** is the size of the government's peak-demand reduction target (TAP, October 2026). 600 MW is a sensitivity (an assumption, labelled as such in the register).
- **Gas price ±50%** because the gas price is the biggest unknown in a gas-run system. Each gas-price scenario is compared with the base case *at the same gas price*, so the comparison stays fair.

## How shifting is modelled

Think of it as a free, lossless battery that belongs to the consumers. Every day starts half full. Load can be brought forward (the "battery" fills) or postponed (it empties), but every MWh moved must come back within 3 hours, load moved up plus load moved down in one hour cannot exceed the shift limit, and each day ends back at half full. Nothing is saved over the day; it only moves.

## What is compared with what

For each pair, the model reports:

| Metric | Meaning |
|---|---|
| Avoided cost (EUR per MWh saved) | Lower yearly system cost, divided by the MWh not used |
| Avoided gas (MWh of gas per MWh saved) | Gas not burnt in power plants |
| Avoided CO2 (t per MWh saved) | CO2 not emitted |
| Avoided capacity (MW per TWh saved per year) | New plants the model no longer builds (all types added together, mostly solar and wind) |

## Then the realistic version: 2027 to 2030, one year at a time

Everything above treats 2030 as a single year: the model starts from the 2024 fleet and may build whatever is cheapest, in one go. That answers "what would least cost do?", but no country adds 6 GW of solar and wind in one step. Tunisia connected its first 100 MW-class solar plant only in December 2025.

So the same eleven scenarios are also run as a **pathway**:

1. **2025 and 2026 are solved once**, in the base case, to bring the fleet from 2024 to the start of the plan.
2. **Each scenario then runs 2027, 2028, 2029 and 2030 in order.** Each year starts with everything built the year before; nothing is taken down.
3. **Committed projects switch on in the year they are due** (about 0.8 GW of solar in 2027, Voltalia's 132 MW at Gabès in 2028).
4. **New building is capped at the pace Tunisia has shown**: at most 268 MW of extra solar a year (what it added in 2024, its best year), no new wind before 2029 and then 75 MW a year (one tender lot), batteries only from 2029 and at most 150 MW / 540 MWh (the Bazma tender). New gas turbines are not capped: one can be added within a year.
5. **Savings and shifting ramp up**: a quarter of the scenario's saving in 2027, half in 2028, three quarters in 2029, all of it in 2030.
6. **The 35% target is measured, not forced.** At this pace it cannot be met, and forcing it would make the model build faster than Tunisia can.

Each year is planned without knowing the next one (a "myopic" model), which is close to how Tunisia buys power plants: one tender at a time. The design and every source are in the [Phase 6 write-up](../project-history/phase6-pathway.md).

---

**Next:** [5. Results](05-results.md): what the model found.
