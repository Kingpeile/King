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
const RED = F.RED;

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
  } catch {
    return false;
  }
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
renderer.toneMappingExposure = 0.9;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
app.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x040405);

const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
scene.environmentIntensity = 0.28;

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

/* ───────────── textures ───────────── */
const texMetal = TX.brushedMetal([2.5, 1]);
const texFloor = TX.floorTiles([3, 2.6]);
const texPeg = TX.pegboard([5, 2.4]);
const texScreen = TX.screenWallpaper();
const texView = TX.windowView();
const texLogo = TX.wallLogo();
const texKeys = TX.keyboardTop();
const texRug = TX.rugFabric();

/* ───────────── room shell ───────────── */
function plane(w, h, material, x, y, z, rotY = 0, rotX = 0) {
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), material);
  m.position.set(x, y, z);
  m.rotation.set(rotX, rotY, 0);
  m.receiveShadow = true;
  return m;
}

function buildShell() {
  const g = new THREE.Group();
  const wallMat = new THREE.MeshStandardMaterial({ map: texMetal.map, color: 0xd4d6db, metalness: 0.75, roughness: 0.35 });
  const wallDark = new THREE.MeshStandardMaterial({ color: 0x1a1b20, metalness: 0.35, roughness: 0.6 });
  const floorMat = new THREE.MeshPhysicalMaterial({
    map: texFloor.map, roughnessMap: texFloor.roughnessMap, roughness: 0.35, metalness: 0.05, clearcoat: 0.9, clearcoatRoughness: 0.08,
  });
  const ceilMat = new THREE.MeshStandardMaterial({ color: 0xf0f0f2, roughness: 0.9 });

  const floor = plane(ROOM_W, ROOM_D, floorMat, 0, 0, 0, 0, -Math.PI / 2);
  g.add(floor);

  // Single-sided planes facing inward: from outside they are culled (dollhouse view)
  g.add(plane(ROOM_W, ROOM_D, ceilMat, 0, ROOM_H, 0, 0, Math.PI / 2));
  g.add(plane(ROOM_D, ROOM_H, wallMat, -ROOM_W / 2, ROOM_H / 2, 0, Math.PI / 2));
  g.add(plane(ROOM_D, ROOM_H, wallMat, ROOM_W / 2, ROOM_H / 2, 0, -Math.PI / 2));
  g.add(plane(ROOM_W, ROOM_H, wallMat, 0, ROOM_H / 2, -ROOM_D / 2, 0));
  g.add(plane(ROOM_W, ROOM_H, wallDark, 0, ROOM_H / 2, ROOM_D / 2, Math.PI));

  // Ceiling recess (tray): lowered inner panel, single-sided so overview can see in
  g.add(plane(ROOM_W - 0.7, ROOM_D - 0.7, ceilMat, 0, ROOM_H - 0.08, 0, 0, Math.PI / 2));
  const cove = [
    [0, -ROOM_D / 2 + 0.35, 'x', ROOM_W - 0.7],
    [0, ROOM_D / 2 - 0.35, 'x', ROOM_W - 0.7],
    [-ROOM_W / 2 + 0.35, 0, 'z', ROOM_D - 0.7],
    [ROOM_W / 2 - 0.35, 0, 'z', ROOM_D - 0.7],
  ];
  cove.forEach(([x, z, axis, len]) => {
    const warm = F.ledStrip(len, axis, F.Materials.warmGlow);
    warm.position.set(x, ROOM_H - 0.085, z);
    g.add(warm);
    const red = F.ledStrip(len + 0.4, axis);
    const off = 0.2;
    red.position.set(axis === 'x' ? x : x + (x > 0 ? off : -off), ROOM_H - 0.16, axis === 'z' ? z : z + (z > 0 ? off : -off));
    g.add(red);
  });
  // Vertical red corner lines
  [[-ROOM_W / 2 + 0.03, -ROOM_D / 2 + 0.03], [ROOM_W / 2 - 0.03, -ROOM_D / 2 + 0.03], [-ROOM_W / 2 + 0.03, ROOM_D / 2 - 0.03]].forEach(([x, z]) => {
    const v = F.ledStrip(ROOM_H - 0.3, 'y');
    v.position.set(x, ROOM_H / 2, z);
    g.add(v);
  });
  // Floor perimeter glow on desk side
  const fl = F.ledStrip(ROOM_D - 0.5, 'z');
  fl.position.set(-ROOM_W / 2 + 0.06, 0.02, 0);
  g.add(fl);

  // Door + frame at bottom-right
  const doorX = ROOM_W / 2 - 0.55;
  const frameMat = new THREE.MeshStandardMaterial({ color: 0x0c0c0f, roughness: 0.5, metalness: 0.3 });
  const frameL = new THREE.Mesh(new THREE.BoxGeometry(0.06, 2.15, 0.06), frameMat);
  frameL.position.set(doorX - 0.47, 1.075, ROOM_D / 2 - 0.03);
  const frameR = new THREE.Mesh(new THREE.BoxGeometry(0.06, 2.15, 0.06), frameMat);
  frameR.position.set(doorX + 0.47, 1.075, ROOM_D / 2 - 0.03);
  const frameT = new THREE.Mesh(new THREE.BoxGeometry(1.0, 0.06, 0.06), frameMat);
  frameT.position.set(doorX, 2.18, ROOM_D / 2 - 0.03);
  g.add(frameL, frameR, frameT);
  const door = new THREE.Mesh(new THREE.BoxGeometry(0.88, 2.1, 0.045), new THREE.MeshPhysicalMaterial({ color: 0x1d1a19, roughness: 0.45, clearcoat: 0.3 }));
  door.position.set(doorX + 0.05, 1.05, ROOM_D / 2 - 0.5);
  door.rotation.y = Math.PI / 2.6; // ajar
  door.castShadow = true;
  g.add(door);
  const handle = new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.012, 0.14, 12), F.Materials.chrome);
  handle.rotation.x = Math.PI / 2;
  handle.position.set(doorX - 0.28, 1.0, ROOM_D / 2 - 0.16);
  g.add(handle);

  // Rug
  const rug = new THREE.Mesh(new THREE.CylinderGeometry(0.75, 0.75, 0.025, 64), new THREE.MeshStandardMaterial({ map: texRug, roughness: 1 }));
  rug.position.set(0.2, 0.0125, -0.15);
  rug.receiveShadow = true;
  g.add(rug);

  return g;
}

