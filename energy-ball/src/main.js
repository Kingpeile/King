import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import GUI from 'lil-gui';

// ─── Simplex noise (Stefan Gustavson) ────────────────────────────────────────
const NOISE_GLSL = /* glsl */`
vec3 mod289(vec3 x){ return x - floor(x*(1./289.))*289.; }
vec4 mod289(vec4 x){ return x - floor(x*(1./289.))*289.; }
vec4 permute(vec4 x){ return mod289(((x*34.)+1.)*x); }
vec4 taylorInvSqrt(vec4 r){ return 1.79284291400159 - 0.85373472095314*r; }

float snoise(vec3 v){
  const vec2 C = vec2(1./6., 1./3.);
  const vec4 D = vec4(0., .5, 1., 2.);
  vec3 i  = floor(v + dot(v, C.yyy));
  vec3 x0 = v - i + dot(i, C.xxx);
  vec3 g  = step(x0.yzx, x0.xyz);
  vec3 l  = 1. - g;
  vec3 i1 = min(g.xyz, l.zxy);
  vec3 i2 = max(g.xyz, l.zxy);
  vec3 x1 = x0 - i1 + C.xxx;
  vec3 x2 = x0 - i2 + C.yyy;
  vec3 x3 = x0 - D.yyy;
  i = mod289(i);
  vec4 p = permute(permute(permute(
    i.z + vec4(0., i1.z, i2.z, 1.))
    + i.y + vec4(0., i1.y, i2.y, 1.))
    + i.x + vec4(0., i1.x, i2.x, 1.));
  float n_ = .142857142857;
  vec3  ns = n_ * D.wyz - D.xzx;
  vec4 j  = p - 49. * floor(p * ns.z * ns.z);
  vec4 x_ = floor(j * ns.z);
  vec4 y_ = floor(j - 7. * x_);
  vec4 x  = x_*ns.x + ns.yyyy;
  vec4 y  = y_*ns.x + ns.yyyy;
  vec4 h  = 1. - abs(x) - abs(y);
  vec4 b0 = vec4(x.xy, y.xy);
  vec4 b1 = vec4(x.zw, y.zw);
  vec4 s0 = floor(b0)*2.+1.;
  vec4 s1 = floor(b1)*2.+1.;
  vec4 sh = -step(h, vec4(0.));
  vec4 a0 = b0.xzyw + s0.xzyw*sh.xxyy;
  vec4 a1 = b1.xzyw + s1.xzyw*sh.zzww;
  vec3 p0 = vec3(a0.xy, h.x);
  vec3 p1 = vec3(a0.zw, h.y);
  vec3 p2 = vec3(a1.xy, h.z);
  vec3 p3 = vec3(a1.zw, h.w);
  vec4 norm = taylorInvSqrt(vec4(dot(p0,p0),dot(p1,p1),dot(p2,p2),dot(p3,p3)));
  p0*=norm.x; p1*=norm.y; p2*=norm.z; p3*=norm.w;
  vec4 m = max(.6 - vec4(dot(x0,x0),dot(x1,x1),dot(x2,x2),dot(x3,x3)), 0.);
  m = m*m;
  return 42. * dot(m*m, vec4(dot(p0,x0),dot(p1,x1),dot(p2,x2),dot(p3,x3)));
}
`;

// ─── Energy ball vertex shader ────────────────────────────────────────────────
const ballVert = /* glsl */`
${NOISE_GLSL}

uniform float uTime;
uniform float uSpeed;
uniform float uDistortion;

varying vec3  vWorldNormal;
varying vec3  vWorldPos;
varying float vNoise;

void main(){
  float t = uTime * uSpeed;

  // two octaves of noise for rich surface flow
  float n1 = snoise(position * 1.8 + vec3(t*0.30, t*0.22, t*0.18));
  float n2 = snoise(position * 3.6 + vec3(t*0.55, t*0.40, t*0.35));
  float n3 = snoise(position * 7.0 + vec3(t*0.90, t*0.70, t*0.60));
  float noise = n1*0.60 + n2*0.28 + n3*0.12;

  vNoise = noise;

  vec3 displaced = position + normal * noise * uDistortion;

  // world-space outputs for Fresnel
  vec4 worldPos    = modelMatrix * vec4(displaced, 1.0);
  vWorldPos        = worldPos.xyz;
  vWorldNormal     = normalize(mat3(modelMatrix) * normal);

  gl_Position = projectionMatrix * viewMatrix * worldPos;
}
`;

