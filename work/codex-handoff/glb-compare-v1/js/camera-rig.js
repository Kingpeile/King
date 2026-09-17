/* Shared orbit / pan / zoom + view presets. One rig drives both panes. */
(function (root) {
  "use strict";

  function createRig() {
    return {
      target: [0, 0.5, 0],
      theta: 0,
      phi: Math.PI / 2,
      radius: 6,
      fov: 35 * Math.PI / 180,
      near: 0.05,
      far: 200,
      lightDir: [0.35, 0.85, 0.45],
      ambient: 0.32
    };
  }

  function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }

  function applyPreset(rig, name) {
    rig.phi = Math.PI / 2;
    if (name === "front") rig.theta = 0;
    else if (name === "45") rig.theta = Math.PI / 4;
    else if (name === "side") rig.theta = Math.PI / 2;
    else if (name === "back") rig.theta = Math.PI;
    else rig.theta = 0;
  }

  function eyeOf(rig) {
    var s = Math.sin(rig.phi), c = Math.cos(rig.phi);
    return [
      rig.target[0] + rig.radius * s * Math.sin(rig.theta),
      rig.target[1] + rig.radius * c,
      rig.target[2] + rig.radius * s * Math.cos(rig.theta)
    ];
  }

  function lookAt(eye, target, up) {
    var zx = eye[0] - target[0], zy = eye[1] - target[1], zz = eye[2] - target[2];
    var zl = Math.hypot(zx, zy, zz) || 1;
    zx /= zl; zy /= zl; zz /= zl;
    var xx = up[1] * zz - up[2] * zy;
    var xy = up[2] * zx - up[0] * zz;
    var xz = up[0] * zy - up[1] * zx;
    var xl = Math.hypot(xx, xy, xz) || 1;
    xx /= xl; xy /= xl; xz /= xl;
    var yx = zy * xz - zz * xy;
    var yy = zz * xx - zx * xz;
    var yz = zx * xy - zy * xx;
    return [
      xx, yx, zx, 0,
      xy, yy, zy, 0,
      xz, yz, zz, 0,
      -(xx * eye[0] + xy * eye[1] + xz * eye[2]),
      -(yx * eye[0] + yy * eye[1] + yz * eye[2]),
      -(zx * eye[0] + zy * eye[1] + zz * eye[2]),
      1
    ];
  }

  function perspective(fovy, aspect, near, far) {
    var f = 1 / Math.tan(fovy / 2);
    var m = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
    m[0] = f / aspect;
    m[5] = f;
    m[10] = (far + near) / (near - far);
    m[11] = -1;
    m[14] = (2 * far * near) / (near - far);
    return m;
  }

  function viewOf(rig) {
    return lookAt(eyeOf(rig), rig.target, [0, 1, 0]);
  }

  function unionBox(boxes) {
    var mn = [Infinity, Infinity, Infinity];
    var mx = [-Infinity, -Infinity, -Infinity];
    var any = false;
    boxes.forEach(function (b) {
      if (!b || !b.min || !b.max) return;
      any = true;
      for (var i = 0; i < 3; i++) {
        if (b.min[i] < mn[i]) mn[i] = b.min[i];
        if (b.max[i] > mx[i]) mx[i] = b.max[i];
      }
    });
    if (!any) return null;
    return { min: mn, max: mx };
  }

  function fitToBoxes(rig, boxes) {
    var u = unionBox(boxes);
    if (!u) {
      rig.target = [0, 0.5, 0];
      rig.radius = 6;
      return "empty";
    }
    rig.target = [
      (u.min[0] + u.max[0]) / 2,
      (u.min[1] + u.max[1]) / 2,
      (u.min[2] + u.max[2]) / 2
    ];
    var dx = u.max[0] - u.min[0], dy = u.max[1] - u.min[1], dz = u.max[2] - u.min[2];
    var span = Math.max(dx, dy, dz, 0.01);
    rig.radius = span * 2.2;
    rig.near = Math.max(span / 200, 0.01);
    rig.far = Math.max(span * 40, 20);
    return "fitted";
  }

  function bindPointer(el, rig, onChange) {
    var dragging = false;
    var mode = "orbit";
    var lastX = 0, lastY = 0;

    function start(ev) {
      dragging = true;
      lastX = ev.clientX; lastY = ev.clientY;
      mode = (ev.button === 1 || ev.button === 2 || ev.shiftKey) ? "pan" : "orbit";
      try { el.setPointerCapture(ev.pointerId); } catch (e) {}
      ev.preventDefault();
    }
    function move(ev) {
      if (!dragging) return;
      var dx = ev.clientX - lastX, dy = ev.clientY - lastY;
      lastX = ev.clientX; lastY = ev.clientY;
      if (mode === "pan") {
        var scale = rig.radius * 0.0025;
        var eye = eyeOf(rig);
        var fx = rig.target[0] - eye[0], fy = rig.target[1] - eye[1], fz = rig.target[2] - eye[2];
        var fl = Math.hypot(fx, fy, fz) || 1;
        fx /= fl; fy /= fl; fz /= fl;
        var rx = fy * 0 - 1 * fz, ry = fz * 0 - fx * 0, rz = fx * 1 - fy * 0;
        var rl = Math.hypot(rx, ry, rz) || 1;
        rx /= rl; ry /= rl; rz /= rl;
        var ux = ry * fz - rz * fy, uy = rz * fx - rx * fz, uz = rx * fy - ry * fx;
        rig.target[0] += (-dx) * scale * rx + dy * scale * ux;
        rig.target[1] += (-dx) * scale * ry + dy * scale * uy;
        rig.target[2] += (-dx) * scale * rz + dy * scale * uz;
      } else {
        rig.theta -= dx * 0.008;
        rig.phi = clamp(rig.phi - dy * 0.008, 0.05, Math.PI - 0.05);
      }
      onChange();
    }
    function end(ev) {
      dragging = false;
      try { el.releasePointerCapture(ev.pointerId); } catch (e) {}
    }
    function wheel(ev) {
      ev.preventDefault();
      var f = ev.deltaY > 0 ? 1.08 : 0.92;
      rig.radius = clamp(rig.radius * f, 0.05, 500);
      onChange();
    }
    function ctx(ev) { ev.preventDefault(); }
    el.addEventListener("pointerdown", start);
    el.addEventListener("pointermove", move);
    el.addEventListener("pointerup", end);
    el.addEventListener("pointercancel", end);
    el.addEventListener("wheel", wheel, { passive: false });
    el.addEventListener("contextmenu", ctx);
    return function unbind() {
      el.removeEventListener("pointerdown", start);
      el.removeEventListener("pointermove", move);
      el.removeEventListener("pointerup", end);
      el.removeEventListener("pointercancel", end);
      el.removeEventListener("wheel", wheel);
      el.removeEventListener("contextmenu", ctx);
    };
  }

  root.GlbCompareCamera = {
    createRig: createRig,
    applyPreset: applyPreset,
    eyeOf: eyeOf,
    viewOf: viewOf,
    perspective: perspective,
    fitToBoxes: fitToBoxes,
    unionBox: unionBox,
    bindPointer: bindPointer
  };
})(typeof globalThis !== "undefined" ? globalThis : this);
