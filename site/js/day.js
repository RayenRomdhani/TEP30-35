// "The day": a small 3D landscape of Tunisia's power system, driven hour by hour by the model's output on its
// summer peak day. Scroll moves the clock; the sun crosses the sky; the solar field, the turbines, the gas
// plant's flame and smoke, the city's lights and the energy on the lines all follow the real numbers.

import * as THREE from "three";

const SKY = [ // hour (local) -> sky colour, ground light; read as a day's colour script
  [0, "#081726", 0.12], [5, "#0f2a44", 0.18], [6.5, "#e9a98b", 0.55], [8, "#bcd3e6", 0.9], [12, "#dfe9f0", 1.15],
  [16, "#f0d9a6", 1.0], [18.5, "#e2753f", 0.6], [19.6, "#5a1d2a", 0.28], [21, "#0c1c30", 0.14], [24, "#081726", 0.12]];

function lerpSky(h) {
  for (let i = 0; i < SKY.length - 1; i++) {
    const [h0, c0, l0] = SKY[i], [h1, c1, l1] = SKY[i + 1];
    if (h >= h0 && h <= h1) { const k = (h - h0) / (h1 - h0);
      return { color: new THREE.Color(c0).lerp(new THREE.Color(c1), k), light: l0 + (l1 - l0) * k }; }
  }
  return { color: new THREE.Color(SKY[0][1]), light: SKY[0][2] };
}

const rnd = (() => { let s = 7; return () => ((s = (s * 16807) % 2147483647) / 2147483647); })(); // fixed seed: same town every visit

function ground(scene) {
  // one large field running to the horizon: dunes inland, a ridge in the west, a beach sloping into the sea up north
  const g = new THREE.PlaneGeometry(320, 320, 160, 160); g.rotateX(-Math.PI / 2);
  const pos = g.attributes.position;
  for (let i = 0; i < pos.count; i++) {
    const x = pos.getX(i), z = pos.getZ(i);
    const ridge = Math.max(0, -x - 8) * 0.12 * Math.max(0, 1 - Math.abs(z - 6) / 16);
    const coastLine = -15 + Math.sin(x * 0.08) * 2.5;              // a gently curving shore
    const beach = Math.min(0, (z - coastLine) * 0.25);             // slopes under the water north of the shore
    pos.setY(i, Math.sin(x * 0.35) * Math.cos(z * 0.28) * 0.18 + ridge + beach + Math.max(0, z - 30) * 0.04);
  }
  g.computeVertexNormals();
  const land = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ color: 0xd8b98a, roughness: 1, flatShading: true }));
  land.receiveShadow = true; scene.add(land);
  const sea = new THREE.Mesh(new THREE.PlaneGeometry(400, 200).rotateX(-Math.PI / 2),
    new THREE.MeshStandardMaterial({ color: 0x1d5c86, roughness: 0.18, metalness: 0.35 }));
  sea.position.set(0, -0.35, -110); scene.add(sea);
}

function city(scene) {
  const n = 140, body = new THREE.InstancedMesh(new THREE.BoxGeometry(1, 1, 1),
    new THREE.MeshStandardMaterial({ color: 0xf1ebe0, roughness: 0.9 }), n);
  const lights = new THREE.InstancedMesh(new THREE.BoxGeometry(1.02, 1, 1.02),
    new THREE.MeshStandardMaterial({ color: 0x000000, emissive: 0xffc56b, emissiveIntensity: 0, transparent: true, opacity: 0.9 }), n);
  const m = new THREE.Matrix4();
  for (let i = 0; i < n; i++) {
    const r = Math.sqrt(rnd()) * 6.5, a = rnd() * Math.PI * 2, h = 0.5 + rnd() ** 2 * 3.6, w = 0.7 + rnd() * 0.7;
    const x = -6 + Math.cos(a) * r, z = -8 + Math.sin(a) * r * 0.7;
    m.compose(new THREE.Vector3(x, h / 2, z), new THREE.Quaternion(), new THREE.Vector3(w, h, w)); body.setMatrixAt(i, m);
    m.compose(new THREE.Vector3(x, h * 0.55, z), new THREE.Quaternion(), new THREE.Vector3(w * 1.01, h * 0.5, w * 1.01)); lights.setMatrixAt(i, m);
  }
  body.castShadow = true; scene.add(body, lights);
  return lights.material;
}

function solarField(scene) {
  const rows = 9, cols = 16, n = rows * cols;
  const mat = new THREE.MeshStandardMaterial({ color: 0x1b3557, roughness: 0.25, metalness: 0.6, emissive: 0x9fd4ff, emissiveIntensity: 0 });
  const panels = new THREE.InstancedMesh(new THREE.BoxGeometry(1.1, 0.06, 0.7), mat, n);
  const m = new THREE.Matrix4(), q = new THREE.Quaternion().setFromEuler(new THREE.Euler(-0.55, 0, 0));
  let i = 0;
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    m.compose(new THREE.Vector3(6 + c * 1.3, 0.55, 5 + r * 1.15), q, new THREE.Vector3(1, 1, 1)); panels.setMatrixAt(i++, m);
  }
  panels.castShadow = true; scene.add(panels);
  return mat;
}