/* ───────────── furniture placement ───────────── */
function buildFurniture() {
  const g = new THREE.Group();
  const deskX = -ROOM_W / 2 + 0.36; // desk center x (depth 0.7 against left wall)

  // Pegboard wall panel behind desks
  const peg = new THREE.Mesh(new THREE.PlaneGeometry(3.1, 1.5), new THREE.MeshStandardMaterial({
    map: texPeg.map, bumpMap: texPeg.bumpMap, bumpScale: 0.01, metalness: 0.5, roughness: 0.5,
  }));
  peg.position.set(-ROOM_W / 2 + 0.01, 1.6, 0.2);
  peg.rotation.y = Math.PI / 2;
  peg.receiveShadow = true;
  g.add(peg);
  const pegFrame = F.ledStrip(3.1, 'z');
  pegFrame.position.set(-ROOM_W / 2 + 0.02, 2.36, 0.2);
  g.add(pegFrame);

  // WE logo
  const logo = F.wallLogoPlane(texLogo, 0.95);
  logo.position.set(-ROOM_W / 2 + 0.03, 2.0, 0.2);
  logo.rotation.y = Math.PI / 2;
  g.add(logo);

  // red pipe run across the pegboard
  g.add(F.redPipe([
    [-ROOM_W / 2 + 0.06, 1.1, -1.3],
    [-ROOM_W / 2 + 0.06, 1.1, -0.6],
    [-ROOM_W / 2 + 0.06, 1.45, -0.45],
    [-ROOM_W / 2 + 0.06, 1.45, 0.9],
    [-ROOM_W / 2 + 0.06, 1.1, 1.05],
    [-ROOM_W / 2 + 0.06, 1.1, 1.7],
  ]));

  // Two desks (1.5 m each) along left wall, sitter faces -X
  [-0.55, 0.95].forEach((z, i) => {
    const desk = F.gamingDesk({ screenTex: texScreen, keyboardTex: texKeys, withHeadset: i === 0 });
    desk.rotation.y = Math.PI / 2; // local -Z (monitor side) → world -X
    desk.position.set(deskX, 0, z);
    g.add(desk);

    const chair = F.gamingChair();
    chair.rotation.y = Math.PI / 2; // local -Z (front) → world -X
    chair.position.set(deskX + 0.62, 0, z + (i === 0 ? 0.05 : -0.05));
    g.add(chair);
  });

  // PC tower on the floor at the desk end, glass facing the room
  const pc = F.pcTower();
  pc.position.set(-ROOM_W / 2 + 0.36, 0, 1.75);
  g.add(pc);

  // Floating shelves above the second desk area
  const s1 = F.floatingShelf(0.9);
  s1.position.set(-ROOM_W / 2 + 0.14, 1.55, 1.25);
  g.add(s1);
  const s2 = F.floatingShelf(0.9);
  s2.position.set(-ROOM_W / 2 + 0.14, 1.9, 1.25);
  g.add(s2);

  // ── L-shaped 卡座书架 behind the chairs (right wall + far-wall arm) ──
  const boothDepth = 0.72;
  const boothLen = 2.8;
  const boothZ = -0.15;
  const mainBooth = F.boothUnit({ length: boothLen, depth: boothDepth });
  mainBooth.position.set(ROOM_W / 2 - boothDepth / 2, 0, boothZ);
  g.add(mainBooth);

  // Window with blinds above the bench
  const win = F.windowUnit({ width: 1.7, height: 1.1, viewTex: texView });
  win.position.set(ROOM_W / 2 - 0.03, 1.75, boothZ);
  g.add(win);

  // Bookshelf towers flanking the window (卡座书架)
  const towerY0 = 1.0;
  [boothZ - boothLen / 2 + 0.25, boothZ + boothLen / 2 - 0.25].forEach((z) => {
    const t = F.bookshelf({ width: 0.5, height: 1.35, depth: 0.3, shelves: 3, y0: towerY0 });
    t.position.set(ROOM_W / 2 - 0.15, 0, z);
    g.add(t);
  });

  // Far-wall arm: bench + tall bookshelf above it (1.0 m)
  const armBooth = F.boothUnit({ length: 1.0, depth: boothDepth });
  armBooth.rotation.y = Math.PI / 2; // front (local -X) → world +Z (into the room)
  armBooth.position.set(ROOM_W / 2 - boothDepth - 0.5, 0, -ROOM_D / 2 + boothDepth / 2);
  g.add(armBooth);
  const armShelf = F.bookshelf({ width: 1.0, height: 1.35, depth: 0.3, shelves: 3, y0: towerY0 });
  armShelf.rotation.y = Math.PI / 2;
  armShelf.position.set(ROOM_W / 2 - boothDepth - 0.5, 0, -ROOM_D / 2 + 0.15);
  g.add(armShelf);

  // Tall red light column at the L corner
  const column = new THREE.Mesh(new THREE.BoxGeometry(0.08, 1.4, 0.08), F.Materials.redGlow);
  column.position.set(ROOM_W / 2 - boothDepth - 1.12, 1.2, -ROOM_D / 2 + 0.2);
  g.add(column);

  // Tetris lamp near the booth end
  const lamp = F.tetrisLamp();
  lamp.position.set(ROOM_W / 2 - 0.95, 0, 1.45);
  g.add(lamp);

  // Display cabinet on the entrance wall, left of the door
  const cab = F.displayCabinet({ width: 2.15, depth: 0.4, height: 0.95 });
  cab.position.set(-0.45, 0, ROOM_D / 2 - 0.2);
  g.add(cab);

  return g;
}

