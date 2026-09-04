import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/examples/jsm/geometries/RoundedBoxGeometry.js';
import * as TX from './textures.js';

export const RED = 0xff2a36;

const M = {
  blackMatte: new THREE.MeshStandardMaterial({ color: 0x0f1013, roughness: 0.6, metalness: 0.2 }),
  blackGloss: new THREE.MeshPhysicalMaterial({ color: 0x0b0c0f, roughness: 0.22, metalness: 0.5, clearcoat: 0.8, clearcoatRoughness: 0.15 }),
  mesh: new THREE.MeshStandardMaterial({ color: 0x15161a, roughness: 0.95, metalness: 0.0 }),
  leather: new THREE.MeshPhysicalMaterial({ color: 0x14151a, roughness: 0.55, metalness: 0.05, clearcoat: 0.25, clearcoatRoughness: 0.5 }),
  chrome: new THREE.MeshStandardMaterial({ color: 0xd8dadf, roughness: 0.15, metalness: 1.0 }),
  gunmetal: new THREE.MeshStandardMaterial({ color: 0x3b3e46, roughness: 0.35, metalness: 0.9 }),
  redAccent: new THREE.MeshStandardMaterial({ color: RED, roughness: 0.5, metalness: 0.1 }),
  redGlow: new THREE.MeshStandardMaterial({ color: RED, emissive: RED, emissiveIntensity: 3.0, roughness: 0.4 }),
  warmGlow: new THREE.MeshStandardMaterial({ color: 0xfff1dc, emissive: 0xffe2bd, emissiveIntensity: 2.2, roughness: 0.6 }),
  cushion: new THREE.MeshStandardMaterial({ color: 0xf3f2ee, roughness: 0.95, metalness: 0 }),
  glass: new THREE.MeshPhysicalMaterial({ color: 0xbfd6e6, roughness: 0.05, metalness: 0, transmission: 0.0, transparent: true, opacity: 0.28, clearcoat: 1 }),
  walnut: new THREE.MeshStandardMaterial({ color: 0x2b2420, roughness: 0.6, metalness: 0.05 }),
  cabinet: new THREE.MeshPhysicalMaterial({ color: 0x1c1d22, roughness: 0.35, metalness: 0.25, clearcoat: 0.4, clearcoatRoughness: 0.3 }),
};

function rbox(w, h, d, material, r = 0.02, seg = 3) {
  const m = new THREE.Mesh(new RoundedBoxGeometry(w, h, d, seg, Math.min(r, Math.min(w, h, d) / 2)), material);
  m.castShadow = true;
  m.receiveShadow = true;
  return m;
}

function at(mesh, x, y, z, ry = 0) {
  mesh.position.set(x, y, z);
  if (ry) mesh.rotation.y = ry;
  return mesh;
}

export function ledStrip(length, axis = 'x', material = M.redGlow) {
  const geo =
    axis === 'x' ? new THREE.BoxGeometry(length, 0.014, 0.014)
      : axis === 'y' ? new THREE.BoxGeometry(0.014, length, 0.014)
        : new THREE.BoxGeometry(0.014, 0.014, length);
  return new THREE.Mesh(geo, material);
}

