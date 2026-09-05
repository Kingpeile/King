import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/examples/jsm/geometries/RoundedBoxGeometry.js';
import * as TX from './textures.js';

/* ────────────────────────────────────────────
   Palette / materials (swappable per theme)
──────────────────────────────────────────── */
export const THEMES = {
  ferrari: {
    key: 'ferrari',
    name: '法拉利 Rosso Corsa',
    style: 'ferrari',
    accent: 0xd40000,
    led: 0xff1e1e,
    ledIntensity: 2.6,
    furniture: 0x0d0d10,
    furnitureRough: 0.2,
    cabinet: 0x131418,
    wall: 0xe9e6e0,
    wallBase: '#d8d5cf',
    wallStreak: 200,
    floorBase: '#2b2c30',
    floorGrout: '#141416',
    floorVein: '80,82,90',
    pegBase: '#8d9199',
    pegHole: '#3a3d44',
    cushion: 0x15161a,
    background: 0x050506,
    envIntensity: 0.34,
    exposure: 0.95,
    keyLight: 18,
    coveColor: 0xffe2c2,
    coveIntensity: 0.45,
    rugBase: '#22232a',
    rugLo: 26,
    bloom: { strength: 0.26, radius: 0.5, threshold: 0.9 },
    mario: false,
  },
  red: {
    key: 'red',
    name: '深红赛博',
    style: 'cyber',
    accent: 0xff2a36,
    led: 0xff2a36,
    ledIntensity: 3.0,
    furniture: 0x0b0c0f,      // desks / shelves / cabinets
    furnitureRough: 0.22,
    cabinet: 0x1c1d22,
    wall: 0xd4d6db,
    wallBase: '#b9bcc3',
    wallStreak: 150,
    floorBase: '#c9cbd0',
    floorGrout: '#9a9ca3',
    floorVein: '150,152,160',
    pegBase: '#8d9199',
    pegHole: '#3a3d44',
    cushion: 0xf3f2ee,
    background: 0x040405,
    envIntensity: 0.28,
    exposure: 0.9,
    keyLight: 22,
    coveColor: 0xffe4c4,
    coveIntensity: 0.55,
    rugBase: '#2a2b31',
    rugLo: 30,
    bloom: { strength: 0.3, radius: 0.5, threshold: 0.9 },
    mario: false,
  },
  white: {
    key: 'white',
    name: '白色马里奥',
    style: 'mario',
    accent: 0xe4291b,
    led: 0xfff4e6,
    ledIntensity: 1.6,
    furniture: 0xf4f5f7,
    furnitureRough: 0.25,
    cabinet: 0xf1f2f4,
    wall: 0xe9eaee,
    wallBase: '#d9dbe0',
    wallStreak: 200,
    floorBase: '#eceef1',
    floorGrout: '#c3c6cc',
    floorVein: '190,192,198',
    pegBase: '#b3b7bf',
    pegHole: '#7d8189',
    cushion: 0xffffff,
    background: 0x0e0f12,
    envIntensity: 0.3,
    exposure: 0.72,
    keyLight: 14,
    coveColor: 0xffffff,
    coveIntensity: 0.3,
    bloom: { strength: 0.12, radius: 0.4, threshold: 0.97 },
    rugBase: '#d8d9dc',
    rugLo: 190,
    mario: true,
  },
};

export let RED = 0xff2a36;
export let M = null;
export let THEME = THEMES.red;

export function applyTheme(theme) {
  THEME = theme;
  RED = theme.accent;
  const F = theme.style === 'ferrari';
  const carbonMap = TX.carbonFiber([8, 8]).map;
  const led = new THREE.MeshStandardMaterial({ color: theme.led, emissive: theme.led, emissiveIntensity: theme.ledIntensity, roughness: 0.4 });
  const carbon = new THREE.MeshPhysicalMaterial({ map: carbonMap, roughness: 0.25, metalness: 0.2, clearcoat: 1.0, clearcoatRoughness: 0.08 });
  const leather = F
    ? new THREE.MeshPhysicalMaterial({ color: 0x101114, roughness: 0.5, metalness: 0.05, clearcoat: 0.35, clearcoatRoughness: 0.45 })
    : new THREE.MeshPhysicalMaterial({ color: 0x14151a, roughness: 0.55, metalness: 0.05, clearcoat: 0.25, clearcoatRoughness: 0.5 });
  M = {
    blackMatte: new THREE.MeshStandardMaterial({ color: 0x0f1013, roughness: 0.6, metalness: 0.2 }),
    blackGloss: new THREE.MeshPhysicalMaterial({ color: 0x0b0c0f, roughness: 0.22, metalness: 0.5, clearcoat: 0.8, clearcoatRoughness: 0.15 }),
    furniture: F ? carbon : new THREE.MeshPhysicalMaterial({ color: theme.furniture, roughness: theme.furnitureRough, metalness: theme.mario ? 0.05 : 0.5, clearcoat: 0.8, clearcoatRoughness: 0.15 }),
    mesh: new THREE.MeshStandardMaterial({ color: 0x15161a, roughness: 0.95, metalness: 0.0 }),
    leather,
    chrome: new THREE.MeshStandardMaterial({ color: 0xd8dadf, roughness: 0.15, metalness: 1.0 }),
    gunmetal: new THREE.MeshStandardMaterial({ color: theme.mario ? 0xd9dbe0 : 0x3b3e46, roughness: 0.35, metalness: 0.9 }),
    accent: new THREE.MeshStandardMaterial({ color: theme.accent, roughness: 0.5, metalness: 0.1 }),
    led,
    redGlow: new THREE.MeshStandardMaterial({ color: theme.accent, emissive: theme.accent, emissiveIntensity: 2.6, roughness: 0.4 }),
    warmGlow: new THREE.MeshStandardMaterial({ color: 0xfff1dc, emissive: 0xffe2bd, emissiveIntensity: 2.2, roughness: 0.6 }),
    cushion: F ? leather : new THREE.MeshStandardMaterial({ color: theme.cushion, roughness: 0.95, metalness: 0 }),
    glass: new THREE.MeshPhysicalMaterial({ color: 0xbfd6e6, roughness: 0.05, metalness: 0, transparent: true, opacity: 0.28, clearcoat: 1 }),
    cabinet: F
      ? new THREE.MeshPhysicalMaterial({ color: theme.cabinet, roughness: 0.22, metalness: 0.3, clearcoat: 0.9, clearcoatRoughness: 0.1 })
      : new THREE.MeshPhysicalMaterial({ color: theme.cabinet, roughness: 0.35, metalness: theme.mario ? 0.05 : 0.25, clearcoat: 0.4, clearcoatRoughness: 0.3 }),
    niche: new THREE.MeshStandardMaterial({ color: theme.mario ? 0xdfe1e6 : F ? 0x1c1d22 : 0x0a0a0d, roughness: 0.85 }),
    // Ferrari palette
    carbon,
    rosso: new THREE.MeshPhysicalMaterial({ color: 0xd40000, roughness: 0.18, metalness: 0.15, clearcoat: 1, clearcoatRoughness: 0.05 }),
    giallo: new THREE.MeshPhysicalMaterial({ color: 0xffd400, roughness: 0.25, clearcoat: 0.9 }),
    rossoSoft: new THREE.MeshStandardMaterial({ color: 0xb80009, roughness: 0.8 }),
    gialloSoft: new THREE.MeshStandardMaterial({ color: 0xe3ba00, roughness: 0.8 }),
    rubber: new THREE.MeshStandardMaterial({ color: 0x14151a, roughness: 0.95 }),
    darkGlass: new THREE.MeshPhysicalMaterial({ color: 0x0a0a0c, roughness: 0.05, metalness: 0.2, clearcoat: 1 }),
    fabric: new THREE.MeshStandardMaterial({ color: F ? 0x2a2b30 : theme.mario ? 0xe6e7ea : 0x2a2b31, roughness: 1 }),
    stone: new THREE.MeshPhysicalMaterial({ color: F ? 0xf0eee9 : 0xf4f4f6, roughness: 0.3, clearcoat: 0.6, clearcoatRoughness: 0.2 }),
    // Mario palette
    marioRed: new THREE.MeshPhysicalMaterial({ color: 0xe4291b, roughness: 0.3, clearcoat: 0.8 }),
    marioGreen: new THREE.MeshPhysicalMaterial({ color: 0x2fa84f, roughness: 0.3, clearcoat: 0.8 }),
    marioYellow: new THREE.MeshStandardMaterial({ color: 0xf7b515, roughness: 0.35, emissive: 0xf7b515, emissiveIntensity: 0.25 }),
    marioBlue: new THREE.MeshPhysicalMaterial({ color: 0x2f7be5, roughness: 0.3, clearcoat: 0.8 }),
    marioCream: new THREE.MeshStandardMaterial({ color: 0xf6e3c3, roughness: 0.6 }),
    marioBrown: new THREE.MeshStandardMaterial({ color: 0x7a2a00, roughness: 0.6 }),
  };
  return M;
}
applyTheme(THEMES.red);

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

