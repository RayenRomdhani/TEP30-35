# 4. The experiment: eleven versions of 2030

> **Learning path:** [1. The problem](01-the-problem.md) · [2. Key ideas](02-key-ideas.md) · [3. How the model works](03-how-the-model-works.md) · **4. The experiment** · [5. Results](05-results.md) · [6. How far to trust it](06-how-far-to-trust-it.md) · [7. Try it yourself](07-try-it-yourself.md) · [Glossary](glossary.md)

A model on its own answers nothing. The trick is to run it twice, change exactly one thing, and look at the difference. This study runs it eleven times.

## The starting point: 2030 without extra savings (S0)

- 2024 demand: **22.5 TWh** (ONEM).
- Growth: **3.2% a year** (STEG's forecast), so 2030 demand is 22.5 × 1.032⁶ = **27.2 TWh**.
- Imports stay at their 2024 level (3.1 TWh), so power plants in Tunisia must produce **24.1 TWh**.
- The hourly shape is stretched to match STEG's official load factor and minimum-to-peak ratio.
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
| Avoided capacity (MW per TWh saved per year) | New plants the model no longer builds |

---

**Next:** [5. Results](05-results.md): what the model found.
