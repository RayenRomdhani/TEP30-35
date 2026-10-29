// Page logic. Every number on the page is computed here from site/data/*.json (written by
// scripts/export_site_data.py from the study's results); the HTML holds none of them.

import { createDay } from "./day.js";
import { drawMap, drawRoad, drawWeek } from "./graphics.js";

const getJSON = (n) => fetch(`data/${n}.json`, { cache: "no-cache" }).then((r) => r.json());
const fmt = (x, d = 0) => x.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });
const pct = (x, d = 0) => `${fmt(x * 100, d)}%`;
const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];

const LABELS = { CCGT: "Gas, combined cycle", OCGT: "Gas turbines and steam", hydro: "Hydro", onwind: "Wind", solar: "Solar", battery: "Batteries" };
const ORDER = ["CCGT", "OCGT", "hydro", "onwind", "solar", "battery"];
// technologies take the colours of the chapters they belong to; one set per background so each stays legible
const ON_PEAK = { CCGT: "#1b1306", OCGT: "#5a1414", hydro: "#0b1f33", onwind: "#c9d6df", solar: "#f2c230", battery: "#fff3e8" };
const ON_DUSK = { CCGT: "#f3ede2", OCGT: "#e2753f", hydro: "#9fd3c0", onwind: "#c9d6df", solar: "#f2c230", battery: "#e87ba4" };
const HUD_KEYS = { gas: "#e66767", solar: "#f2c230", wind: "#7fb6e8", load: "#f3ede2" };

// ---------- facts ----------
function facts(study, grid) {
  const sc = Object.fromEntries(study.scenarios.map((s) => [s.code, s]));
  const c = (id) => study.context[id].value, head = sc["S1-15"].avoided;
  const supply = c("gas_supply_domestic_2024_ktep") + c("gas_supply_royalty_2024_ktep") + c("gas_supply_purchases_2024_ktep");
  const marg = (sc["S1-10"].system_cost_meur - sc["S1-15"].system_cost_meur) / (sc["S1-10"].demand_twh - sc["S1-15"].demand_twh);
  const cal = study.validation.find((r) => r.metric === "gas_fuel_for_power_twh_th");
  const flex = sc["S1-15"].system_cost_meur - sc["S2-300"].system_cost_meur;
  return {
    sc, supply,
    text: {
      gasShare: pct(c("gas_share_2024"), 1), cost: fmt(head.cost_eur_per_mwh), gas: fmt(head.gas_mwh_th_per_mwh, 2), co2: fmt(head.co2_t_per_mwh, 2),
      gasForPower: pct(c("gas_for_power_2024_ktep_ncv") / supply), independence: pct(c("energy_independence_2024")),
      lineCount: fmt(grid.lines.length), tsp: pct(c("tsp_re_target_2030")), indc: pct(c("indc_co2_intensity_cut_2030")),
      target: pct(c("re_target_2030")), reserve: pct(c("reserve_margin")), growth: pct(c("demand_growth"), 1),
      demand2030: fmt(c("demand_2024_twh") * (1 + c("demand_growth")) ** 6, 1), calGas: pct(Math.abs(cal.diff_pct) / 100, 1),
      s0Ocgt: fmt(sc.S0.new_cap_OCGT_mw), s110: fmt(sc["S1-10"].avoided.cost_eur_per_mwh, 1), marg: fmt(marg, 1),
      coolGain: pct(sc["S1-15C"].avoided.gas_mwh_th_per_mwh / head.gas_mwh_th_per_mwh - 1), coolShare: pct(sc["S1-15C"].cooling_share),
      flex: fmt(flex, 1), flexCo2: fmt(sc["S1-15"].co2_mt - sc["S2-300"].co2_mt, 2),
    },
    count: { cost: head.cost_eur_per_mwh, gas: head.gas_mwh_th_per_mwh, co2: head.co2_t_per_mwh, cap: head.capacity_mw_per_twh },
  };
}

function fill(f, study) {
  $$("[data-f]").forEach((e) => { e.textContent = f.text[e.dataset.f] ?? ""; });
  $$("[data-src]").forEach((e) => {
    const r = study.context[e.dataset.src];
    e.innerHTML = r.url ? `Source: <a href="${r.url}">${r.source.split(",")[0]}</a>` : `Source: ${r.source}`;
  });
}