function turbines(scene) {
  const rotors = [], white = new THREE.MeshStandardMaterial({ color: 0xf4f1ea, roughness: 0.6 });
  [[-19, 2], [-16.5, 6], [-20, 9.5], [-15, 11], [-18, 14]].forEach(([x, z]) => {
    const base = 0.12 * Math.max(0, -x - 8);
    const tower = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.16, 6, 10), white);
    tower.position.set(x, base + 3, z); tower.castShadow = true; scene.add(tower);
    const rotor = new THREE.Group(); rotor.position.set(x, base + 6.05, z + 0.2);
    for (let b = 0; b < 3; b++) {
      const blade = new THREE.Mesh(new THREE.BoxGeometry(0.16, 2.6, 0.04).translate(0, 1.3, 0), white);
      blade.rotation.z = (b * Math.PI * 2) / 3; rotor.add(blade);
    }
    rotor.add(new THREE.Mesh(new THREE.SphereGeometry(0.16, 10, 10), white));
    scene.add(rotor); rotors.push(rotor);
  });
  return rotors;
}

function gasPlant(scene) {
  const concrete = new THREE.MeshStandardMaterial({ color: 0x8a8f96, roughness: 0.85 });
  const hall = new THREE.Mesh(new THREE.BoxGeometry(5, 2.2, 3), concrete); hall.position.set(10, 1.1, -7); hall.castShadow = true;
  scene.add(hall);
  const tops = [];
  [[8.6, -7.6], [10.2, -7.6]].forEach(([x, z]) => {
    const stack = new THREE.Mesh(new THREE.CylinderGeometry(0.32, 0.42, 7, 14), concrete);
    stack.position.set(x, 3.5, z); stack.castShadow = true; scene.add(stack); tops.push(new THREE.Vector3(x, 7.1, z));
  });
  const flame = new THREE.PointLight(0xff7a2f, 0, 26, 1.6); flame.position.set(9.4, 7.6, -7.6); scene.add(flame);
  // smoke: soft points rising from the stacks, how many depends on gas output
  const N = 260, geo = new THREE.BufferGeometry(), pos = new Float32Array(N * 3), life = new Float32Array(N).fill(-1);
  geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  const c = document.createElement("canvas"); c.width = c.height = 64;
  const g = c.getContext("2d"), grd = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  grd.addColorStop(0, "rgba(255,255,255,0.9)"); grd.addColorStop(1, "rgba(255,255,255,0)"); g.fillStyle = grd; g.fillRect(0, 0, 64, 64);
  const smoke = new THREE.Points(geo, new THREE.PointsMaterial({ size: 1.5, map: new THREE.CanvasTexture(c), transparent: true,
    opacity: 0.55, depthWrite: false, color: 0xd9d4cc }));
  scene.add(smoke);
  return { tops, flame, smoke, pos, life, geo, N };
}

function powerLines(scene) {
  const routes = [ // from each plant to the city, over a few pylons
    [new THREE.Vector3(10, 0, -7), new THREE.Vector3(4, 0, -8), new THREE.Vector3(-2, 0, -8)],
    [new THREE.Vector3(12, 0, 5), new THREE.Vector3(6, 0, -1), new THREE.Vector3(-1, 0, -4)],
    [new THREE.Vector3(-16, 0, 8), new THREE.Vector3(-11, 0, 2), new THREE.Vector3(-8, 0, -4)]];
  const steel = new THREE.MeshStandardMaterial({ color: 0x55595f, roughness: 0.7 });
  const curves = [];
  routes.forEach((pts) => {
    const top = pts.map((p) => p.clone().setY(2.6));
    pts.forEach((p) => { const pylon = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.22, 2.6, 4), steel); pylon.position.copy(p).setY(1.3); scene.add(pylon); });
    const curve = new THREE.CatmullRomCurve3(top); curves.push(curve);
    scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(curve.getPoints(40)), new THREE.LineBasicMaterial({ color: 0x2b2b2b })));
  });
  const N = 60, geo = new THREE.BufferGeometry(), pos = new Float32Array(N * 3);
  geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  const sparks = new THREE.Points(geo, new THREE.PointsMaterial({ size: 0.28, color: 0xfff1a8, transparent: true, opacity: 0.95, depthWrite: false }));
  scene.add(sparks);
  return { curves, sparks, pos, geo, N };
}

function stars(scene) {
  const N = 500, pos = new Float32Array(N * 3);
  for (let i = 0; i < N; i++) { const a = rnd() * Math.PI * 2, e = 0.15 + rnd() * 1.2, r = 90;
    pos.set([Math.cos(a) * Math.cos(e) * r, Math.sin(e) * r, Math.sin(a) * Math.cos(e) * r], i * 3); }
  const geo = new THREE.BufferGeometry(); geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  const mat = new THREE.PointsMaterial({ size: 0.5, color: 0xffffff, transparent: true, opacity: 0, depthWrite: false, sizeAttenuation: true });
  scene.add(new THREE.Points(geo, mat));
  return mat;
}

