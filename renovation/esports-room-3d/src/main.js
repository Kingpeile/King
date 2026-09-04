import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { PointerLockControls } from 'three/examples/jsm/controls/PointerLockControls.js';
import { RectAreaLightUniformsLib } from 'three/examples/jsm/lights/RectAreaLightUniformsLib.js';

/**
 * Floor plan (meters), entrance at +Z:
 *  -X left wall  : dual height desks (sit facing left / -X)
 *  +X right wall : 卡座书架 BEHIND the chairs (opposite desks)
 *  -Z top wall   : L-shaped 卡座书架 continuation
 *  +Z bottom     : entrance + display shelf
 */
const ROOM_W = 4.5;
const ROOM_D = 3.85;
const ROOM_H = 2.65;

const RED = 0xff2a36;
const METAL = 0xb8bcc4;
const DARK = 0x16171b;
const FLOOR = 0xc8cacf;

RectAreaLightUniformsLib.init();

const app = document.getElementById('app');
const hint = document.getElementById('hint');

const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
app.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x050506);
scene.fog = new THREE.FogExp2(0x050506, 0.04);

const camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 0.05, 40);

const orbit = new OrbitControls(camera, renderer.domElement);
orbit.enableDamping = true;
orbit.dampingFactor = 0.06;
orbit.minDistance = 1.2;
orbit.maxDistance = 9;
orbit.maxPolarAngle = Math.PI * 0.49;
orbit.target.set(0, 1.05, 0);

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

document.getElementById('btn-orbit').onclick = () => setMode('orbit');
document.getElementById('btn-walk').onclick = () => setMode('walk');
document.getElementById('btn-entrance').onclick = () => {
  setMode('orbit');
  // From door (+Z,+X) looking in: desks left, 卡座 behind chairs on the right
  camera.position.set(1.55, 1.55, 2.45);
  orbit.target.set(-0.2, 1.05, -0.15);
  orbit.update();
};
document.getElementById('btn-overview').onclick = () => {
  setMode('orbit');
  camera.position.set(0.2, 4.6, 0.15);
  orbit.target.set(0.2, 0, 0.15);
  orbit.update();
};

window.addEventListener('keydown', (e) => {
  switch (e.code) {
    case 'KeyW': walkKeys.forward = true; break;
    case 'KeyS': walkKeys.back = true; break;
    case 'KeyA': walkKeys.left = true; break;
    case 'KeyD': walkKeys.right = true; break;
  }
});
window.addEventListener('keyup', (e) => {
  switch (e.code) {
    case 'KeyW': walkKeys.forward = false; break;
    case 'KeyS': walkKeys.back = false; break;
    case 'KeyA': walkKeys.left = false; break;
    case 'KeyD': walkKeys.right = false; break;
  }
});

function mat(opts) {
  return new THREE.MeshStandardMaterial(opts);
}

function box(w, h, d, material, x = 0, y = 0, z = 0) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), material);
  m.position.set(x, y, z);
  m.castShadow = true;
  m.receiveShadow = true;
  return m;
}

function makeLedStrip(length, axis = 'x') {
  const geo =
    axis === 'x' ? new THREE.BoxGeometry(length, 0.018, 0.018)
      : axis === 'y' ? new THREE.BoxGeometry(0.018, length, 0.018)
        : new THREE.BoxGeometry(0.018, 0.018, length);
  const mesh = new THREE.Mesh(geo, mat({
    color: RED,
    emissive: RED,
    emissiveIntensity: 3.2,
    roughness: 0.35,
    metalness: 0.1,
  }));
  return mesh;
}

