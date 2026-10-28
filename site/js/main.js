// Page logic: load the study's data files, fill every number in the text, draw the charts.
// No number is typed in the HTML: each one is computed here from site/data/*.json.

import { startHero } from "./hero.js";
import { startLandscape } from "./landscape.js";

const COLORS = { CCGT: "#e66767", OCGT: "#9085e9", hydro: "#199e70", onwind: "#3987e5", solar: "#c98500", battery: "#d55181" };
const LABELS = { CCGT: "Gas CCGT", OCGT: "Gas OCGT + steam", hydro: "Hydro", onwind: "Onshore wind", solar: "Solar PV", battery: "Battery" };
const ORDER = ["CCGT", "OCGT", "hydro", "onwind", "solar", "battery"];
const INK = "#e8eef7", INK2 = "#a9b6c9", GRID = "rgba(148,178,220,0.12)";
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const getJSON = (name) => fetch(`data/${name}.json`, { cache: "no-cache" }).then((r) => r.json()); // revalidate after re-exports
const pct = (x, d = 0) => `${(x * 100).toFixed(d)}%`;
const num = (x, d = 0) => x.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });

// ---------- facts shown in the text ----------
function computeFacts(study) {
  const sc = Object.fromEntries(study.scenarios.map((s) => [s.code, s]));
  const c = (id) => study.context[id].value;
  const head = sc["S1-15"].avoided;
  const supply = c("gas_supply_domestic_2024_ktep") + c("gas_supply_royalty_2024_ktep") + c("gas_supply_purchases_2024_ktep");
  const gasGen = (s) => sc[s].gen_CCGT_twh + sc[s].gen_OCGT_twh;
  const saved = sc.S0.demand_twh - sc["S1-15"].demand_twh;
  const flex = sc["S1-15"].system_cost_meur - sc["S2-300"].system_cost_meur;
  const marg = (a, b) => (sc[a].system_cost_meur - sc[b].system_cost_meur) / (sc[a].demand_twh - sc[b].demand_twh);
  const cal = Object.fromEntries(study.validation.map((r) => [r.metric, r]));
  const merit = Object.fromEntries(study.merit.map((m) => [m.name, m]));
  return {
    raw: { sc, head },
    text: {
      gasShare2024: pct(c("gas_share_2024"), 1),
      reTarget: pct(c("re_target_2030")),
      tspTarget: pct(c("tsp_re_target_2030")),
      indc: pct(c("indc_co2_intensity_cut_2030")),
      growth: pct(c("demand_growth"), 1),
      reserve: pct(c("reserve_margin")),
      gasPrice: num(c("gas_price_eur_per_mwh_th"), 1),
      demand2030: num(c("demand_2024_twh") * (1 + c("demand_growth")) ** 6, 1),
      peak2030: num(c("peak_ref_2030_mw")),
      algeriaShare: pct((c("gas_supply_royalty_2024_ktep") + c("gas_supply_purchases_2024_ktep")) / supply),
      gasForPowerShare: pct(c("gas_for_power_2024_ktep_ncv") / supply),
      domesticDrop: pct(1 - c("gas_supply_domestic_2024_ktep") / c("gas_supply_domestic_2023_ktep")),
      energyIndependence: pct(c("energy_independence_2024")),
      calGas: pct(Math.abs(cal.gas_fuel_for_power_twh_th.diff_pct) / 100, 1),
      s0Ocgt: num(sc.S0.new_cap_OCGT_mw),
      s110Cost: num(sc["S1-10"].avoided.cost_eur_per_mwh, 1),
      marg1015: num(marg("S1-10", "S1-15"), 1),
      splitGas: pct((gasGen("S0") - gasGen("S1-15")) / saved),
      splitRes: pct(1 - (gasGen("S0") - gasGen("S1-15")) / saved),
      coolingShare: pct(sc["S1-15C"].cooling_share),
      coolGain: pct(sc["S1-15C"].avoided.gas_mwh_th_per_mwh / head.gas_mwh_th_per_mwh - 1),
      flexCost: num(flex, 1),
      flexCo2: num(sc["S1-15"].co2_mt - sc["S2-300"].co2_mt, 2),
      flexPerMw: num(Math.round((flex * 1e6) / c("flex_cap_mw") / 1000) * 1000),
      meritCcgt: num(merit["Combined cycle, existing"].run_cost),
      meritOcgt: num(merit["Gas turbine / steam, existing"].run_cost),
    },
    count: { headCost: head.cost_eur_per_mwh, headGas: head.gas_mwh_th_per_mwh, headCo2: head.co2_t_per_mwh, headCap: head.capacity_mw_per_twh },
  };
}