// ─── Energy ball fragment shader ─────────────────────────────────────────────
const ballFrag = /* glsl */`
uniform float uIntensity;
uniform vec3  uColor1;
uniform vec3  uColor2;
uniform float uTime;

varying vec3  vWorldNormal;
varying vec3  vWorldPos;
varying float vNoise;

void main(){
  vec3 viewDir = normalize(cameraPosition - vWorldPos);
  float NdotV  = max(dot(vWorldNormal, viewDir), 0.0);

  // Fresnel rim glow
  float fresnel = pow(1.0 - NdotV, 3.5);

  // base colour from noise + time drift
  float t = vNoise * 0.5 + 0.5;
  vec3 base = mix(uColor1, uColor2, t);

  // pulsing core brightness
  float pulse = 0.85 + 0.15 * sin(uTime * 2.3);

  // inner body: brighter at centre, dimmer at rim
  vec3 body = base * (0.4 + 0.6 * (1.0 - fresnel)) * pulse;

  // rim: saturated color2 halo
  vec3 rim  = uColor2 * fresnel * 2.5;

  // specular-style highlight
  vec3 halfV   = normalize(viewDir + vec3(0.577, 0.577, 0.577));
  float spec   = pow(max(dot(vWorldNormal, halfV), 0.0), 32.0);
  vec3 specCol = mix(uColor1, vec3(1.0), 0.5) * spec * 0.8;

  vec3 final = (body + rim + specCol) * uIntensity;
  gl_FragColor = vec4(final, 1.0);
}
`;

// ─── Particle vertex shader ───────────────────────────────────────────────────
const particleVert = /* glsl */`
uniform float uTime;
uniform float uSpeed;

attribute float aAngle;
attribute float aRadius;
attribute float aY;
attribute float aOrbSpeed;
attribute float aSize;
attribute float aPhase;

varying float vAlpha;
varying float vT;

void main(){
  float angle = aAngle + uTime * uSpeed * aOrbSpeed;
  vec3 pos = vec3(cos(angle) * aRadius, aY + sin(uTime * 0.8 + aPhase) * 0.08, sin(angle) * aRadius);

  vec4 mvPos = modelViewMatrix * vec4(pos, 1.0);
  gl_PointSize = aSize * (280.0 / -mvPos.z);
  gl_Position  = projectionMatrix * mvPos;

  vAlpha = 0.35 + 0.65 * abs(sin(uTime * 1.2 + aPhase));
  vT     = 0.5  + 0.5  * sin(aAngle * 2.0 + uTime * uSpeed * 0.5);
}
`;

// ─── Particle fragment shader ─────────────────────────────────────────────────
const particleFrag = /* glsl */`
uniform vec3 uColor1;
uniform vec3 uColor2;

varying float vAlpha;
varying float vT;

void main(){
  vec2  uv = gl_PointCoord - 0.5;
  float d  = length(uv) * 2.0;
  if(d > 1.0) discard;

  float soft  = 1.0 - smoothstep(0.3, 1.0, d);
  float alpha = soft * vAlpha;

  vec3 col = mix(uColor1, uColor2, vT);
  // bright core
  col = mix(col, vec3(1.0), (1.0 - d) * 0.4);

  gl_FragColor = vec4(col, alpha);
}
`;

