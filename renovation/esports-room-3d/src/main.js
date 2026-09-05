import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { PointerLockControls } from 'three/examples/jsm/controls/PointerLockControls.js';
import { RectAreaLightUniformsLib } from 'three/examples/jsm/lights/RectAreaLightUniformsLib.js';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js';
import * as F from './furniture.js';
import * as TX from './textures.js';

/**
 * Floor plan (metres) — traced from the owner's drawing. North is -Z.
 *
 *   -X (west) wall  : two 升降电竞桌 side by side, one PC + monitor each, sitters face -X
 *   -Z (north) wall : 2.2 m 飘窗 bay window (the backdrop), structural column in the NE corner
 *   +X (east) wall  : 卡座 bench continuing from under the window, wrapping the column (L shape)
 *   +Z (south) wall : 展示架 display cabinet (left) + 夹丝玻璃偏轴门 pivot door (right, SE corner)
 *   centre-right    : round table for the booth
 */
const ROOM_W = 3.4;
const ROOM_D = 4.0;
const ROOM_H = 2.8;
const SOFFIT_Y = 2.5;
const SOFFIT_W = 0.5;
const COLUMN = 0.65;
const WIN = { x: -0.1, width: 2.2, sillY: 0.45, height: 1.85, depth: 0.55 };
const DOOR = { x: 0.975, width: 0.95, height: 2.2 };
const DESK_X = -ROOM_W / 2 + 0.39;
const DESK_Z = [-0.8, 0.75];
const BOOTH_DEPTH = 0.45;
const BOOTH_EAST = { from: -ROOM_D / 2 + COLUMN, to: 0.3 };
const BOOTH_NORTH = { from: 0.0, to: ROOM_W / 2 - COLUMN };
const TABLE = [0.72, -0.6];

const app = document.getElementById('app');
const hint = document.getElementById('hint');

function showFatal(title, detail) {
  const el = document.createElement('div');
  el.style.cssText = 'position:fixed;inset:0;display:flex;align-items:center;justify-content:center;z-index:50;padding:24px;text-align:center;color:#f2f2f4;font-family:sans-serif;background:rgba(5,5,6,.92)';
  el.innerHTML = `<div><div style="font-size:20px;font-weight:650;margin-bottom:10px">${title}</div><div style="color:#9a9aa3;font-size:14px;line-height:1.6;max-width:520px">${detail}</div></div>`;
  document.body.appendChild(el);
}
function webglAvailable() {
  try {
    const c = document.createElement('canvas');
    return !!(c.getContext('webgl2') || c.getContext('webgl'));
  } catch { return false; }
}
if (!webglAvailable()) {
  showFatal('浏览器未开启 WebGL', '3D 需要 WebGL。请在 Chrome 打开 chrome://settings/system 勾选「使用图形加速」，或在 chrome://flags 搜索 WebGL 并启用，然后重启浏览器。');
  throw new Error('WebGL unavailable');
}
window.addEventListener('error', (e) => showFatal('3D 场景加载出错', String(e.message || e.error || '未知错误')));

RectAreaLightUniformsLib.init();

/* ───────────── renderer / scene / camera ───────────── */
const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
app.appendChild(renderer.domElement);

const scene = new THREE.Scene();
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;

const camera = new THREE.PerspectiveCamera(52, window.innerWidth / window.innerHeight, 0.05, 60);

const orbit = new OrbitControls(camera, renderer.domElement);
orbit.enableDamping = true;
orbit.dampingFactor = 0.07;
orbit.minDistance = 0.6;
orbit.maxDistance = 12;
orbit.maxPolarAngle = Math.PI * 0.495;

const walk = new PointerLockControls(camera, renderer.domElement);
let mode = 'orbit';
const walkKeys = { forward: false, back: false, left: false, right: false };
const walkVelocity = new THREE.Vector3();
const clock = new THREE.Clock();

function setMode(next) {
  mode = next;
  document.getElementById('btn-orbit').classList.toggle('active', next === 'orbit');
  document.getElementById('btn-walk').classList.toggle('active', next === 'walk');
  if (next === 'orbit') {
    walk.unlock();
    orbit.enabled = true;
    hint.innerHTML = '<b>拖拽</b> 旋转 · <b>滚轮</b> 缩放 · <b>右键拖拽</b> 平移';
  } else {
    orbit.enabled = false;
    hint.innerHTML = '点击画面锁定鼠标 · <b>W A S D</b> 走动 · <b>Esc</b> 退出';
    walk.lock();
  }
}