/* ────────────────────────────────────────────
   Gaming chair — faces -Z in local space
──────────────────────────────────────────── */
export function gamingChair() {
  const g = new THREE.Group();

  // 5-star base + casters
  const hub = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.06, 0.05, 24), M.gunmetal);
  hub.position.y = 0.06;
  g.add(hub);
  for (let i = 0; i < 5; i++) {
    const a = (i / 5) * Math.PI * 2;
    const leg = rbox(0.32, 0.03, 0.05, M.gunmetal, 0.012);
    leg.position.set(Math.cos(a) * 0.16, 0.05, Math.sin(a) * 0.16);
    leg.rotation.y = -a;
    g.add(leg);
    const wheel = new THREE.Mesh(new THREE.SphereGeometry(0.028, 16, 12), M.blackGloss);
    wheel.position.set(Math.cos(a) * 0.31, 0.03, Math.sin(a) * 0.31);
    g.add(wheel);
  }
  // gas lift
  g.add(at(new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.28, 20), M.chrome), 0, 0.22, 0));
  g.add(at(new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.045, 0.14, 20), M.blackMatte), 0, 0.14, 0));

  // seat with side bolsters
  const seat = rbox(0.5, 0.1, 0.5, M.leather, 0.04);
  seat.position.set(0, 0.45, 0);
  g.add(seat);
  g.add(at(rbox(0.1, 0.09, 0.44, M.leather, 0.03), -0.22, 0.52, 0.02));
  g.add(at(rbox(0.1, 0.09, 0.44, M.leather, 0.03), 0.22, 0.52, 0.02));
  g.add(at(rbox(0.28, 0.02, 0.36, M.mesh, 0.01), 0, 0.51, 0));

  // backrest (slight recline), wings, lumbar, headrest
  const back = new THREE.Group();
  back.position.set(0, 0.5, 0.22);
  back.rotation.x = -0.14;
  back.add(at(rbox(0.5, 0.72, 0.09, M.leather, 0.04), 0, 0.36, 0));
  back.add(at(rbox(0.12, 0.6, 0.11, M.leather, 0.04), -0.24, 0.34, -0.03));
  back.add(at(rbox(0.12, 0.6, 0.11, M.leather, 0.04), 0.24, 0.34, -0.03));
  back.add(at(rbox(0.3, 0.55, 0.02, M.mesh, 0.01), 0, 0.36, -0.045));
  back.add(at(rbox(0.06, 0.4, 0.015, M.redAccent, 0.005), -0.11, 0.36, -0.052));
  back.add(at(rbox(0.06, 0.4, 0.015, M.redAccent, 0.005), 0.11, 0.36, -0.052));
  back.add(at(rbox(0.34, 0.16, 0.1, M.leather, 0.05), 0, 0.82, -0.01));
  g.add(back);

  // armrests
  for (const s of [-1, 1]) {
    g.add(at(rbox(0.06, 0.2, 0.06, M.blackMatte, 0.01), s * 0.3, 0.6, 0.05));
    g.add(at(rbox(0.08, 0.035, 0.3, M.leather, 0.015), s * 0.3, 0.71, -0.02));
  }
  return g;
}

/* ────────────────────────────────────────────
   Monitor (27", slight curve) — screen faces +Z in local space
──────────────────────────────────────────── */
/** Plane bent into a concave arc toward +Z (viewer side). */
function curvedScreenGeometry(w, h, radius, segs = 24) {
  const geo = new THREE.PlaneGeometry(w, h, segs, 1);
  const pos = geo.attributes.position;
  for (let i = 0; i < pos.count; i++) {
    const x = pos.getX(i);
    const theta = x / radius;
    pos.setX(i, Math.sin(theta) * radius);
    pos.setZ(i, (1 - Math.cos(theta)) * radius);
  }
  geo.computeVertexNormals();
  return geo;
}

export function monitor(screenTex) {
  const g = new THREE.Group();
  const w = 0.62;
  const h = 0.36;
  const radius = 1.5;

  const screenMat = new THREE.MeshStandardMaterial({
    map: screenTex,
    emissive: 0xffffff,
    emissiveMap: screenTex,
    emissiveIntensity: 1.1,
    roughness: 0.3,
    metalness: 0.0,
  });
  const screen = new THREE.Mesh(curvedScreenGeometry(w, h, radius), screenMat);
  g.add(screen);

  const bezel = new THREE.Mesh(curvedScreenGeometry(w + 0.02, h + 0.02, radius), M.blackGloss);
  bezel.position.z = -0.004;
  g.add(bezel);
  const backCap = new THREE.Mesh(curvedScreenGeometry(w + 0.02, h + 0.02, radius), M.blackMatte);
  backCap.material = M.blackMatte.clone();
  backCap.material.side = THREE.BackSide;
  backCap.position.z = -0.035;
  g.add(backCap);
  const shell = rbox(w - 0.1, h - 0.1, 0.03, M.blackMatte, 0.01);
  shell.position.z = -0.02;
  g.add(shell);
  // red ring on back
  g.add(at(new THREE.Mesh(new THREE.TorusGeometry(0.06, 0.006, 8, 32), M.redGlow), 0, 0, -0.035));

  // stand
  g.add(at(rbox(0.05, 0.26, 0.05, M.gunmetal, 0.01), 0, -0.3, -0.05));
  g.add(at(rbox(0.3, 0.015, 0.2, M.gunmetal, 0.006), 0, -0.43, -0.02));
  return g;
}