function bindText(facts, study) {
  document.querySelectorAll("[data-f]").forEach((el) => { el.textContent = facts.text[el.dataset.f] ?? "?"; });
  document.querySelectorAll("[data-src]").forEach((el) => {
    const row = study.context[el.dataset.src];
    el.innerHTML = row.url ? `Source: <a href="${row.url}">${row.source.split(",")[0]}</a>` : `Source: ${row.source}`;
  });
  document.querySelectorAll("[data-count]").forEach((el) => {
    const target = facts.count[el.dataset.count], dec = Number(el.dataset.dec || 0);
    if (reduceMotion) { el.textContent = num(target, dec); return; }
    const t0 = performance.now(), dur = 1400;
    const tick = (t) => {
      const k = Math.min(1, (t - t0) / dur), e = 1 - (1 - k) ** 3;
      el.textContent = num(target * e, dec);
      if (k < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  });
}

// ---------- scroll reveal and active nav ----------
function reveal() {
  const io = new IntersectionObserver((entries) => entries.forEach((e) => {
    if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
  }), { rootMargin: "0px 0px -8% 0px" });
  document.querySelectorAll(".reveal").forEach((el) => io.observe(el));
  const links = [...document.querySelectorAll(".nav-links a")];
  const spy = new IntersectionObserver((entries) => entries.forEach((e) => {
    if (e.isIntersecting) links.forEach((a) => a.classList.toggle("active", a.getAttribute("href") === `#${e.target.id}`));
  }), { rootMargin: "-45% 0px -50% 0px" });
  document.querySelectorAll("main section[id]").forEach((s) => spy.observe(s));
}

// ---------- charts ----------
function chartDefaults() {
  Chart.defaults.color = INK2;
  Chart.defaults.font.family = '"Fira Sans", system-ui, sans-serif';
  Chart.defaults.font.size = 13;
  Chart.defaults.borderColor = GRID;
  Chart.defaults.plugins.legend.display = false;
  Chart.defaults.plugins.tooltip.backgroundColor = "rgba(11,18,32,0.95)";
  Chart.defaults.plugins.tooltip.borderColor = "rgba(148,178,220,0.28)";
  Chart.defaults.plugins.tooltip.borderWidth = 1;
  Chart.defaults.plugins.tooltip.padding = 10;
  Chart.defaults.animation = reduceMotion ? false : { duration: 700 };
}

function gasChart(study) {
  const c = (id) => study.context[id].value;
  new Chart(document.getElementById("ch-gas"), {
    type: "doughnut",
    data: { labels: ["Tunisian gas fields", "Royalty on Algerian transit gas", "Bought from Algeria"],
      datasets: [{ data: [c("gas_supply_domestic_2024_ktep"), c("gas_supply_royalty_2024_ktep"), c("gas_supply_purchases_2024_ktep")],
        backgroundColor: ["#199e70", "#3987e5", "#e66767"], borderColor: "#0b1220", borderWidth: 3 }] },
    options: { maintainAspectRatio: false, cutout: "62%",
      plugins: { legend: { display: true, position: "right", labels: { boxWidth: 12, boxHeight: 12, color: INK2 } },
        tooltip: { callbacks: { label: (ctx) => ` ${ctx.label}: ${num(ctx.raw)} ktep` } } } },
  });
}

function meritChart(study) {
  new Chart(document.getElementById("ch-merit"), {
    type: "bar",
    data: { labels: study.merit.map((m) => m.name),
      datasets: [{ data: study.merit.map((m) => m.run_cost), backgroundColor: ["#e66767", "#e66767", "#9085e9", "#9085e9"],
        borderRadius: 4, barThickness: 22 }] },
    options: { indexAxis: "y", maintainAspectRatio: false,
      scales: { x: { title: { display: true, text: "EUR per MWh of electricity" }, grid: { color: GRID } }, y: { grid: { display: false } } },
      plugins: { tooltip: { callbacks: { label: (ctx) => {
        const m = study.merit[ctx.dataIndex];
        return ` ${num(m.run_cost, 1)} EUR/MWh · ${pct(m.efficiency)} efficient · ${num(m.co2, 2)} t CO2/MWh`; } } } } },
  });
}

function capacityExplorer(study, facts) {
  const sc = facts.raw.sc;
  const grid = document.getElementById("scen-grid");
  study.scenarios.forEach((s, i) => {
    const b = document.createElement("button");
    b.className = "scen" + (s.code === "S0" ? " base" : "");
    b.dataset.code = s.code;
    b.setAttribute("aria-pressed", s.code === "S1-15" ? "true" : "false");
    b.innerHTML = `<span class="code">${s.code}</span><span class="name">${s.name}</span>`;
    grid.appendChild(b);
  });
  const capOf = (s) => ORDER.map((k) => ((sc[s][`cap_${k}_mw`] || 0) + (k === "hydro" ? sc[s].cap_ror_mw || 0 : 0)) / 1000);
  document.getElementById("cap-legend").innerHTML = ORDER.map((k) => `<span><i style="background:${COLORS[k]}"></i>${LABELS[k]}</span>`).join("");
  const refOf = (code) => (code.startsWith("G-lo") ? "G-lo-S0" : code.startsWith("G-hi") ? "G-hi-S0" : "S0");
  const chart = new Chart(document.getElementById("ch-cap"), {
    type: "bar",
    data: { labels: ["", ""], datasets: ORDER.map((k) => ({ label: LABELS[k], data: [0, 0], backgroundColor: COLORS[k], borderColor: "#0b1220", borderWidth: 1, borderRadius: 3, barThickness: 46 })) },
    options: { indexAxis: "y", maintainAspectRatio: false,
      scales: { x: { stacked: true, title: { display: true, text: "GW installed in 2030" }, grid: { color: GRID } }, y: { stacked: true, grid: { display: false }, ticks: { color: INK, font: { size: 14 } } } },
      plugins: { tooltip: { callbacks: { label: (ctx) => ` ${ctx.dataset.label}: ${num(ctx.raw, 2)} GW` } } } },
  });
  const deltas = document.getElementById("delta-row");
  const metric = (k, v, ref, unit, d, lowerIsGood = true) => {
    const diff = v - ref, cls = diff === 0 ? "" : (diff < 0) === lowerIsGood ? "down" : "up";
    const sign = diff > 0 ? "+" : diff < 0 ? "−" : "±";
    return `<div class="delta"><div class="k">${k}</div><div class="v">${num(v, d)} <span class="small">${unit}</span></div><div class="d ${cls}">${sign}${num(Math.abs(diff), d)} vs ref</div></div>`;
  };
  function show(code) {
    const ref = refOf(code);
    const codes = code === ref ? [code] : [ref, code];
    chart.data.labels = codes.map((c) => `${c}  ${sc[c].name}`);
    chart.data.datasets.forEach((ds, i) => { ds.data = codes.map((c) => capOf(c)[i]); });
    chart.update();
    document.getElementById("cap-title").textContent = code === ref ? `Installed capacity in 2030 · ${code}` : `Installed capacity in 2030 · ${code} vs ${ref}`;
    const s = sc[code], r = sc[ref];
    deltas.innerHTML = metric("System cost", s.system_cost_meur, r.system_cost_meur, "M EUR/yr", 0)
      + metric("Gas burnt", s.gas_use_twh_th, r.gas_use_twh_th, "TWh th", 2)
      + metric("CO2", s.co2_mt, r.co2_mt, "Mt", 2)
      + metric("Renewable share", s.res_share * 100, r.res_share * 100, "%", 0, false);
    grid.querySelectorAll(".scen").forEach((b) => b.setAttribute("aria-pressed", b.dataset.code === code ? "true" : "false"));
  }
  grid.addEventListener("click", (e) => { const b = e.target.closest(".scen"); if (b) show(b.dataset.code); });
  show("S1-15");
}

function avoidedChart(study) {
  const rows = study.scenarios.filter((s) => s.avoided);
  const units = { cost_eur_per_mwh: "EUR per MWh saved", co2_t_per_mwh: "t CO2 per MWh saved", gas_mwh_th_per_mwh: "MWh of gas per MWh saved", capacity_mw_per_twh: "MW per TWh saved per year" };
  const chart = new Chart(document.getElementById("ch-avoid"), {
    type: "bar",
    data: { labels: rows.map((s) => [`${s.code}`, s.name]), datasets: [{ data: [], borderRadius: 4, barThickness: 20,
      backgroundColor: rows.map((s) => (s.code === "S1-15" ? "#ffb347" : "#3fc1ff")) }] },
    options: { indexAxis: "y", maintainAspectRatio: false,
      scales: { x: { grid: { color: GRID }, title: { display: true } }, y: { grid: { display: false }, ticks: { color: INK } } },
      plugins: { tooltip: { callbacks: { label: (ctx) => ` ${num(ctx.raw, ctx.raw < 5 ? 2 : 1)} · vs ${rows[ctx.dataIndex].code.startsWith("G-") ? rows[ctx.dataIndex].code.slice(0, 4) + "-S0" : "S0"}` } } } },
  });
  const seg = document.getElementById("avoid-seg");
  const set = (m) => {
    chart.data.datasets[0].data = rows.map((s) => s.avoided[m]);
    chart.options.scales.x.title.text = units[m];
    chart.update();
    seg.querySelectorAll("button").forEach((b) => b.setAttribute("aria-pressed", b.dataset.m === m ? "true" : "false"));
  };
  seg.addEventListener("click", (e) => { if (e.target.dataset.m) set(e.target.dataset.m); });
  set("cost_eur_per_mwh");
}

function weekChart(week) {
  const start = new Date(week.start + "Z");
  const labels = week.S0.load_planned.map((_, i) => new Date(start.getTime() + i * 3600e3));
  const fmt = (d) => d.toLocaleString("en-GB", { day: "2-digit", month: "short", hour: "2-digit", timeZone: "UTC" });
  // Generation is stacked by hand (each area's top = running sum), so the load lines stay unstacked on the same axis.
  const datasets = (s) => {
    let acc = null;
    const gen = ORDER.filter((k) => week[s].dispatch[k]).map((k, i) => {
      const own = week[s].dispatch[k].map((v) => v / 1000);
      acc = acc ? acc.map((a, j) => a + own[j]) : own.slice();
      return { label: LABELS[k], own, data: acc.slice(), backgroundColor: COLORS[k] + "e6", borderWidth: 0,
        fill: i === 0 ? "origin" : "-1", pointRadius: 0, tension: 0.25 };
    });
    const lines = [{ label: "Load (planned)", data: week[s].load_planned.map((v) => v / 1000), borderColor: INK, borderWidth: 1.6, fill: false, pointRadius: 0, tension: 0.25 }];
    if (s === "S2-300") lines.push({ label: "Load after shifting", data: week[s].load_served.map((v) => v / 1000), borderColor: "#ffb347", borderDash: [5, 4], borderWidth: 1.8, fill: false, pointRadius: 0, tension: 0.25 });
    return [...gen, ...lines];
  };
  const chart = new Chart(document.getElementById("ch-week"), {
    type: "line", data: { labels, datasets: datasets("S0") },
    options: { maintainAspectRatio: false, interaction: { mode: "index", intersect: false },
      scales: { x: { ticks: { callback: (v, i) => (i % 24 === 0 ? fmt(labels[i]).slice(0, 6) : ""), autoSkip: false, maxRotation: 0 }, grid: { color: (c) => (c.index % 24 === 0 ? GRID : "transparent") } },
        y: { title: { display: true, text: "GW" }, grid: { color: GRID }, beginAtZero: true } },
      plugins: { tooltip: { callbacks: { title: (items) => `${fmt(labels[items[0].dataIndex])}:00 UTC`,
        label: (ctx) => ` ${ctx.dataset.label}: ${num((ctx.dataset.own || ctx.dataset.data)[ctx.dataIndex], 2)} GW` } } } },
  });
  const legend = () => { document.getElementById("week-legend").innerHTML = chart.data.datasets.map((d) =>
    `<span><i style="background:${d.backgroundColor || d.borderColor}"></i>${d.label}</span>`).join(""); };
  legend();
  const seg = document.getElementById("week-seg");
  seg.addEventListener("click", (e) => {
    const s = e.target.dataset.w; if (!s) return;
    chart.data.datasets = datasets(s); chart.update(); legend();
    seg.querySelectorAll("button").forEach((b) => b.setAttribute("aria-pressed", b.dataset.w === s ? "true" : "false"));
  });
}

function priceChart(prices) {
  const colors = { S0: "#3fc1ff", "S1-15": "#ffb347", "S2-300": "#34d399" };
  new Chart(document.getElementById("ch-price"), {
    type: "line",
    data: { labels: prices.S0.map((_, i) => i * 10), datasets: Object.entries(prices).map(([s, v]) => ({ label: s, data: v, borderColor: colors[s], borderWidth: 2, pointRadius: 0, stepped: true })) },
    options: { maintainAspectRatio: false, interaction: { mode: "index", intersect: false },
      scales: { x: { title: { display: true, text: "hours of the year, most expensive first" }, ticks: { callback: (v, i) => (i % 100 === 0 ? num(i * 10) : ""), autoSkip: false, maxRotation: 0 }, grid: { display: false } },
        y: { title: { display: true, text: "EUR/MWh" }, grid: { color: GRID } } },
      plugins: { legend: { display: true, position: "top", align: "end", labels: { boxWidth: 12, boxHeight: 2, color: INK2 } },
        tooltip: { callbacks: { title: (it) => `hour ${num(it[0].dataIndex * 10)}`, label: (ctx) => ` ${ctx.dataset.label}: ${num(ctx.raw, 1)} EUR/MWh` } } } },
  });
}

function gasTable(facts) {
  const sc = facts.raw.sc;
  const rows = [["Avoided cost per MWh saved", (s) => `${num(sc[s].avoided.cost_eur_per_mwh)} EUR`],
    ["Avoided CO2 per MWh saved", (s) => `${num(sc[s].avoided.co2_t_per_mwh, 2)} t`],
    ["Avoided gas per MWh saved", (s) => `${num(sc[s].avoided.gas_mwh_th_per_mwh, 2)} MWh`]];
  const refRow = ["Renewable share, reference run", (s) => pct(sc[s === "S1-15" ? "S0" : s.replace("S1-15", "S0")].res_share)];
  const cols = [["Cheap gas (×0.5)", "G-lo-S1-15"], ["Base gas price", "S1-15"], ["Expensive gas (×1.5)", "G-hi-S1-15"]];
  document.getElementById("gas-table").innerHTML = `<thead><tr><th></th>${cols.map(([h]) => `<th class="num">${h}</th>`).join("")}</tr></thead><tbody>`
    + [...rows, refRow].map(([k, f]) => `<tr><td>${k}</td>${cols.map(([, s]) => `<td class="num">${f(s)}</td>`).join("")}</tr>`).join("") + "</tbody>";
}

function validationTable(study) {
  const want = [["cap_thermal_mw", "Gas power plants", "MW", 0, "cal", "set by calibration"],
    ["peak_mw", "Peak demand", "MW", 0, "cal", "set by calibration"],
    ["gas_fleet_efficiency_ncv", "Gas fleet efficiency", "", 2, "cal", "fitted"],
    ["gas_fuel_for_power_twh_th", "Gas burnt for power", "TWh th", 1, "chk", "consistency check"],
    ["gas_share", "Gas share of generation", "", 3, "chk", "close"],
    ["gen_wind_twh", "Wind generation", "TWh", 2, "off", "not calibrated"],
    ["gen_solar_twh", "Solar generation", "TWh", 2, "off", "not calibrated"]];
  const v = Object.fromEntries(study.validation.map((r) => [r.metric, r]));
  const fmt = (x, d, unit) => (unit === "" && x < 1.5 ? pct(x, 1) : num(x, d));
  document.getElementById("val-table").innerHTML = `<thead><tr><th>2024</th><th class="num">Model</th><th class="num">Official</th><th class="num">Difference</th><th>What it shows</th></tr></thead><tbody>`
    + want.map(([id, label, unit, d, cls, tag]) => { const r = v[id];
      return `<tr><td>${label}${unit ? ` <span class="small">(${unit})</span>` : ""}</td><td class="num">${fmt(r.model, d, unit)}</td><td class="num">${fmt(r.reference, d, unit)}</td><td class="num">${r.diff_pct >= 0 ? "+" : "−"}${num(Math.abs(r.diff_pct), 1)}%</td><td><span class="tag ${cls}">${tag}</span></td></tr>`; }).join("") + "</tbody>";
}

// ---------- start ----------
async function main() {
  const [study, week, prices] = await Promise.all([getJSON("study"), getJSON("peakweek"), getJSON("prices")]);
  const facts = computeFacts(study);
  bindText(facts, study);
  reveal();
  chartDefaults();
  gasChart(study); meritChart(study); capacityExplorer(study, facts); avoidedChart(study);
  weekChart(week); priceChart(prices); gasTable(facts); validationTable(study);
  startHero(document.getElementById("hero-scene"), getJSON("grid"), reduceMotion);
  startLandscape(document.getElementById("ls"), getJSON("hourly"), reduceMotion);
}

window.addEventListener("load", main);
