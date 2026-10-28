# src/tn2030/

The study's Python package. Each file does one job; read them in this order to follow a scenario from inputs to results.

| File | Job |
|---|---|
| [`register.py`](register.py) | Read the assumptions register (and export it as Markdown) |
| [`toy.py`](toy.py) | The one-bus toy model from Phase 1, and the annuity formula |
| [`fleet.py`](fleet.py) | Replace PyPSA-Earth's gas fleet with the official one; add new gas turbine options |
| [`demand.py`](demand.py) | 2030 demand: growth, reshaping to official statistics, imports |
| [`efficiency.py`](efficiency.py) | The uniform and cooling-first demand cuts |
| [`flexibility.py`](flexibility.py) | Shiftable load as a free daily store, with its 3-hour limit |
| [`constraints.py`](constraints.py) | The 35% renewable rule, the reserve margin, the battery rule, and the solve |
| [`scenario.py`](scenario.py) | Read a scenario file and build its network |
| [`checks.py`](checks.py) | Checks after every solve (the pipeline stops if one fails) |
| [`results.py`](results.py) | Summary numbers and "avoided per MWh" |
| [`pipeline.py`](pipeline.py) | The three steps the `Snakefile` calls: build, solve, summarize |
| [`plotting.py`](plotting.py) | Colours, figure style and the data helpers the figures use |
