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
export function wallLogo(text = 'WE', color = '#ff2a36', fontPx = 340) {
  const [c, g] = canvas(1024, 512);
  g.clearRect(0, 0, 1024, 512);
  g.font = `italic 900 ${fontPx}px "Arial Black", Arial, sans-serif`;
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

/* ────────────────────────────────────────────
   Ferrari / Rosso Corsa set
──────────────────────────────────────────── */

/** 2x2 twill carbon fibre weave. */
export function carbonFiber(repeat = [8, 8]) {
  const [c, g] = canvas(256, 256);
  const cell = 32;
  for (let y = 0; y < 256; y += cell) {
    for (let x = 0; x < 256; x += cell) {
      const horiz = ((x / cell + y / cell) % 2) === 0;
      const grad = horiz ? g.createLinearGradient(x, y, x, y + cell) : g.createLinearGradient(x, y, x + cell, y);
      grad.addColorStop(0, '#0b0b0d');
      grad.addColorStop(0.5, horiz ? '#3d3f46' : '#26282d');
      grad.addColorStop(1, '#0b0b0d');
      g.fillStyle = grad;
      g.fillRect(x, y, cell, cell);
      g.strokeStyle = 'rgba(255,255,255,0.06)';
      g.lineWidth = 1;
      for (let k = 3; k < cell; k += 5) {
        g.beginPath();
        if (horiz) { g.moveTo(x, y + k); g.lineTo(x + cell, y + k); } else { g.moveTo(x + k, y); g.lineTo(x + k, y + cell); }
        g.stroke();
      }
    }
  }
  return { map: toTexture(c, { repeat }) };
}

function drawCarSide(g, L, color) {
  const s = L / 600;
  g.scale(s, s);
  g.fillStyle = color;
  g.beginPath();
  g.moveTo(8, 165);
  g.lineTo(4, 125);
  g.quadraticCurveTo(10, 100, 70, 96);
  g.quadraticCurveTo(150, 84, 215, 50);
  g.quadraticCurveTo(290, 30, 360, 46);
  g.quadraticCurveTo(440, 72, 505, 98);
  g.quadraticCurveTo(570, 108, 596, 138);
  g.lineTo(598, 165);
  g.closePath();
  g.fill();
  const hl = g.createLinearGradient(0, 40, 0, 165);
  hl.addColorStop(0, 'rgba(255,255,255,0.28)');
  hl.addColorStop(0.55, 'rgba(255,255,255,0)');
  g.fillStyle = hl;
  g.fill();
  g.fillStyle = '#0c0c10';
  g.beginPath();
  g.moveTo(228, 58);
  g.quadraticCurveTo(290, 40, 355, 54);
  g.quadraticCurveTo(420, 76, 468, 96);
  g.lineTo(242, 96);
  g.quadraticCurveTo(205, 92, 228, 58);
  g.fill();
  for (const x of [125, 480]) {
    g.fillStyle = '#050000';
    g.beginPath(); g.arc(x, 160, 48, 0, Math.PI * 2); g.fill();
    g.fillStyle = '#111114';
    g.beginPath(); g.arc(x, 165, 42, 0, Math.PI * 2); g.fill();
    g.fillStyle = '#8d8f95';
    g.beginPath(); g.arc(x, 165, 26, 0, Math.PI * 2); g.fill();
    g.strokeStyle = '#3a3a3f';
    g.lineWidth = 4;
    for (let k = 0; k < 5; k++) {
      const a = (k / 5) * Math.PI * 2;
      g.beginPath(); g.moveTo(x, 165); g.lineTo(x + Math.cos(a) * 24, 165 + Math.sin(a) * 24); g.stroke();
    }
    g.fillStyle = '#2a2a2e';
    g.beginPath(); g.arc(x, 165, 8, 0, Math.PI * 2); g.fill();
  }
  g.fillStyle = '#ffe9a8';
  g.beginPath(); g.ellipse(560, 122, 22, 7, -0.25, 0, Math.PI * 2); g.fill();
  g.fillStyle = '#ff3b3b';
  g.fillRect(6, 118, 22, 10);
}

/** Monitor wallpaper: red GT silhouette, speed lines, ROSSO CORSA wordmark. */
export function ferrariWallpaper() {
  const [c, g] = canvas(1024, 576);
  const bg = g.createRadialGradient(512, 300, 60, 512, 300, 720);
  bg.addColorStop(0, '#5a0006');
  bg.addColorStop(0.6, '#1a0002');
  bg.addColorStop(1, '#050000');
  g.fillStyle = bg;
  g.fillRect(0, 0, 1024, 576);
  g.strokeStyle = 'rgba(255,255,255,0.07)';
  g.lineWidth = 2;
  for (let i = 0; i < 18; i++) {
    const y = 120 + rand() * 340;
    g.beginPath(); g.moveTo(0, y); g.lineTo(200 + rand() * 700, y); g.stroke();
  }
  g.save();
  g.translate(212, 220);
  drawCarSide(g, 600, '#e40000');
  g.restore();
  g.font = 'italic 900 64px "Arial Black", Arial, sans-serif';
  g.textAlign = 'center';
  g.fillStyle = '#ffffff';
  g.fillText('ROSSO CORSA', 512, 500);
  g.font = '24px Arial';
  g.fillStyle = '#ffd400';
  g.fillText('GAMING ROOM  ·  SCUDERIA EDITION', 512, 540);
  return toTexture(c, { clamp: true });
}

/** Yellow shield emblem with tricolour band (transparent background). */
export function ferrariEmblem() {
  const [c, g] = canvas(512, 640);
  g.clearRect(0, 0, 512, 640);
  const shield = () => {
    g.beginPath();
    g.moveTo(40, 30);
    g.lineTo(472, 30);
    g.lineTo(472, 330);
    g.quadraticCurveTo(472, 520, 256, 620);
    g.quadraticCurveTo(40, 520, 40, 330);
    g.closePath();
  };
  shield();
  g.fillStyle = '#ffd400';
  g.fill();
  g.save();
  shield();
  g.clip();
  g.fillStyle = '#009246'; g.fillRect(40, 30, 144, 74);
  g.fillStyle = '#ffffff'; g.fillRect(184, 30, 144, 74);
  g.fillStyle = '#ce2b37'; g.fillRect(328, 30, 144, 74);
  g.restore();
  shield();
  g.lineWidth = 16;
  g.strokeStyle = '#111111';
  g.stroke();
  g.fillStyle = '#111111';
  g.font = 'italic 900 220px "Arial Black", Arial, sans-serif';
  g.textAlign = 'center';
  g.textBaseline = 'middle';
  g.fillText('SF', 256, 380);
  return toTexture(c, { clamp: true });
}

/** Dusk city skyline for the bay window backdrop. */
export function skylineDusk() {
  const [c, g] = canvas(2048, 1024);
  const sky = g.createLinearGradient(0, 0, 0, 700);
  sky.addColorStop(0, '#070b1e');
  sky.addColorStop(0.45, '#2a2250');
  sky.addColorStop(0.8, '#b0456a');
  sky.addColorStop(1, '#ffa35c');
  g.fillStyle = sky;
  g.fillRect(0, 0, 2048, 1024);
  for (let i = 0; i < 260; i++) {
    g.globalAlpha = 0.3 + rand() * 0.7;
    g.fillStyle = '#ffffff';
    g.fillRect(rand() * 2048, rand() * 380, 2, 2);
  }
  g.globalAlpha = 1;
  g.fillStyle = '#fff4d6';
  g.beginPath(); g.arc(1660, 170, 46, 0, Math.PI * 2); g.fill();
  const horizon = 700;
  g.fillStyle = '#1a1830';
  for (let x = 0; x < 2048;) {
    const w = 40 + rand() * 90;
    const h = 120 + rand() * 260;
    g.fillRect(x, horizon - h, w, h + 40);
    x += w + 4 + rand() * 20;
  }
  for (let x = -20; x < 2048;) {
    const w = 70 + rand() * 140;
    const h = 200 + rand() * 420;
    const top = horizon + 60 - h;
    g.fillStyle = '#0b0c16';
    g.fillRect(x, top, w, h + 300);
    for (let wy = top + 14; wy < horizon + 40; wy += 18) {
      for (let wx = x + 8; wx < x + w - 10; wx += 16) {
        if (rand() > 0.45) {
          g.fillStyle = rand() > 0.85 ? 'rgba(255,120,90,0.9)' : `rgba(255,${200 + Math.floor(rand() * 40)},${140 + Math.floor(rand() * 60)},${0.5 + rand() * 0.5})`;
          g.fillRect(wx, wy, 7, 10);
        }
      }
    }
    if (rand() > 0.6) {
      g.fillStyle = '#ff2a2a';
      g.fillRect(x + w / 2 - 2, top - 30, 4, 30);
      g.beginPath(); g.arc(x + w / 2, top - 32, 5, 0, Math.PI * 2); g.fill();
    }
    x += w + 6 + rand() * 30;
  }
  const hz = g.createLinearGradient(0, 760, 0, 1024);
  hz.addColorStop(0, 'rgba(10,8,20,0)');
  hz.addColorStop(1, 'rgba(5,4,10,1)');
  g.fillStyle = hz;
  g.fillRect(0, 760, 2048, 264);
  return toTexture(c, { clamp: true });
}

/** Charcoal rug with twin racing stripes (stripes run along V). */
export function rugStripes(base = '#22232a', lo = 26) {
  const [c, g] = canvas(512, 768);
  g.fillStyle = base;
  g.fillRect(0, 0, 512, 768);
  for (let i = 0; i < 14000; i++) {
    const v = lo + Math.floor(rand() * 26);
    g.fillStyle = `rgb(${v},${v},${v + 4})`;
    g.fillRect(rand() * 512, rand() * 768, 2, 2);
  }
  g.fillStyle = '#c40010';
  g.fillRect(196, 0, 50, 768);
  g.fillRect(266, 0, 50, 768);
  g.fillStyle = '#ffd400';
  g.fillRect(250, 0, 12, 768);
  g.strokeStyle = '#c40010';
  g.lineWidth = 10;
  g.strokeRect(14, 14, 484, 740);
  return toTexture(c, { clamp: true });
}

/** Wired (夹丝) safety glass: faint tint with a fine wire grid; alpha in the map. */
export function wireGlass() {
  const [c, g] = canvas(256, 256);
  g.clearRect(0, 0, 256, 256);
  g.fillStyle = 'rgba(210,225,235,0.30)';
  g.fillRect(0, 0, 256, 256);
  g.strokeStyle = 'rgba(40,40,45,0.85)';
  g.lineWidth = 2;
  for (let i = 0; i <= 256; i += 32) {
    g.beginPath(); g.moveTo(i, 0); g.lineTo(i, 256); g.stroke();
    g.beginPath(); g.moveTo(0, i); g.lineTo(256, i); g.stroke();
  }
  return toTexture(c, { repeat: [3, 7] });
}