export function ledStrip(length, axis = 'x', material = null) {
  const geo =
    axis === 'x' ? new THREE.BoxGeometry(length, 0.014, 0.014)
      : axis === 'y' ? new THREE.BoxGeometry(0.014, length, 0.014)
        : new THREE.BoxGeometry(0.014, 0.014, length);
  return new THREE.Mesh(geo, material || M.led);
}

/* ────────────────────────────────────────────
   Gaming chair — faces -Z in local space
──────────────────────────────────────────── */
export function gamingChair() {
  const g = new THREE.Group();
  const shell = M.leather; // reference keeps black ergonomic chairs in both themes
  const pad = M.leather;

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
  g.add(at(new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.28, 20), M.chrome), 0, 0.22, 0));
  g.add(at(new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.045, 0.14, 20), M.blackMatte), 0, 0.14, 0));

  const seat = rbox(0.5, 0.1, 0.5, pad, 0.04);
  seat.position.set(0, 0.45, 0);
  g.add(seat);
  g.add(at(rbox(0.1, 0.09, 0.44, shell, 0.03), -0.22, 0.52, 0.02));
  g.add(at(rbox(0.1, 0.09, 0.44, shell, 0.03), 0.22, 0.52, 0.02));
  g.add(at(rbox(0.28, 0.02, 0.36, M.mesh, 0.01), 0, 0.51, 0));

  const back = new THREE.Group();
  back.position.set(0, 0.5, 0.22);
  back.rotation.x = -0.14;
  back.add(at(rbox(0.5, 0.72, 0.09, shell, 0.04), 0, 0.36, 0));
  back.add(at(rbox(0.12, 0.6, 0.11, shell, 0.04), -0.24, 0.34, -0.03));
  back.add(at(rbox(0.12, 0.6, 0.11, shell, 0.04), 0.24, 0.34, -0.03));
  back.add(at(rbox(0.3, 0.55, 0.02, M.mesh, 0.01), 0, 0.36, -0.045));
  back.add(at(rbox(0.06, 0.4, 0.015, M.accent, 0.005), -0.11, 0.36, -0.052));
  back.add(at(rbox(0.06, 0.4, 0.015, M.accent, 0.005), 0.11, 0.36, -0.052));
  back.add(at(rbox(0.34, 0.16, 0.1, pad, 0.05), 0, 0.82, -0.01));
  g.add(back);

  for (const s of [-1, 1]) {
    g.add(at(rbox(0.06, 0.2, 0.06, M.blackMatte, 0.01), s * 0.3, 0.6, 0.05));
    g.add(at(rbox(0.08, 0.035, 0.3, pad, 0.015), s * 0.3, 0.71, -0.02));
  }
  return g;
}

/* ────────────────────────────────────────────
   Monitor (27", concave toward +Z)
──────────────────────────────────────────── */
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
  const body = THEME.mario ? M.furniture : M.blackGloss;

  const screenMat = new THREE.MeshStandardMaterial({
    map: screenTex, emissive: 0xffffff, emissiveMap: screenTex, emissiveIntensity: 1.1, roughness: 0.3, metalness: 0.0,
  });
  g.add(new THREE.Mesh(curvedScreenGeometry(w, h, radius), screenMat));
  const bezel = new THREE.Mesh(curvedScreenGeometry(w + 0.02, h + 0.02, radius), M.blackGloss);
  bezel.position.z = -0.004;
  g.add(bezel);
  const backMat = body.clone();
  backMat.side = THREE.BackSide;
  const backCap = new THREE.Mesh(curvedScreenGeometry(w + 0.02, h + 0.02, radius), backMat);
  backCap.position.z = -0.035;
  g.add(backCap);
  const shell = rbox(w - 0.1, h - 0.1, 0.03, body, 0.01);
  shell.position.z = -0.02;
  g.add(shell);
  g.add(at(new THREE.Mesh(new THREE.TorusGeometry(0.06, 0.006, 8, 32), M.redGlow), 0, 0, -0.035));
  g.add(at(rbox(0.05, 0.26, 0.05, M.gunmetal, 0.01), 0, -0.3, -0.05));
  g.add(at(rbox(0.3, 0.015, 0.2, M.gunmetal, 0.006), 0, -0.43, -0.02));
  return g;
}

