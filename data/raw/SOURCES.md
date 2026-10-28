# Raw data sources

Files in `data/raw/` are not committed (size, licences). This list says where each one came from, so anyone can download them again.
Every number used by the model is in `data/assumptions_register.xlsx`, with its source URL.

## Files in this folder

| File | Source | Size | Downloaded | SHA-256 |
|---|---|---|---|---|
| `technology-data_v0.15.0_costs_2030.csv` | https://github.com/PyPSA/technology-data/blob/v0.15.0/outputs/costs_2030.csv | 281 KB | 2026-10-27 | – |
| `onem/Chiffres_cles_energie_2024.pdf` | ONEM / Ministry of Industry, Mines and Energy, *Memento du secteur de l'énergie, Chiffres de 2024* (Aug 2025): https://www.energiemines.gov.tn/fileadmin/docs-u1/Chiffres_cl%C3%A9s_%C3%A9nergie_2024.pdf | 3.7 MB | 2026-10-28 | `76a0a8de…8690892b` |
| `jica/jica_2022_12342283.pdf` | JICA / TEPSCO / KPMG, *Data Collection Survey on Power Sector in Tunisia*, Final Report (Mar 2022): https://openjicareport.jica.go.jp/pdf/12342283.pdf | 14.5 MB | 2026-10-28 | `883af51f…6c636935` |

How the JICA survey was read:
- **Text:** extracted with `pdftotext`. Page numbers are the report's own (e.g. 2-17).
- **What it gives:** STEG's base-case demand forecast (3.2%/yr from 2019; 28,362 GWh and 6,000 MW in 2030; 54% load factor; minimum-to-peak ratio 34%).
- **Thermal plans:** STEG's planned thermal retirements and additions to 2030.

How the ONEM Memento was read:
- **Text tables:** extracted with `pdftotext` (2024 production by fuel, exchanges, peak, specific consumption). Pages are given as printed page numbers.
- **Capacity chart:** the 2024 capacity by plant type (printed p.17) is a drawn chart with no text layer. Its values were read from the chart and cross-checked against the text on the same page (combined cycles = 42% of the fleet).

## Web sources read but not downloaded (accessed 2026-10-27/28)

- **Ember, Electricity Data Explorer, Tunisia:** https://ember-energy.org/data/electricity-data-explorer/?entity=Tunisia
  - 2024: demand 23.96 TWh, net imports 2.59 TWh, generation 21.37 TWh, gas 94.52% of generation.
  - Used as a cross-check only. Not verified from Ember's data file: the author declined the 49 MB download.
- **STEG, "Produire":** https://www.steg.com.tn/fr/page/produire
  - Peaks: 4,888 MW (Wed 14 Aug 2024, 15:41) and 4,837 MW (Fri 25 Jul 2025, 15:41).
  - Demand growth of 4.1% in 2025.
- **La Presse, 9 Oct 2026** (STEG short-term plan: restoring the full capacity of the Kchabta and Metline plants, about 190 MW): https://www.lapresse.tn/2026/10/09/electricite-la-steg-prevoit-des-capacites-supplementaires-de-250-mw-grace-a-lamelioration-des-centrales/
- **IRENA, Tunisia renewable energy statistical profile** (wind 245 MW in 2024): https://www.irena.org/-/media/Files/IRENA/Agency/Statistics/Statistical_Profiles/Africa/Tunisia_Africa_RE_SP.pdf
  - The 245 MW was reported by a research agent and not re-read by the author.
- **PyPSA-Earth DemandCast data** (`D:\pypsa-earth\data\demand\forecasts_on_historical_period.parquet`, from the approved data bundle).
  - The Tunisia 2024 load factor of 0.70 was computed from it in Phase 3.
- **Committed projects:** see `source_url` and `notes` in `data/committed_projects.csv`.
  - Inclusion rule (spec D6): under construction or signed contract, plus plants that came online in 2025–26 and so are missing from the 2024 fleet.
  - Excluded:
    - Projects whose developer only says "awarded" (Scatec Tataouine 120 MW solar, El Fahs 75 MW wind). Author's decision, 2026-10-28.
    - All tenders and announcements: wind tenders, STEG 300 MW / 600 MWh batteries, Bazma PV + storage, new gas units, the STEG–Sonelgaz combined cycle.
  - ELMED (Tunisia–Italy, 600 MW) is under construction but due 2030–31. It is left to the optional scenario (spec D13).
  - Bus assignment: each governorate (GADM 4.1, `D:\pypsa-earth\data\gadm\gadm41_TUN`) was mapped to the base-network bus region that holds most of its area (`resources/TN/bus_regions/regions_onshore_elec_s_2.geojson`). Kairouan is split 73% / 27%; it goes to `TN0 0` (north).

## Searched for, not found

- **An evaluated cost per MWh saved for ANME / FTE efficiency programmes.**
  - The only figures found are 152 TND per toe saved (industry contract programmes, 2004–2010, mostly fuel savings, cost basis not stated; Osman 2012, https://www.citego.org/bdf_fiche-document-984_fr.html) and an ex-ante estimate below 1 US cent/kWh for fridge labelling (eceee 2005, https://www.osti.gov/etdeweb/biblio/20646780).
  - Neither is a defensible electricity cost per MWh, so no `ee_programme_cost_eur_per_mwh` row was added. The README will state this as a limitation (spec §1).
- **A recent official 2030 demand projection.** The Energy Strategy 2035 synthesis has none. The newest STEG forecast found is the 2022 one quoted in the JICA survey (above). It is used for the growth rate.
- **A public hourly load curve for Tunisia** (risk R5).
- **2024 capacity by individual plant.** Fleet validation therefore uses capacity by plant type.
