# Glossary

> **Learning path:** [1. The problem](01-the-problem.md) · [2. Key ideas](02-key-ideas.md) · [3. How the model works](03-how-the-model-works.md) · [4. The experiment](04-the-experiment.md) · [5. Results](05-results.md) · [6. How far to trust it](06-how-far-to-trust-it.md) · [7. Try it yourself](07-try-it-yourself.md) · **Glossary**

**Annualised cost.** A plant's investment spread evenly over its lifetime (with interest, here a 7.1% discount rate), plus its yearly fixed maintenance. It lets one year of operation be compared with the cost of building.

**Avoided per MWh.** The difference in a result (cost, gas, CO2) between a reference scenario and a scenario with savings, divided by the electricity saved. The headline metric of this study.

**Battery (in PyPSA-Earth).** A store of energy (MWh) with a charger and a discharger (MW). In this model the charger's size is tied to the discharger's (charger = efficiency × discharger), as PyPSA-Earth itself does.

**Build limit.** The most new capacity of one technology the pathway may add in a year (for example 268 MW of solar, Tunisia's best year so far). Each limit is a row of the assumptions register.

**Capacity.** The maximum power a plant can produce, in MW.

**Capacity expansion model.** A model that decides what to build as well as how to run it. The opposite is a dispatch model, where the plants are given.

**CCGT (combined-cycle gas turbine).** A gas plant that uses the hot exhaust of a gas turbine to drive a steam turbine. Efficient (58% for a new one), so it runs many hours.

**CO2 intensity of gas.** 0.198 t of CO2 per MWh of gas burnt (thermal). Divide by a plant's efficiency to get CO2 per MWh of electricity.

**Committed project.** A plant under construction or with a signed contract. The model must build it.

**Cooling load.** In this study: summer demand above the average spring and autumn demand for the same hour of the day. A simple way to estimate air conditioning without extra data.

**Demand flexibility (load shifting).** Using electricity earlier or later than planned, without using less over the day.

**Dispatch.** How much each plant produces in each hour.

**Efficiency (energy efficiency).** Getting the same service with less electricity.

**Electricity price (marginal price).** In the model, the cost of supplying one more MWh at a node in a given hour: usually the running cost of the most expensive plant that is running. It is what the optimisation's energy-balance rule is "worth" in that hour.

**Energy (MWh, TWh).** Power times time. 1 TWh = 1,000,000 MWh.

**Firm capacity.** Plants that can produce whenever needed: here gas and hydro. Solar, wind and batteries get no firm credit in this study.

**HiGHS.** The open-source solver that finds the cheapest answer to the model's linear program.

**INDC.** Tunisia's climate pledge under the Paris process (2015), including a 41% cut in CO2 emission intensity by 2030 versus 2010.

**JICA.** The Japan International Cooperation Agency. Its 2022 survey of Tunisia's power sector is the source for STEG's forecasts used here.

**ktep.** Thousand tonnes of oil equivalent, a unit of energy used in Tunisian energy statistics. 1 ktep = 11.63 GWh. "Net CV" (net calorific value) means the heat of the fuel without counting the heat lost in water vapour.

**Linear program (LP).** An optimisation problem where the cost and all the rules are straight-line (linear) relationships. Solvers can find the exact optimum of very large ones.

**Load factor.** Average demand divided by peak demand. Tunisia's was 0.52 in 2024.

**Marginal cost.** The cost of producing one more MWh from a plant: mostly fuel divided by efficiency, plus variable maintenance.

**Minimum-to-peak ratio.** The lowest hourly demand of the year divided by the highest. STEG forecasts 0.34 for 2030: at night, demand falls to about a third of the summer peak.

**Merit order.** Running plants from cheapest to most expensive marginal cost until demand is met.

**Myopic (model).** A pathway model that plans each year without knowing the years after it, like a country buying plants one tender at a time. The opposite is perfect foresight.

**Node (bus).** A point in the network where plants, demand and lines connect. The model has two: north and south.

**OCGT (open-cycle gas turbine).** A simple gas turbine. Cheap to build, less efficient (41% for a new one), so it runs mainly at peaks. In this study "OCGT" also covers the existing steam units.

**ONEM.** Tunisia's national energy observatory, which publishes the yearly energy statistics (*Memento*) used to calibrate the model.

**Pathway.** The study's year-by-year runs, 2027 to 2030: each year starts from the fleet of the year before, committed projects arrive in their year, and building is capped by build limits.

**Peak.** The highest demand of the year, in MW. The official 2024 figure (4,888 MW) is a record at one moment; the model's peak is the highest hourly average.

**Price duration curve.** The 8,760 hourly prices of a year sorted from highest to lowest. Its shape shows how many hours are expensive, how many are cheap, and which plants set the price.

**Power (MW).** The rate of producing or using electricity at a moment.

**PyPSA / PyPSA-Earth.** Open-source Python tools to model power systems. PyPSA-Earth builds a PyPSA network of a country from open data.

**Renewable share.** Solar, wind and hydro generation divided by all domestic generation over the year. The 2030 target is at least 35%.

**Reserve margin.** Firm capacity kept above the expected peak, to cover breakdowns and forecast errors. 10% in this study.

**Scenario codes.** S0 base case; S1-10/15/20 save 10/15/20% in every hour; S1-15C save 15% cooling first; S2-300/600 save 15% plus 300/600 MW of shifting; G-lo / G-hi gas price ×0.5 / ×1.5. See [chapter 4](04-the-experiment.md).

**Snapshot weighting.** How many hours one time step of the model stands for (1 here). Every energy total multiplies power by it.

**STEG.** Société Tunisienne de l'Électricité et du Gaz, the state-owned electricity and gas company (founded 1962). It runs the grid and supplies gas.

**System cost.** Everything the power system pays in a year: annualised cost of the plants plus the cost of running them.

**UTC.** Coordinated Universal Time, used for all model hours. Tunisian time is UTC+1 all year, so 14:00 UTC is 15:00 in Tunis.

**Thermal (MWh_th).** Energy in the fuel, before conversion to electricity. 1 MWh of electricity from a 58% efficient plant needs about 1.7 MWh of gas (thermal).
