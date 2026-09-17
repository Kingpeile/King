# CT-GLB-COMPARE-01 — offline dual-GLB compare viewer

Bounded **file://** two-pane viewer for two user-selected self-contained GLB v2 files. Cloud cannot open local scholar/Kimi paths; pick files explicitly.

**Not art PASS. Not G1–G5. Walking not proven.** Does not modify inputs. Does not upload. Does not fetch `mesh.bin` / `albedo.png` / `http(s)` URIs. Does not edit PR22, character assets, or palace scene/identity controls.

Reported context (not measured here): local scholar **1 475 201** triangles; Kimi delivery **119 999** triangles, **18.35 MB**, **0 skins**, **0 animations**, awaiting root art review.

## Dependency gap (exact)

**No Three.js and no GLTFLoader are checked into this branch.** Nothing was installed, no CDN, no new port.

| Wanted | On `claude/add-claude-documentation-2QQ1A` + this pack |
|---|---|
| `three` module / `three.min.js` | **missing** |
| `GLTFLoader.js` | **missing** (also absent from all remote refs) |

Unrelated trees that **must not** be reused here (would need npm install + a dev port, and they still do not ship GLTFLoader):

- `energy-ball/package.json` → `three ^0.170.0` (closed PR5)
- `renovation/esports-room-3d/package.json` → `three ^0.175.0` (draft PR15, OrbitControls only)

Court `work/codex-handoff/*` packs are Python. PR22 `work/codex-handoff/glb-intake-v1/` is a metadata inspector — **unchanged**.

Fallback renderer: `js/webgl-pane.js` draws **embedded FLOAT VEC3** triangles with a shared camera. PBR textures, Draco, skins-as-pose, and animations are **not** applied.

## Whitelist (this pack only)

```
work/codex-handoff/glb-compare-v1/
  index.html  compare.css  README.md  .gitignore  SHA256SUMS
  make_fixtures.py  test_glb_compare.py  test_node.js
  js/*.js
  fixtures/*   (honest cubes/tets, not characters)
  out/self_test.json  out/dependency_gap.json
  screenshots/*
```

## One local command (no server)

```bash
cd work/codex-handoff/glb-compare-v1
python3 test_glb_compare.py
```

Open `index.html` in a browser as **file://** (do not start a port). Choose a GLB for A and for B. Optional `index.html?fixtures=1` loads the bundled cubes for a smoke view. `?selftest=1` runs in-page behavioral checks. `?error=1` loads invalid A + fixture B.

Cloud Chrome 148: in-page selftest **25/25 PASS**. Screenshots under `screenshots/` (`desktop-dual.png`, `narrow.png`, `empty.png`, `error-invalid.png`). See `screenshots/BROWSER-STATUS.txt`.

## Shared view

- One orbit/pan/zoom rig drives **both** canvases and the same world-space light.
- Presets: front / 45° / side / back.
- Materials: original `baseColorFactor` / neutral gray / wireframe.
- Default: **world transforms preserved**, camera frames the **union AABB** (shared world scale).
- Optional normalize is a labeled checkbox: **NORMALIZED (not world scale)** appears on each pane when on.

## Counts

Each pane reports actual **triangles / skins / animations / bytes / sha256**. Skins and animations are counted, not played. Invalid files and external-URI files error that side only.

Either side can be replaced. Rapid A1→A2: generation token cancels the stale load and disposes GPU buffers.

Narrow screens (`≤720px`) stack the panes.

## Not proven

Geometric quality, art quality, walking, G1–G5.

[TO_CODEX CT-GLB-COMPARE-01]