const CAMS = {
  entrance: { pos: [0.95, 1.5, 1.8], target: [-0.65, 1.0, -1.1] },
  desks: { pos: [0.75, 1.35, 0.15], target: [-1.5, 1.05, -0.1] },
  window: { pos: [0.05, 1.45, 1.05], target: [0.4, 0.9, -2.3] },
  overview: { pos: [3.4, 4.9, 3.9], target: [0, 0.3, -0.1] },
};
function flyTo({ pos, target }) {
  setMode('orbit');
  camera.position.set(...pos);
  orbit.target.set(...target);
  orbit.update();
}
document.getElementById('btn-orbit').onclick = () => setMode('orbit');
document.getElementById('btn-walk').onclick = () => setMode('walk');
document.querySelectorAll('[data-cam]').forEach((b) => { b.onclick = () => flyTo(CAMS[b.dataset.cam]); });
window.addEventListener('debug-cam', (e) => flyTo(e.detail));

const keyMap = { KeyW: 'forward', KeyS: 'back', KeyA: 'left', KeyD: 'right' };
window.addEventListener('keydown', (e) => { if (keyMap[e.code]) walkKeys[keyMap[e.code]] = true; });
window.addEventListener('keyup', (e) => { if (keyMap[e.code]) walkKeys[keyMap[e.code]] = false; });

/* ───────────── helpers ───────────── */
function plane(w, h, material, x, y, z, rotY = 0, rotX = 0) {
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), material);
  m.position.set(x, y, z);
  m.rotation.set(rotX, rotY, 0);
  m.receiveShadow = true;
  return m;
}
function box(w, h, d, material, x, y, z) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), material);
  m.position.set(x, y, z);
  m.castShadow = true;
  m.receiveShadow = true;
  return m;
}
function disposeGroup(root) {
  root.traverse((o) => {
    if (o.geometry) o.geometry.dispose();
    if (o.material) {
      const mats = Array.isArray(o.material) ? o.material : [o.material];
      mats.forEach((m) => {
        for (const k of ['map', 'emissiveMap', 'roughnessMap', 'bumpMap']) if (m[k]) m[k].dispose();
        m.dispose();
      });
    }
  });
}

