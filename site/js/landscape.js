// The 8,760-hour landscape: one year of hourly output as a 3D surface.
// x = day of the year, z = hour of the day, height and colour = MW. Switching scenario or layer morphs the surface.

import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const DAYS = 365, HOURS = 24;
const W = 36.5, D = 12, H = 7;        // scene size: 1 unit = 10 days along x, 2 hours along z
const RAMP = ["#0d2a4a", "#1f5fae", "#3fc1ff", "#ffd27a", "#ff7a45"].map((c) => new THREE.Color(c));
const LAYER_NAMES = { gas: "Gas output", solar: "Solar output", wind: "Wind output", load: "Demand" };
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function rampColor(k, out) {         // k in [0, 1] -> colour along the ramp
  const x = Math.min(0.9999, Math.max(0, k)) * (RAMP.length - 1), i = Math.floor(x);
  return out.copy(RAMP[i]).lerp(RAMP[i + 1], x - i);
}

function label(text, size = 0.9) {
  const c = document.createElement("canvas"); c.width = 256; c.height = 64;
  const g = c.getContext("2d"); g.font = "500 30px Fira Code, monospace"; g.fillStyle = "#a9b6c9"; g.textAlign = "center"; g.textBaseline = "middle";
  g.fillText(text, 128, 32);
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(c), transparent: true, depthWrite: false }));
  s.scale.set(size * 4, size, 1);
  return s;
}

export async function startLandscape(box, hourlyPromise, reduceMotion) {
  const canvas = box.querySelector("canvas");
  const data = await hourlyPromise;
  const scenarios = Object.keys(data);
  // one height scale per layer across scenarios, so a lower mountain really means less
  const maxOf = (layer) => Math.max(...scenarios.map((s) => Math.max(...data[s][layer].flat())));

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 200);
  camera.position.set(-9, 17, 30);   // facing the long (days) side, slightly from the left
  const controls = new OrbitControls(camera, canvas);
  controls.target.set(0, 1.5, 0); controls.enableDamping = true; controls.dampingFactor = 0.08;
  controls.minDistance = 14; controls.maxDistance = 70; controls.maxPolarAngle = Math.PI * 0.48;
  controls.autoRotate = !reduceMotion; controls.autoRotateSpeed = 0.35;
  controls.addEventListener("start", () => { controls.autoRotate = false; });

  scene.add(new THREE.AmbientLight(0x8fb4e6, 0.75));
  const sun = new THREE.DirectionalLight(0xffffff, 1.5); sun.position.set(-20, 30, 15); scene.add(sun);
  const fillLight = new THREE.DirectionalLight(0x3fc1ff, 0.5); fillLight.position.set(20, 10, -20); scene.add(fillLight);

  // surface: (DAYS x HOURS) vertices on a plane, heights set per layer
  const geom = new THREE.PlaneGeometry(W, D, DAYS - 1, HOURS - 1);
  geom.rotateX(-Math.PI / 2);
  const pos = geom.attributes.position, n = pos.count;
  const colors = new Float32Array(n * 3); geom.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  const surface = new THREE.Mesh(geom, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.55, metalness: 0.1, side: THREE.DoubleSide }));
  scene.add(surface);
  const wire = new THREE.LineSegments(new THREE.WireframeGeometry(new THREE.PlaneGeometry(W, D, 73, 12).rotateX(-Math.PI / 2)),
    new THREE.LineBasicMaterial({ color: 0x1b2c48, transparent: true, opacity: 0.5 }));
  wire.position.y = -0.02; scene.add(wire);

  // axis labels: months along x, hours along z
  MONTHS.forEach((m, i) => { const s = label(m, 0.75); s.position.set(-W / 2 + ((i + 0.5) / 12) * W, 0.2, D / 2 + 1.1); scene.add(s); });
  [["00h", 0], ["06h", 6], ["12h", 12], ["18h", 18], ["23h", 23]].forEach(([t, h]) => {
    const s = label(t, 0.7); s.position.set(-W / 2 - 1.8, 0.2, -D / 2 + (h / 23) * D); scene.add(s); });

  // PlaneGeometry vertex order: rows run along x (days), one row per hour (z)
  const vertexValue = (grid, v) => { const day = v % DAYS, hour = Math.floor(v / DAYS); return grid[day][hour]; };
  const from = new Float32Array(n), to = new Float32Array(n), cur = new Float32Array(n);
  let state = { scen: "S0", layer: "gas" }, animStart = 0, animating = false;
  const tmp = new THREE.Color();

  function apply(heights) {
    for (let v = 0; v < n; v++) {
      pos.setY(v, heights[v] * H);
      rampColor(heights[v], tmp); colors.set([tmp.r, tmp.g, tmp.b], v * 3);
    }
    pos.needsUpdate = true; geom.attributes.color.needsUpdate = true; geom.computeVertexNormals();
  }

  function setTarget() {
    const grid = data[state.scen][state.layer], max = maxOf(state.layer);
    for (let v = 0; v < n; v++) { from[v] = cur[v]; to[v] = vertexValue(grid, v) / max; }
    const twh = grid.flat().reduce((a, b) => a + b, 0) / 1e6;     // 1-hour steps: MW summed = MWh
    box.querySelector("#ls-title").textContent = `${LAYER_NAMES[state.layer]} · ${state.scen}`;
    box.querySelector("#ls-total").textContent = `${twh.toFixed(2)} TWh`;
    box.querySelector("#ls-max").textContent = `peak of scale: ${Math.round(max).toLocaleString("en-US")} MW`;
    if (reduceMotion) { cur.set(to); apply(cur); return; }
    animStart = performance.now(); animating = true; kick();
  }

  box.querySelectorAll(".seg").forEach((seg) => seg.addEventListener("click", (e) => {
    const b = e.target.closest("button"); if (!b) return;
    if (b.dataset.scen) state.scen = b.dataset.scen;
    if (b.dataset.layer) state.layer = b.dataset.layer;
    seg.querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", x === b ? "true" : "false"));
    setTarget();
  }));

  function resize() {
    const w = canvas.clientWidth, h = canvas.clientHeight;
    renderer.setSize(w, h, false); camera.aspect = w / h;
    camera.position.setLength(w < 640 ? 52 : 40);
    camera.updateProjectionMatrix();
  }
  resize(); window.addEventListener("resize", resize);

  let visible = false, running = false, lastMove = 0;   // keep rendering ~1 s after a drag so damping can settle
  new IntersectionObserver(([e]) => { visible = e.isIntersecting; kick(); }).observe(box);
  controls.addEventListener("change", () => { lastMove = performance.now(); kick(); });
  function kick() { if (!running && visible) { running = true; requestAnimationFrame(loop); } }
  function loop(t) {
    if (animating) {
      const k = Math.min(1, (t - animStart) / 900), e = k < 0.5 ? 4 * k * k * k : 1 - (-2 * k + 2) ** 3 / 2;
      for (let v = 0; v < n; v++) cur[v] = from[v] + (to[v] - from[v]) * e;
      apply(cur); if (k >= 1) animating = false;
    }
    controls.update();
    renderer.render(scene, camera);
    if (visible && (animating || controls.autoRotate || t - lastMove < 1200)) requestAnimationFrame(loop); else running = false;
  }
  setTarget();
}
