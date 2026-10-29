// Drawn graphics in the page's own language: the grid map and the week of hourly output.
// Plain SVG, coloured by the chapter's ink (currentColor), no chart library.

const NS = "http://www.w3.org/2000/svg";
const el = (name, attrs = {}, parent) => {
  const e = document.createElementNS(NS, name);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  if (parent) parent.appendChild(e);
  return e;
};

// ---------- Tunisia: Natural Earth outline + OpenStreetMap grid + the model's two nodes ----------
export async function drawMap(svg, grid) {
  const world = await fetch("https://cdn.jsdelivr.net/npm/world-atlas@2.0.2/countries-50m.json").then((r) => r.json());
  const tn = topojson.feature(world, world.objects.countries).features.find((f) => String(f.id) === "788");
  const polys = tn.geometry.type === "Polygon" ? [tn.geometry.coordinates] : tn.geometry.coordinates;
  const lat0 = 34, kx = Math.cos((lat0 * Math.PI) / 180);                 // equirectangular, true shape at 34° N
  const W = 7.6, E = 11.7, S = 30.1, N = 37.6, scale = 100;
  const X = (lon) => (lon - W) * kx * scale, Y = (lat) => (N - lat) * scale;
  svg.setAttribute("viewBox", `-150 -20 ${(E - W) * kx * scale + 180} ${(N - S) * scale + 40}`);
  const path = (ring) => ring.map(([lon, lat], i) => `${i ? "L" : "M"}${X(lon).toFixed(1)},${Y(lat).toFixed(1)}`).join("") + "Z";
  el("path", { d: polys.map((rings) => rings.map(path).join("")).join(""), fill: "currentColor", "fill-opacity": "0.1", stroke: "none" }, svg);
  const lines = el("g", { fill: "none", stroke: "currentColor", "stroke-linecap": "round", "stroke-linejoin": "round" }, svg);
  grid.lines.forEach(({ kv, c }) => el("path", {
    d: c.map(([lon, lat], i) => `${i ? "L" : "M"}${X(lon).toFixed(1)},${Y(lat).toFixed(1)}`).join(""),
    "stroke-width": kv >= 400 ? 3.2 : kv >= 220 ? 2 : 1.1, "stroke-opacity": kv >= 220 ? 0.95 : 0.5 }, lines));
  grid.nodes.forEach((n, i) => {
    const g = el("g", { transform: `translate(${X(n.lon)},${Y(n.lat)})` }, svg);
    el("circle", { r: 16, fill: "currentColor" }, g);
    el("circle", { r: 30, fill: "none", stroke: "currentColor", "stroke-width": 2, class: "pulse" }, g);
    el("text", { x: 26, y: 8, "font-size": 26, "font-weight": 600, fill: "currentColor" }, g).textContent = i === 0 ? "North" : "South";
  });
  el("text", { x: -16, y: (N - 33.4) * scale, "text-anchor": "end", "font-size": 24, fill: "currentColor", "fill-opacity": 0.75 }, svg).textContent = "Algeria";
  el("text", { x: (E - W) * kx * scale - 150, y: 30, "font-size": 24, fill: "currentColor", "fill-opacity": 0.75 }, svg).textContent = "Mediterranean";
}