function makeRoomShell() {
  const group = new THREE.Group();
  const wallMat = mat({ color: METAL, metalness: 0.72, roughness: 0.32 });
  const darkMat = mat({ color: DARK, metalness: 0.4, roughness: 0.55 });
  const floorMat = mat({ color: FLOOR, metalness: 0.55, roughness: 0.18 });
  const ceilingMat = mat({ color: 0xe8e8ea, metalness: 0.05, roughness: 0.85 });

  group.add(box(ROOM_W, 0.06, ROOM_D, floorMat, 0, 0.03, 0));
  group.add(box(ROOM_W, 0.06, ROOM_D, ceilingMat, 0, ROOM_H - 0.03, 0));

  const t = 0.08;
  group.add(box(t, ROOM_H, ROOM_D, wallMat, -ROOM_W / 2 + t / 2, ROOM_H / 2, 0));
  group.add(box(t, ROOM_H, ROOM_D, wallMat, ROOM_W / 2 - t / 2, ROOM_H / 2, 0));
  group.add(box(ROOM_W, ROOM_H, t, wallMat, 0, ROOM_H / 2, -ROOM_D / 2 + t / 2));
  group.add(box(ROOM_W, ROOM_H, t, darkMat, 0, ROOM_H / 2, ROOM_D / 2 - t / 2));

  // Door leaf at bottom-right
  group.add(box(0.06, 2.1, 0.85, mat({ color: 0x1a1a1e, metalness: 0.3, roughness: 0.5 }), ROOM_W / 2 - 0.5, 1.05, ROOM_D / 2 - 0.04));

  const coveY = ROOM_H - 0.12;
  [[-ROOM_W / 2 + 0.12, 0, 'z', ROOM_D - 0.3],
    [ROOM_W / 2 - 0.12, 0, 'z', ROOM_D - 0.3],
    [0, -ROOM_D / 2 + 0.12, 'x', ROOM_W - 0.3],
    [0, ROOM_D / 2 - 0.12, 'x', ROOM_W - 0.3]].forEach(([x, z, axis, len]) => {
    const led = makeLedStrip(len, axis);
    led.position.set(x, coveY, z);
    group.add(led);
  });

  const floorLedL = makeLedStrip(ROOM_D - 0.4, 'z');
  floorLedL.position.set(-ROOM_W / 2 + 0.1, 0.08, 0);
  const floorLedR = makeLedStrip(ROOM_D - 0.4, 'z');
  floorLedR.position.set(ROOM_W / 2 - 0.1, 0.08, 0);
  group.add(floorLedL, floorLedR);

  const rug = new THREE.Mesh(
    new THREE.CylinderGeometry(0.7, 0.7, 0.03, 48),
    mat({ color: 0x2a2b31, roughness: 0.95, metalness: 0 }),
  );
  rug.position.set(0.2, 0.075, -0.15);
  rug.receiveShadow = true;
  group.add(rug);

  return group;
}

function makePegboard(w, h) {
  const g = new THREE.Group();
  g.add(box(0.03, h, w, mat({ color: 0x8f939c, metalness: 0.65, roughness: 0.4 }), 0, 0, 0));
  const holeMat = mat({ color: 0x5c6068, metalness: 0.5, roughness: 0.45 });
  const cols = 14;
  const rows = 10;
  for (let i = 0; i < cols; i++) {
    for (let j = 0; j < rows; j++) {
      const hole = new THREE.Mesh(new THREE.CylinderGeometry(0.018, 0.018, 0.04, 8), holeMat);
      hole.rotation.z = Math.PI / 2;
      hole.position.set(
        0.01,
        -h / 2 + 0.12 + j * ((h - 0.2) / (rows - 1)),
        -w / 2 + 0.12 + i * ((w - 0.2) / (cols - 1)),
      );
      g.add(hole);
    }
  }
  return g;
}

function makeChair() {
  const g = new THREE.Group();
  const cMat = mat({ color: 0x0e0f12, metalness: 0.25, roughness: 0.55 });
  g.add(box(0.48, 0.08, 0.48, cMat, 0, 0.46, 0));
  g.add(box(0.48, 0.55, 0.08, cMat, 0, 0.8, -0.2));
  g.add(box(0.07, 0.42, 0.07, cMat, -0.18, 0.23, -0.15));
  g.add(box(0.07, 0.42, 0.07, cMat, 0.18, 0.23, -0.15));
  g.add(box(0.07, 0.42, 0.07, cMat, -0.18, 0.23, 0.15));
  g.add(box(0.07, 0.42, 0.07, cMat, 0.18, 0.23, 0.15));
  return g;
}

