/* Optional ?selftest=1 runner. Uses embedded fixtures; never fetches scholar files. */
(function (root) {
  "use strict";

  function qtrue(name) {
    if (typeof location === "undefined") return false;
    return new URLSearchParams(location.search).get(name) === "1";
  }

  function wait(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }

  function fixtureU8(name) {
    var f = root.GLB_COMPARE_FIXTURES[name];
    return root.GlbCompareParse.b64ToU8(f.b64);
  }

  function delayedBuffer(u8, ms) {
    return {
      name: "delayed.glb",
      arrayBuffer: function () {
        return new Promise(function (resolve) {
          setTimeout(function () { resolve(u8.buffer.slice(u8.byteOffset, u8.byteOffset + u8.byteLength)); }, ms);
        });
      }
    };
  }

  async function run() {
    var app = root.__GLB_COMPARE__;
    var results = [];
    function check(name, ok, detail) {
      results.push({ name: name, ok: !!ok, detail: detail || "" });
    }

    try {
      check("probe-reports-gap", app.probe && app.probe.usable === false, app.probe && app.probe.gap);
      check("normalize-default-off", app.normalize() === false, "default must preserve world scale");

      await app.onBytes("A", fixtureU8("a1.glb"), "a1.glb");
      await app.onBytes("B", fixtureU8("b.glb"), "b.glb");
      check("a1-triangles-12", app.sides.A.stats && app.sides.A.stats.triangles === 12, String(app.sides.A.stats && app.sides.A.stats.triangles));
      check("a1-skins-0", app.sides.A.stats.skins === 0);
      check("a1-anims-0", app.sides.A.stats.animations === 0);
      check("b-triangles-12", app.sides.B.stats && app.sides.B.stats.triangles === 12);
      check("b-not-empty", app.sides.B.empty === false);

      var a1 = delayedBuffer(fixtureU8("a1.glb"), 80);
      var a2 = delayedBuffer(fixtureU8("a2.glb"), 10);
      var p1 = app.onFile("A", a1);
      var p2 = app.onFile("A", a2);
      var settled = await Promise.all([p1, p2]);
      check("rapid-a1-cancelled-or-stale", settled[0].cancelled === true, JSON.stringify(settled[0]));
      check("rapid-a2-ok", settled[1].ok === true);
      check("rapid-final-is-a2-4-tris", app.sides.A.stats && app.sides.A.stats.triangles === 4, String(app.sides.A.stats && app.sides.A.stats.triangles));
      check("rapid-b-untouched", app.sides.B.stats && app.sides.B.stats.triangles === 12);

      await app.onBytes("A", fixtureU8("invalid.glb"), "invalid.glb");
      check("invalid-error", !!app.sides.A.error, app.sides.A.error);
      check("invalid-empty-side", app.sides.A.empty === true);
      check("invalid-does-not-clear-b", app.sides.B.empty === false && app.sides.B.stats.triangles === 12);

      await app.onBytes("A", fixtureU8("external.glb"), "external.glb");
      check("external-blocked", /Blocked external/.test(app.sides.A.error || ""), app.sides.A.error);
      check("external-empty", app.sides.A.empty === true);

      await app.onBytes("A", fixtureU8("skinned-count.glb"), "skinned-count.glb");
      check("skin-count-1", app.sides.A.stats && app.sides.A.stats.skins === 1);
      check("anim-count-1", app.sides.A.stats && app.sides.A.stats.animations === 1);
      check("skin-not-claimed-walking", app.sides.A.stats.not_proven.indexOf("walking") >= 0);

      app.setNormalize(true);
      check("normalize-explicit-on", app.normalize() === true);
      var badge = document.getElementById("scale-A");
      check("normalize-badge-visible", badge && /NORMALIZED/.test(badge.textContent), badge && badge.textContent);

      app.setNormalize(false);
      check("normalize-off-world-label", /WORLD SCALE/.test(document.getElementById("scale-A").textContent));

      app.setPreset("side");
      check("preset-side", app.rig.theta === Math.PI / 2);
      app.setMaterial("wire");
      check("material-wire", app.materialMode() === "wire");
      app.setMaterial("gray");
      check("material-gray", app.materialMode() === "gray");
      app.setMaterial("original");

      app.setPreset("front");
      app.setMaterial("original");
      app.setNormalize(false);
      await app.onBytes("A", fixtureU8("a1.glb"), "a1.glb");
      await app.onBytes("B", fixtureU8("b.glb"), "b.glb");
      await wait(120);
    } catch (e) {
      check("selftest-threw", false, String(e && e.stack || e));
    }

    var failed = results.filter(function (r) { return !r.ok; });
    var summary = {
      task: "CT-GLB-COMPARE-01",
      ok: failed.length === 0,
      tests_run: results.length,
      failures: failed.length,
      results: results,
      not_proven: root.GlbCompareParse.NOT_PROVEN,
      browser: "selftest"
    };
    var pre = document.getElementById("selftest-json");
    if (pre) pre.textContent = JSON.stringify(summary, null, 2);
    var banner = document.getElementById("selftest-banner");
    if (banner) {
      banner.hidden = false;
      banner.textContent = summary.ok
        ? "SELFTEST PASS " + results.length + "/" + results.length
        : "SELFTEST FAIL " + failed.map(function (f) { return f.name; }).join(", ");
      banner.className = "banner " + (summary.ok ? "ok" : "bad");
    }
    root.__GLB_COMPARE_SELFTEST__ = summary;
    return summary;
  }

  async function loadDemo() {
    var app = root.__GLB_COMPARE__;
    app.setPreset("front");
    app.setMaterial("original");
    app.setNormalize(false);
    await app.onBytes("A", fixtureU8("a1.glb"), "a1.glb");
    await app.onBytes("B", fixtureU8("b.glb"), "b.glb");
  }

  if (qtrue("selftest")) {
    window.addEventListener("load", function () {
      setTimeout(run, 50);
    });
  } else if (qtrue("fixtures")) {
    window.addEventListener("load", function () {
      setTimeout(loadDemo, 50);
    });
  } else if (qtrue("error")) {
    window.addEventListener("load", function () {
      setTimeout(async function () {
        var app = root.__GLB_COMPARE__;
        app.setPreset("front");
        await app.onBytes("B", fixtureU8("b.glb"), "b.glb");
        await app.onBytes("A", fixtureU8("invalid.glb"), "invalid.glb");
      }, 50);
    });
  }
})(typeof globalThis !== "undefined" ? globalThis : this);