// ---------- the road: renewable share year by year, one line per scenario, against the target ----------
// series: [{ key, points: [{year, v}], strong }] ; shared history points sit at the start of every line
export function drawRoad(svg, series, target, years) {
  svg.textContent = "";
  const W = 1200, H = 460, pad = { l: 64, r: 120, t: 24, b: 48 };
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  const max = Math.max(target * 1.15, ...series.flatMap((s) => s.points.map((p) => p.v))) * 1.05;
  const x = (y) => pad.l + ((y - years[0]) / (years[years.length - 1] - years[0])) * (W - pad.l - pad.r);
  const y = (v) => H - pad.b - (v / max) * (H - pad.t - pad.b);
  for (let k = 0; k <= max + 1e-9; k += 0.1) {
    el("text", { x: pad.l - 14, y: y(k) + 6, "text-anchor": "end", "font-size": 18, fill: "currentColor", "fill-opacity": 0.7 }, svg).textContent = `${Math.round(k * 100)}%`;
  }
  years.forEach((yr) => { el("text", { x: x(yr), y: H - 12, "text-anchor": "middle", "font-size": 18, fill: "currentColor", "fill-opacity": 0.7 }, svg).textContent = yr; });
  el("line", { x1: pad.l, x2: W - pad.r, y1: y(target), y2: y(target), stroke: "currentColor", "stroke-width": 2, "stroke-dasharray": "10 8" }, svg);
  el("text", { x: W - pad.r + 12, y: y(target) + 6, "font-size": 18, fill: "currentColor" }, svg).textContent = `Target ${Math.round(target * 100)}%`;
  const drawn = [];
  series.forEach((s) => {
    const d = s.points.map((p, i) => `${i ? "L" : "M"}${x(p.year).toFixed(1)},${y(p.v).toFixed(1)}`).join("");
    const path = el("path", { d, fill: "none", stroke: "currentColor", "stroke-width": s.strong ? 4 : 2, "stroke-opacity": s.strong ? 1 : 0.45,
      "stroke-linejoin": "round", class: "line" }, svg);
    s.points.forEach((p) => el("circle", { cx: x(p.year), cy: y(p.v), r: s.strong ? 7 : 4, fill: "currentColor", "fill-opacity": s.strong ? 1 : 0.45 }, svg));
    const last = s.points[s.points.length - 1];
    if (s.strong) el("text", { x: x(last.year) + 16, y: y(last.v) + 7, "font-size": 22, "font-weight": 600, fill: "currentColor" }, svg).textContent = `${Math.round(last.v * 100)}%`;
    drawn.push(path);
  });
  return drawn;
}

// ---------- a week of hourly output, stacked, with the load line ----------
export function drawWeek(svg, week, scen, colors, labels, order) {
  svg.textContent = "";
  const W = 1200, H = 440, pad = { l: 56, r: 16, t: 16, b: 40 };
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  const s = week[scen], n = s.load_planned.length;
  const keys = order.filter((k) => s.dispatch[k]);
  const max = Math.max(...week.S0.load_planned, ...week["S2-300"].load_planned) * 1.08;
  const x = (i) => pad.l + (i / (n - 1)) * (W - pad.l - pad.r), y = (v) => H - pad.b - (v / max) * (H - pad.t - pad.b);
  for (let gw = 0; gw * 1000 < max; gw++) {   // a quiet scale on the left, no grid lines
    el("text", { x: pad.l - 14, y: y(gw * 1000) + 6, "text-anchor": "end", "font-size": 18, fill: "currentColor", "fill-opacity": 0.7 }, svg).textContent = `${gw} GW`;
  }
  const start = new Date(week.start + "Z");
  for (let i = 0; i < n; i += 24) {
    const d = new Date(start.getTime() + i * 3600e3);
    el("text", { x: x(i), y: H - 10, "font-size": 18, fill: "currentColor", "fill-opacity": 0.7 }, svg).textContent =
      d.toLocaleDateString("en-GB", { day: "numeric", month: "short", timeZone: "UTC" });
  }
  let base = new Array(n).fill(0);
  keys.forEach((k) => {
    const top = base.map((b, i) => b + s.dispatch[k][i]);
    const up = top.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join("");
    const down = base.map((v, i) => `L${x(n - 1 - i).toFixed(1)},${y(base[n - 1 - i]).toFixed(1)}`).join("");
    el("path", { d: `${up}${down}Z`, fill: colors[k] }, svg);
    base = top;
  });
  const line = (arr, extra) => el("path", { d: arr.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(""),
    fill: "none", stroke: "currentColor", "stroke-width": 2.5, ...extra }, svg);
  line(s.load_planned, {});
  if (scen === "S2-300") line(s.load_served, { "stroke-dasharray": "8 6" });
  return keys.map((k) => labels[k]);
}
