/* Generation-token loader: rapid A1→A2 keeps only A2. Disposes GPU of losers. */
(function (root) {
  "use strict";

  function createSide(id) {
    return {
      id: id,
      token: 0,
      stats: null,
      error: null,
      empty: true,
      parts: null,
      fileName: null,
      bytes: 0,
      sha256: null
    };
  }

  function disposeSide(side, gpuDispose) {
    if (gpuDispose) gpuDispose(side);
    side.stats = null;
    side.parts = null;
    side.empty = true;
    side.fileName = null;
    side.bytes = 0;
    side.sha256 = null;
  }

  function hexSha(buf) {
    if (!root.crypto || !root.crypto.subtle) return Promise.resolve(null);
    return root.crypto.subtle.digest("SHA-256", buf).then(function (d) {
      var u = new Uint8Array(d);
      var s = "";
      for (var i = 0; i < u.length; i++) s += (u[i] + 256).toString(16).slice(-2);
      return s;
    }).catch(function () { return null; });
  }

  function beginLoad(side) {
    return ++side.token;
  }

  function isCurrent(side, token) {
    return token === side.token;
  }

  function applyParsed(side, token, parsed, fileName, opts) {
    opts = opts || {};
    if (!isCurrent(side, token)) return { cancelled: true, token: token, side: side.id };
    var gpuDispose = opts.gpuDispose;
    var gpuUpload = opts.gpuUpload;
    if (parsed.external_resources && parsed.external_resources.length) {
      disposeSide(side, gpuDispose);
      side.error = "Blocked external resources (no fetch/upload): " +
        parsed.external_resources.map(function (e) { return e.uri; }).join(", ");
      side.empty = true;
      return { blocked: true, token: token, side: side.id, report: parsed };
    }
    if (!parsed.ok) {
      disposeSide(side, gpuDispose);
      side.error = (parsed.malformed && parsed.malformed.length)
        ? parsed.malformed.join("; ")
        : "invalid GLB";
      side.empty = true;
      return { error: true, token: token, side: side.id, report: parsed };
    }
    disposeSide(side, gpuDispose);
    side.empty = false;
    side.error = null;
    side.parts = parsed.parts;
    side.fileName = fileName || "untitled.glb";
    side.bytes = parsed.bytes;
    side.stats = {
      triangles: parsed.triangles,
      skins: parsed.skins,
      animations: parsed.animations,
      extents: parsed.extents,
      not_proven: parsed.not_proven
    };
    if (gpuUpload) gpuUpload(side);
    return { ok: true, token: token, side: side.id, report: parsed };
  }

  function loadBytesWithToken(side, token, bytes, fileName, opts) {
    opts = opts || {};
    if (!isCurrent(side, token)) {
      return Promise.resolve({ cancelled: true, token: token, side: side.id });
    }
    var parse = opts.parse || root.GlbCompareParse.parseGlb;
    var u8 = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
    var parsed = parse(u8);
    if (!isCurrent(side, token)) {
      return Promise.resolve({ cancelled: true, token: token, side: side.id });
    }
    var slice = u8.buffer.slice(u8.byteOffset, u8.byteOffset + u8.byteLength);
    return hexSha(slice).then(function (sha) {
      var result = applyParsed(side, token, parsed, fileName, opts);
      if (result.ok) side.sha256 = sha;
      return result;
    });
  }

  function loadBytes(side, bytes, fileName, opts) {
    var token = beginLoad(side);
    side.error = null;
    return loadBytesWithToken(side, token, bytes, fileName, opts);
  }

  function loadFile(side, file, opts) {
    if (!file) {
      side.error = "no file";
      return Promise.resolve({ error: true, token: side.token, side: side.id });
    }
    var token = beginLoad(side);
    side.error = null;
    return Promise.resolve(file.arrayBuffer()).then(function (buf) {
      return loadBytesWithToken(side, token, buf, file.name, opts);
    });
  }

  root.GlbCompareLoad = {
    createSide: createSide,
    disposeSide: disposeSide,
    beginLoad: beginLoad,
    isCurrent: isCurrent,
    loadBytes: loadBytes,
    loadBytesWithToken: loadBytesWithToken,
    loadFile: loadFile
  };
})(typeof globalThis !== "undefined" ? globalThis : this);
