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
 * Floor plan (meters). Entrance wall is +Z.
 *  -X left wall  : two height-adjustable desks, sitter faces -X
 *  +X right wall : L-shaped 卡座书架 directly BEHIND the chairs
 *  -Z far wall   : short booth arm (L corner)
 *  +Z near wall  : entrance door (right) + display cabinet (left)
 */
const ROOM_W = 4.5;
const ROOM_D = 3.85;
const ROOM_H = 2.65;

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

const ENTRANCE_CAM = { pos: [1.45, 1.5, 1.72], target: [-0.7, 0.95, -0.55] };
const OVERVIEW_CAM = { pos: [3.4, 4.6, 3.6], target: [0, 0.5, 0] };
function flyTo({ pos, target }) {
  setMode('orbit');
  camera.position.set(...pos);
  orbit.target.set(...target);
  orbit.update();
}
document.getElementById('btn-orbit').onclick = () => setMode('orbit');
document.getElementById('btn-walk').onclick = () => setMode('walk');
document.getElementById('btn-entrance').onclick = () => flyTo(ENTRANCE_CAM);
document.getElementById('btn-overview').onclick = () => flyTo(OVERVIEW_CAM);
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
  const wallMat = new THREE.MeshStandardMaterial({ map: tex.metal.map, color: T.wall, metalness: 0.75, roughness: 0.35 });
  const wallEntrance = T.mario ? wallMat : new THREE.MeshStandardMaterial({ color: 0x1a1b20, metalness: 0.35, roughness: 0.6 });
  const floorMat = new THREE.MeshPhysicalMaterial({
    map: tex.floor.map, roughnessMap: tex.floor.roughnessMap, roughness: 0.35, metalness: 0.05, clearcoat: 0.9, clearcoatRoughness: 0.08,
  });
  const ceilMat = new THREE.MeshStandardMaterial({ color: 0xf4f4f6, roughness: 0.9 });

  g.add(plane(ROOM_W, ROOM_D, floorMat, 0, 0, 0, 0, -Math.PI / 2));
  // Single-sided planes facing inward: from outside they are culled (dollhouse view)
  g.add(plane(ROOM_W, ROOM_D, ceilMat, 0, ROOM_H, 0, 0, Math.PI / 2));
  g.add(plane(ROOM_D, ROOM_H, wallMat, -ROOM_W / 2, ROOM_H / 2, 0, Math.PI / 2));
  g.add(plane(ROOM_D, ROOM_H, wallMat, ROOM_W / 2, ROOM_H / 2, 0, -Math.PI / 2));
  g.add(plane(ROOM_W, ROOM_H, wallMat, 0, ROOM_H / 2, -ROOM_D / 2, 0));
  g.add(plane(ROOM_W, ROOM_H, wallEntrance, 0, ROOM_H / 2, ROOM_D / 2, Math.PI));

  // Ceiling tray with warm cove + accent perimeter line
  g.add(plane(ROOM_W - 0.7, ROOM_D - 0.7, ceilMat, 0, ROOM_H - 0.08, 0, 0, Math.PI / 2));
  const cove = [
    [0, -ROOM_D / 2 + 0.35, 'x', ROOM_W - 0.7],
    [0, ROOM_D / 2 - 0.35, 'x', ROOM_W - 0.7],
    [-ROOM_W / 2 + 0.35, 0, 'z', ROOM_D - 0.7],
    [ROOM_W / 2 - 0.35, 0, 'z', ROOM_D - 0.7],
  ];
  cove.forEach(([x, z, axis, len]) => {
    const warm = F.ledStrip(len, axis, F.M.warmGlow);
    warm.position.set(x, ROOM_H - 0.085, z);
    g.add(warm);
    const line = F.ledStrip(len + 0.4, axis);
    const off = 0.2;
    line.position.set(axis === 'x' ? x : x + (x > 0 ? off : -off), ROOM_H - 0.16, axis === 'z' ? z : z + (z > 0 ? off : -off));
    g.add(line);
  });
  [[-ROOM_W / 2 + 0.03, -ROOM_D / 2 + 0.03], [ROOM_W / 2 - 0.03, -ROOM_D / 2 + 0.03], [-ROOM_W / 2 + 0.03, ROOM_D / 2 - 0.03]].forEach(([x, z]) => {
    const v = F.ledStrip(ROOM_H - 0.3, 'y');
    v.position.set(x, ROOM_H / 2, z);
    g.add(v);
  });
  const fl = F.ledStrip(ROOM_D - 0.5, 'z');
  fl.position.set(-ROOM_W / 2 + 0.06, 0.02, 0);
  g.add(fl);

  // Door + frame at bottom-right
  const doorX = ROOM_W / 2 - 0.55;
  const frameMat = new THREE.MeshStandardMaterial({ color: T.mario ? 0xe6e7ea : 0x0c0c0f, roughness: 0.5, metalness: 0.3 });
  const mkFrame = (w, h, x, y) => { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, 0.06), frameMat); m.position.set(x, y, ROOM_D / 2 - 0.03); return m; };
  g.add(mkFrame(0.06, 2.15, doorX - 0.47, 1.075), mkFrame(0.06, 2.15, doorX + 0.47, 1.075), mkFrame(1.0, 0.06, doorX, 2.18));
  const door = new THREE.Mesh(new THREE.BoxGeometry(0.88, 2.1, 0.045), new THREE.MeshPhysicalMaterial({ color: T.mario ? 0xf2f2f4 : 0x1d1a19, roughness: 0.45, clearcoat: 0.3 }));
  door.position.set(doorX + 0.05, 1.05, ROOM_D / 2 - 0.5);
  door.rotation.y = Math.PI / 2.6;
  door.castShadow = true;
  g.add(door);
  const handle = new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.012, 0.14, 12), F.M.chrome);
  handle.rotation.x = Math.PI / 2;
  handle.position.set(doorX - 0.28, 1.0, ROOM_D / 2 - 0.16);
  g.add(handle);

  const rug = new THREE.Mesh(new THREE.CylinderGeometry(0.75, 0.75, 0.025, 64), new THREE.MeshStandardMaterial({ map: tex.rug, roughness: 1 }));
  rug.position.set(0.2, 0.0125, -0.15);
  rug.receiveShadow = true;
  g.add(rug);
  return g;
}