// ─── Params ───────────────────────────────────────────────────────────────────
const params = {
  speed:         0.50,
  distortion:    0.14,
  intensity:     1.60,
  color1:        '#2211cc',
  color2:        '#cc22ff',
  bloomStrength: 1.40,
  bloomRadius:   0.45,
  bloomThreshold:0.05,
};

// ─── Renderer ─────────────────────────────────────────────────────────────────
const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
renderer.outputColorSpace = THREE.SRGBColorSpace;
document.body.appendChild(renderer.domElement);

// ─── Scene / camera ───────────────────────────────────────────────────────────
const scene  = new THREE.Scene();
scene.background = new THREE.Color(0x020008);

const camera = new THREE.PerspectiveCamera(55, innerWidth / innerHeight, 0.1, 100);
camera.position.set(0, 0.5, 4.2);

// ─── Controls ─────────────────────────────────────────────────────────────────
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping   = true;
controls.dampingFactor   = 0.06;
controls.minDistance     = 2.0;
controls.maxDistance     = 10.0;

// ─── Energy ball ─────────────────────────────────────────────────────────────
const ballGeo = new THREE.SphereGeometry(1, 128, 128);

const ballUniforms = {
  uTime:        { value: 0 },
  uSpeed:       { value: params.speed },
  uDistortion:  { value: params.distortion },
  uIntensity:   { value: params.intensity },
  uColor1:      { value: new THREE.Color(params.color1) },
  uColor2:      { value: new THREE.Color(params.color2) },
};

const ballMat = new THREE.ShaderMaterial({
  vertexShader:   ballVert,
  fragmentShader: ballFrag,
  uniforms:       ballUniforms,
});

const ball = new THREE.Mesh(ballGeo, ballMat);
scene.add(ball);

// ─── Particles ────────────────────────────────────────────────────────────────
const COUNT = 4000;

const aAngle    = new Float32Array(COUNT);
const aRadius   = new Float32Array(COUNT);
const aY        = new Float32Array(COUNT);
const aOrbSpeed = new Float32Array(COUNT);
const aSize     = new Float32Array(COUNT);
const aPhase    = new Float32Array(COUNT);

for (let i = 0; i < COUNT; i++) {
  aAngle[i]  = Math.random() * Math.PI * 2;
  aPhase[i]  = Math.random() * Math.PI * 2;

  // Three bands: tight inner halo, mid ring, sparse outer cloud
  const band = Math.random();
  if (band < 0.40) {
    aRadius[i]   = 1.25 + Math.random() * 0.18;
    aY[i]        = (Math.random() - 0.5) * 0.25;
    aSize[i]     = 1.5 + Math.random() * 2.0;
  } else if (band < 0.75) {
    aRadius[i]   = 1.55 + Math.random() * 0.28;
    aY[i]        = (Math.random() - 0.5) * 0.65;
    aSize[i]     = 1.2 + Math.random() * 1.8;
  } else {
    aRadius[i]   = 1.85 + Math.random() * 0.55;
    aY[i]        = (Math.random() - 0.5) * 1.40;
    aSize[i]     = 0.8 + Math.random() * 1.2;
  }

  // random direction orbit
  aOrbSpeed[i] = (0.25 + Math.random() * 0.75) * (Math.random() < 0.5 ? 1 : -1);
}

// dummy position buffer (positions computed in vertex shader)
const dummyPos = new Float32Array(COUNT * 3);
const pGeo = new THREE.BufferGeometry();
pGeo.setAttribute('position',  new THREE.BufferAttribute(dummyPos,  3));
pGeo.setAttribute('aAngle',    new THREE.BufferAttribute(aAngle,    1));
pGeo.setAttribute('aRadius',   new THREE.BufferAttribute(aRadius,   1));
pGeo.setAttribute('aY',        new THREE.BufferAttribute(aY,        1));
pGeo.setAttribute('aOrbSpeed', new THREE.BufferAttribute(aOrbSpeed, 1));
pGeo.setAttribute('aSize',     new THREE.BufferAttribute(aSize,     1));
pGeo.setAttribute('aPhase',    new THREE.BufferAttribute(aPhase,    1));