/* ────────────────────────────────────────────
   Height-adjustable desk with peripherals — sitter at +Z facing -Z
──────────────────────────────────────────── */
export function gamingDesk({ width = 1.5, depth = 0.7, screenTex, keyboardTex, withHeadset = true, withTower = false }) {
  const g = new THREE.Group();
  const top = rbox(width, 0.035, depth, M.furniture, 0.012);
  top.position.y = 0.745;
  g.add(top);
  g.add(at(rbox(width - 0.1, 0.004, 0.012, M.led, 0.001), 0, 0.764, depth / 2 - 0.02));
  if (THEME.style === 'ferrari') {
    // Rosso edge trim along the front of the carbon top
    g.add(at(rbox(width, 0.012, 0.01, M.rosso, 0.003), 0, 0.745, depth / 2 + 0.003));
  }
  if (withTower) {
    const pc = pcTower();
    pc.rotation.y = -Math.PI / 2; // tempered glass faces the sitter
    pc.position.set(width / 2 - 0.2, 0.7625, -0.05);
    g.add(pc);
  }

  for (const s of [-1, 1]) {
    const x = s * (width / 2 - 0.12);
    g.add(at(rbox(0.07, 0.12, depth - 0.16, M.gunmetal, 0.01), x, 0.67, 0));
    g.add(at(rbox(0.06, 0.55, 0.09, M.gunmetal, 0.01), x, 0.34, 0));
    g.add(at(rbox(0.075, 0.03, depth - 0.1, M.gunmetal, 0.01), x, 0.03, 0));
  }
  g.add(at(rbox(width - 0.5, 0.08, 0.14, THEME.mario ? M.furniture : M.blackMatte, 0.01), 0, 0.68, -0.18));
  const glow = ledStrip(width - 0.2, 'x');
  glow.position.set(0, 0.72, depth / 2 - 0.05);
  g.add(glow);

  const mon = monitor(screenTex);
  mon.position.set(0, 1.19, -0.22);
  g.add(mon);

  const pad = rbox(0.9, 0.004, 0.4, M.mesh, 0.002);
  pad.position.set(0.05, 0.765, 0.05);
  g.add(pad);
  const kb = rbox(0.44, 0.03, 0.15, THEME.mario ? M.furniture : M.blackMatte, 0.006);
  kb.position.set(-0.05, 0.78, 0.06);
  g.add(kb);
  const keys = new THREE.Mesh(new THREE.PlaneGeometry(0.42, 0.13), new THREE.MeshStandardMaterial({
    map: keyboardTex, emissive: 0xffffff, emissiveMap: keyboardTex, emissiveIntensity: 0.35, roughness: 0.6,
  }));
  keys.rotation.x = -Math.PI / 2;
  keys.position.set(-0.05, 0.796, 0.06);
  g.add(keys);
  const mouse = new THREE.Mesh(new THREE.SphereGeometry(0.036, 24, 16), THEME.mario ? M.furniture : M.blackGloss);
  mouse.scale.set(1, 0.55, 1.6);
  mouse.position.set(0.3, 0.785, 0.08);
  mouse.castShadow = true;
  g.add(mouse);
  g.add(at(new THREE.Mesh(new THREE.BoxGeometry(0.02, 0.004, 0.05), M.redGlow), 0.3, 0.802, 0.06));

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
  const body = THEME.mario ? M.furniture : M.blackMatte;
  const W = 0.24, H = 0.48, Dp = 0.46;
  // open-sided chassis (glass on +X)
  g.add(at(rbox(0.02, H, Dp, body, 0.008), -W / 2 + 0.01, H / 2, 0));
  g.add(at(rbox(W, 0.02, Dp, body, 0.008), 0, H - 0.01, 0));
  g.add(at(rbox(W, 0.02, Dp, body, 0.008), 0, 0.01, 0));
  g.add(at(rbox(W, H, 0.02, body, 0.008), 0, H / 2, Dp / 2 - 0.01));
  g.add(at(rbox(W, H, 0.02, body, 0.008), 0, H / 2, -Dp / 2 + 0.01));
  // PSU shroud, motherboard tray, board
  const pcb = new THREE.MeshStandardMaterial({ color: 0x0b0b0f, roughness: 0.75 });
  g.add(at(rbox(W - 0.03, 0.09, Dp - 0.04, M.blackMatte, 0.006), -0.005, 0.065, 0));
  g.add(at(rbox(0.006, 0.34, 0.38, M.blackMatte, 0.002), -0.105, 0.29, 0.0));
  g.add(at(rbox(0.004, 0.28, 0.28, pcb, 0.002), -0.1, 0.29, 0.02));
  // GPU (with RGB edge), CPU block with glow ring, RAM sticks
  g.add(at(rbox(0.16, 0.035, 0.28, M.blackGloss, 0.006), -0.02, 0.2, 0.02));
  g.add(at(rbox(0.12, 0.004, 0.24, M.redGlow, 0.001), -0.02, 0.183, 0.02));
  g.add(at(rbox(0.045, 0.07, 0.07, M.blackGloss, 0.004), -0.075, 0.36, 0.05));
  const cpuRing = new THREE.Mesh(new THREE.TorusGeometry(0.028, 0.004, 8, 32), M.redGlow);
  cpuRing.rotation.y = Math.PI / 2;
  cpuRing.position.set(-0.05, 0.36, 0.05);
  g.add(cpuRing);
  for (let i = 0; i < 4; i++) {
    g.add(at(rbox(0.03, 0.12, 0.006, M.blackGloss, 0.001), -0.08, 0.36, -0.03 - i * 0.012));
    g.add(at(rbox(0.026, 0.006, 0.004, M.led, 0.001), -0.08, 0.423, -0.03 - i * 0.012));
  }
  // intake fans at the front (+Z) and exhaust at the rear
  for (let i = 0; i < 3; i++) {
    const fan = new THREE.Mesh(new THREE.TorusGeometry(0.05, 0.006, 8, 32), M.redGlow);
    fan.position.set(-0.02, 0.13 + i * 0.12, Dp / 2 - 0.025);
    g.add(fan);
  }
  const ex = new THREE.Mesh(new THREE.TorusGeometry(0.045, 0.005, 8, 32), M.redGlow);
  ex.position.set(-0.02, 0.38, -Dp / 2 + 0.025);
  g.add(ex);
  // tempered-glass side panel
  const glassMat = new THREE.MeshPhysicalMaterial({ color: 0x3a4652, roughness: 0.03, metalness: 0, transparent: true, opacity: 0.22, clearcoat: 0.25, clearcoatRoughness: 0.05, depthWrite: false });
  const glass = new THREE.Mesh(new THREE.PlaneGeometry(Dp - 0.02, H - 0.02), glassMat);
  glass.rotation.y = Math.PI / 2;
  glass.position.set(W / 2 - 0.004, H / 2, 0);
  g.add(glass);
  g.add(at(rbox(0.22, 0.008, 0.42, M.led, 0.001), 0, H + 0.004, 0));
  return g;
}