export function createDay(canvas) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  const scene = new THREE.Scene();
  scene.fog = new THREE.Fog(0x081726, 60, 170);      // fog in the sky's colour melts the horizon away
  const camera = new THREE.PerspectiveCamera(36, 1, 0.1, 400);

  const hemi = new THREE.HemisphereLight(0xdcecff, 0x8a6a45, 0.6); scene.add(hemi);
  const sun = new THREE.DirectionalLight(0xfff1d6, 2); sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048); Object.assign(sun.shadow.camera, { left: -36, right: 36, top: 36, bottom: -36, far: 160 });
  scene.add(sun, sun.target);
  const sunDisc = new THREE.Mesh(new THREE.SphereGeometry(3, 24, 24), new THREE.MeshBasicMaterial({ color: 0xfff3c8, fog: false }));
  scene.add(sunDisc);

  ground(scene);
  const windowMat = city(scene), solarMat = solarField(scene), rotors = turbines(scene), plant = gasPlant(scene), lines = powerLines(scene);
  const starMat = stars(scene);

  function resize() {
    const w = canvas.clientWidth, h = canvas.clientHeight;
    renderer.setSize(w, h, false); camera.aspect = w / h;
    camera.fov = w < 760 ? 48 : 36; camera.updateProjectionMatrix();
  }
  resize(); window.addEventListener("resize", resize);

  let state = { hour: 0, gas: 0, solar: 0, wind: 0, load: 0, progress: 0 };
  let t0 = performance.now(), spin = 0, sparkT = 0;

  function render(now) {
    const dt = Math.min(0.05, (now - t0) / 1000); t0 = now;
    const h = state.hour, sky = lerpSky(h);
    scene.background = sky.color; scene.fog.color.copy(sky.color);
    // sun: rises in the east (+x) around 06:00, highest at 13:00, sets in the west around 19:30
    const dayK = Math.min(1, Math.max(0, (h - 5.8) / (19.8 - 5.8)));
    const alt = Math.sin(dayK * Math.PI), az = Math.PI * (1 - dayK);
    sun.position.set(Math.cos(az) * 60, Math.max(-10, alt * 55) + 2, 30 - alt * 10);
    sun.intensity = 2.4 * Math.max(0, alt) ** 0.6;
    sun.color.set(alt < 0.3 ? 0xffb07a : 0xfff1d6);
    sunDisc.position.copy(sun.position).multiplyScalar(1.6); sunDisc.visible = alt > 0.02;
    hemi.intensity = 0.25 + sky.light * 0.55;
    starMat.opacity = Math.max(0, 1 - sky.light * 2.2);
    // the model's numbers drive the machines
    solarMat.emissiveIntensity = 0.9 * state.solar;
    windowMat.emissiveIntensity = (0.35 + 1.6 * state.load) * Math.max(0.08, 1 - sky.light * 0.9);
    spin += dt * (0.4 + 7 * state.wind); rotors.forEach((r, i) => { r.rotation.z = spin + i; });
    plant.flame.intensity = 60 * state.gas * (0.85 + 0.15 * Math.sin(now / 90));
    // smoke particles: spawn rate proportional to gas output
    const spawn = state.gas * 6;
    for (let i = 0; i < plant.N; i++) {
      if (plant.life[i] < 0 && Math.random() < spawn * dt) { const top = plant.tops[i % 2]; plant.life[i] = 0;
        plant.pos.set([top.x + (Math.random() - 0.5) * 0.3, top.y, top.z + (Math.random() - 0.5) * 0.3], i * 3); }
      if (plant.life[i] >= 0) { plant.life[i] += dt;
        plant.pos[i * 3] += dt * (0.9 + plant.life[i] * 0.4); plant.pos[i * 3 + 1] += dt * 1.6; plant.pos[i * 3 + 2] += dt * 0.2;
        if (plant.life[i] > 4.5) { plant.life[i] = -1; plant.pos[i * 3 + 1] = -50; } }
    }
    plant.geo.attributes.position.needsUpdate = true;
    // energy on the lines: faster when demand is higher
    sparkT += dt * (0.08 + 0.35 * state.load);
    for (let i = 0; i < lines.N; i++) {
      const c = lines.curves[i % 3], u = (sparkT + i / lines.N) % 1, p = c.getPoint(u); lines.pos.set([p.x, p.y, p.z], i * 3);
    }
    lines.geo.attributes.position.needsUpdate = true;
    // camera drifts along the day so the landscape turns slowly under the light
    const a = -0.65 + state.progress * 1.1, r = canvas.clientWidth < 760 ? 58 : 46;
    camera.position.set(Math.sin(a) * r, 13 + Math.sin(state.progress * Math.PI) * 3, Math.cos(a) * r);
    camera.lookAt(0, 3.5, -6);
    renderer.render(scene, camera);
  }

  return { set(next) { Object.assign(state, next); }, render };
}