/** Desk along left wall; chair is on +X side of desk so sitter faces -X (wall). */
function makeDeskSetup(z) {
  const g = new THREE.Group();
  const deskMat = mat({ color: 0x111215, metalness: 0.45, roughness: 0.4 });
  const x = -ROOM_W / 2 + 0.95;

  g.add(box(1.5, 0.04, 0.7, deskMat, x, 0.74, z));
  g.add(box(0.06, 0.72, 0.6, deskMat, x - 0.65, 0.36, z));
  g.add(box(0.06, 0.72, 0.6, deskMat, x + 0.65, 0.36, z));

  const glow = makeLedStrip(1.35, 'z');
  glow.position.set(x + 0.28, 0.7, z);
  g.add(glow);

  g.add(box(0.04, 0.38, 0.62, mat({ color: 0x0a0a0c, metalness: 0.5, roughness: 0.35 }), x - 0.28, 1.12, z));
  g.add(box(0.01, 0.32, 0.56, mat({
    color: 0x22060a,
    emissive: RED,
    emissiveIntensity: 0.55,
    roughness: 0.25,
    metalness: 0.1,
  }), x - 0.255, 1.12, z));
  g.add(box(0.08, 0.22, 0.08, deskMat, x - 0.2, 0.88, z));

  const chair = makeChair();
  // Chair behind desk toward room center (+X): sitting faces the left wall
  chair.position.set(x + 0.75, 0, z);
  chair.rotation.y = -Math.PI / 2; // face -X
  g.add(chair);

  return g;
}

/**
 * L-shaped 卡座书架: main run on +X (RIGHT / behind gamers), short run on -Z (TOP).
 * Seat faces toward the desks (−X), so when you sit at PC the booth is at your back.
 */