/* ────────────────────────────────────────────
   Booth bench — front faces -X in local space
──────────────────────────────────────────── */
export function boothUnit({ length = 2.8, depth = 0.72, withBack = true, bolsters = true }) {
  const g = new THREE.Group();
  const F = THEME.style === 'ferrari';
  const baseMat = THEME.mario ? M.blackGloss : M.cabinet; // reference: black base under white cushions
  const base = rbox(depth, 0.46, length, baseMat, 0.01);
  base.position.set(0, 0.23, 0);
  g.add(base);
  const doors = Math.round(length / 0.7);
  for (let i = 0; i < doors; i++) {
    const z = -length / 2 + (i + 0.5) * (length / doors);
    g.add(at(rbox(0.008, 0.36, 0.02, M.blackMatte, 0.002), -depth / 2 - 0.002, 0.23, z));
    g.add(at(rbox(0.01, 0.01, 0.16, M.chrome, 0.003), -depth / 2 - 0.006, 0.4, z + 0.16));
  }
  const kick = ledStrip(length - 0.1, 'z');
  kick.position.set(-depth / 2 + 0.02, 0.03, 0);
  g.add(kick);

  const cushionW = Math.min(0.46, depth - 0.02);
  const segs = Math.max(2, Math.round(length / 0.7));
  for (let i = 0; i < segs; i++) {
    const z = -length / 2 + (i + 0.5) * (length / segs);
    const segLen = length / segs - 0.03;
    const c = rbox(cushionW, 0.11, segLen, M.cushion, 0.045);
    c.position.set(-depth / 2 + cushionW / 2 + 0.01, 0.515, z);
    g.add(c);
    if (F) {
      // red piping on the front edge of every seat cushion
      g.add(at(rbox(0.012, 0.012, segLen - 0.04, M.rosso, 0.004), -depth / 2 + 0.012, 0.572, z));
    }
  }
  if (bolsters) {
    const bolsterGeo = new THREE.CapsuleGeometry(0.09, 0.32, 8, 16);
    for (const z of [-length / 2 + 0.3, length / 2 - 0.3]) {
      const b = new THREE.Mesh(bolsterGeo, M.cushion);
      b.rotation.z = Math.PI / 2;
      b.rotation.y = Math.PI / 2;
      b.position.set(-depth / 2 + 0.22, 0.66, z);
      b.castShadow = true;
      g.add(b);
    }
  }
  if (withBack) {
    for (let i = 0; i < segs; i++) {
      const z = -length / 2 + (i + 0.5) * (length / segs);
      const bc = rbox(0.1, 0.42, length / segs - 0.04, M.cushion, 0.04);
      bc.position.set(depth / 2 - 0.12, 0.8, z);
      bc.rotation.z = 0.1;
      g.add(bc);
      if (F) g.add(at(rbox(0.012, 0.3, 0.012, M.rosso, 0.004), depth / 2 - 0.175, 0.8, z));
    }
    const backPanel = rbox(0.06, 0.5, length, M.cabinet, 0.008);
    backPanel.position.set(depth / 2 - 0.03, 0.75, 0);
    g.add(backPanel);
  }
  return g;
}