/* ───────────── room shell ───────────── */
function buildShell(T, tex) {
  const g = new THREE.Group();
  const ferrari = T.style === 'ferrari';
  const wallMat = ferrari
    ? new THREE.MeshStandardMaterial({ color: T.wall, roughness: 0.92 })
    : new THREE.MeshStandardMaterial({ map: tex.metal.map, color: T.wall, metalness: 0.75, roughness: 0.35 });
  const wallEntrance = T.mario || ferrari ? wallMat : new THREE.MeshStandardMaterial({ color: 0x1a1b20, metalness: 0.35, roughness: 0.6 });
  const floorMat = new THREE.MeshPhysicalMaterial({
    map: tex.floor.map, roughnessMap: tex.floor.roughnessMap, roughness: 0.35, metalness: 0.05, clearcoat: 0.9, clearcoatRoughness: 0.08,
  });
  const ceilMat = new THREE.MeshStandardMaterial({ color: 0xf4f4f6, roughness: 0.9 });
  const soffitMat = new THREE.MeshStandardMaterial({ color: ferrari ? 0xf1f0ec : 0xf4f4f6, roughness: 0.9 });

  const W = ROOM_W, D = ROOM_D, H = ROOM_H;
  g.add(plane(W, D, floorMat, 0, 0, 0, 0, -Math.PI / 2));
  // Single-sided planes facing inward: from outside they are culled (dollhouse view)
  g.add(plane(W - 2 * SOFFIT_W, D - 2 * SOFFIT_W, ceilMat, 0, H, 0, 0, Math.PI / 2));
  // perimeter soffit (dropped ceiling band) — undersides + inner vertical faces
  g.add(plane(W, SOFFIT_W, soffitMat, 0, SOFFIT_Y, -D / 2 + SOFFIT_W / 2, 0, Math.PI / 2));
  g.add(plane(W, SOFFIT_W, soffitMat, 0, SOFFIT_Y, D / 2 - SOFFIT_W / 2, 0, Math.PI / 2));
  g.add(plane(SOFFIT_W, D - 2 * SOFFIT_W, soffitMat, -W / 2 + SOFFIT_W / 2, SOFFIT_Y, 0, 0, Math.PI / 2));
  g.add(plane(SOFFIT_W, D - 2 * SOFFIT_W, soffitMat, W / 2 - SOFFIT_W / 2, SOFFIT_Y, 0, 0, Math.PI / 2));
  const sh = H - SOFFIT_Y;
  const sy = SOFFIT_Y + sh / 2;
  g.add(plane(W - 2 * SOFFIT_W, sh, soffitMat, 0, sy, -D / 2 + SOFFIT_W, 0));
  g.add(plane(W - 2 * SOFFIT_W, sh, soffitMat, 0, sy, D / 2 - SOFFIT_W, Math.PI));
  g.add(plane(D - 2 * SOFFIT_W, sh, soffitMat, -W / 2 + SOFFIT_W, sy, 0, Math.PI / 2));
  g.add(plane(D - 2 * SOFFIT_W, sh, soffitMat, W / 2 - SOFFIT_W, sy, 0, -Math.PI / 2));

  // walls
  g.add(plane(D, H, wallMat, -W / 2, H / 2, 0, Math.PI / 2));
  g.add(plane(D, H, wallMat, W / 2, H / 2, 0, -Math.PI / 2));
  // north wall with the bay-window opening
  const wl = WIN.x - WIN.width / 2;
  const wr = WIN.x + WIN.width / 2;
  g.add(plane(wl + W / 2, H, wallMat, (-W / 2 + wl) / 2, H / 2, -D / 2, 0));
  g.add(plane(W / 2 - wr, H, wallMat, (wr + W / 2) / 2, H / 2, -D / 2, 0));
  g.add(plane(WIN.width, WIN.sillY, wallMat, WIN.x, WIN.sillY / 2, -D / 2, 0));
  const aboveWin = H - (WIN.sillY + WIN.height);
  g.add(plane(WIN.width, aboveWin, wallMat, WIN.x, H - aboveWin / 2, -D / 2, 0));
  // south wall with the door opening
  const dl = DOOR.x - DOOR.width / 2;
  const dr = DOOR.x + DOOR.width / 2;
  g.add(plane(dl + W / 2, H, wallEntrance, (-W / 2 + dl) / 2, H / 2, D / 2, Math.PI));
  g.add(plane(W / 2 - dr, H, wallEntrance, (dr + W / 2) / 2, H / 2, D / 2, Math.PI));
  g.add(plane(DOOR.width, H - DOOR.height, wallEntrance, DOOR.x, (H + DOOR.height) / 2, D / 2, Math.PI));

  // structural column in the NE corner (the booth wraps around it)
  g.add(box(COLUMN, H, COLUMN, wallMat, W / 2 - COLUMN / 2, H / 2, -D / 2 + COLUMN / 2));
  const colLed = F.ledStrip(H - 0.5, 'y');
  colLed.position.set(W / 2 - COLUMN - 0.01, H / 2 - 0.1, -D / 2 + COLUMN + 0.01);
  g.add(colLed);

  // skirting
  const skirtMat = ferrari ? F.M.blackGloss : T.mario ? new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.6 }) : F.M.blackMatte;
  g.add(box(0.012, 0.08, D, skirtMat, W / 2 - 0.006, 0.04, 0));
  g.add(box(0.012, 0.08, D, skirtMat, -W / 2 + 0.006, 0.04, 0));
  g.add(box(W, 0.08, 0.012, skirtMat, 0, 0.04, -D / 2 + 0.006));
  g.add(box(dl + W / 2, 0.08, 0.012, skirtMat, (-W / 2 + dl) / 2, 0.04, D / 2 - 0.006));

  // ceiling accent line along the soffit inner edge + warm cove glow
  const inset = SOFFIT_W + 0.02;
  const accentMat = T.mario ? F.M.warmGlow : F.M.led;
  [[0, -D / 2 + inset, 'x', W - 2 * inset], [0, D / 2 - inset, 'x', W - 2 * inset], [-W / 2 + inset, 0, 'z', D - 2 * inset], [W / 2 - inset, 0, 'z', D - 2 * inset]].forEach(([x, z, axis, len]) => {
    const line = F.ledStrip(len, axis, accentMat);
    line.position.set(x, H - 0.03, z);
    g.add(line);
  });

  // recessed light box in the soffit above the desks (reference: SketchUp ceiling trough)
  const lb = F.lightBox(3.0, 0.3, T.mario ? 1.6 : 2.2);
  lb.position.set(-W / 2 + SOFFIT_W / 2, SOFFIT_Y, 0);
  g.add(lb);
  // linear AC grille in the south soffit
  const ac = F.acGrille(1.3);
  ac.position.set(-0.55, SOFFIT_Y, D / 2 - SOFFIT_W / 2);
  g.add(ac);

  // 飘窗 bay window in the north wall
  const win = F.bayWindow({ ...WIN, viewTex: tex.view, wallColor: T.wall });
  win.position.set(WIN.x, 0, -D / 2);
  g.add(win);

  // 夹丝玻璃偏轴门 at the SE corner, swinging out toward the kitchen
  const door = F.pivotDoor({ width: DOOR.width, height: DOOR.height, open: 0.65, wireTex: tex.wire });
  door.position.set(DOOR.x, 0, D / 2);
  g.add(door);
  // a hint of the corridor floor outside the door so the glass door has something behind it
  const outsideFloor = plane(2.4, 1.6, new THREE.MeshStandardMaterial({ color: 0x1b1b1f, roughness: 0.7 }), DOOR.x, -0.002, D / 2 + 0.8, 0, -Math.PI / 2);
  g.add(outsideFloor);

  // rug in the middle
  if (ferrari) {
    const rug = new THREE.Mesh(new THREE.PlaneGeometry(1.5, 1.9), new THREE.MeshStandardMaterial({ map: tex.rug, roughness: 1 }));
    rug.rotation.x = -Math.PI / 2;
    rug.position.set(0.3, 0.008, -0.45);
    rug.receiveShadow = true;
    g.add(rug);
  } else if (T.mario) {
    // giant coin rug
    const rug = new THREE.Mesh(new THREE.CircleGeometry(0.85, 72), new THREE.MeshStandardMaterial({ map: tex.rug, transparent: true, roughness: 1 }));
    rug.rotation.x = -Math.PI / 2;
    rug.position.set(0.3, 0.008, -0.45);
    rug.receiveShadow = true;
    g.add(rug);
  } else {
    const rug = new THREE.Mesh(new THREE.CylinderGeometry(0.8, 0.8, 0.02, 64), new THREE.MeshStandardMaterial({ map: tex.rug, roughness: 1 }));
    rug.position.set(0.3, 0.01, -0.45);
    rug.receiveShadow = true;
    g.add(rug);
  }
  return g;
}