// ---------- chrome: bar colour per chapter, rises, word-by-word statements, counters ----------
function chrome(f) {
  const bar = $(".bar"), act = $(".act", bar);
  const paint = (sec) => { const cs = getComputedStyle(sec); bar.style.background = cs.backgroundColor; bar.style.color = cs.color;
    act.style.background = cs.color; act.style.color = cs.backgroundColor; };
  const io = new IntersectionObserver((es) => es.forEach((e) => e.isIntersecting && paint(e.target)), { rootMargin: "0px 0px -92% 0px" });
  $$("[data-chapter], #day").forEach((s) => io.observe(s));
  const rise = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { e.target.classList.add("in"); rise.unobserve(e.target); } }),
    { rootMargin: "0px 0px -8% 0px" });
  $$(".rise").forEach((el) => { const sib = [...el.parentElement.children].filter((x) => x.classList.contains("rise"));
    el.style.transitionDelay = `${Math.min(sib.indexOf(el), 4) * 80}ms`; rise.observe(el); });
  $$(".words").forEach((p) => {
    p.innerHTML = p.textContent.trim().split(/\s+/).map((w) => `<span>${w}</span>`).join(" ");
    const io2 = new IntersectionObserver((es) => es.forEach((e) => e.target.classList.toggle("on", e.isIntersecting || e.boundingClientRect.top < 0)),
      { rootMargin: "0px 0px -42% 0px" });
    $$("span", p).forEach((s) => io2.observe(s));
  });
  const counters = new IntersectionObserver((es) => es.forEach((e) => {
    if (!e.isIntersecting) return; counters.unobserve(e.target);
    const el = e.target, target = f.count[el.dataset.count], dec = +(el.dataset.dec || 0);
    if (reduce) { el.textContent = fmt(target, dec); return; }
    const t0 = performance.now(); (function tick(t) { const k = Math.min(1, (t - t0) / 1600);
      el.textContent = fmt(target * (1 - (1 - k) ** 4), dec); if (k < 1) requestAnimationFrame(tick); })(t0);
  }), { rootMargin: "0px 0px -15% 0px" });
  $$("[data-count]").forEach((e) => counters.observe(e));
}

// ---------- the day ----------
function peakDay(week, scen) {
  const start = new Date(week.start + "Z"), peak = new Date(week.peak + "Z");
  const first = Math.round((peak - start) / 3600e3) - peak.getUTCHours() - 1;   // 00:00 in Tunis = 23:00 UTC the day before
  const d = week[scen].dispatch, take = (a) => a.slice(first, first + 25);
  return { gas: take(d.CCGT).map((v, i) => v + (d.OCGT ? d.OCGT[first + i] : 0)), solar: take(d.solar), wind: take(d.onwind),
    load: take(scen === "S2-300" ? week[scen].load_served : week[scen].load_planned),
    date: new Date(start.getTime() + (first + 1) * 3600e3), peakLocal: peak.getUTCHours() + 1 };
}
const at = (a, h) => { const i = Math.floor(h); return a[i] + (a[Math.min(i + 1, a.length - 1)] - a[i]) * (h - i); };
function caption(h, v, peakH) {
  if (h < 5.5) return `Night. The country still draws ${fmt(v.load / 1000, 1)} GW, and ${pct(v.gas / v.load)} of it comes from gas.`;
  if (h < 9) return "Sunrise. The solar field wakes up and starts pushing the gas plants down.";
  if (h < peakH - 1.5) return `Midday over the Sahara: solar covers ${pct(v.solar / v.load)} of demand.`;
  if (h < peakH + 1.5) return `The model's peak: ${fmt(v.load / 1000, 1)} GW, and the sun is already low. This is the hour the system is built for.`;
  if (h < 21) return "Night falls and gas carries the country: the evening ridge, the most expensive hours of the day.";
  return "Midnight again. Tomorrow, the same climb.";
}
function runDay(week) {
  const sec = $("#day"), scene = createDay($("canvas", sec));
  const both = [peakDay(week, "S0"), peakDay(week, "S2-300")];
  const max = (k) => Math.max(...both.flatMap((d) => d[k]));
  const scale = { gas: max("gas"), solar: max("solar"), wind: max("wind"), load: max("load") };
  let data = both[0];
  $("#day-date").textContent = `${data.date.toLocaleDateString("en-GB", { day: "numeric", month: "long", timeZone: "UTC" })}, the model's summer peak day · Tunis time`;
  $$("[data-key]", sec).forEach((i) => { i.style.background = HUD_KEYS[i.dataset.key]; });
  let visible = false, raf = 0;
  function update() {
    const p = Math.min(1, Math.max(0, -sec.getBoundingClientRect().top / (sec.offsetHeight - innerHeight))), h = p * 24;
    const v = { gas: at(data.gas, h), solar: at(data.solar, h), wind: at(data.wind, h), load: at(data.load, h) };
    scene.set({ hour: h, progress: p, gas: v.gas / scale.gas, solar: v.solar / scale.solar, wind: v.wind / scale.wind, load: v.load / scale.load });
    $("#clock").textContent = `${String(Math.floor(h) % 24).padStart(2, "0")}:${String(Math.floor((h % 1) * 60)).padStart(2, "0")}`;
    $("#caption").textContent = caption(h, v, data.peakLocal);
    for (const k of ["gas", "solar", "wind", "load"]) $(`[data-mix="${k}"]`, sec).textContent = fmt(v[k] / 1000, 2);
    $(".hud", sec).style.color = h > 7.2 && h < 18.3 ? "#10202c" : "#f3ede2";
  }
  function loop(t) { if (!visible) { raf = 0; return; } update(); scene.render(t); raf = requestAnimationFrame(loop); }
  new IntersectionObserver(([e]) => { visible = e.isIntersecting; if (visible && !raf) raf = requestAnimationFrame(loop); }).observe(sec);
  $(".switch", sec).addEventListener("click", (e) => { const b = e.target.closest("button"); if (!b) return;
    data = both[b.dataset.s === "S0" ? 0 : 1];
    $$(".switch button", sec).forEach((x) => x.setAttribute("aria-pressed", x === b ? "true" : "false")); });
}