/* ────────────────────────────────────────────
   Open bookshelf tower — open face toward -X in local space
──────────────────────────────────────────── */
export function bookshelf({ width = 0.5, height = 1.6, depth = 0.3, shelves = 4, y0 = 0 }) {
  const g = new THREE.Group();
  const side = 0.025;
  const mk = (w, h, d, x, y, z) => at(rbox(w, h, d, M.cabinet, 0.004), x, y, z);
  g.add(mk(side, height, width, depth / 2 - side / 2, y0 + height / 2, 0));
  g.add(mk(depth, height, side, 0, y0 + height / 2, -width / 2 + side / 2));
  g.add(mk(depth, height, side, 0, y0 + height / 2, width / 2 - side / 2));
  g.add(mk(depth, side, width, 0, y0 + height - side / 2, 0));
  g.add(mk(depth, side, width, 0, y0 + side / 2, 0));
  const gap = (height - side) / shelves;
  for (let s = 0; s < shelves; s++) {
    const y = y0 + side + s * gap;
    if (s > 0) g.add(mk(depth - 0.01, side, width - side * 2, 0, y, 0));
    const led = ledStrip(width - 0.08, 'z');
    led.position.set(-depth / 2 + 0.02, y + gap - side - 0.012, 0);
    g.add(led);
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
      const fig = THEME.mario
        ? mushroom(0.05)
        : new THREE.Mesh(new THREE.SphereGeometry(0.045, 20, 14), new THREE.MeshPhysicalMaterial({ color: 0xff3b45, roughness: 0.2, clearcoat: 1 }));
      fig.position.set(0.0, y + side / 2 + (THEME.mario ? 0 : 0.045), width / 2 - 0.09);
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
  const frameMat = M.blackMatte;
  g.add(rbox(0.06, height + 0.1, width + 0.1, frameMat, 0.01));
  const view = new THREE.Mesh(new THREE.PlaneGeometry(width, height), new THREE.MeshStandardMaterial({
    map: viewTex, emissive: 0xffffff, emissiveMap: viewTex, emissiveIntensity: 0.9, roughness: 1,
  }));
  view.rotation.y = -Math.PI / 2;
  g.add(view);
  const glass = new THREE.Mesh(new THREE.PlaneGeometry(width, height), M.glass);
  glass.rotation.y = -Math.PI / 2;
  glass.position.x = -0.02;
  g.add(glass);
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
   Display cabinet — front faces -Z in local space
──────────────────────────────────────────── */
export function displayCabinet({ width = 2.15, depth = 0.4, height = 0.95 }) {
  const g = new THREE.Group();
  const body = rbox(width, height, depth, M.cabinet, 0.01);
  body.position.y = height / 2;
  g.add(body);
  const niche = new THREE.Mesh(new THREE.BoxGeometry(width - 0.12, height - 0.24, depth - 0.1), M.niche);
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
  const n = 7;
  for (let i = 0; i < n; i++) {
    const x = -width / 2 + 0.2 + i * ((width - 0.4) / (n - 1));
    if (THEME.mario) {
      const kinds = [() => mushroom(0.07), () => questionBlock(0.14), () => star(0.08), () => mushroom(0.07, 0x2fa84f), () => brickBlock(0.14), () => mushroom(0.07), () => questionBlock(0.14)];
      const p = kinds[i % kinds.length]();
      p.position.set(x, 0.14, -0.02);
      g.add(p);
    } else if (THEME.style === 'ferrari') {
      const paints = [0xd40000, 0xffd400, 0xd40000, 0x111114, 0xd40000, 0xf2f2f2, 0xd40000];
      const p = i === 3 ? helmet(0xd40000, 0.085) : modelCar(paints[i], 0.24);
      p.position.set(x, 0.14, -0.02);
      p.rotation.y = i === 3 ? Math.PI : (i % 2 ? 0.25 : -0.25);
      g.add(p);
    } else {
      const h = 0.14 + Math.random() * 0.12;
      const cols = [0xff3b45, 0xf5f5f5, 0xffc933, 0x2b2c31, 0x8fa3ff];
      const body2 = new THREE.Mesh(new THREE.CapsuleGeometry(0.035, h - 0.07, 6, 12), new THREE.MeshStandardMaterial({ color: cols[i % cols.length], roughness: 0.45 }));
      body2.position.set(x, 0.14 + h / 2, -0.02);
      body2.castShadow = true;
      g.add(body2);
      const head = new THREE.Mesh(new THREE.SphereGeometry(0.035, 16, 12), new THREE.MeshStandardMaterial({ color: 0xf1d5c2, roughness: 0.6 }));
      head.position.set(x, 0.14 + h + 0.03, -0.02);
      g.add(head);
    }
  }
  return g;
}

/* ────────────────────────────────────────────
   Floating shelf with under-glow — length along Z
──────────────────────────────────────────── */
export function floatingShelf(length = 0.9) {
  const g = new THREE.Group();
  g.add(rbox(0.24, 0.035, length, M.furniture, 0.008));
  const led = ledStrip(length - 0.06, 'z');
  led.position.set(-0.08, -0.024, 0);
  g.add(led);
  if (THEME.mario) {
    const q = questionBlock(0.16);
    q.position.set(0.02, 0.0175, -length / 4);
    g.add(q);
    const m = mushroom(0.07);
    m.position.set(0.02, 0.0175, length / 4);
    g.add(m);
  } else if (THEME.style === 'ferrari') {
    const h = helmet(0xd40000, 0.085);
    h.position.set(0.02, 0.0175, -length / 4);
    h.rotation.y = -Math.PI / 2;
    g.add(h);
    const car = modelCar(0xffd400, 0.22);
    car.position.set(0.0, 0.0175, length / 4);
    car.rotation.y = Math.PI / 2;
    g.add(car);
  } else {
    const helmet = new THREE.Mesh(new THREE.SphereGeometry(0.09, 24, 16, 0, Math.PI * 2, 0, Math.PI * 0.62), new THREE.MeshPhysicalMaterial({ color: 0xe11d2a, roughness: 0.2, clearcoat: 1 }));
    helmet.position.set(0.02, 0.02, -length / 4);
    helmet.castShadow = true;
    g.add(helmet);
    const fig = new THREE.Mesh(new THREE.CapsuleGeometry(0.03, 0.1, 6, 12), new THREE.MeshStandardMaterial({ color: 0xf5f5f5, roughness: 0.5 }));
    fig.position.set(0.02, 0.1, length / 4);
    g.add(fig);
  }
  return g;
}

export function redPipe(points, radius = 0.025) {
  const curve = new THREE.CatmullRomCurve3(points.map((p) => new THREE.Vector3(...p)));
  const tube = new THREE.Mesh(new THREE.TubeGeometry(curve, 64, radius, 12, false), new THREE.MeshStandardMaterial({ color: 0xc41a24, roughness: 0.35, metalness: 0.6 }));
  tube.castShadow = true;
  return tube;
}

export function wallLogoPlane(tex, w = 1.0) {
  return new THREE.Mesh(new THREE.PlaneGeometry(w, w / 2), new THREE.MeshStandardMaterial({
    map: tex, emissive: 0xffffff, emissiveMap: tex, emissiveIntensity: 2.6, transparent: true, roughness: 0.5,
  }));
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

/* ────────────────────────────────────────────
   Mario props
──────────────────────────────────────────── */
let _qTex = null;
let _bTex = null;
let _capTex = null;
function qTex() { return (_qTex ||= TX.questionBlock()); }
function bTex() { return (_bTex ||= TX.brickBlock()); }
function capTex() { return (_capTex ||= TX.mushroomCap()); }

/** Question block; origin at bottom center. */
export function questionBlock(size = 0.16, glow = true) {
  const mat = new THREE.MeshStandardMaterial({ map: qTex(), emissive: 0xffffff, emissiveMap: qTex(), emissiveIntensity: glow ? 0.45 : 0.0, roughness: 0.4 });
  const m = new THREE.Mesh(new RoundedBoxGeometry(size, size, size, 2, size * 0.04), mat);
  m.position.y = size / 2;
  m.castShadow = true;
  return m;
}

/** Brick block; origin at bottom center. */
export function brickBlock(size = 0.16) {
  const m = new THREE.Mesh(new RoundedBoxGeometry(size, size, size, 2, size * 0.03), new THREE.MeshStandardMaterial({ map: bTex(), roughness: 0.7 }));
  m.position.y = size / 2;
  m.castShadow = true;
  return m;
}

/** Super Mushroom; origin at bottom center. capColor overrides red (e.g. 1-UP green). */
export function mushroom(r = 0.07, capColor = null) {
  const g = new THREE.Group();
  const stem = new THREE.Mesh(new THREE.CylinderGeometry(r * 0.62, r * 0.7, r * 0.9, 24), M.marioCream);
  stem.position.y = r * 0.45;
  stem.castShadow = true;
  g.add(stem);
  for (const s of [-1, 1]) {
    const eye = new THREE.Mesh(new THREE.BoxGeometry(r * 0.12, r * 0.3, r * 0.05), M.blackMatte);
    eye.position.set(s * r * 0.22, r * 0.5, -r * 0.66);
    g.add(eye);
  }
  const capMat = capColor
    ? new THREE.MeshPhysicalMaterial({ color: capColor, roughness: 0.3, clearcoat: 0.8 })
    : new THREE.MeshPhysicalMaterial({ map: capTex(), roughness: 0.3, clearcoat: 0.8 });
  const cap = new THREE.Mesh(new THREE.SphereGeometry(r, 32, 20, 0, Math.PI * 2, 0, Math.PI * 0.5), capMat);
  cap.position.y = r * 0.9;
  cap.castShadow = true;
  g.add(cap);
  if (capColor) {
    // spots for coloured caps
    for (const [a, e] of [[0, 0.5], [2.1, 0.7], [4.2, 0.55], [1.0, 1.1], [3.2, 1.15], [5.3, 1.05]]) {
      const spot = new THREE.Mesh(new THREE.SphereGeometry(r * 0.22, 12, 8), new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.4 }));
      spot.position.set(Math.cos(a) * Math.sin(e) * r * 0.98, r * 0.9 + Math.cos(e) * r * 0.98, Math.sin(a) * Math.sin(e) * r * 0.98);
      spot.scale.set(1, 0.4, 1);
      spot.lookAt(0, r * 0.9, 0);
      g.add(spot);
    }
  }
  const rim = new THREE.Mesh(new THREE.CylinderGeometry(r, r, r * 0.12, 32), capMat);
  rim.position.y = r * 0.84;
  g.add(rim);
  return g;
}

/** Super Star; origin at bottom center. */
export function star(size = 0.1) {
  const shape = new THREE.Shape();
  for (let i = 0; i < 10; i++) {
    const rr = i % 2 === 0 ? size : size * 0.45;
    const a = (i / 10) * Math.PI * 2 - Math.PI / 2;
    const x = Math.cos(a) * rr;
    const y = Math.sin(a) * rr;
    if (i === 0) shape.moveTo(x, y);
    else shape.lineTo(x, y);
  }
  shape.closePath();
  const geo = new THREE.ExtrudeGeometry(shape, { depth: size * 0.35, bevelEnabled: true, bevelThickness: size * 0.06, bevelSize: size * 0.06, bevelSegments: 3 });
  geo.center();
  const m = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color: 0xffd23f, emissive: 0xffc400, emissiveIntensity: 0.9, roughness: 0.3 }));
  m.position.y = size;
  m.castShadow = true;
  return m;
}