/* ───────────── furniture placement ───────────── */
function buildFurniture(T, tex) {
  const g = new THREE.Group();
  const W = ROOM_W, D = ROOM_D;
  const style = T.style;

  // ── two 升降电竞桌 along the west wall, each with its own PC ──
  DESK_Z.forEach((z, i) => {
    const desk = F.gamingDesk({ width: 1.5, depth: 0.7, screenTex: tex.screen, keyboardTex: tex.keys, withHeadset: i === 1, withTower: true });
    desk.rotation.y = Math.PI / 2;
    desk.position.set(DESK_X, 0, z);
    g.add(desk);
    const chair = F.gamingChair();
    chair.rotation.y = Math.PI / 2;
    chair.position.set(DESK_X + 0.64, 0, z + (i === 0 ? 0.04 : -0.04));
    g.add(chair);
  });

  // ── feature wall behind the desks ──
  if (style === 'ferrari') {
    // single-sided so the dollhouse view from the west is not blocked
    const panel = plane(3.3, SOFFIT_Y - 0.1, F.M.carbon, -W / 2 + 0.04, (SOFFIT_Y - 0.1) / 2 + 0.08, 0, Math.PI / 2);
    g.add(panel);
    const panelFrame = new THREE.Mesh(new THREE.BoxGeometry(0.04, 0.03, 3.3), F.M.blackGloss);
    panelFrame.position.set(-W / 2 + 0.02, SOFFIT_Y - 0.02 - 0.015, 0);
    g.add(panelFrame);
    for (const y of [1.98, 1.9]) {
      const stripe = new THREE.Mesh(new THREE.BoxGeometry(0.012, y === 1.98 ? 0.05 : 0.018, 3.2), F.M.rosso);
      stripe.position.set(-W / 2 + 0.046, y, 0);
      g.add(stripe);
    }
    const emblem = new THREE.Mesh(new THREE.PlaneGeometry(0.42, 0.525), new THREE.MeshStandardMaterial({ map: tex.emblem, transparent: true, roughness: 0.5, emissive: 0xffffff, emissiveMap: tex.emblem, emissiveIntensity: 0.35 }));
    emblem.position.set(-W / 2 + 0.055, 2.22, 0);
    emblem.rotation.y = Math.PI / 2;
    g.add(emblem);
    const word = F.wallLogoPlane(tex.wordmark, 1.7);
    word.position.set(-W / 2 + 0.05, 1.62, 0);
    word.rotation.y = Math.PI / 2;
    g.add(word);
    for (const z of [-1.66, 1.66]) {
      const v = F.ledStrip(SOFFIT_Y - 0.2, 'y');
      v.position.set(-W / 2 + 0.045, (SOFFIT_Y - 0.2) / 2 + 0.1, z);
      g.add(v);
    }
  } else {
    const peg = new THREE.Mesh(new THREE.PlaneGeometry(3.3, 1.5), new THREE.MeshStandardMaterial({
      map: tex.peg.map, bumpMap: tex.peg.bumpMap, bumpScale: 0.01, metalness: 0.5, roughness: 0.5,
    }));
    peg.position.set(-W / 2 + 0.01, 1.6, 0);
    peg.rotation.y = Math.PI / 2;
    peg.receiveShadow = true;
    g.add(peg);
    const pegFrame = F.ledStrip(3.3, 'z');
    pegFrame.position.set(-W / 2 + 0.02, 2.36, 0);
    g.add(pegFrame);
    if (style === 'mario') {
      // P1 / P2 signs above each desk
      DESK_Z.forEach((z, i) => {
        const sign = F.wallLogoPlane(tex.signs[i], 0.8);
        sign.position.set(-W / 2 + 0.03, 1.95, z);
        sign.rotation.y = Math.PI / 2;
        g.add(sign);
      });
      // brick + ? block row between the two setups, star on top
      [-0.36, -0.18, 0.0, 0.18, 0.36].forEach((z, i) => {
        const b = i % 2 ? F.questionBlock(0.17) : F.brickBlock(0.17);
        b.position.set(-W / 2 + 0.1, 1.62, z);
        g.add(b);
      });
      const st = F.star(0.09);
      st.position.set(-W / 2 + 0.12, 1.82, 0);
      st.rotation.y = Math.PI / 2;
      g.add(st);
      // colourful modules on the pegboard
      [[0xe4291b, 1.25, -1.45, 0.3, 0.2], [0x2f7be5, 2.2, -0.9, 0.24, 0.16], [0xf7b515, 2.2, 0.85, 0.24, 0.16], [0x2fa84f, 1.25, 1.45, 0.3, 0.2]].forEach(([c, y, z, w, h]) => {
        const m = F.pegModule(c, w, h);
        m.position.set(-W / 2 + 0.015, y, z);
        g.add(m);
      });
      // warp pipe with a piranha plant in the NW corner beside the window
      const pipe = F.warpPipe(0.55, 0.13);
      pipe.position.set(-W / 2 + 0.15, 0, -1.72);
      g.add(pipe);
      const plant = F.piranhaPlant(0.09);
      plant.position.set(-W / 2 + 0.15, 0.55, -1.72);
      g.add(plant);
    } else {
      const logo = F.wallLogoPlane(tex.logo, 0.95);
      logo.position.set(-W / 2 + 0.03, 1.95, 0);
      logo.rotation.y = Math.PI / 2;
      g.add(logo);
      g.add(F.redPipe([
        [-W / 2 + 0.06, 1.1, -1.6], [-W / 2 + 0.06, 1.1, -0.75], [-W / 2 + 0.06, 1.5, -0.6],
        [-W / 2 + 0.06, 1.5, 0.6], [-W / 2 + 0.06, 1.1, 0.75], [-W / 2 + 0.06, 1.1, 1.6],
      ]));
    }
  }

  // ── L-shaped 卡座: bench under the bay window + bench along the east wall, wrapping the column ──
  const eastLen = BOOTH_EAST.to - BOOTH_EAST.from;
  const east = F.boothUnit({ length: eastLen, depth: BOOTH_DEPTH, withBack: true });
  east.position.set(W / 2 - BOOTH_DEPTH / 2, 0, (BOOTH_EAST.from + BOOTH_EAST.to) / 2);
  g.add(east);
  const northLen = BOOTH_NORTH.to - BOOTH_NORTH.from;
  const north = F.boothUnit({ length: northLen, depth: BOOTH_DEPTH, withBack: false, bolsters: false });
  north.rotation.y = Math.PI / 2;
  north.position.set((BOOTH_NORTH.from + BOOTH_NORTH.to) / 2, 0, -D / 2 + BOOTH_DEPTH / 2);
  g.add(north);
  // corner filler where the two arms meet
  g.add(box(BOOTH_DEPTH, 0.46, BOOTH_DEPTH, T.mario ? F.M.blackGloss : F.M.cabinet, W / 2 - COLUMN - BOOTH_DEPTH / 2, 0.23, -D / 2 + COLUMN + BOOTH_DEPTH / 2));
  const cornerCushion = new THREE.Mesh(new THREE.BoxGeometry(BOOTH_DEPTH - 0.02, 0.11, BOOTH_DEPTH - 0.02), F.M.cushion);
  cornerCushion.position.set(W / 2 - COLUMN - BOOTH_DEPTH / 2, 0.515, -D / 2 + COLUMN + BOOTH_DEPTH / 2);
  cornerCushion.castShadow = true;
  g.add(cornerCushion);
  // pillows on the east bench
  const pMats = style === 'ferrari' ? [F.M.rossoSoft, F.M.gialloSoft] : style === 'mario' ? [F.M.marioRed, F.M.marioYellow] : [F.M.accent, F.M.cushion];
  [[-1.0, 0, 0.1], [-0.15, 1, -0.12], [0.2, 0, 0.15]].forEach(([dz, k, dyaw], i) => {
    const p = F.pillow(0.38, 0.36, pMats[k], { yaw: -Math.PI / 2 + dyaw, lean: 0.3 + (i % 2) * 0.08 });
    p.position.set(W / 2 - 0.17 - (i % 2) * 0.03, 0.57, (BOOTH_EAST.from + BOOTH_EAST.to) / 2 + dz);
    g.add(p);
  });

  // table for the booth
  const table = style === 'ferrari' ? F.rimTable(0.32, 0.5) : style === 'mario' ? F.mushroomTable(0.34, 0.5) : F.roundTable(0.3, 0.5);
  table.position.set(TABLE[0], 0, TABLE[1]);
  g.add(table);

  // ── shelves above the east bench ──
  const shelfZ = (BOOTH_EAST.from + BOOTH_EAST.to) / 2;
  [1.35, 1.75].forEach((y, row) => {
    const shelf = new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.028, 1.4), F.M.furniture);
    shelf.position.set(W / 2 - 0.1, y, shelfZ);
    shelf.castShadow = true;
    g.add(shelf);
    const led = F.ledStrip(1.3, 'z');
    led.position.set(W / 2 - 0.16, y - 0.02, shelfZ);
    g.add(led);
    [-0.45, 0, 0.45].forEach((dz, k) => {
      let item;
      if (style === 'ferrari') {
        const paints = [0xd40000, 0xffd400, 0x111114, 0xf2f2f2, 0xd40000, 0xd40000];
        item = (row === 1 && k === 1) ? F.helmet(0xffd400, 0.08) : F.modelCar(paints[row * 3 + k], 0.22);
        item.rotation.y = (row === 1 && k === 1) ? -Math.PI / 2 : Math.PI / 2;
      } else if (style === 'mario') {
        item = k === 1 ? F.questionBlock(0.15) : F.mushroom(0.065, row === 0 ? null : 0x2fa84f);
      } else {
        item = new THREE.Mesh(new THREE.SphereGeometry(0.06, 20, 14), new THREE.MeshPhysicalMaterial({ color: k === 1 ? 0xf5f5f5 : 0xff3b45, roughness: 0.2, clearcoat: 1 }));
        item.position.y = 0.06;
      }
      item.position.x = W / 2 - 0.1;
      item.position.y += y + 0.014;
      item.position.z = shelfZ + dz;
      g.add(item);
    });
  });

  // ── east wall between the booth and the door ──
  const ex = W / 2;
  const ez = 1.15;
  if (style === 'ferrari') {
    const lp = F.litPanel(0.9, 0.9);
    lp.rotation.y = -Math.PI / 2;
    lp.position.set(ex - 0.03, 1.6, ez);
    g.add(lp);
    const wheel = F.steeringWheel(0.17);
    wheel.rotation.y = -Math.PI / 2;
    wheel.position.set(ex - 0.12, 1.65, ez);
    g.add(wheel);
    const shelf = new THREE.Mesh(new THREE.BoxGeometry(0.24, 0.03, 1.0), F.M.furniture);
    shelf.position.set(ex - 0.12, 0.95, ez);
    shelf.castShadow = true;
    g.add(shelf);
    const led = F.ledStrip(0.9, 'z');
    led.position.set(ex - 0.2, 0.93, ez);
    g.add(led);
    [[0xd40000, -0.27], [0xf2f2f2, 0.27]].forEach(([c, dz]) => {
      const h = F.helmet(c, 0.1);
      h.rotation.y = -Math.PI / 2;
      h.position.set(ex - 0.12, 0.965, ez + dz);
      g.add(h);
    });
  } else if (style === 'mario') {
    // white backlit panel with a big ? block + brick stack, pipe with 1-UP by the door
    const lp = F.litPanel(0.9, 0.9, 0.04, F.M.marioBlue);
    lp.rotation.y = -Math.PI / 2;
    lp.position.set(ex - 0.03, 1.6, ez);
    g.add(lp);
    const bigQ = F.questionBlock(0.34);
    bigQ.position.set(ex - 0.23, 1.43, ez);
    g.add(bigQ);
    const pipe = F.warpPipe(0.62, 0.15);
    pipe.position.set(ex - 0.3, 0, ez + 0.05);
    g.add(pipe);
    const oneUp = F.mushroom(0.09, 0x2fa84f);
    oneUp.position.set(ex - 0.3, 0.62, ez + 0.05);
    g.add(oneUp);
    [[0, 0], [0.2, 0], [0.1, 0.2]].forEach(([dz, dy], i) => {
      const b = i === 2 ? F.questionBlock(0.2) : F.brickBlock(0.2);
      b.position.set(ex - 0.25, dy, ez - 0.55 + dz);
      g.add(b);
    });
  } else {
    const lamp = F.tetrisLamp();
    lamp.position.set(ex - 0.3, 0, ez - 0.1);
    g.add(lamp);
    const sh = F.floatingShelf(0.9);
    sh.rotation.y = Math.PI;
    sh.position.set(ex - 0.14, 1.55, ez);
    g.add(sh);
  }

  // ── 展示架 display cabinet on the south wall + shelves above it ──
  const cab = F.displayCabinet({ width: 2.2, depth: 0.45, height: 0.95 });
  cab.position.set(-0.6, 0, D / 2 - 0.225);
  g.add(cab);
  [1.5, 1.9].forEach((y, row) => {
    const shelf = new THREE.Mesh(new THREE.BoxGeometry(2.0, 0.028, 0.22), F.M.furniture);
    shelf.position.set(-0.6, y, D / 2 - 0.11);
    shelf.castShadow = true;
    g.add(shelf);
    const led = F.ledStrip(1.9, 'x');
    led.position.set(-0.6, y - 0.02, D / 2 - 0.18);
    g.add(led);
    [-0.7, -0.23, 0.23, 0.7].forEach((dx, k) => {
      let item;
      if (style === 'ferrari') {
        const isHelmet = (row === 0 && k === 1) || (row === 1 && k === 2);
        item = isHelmet ? F.helmet(k === 1 ? 0xffd400 : 0xd40000, 0.08) : F.modelCar([0xd40000, 0xd40000, 0x111114, 0xffd400][k], 0.22);
        item.rotation.y = isHelmet ? Math.PI : (k % 2 ? Math.PI : 0);
      } else if (style === 'mario') {
        item = [() => F.mushroom(0.065), () => F.questionBlock(0.15), () => F.star(0.075), () => F.brickBlock(0.15)][(k + row) % 4]();
      } else {
        item = new THREE.Mesh(new THREE.CapsuleGeometry(0.035, 0.12, 6, 12), new THREE.MeshStandardMaterial({ color: [0xff3b45, 0xf5f5f5, 0xffc933, 0x8fa3ff][k], roughness: 0.45 }));
        item.position.y = 0.095;
      }
      item.position.x = -0.6 + dx;
      item.position.y += y + 0.014;
      item.position.z = D / 2 - 0.11;
      g.add(item);
    });
  });
  return g;
}