const particleUniforms = {
  uTime:   { value: 0 },
  uSpeed:  { value: params.speed },
  uColor1: { value: new THREE.Color(params.color1) },
  uColor2: { value: new THREE.Color(params.color2) },
};

const particleMat = new THREE.ShaderMaterial({
  vertexShader:   particleVert,
  fragmentShader: particleFrag,
  uniforms:       particleUniforms,
  transparent:    true,
  depthWrite:     false,
  blending:       THREE.AdditiveBlending,
});

const particles = new THREE.Points(pGeo, particleMat);
scene.add(particles);

// ─── Ambient fog ring (subtle) ────────────────────────────────────────────────
const fogGeo = new THREE.SphereGeometry(2.2, 32, 32);
const fogMat = new THREE.MeshBasicMaterial({
  color:       new THREE.Color(params.color2),
  side:        THREE.BackSide,
  transparent: true,
  opacity:     0.04,
  blending:    THREE.AdditiveBlending,
  depthWrite:  false,
});
const fogSphere = new THREE.Mesh(fogGeo, fogMat);
scene.add(fogSphere);

// ─── Post processing ──────────────────────────────────────────────────────────
const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));

const bloomPass = new UnrealBloomPass(
  new THREE.Vector2(innerWidth, innerHeight),
  params.bloomStrength,
  params.bloomRadius,
  params.bloomThreshold,
);
composer.addPass(bloomPass);
composer.addPass(new OutputPass());

// ─── GUI ──────────────────────────────────────────────────────────────────────
const gui = new GUI({ title: '⚡ Energy Ball' });

gui.add(params, 'speed', 0.05, 3.0, 0.01).name('Speed').onChange(v => {
  ballUniforms.uSpeed.value = v;
  particleUniforms.uSpeed.value = v;
});

gui.add(params, 'distortion', 0.0, 0.5, 0.005).name('Distortion').onChange(v => {
  ballUniforms.uDistortion.value = v;
});

gui.add(params, 'intensity', 0.2, 6.0, 0.05).name('Intensity').onChange(v => {
  ballUniforms.uIntensity.value = v;
});

gui.addColor(params, 'color1').name('Color 1').onChange(v => {
  ballUniforms.uColor1.value.set(v);
  particleUniforms.uColor1.value.set(v);
  fogMat.color.set(v);
});

gui.addColor(params, 'color2').name('Color 2').onChange(v => {
  ballUniforms.uColor2.value.set(v);
  particleUniforms.uColor2.value.set(v);
});

const bloomFolder = gui.addFolder('Bloom');
bloomFolder.add(params, 'bloomStrength', 0.0, 4.0, 0.05).name('Strength').onChange(v => {
  bloomPass.strength = v;
});
bloomFolder.add(params, 'bloomRadius', 0.0, 1.0, 0.01).name('Radius').onChange(v => {
  bloomPass.radius = v;
});
bloomFolder.add(params, 'bloomThreshold', 0.0, 1.0, 0.01).name('Threshold').onChange(v => {
  bloomPass.threshold = v;
});

// ─── Animation loop ───────────────────────────────────────────────────────────
const clock = new THREE.Clock();

function animate() {
  requestAnimationFrame(animate);

  const t = clock.getElapsedTime();

  ballUniforms.uTime.value      = t;
  particleUniforms.uTime.value  = t;

  // slow self-rotation adds depth without fighting OrbitControls
  ball.rotation.y = t * 0.04;

  // gently breathe the fog sphere
  const s = 1.0 + 0.05 * Math.sin(t * 0.7);
  fogSphere.scale.setScalar(s);

  controls.update();
  composer.render();
}

animate();

// ─── Resize ───────────────────────────────────────────────────────────────────
window.addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
  composer.setSize(innerWidth, innerHeight);
});
