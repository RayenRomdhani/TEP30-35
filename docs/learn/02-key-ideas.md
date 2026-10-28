# 2. Key ideas: the toolkit in ten minutes

> **Learning path:** [1. The problem](01-the-problem.md) · **2. Key ideas** · [3. How the model works](03-how-the-model-works.md) · [4. The experiment](04-the-experiment.md) · [5. Results](05-results.md) · [6. How far to trust it](06-how-far-to-trust-it.md) · [7. Try it yourself](07-try-it-yourself.md) · [Glossary](glossary.md)

Seven ideas carry the whole study. If you already work in power systems, skim the headings and jump to [chapter 3](03-how-the-model-works.md).

## 1. Energy is not power

- **Power** (MW) is a rate: how much electricity flows right now. A plant's size is its power, e.g. a 500 MW gas turbine.
- **Energy** (MWh) is power times time. A 500 MW plant running for 2 hours delivers 1,000 MWh.

A country needs enough *power* for its worst moment and enough *energy* over the year. Those are two different bills: plants to cover the peak, and fuel to cover the hours. Saving energy can cut both, but not always equally, and that difference is a big part of this study.

## 2. Demand has a shape

Electricity use changes every hour. In Tunisia it peaks on summer afternoons, when air conditioners run flat out, and drops at night. In 2024 the average demand was only about half of the peak (a **load factor** of 0.52). The peak decides how many plants you need; the rest of the year they sit partly idle.

## 3. Efficiency and flexibility are not the same thing

- **Efficiency** lowers demand: the same service with less electricity. Over a year it removes MWh.
- **Flexibility** moves demand in time: the same MWh, used a few hours earlier or later. Over a year it removes nothing, but it can move use away from expensive hours into cheap ones (for example into midday, when solar panels produce the most).

The study tests both, separately and together.

## 4. The merit order: who runs when

Each hour, the grid runs the cheapest plants first and adds more expensive ones until demand is met. Solar and wind cost almost nothing to run once built, so they go first when available. Gas plants follow, cheapest first:

| Plant type | Turns gas into electricity at | Fuel cost per MWh of electricity (gas at 28.4 EUR/MWh) | CO2 per MWh of electricity |
|---|---|---|---|
| Combined cycle (CCGT), new | 58% | about 49 EUR | about 0.34 t |
| Gas turbine (OCGT), new | 41% | about 69 EUR | about 0.48 t |

(Efficiencies, gas price and CO2 content from PyPSA technology-data 2030, via the [register](../../data/assumptions_register.md); 0.198 t of CO2 per MWh of gas burnt.)

The last plant needed in an hour sets that hour's **price**. So a MWh saved in an hour when an old gas turbine is running is worth much more than one saved at noon on a sunny day.

## 5. Capacity and the reserve margin

Plants break down and forecasts miss, so planners keep more firm capacity than the expected peak. STEG plans for a **reserve margin** of 10-15% above the peak; this study uses 10%. "Firm" here means plants that can run whenever needed: gas and hydro. Solar and wind get no credit, because the sun sets and the wind drops.

This is how saving electricity can avoid *building* plants: lower the peak, and the reserve margin needs fewer firm megawatts.

## 6. Renewables: cheap energy, variable power

Solar and wind produce the cheapest energy over a year, but only when the sun shines or the wind blows. A system with more of them needs something for the other hours: gas plants, batteries, or demand that can move. Tunisia's target says at least **35%** of the electricity generated in the country must be renewable by 2030.

## 7. System cost, and "avoided per MWh"

The **system cost** is everything the power system pays in a year: the yearly cost of the plants (their investment spread over their lifetime, plus fixed maintenance) and the cost of running them (fuel and variable maintenance).

The headline metric of this study is simple:

> **avoided per MWh = (cost in the base case − cost with savings) ÷ (MWh saved)**

and the same for gas burnt, CO2 and new capacity. It answers: *what is one MWh of saving worth to the power system?*

---

**Next:** [3. How the model works](03-how-the-model-works.md): how a computer finds the cheapest power system that keeps the lights on.