/* ───────────── furniture placement ───────────── */
function buildFurniture(T, tex) {
  const g = new THREE.Group();
  const deskX = -ROOM_W / 2 + 0.36;

  // Pegboard wall panel behind desks
  const peg = new THREE.Mesh(new THREE.PlaneGeometry(3.1, 1.5), new THREE.MeshStandardMaterial({
    map: tex.peg.map, bumpMap: tex.peg.bumpMap, bumpScale: 0.01, metalness: 0.5, roughness: 0.5,
  }));
  peg.position.set(-ROOM_W / 2 + 0.01, 1.6, 0.2);
  peg.rotation.y = Math.PI / 2;
  peg.receiveShadow = true;
  g.add(peg);
  const pegFrame = F.ledStrip(3.1, 'z');
  pegFrame.position.set(-ROOM_W / 2 + 0.02, 2.36, 0.2);
  g.add(pegFrame);

  if (T.mario) {
    // Long white shelves with accent LED (reference: 白色层板)
    [[2.15, 1.05], [2.02, -0.55]].forEach(([y, zc]) => {
      const sh = F.floatingShelf(1.3);
      sh.position.set(-ROOM_W / 2 + 0.14, y, zc);
      g.add(sh);
    });
    // Colourful detachable modules on the pegboard
    const mods = [
      [0xe4291b, 1.7, 0.25, 0.4, 0.22], [0xffffff, 1.35, 0.85, 0.3, 0.2], [0xf7b515, 1.45, -0.25, 0.26, 0.18],
      [0x2fa84f, 1.8, -0.75, 0.3, 0.2], [0x2f7be5, 1.2, 1.35, 0.22, 0.16],
    ];
    mods.forEach(([c, y, z, w, h]) => {
      const m = F.pegModule(c, w, h);
      m.position.set(-ROOM_W / 2 + 0.015, y, z);
      g.add(m);
    });
    // ? blocks + bricks row as the wall focal (instead of WE logo)
    [-0.15, 0.03, 0.21].forEach((z, i) => {
      const b = i === 1 ? F.questionBlock(0.17) : F.brickBlock(0.17);
      b.position.set(-ROOM_W / 2 + 0.1, 1.95, z);
      g.add(b);
    });
    const st = F.star(0.09);
    st.position.set(-ROOM_W / 2 + 0.12, 2.28, 0.03);
    st.rotation.y = Math.PI / 2;
    g.add(st);
  } else {
    const logo = F.wallLogoPlane(tex.logo, 0.95);
    logo.position.set(-ROOM_W / 2 + 0.03, 2.0, 0.2);
    logo.rotation.y = Math.PI / 2;
    g.add(logo);
    g.add(F.redPipe([
      [-ROOM_W / 2 + 0.06, 1.1, -1.3], [-ROOM_W / 2 + 0.06, 1.1, -0.6], [-ROOM_W / 2 + 0.06, 1.45, -0.45],
      [-ROOM_W / 2 + 0.06, 1.45, 0.9], [-ROOM_W / 2 + 0.06, 1.1, 1.05], [-ROOM_W / 2 + 0.06, 1.1, 1.7],
    ]));
    const s1 = F.floatingShelf(0.9);
    s1.position.set(-ROOM_W / 2 + 0.14, 1.55, 1.25);
    g.add(s1);
    const s2 = F.floatingShelf(0.9);
    s2.position.set(-ROOM_W / 2 + 0.14, 1.9, 1.25);
    g.add(s2);
  }

  // Two desks along left wall, sitter faces -X
  [-0.55, 0.95].forEach((z, i) => {
    const desk = F.gamingDesk({ screenTex: tex.screen, keyboardTex: tex.keys, withHeadset: i === 0 });
    desk.rotation.y = Math.PI / 2;
    desk.position.set(deskX, 0, z);
    g.add(desk);
    const chair = F.gamingChair();
    chair.rotation.y = Math.PI / 2;
    chair.position.set(deskX + 0.62, 0, z + (i === 0 ? 0.05 : -0.05));
    g.add(chair);
    if (T.mario) {
      const m = F.mushroom(0.05, i === 0 ? null : 0x2fa84f);
      m.position.set(deskX + 0.02, 0.762, z + 0.55);
      g.add(m);
    }
  });

  const pc = F.pcTower();
  pc.position.set(-ROOM_W / 2 + 0.36, 0, 1.75);
  g.add(pc);

  // ── L-shaped 卡座书架 behind the chairs ──
  const boothDepth = 0.72;
  const boothLen = 2.8;
  const boothZ = -0.15;
  const mainBooth = F.boothUnit({ length: boothLen, depth: boothDepth });
  mainBooth.position.set(ROOM_W / 2 - boothDepth / 2, 0, boothZ);
  g.add(mainBooth);

  const win = F.windowUnit({ width: 1.7, height: 1.1, viewTex: tex.view });
  win.position.set(ROOM_W / 2 - 0.03, 1.75, boothZ);
  g.add(win);

  const towerY0 = 1.0;
  [boothZ - boothLen / 2 + 0.25, boothZ + boothLen / 2 - 0.25].forEach((z) => {
    const t = F.bookshelf({ width: 0.5, height: 1.35, depth: 0.3, shelves: 3, y0: towerY0 });
    t.position.set(ROOM_W / 2 - 0.15, 0, z);
    g.add(t);
  });

  const armBooth = F.boothUnit({ length: 1.0, depth: boothDepth });
  armBooth.rotation.y = Math.PI / 2;
  armBooth.position.set(ROOM_W / 2 - boothDepth - 0.5, 0, -ROOM_D / 2 + boothDepth / 2);
  g.add(armBooth);
  const armShelf = F.bookshelf({ width: 1.0, height: 1.35, depth: 0.3, shelves: 3, y0: towerY0 });
  armShelf.rotation.y = Math.PI / 2;
  armShelf.position.set(ROOM_W / 2 - boothDepth - 0.5, 0, -ROOM_D / 2 + 0.15);
  g.add(armShelf);

  const column = new THREE.Mesh(new THREE.BoxGeometry(0.08, 1.4, 0.08), T.mario ? F.M.warmGlow : F.M.redGlow);
  column.position.set(ROOM_W / 2 - boothDepth - 1.12, 1.2, -ROOM_D / 2 + 0.2);
  g.add(column);

  if (T.mario) {
    const pipe = F.warpPipe(0.62, 0.15);
    pipe.position.set(ROOM_W / 2 - 0.95, 0, 1.5);
    g.add(pipe);
    const plant = F.mushroom(0.09);
    plant.position.set(ROOM_W / 2 - 0.95, 0.62, 1.5);
    g.add(plant);
    // block stack by the entrance display
    const b1 = F.brickBlock(0.2); b1.position.set(0.95, 0, ROOM_D / 2 - 0.35); g.add(b1);
    const b2 = F.questionBlock(0.2); b2.position.set(0.95, 0.2, ROOM_D / 2 - 0.35); g.add(b2);
  } else {
    const lamp = F.tetrisLamp();
    lamp.position.set(ROOM_W / 2 - 0.95, 0, 1.45);
    g.add(lamp);
  }

  const cab = F.displayCabinet({ width: 2.15, depth: 0.4, height: 0.95 });
  cab.position.set(-0.45, 0, ROOM_D / 2 - 0.2);
  g.add(cab);
  return g;
}