/* ───────────── lights ───────────── */
function buildLights() {
  const g = new THREE.Group();
  g.add(new THREE.AmbientLight(0xfff4ea, 0.06));

  // Key light from ceiling with soft shadows
  const key = new THREE.SpotLight(0xfff0e4, 22, 9, Math.PI / 3.2, 0.6, 1.6);
  key.position.set(0.4, ROOM_H - 0.1, 0.3);
  key.target.position.set(0, 0, 0);
  key.castShadow = true;
  key.shadow.mapSize.set(2048, 2048);
  key.shadow.bias = -0.00015;
  key.shadow.radius = 4;
  g.add(key, key.target);

  // Down-lights over desks
  [-0.55, 0.95].forEach((z) => {
    const s = new THREE.SpotLight(0xfff3ea, 8, 4, Math.PI / 5, 0.7, 1.5);
    s.position.set(-ROOM_W / 2 + 0.7, ROOM_H - 0.1, z);
    s.target.position.set(-ROOM_W / 2 + 0.5, 0.75, z);
    g.add(s, s.target);
  });

  // Booth wash from above
  const b = new THREE.SpotLight(0xfff3ea, 7, 4, Math.PI / 4.5, 0.7, 1.5);
  b.position.set(ROOM_W / 2 - 0.9, ROOM_H - 0.1, -0.15);
  b.target.position.set(ROOM_W / 2 - 0.4, 0.6, -0.15);
  g.add(b, b.target);

  // Red accent fills
  const redA = new THREE.PointLight(RED, 2.5, 5, 2);
  redA.position.set(-ROOM_W / 2 + 0.5, 1.9, 0.2);
  g.add(redA);
  const redB = new THREE.PointLight(RED, 1.5, 4, 2);
  redB.position.set(ROOM_W / 2 - 0.6, 1.2, -0.15);
  g.add(redB);

  // Daylight from the window
  const winLight = new THREE.RectAreaLight(0xcfe3ff, 2.2, 1.7, 1.1);
  winLight.position.set(ROOM_W / 2 - 0.08, 1.75, -0.15);
  winLight.lookAt(0, 1.1, -0.15);
  g.add(winLight);

  // Warm cove glow
  const cove = new THREE.RectAreaLight(0xffe4c4, 0.55, ROOM_W - 0.8, ROOM_D - 0.8);
  cove.position.set(0, ROOM_H - 0.12, 0);
  cove.lookAt(0, 0, 0);
  g.add(cove);

  return g;
}

scene.add(buildShell(), buildFurniture(), buildLights());

/* ───────────── post-processing ───────────── */
const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));
const bloom = new UnrealBloomPass(new THREE.Vector2(window.innerWidth, window.innerHeight), 0.3, 0.5, 0.9);
composer.addPass(bloom);
composer.addPass(new OutputPass());

flyTo(ENTRANCE_CAM);

/* ───────────── loop ───────────── */
function updateWalk(dt) {
  if (mode !== 'walk' || !walk.isLocked) return;
  const speed = 2.2;
  walkVelocity.x -= walkVelocity.x * 8.0 * dt;
  walkVelocity.z -= walkVelocity.z * 8.0 * dt;
  const dir = new THREE.Vector3(
    Number(walkKeys.right) - Number(walkKeys.left),
    0,
    Number(walkKeys.forward) - Number(walkKeys.back),
  ).normalize();
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
