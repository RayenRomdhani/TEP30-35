# config/

| File | What it is |
|---|---|
| [`scenarios/`](scenarios/) | One small YAML file per scenario. Each says which reference it is compared with, how much demand is saved and how (`uniform` or `cooling`), how much load can be shifted, and the gas price factor. Numbers can be written directly or as an id from the assumptions register |
| [`pipeline.yaml`](pipeline.yaml) | Where the PyPSA-Earth base network file is on your disk |
| [`tn_base.yaml`](tn_base.yaml) | The settings given to PyPSA-Earth to build the Tunisia network (country, 2 nodes, hourly steps, technologies) |

To add a scenario, copy one of the YAML files, change it, and run the pipeline: [chapter 7 of the learning path](../docs/learn/07-try-it-yourself.md) walks through it.