/* ────────────────────────────────────────────
   Height-adjustable desk with peripherals — user sits at +Z side facing -Z
──────────────────────────────────────────── */
export function gamingDesk({ width = 1.5, depth = 0.7, screenTex, keyboardTex, withHeadset = true }) {
  const g = new THREE.Group();
  const top = rbox(width, 0.035, depth, M.blackGloss, 0.012);
  top.position.y = 0.745;
  g.add(top);
  // red edge inlay at the front
  g.add(at(rbox(width - 0.1, 0.004, 0.012, M.redGlow, 0.001), 0, 0.764, depth / 2 - 0.02));

  // T-legs with column and foot
  for (const s of [-1, 1]) {
    const x = s * (width / 2 - 0.12);
    g.add(at(rbox(0.07, 0.12, depth - 0.16, M.gunmetal, 0.01), x, 0.67, 0));
    g.add(at(rbox(0.06, 0.55, 0.09, M.gunmetal, 0.01), x, 0.34, 0));
    g.add(at(rbox(0.075, 0.03, depth - 0.1, M.gunmetal, 0.01), x, 0.03, 0));
  }
  // cable tray + underglow
  g.add(at(rbox(width - 0.5, 0.08, 0.14, M.blackMatte, 0.01), 0, 0.68, -0.18));
  const glow = ledStrip(width - 0.2, 'x');
  glow.position.set(0, 0.72, depth / 2 - 0.05);
  g.add(glow);

  // monitor
  const mon = monitor(screenTex);
  mon.position.set(0, 1.19, -0.22); // screen already faces +Z (toward sitter)
  g.add(mon);

  // keyboard + wrist rest + mouse + mousepad
  const pad = rbox(0.9, 0.004, 0.4, M.mesh, 0.002);
  pad.position.set(0.05, 0.765, 0.05);
  g.add(pad);
  const kb = rbox(0.44, 0.03, 0.15, M.blackMatte, 0.006);
  kb.position.set(-0.05, 0.78, 0.06);
  g.add(kb);
  const keys = new THREE.Mesh(new THREE.PlaneGeometry(0.42, 0.13), new THREE.MeshStandardMaterial({
    map: keyboardTex, emissive: 0xffffff, emissiveMap: keyboardTex, emissiveIntensity: 0.35, roughness: 0.6,
  }));
  keys.rotation.x = -Math.PI / 2;
  keys.position.set(-0.05, 0.796, 0.06);
  g.add(keys);
  const mouse = new THREE.Mesh(new THREE.SphereGeometry(0.036, 24, 16), M.blackGloss);
  mouse.scale.set(1, 0.55, 1.6);
  mouse.position.set(0.3, 0.785, 0.08);
  mouse.castShadow = true;
  g.add(mouse);
  g.add(at(new THREE.Mesh(new THREE.BoxGeometry(0.02, 0.004, 0.05), M.redGlow), 0.3, 0.802, 0.06));

  // headset on a stand
  if (withHeadset) {
    const hs = new THREE.Group();
    hs.add(at(new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 0.01, 24), M.gunmetal), 0, 0.005, 0));
    hs.add(at(new THREE.Mesh(new THREE.CylinderGeometry(0.01, 0.01, 0.24, 12), M.gunmetal), 0, 0.13, 0));
    const band = new THREE.Mesh(new THREE.TorusGeometry(0.085, 0.012, 10, 32, Math.PI), M.blackMatte);
    band.position.set(0, 0.24, 0);
    hs.add(band);
    for (const s of [-1, 1]) {
      const cup = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.045, 0.035, 24), M.leather);
      cup.rotation.z = Math.PI / 2;
      cup.position.set(s * 0.085, 0.2, 0);
      hs.add(cup);
      hs.add(at(new THREE.Mesh(new THREE.TorusGeometry(0.03, 0.004, 8, 24), M.redGlow), s * 0.105, 0.2, 0, 0).rotateY(Math.PI / 2));
    }
    hs.position.set(-width / 2 + 0.16, 0.762, -0.12);
    g.add(hs);
  }
  return g;
}

