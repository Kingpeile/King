/* Dual-pane compare app. file:// compatible. No uploads, no new port. */
(function (root) {
  "use strict";

  var MATERIAL_MODES = ["original", "gray", "wire"];
  var PRESETS = ["front", "45", "side", "back"];

  function $(id) { return document.getElementById(id); }

  function fmtInt(n) {
    if (n == null) return "—";
    return String(n);
  }

  function fmtSha(s) {
    if (!s) return "sha256 unavailable";
    return s.slice(0, 12) + "…" + s.slice(-8);
  }

  function createApp(cfg) {
    cfg = cfg || {};
    var probe = root.GlbCompareProbe.probe();
    root.GlbCompareProbe.installNetworkGuard(root);

    var rig = root.GlbCompareCamera.createRig();
    var sides = {
      A: root.GlbCompareLoad.createSide("A"),
      B: root.GlbCompareLoad.createSide("B")
    };
    var panes = {};
    var materialMode = "original";
    var normalize = false;
    var preset = "front";
    var raf = 0;

    function gpuDispose(side) {
      var pane = panes[side.id];
      if (pane && pane.dispose) pane.dispose();
    }
    function gpuUpload(side) {
      var pane = panes[side.id];
      if (pane && pane.upload) pane.upload(side.parts || [], normalize);
    }

    function loadOpts() {
      return { gpuDispose: gpuDispose, gpuUpload: gpuUpload };
    }

    function boxesForFit() {
      var boxes = [];
      ["A", "B"].forEach(function (id) {
        var s = sides[id];
        if (s.empty || !s.stats || !s.stats.extents) return;
        if (normalize) {
          boxes.push({ min: [-0.5, -0.5, -0.5], max: [0.5, 0.5, 0.5] });
        } else if (s.stats.extents.status === "DECODED") {
          boxes.push(s.stats.extents);
        }
      });
      return boxes;
    }

    function refit() {
      root.GlbCompareCamera.fitToBoxes(rig, boxesForFit());
    }

    function renderPane(id) {
      var pane = panes[id];
      if (pane && pane.draw) pane.draw(rig, materialMode);
    }

    function renderAll() {
      renderPane("A");
      renderPane("B");
    }

    function setOverlay(id) {
      var s = sides[id];
      var emptyEl = $("empty-" + id);
      var errEl = $("error-" + id);
      var scaleEl = $("scale-" + id);
      if (emptyEl) emptyEl.hidden = !s.empty || !!s.error;
      if (errEl) {
        errEl.hidden = !s.error;
        errEl.textContent = s.error || "";
      }
      if (scaleEl) {
        scaleEl.hidden = s.empty;
        if (normalize) {
          scaleEl.textContent = "NORMALIZED (not world scale)";
          scaleEl.className = "scale-badge warn";
        } else {
          scaleEl.textContent = "WORLD SCALE (transforms preserved)";
          scaleEl.className = "scale-badge";
        }
      }
      var st = s.stats;
      $("stat-name-" + id).textContent = s.empty ? "—" : (s.fileName || "—");
      $("stat-tri-" + id).textContent = s.empty ? "—" : fmtInt(st && st.triangles);
      $("stat-skin-" + id).textContent = s.empty ? "—" : fmtInt(st && st.skins);
      $("stat-anim-" + id).textContent = s.empty ? "—" : fmtInt(st && st.animations);
      $("stat-bytes-" + id).textContent = s.empty ? "—" : fmtInt(s.bytes);
      $("stat-sha-" + id).textContent = s.empty ? "—" : fmtSha(s.sha256);
    }

    function refresh() {
      setOverlay("A");
      setOverlay("B");
      $("normalize-label-live").textContent = normalize
        ? "ON — each model unit-boxed (overrides world transforms)"
        : "OFF — shared world scale, node TRS kept";
      $("material-live").textContent = materialMode;
      $("preset-live").textContent = preset;
      renderAll();
    }

    function tick() {
      renderAll();
      raf = root.requestAnimationFrame(tick);
    }

    async function onFile(id, file) {
      var result = await root.GlbCompareLoad.loadFile(sides[id], file, loadOpts());
      if (result.cancelled) return result;
      refit();
      refresh();
      return result;
    }

    async function onBytes(id, bytes, name) {
      var result = await root.GlbCompareLoad.loadBytes(sides[id], bytes, name, loadOpts());
      if (result.cancelled) return result;
      refit();
      refresh();
      return result;
    }

    function setMaterial(mode) {
      if (MATERIAL_MODES.indexOf(mode) < 0) return;
      materialMode = mode;
      document.querySelectorAll("[data-material]").forEach(function (btn) {
        btn.classList.toggle("active", btn.getAttribute("data-material") === mode);
      });
      refresh();
    }

    function setPreset(name) {
      if (PRESETS.indexOf(name) < 0) return;
      preset = name;
      root.GlbCompareCamera.applyPreset(rig, name);
      document.querySelectorAll("[data-preset]").forEach(function (btn) {
        btn.classList.toggle("active", btn.getAttribute("data-preset") === name);
      });
      refresh();
    }

    function setNormalize(on) {
      normalize = !!on;
      var box = $("normalize");
      if (box) box.checked = normalize;
      ["A", "B"].forEach(function (id) {
        if (!sides[id].empty && sides[id].parts) gpuUpload(sides[id]);
      });
      refit();
      refresh();
    }

    function bindUi() {
      ["A", "B"].forEach(function (id) {
        var canvas = $("canvas-" + id);
        panes[id] = root.GlbCompareWebGL.createPane(canvas);
        root.GlbCompareCamera.bindPointer(canvas, rig, renderAll);
        var input = $("file-" + id);
        input.addEventListener("change", function () {
          var f = input.files && input.files[0];
          if (f) onFile(id, f);
        });
      });
      document.querySelectorAll("[data-preset]").forEach(function (btn) {
        btn.addEventListener("click", function () { setPreset(btn.getAttribute("data-preset")); });
      });
      document.querySelectorAll("[data-material]").forEach(function (btn) {
        btn.addEventListener("click", function () { setMaterial(btn.getAttribute("data-material")); });
      });
      $("normalize").addEventListener("change", function (e) {
        setNormalize(e.target.checked);
      });
      window.addEventListener("resize", renderAll);
    }

    function fillProbeBanner() {
      var el = $("dep-banner");
      if (!el) return;
      if (probe.usable) {
        el.textContent = "Using repository Three.js + GLTFLoader.";
        el.className = "banner ok";
      } else {
        el.innerHTML = "<strong>Three.js / GLTFLoader gap.</strong> " +
          "No checked-in <code>three</code> module or <code>GLTFLoader.js</code> on this branch. " +
          "Panes use a bounded WebGL fallback for embedded FLOAT VEC3 triangles. " +
          "No npm install, no CDN, no new port. " +
          probe.gap;
      }
    }

    bindUi();
    fillProbeBanner();
    setPreset("front");
    setMaterial("original");
    setNormalize(false);
    refresh();
    tick();

    var api = {
      sides: sides,
      rig: rig,
      probe: probe,
      onFile: onFile,
      onBytes: onBytes,
      setMaterial: setMaterial,
      setPreset: setPreset,
      setNormalize: setNormalize,
      materialMode: function () { return materialMode; },
      normalize: function () { return normalize; },
      refresh: refresh,
      loadOpts: loadOpts
    };
    root.__GLB_COMPARE__ = api;
    return api;
  }

  root.GlbCompareApp = { createApp: createApp, MATERIAL_MODES: MATERIAL_MODES, PRESETS: PRESETS };

  if (typeof document !== "undefined") {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", function () { createApp(); });
    } else {
      createApp();
    }
  }
})(typeof globalThis !== "undefined" ? globalThis : this);