/* ───────────── lights ───────────── */
function buildLights(T) {
  const g = new THREE.Group();
  const ferrari = T.style === 'ferrari';
  const warm = T.mario ? 0xffffff : 0xfff0e4;
  g.add(new THREE.AmbientLight(warm, T.mario ? 0.05 : 0.06));

  const key = new THREE.SpotLight(warm, T.keyLight, 9, Math.PI / 3.0, 0.6, 1.6);
  key.position.set(0.3, ROOM_H - 0.1, -0.2);
  key.target.position.set(0, 0, -0.2);
  key.castShadow = true;
  key.shadow.mapSize.set(2048, 2048);
  key.shadow.bias = -0.00015;
  key.shadow.radius = 4;
  g.add(key, key.target);

  // light box over the desks
  const lbLight = new THREE.RectAreaLight(0xfff0dc, T.mario ? 4 : 6, 3.0, 0.3);
  lbLight.position.set(-ROOM_W / 2 + SOFFIT_W / 2, SOFFIT_Y - 0.01, 0);
  lbLight.lookAt(-ROOM_W / 2 + SOFFIT_W / 2, 0, 0);
  g.add(lbLight);
  DESK_Z.forEach((z) => {
    const s = new THREE.SpotLight(warm, T.mario ? 4 : 6, 4, Math.PI / 5, 0.7, 1.5);
    s.position.set(DESK_X + 0.5, SOFFIT_Y - 0.05, z);
    s.target.position.set(DESK_X + 0.1, 0.75, z);
    g.add(s, s.target);
  });

  // booth + display cabinet spots
  const b = new THREE.SpotLight(warm, T.mario ? 4 : 6, 4.5, Math.PI / 4.5, 0.7, 1.5);
  b.position.set(0.9, ROOM_H - 0.1, -0.6);
  b.target.position.set(1.4, 0.6, -0.6);
  g.add(b, b.target);
  const c = new THREE.SpotLight(warm, T.mario ? 3.5 : 5, 4.5, Math.PI / 4.5, 0.7, 1.5);
  c.position.set(-0.6, ROOM_H - 0.1, 1.2);
  c.target.position.set(-0.6, 0.6, 1.9);
  g.add(c, c.target);

  // bay window dusk light
  const winLight = new THREE.RectAreaLight(ferrari ? 0xc9b8ff : 0xcfe3ff, T.mario ? 1.8 : 2.4, WIN.width, WIN.height);
  winLight.position.set(WIN.x, WIN.sillY + WIN.height / 2, -ROOM_D / 2 + 0.02);
  winLight.lookAt(WIN.x, 1.0, 0);
  g.add(winLight);

  if (!T.mario) {
    const redA = new THREE.PointLight(T.accent, 2.2, 4.5, 2);
    redA.position.set(-ROOM_W / 2 + 0.45, 2.0, 0);
    const redB = new THREE.PointLight(T.accent, 0.7, 3.0, 2);
    redB.position.set(ROOM_W / 2 - 0.75, 2.2, 1.15);
    const redC = new THREE.PointLight(T.accent, 1.0, 3, 2);
    redC.position.set(ROOM_W / 2 - 0.6, 0.15, -0.5);
    g.add(redA, redB, redC);
  }

  // corridor light outside the glass door
  const out = new THREE.PointLight(0xffe0b8, 1.4, 4, 2);
  out.position.set(DOOR.x, 2.1, ROOM_D / 2 + 0.8);
  g.add(out);

  const cove = new THREE.RectAreaLight(T.coveColor, T.coveIntensity, ROOM_W - 1.1, ROOM_D - 1.1);
  cove.position.set(0, ROOM_H - 0.05, 0);
  cove.lookAt(0, 0, 0);
  g.add(cove);
  return g;
}

