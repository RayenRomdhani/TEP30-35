// Hero scene: Tunisia (Natural Earth outline) extruded in 3D, its high-voltage grid from OpenStreetMap
// glowing on top, and the model's two nodes with energy flowing along the line that joins them.

import * as THREE from "three";

const WORLD = "https://cdn.jsdelivr.net/npm/world-atlas@2.0.2/countries-50m.json"; // Natural Earth, public domain
const TUNISIA_ID = "788";                     // ISO 3166 numeric code
const LON0 = 9.6, LAT0 = 33.9, SCALE = 1.35;  // projection centre and size
const KX = Math.cos((LAT0 * Math.PI) / 180);  // shrink longitude so the map keeps its true shape
const DEPTH = 0.32;
const KV_COLOR = { 400: 0xffb347, 225: 0x3fc1ff, 220: 0x3fc1ff, 150: 0x2f7fd0, 90: 0x285a8f };

const project = ([lon, lat]) => new THREE.Vector2((lon - LON0) * KX * SCALE, (lat - LAT0) * SCALE);

function glowTexture(color) {
  const c = document.createElement("canvas"); c.width = c.height = 128;
  const g = c.getContext("2d"), grd = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  grd.addColorStop(0, color); grd.addColorStop(0.25, color + "aa"); grd.addColorStop(1, color + "00");
  g.fillStyle = grd; g.fillRect(0, 0, 128, 128);
  return new THREE.CanvasTexture(c);
}

function tunisiaMesh(polygons) {
  const group = new THREE.Group();
  const fill = new THREE.MeshStandardMaterial({ color: 0x0c1830, metalness: 0.35, roughness: 0.65, emissive: 0x06101f });
  const edge = new THREE.LineBasicMaterial({ color: 0x3fc1ff, transparent: true, opacity: 0.55 });
  polygons.forEach((rings) => {
    const shape = new THREE.Shape(rings[0].map(project));
    rings.slice(1).forEach((hole) => shape.holes.push(new THREE.Path(hole.map(project))));
    const geom = new THREE.ExtrudeGeometry(shape, { depth: DEPTH, bevelEnabled: true, bevelThickness: 0.04, bevelSize: 0.03, bevelSegments: 2 });
    group.add(new THREE.Mesh(geom, fill));
    const top = new THREE.BufferGeometry().setFromPoints(rings[0].map((p) => { const v = project(p); return new THREE.Vector3(v.x, v.y, DEPTH + 0.045); }));
    group.add(new THREE.Line(top, edge));
  });
  return group;
}

function gridLines(lines) {
  const group = new THREE.Group();
  const mats = {};
  lines.forEach(({ kv, c }) => {
    const color = KV_COLOR[kv] ?? 0x285a8f;
    mats[color] ??= new THREE.LineBasicMaterial({ color, transparent: true, opacity: kv >= 220 ? 0.95 : 0.6, blending: THREE.AdditiveBlending });
    const pts = c.map((p) => { const v = project(p); return new THREE.Vector3(v.x, v.y, DEPTH + 0.06); });
    group.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), mats[color]));
  });
  return group;
}