function makeBoothBookshelfL() {
  const g = new THREE.Group();
  const shell = mat({ color: 0x1b1c21, metalness: 0.35, roughness: 0.45 });
  const cushion = mat({ color: 0xf4f4f6, roughness: 0.9, metalness: 0 });
  const shelfDark = mat({ color: 0x0c0c10, roughness: 0.7, metalness: 0.2 });

  // —— Right wall main booth (behind chairs): depth ~0.72, length ~2.8 spanning mid room ——
  const boothDepth = 0.72;
  const boothLen = 2.8; // 1.6 + part of 1.21 run visually
  const boothX = ROOM_W / 2 - boothDepth / 2;
  const boothZ = -0.15; // centered opposite desks

  // Base cabinets + seat ledge
  g.add(box(boothDepth, 0.48, boothLen, shell, boothX, 0.24, boothZ));
  // Seat cushion facing into room (−X face of unit)
  g.add(box(0.42, 0.1, boothLen - 0.1, cushion, boothX - boothDepth / 2 + 0.24, 0.53, boothZ));
  // Backrest / tall bookshelf spine against wall
  g.add(box(0.28, 1.45, boothLen, shell, boothX + boothDepth / 2 - 0.14, 1.2, boothZ));

  // Open shelf niches with red LED on the tall spine (facing room)
  for (let i = 0; i < 4; i++) {
    const nz = boothZ - boothLen / 2 + 0.35 + i * 0.65;
    g.add(box(0.18, 0.32, 0.5, shelfDark, boothX + 0.05, 1.35, nz));
    const led = makeLedStrip(0.48, 'z');
    led.position.set(boothX - 0.02, 1.2, nz);
    g.add(led);
    // small display objects
    g.add(box(0.1, 0.12, 0.1, mat({
      color: i % 2 ? 0xffffff : RED,
      emissive: i % 2 ? 0x000000 : RED,
      emissiveIntensity: i % 2 ? 0 : 0.9,
      roughness: 0.4,
    }), boothX - 0.05, 1.35, nz));
  }

  // Window + blinds on the RIGHT wall ABOVE the booth (behind computers)
  const glass = box(0.04, 1.15, 2.2, mat({
    color: 0x8fb8d8,
    metalness: 0.1,
    roughness: 0.05,
    transparent: true,
    opacity: 0.35,
  }), ROOM_W / 2 - 0.1, 1.85, boothZ);
  g.add(glass);
  for (let i = 0; i < 14; i++) {
    g.add(box(0.02, 0.03, 2.15, mat({ color: 0x111215, metalness: 0.4, roughness: 0.45 }), ROOM_W / 2 - 0.13, 1.3 + i * 0.08, boothZ));
  }

  // —— Top wall short booth arm (1000mm) —— L corner
  const topLen = 1.0;
  const topZ = -ROOM_D / 2 + boothDepth / 2;
  const topX = ROOM_W / 2 - boothDepth - topLen / 2 + 0.05;
  g.add(box(topLen, 0.48, boothDepth, shell, topX, 0.24, topZ));
  g.add(box(topLen - 0.08, 0.1, 0.42, cushion, topX, 0.53, topZ + boothDepth / 2 - 0.24));
  g.add(box(topLen, 1.45, 0.28, shell, topX, 1.2, topZ - boothDepth / 2 + 0.14));

  const topLed = makeLedStrip(topLen - 0.15, 'x');
  topLed.position.set(topX, 1.55, topZ + 0.05);
  g.add(topLed);

  // Vertical red accent at corner behind chairs
  g.add(box(0.06, 1.8, 0.06, mat({
    color: RED, emissive: RED, emissiveIntensity: 2.6, roughness: 0.3,
  }), boothX - boothDepth / 2 + 0.08, 1.0, boothZ - boothLen / 2 + 0.12));

  return g;
}

function makeDisplayShelf() {
  const g = new THREE.Group();
  const wood = mat({ color: 0x1a1b20, metalness: 0.3, roughness: 0.5 });
  // Entrance wall (+Z), left of door — 2.15 × 0.4
  g.add(box(2.15, 0.9, 0.4, wood, -0.4, 0.45, ROOM_D / 2 - 0.28));
  const led = makeLedStrip(2.0, 'x');
  led.position.set(-0.4, 0.92, ROOM_D / 2 - 0.28);
  g.add(led);

  const accents = [0xff3b45, 0xffffff, 0xffcc33, 0x222222];
  for (let i = 0; i < 6; i++) {
    g.add(box(0.12, 0.16 + (i % 3) * 0.05, 0.12, mat({
      color: accents[i % accents.length],
      emissive: i % 2 === 0 ? RED : 0x000000,
      emissiveIntensity: i % 2 === 0 ? 0.8 : 0,
      roughness: 0.4,
    }), -1.2 + i * 0.32, 1.05, ROOM_D / 2 - 0.28));
  }
  return g;
}

function makeFloatingShelves() {
  const g = new THREE.Group();
  const shelfMat = mat({ color: 0x101114, metalness: 0.4, roughness: 0.4 });
  for (let i = 0; i < 3; i++) {
    const y = 1.55 + i * 0.28;
    const z = -0.85 + i * 0.7;
    g.add(box(0.22, 0.03, 0.7, shelfMat, -ROOM_W / 2 + 0.28, y, z));
    const led = makeLedStrip(0.65, 'z');
    led.position.set(-ROOM_W / 2 + 0.18, y - 0.02, z);
    g.add(led);
  }
  return g;
}

function makeLogo() {
  return box(0.04, 0.45, 0.7, mat({
    color: RED, emissive: RED, emissiveIntensity: 2.8, roughness: 0.35,
  }), -ROOM_W / 2 + 0.12, 1.85, 0.15);
}