// ---------- the model: steps slide sideways while the section is pinned ----------
function runSteps() {
  const sec = $("#steps"), track = $(".steps-track", sec);
  if (reduce || innerWidth < 760) return;
  let ticking = false;
  const move = () => { ticking = false;
    const p = Math.min(1, Math.max(0, -sec.getBoundingClientRect().top / (sec.offsetHeight - innerHeight)));
    track.style.transform = `translateX(${-p * Math.max(0, track.scrollWidth - innerWidth)}px)`; };
  addEventListener("scroll", () => { if (!ticking) { ticking = true; requestAnimationFrame(move); } }, { passive: true });
  move();
}

// ---------- the answer: split bar and the live chooser ----------
function splitBar(f) {
  const s = f.sc, saved = s.S0.demand_twh - s["S1-15"].demand_twh;
  const gasGen = (k) => s[k].gen_CCGT_twh + s[k].gen_OCGT_twh, g = (gasGen("S0") - gasGen("S1-15")) / saved;
  $("#split-bar").innerHTML = `<div style="flex:${g};background:#1b1306;color:#fff3e8">${pct(g)} gas</div>`
    + `<div style="flex:${1 - g};background:#f2c230;color:#1b1306">${pct(1 - g)} solar and wind not built</div>`;
}
function chooser(f) {
  const s = f.sc, box = $("#chooser"), chips = $(".chips", box);
  const options = [["S1-10", "Save 10%"], ["S1-15", "Save 15%"], ["S1-20", "Save 20%"], ["S1-15C", "15%, cooling first"],
    ["S2-300", "15% + 300 MW shift"], ["S2-600", "15% + 600 MW shift"]];
  chips.innerHTML = options.map(([c, l]) => `<button data-v="${c}" aria-pressed="${c === "S1-15"}"><span>${l}</span></button>`).join("");
  const capOf = (c) => ORDER.map((k) => ((s[c][`cap_${k}_mw`] || 0) + (k === "hydro" ? s[c].cap_ror_mw || 0 : 0)));
  const maxTotal = Math.max(...Object.keys(s).filter((c) => !c.startsWith("G-")).map((c) => capOf(c).reduce((a, b) => a + b, 0)));
  $("#cap-legend").innerHTML = ORDER.map((k) => `<span><i style="background:${ON_PEAK[k]}"></i>${LABELS[k]}</span>`).join("");
  const row = (label, c) => { const cap = capOf(c), tot = cap.reduce((a, b) => a + b, 0);
    return `<div class="cap-row"><span>${label} · ${fmt(tot / 1000, 1)} GW</span><div class="track" style="width:${(tot / maxTotal) * 100}%">`
      + cap.map((v, i) => `<div style="flex-grow:${v};background:${ON_PEAK[ORDER[i]]}" title="${LABELS[ORDER[i]]}: ${fmt(v)} MW"></div>`).join("") + "</div></div>"; };
  function show(c) {
    const a = s[c].avoided;
    $('[data-out="cost"]', box).textContent = fmt(a.cost_eur_per_mwh, 1);
    $('[data-out="co2"]', box).textContent = fmt(a.co2_t_per_mwh, 2);
    $('[data-out="gas"]', box).textContent = fmt(a.gas_mwh_th_per_mwh, 2);
    $('[data-out="total"]', box).textContent = fmt(s.S0.system_cost_meur - s[c].system_cost_meur);
    $("#cap-bars").innerHTML = row("2030 as planned", "S0") + row(options.find((o) => o[0] === c)[1], c);
    $$("button", chips).forEach((b) => b.setAttribute("aria-pressed", b.dataset.v === c ? "true" : "false"));
  }
  chips.addEventListener("click", (e) => { const b = e.target.closest("button"); if (b) show(b.dataset.v); });
  show("S1-15");
}