/** Warp pipe; origin at bottom center. */
export function warpPipe(height = 0.6, r = 0.16) {
  const g = new THREE.Group();
  const body = new THREE.Mesh(new THREE.CylinderGeometry(r, r, height - 0.12, 40), M.marioGreen);
  body.position.y = (height - 0.12) / 2;
  body.castShadow = true;
  g.add(body);
  const rim = new THREE.Mesh(new THREE.CylinderGeometry(r * 1.18, r * 1.18, 0.12, 40), M.marioGreen);
  rim.position.y = height - 0.06;
  rim.castShadow = true;
  g.add(rim);
  const hole = new THREE.Mesh(new THREE.CylinderGeometry(r * 0.92, r * 0.92, 0.02, 40), new THREE.MeshStandardMaterial({ color: 0x0f3d1e, roughness: 0.9 }));
  hole.position.y = height + 0.001;
  g.add(hole);
  return g;
}

/** Colourful modular wall pocket (reference: rounded detachable modules). Front faces +X. */
export function pegModule(color, w = 0.32, h = 0.2, d = 0.14) {
  const g = new THREE.Group();
  const shellMat = new THREE.MeshPhysicalMaterial({ color, roughness: 0.3, clearcoat: 0.7 });
  const outer = rbox(d, h, w, shellMat, 0.035);
  outer.position.x = d / 2;
  g.add(outer);
  const inner = new THREE.Mesh(new RoundedBoxGeometry(d * 0.7, h - 0.05, w - 0.05, 2, 0.02), new THREE.MeshStandardMaterial({ color: 0xfafafa, roughness: 0.8 }));
  inner.position.x = d * 0.7;
  g.add(inner);
  const led = ledStrip(w - 0.08, 'z', M.warmGlow);
  led.position.set(d * 0.95, -h / 2 + 0.03, 0);
  g.add(led);
  return g;
}

/* ────────────────────────────────────────────
   Ferrari props
──────────────────────────────────────────── */

/** Racing helmet; visor faces +Z, origin at bottom centre. */
export function helmet(color = 0xd40000, r = 0.1) {
  const g = new THREE.Group();
  const paint = new THREE.MeshPhysicalMaterial({ color, roughness: 0.15, clearcoat: 1, clearcoatRoughness: 0.05 });
  const shell = new THREE.Mesh(new THREE.SphereGeometry(r, 40, 24, 0, Math.PI * 2, 0, Math.PI * 0.8), paint);
  shell.scale.set(1, 1.05, 1.1);
  shell.castShadow = true;
  g.add(shell);
  const chin = new THREE.Mesh(new THREE.CylinderGeometry(r * 0.72, r * 0.68, r * 0.4, 32), paint);
  chin.position.set(0, -r * 0.55, r * 0.08);
  g.add(chin);
  const visor = new THREE.Mesh(new THREE.SphereGeometry(r * 1.015, 32, 10, Math.PI / 6, (Math.PI * 2) / 3, Math.PI * 0.36, Math.PI * 0.22), M.darkGlass);
  visor.scale.set(1, 1.05, 1.1);
  g.add(visor);
  for (const phi of [Math.PI / 2, (3 * Math.PI) / 2]) {
    const stripe = new THREE.Mesh(new THREE.SphereGeometry(r * 1.01, 8, 16, phi - 0.09, 0.18, 0, Math.PI * 0.36), M.giallo);
    stripe.scale.set(1, 1.05, 1.1);
    g.add(stripe);
  }
  const ring = new THREE.Mesh(new THREE.TorusGeometry(r * 0.75, r * 0.03, 8, 40), M.blackMatte);
  ring.rotation.x = Math.PI / 2;
  ring.position.y = -r * 0.75;
  g.add(ring);
  g.position.y = 0;
  g.children.forEach((c) => { c.position.y += r * 0.85; });
  return g;
}

/** Low-poly GT model car; nose faces +X, origin at bottom centre, length L. */
export function modelCar(color = 0xd40000, L = 0.22) {
  const g = new THREE.Group();
  const paint = new THREE.MeshPhysicalMaterial({ color, roughness: 0.15, metalness: 0.1, clearcoat: 1, clearcoatRoughness: 0.04 });
  const body = rbox(L, L * 0.2, L * 0.42, paint, L * 0.035);
  body.position.set(0, L * 0.21, 0);
  g.add(body);
  const nose = rbox(L * 0.3, L * 0.13, L * 0.4, paint, L * 0.03);
  nose.position.set(L * 0.36, L * 0.19, 0);
  nose.rotation.z = -0.2;
  g.add(nose);
  const cabin = rbox(L * 0.42, L * 0.15, L * 0.34, M.darkGlass, L * 0.04);
  cabin.position.set(-L * 0.05, L * 0.37, 0);
  g.add(cabin);
  const roof = rbox(L * 0.28, L * 0.03, L * 0.3, paint, L * 0.01);
  roof.position.set(-L * 0.08, L * 0.455, 0);
  g.add(roof);
  const wing = rbox(L * 0.07, L * 0.02, L * 0.42, M.carbon, L * 0.005);
  wing.position.set(-L * 0.47, L * 0.36, 0);
  g.add(wing);
  for (const s of [-1, 1]) g.add(at(rbox(L * 0.03, L * 0.08, L * 0.02, M.carbon, 0.001), -L * 0.46, L * 0.32, s * L * 0.15));
  for (const [x, z] of [[L * 0.32, L * 0.21], [L * 0.32, -L * 0.21], [-L * 0.3, L * 0.21], [-L * 0.3, -L * 0.21]]) {
    const tyre = new THREE.Mesh(new THREE.CylinderGeometry(L * 0.1, L * 0.1, L * 0.07, 24), M.rubber);
    tyre.rotation.x = Math.PI / 2;
    tyre.position.set(x, L * 0.1, z);
    tyre.castShadow = true;
    g.add(tyre);
    const rim = new THREE.Mesh(new THREE.CylinderGeometry(L * 0.065, L * 0.065, L * 0.075, 16), M.chrome);
    rim.rotation.x = Math.PI / 2;
    rim.position.set(x, L * 0.1, z);
    g.add(rim);
  }
  for (const s of [-1, 1]) {
    g.add(at(new THREE.Mesh(new THREE.BoxGeometry(L * 0.02, L * 0.035, L * 0.09), new THREE.MeshStandardMaterial({ color: 0xfff2c0, emissive: 0xfff2c0, emissiveIntensity: 1.6 })), L * 0.5, L * 0.22, s * L * 0.14));
    g.add(at(new THREE.Mesh(new THREE.BoxGeometry(L * 0.015, L * 0.035, L * 0.07), M.redGlow), -L * 0.5, L * 0.24, s * L * 0.13));
  }
  return g;
}