/* ────────────────────────────────────────────
   PC tower with tempered-glass side (glass faces +X)
──────────────────────────────────────────── */
export function pcTower() {
  const g = new THREE.Group();
  const body = rbox(0.24, 0.48, 0.46, M.blackMatte, 0.012);
  body.position.y = 0.24;
  g.add(body);
  const glass = new THREE.Mesh(new THREE.PlaneGeometry(0.4, 0.42), M.glass);
  glass.rotation.y = Math.PI / 2;
  glass.position.set(0.121, 0.24, 0);
  g.add(glass);
  // interior: motherboard, GPU, three red fans
  g.add(at(rbox(0.005, 0.36, 0.34, M.gunmetal, 0.002), -0.1, 0.25, 0));
  g.add(at(rbox(0.16, 0.035, 0.26, M.blackGloss, 0.006), -0.02, 0.2, 0.02));
  g.add(at(rbox(0.12, 0.004, 0.24, M.redGlow, 0.001), -0.02, 0.183, 0.02));
  for (let i = 0; i < 3; i++) {
    const fan = new THREE.Mesh(new THREE.TorusGeometry(0.05, 0.006, 8, 32), M.redGlow);
    fan.rotation.y = Math.PI / 2;
    fan.position.set(0.0, 0.1 + i * 0.14, -0.19);
    g.add(fan);
  }
  g.add(at(rbox(0.22, 0.01, 0.42, M.redGlow, 0.001), 0, 0.485, 0));
  return g;
}

/* ────────────────────────────────────────────
   Booth bench + tall bookshelf back — bench front faces -X in local space
──────────────────────────────────────────── */
export function boothUnit({ length = 2.8, depth = 0.72 }) {
  const g = new THREE.Group();
  // base cabinets with door reveals
  const base = rbox(depth, 0.46, length, M.cabinet, 0.01);
  base.position.set(0, 0.23, 0);
  g.add(base);
  const doors = Math.round(length / 0.7);
  for (let i = 0; i < doors; i++) {
    const z = -length / 2 + (i + 0.5) * (length / doors);
    g.add(at(rbox(0.008, 0.36, 0.02, M.blackMatte, 0.002), -depth / 2 - 0.002, 0.23, z));
    g.add(at(rbox(0.01, 0.01, 0.16, M.chrome, 0.003), -depth / 2 - 0.006, 0.4, z + 0.16));
  }
  // toe-kick LED
  const kick = ledStrip(length - 0.1, 'z');
  kick.position.set(-depth / 2 + 0.02, 0.03, 0);
  g.add(kick);

  // cushions (segmented) with bolsters
  const segs = Math.max(2, Math.round(length / 0.7));
  for (let i = 0; i < segs; i++) {
    const z = -length / 2 + (i + 0.5) * (length / segs);
    const c = rbox(0.46, 0.11, length / segs - 0.03, M.cushion, 0.045);
    c.position.set(-depth / 2 + 0.25, 0.515, z);
    g.add(c);
  }
  const bolsterGeo = new THREE.CapsuleGeometry(0.09, 0.32, 8, 16);
  for (const z of [-length / 2 + 0.3, length / 2 - 0.3]) {
    const b = new THREE.Mesh(bolsterGeo, M.cushion);
    b.rotation.z = Math.PI / 2;
    b.rotation.y = Math.PI / 2;
    b.position.set(-depth / 2 + 0.22, 0.66, z);
    b.castShadow = true;
    g.add(b);
  }
  // back cushions
  for (let i = 0; i < segs; i++) {
    const z = -length / 2 + (i + 0.5) * (length / segs);
    const bc = rbox(0.1, 0.42, length / segs - 0.04, M.cushion, 0.04);
    bc.position.set(depth / 2 - 0.3, 0.8, z);
    bc.rotation.z = 0.1;
    g.add(bc);
  }

  // back panel (upholstered strip behind cushions)
  const backPanel = rbox(0.06, 0.5, length, M.cabinet, 0.008);
  backPanel.position.set(depth / 2 - 0.03, 0.75, 0);
  g.add(backPanel);
  return g;
}

