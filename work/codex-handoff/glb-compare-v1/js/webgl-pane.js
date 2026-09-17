/* Bounded WebGL pane. Fallback because repo Three.js/GLTFLoader are absent. */
(function (root) {
  "use strict";

  var VS = [
    "attribute vec3 aPos;",
    "attribute vec3 aNrm;",
    "uniform mat4 uMVP;",
    "uniform mat4 uView;",
    "varying vec3 vN;",
    "void main(){",
    "  vN = mat3(uView) * aNrm;",
    "  gl_Position = uMVP * vec4(aPos,1.0);",
    "}"
  ].join("\n");

  var FS = [
    "precision mediump float;",
    "varying vec3 vN;",
    "uniform vec3 uColor;",
    "uniform vec3 uLightDir;",
    "uniform float uAmbient;",
    "void main(){",
    "  vec3 n = normalize(vN);",
    "  float ndl = max(dot(n, normalize(uLightDir)), 0.0);",
    "  vec3 col = uColor * (uAmbient + (1.0-uAmbient)*ndl);",
    "  gl_FragColor = vec4(col,1.0);",
    "}"
  ].join("\n");

  function compile(gl, type, src) {
    var s = gl.createShader(type);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
      var log = gl.getShaderInfoLog(s);
      gl.deleteShader(s);
      throw new Error(log);
    }
    return s;
  }

  function mul4(a, b) {
    var o = new Float32Array(16);
    for (var c = 0; c < 4; c++) {
      for (var r = 0; r < 4; r++) {
        o[c * 4 + r] =
          a[0 * 4 + r] * b[c * 4 + 0] +
          a[1 * 4 + r] * b[c * 4 + 1] +
          a[2 * 4 + r] * b[c * 4 + 2] +
          a[3 * 4 + r] * b[c * 4 + 3];
      }
    }
    return o;
  }

  function triList(part) {
    var pts = part.positions;
    var tris = [];
    function pushTri(i0, i1, i2) {
      tris.push(pts[i0], pts[i1], pts[i2]);
    }
    if (part.indices && part.indices.length) {
      var idx = part.indices;
      if (part.mode === 5) {
        for (var s = 0; s + 2 < idx.length; s++) {
          if (s % 2 === 0) pushTri(idx[s], idx[s + 1], idx[s + 2]);
          else pushTri(idx[s + 1], idx[s], idx[s + 2]);
        }
      } else if (part.mode === 6) {
        for (var f = 0; f + 2 < idx.length; f++) pushTri(idx[0], idx[f + 1], idx[f + 2]);
      } else {
        for (var i = 0; i + 2 < idx.length; i += 3) pushTri(idx[i], idx[i + 1], idx[i + 2]);
      }
    } else {
      for (var j = 0; j + 2 < pts.length; j += 3) tris.push(pts[j], pts[j + 1], pts[j + 2]);
    }
    return tris;
  }

  function packMesh(parts, normalize) {
    var all = [];
    parts.forEach(function (p) {
      var tris = triList(p);
      all.push({ tris: tris, color: p.color });
    });
    var mn = [Infinity, Infinity, Infinity];
    var mx = [-Infinity, -Infinity, -Infinity];
    all.forEach(function (chunk) {
      chunk.tris.forEach(function (p) {
        for (var k = 0; k < 3; k++) {
          if (p[k] < mn[k]) mn[k] = p[k];
          if (p[k] > mx[k]) mx[k] = p[k];
        }
      });
    });
    var cx = 0, cy = 0, cz = 0, scale = 1;
    if (normalize && isFinite(mn[0])) {
      cx = (mn[0] + mx[0]) / 2;
      cy = (mn[1] + mx[1]) / 2;
      cz = (mn[2] + mx[2]) / 2;
      var span = Math.max(mx[0] - mn[0], mx[1] - mn[1], mx[2] - mn[2], 1e-6);
      scale = 1 / span;
    }
    var draws = [];
    all.forEach(function (chunk) {
      var pos = [];
      var nrm = [];
      var lines = [];
      chunk.tris.forEach(function (tri, ti) {
        /* grouped in 3 */
      });
      for (var t = 0; t + 2 < chunk.tris.length; t += 3) {
        var a = chunk.tris[t], b = chunk.tris[t + 1], c = chunk.tris[t + 2];
        function xf(p) {
          return [(p[0] - cx) * scale, (p[1] - cy) * scale, (p[2] - cz) * scale];
        }
        a = xf(a); b = xf(b); c = xf(c);
        var e1 = [b[0] - a[0], b[1] - a[1], b[2] - a[2]];
        var e2 = [c[0] - a[0], c[1] - a[1], c[2] - a[2]];
        var nx = e1[1] * e2[2] - e1[2] * e2[1];
        var ny = e1[2] * e2[0] - e1[0] * e2[2];
        var nz = e1[0] * e2[1] - e1[1] * e2[0];
        var nl = Math.hypot(nx, ny, nz) || 1;
        nx /= nl; ny /= nl; nz /= nl;
        pos.push(a[0], a[1], a[2], b[0], b[1], b[2], c[0], c[1], c[2]);
        nrm.push(nx, ny, nz, nx, ny, nz, nx, ny, nz);
        lines.push(a[0], a[1], a[2], b[0], b[1], b[2]);
        lines.push(b[0], b[1], b[2], c[0], c[1], c[2]);
        lines.push(c[0], c[1], c[2], a[0], a[1], a[2]);
      }
      draws.push({
        color: chunk.color,
        pos: new Float32Array(pos),
        nrm: new Float32Array(nrm),
        lines: new Float32Array(lines)
      });
    });
    return { draws: draws, normalized: !!normalize };
  }

  function createPane(canvas) {
    var gl = canvas.getContext("webgl", { antialias: true, alpha: false, preserveDrawingBuffer: true });
    if (!gl) return { ok: false, error: "WebGL unavailable", dispose: function () {}, upload: function () {}, draw: function () {}, resize: function () {} };

    var vs = compile(gl, gl.VERTEX_SHADER, VS);
    var fs = compile(gl, gl.FRAGMENT_SHADER, FS);
    var prog = gl.createProgram();
    gl.attachShader(prog, vs);
    gl.attachShader(prog, fs);
    gl.bindAttribLocation(prog, 0, "aPos");
    gl.bindAttribLocation(prog, 1, "aNrm");
    gl.linkProgram(prog);
    gl.deleteShader(vs);
    gl.deleteShader(fs);
    var uMVP = gl.getUniformLocation(prog, "uMVP");
    var uView = gl.getUniformLocation(prog, "uView");
    var uColor = gl.getUniformLocation(prog, "uColor");
    var uLightDir = gl.getUniformLocation(prog, "uLightDir");
    var uAmbient = gl.getUniformLocation(prog, "uAmbient");

    var gpu = [];
    var meshMeta = { normalized: false };

    function clearGpu() {
      gpu.forEach(function (g) {
        if (g.pos) gl.deleteBuffer(g.pos);
        if (g.nrm) gl.deleteBuffer(g.nrm);
        if (g.lines) gl.deleteBuffer(g.lines);
      });
      gpu = [];
    }

    function makeBuf(data) {
      var b = gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER, b);
      gl.bufferData(gl.ARRAY_BUFFER, data, gl.STATIC_DRAW);
      return b;
    }

    function upload(parts, normalize) {
      clearGpu();
      if (!parts || !parts.length) return;
      var packed = packMesh(parts, normalize);
      meshMeta.normalized = packed.normalized;
      packed.draws.forEach(function (d) {
        gpu.push({
          color: d.color,
          pos: makeBuf(d.pos),
          nrm: makeBuf(d.nrm),
          lines: makeBuf(d.lines),
          triCount: d.pos.length / 3,
          lineCount: d.lines.length / 3
        });
      });
    }

    function resize() {
      var dpr = Math.min(root.devicePixelRatio || 1, 2);
      var w = Math.max(1, Math.floor(canvas.clientWidth * dpr));
      var h = Math.max(1, Math.floor(canvas.clientHeight * dpr));
      if (canvas.width !== w || canvas.height !== h) {
        canvas.width = w;
        canvas.height = h;
      }
      gl.viewport(0, 0, canvas.width, canvas.height);
    }

    function draw(rig, materialMode) {
      resize();
      gl.clearColor(0.09, 0.09, 0.11, 1);
      gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
      gl.enable(gl.DEPTH_TEST);
      if (!gpu.length) return;
      var aspect = canvas.width / Math.max(1, canvas.height);
      var proj = root.GlbCompareCamera.perspective(rig.fov, aspect, rig.near, rig.far);
      var view = root.GlbCompareCamera.viewOf(rig);
      var mvp = mul4(proj, view);
      gl.useProgram(prog);
      gl.uniformMatrix4fv(uMVP, false, mvp);
      gl.uniformMatrix4fv(uView, false, new Float32Array(view));
      var ld = rig.lightDir;
      var viewLight = [
        view[0] * ld[0] + view[4] * ld[1] + view[8] * ld[2],
        view[1] * ld[0] + view[5] * ld[1] + view[9] * ld[2],
        view[2] * ld[0] + view[6] * ld[1] + view[10] * ld[2]
      ];
      gl.uniform3fv(uLightDir, viewLight);
      gl.uniform1f(uAmbient, rig.ambient);
      gpu.forEach(function (g) {
        var col = materialMode === "gray" ? [0.62, 0.62, 0.64] : g.color;
        gl.uniform3fv(uColor, col);
        gl.bindBuffer(gl.ARRAY_BUFFER, g.pos);
        gl.enableVertexAttribArray(0);
        gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 0, 0);
        gl.bindBuffer(gl.ARRAY_BUFFER, g.nrm);
        gl.enableVertexAttribArray(1);
        gl.vertexAttribPointer(1, 3, gl.FLOAT, false, 0, 0);
        if (materialMode === "wire") {
          gl.bindBuffer(gl.ARRAY_BUFFER, g.lines);
          gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 0, 0);
          gl.disableVertexAttribArray(1);
          gl.drawArrays(gl.LINES, 0, g.lineCount);
        } else {
          gl.drawArrays(gl.TRIANGLES, 0, g.triCount);
        }
      });
    }

    return {
      ok: true,
      error: null,
      upload: upload,
      draw: draw,
      dispose: clearGpu,
      resize: resize,
      normalized: function () { return meshMeta.normalized; }
    };
  }

  root.GlbCompareWebGL = { createPane: createPane, packMesh: packMesh };
})(typeof globalThis !== "undefined" ? globalThis : this);