function setupLights() {
  scene.add(new THREE.AmbientLight(0xfff2ea, 0.28));
  scene.add(new THREE.HemisphereLight(0xfff5ef, 0x1a1012, 0.45));

  const key = new THREE.DirectionalLight(0xfff0e8, 1.15);
  key.position.set(2.2, 4.2, 2.0);
  key.castShadow = true;
  key.shadow.mapSize.set(2048, 2048);
  key.shadow.camera.near = 0.5;
  key.shadow.camera.far = 16;
  key.shadow.camera.left = -5;
  key.shadow.camera.right = 5;
  key.shadow.camera.top = 5;
  key.shadow.camera.bottom = -5;
  key.shadow.bias = -0.0002;
  scene.add(key);

  scene.add(Object.assign(new THREE.PointLight(RED, 8, 8, 2), { position: new THREE.Vector3(0.2, 2.1, 0) }));

  const deskWash = new THREE.RectAreaLight(0xff4450, 6, 0.12, 3.0);
  deskWash.position.set(-ROOM_W / 2 + 0.2, 2.2, 0.1);
  deskWash.lookAt(-ROOM_W / 2 + 1, 1, 0.1);
  scene.add(deskWash);

  // Light from window behind booth (right wall)
  const windowLight = new THREE.RectAreaLight(0xb7d7ff, 5, 1.1, 2.0);
  windowLight.position.set(ROOM_W / 2 - 0.05, 1.85, -0.15);
  windowLight.lookAt(0, 1.2, -0.15);
  scene.add(windowLight);
}

const room = new THREE.Group();
room.add(makeRoomShell());
room.add(makeBoothBookshelfL());
room.add(makeDisplayShelf());
room.add(makeFloatingShelves());
room.add(makeLogo());

const peg = makePegboard(3.0, 1.5);
peg.position.set(-ROOM_W / 2 + 0.1, 1.55, 0.2);
room.add(peg);

// Two desks along left wall (plan: each 1.5m)
room.add(makeDeskSetup(-0.55));
room.add(makeDeskSetup(0.95));

room.add(box(0.22, 0.48, 0.42, mat({
  color: 0x0c0d10,
  metalness: 0.5,
  roughness: 0.35,
  emissive: RED,
  emissiveIntensity: 0.35,
}), -ROOM_W / 2 + 0.55, 0.98, 1.55));

scene.add(room);
setupLights();

camera.position.set(1.55, 1.55, 2.45);
orbit.target.set(-0.2, 1.05, -0.15);
orbit.update();

function updateWalk(dt) {
  if (mode !== 'walk' || !walk.isLocked) return;
  const speed = 2.2;
  walkVelocity.x -= walkVelocity.x * 8.0 * dt;
  walkVelocity.z -= walkVelocity.z * 8.0 * dt;
  const dir = new THREE.Vector3();
  dir.z = Number(walkKeys.forward) - Number(walkKeys.back);
  dir.x = Number(walkKeys.right) - Number(walkKeys.left);
  dir.normalize();
  if (walkKeys.forward || walkKeys.back) walkVelocity.z -= dir.z * speed * dt;
  if (walkKeys.left || walkKeys.right) walkVelocity.x -= dir.x * speed * dt;
  walk.moveRight(-walkVelocity.x * dt * 60);
  walk.moveForward(-walkVelocity.z * dt * 60);
  camera.position.y = 1.55;
  camera.position.x = THREE.MathUtils.clamp(camera.position.x, -ROOM_W / 2 + 0.45, ROOM_W / 2 - 0.85);
  camera.position.z = THREE.MathUtils.clamp(camera.position.z, -ROOM_D / 2 + 0.85, ROOM_D / 2 - 0.4);
}

function animate() {
  requestAnimationFrame(animate);
  const dt = Math.min(clock.getDelta(), 0.05);
  if (mode === 'orbit') orbit.update();
  else updateWalk(dt);
  renderer.render(scene, camera);
}
animate();

window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});