/* ────────────────────────────────────────────
   Open bookshelf tower — open face toward -X in local space
──────────────────────────────────────────── */
export function bookshelf({ width = 0.5, height = 1.6, depth = 0.3, shelves = 4, y0 = 0 }) {
  const g = new THREE.Group();
  const side = 0.025;
  const mk = (w, h, d, x, y, z) => at(rbox(w, h, d, M.cabinet, 0.004), x, y, z);
  // back, two sides, top, bottom
  g.add(mk(side, height, width, depth / 2 - side / 2, y0 + height / 2, 0));
  g.add(mk(depth, height, side, 0, y0 + height / 2, -width / 2 + side / 2));
  g.add(mk(depth, height, side, 0, y0 + height / 2, width / 2 - side / 2));
  g.add(mk(depth, side, width, 0, y0 + height - side / 2, 0));
  g.add(mk(depth, side, width, 0, y0 + side / 2, 0));
  const gap = (height - side) / shelves;
  for (let s = 0; s < shelves; s++) {
    const y = y0 + side + s * gap;
    if (s > 0) g.add(mk(depth - 0.01, side, width - side * 2, 0, y, 0));
    // LED under the shelf above, at the front edge
    const led = ledStrip(width - 0.08, 'z');
    led.position.set(-depth / 2 + 0.02, y + gap - side - 0.012, 0);
    g.add(led);
    // contents: books or a collectible
    const items = 3 + Math.floor(Math.random() * 4);
    let z = -width / 2 + side + 0.03;
    for (let k = 0; k < items && z < width / 2 - 0.06; k++) {
      const bw = 0.02 + Math.random() * 0.025;
      const bh = Math.min(gap - 0.06, 0.16 + Math.random() * 0.12);
      const col = [0xe94b58, 0xf2f2f2, 0x2b2c31, 0xffc933, 0x8fa3ff, 0x4dd0e1][Math.floor(Math.random() * 6)];
      const book = rbox(depth - 0.1, bh, bw, new THREE.MeshStandardMaterial({ color: col, roughness: 0.7 }), 0.003);
      book.position.set(0.01, y + side / 2 + bh / 2, z + bw / 2);
      g.add(book);
      z += bw + 0.004;
    }
    if (s % 2 === 1) {
      const fig = new THREE.Mesh(new THREE.SphereGeometry(0.045, 20, 14), new THREE.MeshPhysicalMaterial({ color: 0xff3b45, roughness: 0.2, clearcoat: 1 }));
      fig.position.set(0.0, y + side / 2 + 0.045, width / 2 - 0.09);
      fig.castShadow = true;
      g.add(fig);
    }
  }
  return g;
}

/* ────────────────────────────────────────────
   Window with blinds + outside view — faces -X in local space
──────────────────────────────────────────── */
export function windowUnit({ width = 2.2, height = 1.15, viewTex }) {
  const g = new THREE.Group();
  const frame = rbox(0.06, height + 0.1, width + 0.1, M.blackMatte, 0.01);
  g.add(frame);
  const view = new THREE.Mesh(new THREE.PlaneGeometry(width, height), new THREE.MeshStandardMaterial({
    map: viewTex, emissive: 0xffffff, emissiveMap: viewTex, emissiveIntensity: 0.9, roughness: 1,
  }));
  view.rotation.y = -Math.PI / 2;
  view.position.x = 0.0;
  g.add(view);
  const glass = new THREE.Mesh(new THREE.PlaneGeometry(width, height), M.glass);
  glass.rotation.y = -Math.PI / 2;
  glass.position.x = -0.02;
  g.add(glass);
  // slats (slightly tilted)
  const slats = Math.floor(height / 0.06);
  for (let i = 0; i < slats; i++) {
    const s = rbox(0.045, 0.006, width - 0.06, M.blackGloss, 0.002);
    s.rotation.z = 0.35;
    s.position.set(-0.06, -height / 2 + 0.04 + i * 0.06, 0);
    g.add(s);
  }
  g.add(at(rbox(0.05, 0.05, width - 0.04, M.gunmetal, 0.008), -0.06, height / 2 + 0.02, 0));
  return g;
}