export async function startHero(canvas, gridPromise, reduceMotion) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  const scene = new THREE.Scene();
  scene.fog = new THREE.Fog(0x060a12, 18, 42);
  const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 100);

  scene.add(new THREE.AmbientLight(0x6f8fbf, 0.9));
  const key = new THREE.DirectionalLight(0xbfe6ff, 1.4); key.position.set(-6, 10, 12); scene.add(key);
  const rim = new THREE.PointLight(0x3fc1ff, 30, 30); rim.position.set(6, -4, 6); scene.add(rim);

  // floor grid for depth
  const floor = new THREE.GridHelper(60, 60, 0x13233d, 0x0d1a2e);
  floor.rotation.x = Math.PI / 2; floor.position.z = -0.02; floor.material.transparent = true; floor.material.opacity = 0.6;

  // Map group lies in the XY plane (north = +y); the whole stage is tilted towards the camera.
  const TILT = -0.7;                    // radians: enough perspective to read as 3D, not so much that the map squashes
  const stage = new THREE.Group(); stage.add(floor); scene.add(stage);
  stage.rotation.x = TILT;

  const [world, grid] = await Promise.all([fetch(WORLD).then((r) => r.json()), gridPromise]);
  const feature = topojson.feature(world, world.objects.countries).features.find((f) => String(f.id) === TUNISIA_ID);
  const polys = feature.geometry.type === "Polygon" ? [feature.geometry.coordinates] : feature.geometry.coordinates;
  stage.add(tunisiaMesh(polys));
  stage.add(gridLines(grid.lines));

  // the model's two nodes and the line between them
  const nodes = grid.nodes.map((n) => { const v = project([n.lon, n.lat]); return new THREE.Vector3(v.x, v.y, DEPTH + 0.1); });
  const glow = new THREE.SpriteMaterial({ map: glowTexture("#3fc1ff"), transparent: true, blending: THREE.AdditiveBlending, depthWrite: false });
  const rings = [];
  nodes.forEach((p) => {
    const core = new THREE.Mesh(new THREE.SphereGeometry(0.13, 24, 24), new THREE.MeshBasicMaterial({ color: 0xe8f7ff }));
    core.position.copy(p); stage.add(core);
    const halo = new THREE.Sprite(glow); halo.scale.set(1.05, 1.05, 1); halo.position.copy(p); stage.add(halo);
    const ring = new THREE.Mesh(new THREE.RingGeometry(0.22, 0.25, 48), new THREE.MeshBasicMaterial({ color: 0x3fc1ff, transparent: true, side: THREE.DoubleSide }));
    ring.position.copy(p); stage.add(ring); rings.push(ring);
  });
  const mid = nodes[0].clone().add(nodes[1]).multiplyScalar(0.5); mid.z += 1.6;
  const arc = new THREE.QuadraticBezierCurve3(nodes[0], mid, nodes[1]);
  stage.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(arc.getPoints(64)),
    new THREE.LineBasicMaterial({ color: 0xffb347, transparent: true, opacity: 0.55 })));
  const N = 26, flowGeom = new THREE.BufferGeometry(), flowPos = new Float32Array(N * 3);
  flowGeom.setAttribute("position", new THREE.BufferAttribute(flowPos, 3));
  const flow = new THREE.Points(flowGeom, new THREE.PointsMaterial({ size: 0.16, map: glowTexture("#ffb347"), color: 0xffd9a0,
    transparent: true, blending: THREE.AdditiveBlending, depthWrite: false }));
  stage.add(flow);

  // camera framing: map to the right of the text on wide screens, centred behind it on phones
  function resize() {
    const w = canvas.clientWidth, h = canvas.clientHeight;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    const wide = w > 860;
    camera.position.set(wide ? -3.6 : 0, wide ? -0.6 : -2, wide ? 13.5 : 18);
    camera.lookAt(wide ? -3.6 : 0, wide ? 0.2 : 0.6, 0);
    stage.position.x = wide ? -0.4 : 0;
    camera.updateProjectionMatrix();
  }
  resize(); window.addEventListener("resize", resize);

  let mx = 0, my = 0, visible = true, t0 = performance.now();
  window.addEventListener("pointermove", (e) => { mx = e.clientX / window.innerWidth - 0.5; my = e.clientY / window.innerHeight - 0.5; });
  new IntersectionObserver(([e]) => { visible = e.isIntersecting; if (visible) loop(); }).observe(canvas);

  function frame(t) {
    const s = (t - t0) / 1000;
    stage.rotation.z = Math.sin(s * 0.12) * 0.18 + mx * 0.25;
    stage.rotation.x = TILT + my * 0.08;
    rings.forEach((r, i) => { const k = (s * 0.6 + i * 0.5) % 1; r.scale.setScalar(1 + k * 3); r.material.opacity = 0.7 * (1 - k); });
    for (let i = 0; i < N; i++) {           // particles move both ways along the arc
      const dir = i % 2 ? 1 : -1, u = ((s * 0.18 * dir + i / N) % 1 + 1) % 1;
      const p = arc.getPoint(u); flowPos.set([p.x, p.y, p.z], i * 3);
    }
    flowGeom.attributes.position.needsUpdate = true;
    renderer.render(scene, camera);
  }
  function loop() {
    if (!visible || document.hidden) return;
    frame(performance.now());
    if (!reduceMotion) requestAnimationFrame(loop);
  }
  document.addEventListener("visibilitychange", () => { if (!document.hidden) loop(); });
  loop();
}