// ---------- the evening: the week chart and the gas-price table ----------
function week(weekData) {
  const svg = $("#week"), group = $('[data-group="week"]');
  const draw = (scen) => {
    const names = drawWeek(svg, weekData, scen, ON_DUSK, LABELS, ORDER);
    $("#week-legend").innerHTML = ORDER.filter((k) => weekData[scen].dispatch[k]).map((k) => `<span><i style="background:${ON_DUSK[k]}"></i>${LABELS[k]}</span>`).join("")
      + `<span><i style="background:currentColor"></i>Demand${scen === "S2-300" ? " (dashed: after shifting)" : ""}</span>`;
    $$("button", group).forEach((b) => b.setAttribute("aria-pressed", b.dataset.v === scen ? "true" : "false"));
    return names;
  };
  group.addEventListener("click", (e) => { const b = e.target.closest("button"); if (b) draw(b.dataset.v); });
  draw("S0");
}
function flip(f) {
  const s = f.sc, cols = [["Gas at half price", "G-lo-S1-15", "G-lo-S0"], ["Gas as forecast", "S1-15", "S0"], ["Gas 50% dearer", "G-hi-S1-15", "G-hi-S0"]];
  const rows = [["Cost avoided per MWh saved", (c) => `${fmt(s[c].avoided.cost_eur_per_mwh)} EUR`],
    ["CO2 avoided per MWh saved", (c) => `${fmt(s[c].avoided.co2_t_per_mwh, 2)} t`],
    ["Gas avoided per MWh saved", (c) => `${fmt(s[c].avoided.gas_mwh_th_per_mwh, 2)} MWh`],
    ["Renewable share without the saving", (c, r) => pct(s[r].res_share)]];
  $("#flip").innerHTML = `<thead><tr><th></th>${cols.map(([h]) => `<th class="num">${h}</th>`).join("")}</tr></thead><tbody>`
    + rows.map(([k, fn]) => `<tr><td>${k}</td>${cols.map(([, c, r]) => `<td class="num">${fn(c, r)}</td>`).join("")}</tr>`).join("") + "</tbody>";
}
function validation(study) {
  const want = [["cap_thermal_mw", "Gas plants (MW)", 0, "set by calibration"], ["peak_mw", "Peak demand (MW)", 0, "set by calibration"],
    ["gas_fuel_for_power_twh_th", "Gas burnt for power (TWh)", 1, "consistency check"], ["gas_share", "Share of generation from gas", -1, "close"],
    ["gen_wind_twh", "Wind generation (TWh)", 2, "not calibrated, too high"], ["gen_solar_twh", "Solar generation (TWh)", 2, "not calibrated, too high"]];
  const v = Object.fromEntries(study.validation.map((r) => [r.metric, r]));
  const show = (x, d) => (d < 0 ? pct(x, 1) : fmt(x, d));
  $("#val").innerHTML = "<thead><tr><th>2024</th><th class='num'>Model</th><th class='num'>Official</th><th>What it shows</th></tr></thead><tbody>"
    + want.map(([id, l, d, how]) => `<tr><td>${l}</td><td class="num">${show(v[id].model, d)}</td><td class="num">${show(v[id].reference, d)}</td><td class="how">${how}</td></tr>`).join("") + "</tbody>";
}
function bar3(f, study) {
  const c = (id) => study.context[id].value;
  const parts = [["Tunisian gas fields", c("gas_supply_domestic_2024_ktep"), "#0b1f33", "#f3ede2"],
    ["Royalty on Algerian gas crossing to Italy", c("gas_supply_royalty_2024_ktep"), "#5a7d96", "#f3ede2"],
    ["Gas bought from Algeria", c("gas_supply_purchases_2024_ktep"), "#d9481c", "#fff3e8"]];
  $("#bar3").innerHTML = parts.map(([l, v, bg, ink]) => `<div style="flex:${v};background:${bg};color:${ink}"><span class="p">${pct(v / f.supply)}</span><span class="n">${l} · ${fmt(v)} ktep</span></div>`).join("");
}