/** Racing steering wheel facing +Z (wall-mount stem at -Z). */
export function steeringWheel(r = 0.17) {
  const g = new THREE.Group();
  const rim = new THREE.Mesh(new THREE.TorusGeometry(r, 0.021, 18, 60), M.leather);
  rim.castShadow = true;
  g.add(rim);
  g.add(at(rbox(0.045, 0.05, 0.05, M.rosso, 0.01), 0, r, 0));
  g.add(at(rbox(r * 0.95, 0.035, 0.02, M.carbon, 0.005), -r / 2, 0, 0));
  g.add(at(rbox(r * 0.95, 0.035, 0.02, M.carbon, 0.005), r / 2, 0, 0));
  g.add(at(rbox(0.035, r * 0.95, 0.02, M.carbon, 0.005), 0, -r / 2, 0));
  const hub = new THREE.Mesh(new THREE.CylinderGeometry(0.055, 0.055, 0.03, 32), M.blackGloss);
  hub.rotation.x = Math.PI / 2;
  g.add(hub);
  const badge = new THREE.Mesh(new THREE.CylinderGeometry(0.028, 0.028, 0.006, 32), M.giallo);
  badge.rotation.x = Math.PI / 2;
  badge.position.z = 0.018;
  g.add(badge);
  for (const s of [-1, 1]) {
    g.add(at(new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.012, 0.012, 16), M.redGlow), s * 0.075, 0.035, 0.012).rotateX(Math.PI / 2));
    g.add(at(new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.012, 0.012, 16), M.giallo), s * 0.075, -0.035, 0.012).rotateX(Math.PI / 2));
  }
  const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 0.09, 16), M.gunmetal);
  stem.rotation.x = Math.PI / 2;
  stem.position.z = -0.05;
  g.add(stem);
  return g;
}

/** Wheel-rim coffee table with glass top; origin at floor. */
export function rimTable(R = 0.32, h = 0.5) {
  const g = new THREE.Group();
  const tyre = new THREE.Mesh(new THREE.TorusGeometry(0.2, 0.065, 20, 56), M.rubber);
  tyre.rotation.x = Math.PI / 2;
  tyre.position.y = 0.075;
  tyre.castShadow = true;
  g.add(tyre);
  const rim = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.2, 0.09, 40), M.gunmetal);
  rim.position.y = 0.075;
  g.add(rim);
  for (let i = 0; i < 5; i++) {
    const a = (i / 5) * Math.PI * 2;
    const spoke = rbox(0.03, 0.1, 0.17, M.chrome, 0.006);
    spoke.position.set(Math.cos(a) * 0.1, 0.078, Math.sin(a) * 0.1);
    spoke.rotation.y = -a + Math.PI / 2;
    g.add(spoke);
  }
  const hub = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.11, 32), M.giallo);
  hub.position.y = 0.08;
  g.add(hub);
  const col = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, h - 0.17, 24), M.chrome);
  col.position.y = 0.12 + (h - 0.17) / 2;
  g.add(col);
  const under = new THREE.Mesh(new THREE.CylinderGeometry(0.13, 0.13, 0.02, 32), M.blackGloss);
  under.position.y = h - 0.03;
  g.add(under);
  const ring = new THREE.Mesh(new THREE.TorusGeometry(R - 0.04, 0.005, 8, 72), M.redGlow);
  ring.rotation.x = Math.PI / 2;
  ring.position.y = h - 0.018;
  g.add(ring);
  const top = new THREE.Mesh(new THREE.CylinderGeometry(R, R, 0.012, 72), M.glass);
  top.position.y = h - 0.006;
  g.add(top);
  return g;
}

/** Simple pedestal round table; origin at floor. */
export function roundTable(R = 0.3, h = 0.5) {
  const g = new THREE.Group();
  g.add(at(new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.24, 0.02, 48), M.gunmetal), 0, 0.01, 0));
  g.add(at(new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, h - 0.05, 24), M.chrome), 0, h / 2, 0));
  const top = new THREE.Mesh(new THREE.CylinderGeometry(R, R, 0.03, 72), M.furniture);
  top.position.y = h - 0.015;
  top.castShadow = true;
  g.add(top);
  return g;
}

/**
 * Throw pillow; origin at bottom centre. `yaw` turns the pillow (width along local X),
 * `lean` tips its top toward local +Z (negative → toward -Z).
 */
export function pillow(w, h, mat, { yaw = 0, lean = 0 } = {}) {
  const g = new THREE.Group();
  const p = rbox(w, h, w * 0.22, mat, Math.min(w, h) * 0.3, 4);
  p.position.y = h / 2;
  const inner = new THREE.Group();
  inner.add(p);
  inner.rotation.x = lean;
  g.add(inner);
  g.rotation.y = yaw;
  return g;
}

/** Backlit black panel facing +Z with an LED halo behind. */
export function litPanel(w, h, d = 0.04) {
  const g = new THREE.Group();
  g.add(rbox(w, h, d, M.blackGloss, 0.01));
  const top = ledStrip(w, 'x'); top.position.set(0, h / 2 + 0.01, -d / 2); g.add(top);
  const bot = ledStrip(w, 'x'); bot.position.set(0, -h / 2 - 0.01, -d / 2); g.add(bot);
  const l = ledStrip(h, 'y'); l.position.set(-w / 2 - 0.01, 0, -d / 2); g.add(l);
  const r = ledStrip(h, 'y'); r.position.set(w / 2 + 0.01, 0, -d / 2); g.add(r);
  return g;
}

/* ────────────────────────────────────────────
   Architecture: bay window, pivot door, ceiling fixtures
──────────────────────────────────────────── */

/**
 * 飘窗 bay window. Local: wall plane at z=0, room at +Z, outside at -Z, floor y=0.
 * Includes the protruding bay (side walls, ceiling, lower wall), stone sill, glazing
 * with black frame + mullion, seat cushion, curtains and the outside backdrop.
 */
