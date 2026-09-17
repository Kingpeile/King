/* Probe repo Three.js / GLTFLoader. Never CDN, never npm install. */
(function (root) {
  "use strict";

  var CANDIDATE_RELATIVE = [
    "vendor/three/build/three.min.js",
    "vendor/three/examples/js/loaders/GLTFLoader.js",
    "js/vendor/three.min.js",
    "js/vendor/GLTFLoader.js"
  ];

  var KNOWN_UNAVAILABLE_ON_DEFAULT = [
    {
      path: "energy-ball/package.json -> three ^0.170.0",
      note: "Closed PR5 only. Vite npm dep, not vendored, no GLTFLoader import, requires install + dev port."
    },
    {
      path: "renovation/esports-room-3d/package.json -> three ^0.175.0",
      note: "Draft PR15 only. OrbitControls, no GLTFLoader, requires install + port 5173."
    },
    {
      path: "work/codex-handoff/**",
      note: "Court handoff packs are Python stdlib. None ship three.js or GLTFLoader.js."
    }
  ];

  function probe(doc) {
    doc = doc || (typeof document !== "undefined" ? document : null);
    var foundThree = typeof root.THREE === "object" && root.THREE !== null;
    var foundLoader = !!(
      (foundThree && root.THREE.GLTFLoader) ||
      root.GLTFLoader ||
      (foundThree && root.THREE.GLTFLoader === undefined && false)
    );
    if (foundThree && root.THREE.GLTFLoader) foundLoader = true;
    var missingFiles = CANDIDATE_RELATIVE.slice();
    return {
      foundThree: foundThree,
      foundGLTFLoader: foundLoader,
      usable: foundThree && foundLoader,
      candidateRelativePaths: CANDIDATE_RELATIVE.slice(),
      missingOnThisBranch: missingFiles,
      knownUnrelatedNpmOnly: KNOWN_UNAVAILABLE_ON_DEFAULT,
      renderer: foundThree && foundLoader ? "three-gltfloader" : "bounded-webgl-fallback",
      gap: foundThree && foundLoader ? null :
        "No Three.js module and no GLTFLoader.js are checked into this branch. " +
        "Default tree, Court work/codex-handoff/*, and this pack contain neither file. " +
        "Unrelated PRs declare npm three but are out of scope, not vendored, and would need install + a port."
    };
  }

  function installNetworkGuard(win) {
    win = win || root;
    if (!win.fetch && !win.XMLHttpRequest) return { installed: false };
    var origFetch = win.fetch && win.fetch.bind(win);
    if (origFetch) {
      win.fetch = function (input) {
        var url = typeof input === "string" ? input : (input && input.url) || "";
        if (/^https?:/i.test(url) || /^\/\//.test(url)) {
          return Promise.reject(new Error("Blocked external request: " + url));
        }
        return origFetch.apply(win, arguments);
      };
    }
    if (win.XMLHttpRequest) {
      var open = win.XMLHttpRequest.prototype.open;
      win.XMLHttpRequest.prototype.open = function (method, url) {
        if (typeof url === "string" && (/^https?:/i.test(url) || /^\/\//.test(url))) {
          throw new Error("Blocked external request: " + url);
        }
        return open.apply(this, arguments);
      };
    }
    return { installed: true };
  }

  root.GlbCompareProbe = {
    probe: probe,
    installNetworkGuard: installNetworkGuard,
    CANDIDATE_RELATIVE: CANDIDATE_RELATIVE
  };
})(typeof globalThis !== "undefined" ? globalThis : this);
