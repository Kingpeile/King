import * as THREE from 'three';

function canvas(w, h) {
  const c = document.createElement('canvas');
  c.width = w;
  c.height = h;
  return [c, c.getContext('2d')];
}

function toTexture(c, { repeat = [1, 1], srgb = true, clamp = false } = {}) {
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = clamp ? THREE.ClampToEdgeWrapping : THREE.RepeatWrapping;
  t.repeat.set(repeat[0], repeat[1]);
  t.anisotropy = 8;
  if (srgb) t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

let seed = 1337;
function rand() {
  seed = (seed * 16807) % 2147483647;
  return (seed - 1) / 2147483646;
}
export function resetSeed() { seed = 1337; }

/** Brushed aluminium: horizontal streaks over a base tone. */
export function brushedMetal(repeat = [2, 1], base = '#b9bcc3', streak = 150) {
  const [c, g] = canvas(512, 512);
  g.fillStyle = base;
  g.fillRect(0, 0, 512, 512);
  for (let i = 0; i < 2600; i++) {
    const y = rand() * 512;
    const l = 40 + rand() * 300;
    const x = rand() * 512;
    const v = streak + Math.floor(rand() * 70);
    g.strokeStyle = `rgba(${v},${v + 3},${v + 8},${0.10 + rand() * 0.25})`;
    g.lineWidth = 1;
    g.beginPath();
    g.moveTo(x, y);
    g.lineTo(x + l, y + (rand() - 0.5) * 1.5);
    g.stroke();
  }
  return { map: toTexture(c, { repeat }) };
}

/** Large-format polished tiles with thin grout and marble veins. */
export function floorTiles(repeat = [3, 2.6], base = '#c9cbd0', grout = '#9a9ca3', vein = '150,152,160') {
  const [c, g] = canvas(1024, 1024);
  g.fillStyle = base;
  g.fillRect(0, 0, 1024, 1024);
  for (let i = 0; i < 90; i++) {
    g.strokeStyle = `rgba(${vein},${0.05 + rand() * 0.12})`;
    g.lineWidth = 1 + rand() * 2;
    g.beginPath();
    let x = rand() * 1024;
    let y = rand() * 1024;
    g.moveTo(x, y);
    for (let k = 0; k < 8; k++) {
      x += (rand() - 0.5) * 220;
      y += (rand() - 0.5) * 220;
      g.lineTo(x, y);
    }
    g.stroke();
  }
  g.fillStyle = grout;
  g.fillRect(0, 508, 1024, 8);
  g.fillRect(508, 0, 8, 1024);
  const [rc, rg] = canvas(1024, 1024);
  rg.fillStyle = '#404040';
  rg.fillRect(0, 0, 1024, 1024);
  rg.fillStyle = '#c0c0c0';
  rg.fillRect(0, 508, 1024, 8);
  rg.fillRect(508, 0, 8, 1024);
  return { map: toTexture(c, { repeat }), roughnessMap: toTexture(rc, { repeat, srgb: false }) };
}

/** Pegboard with holes, plus bump map. */
export function pegboard(repeat = [4, 2], base = '#8d9199', hole = '#3a3d44') {
  const [c, g] = canvas(512, 512);
  g.fillStyle = base;
  g.fillRect(0, 0, 512, 512);
  const [bc, bg] = canvas(512, 512);
  bg.fillStyle = '#ffffff';
  bg.fillRect(0, 0, 512, 512);
  const step = 64;
  for (let y = step / 2; y < 512; y += step) {
    for (let x = step / 2; x < 512; x += step) {
      g.fillStyle = hole;
      g.beginPath();
      g.arc(x, y, 9, 0, Math.PI * 2);
      g.fill();
      bg.fillStyle = '#000000';
      bg.beginPath();
      bg.arc(x, y, 9, 0, Math.PI * 2);
      bg.fill();
    }
  }
  return { map: toTexture(c, { repeat }), bumpMap: toTexture(bc, { repeat, srgb: false }) };
}

/** Red/black gaming wallpaper with WE mark and HUD lines. */
export function screenWallpaper() {
  const [c, g] = canvas(1024, 576);
  const grad = g.createLinearGradient(0, 0, 1024, 576);
  grad.addColorStop(0, '#2a0409');
  grad.addColorStop(0.55, '#7a0a14');
  grad.addColorStop(1, '#14040a');
  g.fillStyle = grad;
  g.fillRect(0, 0, 1024, 576);
  g.strokeStyle = 'rgba(255,255,255,0.08)';
  g.lineWidth = 2;
  for (let i = 0; i < 12; i++) {
    g.beginPath();
    g.moveTo(rand() * 1024, 0);
    g.lineTo(rand() * 1024, 576);
    g.stroke();
  }
  g.font = 'bold 260px "Arial Black", Arial, sans-serif';
  g.textAlign = 'center';
  g.textBaseline = 'middle';
  g.shadowColor = '#ff2a36';
  g.shadowBlur = 60;
  g.fillStyle = '#ff3b45';
  g.fillText('WE', 512, 300);
  g.shadowBlur = 0;
  g.fillStyle = 'rgba(255,255,255,0.75)';
  g.font = '28px Arial';
  g.fillText('TEAM WE · ESPORTS', 512, 470);
  return toTexture(c, { clamp: true });
}

/** Mario-style sky wallpaper: blue gradient, clouds, hills, bricks, ? blocks. */
export function marioWallpaper() {
  const [c, g] = canvas(1024, 576);
  const sky = g.createLinearGradient(0, 0, 0, 576);
  sky.addColorStop(0, '#5c94fc');
  sky.addColorStop(1, '#9ec5ff');
  g.fillStyle = sky;
  g.fillRect(0, 0, 1024, 576);
  // clouds
  g.fillStyle = '#ffffff';
  for (let i = 0; i < 7; i++) {
    const x = 60 + i * 150 + rand() * 40;
    const y = 60 + rand() * 120;
    for (const [dx, dy, r] of [[0, 0, 28], [30, -8, 34], [62, 0, 28], [30, 14, 30]]) {
      g.beginPath();
      g.arc(x + dx, y + dy, r, 0, Math.PI * 2);
      g.fill();
    }
  }
  // hills
  g.fillStyle = '#3cb043';
  for (let i = 0; i < 4; i++) {
    g.beginPath();
    g.arc(100 + i * 300, 480, 110, Math.PI, 0);
    g.fill();
  }
  // ground bricks
  g.fillStyle = '#c84c0c';
  g.fillRect(0, 496, 1024, 80);
  g.strokeStyle = '#7a2a00';
  g.lineWidth = 3;
  for (let x = 0; x < 1024; x += 64) {
    g.strokeRect(x, 496, 64, 40);
    g.strokeRect(x + 32, 536, 64, 40);
  }
  // ? blocks row
  for (let i = 0; i < 3; i++) drawQuestion(g, 420 + i * 72, 230, 64);
  g.font = 'bold 44px "Arial Black", Arial, sans-serif';
  g.fillStyle = '#ffffff';
  g.textAlign = 'center';
  g.strokeStyle = '#1b1b1b';
  g.lineWidth = 6;
  g.strokeText('LET\'S-A GO!', 512, 400);
  g.fillText('LET\'S-A GO!', 512, 400);
  return toTexture(c, { clamp: true });
}

function drawQuestion(g, x, y, s) {
  g.fillStyle = '#f7b515';
  g.fillRect(x, y, s, s);
  g.fillStyle = '#8a5200';
  g.fillRect(x, y, s, s * 0.06);
  g.fillRect(x, y, s * 0.06, s);
  g.fillStyle = '#c47a06';
  g.fillRect(x + s * 0.94, y, s * 0.06, s);
  g.fillRect(x, y + s * 0.94, s, s * 0.06);
  for (const [cx, cy] of [[0.12, 0.12], [0.88, 0.12], [0.12, 0.88], [0.88, 0.88]]) {
    g.fillStyle = '#8a5200';
    g.fillRect(x + s * cx - s * 0.04, y + s * cy - s * 0.04, s * 0.08, s * 0.08);
  }
  g.fillStyle = '#ffffff';
  g.font = `bold ${Math.floor(s * 0.72)}px "Arial Black", Arial, sans-serif`;
  g.textAlign = 'center';
  g.textBaseline = 'middle';
  g.fillText('?', x + s / 2, y + s / 2 + s * 0.04);
}

/** Question block face. */
export function questionBlock() {
  const [c, g] = canvas(256, 256);
  drawQuestion(g, 0, 0, 256);
  return toTexture(c, { clamp: true });
}

/** Brick block face. */
export function brickBlock() {
  const [c, g] = canvas(256, 256);
  g.fillStyle = '#c84c0c';
  g.fillRect(0, 0, 256, 256);
  g.fillStyle = '#7a2a00';
  g.fillRect(0, 60, 256, 8);
  g.fillRect(0, 124, 256, 8);
  g.fillRect(0, 188, 256, 8);
  g.fillRect(0, 0, 256, 6);
  g.fillRect(0, 250, 256, 6);
  g.fillRect(124, 0, 8, 64);
  g.fillRect(60, 64, 8, 64);
  g.fillRect(188, 64, 8, 64);
  g.fillRect(124, 128, 8, 64);
  g.fillRect(60, 192, 8, 64);
  g.fillRect(188, 192, 8, 64);
  return toTexture(c, { clamp: true });
}

/** Mushroom cap: red with white spots. */
export function mushroomCap() {
  const [c, g] = canvas(512, 256);
  g.fillStyle = '#e4291b';
  g.fillRect(0, 0, 512, 256);
  g.fillStyle = '#ffffff';
  for (const [x, y, r] of [[80, 70, 40], [250, 40, 46], [420, 80, 40], [160, 170, 34], [340, 170, 34]]) {
    g.beginPath();
    g.arc(x, y, r, 0, Math.PI * 2);
    g.fill();
  }
  return toTexture(c, { repeat: [1, 1] });
}

/** Outdoor view: sky gradient, distant trees, lawn. */
export function windowView() {
  const [c, g] = canvas(1024, 768);
  const sky = g.createLinearGradient(0, 0, 0, 480);
  sky.addColorStop(0, '#9fc6ea');
  sky.addColorStop(1, '#e8f0f7');
  g.fillStyle = sky;
  g.fillRect(0, 0, 1024, 480);
  g.fillStyle = '#7fa96b';
  g.fillRect(0, 470, 1024, 300);
  for (let i = 0; i < 26; i++) {
    const x = rand() * 1024;
    const r = 50 + rand() * 90;
    const y = 470 - r * 0.45;
    const gshade = 60 + Math.floor(rand() * 60);
    g.fillStyle = `rgb(${gshade - 20},${gshade + 50},${gshade - 10})`;
    g.beginPath();
    g.arc(x, y, r, 0, Math.PI * 2);
    g.fill();
  }
  g.fillStyle = '#5f8d4f';
  g.fillRect(0, 540, 1024, 230);
  return toTexture(c);
}

/** Glowing wall logo text on transparent background. */
export function wallLogo(text = 'WE', color = '#ff2a36') {
  const [c, g] = canvas(1024, 512);
  g.clearRect(0, 0, 1024, 512);
  g.font = 'bold 340px "Arial Black", Arial, sans-serif';
  g.textAlign = 'center';
  g.textBaseline = 'middle';
  g.shadowColor = color;
  g.shadowBlur = 40;
  g.fillStyle = color;
  g.fillText(text, 512, 256);
  return toTexture(c, { clamp: true });
}

/** Keyboard: rows of keycaps with backlight bleed. */
export function keyboardTop(base = '#0d0e11', cap = '#1b1c21', glow = 'rgba(255,42,54,0.35)') {
  const [c, g] = canvas(512, 192);
  g.fillStyle = base;
  g.fillRect(0, 0, 512, 192);
  const rows = 5;
  const cols = 16;
  const kw = 512 / cols;
  const kh = 192 / rows;
  for (let r = 0; r < rows; r++) {
    for (let k = 0; k < cols; k++) {
      g.fillStyle = glow;
      g.fillRect(k * kw + 2, r * kh + 2, kw - 4, kh - 4);
      g.fillStyle = cap;
      g.fillRect(k * kw + 5, r * kh + 5, kw - 10, kh - 10);
    }
  }
  return toTexture(c, { clamp: true });
}

/** Fabric-ish plush rug. */
export function rugFabric(repeat = [4, 4], base = '#2a2b31', lo = 30) {
  const [c, g] = canvas(256, 256);
  g.fillStyle = base;
  g.fillRect(0, 0, 256, 256);
  for (let i = 0; i < 8000; i++) {
    const v = lo + Math.floor(rand() * 30);
    g.fillStyle = `rgb(${v},${v + 1},${v + 5})`;
    g.fillRect(rand() * 256, rand() * 256, 2, 2);
  }
  return toTexture(c, { repeat });
}
