# site/

The study as an interactive web page: a 3D map of Tunisia's grid, a 3D "8,760-hour landscape" of the model's hourly output, a scenario explorer and the results, all in one page.

| File | What it is |
|---|---|
| `index.html` | The page (sections: problem, key ideas, model, landscape, scenarios, results, trust, code) |
| `css/style.css` | The design: dark theme, one colour per technology (the same as the study's figures) |
| `js/main.js` | Loads the data, fills every number in the text, draws the charts (Chart.js) |
| `js/hero.js` | The opening 3D scene (three.js): Tunisia's outline, its high-voltage grid, the model's two nodes |
| `js/landscape.js` | The 3D surface of hourly output (day × hour × MW), switchable by scenario and technology |
| `data/*.json` | Written by `scripts/export_site_data.py` from `results/`, the register and the solved networks |

No number is typed into the page: every figure comes from `data/*.json`.

To view it locally (the page loads its data with `fetch`, so it needs a small web server):

```bash
python -m http.server 8137 --directory site
```

then open http://localhost:8137. After a new pipeline run, refresh the data with `python scripts/export_site_data.py`.

Credits: grid lines © OpenStreetMap contributors (ODbL), country outline from Natural Earth (public domain), three.js, Chart.js, Fira fonts and Material Symbols (Google Fonts).
