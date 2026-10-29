# site/

The study as one scrolling story: "One saved MWh". Each chapter is a flat field of colour taken from a time of a summer day in Tunisia (night, dawn, the Saharan noon, the peak, the gas-fired evening), and the page is built around one idea: the model's summer peak day, lived hour by hour.

| File | What it is |
|---|---|
| `index.html` | The page: the question, the day, the problem, the model, the answer, the evening, trust and code |
| `css/app.css` | The design: one typeface (Bricolage Grotesque), one flat colour per chapter, no gradients or glows |
| `js/app.js` | Fills every number from the data, colours the bar per chapter, scroll reveals, the steps that slide sideways, the "choose how Tunisia saves" panel, the tables |
| `js/day.js` | The pinned 3D scene (three.js): a small landscape with a city, a solar field, wind turbines, a gas plant and the sea. Scroll moves the clock; the sun, the panels, the turbines, the gas flame and smoke and the city lights follow the model's real hourly output on its peak day |
| `js/year.js` | Every hour of 2030 as a 3D surface (day × hour × MW), switchable by scenario and technology |
| `js/graphics.js` | The drawn map of Tunisia's grid and the week chart (plain SVG) |
| `data/*.json` | Written by `scripts/export_site_data.py` from `results/`, the register and the solved networks |
| `assets/headline.png` | The social-sharing picture |

No number is typed into the page: every figure comes from `data/*.json`.

To view it locally (the page loads its data with `fetch`, so it needs a small web server):

```bash
python -m http.server 8137 --directory site
```

then open http://localhost:8137. After a new pipeline run, refresh the data with `python scripts/export_site_data.py`.

Credits: grid lines © OpenStreetMap contributors (ODbL), country outline from Natural Earth (public domain), three.js, Bricolage Grotesque (Google Fonts).
