// Every hour of 2030 at once: a 3D surface, day of the year along x, hour of the day along z, power as height.
// Drawn in the chapter's own colours (from the field towards the ink), on a transparent background.

import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const DAYS = 365, HOURS = 24, W = 36.5, D = 12, H = 7;
const LABEL = { gas: "TWh of gas in the year", solar: "TWh of solar in the year", load: "TWh of demand in the year" };

export function startYear(canvas, data, ui, reduce) {
  const style = getComputedStyle(canvas.closest("section"));
  const field = new THREE.Color(style.backgroundColor), ink = new THREE.Color(style.color);
  const low = field.clone().lerp(ink, 0.15), high = ink.clone();

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  const scene = new THREE.Scene(), camera = new THREE.PerspectiveCamera(34, 1, 0.1, 200);
  camera.position.set(-8, 15, 30);
  const controls = new OrbitControls(camera, canvas);
  Object.assign(controls, { enableDamping: true, dampingFactor: 0.08, enableZoom: false, minPolarAngle: 0.5, maxPolarAngle: 1.35 });
  controls.target.set(0, 1.8, 0);
  scene.add(new THREE.HemisphereLight(0xffffff, 0x8a6a2a, 1.4));
  const key = new THREE.DirectionalLight(0xffffff, 1.6); key.position.set(-20, 30, 20); scene.add(key);

  const geom = new THREE.PlaneGeometry(W, D, DAYS - 1, HOURS - 1).rotateX(-Math.PI / 2);
  const pos = geom.attributes.position, n = pos.count, colors = new Float32Array(n * 3);
  geom.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  scene.add(new THREE.Mesh(geom, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.75, side: THREE.DoubleSide, flatShading: false })));

  const value = (grid, v) => grid[v % DAYS][Math.floor(v / DAYS)];
  const maxOf = (layer) => Math.max(...Object.values(data).map((s) => Math.max(...s[layer].flat())));
  const from = new Float32Array(n), to = new Float32Array(n), cur = new Float32Array(n), tmp = new THREE.Color();
  let state = { scen: "S0", layer: "gas" }, t0 = 0, animating = false;

  function apply() {
    for (let v = 0; v < n; v++) {
      pos.setY(v, cur[v] * H);
      tmp.copy(low).lerp(high, Math.min(1, cur[v] * 1.1)); colors.set([tmp.r, tmp.g, tmp.b], v * 3);
    }
    pos.needsUpdate = true; geom.attributes.color.needsUpdate = true; geom.computeVertexNormals();
  }
  function retarget() {
    const grid = data[state.scen][state.layer], max = maxOf(state.layer);
    for (let v = 0; v < n; v++) { from[v] = cur[v]; to[v] = value(grid, v) / max; }
    ui.total.textContent = (grid.flat().reduce((a, b) => a + b, 0) / 1e6).toFixed(2);   // hourly steps: MW summed = MWh
    ui.label.textContent = LABEL[state.layer];
    if (reduce) { cur.set(to); apply(); draw(); return; }
    t0 = performance.now(); animating = true; kick();
  }
  ui.groups.forEach((g) => g.addEventListener("click", (e) => {
    const b = e.target.closest("button"); if (!b) return;
    state[g.dataset.group] = b.dataset.v;
    g.querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", x === b ? "true" : "false"));
    retarget();
  }));

  function resize() {
    const w = canvas.clientWidth, h = canvas.clientHeight;
    renderer.setSize(w, h, false); camera.aspect = w / h;
    camera.position.setLength(w < 700 ? 50 : 36); camera.updateProjectionMatrix();
  }
  resize(); addEventListener("resize", resize);

  let visible = false, running = false, last = 0;
  controls.addEventListener("change", () => { last = performance.now(); kick(); });
  new IntersectionObserver(([e]) => { visible = e.isIntersecting; kick(); }).observe(canvas);
  function kick() { if (visible && !running) { running = true; requestAnimationFrame(loop); } }
  function draw() { controls.update(); renderer.render(scene, camera); }
  function loop(t) {
    if (animating) {
      const k = Math.min(1, (t - t0) / 1000), e = 1 - (1 - k) ** 4;
      for (let v = 0; v < n; v++) cur[v] = from[v] + (to[v] - from[v]) * e;
      apply(); if (k >= 1) animating = false;
    }
    draw();
    if (visible && (animating || t - last < 1200)) requestAnimationFrame(loop); else running = false;
  }
  retarget();
}
