# Phase 1: the toy model, its objective and its constraints

Code: [`src/tn2030/toy.py`](../src/tn2030/toy.py) · run: `python scripts/phase1_toy_model.py`
Figure: [`results/figures/phase1_toy_dispatch.png`](../results/figures/phase1_toy_dispatch.png)

## In one sentence

The toy model is a linear program that picks how much gas, solar, wind and battery capacity to build,
and how to run it every hour, so that demand is always met **at the lowest total cost**.

**Why it matters:** the full PyPSA-Earth model in later phases is the same idea at country scale
(more buses, a grid, real weather). If the single-node version is clear, the big one is too.

**Analogy:** planning a restaurant kitchen. You choose how many ovens to buy (capacity, paid once
whatever you cook) and how many meals to cook in each oven every hour (dispatch, paid per meal).
Cheap-to-run but expensive-to-buy ovens make sense only if you use them a lot; a fridge (the battery)
lets you cook at quiet times and serve at busy ones.

**What it is not:** a forecast or a simulation of how STEG actually operates. It answers "what would
the cheapest system look like under these assumptions", nothing more.

## The setup

| Element | PyPSA component | Inputs |
|---|---|---|
| One node "TN" | `Bus` | - |
| Demand | `Load` with hourly `p_set` | illustrative summer-day shape, peak ~4.1 GW |
| Gas (CCGT) | `Generator`, `p_nom_extendable=True` | technology-data v0.15.0: 1,109 EUR/kW, 58 % efficiency, gas 28.4 EUR/MWh_th |
| Solar PV | `Generator` + hourly `p_max_pu` | 482 EUR/kW, illustrative daylight curve |
| Onshore wind | `Generator` + hourly `p_max_pu` | 1,383 EUR/kW, illustrative curve with a 2-day lull |
| Battery | `StorageUnit`, `max_hours=4` | inverter 214 EUR/kW + storage 190 EUR/kWh, 96 % each way |

Every number comes from [`data/assumptions_register.xlsx`](../data/assumptions_register.xlsx). Load, solar and
wind **shapes are illustrative**, not measured; they exist only to show the mechanics.

## The objective function

$$
\min \;\; \underbrace{\sum_{g} c_g \, G_g + \sum_{s} c_s \, P_s}_{\text{investment}}
\;+\; \underbrace{\sum_{t} w_t \sum_{g} o_g \, p_{g,t}}_{\text{operation}}
$$

| Symbol | Meaning | In PyPSA |
|---|---|---|
| $G_g$, $P_s$ | capacity to build (MW), decided by the optimizer | `p_nom_opt` |
| $c_g$, $c_s$ | yearly cost of 1 MW of capacity (EUR/MW/yr) | `capital_cost` |
| $p_{g,t}$ | output of generator $g$ in hour $t$ (MW) | `generators_t.p` |
| $o_g$ | running cost (EUR/MWh): fuel ÷ efficiency + variable O&M | `marginal_cost` |
| $w_t$ | hours each snapshot stands for (1 here, 3 at 3-hour resolution) | `snapshot_weightings` |

**Two details worth defending in an interview:**

1. **Annualising the investment.** A plant costs money once but lasts decades. The *annuity factor*
   $a = \frac{r}{1-(1+r)^{-n}}$ turns the investment into an equal yearly payment ($r$ = 7.1 % discount
   rate, same as PyPSA-Earth; $n$ = lifetime). Yearly cost = investment × ($a$ + fixed O&M %).
   Tested in `tests/test_toy_costs.py`.
2. **Scaling to the modelled period.** The toy covers one week, but $c_g$ is a *yearly* cost. Without a
   correction, one week of operation would carry a whole year of investment and the model would build far
   too little. So capital costs are multiplied by hours ÷ 8,760. Tested in `test_toy_capital_cost_scaled_to_horizon`.

## The constraints

| # | Constraint | Formula | Created by |
|---|---|---|---|
| 1 | **Energy balance**: supply equals demand in every hour | $\sum_g p_{g,t} + \sum_s (p^{dis}_{s,t} - p^{ch}_{s,t}) = d_t$ | the `Bus` |
| 2 | **Generator limit**: output ≤ capacity × availability | $0 \le p_{g,t} \le \bar{g}_{g,t}\, G_g$ | `p_max_pu` (1 for gas, weather profile for solar/wind) |
| 3 | **Battery power limit** | $0 \le p^{dis}_{s,t},\, p^{ch}_{s,t} \le P_s$ | `StorageUnit.p_nom` |
| 4 | **State of charge**: energy carried hour to hour, with losses | $e_{s,t} = e_{s,t-1} + w_t\,(\eta\, p^{ch}_{s,t} - p^{dis}_{s,t}/\eta)$ | `StorageUnit` |
| 5 | **Energy capacity** | $0 \le e_{s,t} \le h_s\, P_s$ ($h_s$ = 4 h) | `max_hours` |
| 6 | **Cyclic storage**: end the week with the charge it started with | $e_{s,T} = e_{s,0}$ | `cyclic_state_of_charge=True` |
| 7 | Non-negative capacities | $G_g, P_s \ge 0$ | `p_nom_extendable` |

Everything is **linear**, so this is a linear program (LP) that HiGHS solves exactly in under a second.

**The by-product: prices.** The shadow price (dual) of constraint 1 is the cost of serving one more MWh in
that hour. That is the **marginal electricity price**, one of the outputs of the main study.

## What the toy shows (one summer week, illustrative inputs)

| | Result |
|---|---|
| Gas (CCGT) built | 2,212 MW, 43 % of generation |
| Solar PV built | 6,822 MW, 57 % of generation |
| Onshore wind built | 0 MW |
| Battery built | 2,154 MW / 8,616 MWh (4 h) |
| Cost of the week | 28.8 M EUR |

**Reading the figure:** solar covers the day and over-produces at noon; the surplus charges the battery
(purple, below zero), which discharges in the evening peak. Gas runs flat at night.

**Why no wind?** Wind costs almost three times as much per kW as solar here, and the two-day lull removes
part of its output exactly when it would replace gas. With these illustrative shapes, solar + battery +
gas is cheaper. Change the shapes and the answer changes, which is the point: **results depend on the
inputs, so every input must be sourced** (the rule for the real model).

## Things people often confuse

- **Capacity (MW) vs energy (MWh).** A 2,154 MW battery with 4 h stores 8,616 MWh. Both are decisions.
- **"Cheapest" is not "least gas".** The optimizer has no renewable target yet. The 35 % constraint
  is added in Phase 4.
- **Generation above the load line** is not wasted: it is the battery charging.
- **A toy result is not a Tunisian result.** It validates the method, not the numbers.

## Natural next questions (answered in later phases)

- What happens with real weather and a real grid? → Phase 2 (PyPSA-Earth).
- Does the model reproduce Tunisia's 2024 system? → Phase 3 (validation).
- How much capacity does a 15 % demand cut avoid? → Phase 4 (scenarios).
