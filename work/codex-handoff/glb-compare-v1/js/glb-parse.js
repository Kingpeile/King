/* CT-GLB-COMPARE-01: parse self-contained GLB v2 in-memory. No fetches. */
(function (root) {
  "use strict";

  var MAGIC = 0x46546C67;
  var CHUNK_JSON = 0x4E4F534A;
  var CHUNK_BIN = 0x004E4942;
  var FLOAT = 5126;
  var UNSIGNED_SHORT = 5123;
  var UNSIGNED_INT = 5125;
  var UNSIGNED_BYTE = 5121;
  var MODE_TRIANGLES = 4;
  var MODE_STRIP = 5;
  var MODE_FAN = 6;
  var NOT_PROVEN = ["geometric quality", "art quality", "walking", "G1-G5"];

  function u32(view, off) {
    return view.getUint32(off, true);
  }
  function f32(view, off) {
    return view.getFloat32(off, true);
  }

  function identity4() {
    return [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];
  }

  function mul4(a, b) {
    var o = new Array(16);
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

  function translationMat(t) {
    var m = identity4();
    m[12] = t[0]; m[13] = t[1]; m[14] = t[2];
    return m;
  }

  function scaleMat(s) {
    var m = identity4();
    m[0] = s[0]; m[5] = s[1]; m[10] = s[2];
    return m;
  }

  function rotationMat(q) {
    var x = q[0], y = q[1], z = q[2], w = q[3];
    var xx = x * x, yy = y * y, zz = z * z;
    var xy = x * y, xz = x * z, yz = y * z;
    var wx = w * x, wy = w * y, wz = w * z;
    return [
      1 - 2 * (yy + zz), 2 * (xy + wz), 2 * (xz - wy), 0,
      2 * (xy - wz), 1 - 2 * (xx + zz), 2 * (yz + wx), 0,
      2 * (xz + wy), 2 * (yz - wx), 1 - 2 * (xx + yy), 0,
      0, 0, 0, 1
    ];
  }

  function nodeLocal(node) {
    if (node.matrix && node.matrix.length === 16) return node.matrix.slice();
    var t = node.translation || [0, 0, 0];
    var r = node.rotation || [0, 0, 0, 1];
    var s = node.scale || [1, 1, 1];
    return mul4(translationMat(t), mul4(rotationMat(r), scaleMat(s)));
  }

  function xformPoint(m, p) {
    var x = p[0], y = p[1], z = p[2];
    return [
      m[0] * x + m[4] * y + m[8] * z + m[12],
      m[1] * x + m[5] * y + m[9] * z + m[13],
      m[2] * x + m[6] * y + m[10] * z + m[14]
    ];
  }

  function isDataUri(uri) {
    return typeof uri === "string" && uri.indexOf("data:") === 0;
  }
  function isExternalUri(uri) {
    return typeof uri === "string" && uri !== "" && !isDataUri(uri);
  }

  function emptyReport(bytes) {
    return {
      ok: false,
      malformed: [],
      header: null,
      counts: {
        meshes: 0, primitives: 0, materials: 0, textures: 0, images: 0,
        skins: 0, animations: 0, nodes: 0, triangles: 0
      },
      external_resources: [],
      triangles: 0,
      skins: 0,
      animations: 0,
      extents: { status: "UNKNOWN", min: null, max: null, vertex_count: 0 },
      parts: [],
      bytes: bytes ? bytes.byteLength : 0,
      not_proven: NOT_PROVEN.slice()
    };
  }

  function note(rep, msg) {
    if (rep.malformed.indexOf(msg) < 0) rep.malformed.push(msg);
  }

  function collectExternal(doc) {
    var found = [];
    (doc.buffers || []).forEach(function (buf, i) {
      if (buf && isExternalUri(buf.uri)) found.push({ kind: "buffer", index: i, uri: buf.uri });
    });
    (doc.images || []).forEach(function (img, i) {
      if (img && isExternalUri(img.uri)) found.push({ kind: "image", index: i, uri: img.uri });
    });
    return found;
  }

  function triangleCountOfPrim(prim, doc) {
    var mode = prim.mode == null ? MODE_TRIANGLES : prim.mode;
    var n;
    if (prim.indices != null) {
      var acc = (doc.accessors || [])[prim.indices];
      if (!acc) return { n: 0, err: "indices accessor missing" };
      n = acc.count | 0;
    } else {
      var attrs = prim.attributes || {};
      var pacc = (doc.accessors || [])[attrs.POSITION];
      if (!pacc) return { n: 0, err: "POSITION accessor missing" };
      n = pacc.count | 0;
    }
    if (mode === MODE_TRIANGLES) return { n: Math.floor(n / 3), err: null };
    if (mode === MODE_STRIP || mode === MODE_FAN) return { n: Math.max(0, n - 2), err: null };
    return { n: 0, err: "unsupported primitive mode " + mode };
  }

  function countDoc(doc) {
    var meshes = doc.meshes || [];
    var primitives = 0;
    var triangles = 0;
    var triErr = null;
    meshes.forEach(function (mesh) {
      (mesh.primitives || []).forEach(function (prim) {
        primitives++;
        var t = triangleCountOfPrim(prim, doc);
        triangles += t.n;
        if (t.err && !triErr) triErr = t.err;
      });
    });
    return {
      meshes: meshes.length,
      primitives: primitives,
      materials: (doc.materials || []).length,
      textures: (doc.textures || []).length,
      images: (doc.images || []).length,
      skins: (doc.skins || []).length,
      animations: (doc.animations || []).length,
      nodes: (doc.nodes || []).length,
      triangles: triangles,
      triangle_error: triErr
    };
  }

  function sceneRoots(doc) {
    var si = doc.scene;
    if (si == null) si = 0;
    var scene = (doc.scenes || [])[si];
    if (!scene) return [];
    return scene.nodes || [];
  }

  function walkNodes(doc) {
    var nodes = doc.nodes || [];
    var instances = [];
    function walk(i, parent) {
      if (i < 0 || i >= nodes.length) return;
      var node = nodes[i] || {};
      var world = mul4(parent, nodeLocal(node));
      if (node.mesh != null) instances.push({ mesh: node.mesh, world: world });
      (node.children || []).forEach(function (c) { walk(c, world); });
    }
    var ident = identity4();
    sceneRoots(doc).forEach(function (r) { walk(r, ident); });
    return instances;
  }

  function accessorBytes(acc, views, blobs, rep) {
    if (!acc || acc.bufferView == null) return null;
    var view = views[acc.bufferView];
    if (!view) { note(rep, "bufferView missing"); return null; }
    var blob = blobs[view.buffer || 0];
    if (!blob) { note(rep, "buffer not embedded"); return null; }
    var off = (view.byteOffset || 0) + (acc.byteOffset || 0);
    var comp = { 5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4 }[acc.componentType];
    var ncomp = { SCALAR: 1, VEC2: 2, VEC3: 3, VEC4: 4 }[acc.type];
    if (!comp || !ncomp) { note(rep, "unsupported accessor type"); return null; }
    var stride = view.byteStride || (comp * ncomp);
    var need = off + (acc.count - 1) * stride + comp * ncomp;
    if (need > blob.byteLength) { note(rep, "accessor overruns buffer"); return null; }
    return { blob: blob, off: off, stride: stride, count: acc.count, componentType: acc.componentType, ncomp: ncomp, comp: comp };
  }

  function readPositions(spec, view) {
    var out = [];
    for (var i = 0; i < spec.count; i++) {
      var o = spec.off + i * spec.stride;
      out.push([f32(view, o), f32(view, o + 4), f32(view, o + 8)]);
    }
    return out;
  }

  function readIndices(spec, view) {
    var out = [];
    for (var i = 0; i < spec.count; i++) {
      var o = spec.off + i * spec.stride;
      if (spec.componentType === UNSIGNED_INT) out.push(view.getUint32(o, true));
      else if (spec.componentType === UNSIGNED_SHORT) out.push(view.getUint16(o, true));
      else out.push(view.getUint8(o, true));
    }
    return out;
  }

  function baseColor(doc, prim) {
    var mats = doc.materials || [];
    var mat = prim.material != null ? mats[prim.material] : null;
    var c = mat && mat.pbrMetallicRoughness && mat.pbrMetallicRoughness.baseColorFactor;
    if (c && c.length >= 3) return [c[0], c[1], c[2]];
    return [0.78, 0.78, 0.78];
  }

  function decodeParts(doc, blobs, rep) {
    var views = doc.bufferViews || [];
    var meshes = doc.meshes || [];
    var dvCache = blobs.map(function (b) { return b ? new DataView(b) : null; });
    function dvFor(blob) {
      var i = blobs.indexOf(blob);
      return i >= 0 ? dvCache[i] : new DataView(blob);
    }
    var parts = [];
    var mins = [Infinity, Infinity, Infinity];
    var maxs = [-Infinity, -Infinity, -Infinity];
    var nvert = 0;
    var inst = walkNodes(doc);
    inst.forEach(function (it) {
      var mesh = meshes[it.mesh];
      if (!mesh) return;
      (mesh.primitives || []).forEach(function (prim) {
        var attrs = prim.attributes || {};
        var pacc = (doc.accessors || [])[attrs.POSITION];
        if (!pacc || pacc.componentType !== FLOAT || pacc.type !== "VEC3") {
          note(rep, "POSITION is not embedded FLOAT VEC3");
          return;
        }
        var pspec = accessorBytes(pacc, views, blobs, rep);
        if (!pspec) return;
        var pts = readPositions(pspec, dvFor(pspec.blob));
        var worldPts = pts.map(function (p) { return xformPoint(it.world, p); });
        var idx = null;
        if (prim.indices != null) {
          var iacc = (doc.accessors || [])[prim.indices];
          var ispec = accessorBytes(iacc, views, blobs, rep);
          if (ispec) idx = readIndices(ispec, dvFor(ispec.blob));
        }
        worldPts.forEach(function (p) {
          nvert++;
          for (var k = 0; k < 3; k++) {
            if (p[k] < mins[k]) mins[k] = p[k];
            if (p[k] > maxs[k]) maxs[k] = p[k];
          }
        });
        parts.push({
          positions: worldPts,
          indices: idx,
          color: baseColor(doc, prim),
          mode: prim.mode == null ? MODE_TRIANGLES : prim.mode
        });
      });
    });
    var extents;
    if (nvert === 0) {
      extents = { status: "UNKNOWN", min: null, max: null, vertex_count: 0 };
    } else {
      extents = { status: "DECODED", min: mins, max: maxs, vertex_count: nvert };
    }
    return { parts: parts, extents: extents };
  }

  function resolveBuffers(doc, binPayloads, rep) {
    var buffers = doc.buffers || [];
    var out = [];
    var glbBin = binPayloads[0] || null;
    buffers.forEach(function (buf, i) {
      if (!buf) { out.push(null); return; }
      var uri = buf.uri;
      if (uri == null || uri === "") {
        if (i !== 0 || !glbBin) {
          note(rep, "buffers[" + i + "] not embedded");
          out.push(null);
          return;
        }
        out.push(glbBin);
        return;
      }
      if (isExternalUri(uri)) {
        note(rep, "external buffer blocked: " + uri);
        out.push(null);
        return;
      }
      note(rep, "data URI buffers are not decoded in this bounded viewer");
      out.push(null);
    });
    return out;
  }

  function parseGlb(bytes) {
    var u8 = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
    var rep = emptyReport(u8);
    if (u8.byteLength < 12) {
      note(rep, "truncated header");
      return rep;
    }
    var view = new DataView(u8.buffer, u8.byteOffset, u8.byteLength);
    var magic = u32(view, 0);
    var version = u32(view, 4);
    var length = u32(view, 8);
    rep.header = {
      magic: magic === MAGIC ? "glTF" : "0x" + magic.toString(16),
      version: version,
      length: length,
      length_matches_file: length === u8.byteLength
    };
    if (magic !== MAGIC) { note(rep, "bad magic: expected glTF"); return rep; }
    if (version !== 2) { note(rep, "unsupported GLB version " + version); return rep; }
    if (length !== u8.byteLength) note(rep, "header.length != file bytes");

    var chunks = [];
    var offset = 12;
    var limit = Math.min(length, u8.byteLength);
    while (offset + 8 <= limit) {
      var chunkLen = u32(view, offset);
      var chunkType = u32(view, offset + 4);
      var start = offset + 8;
      var end = start + chunkLen;
      if (end > u8.byteLength) {
        note(rep, "truncated chunk");
        break;
      }
      chunks.push({ type: chunkType, payload: u8.subarray(start, end) });
      offset = end;
    }
    if (!chunks.length || chunks[0].type !== CHUNK_JSON) {
      note(rep, "first chunk is not JSON");
      return rep;
    }
    var doc;
    try {
      doc = JSON.parse(new TextDecoder("utf-8").decode(chunks[0].payload));
    } catch (e) {
      note(rep, "JSON chunk is not valid JSON: " + e);
      return rep;
    }
    if (!doc || typeof doc !== "object") {
      note(rep, "JSON root is not an object");
      return rep;
    }
    var binPayloads = [];
    chunks.forEach(function (c) {
      if (c.type === CHUNK_BIN) {
        var copy = c.payload.slice().buffer;
        binPayloads.push(copy.byteLength === c.payload.byteLength ? copy : c.payload.slice().buffer);
      }
    });
    // Ensure BIN ArrayBuffer is exactly the payload
    binPayloads = chunks.filter(function (c) { return c.type === CHUNK_BIN; }).map(function (c) {
      return c.payload.slice().buffer;
    });

    var counts = countDoc(doc);
    rep.counts = counts;
    rep.triangles = counts.triangles;
    rep.skins = counts.skins;
    rep.animations = counts.animations;
    rep.external_resources = collectExternal(doc);

    if (rep.external_resources.length) {
      note(rep, "blocked external resources: " +
        rep.external_resources.map(function (e) { return e.kind + ":" + e.uri; }).join(", "));
      return rep;
    }

    var blobs = resolveBuffers(doc, binPayloads, rep);
    var decoded = decodeParts(doc, blobs, rep);
    rep.parts = decoded.parts;
    rep.extents = decoded.extents;
    if (counts.triangle_error) note(rep, counts.triangle_error);
    var headerOk = rep.header.magic === "glTF" && rep.header.version === 2 && rep.header.length_matches_file;
    rep.ok = headerOk && rep.malformed.length === 0 && decoded.parts.length > 0;
    if (decoded.parts.length === 0 && rep.malformed.length === 0) {
      note(rep, "no renderable POSITION primitives");
      rep.ok = false;
    }
    return rep;
  }

  function b64ToU8(b64) {
    var bin = atob(b64);
    var u8 = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i);
    return u8;
  }

  root.GlbCompareParse = {
    parseGlb: parseGlb,
    b64ToU8: b64ToU8,
    NOT_PROVEN: NOT_PROVEN,
    isExternalUri: isExternalUri
  };
})(typeof globalThis !== "undefined" ? globalThis : this);
