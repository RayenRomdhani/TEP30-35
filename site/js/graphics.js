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
