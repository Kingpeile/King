#!/usr/bin/env node
/* Node behavioral tests. No browser, no npm packages. */
"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const HERE = __dirname;
const ctx = { console, setTimeout, clearTimeout, Uint8Array, Float32Array,
  DataView, ArrayBuffer, TextDecoder, Promise, JSON, Math, atob: null,
  crypto: undefined, globalThis: null };
ctx.globalThis = ctx;
ctx.window = ctx;
ctx.atob = function (s) { return Buffer.from(s, "base64").toString("binary"); };

function loadScript(rel) {
  const src = fs.readFileSync(path.join(HERE, rel), "utf8");
  vm.runInNewContext(src, ctx, { filename: rel });
}

loadScript("js/glb-parse.js");
loadScript("js/load-session.js");
loadScript("js/three-probe.js");
loadScript("js/embedded-fixtures.js");

const parse = ctx.GlbCompareParse.parseGlb;
const Load = ctx.GlbCompareLoad;
const Probe = ctx.GlbCompareProbe;
const FIX = ctx.GLB_COMPARE_FIXTURES;

function u8of(name) {
  return ctx.GlbCompareParse.b64ToU8(FIX[name].b64);
}

function delayedFile(u8, ms, name) {
  return {
    name: name,
    arrayBuffer: function () {
      return new Promise(function (resolve) {
        setTimeout(function () {
          resolve(u8.buffer.slice(u8.byteOffset, u8.byteOffset + u8.byteLength));
        }, ms);
      });
    }
  };
}

const checks = [];
function check(name, ok, detail) {
  checks.push({ name: name, ok: !!ok, detail: detail == null ? "" : String(detail) });
}

async function main() {
  const a1 = parse(u8of("a1.glb"));
  check("a1-ok", a1.ok, a1.malformed.join("; "));
  check("a1-tri-12", a1.triangles === 12, a1.triangles);
  check("a1-skins-0", a1.skins === 0);
  check("a1-anims-0", a1.animations === 0);
  check("a1-no-external", a1.external_resources.length === 0);
  check("a1-world-min-x-0", a1.extents.status === "DECODED" && a1.extents.min[0] === 0, JSON.stringify(a1.extents));

  const a2 = parse(u8of("a2.glb"));
  check("a2-tri-4", a2.triangles === 4, a2.triangles);
  check("a2-translated", a2.extents.status === "DECODED" && a2.extents.min[0] >= 2, JSON.stringify(a2.extents));
  check("a1-a2-tri-differ", a1.triangles !== a2.triangles);

  const b = parse(u8of("b.glb"));
  check("b-tri-12", b.triangles === 12);
  check("b-scaled-height", b.extents.status === "DECODED" && b.extents.max[1] === 2, JSON.stringify(b.extents));

  const ext = parse(u8of("external.glb"));
  check("external-not-ok", ext.ok === false);
  check("external-listed", ext.external_resources.length === 2, JSON.stringify(ext.external_resources));
  check("external-no-fetch-parts", ext.parts.length === 0);

  const inv = parse(u8of("invalid.glb"));
  check("invalid-not-ok", inv.ok === false);
  check("invalid-bad-magic", inv.malformed.join(" ").indexOf("magic") >= 0, inv.malformed.join("; "));

  const sk = parse(u8of("skinned-count.glb"));
  check("skinned-tri-12", sk.triangles === 12);
  check("skinned-skins-1", sk.skins === 1);
  check("skinned-anims-1", sk.animations === 1);
  check("not-proven-walking", sk.not_proven.indexOf("walking") >= 0);

  const probe = Probe.probe();
  check("three-not-found", probe.foundThree === false);
  check("gltfloader-not-found", probe.foundGLTFLoader === false);
  check("gap-string", typeof probe.gap === "string" && probe.gap.indexOf("GLTFLoader") >= 0);

  const fakeWin = {
    fetchCalls: [],
    fetch: function (url) { this.fetchCalls.push(url); return Promise.resolve("no"); },
    XMLHttpRequest: function () {}
  };
  fakeWin.XMLHttpRequest.prototype = { open: function () { this.opened = arguments; } };
  const origProto = fakeWin.XMLHttpRequest.prototype.open;
  Probe.installNetworkGuard(fakeWin);
  let blocked = false;
  try {
    await fakeWin.fetch("https://example.com/mesh.bin");
  } catch (e) {
    blocked = /Blocked external/.test(String(e));
  }
  check("guard-blocks-https", blocked && fakeWin.fetchCalls.length === 0, blocked);

  const side = Load.createSide("A");
  const p1 = Load.loadFile(side, delayedFile(u8of("a1.glb"), 80, "a1.glb"));
  const p2 = Load.loadFile(side, delayedFile(u8of("a2.glb"), 10, "a2.glb"));
  const settled = await Promise.all([p1, p2]);
  check("race-a1-cancelled", settled[0].cancelled === true, JSON.stringify(settled[0]));
  check("race-a2-ok", settled[1].ok === true, JSON.stringify(settled[1]));
  check("race-final-a2", side.stats && side.stats.triangles === 4, JSON.stringify(side.stats));
  check("race-name-a2", side.fileName === "a2.glb", side.fileName);

  let disposed = 0;
  const side2 = Load.createSide("B");
  await Load.loadBytes(side2, u8of("b.glb"), "b.glb", {
    gpuDispose: function () { disposed++; },
    gpuUpload: function () {}
  });
  await Load.loadBytes(side2, u8of("invalid.glb"), "invalid.glb", {
    gpuDispose: function () { disposed++; },
    gpuUpload: function () {}
  });
  check("invalid-disposes", disposed >= 1, String(disposed));
  check("invalid-error-state", !!side2.error && side2.empty === true, side2.error);

  const failed = checks.filter(function (c) { return !c.ok; });
  const summary = {
    task: "CT-GLB-COMPARE-01",
    runner: "node",
    ok: failed.length === 0,
    tests_run: checks.length,
    failures: failed.length,
    results: checks
  };
  process.stdout.write(JSON.stringify(summary, null, 2) + "\n");
  if (!summary.ok) process.exit(1);
}

main().catch(function (err) {
  console.error(err);
  process.exit(1);
});