/* ───────────── theme build / switch ───────────── */
let current = null;

function buildScene(T) {
  if (current) {
    scene.remove(current.root);
    disposeGroup(current.root);
  }
  F.applyTheme(T);
  TX.resetSeed();
  const ferrari = T.style === 'ferrari';
  const tex = {
    metal: TX.brushedMetal([2.5, 1], T.wallBase, T.wallStreak),
    floor: TX.floorTiles([3, 3.5], T.floorBase, T.floorGrout, T.floorVein),
    peg: TX.pegboard([5, 2.4], T.pegBase, T.pegHole),
    screen: ferrari ? TX.ferrariWallpaper() : T.mario ? TX.marioWallpaper() : TX.screenWallpaper(),
    view: ferrari ? TX.skylineDusk() : T.mario ? TX.marioSkyline() : TX.windowView(),
    logo: TX.wallLogo('WE', '#ff2a36'),
    wordmark: TX.wallLogo('ROSSO CORSA', '#ff2222', 150),
    emblem: TX.ferrariEmblem(),
    signs: T.mario ? [TX.playerSign('P1', '#e4291b'), TX.playerSign('P2', '#2fa84f')] : [],
    keys: T.mario ? TX.keyboardTop('#e9eaee', '#f7f7f9', 'rgba(255,255,255,0.6)') : TX.keyboardTop(),
    rug: ferrari ? TX.rugStripes(T.rugBase, T.rugLo) : T.mario ? TX.coinRug() : TX.rugFabric([4, 4], T.rugBase, T.rugLo),
    wire: TX.wireGlass(),
  };
  const root = new THREE.Group();
  root.add(buildShell(T, tex), buildFurniture(T, tex), buildLights(T));
  scene.add(root);
  scene.background = new THREE.Color(T.background);
  scene.environmentIntensity = T.envIntensity;
  renderer.toneMappingExposure = T.exposure;
  if (bloom) {
    bloom.strength = T.bloom.strength;
    bloom.radius = T.bloom.radius;
    bloom.threshold = T.bloom.threshold;
  }
  current = { root, theme: T };

  document.getElementById('brand').textContent = `Interactive 3D · ${T.name}`;
  document.querySelectorAll('[data-theme]').forEach((b) => b.classList.toggle('active', b.dataset.theme === T.key));
  document.documentElement.dataset.theme = T.key;
}