// ---------- the road to 2030: the year-by-year pathway ----------
function road(pw) {
  const L = (id) => pw.limits[id].value, years = [...pw.history.map((h) => h.year), ...pw.scenarios.S0.map((r) => r.year)];
  const committed = Object.entries(pw.committed).filter(([y]) => y >= 2025 && y <= 2028).reduce((a, [, mw]) => a + mw, 0);
  const last = (c) => pw.scenarios[c][pw.scenarios[c].length - 1];
  const s0 = last("S0").res_share, s1 = last("S1-15").res_share;
  const text = {
    solar: fmt(L("pathway_solar_extra_mw_per_year")), solarYear: "2024", windYear: L("pathway_wind_first_year"),
    wind: fmt(L("pathway_wind_extra_mw_per_year")), battery: fmt(L("pathway_battery_mw")), batteryYear: L("pathway_battery_first_year"),
    batteryMwh: fmt(L("pathway_battery_mwh")), committed: fmt(committed / 1000, 1), s0Share: pct(s0),
    gapText: `At the pace Tunisia has shown, renewables reach ${pct(s0)} of generation in 2030, ${fmt((pw.target - s0) * 100)} points short of the ${pct(pw.target)} target. `
      + `Saving 15% by 2030 lifts that to ${pct(s1)}: the same panels and turbines cover a larger part of a smaller demand.`,
  };
  $$("[data-p]").forEach((e) => { e.textContent = text[e.dataset.p] ?? ""; });

  const options = [["S0", "As planned"], ["S1-15", "Save 15%"], ["S2-300", "15% + 300 MW shift"], ["G-hi-S0", "Gas 50% dearer"]];
  const group = $('[data-group="road"]'), svg = $("#road-chart");
  group.innerHTML = options.map(([c, l]) => `<button data-v="${c}" aria-pressed="${c === "S1-15"}"><span>${l}</span></button>`).join("");
  const points = (c) => [...pw.history, ...pw.scenarios[c]].map((r) => ({ year: r.year, v: r.res_share }));
  let seen = false;
  const draw = (c) => {
    const series = [...(c === "S0" ? [] : [{ key: "S0", points: points("S0") }]), { key: c, points: points(c), strong: true }];
    const paths = drawRoad(svg, series, pw.target, years);
    if (!reduce && !seen) paths.forEach((p) => { const len = p.getTotalLength(); p.style.strokeDasharray = len; p.style.strokeDashoffset = len; });
    $$("button", group).forEach((b) => b.setAttribute("aria-pressed", b.dataset.v === c ? "true" : "false"));
  };
  group.addEventListener("click", (e) => { const b = e.target.closest("button"); if (b) draw(b.dataset.v); });
  draw("S1-15");
  new IntersectionObserver(([e], obs) => { if (!e.isIntersecting) return; obs.disconnect(); seen = true;
    $$(".line", svg).forEach((p) => { p.style.strokeDashoffset = 0; }); }, { rootMargin: "0px 0px -25% 0px" }).observe(svg);

  const rows = pw.avoided["S1-15"];
  $("#road-table").innerHTML = "<thead><tr><th>Year</th><th class='num'>Cost avoided per MWh saved</th><th class='num'>Gas avoided per MWh saved</th><th class='num'>CO2 avoided per MWh saved</th></tr></thead><tbody>"
    + rows.map((r) => `<tr><td>${r.year === "2027-2030" ? "All four years" : r.year}</td><td class="num">${fmt(r.cost_eur_per_mwh)} EUR</td>`
      + `<td class="num">${fmt(r.gas_mwh_th_per_mwh, 2)} MWh</td><td class="num">${fmt(r.co2_t_per_mwh, 2)} t</td></tr>`).join("") + "</tbody>";
}

// ---------- start ----------
async function main() {
  const [study, weekData, grid] = await Promise.all([getJSON("study"), getJSON("peakweek"), getJSON("grid")]);
  const f = facts(study, grid);
  fill(f, study); chrome(f);
  runDay(weekData); runSteps(); splitBar(f); chooser(f); week(weekData); flip(f); validation(study); bar3(f, study);
  drawMap($("#map"), grid);
  getJSON("pathway").then(road).catch(() => { $("#road").hidden = true; });   // no pathway results yet: hide the chapter
  // the year surface is heavy (437 kB): load it when the reader gets close
  const yc = $("#year");
  new IntersectionObserver(async ([e], obs) => {
    if (!e.isIntersecting) return; obs.disconnect();
    const [{ startYear }, hourly] = await Promise.all([import("./year.js"), getJSON("hourly")]);
    startYear(yc, hourly, { total: $("#year-total"), label: $("#year-label"), groups: $$('#model .chips[data-group]') }, reduce);
  }, { rootMargin: "600px 0px" }).observe(yc);
}
main();