/* ────────────────────────────────────────────
   Display cabinet along a wall — front faces -Z in local space
──────────────────────────────────────────── */
export function displayCabinet({ width = 2.15, depth = 0.4, height = 0.95 }) {
  const g = new THREE.Group();
  const body = rbox(width, height, depth, M.cabinet, 0.01);
  body.position.y = height / 2;
  g.add(body);
  // glass front over open niches
  const niche = new THREE.Mesh(new THREE.BoxGeometry(width - 0.12, height - 0.24, depth - 0.1), new THREE.MeshStandardMaterial({ color: 0x0a0a0d, roughness: 0.85 }));
  niche.position.set(0, height / 2 + 0.03, -0.02);
  g.add(niche);
  const glass = new THREE.Mesh(new THREE.PlaneGeometry(width - 0.12, height - 0.24), M.glass);
  glass.position.set(0, height / 2 + 0.03, -depth / 2 - 0.001);
  glass.rotation.y = Math.PI;
  g.add(glass);
  const led = ledStrip(width - 0.16, 'x');
  led.position.set(0, height - 0.13, -depth / 2 + 0.06);
  g.add(led);
  const led2 = ledStrip(width - 0.16, 'x', M.warmGlow);
  led2.position.set(0, height + 0.006, -depth / 2 + 0.02);
  g.add(led2);
  // figurines
  const cols = [0xff3b45, 0xf5f5f5, 0xffc933, 0x2b2c31, 0x8fa3ff];
  const n = 7;
  for (let i = 0; i < n; i++) {
    const x = -width / 2 + 0.2 + i * ((width - 0.4) / (n - 1));
    const h = 0.14 + Math.random() * 0.12;
    const body2 = new THREE.Mesh(new THREE.CapsuleGeometry(0.035, h - 0.07, 6, 12), new THREE.MeshStandardMaterial({ color: cols[i % cols.length], roughness: 0.45 }));
    body2.position.set(x, 0.14 + h / 2, -0.02);
    body2.castShadow = true;
    g.add(body2);
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.035, 16, 12), new THREE.MeshStandardMaterial({ color: 0xf1d5c2, roughness: 0.6 }));
    head.position.set(x, 0.14 + h + 0.03, -0.02);
    g.add(head);
  }
  return g;
}

/* ────────────────────────────────────────────
   Floating shelf with red under-glow — length along Z
──────────────────────────────────────────── */
export function floatingShelf(length = 0.9) {
  const g = new THREE.Group();
  g.add(rbox(0.24, 0.035, length, M.blackGloss, 0.008));
  const led = ledStrip(length - 0.06, 'z');
  led.position.set(-0.08, -0.024, 0);
  g.add(led);
  // a helmet and a figure
  const helmet = new THREE.Mesh(new THREE.SphereGeometry(0.09, 24, 16, 0, Math.PI * 2, 0, Math.PI * 0.62), new THREE.MeshPhysicalMaterial({ color: 0xe11d2a, roughness: 0.2, clearcoat: 1 }));
  helmet.position.set(0.02, 0.02, -length / 4);
  helmet.castShadow = true;
  g.add(helmet);
  const fig = new THREE.Mesh(new THREE.CapsuleGeometry(0.03, 0.1, 6, 12), new THREE.MeshStandardMaterial({ color: 0xf5f5f5, roughness: 0.5 }));
  fig.position.set(0.02, 0.1, length / 4);
  g.add(fig);
  return g;
}

/* ────────────────────────────────────────────
   Red industrial pipe run along a path
──────────────────────────────────────────── */
export function redPipe(points, radius = 0.025) {
  const curve = new THREE.CatmullRomCurve3(points.map((p) => new THREE.Vector3(...p)));
  const tube = new THREE.Mesh(new THREE.TubeGeometry(curve, 64, radius, 12, false), new THREE.MeshStandardMaterial({ color: 0xc41a24, roughness: 0.35, metalness: 0.6 }));
  tube.castShadow = true;
  return tube;
}

export function wallLogoPlane(tex, w = 1.0) {
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, w / 2), new THREE.MeshStandardMaterial({
    map: tex, emissive: 0xffffff, emissiveMap: tex, emissiveIntensity: 2.6, transparent: true, roughness: 0.5,
  }));
  return m;
}

export function tetrisLamp() {
  const g = new THREE.Group();
  const cells = [[0, 0], [1, 0], [1, 1], [2, 1], [0, 2], [1, 2], [2, 2], [1, 3]];
  cells.forEach(([x, y], i) => {
    const c = rbox(0.11, 0.11, 0.11, i % 3 === 0 ? M.redGlow : M.warmGlow, 0.01);
    c.position.set(x * 0.115, 0.06 + y * 0.115, 0);
    g.add(c);
  });
  return g;
}

export const Materials = M;
export { TX };