document.querySelectorAll('[data-theme]').forEach((btn) => {
  btn.onclick = () => buildScene(F.THEMES[btn.dataset.theme]);
});

/* ───────────── post-processing ───────────── */
const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));
const bloom = new UnrealBloomPass(new THREE.Vector2(window.innerWidth, window.innerHeight), 0.3, 0.5, 0.9);
composer.addPass(bloom);
composer.addPass(new OutputPass());

const initial = new URLSearchParams(location.search).get('theme');
buildScene(F.THEMES[initial] || F.THEMES.ferrari);

flyTo(CAMS.entrance);

/* ───────────── loop ───────────── */
function updateWalk(dt) {
  if (mode !== 'walk' || !walk.isLocked) return;
  const speed = 2.2;
  walkVelocity.x -= walkVelocity.x * 8.0 * dt;
  walkVelocity.z -= walkVelocity.z * 8.0 * dt;
  const dir = new THREE.Vector3(Number(walkKeys.right) - Number(walkKeys.left), 0, Number(walkKeys.forward) - Number(walkKeys.back)).normalize();
  if (walkKeys.forward || walkKeys.back) walkVelocity.z -= dir.z * speed * dt;
  if (walkKeys.left || walkKeys.right) walkVelocity.x -= dir.x * speed * dt;
  walk.moveRight(-walkVelocity.x * dt * 60);
  walk.moveForward(-walkVelocity.z * dt * 60);
  camera.position.y = 1.55;
  camera.position.x = THREE.MathUtils.clamp(camera.position.x, -ROOM_W / 2 + 1.2, ROOM_W / 2 - 0.8);
  camera.position.z = THREE.MathUtils.clamp(camera.position.z, -ROOM_D / 2 + 0.85, ROOM_D / 2 - 0.45);
}

function animate() {
  requestAnimationFrame(animate);
  const dt = Math.min(clock.getDelta(), 0.05);
  if (mode === 'orbit') orbit.update();
  else updateWalk(dt);
  composer.render();
  window.__frames = (window.__frames || 0) + 1;
}
animate();

window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
  composer.setSize(window.innerWidth, window.innerHeight);
});