/* ───────────── lights ───────────── */
function buildLights(T) {
  const g = new THREE.Group();
  const warm = T.mario ? 0xffffff : 0xfff0e4;
  g.add(new THREE.AmbientLight(warm, T.mario ? 0.05 : 0.06));

  const key = new THREE.SpotLight(warm, T.keyLight, 9, Math.PI / 3.2, 0.6, 1.6);
  key.position.set(0.4, ROOM_H - 0.1, 0.3);
  key.target.position.set(0, 0, 0);
  key.castShadow = true;
  key.shadow.mapSize.set(2048, 2048);
  key.shadow.bias = -0.00015;
  key.shadow.radius = 4;
  g.add(key, key.target);

  [-0.55, 0.95].forEach((z) => {
    const s = new THREE.SpotLight(warm, T.mario ? 5 : 8, 4, Math.PI / 5, 0.7, 1.5);
    s.position.set(-ROOM_W / 2 + 0.7, ROOM_H - 0.1, z);
    s.target.position.set(-ROOM_W / 2 + 0.5, 0.75, z);
    g.add(s, s.target);
  });
  const b = new THREE.SpotLight(warm, T.mario ? 4.5 : 7, 4, Math.PI / 4.5, 0.7, 1.5);
  b.position.set(ROOM_W / 2 - 0.9, ROOM_H - 0.1, -0.15);
  b.target.position.set(ROOM_W / 2 - 0.4, 0.6, -0.15);
  g.add(b, b.target);

  if (!T.mario) {
    const redA = new THREE.PointLight(T.accent, 2.5, 5, 2);
    redA.position.set(-ROOM_W / 2 + 0.5, 1.9, 0.2);
    const redB = new THREE.PointLight(T.accent, 1.5, 4, 2);
    redB.position.set(ROOM_W / 2 - 0.6, 1.2, -0.15);
    g.add(redA, redB);
  }

  const winLight = new THREE.RectAreaLight(0xcfe3ff, T.mario ? 1.6 : 2.2, 1.7, 1.1);
  winLight.position.set(ROOM_W / 2 - 0.08, 1.75, -0.15);
  winLight.lookAt(0, 1.1, -0.15);
  g.add(winLight);

  const cove = new THREE.RectAreaLight(T.coveColor, T.coveIntensity, ROOM_W - 0.8, ROOM_D - 0.8);
  cove.position.set(0, ROOM_H - 0.12, 0);
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
  const tex = {
    metal: TX.brushedMetal([2.5, 1], T.wallBase, T.wallStreak),
    floor: TX.floorTiles([3, 2.6], T.floorBase, T.floorGrout, T.mario ? '190,192,198' : '150,152,160'),
    peg: TX.pegboard([5, 2.4], T.pegBase, T.pegHole),
    screen: T.mario ? TX.marioWallpaper() : TX.screenWallpaper(),
    view: TX.windowView(),
    logo: TX.wallLogo('WE', '#ff2a36'),
    keys: T.mario ? TX.keyboardTop('#e9eaee', '#f7f7f9', 'rgba(255,255,255,0.6)') : TX.keyboardTop(),
    rug: TX.rugFabric([4, 4], T.rugBase, T.rugLo),
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
buildScene(F.THEMES[initial] || F.THEMES.red);

flyTo(ENTRANCE_CAM);

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
  camera.position.x = THREE.MathUtils.clamp(camera.position.x, -ROOM_W / 2 + 1.35, ROOM_W / 2 - 0.9);
  camera.position.z = THREE.MathUtils.clamp(camera.position.z, -ROOM_D / 2 + 0.9, ROOM_D / 2 - 0.55);
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