export function bayWindow({ width = 2.2, height = 1.85, sillY = 0.45, depth = 0.55, viewTex, seat = true, wallColor = 0xe9e6e0 }) {
  const g = new THREE.Group();
  const F = THEME.style === 'ferrari';
  const wallMat = new THREE.MeshStandardMaterial({ color: wallColor, roughness: 0.9 });
  const sideW = 0.12;
  for (const s of [-1, 1]) {
    g.add(at(new THREE.Mesh(new THREE.BoxGeometry(sideW, height + 0.24, depth), wallMat), s * (width / 2 + sideW / 2), sillY + height / 2 + 0.06, -depth / 2));
  }
  g.add(at(new THREE.Mesh(new THREE.BoxGeometry(width + sideW * 2, 0.12, depth), wallMat), 0, sillY + height + 0.18, -depth / 2));
  g.add(at(new THREE.Mesh(new THREE.BoxGeometry(width + sideW * 2, sillY, depth), wallMat), 0, sillY / 2, -depth / 2));
  // reveal (inner lining) of the opening so the wall thickness reads
  const lining = new THREE.MeshStandardMaterial({ color: wallColor, roughness: 0.9 });
  g.add(at(new THREE.Mesh(new THREE.BoxGeometry(width, 0.04, depth), lining), 0, sillY + height + 0.1, -depth / 2));

  const sill = rbox(width + 0.08, 0.05, depth + 0.1, M.stone, 0.006);
  sill.position.set(0, sillY + 0.025, -depth / 2 + 0.05);
  g.add(sill);

  const gz = -depth + 0.03;
  const frameMat = M.blackMatte;
  const glass = new THREE.Mesh(new THREE.PlaneGeometry(width, height), M.glass);
  glass.position.set(0, sillY + height / 2, gz);
  g.add(glass);
  g.add(at(rbox(width + 0.1, 0.06, 0.06, frameMat, 0.005), 0, sillY + height + 0.03, gz));
  g.add(at(rbox(width + 0.1, 0.06, 0.06, frameMat, 0.005), 0, sillY + 0.03 + 0.05, gz));
  for (const s of [-1, 1]) g.add(at(rbox(0.06, height, 0.06, frameMat, 0.005), s * (width / 2 + 0.02), sillY + height / 2, gz));
  g.add(at(rbox(0.05, height, 0.05, frameMat, 0.005), width * 0.16, sillY + height / 2, gz));
  g.add(at(rbox(width, 0.045, 0.05, frameMat, 0.005), 0, sillY + height * 0.62, gz));

  const view = new THREE.Mesh(new THREE.PlaneGeometry(width * 2.8, height * 2.4), new THREE.MeshBasicMaterial({ map: viewTex }));
  view.position.set(0, sillY + height / 2 + 0.35, -depth - 1.7);
  g.add(view);

  if (seat) {
    const c = rbox(width - 0.1, 0.07, depth - 0.04, M.cushion, 0.03);
    c.position.set(0, sillY + 0.05 + 0.035, -depth / 2 + 0.01);
    c.castShadow = true;
    g.add(c);
    if (F) g.add(at(rbox(width - 0.14, 0.012, 0.012, M.rosso, 0.004), 0, sillY + 0.115, 0.0));
    const pillowMats = F ? [M.rossoSoft, M.gialloSoft, M.leather] : THEME.mario ? [M.marioRed, M.marioYellow, M.cushion] : [M.accent, M.cushion, M.cushion];
    [[-width / 2 + 0.3, 0, 0.15], [-width / 2 + 0.62, 1, -0.1], [width / 2 - 0.35, 2, 0.1], [width / 2 - 0.68, 0, -0.15]].forEach(([x, k, yaw], i) => {
      const p = pillow(0.38, 0.36, pillowMats[k], { yaw, lean: -(0.28 + (i % 2) * 0.08) });
      p.position.set(x, sillY + 0.12, -depth + 0.13 + (i % 2) * 0.1);
      g.add(p);
    });
  }
  // curtains + rod inside the room
  const rod = new THREE.Mesh(new THREE.CylinderGeometry(0.014, 0.014, width + 0.7, 16), M.gunmetal);
  rod.rotation.z = Math.PI / 2;
  rod.position.set(0, sillY + height + 0.3, 0.14);
  g.add(rod);
  for (const s of [-1, 1]) {
    const cur = rbox(0.36, height + 0.5, 0.14, M.fabric, 0.05);
    cur.position.set(s * (width / 2 + 0.05), sillY + (height + 0.5) / 2 + 0.03, 0.12);
    cur.castShadow = true;
    g.add(cur);
  }
  // accent LED under the sill nose
  const led = ledStrip(width - 0.1, 'x');
  led.position.set(0, sillY - 0.02, 0.03);
  g.add(led);
  return g;
}

/**
 * 夹丝玻璃偏轴门 — offset-pivot wired-glass door. Local: leaf in XY plane at z=0,
 * room at -Z, outside at +Z, origin at floor / opening centre. `open` in radians swings outward.
 */
export function pivotDoor({ width = 0.95, height = 2.2, open = 0.6, wireTex }) {
  const g = new THREE.Group();
  const frameMat = M.blackMatte;
  g.add(at(rbox(0.06, height, 0.12, frameMat, 0.005), -width / 2 - 0.03, height / 2, 0));
  g.add(at(rbox(0.06, height, 0.12, frameMat, 0.005), width / 2 + 0.03, height / 2, 0));
  g.add(at(rbox(width + 0.12, 0.06, 0.12, frameMat, 0.005), 0, height + 0.03, 0));
  g.add(at(rbox(width, 0.015, 0.12, M.gunmetal, 0.003), 0, 0.0075, 0));

  const pivotX = -width / 2 + 0.16;
  const leaf = new THREE.Group();
  leaf.position.set(pivotX, 0, 0);
  const lw = width - 0.02;
  const cx = -pivotX;
  const glassMat = new THREE.MeshPhysicalMaterial({ map: wireTex, transparent: true, roughness: 0.08, metalness: 0, clearcoat: 1, side: THREE.DoubleSide, depthWrite: false });
  const glass = new THREE.Mesh(new THREE.PlaneGeometry(lw - 0.08, height - 0.2), glassMat);
  glass.position.set(cx, height / 2 + 0.02, 0);
  leaf.add(glass);
  leaf.add(at(rbox(0.05, height - 0.03, 0.045, frameMat, 0.004), cx - lw / 2 + 0.025, height / 2 - 0.015, 0));
  leaf.add(at(rbox(0.05, height - 0.03, 0.045, frameMat, 0.004), cx + lw / 2 - 0.025, height / 2 - 0.015, 0));
  leaf.add(at(rbox(lw, 0.05, 0.045, frameMat, 0.004), cx, height - 0.055, 0));
  leaf.add(at(rbox(lw, 0.14, 0.045, frameMat, 0.004), cx, 0.07, 0));
  for (const zz of [-0.05, 0.05]) {
    leaf.add(at(new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.012, 0.7, 14), M.chrome), cx + lw / 2 - 0.13, 1.05, zz));
  }
  leaf.rotation.y = -open;
  g.add(leaf);
  return g;
}

/** Recessed ceiling light box (emissive panel facing down, black trim); origin at ceiling underside. */
export function lightBox(w, d, intensity = 2.4) {
  const g = new THREE.Group();
  const panel = new THREE.Mesh(new THREE.PlaneGeometry(w, d), new THREE.MeshStandardMaterial({ color: 0xfff6e8, emissive: 0xfff0dc, emissiveIntensity: intensity, roughness: 0.8 }));
  panel.rotation.x = Math.PI / 2;
  panel.position.y = 0.01;
  g.add(panel);
  const t = 0.035;
  [[0, d / 2 + t / 2, w + 2 * t, t], [0, -d / 2 - t / 2, w + 2 * t, t], [w / 2 + t / 2, 0, t, d], [-w / 2 - t / 2, 0, t, d]].forEach(([x, z, lx, lz]) => {
    g.add(at(new THREE.Mesh(new THREE.BoxGeometry(lx, 0.008, lz), M.blackMatte), x, -0.001, z));
  });
  return g;
}

/** Linear air-conditioning grille facing down; origin at ceiling underside. */
export function acGrille(len = 1.2) {
  const g = new THREE.Group();
  const body = new THREE.Mesh(new THREE.BoxGeometry(len, 0.006, 0.15), new THREE.MeshStandardMaterial({ color: 0xf2f2f4, roughness: 0.7 }));
  body.position.y = -0.001;
  g.add(body);
  for (let i = 0; i < 6; i++) {
    g.add(at(new THREE.Mesh(new THREE.BoxGeometry(len - 0.08, 0.005, 0.012), M.blackMatte), 0, -0.006, -0.05 + i * 0.02));
  }
  return g;
}

export { TX };
