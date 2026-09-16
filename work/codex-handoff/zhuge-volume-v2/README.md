# CT-3D-02 诸葛亮真实三维人物 v2 — Codex handoff

Downloadable **draft** handoff. Not a publish. No armature. **Cannot walk.**

This folder is the exclusive work dir. Codex runs it on **Mac Blender 5.2.1**. The cloud VM that authored the script has no Blender and cannot see King’s Mac.

## What this is

Parameterized self-made meshes (Bezier / lathe-of-profile / loft / sweep / thickened sheets). It is **not** a kitbash of a few UV spheres and cones.

v1 was rejected for egg head + dotted features, cylinder beard, bucket hat, smooth cone robe, jagged overlapping cuffs, sausage feathers. v2 builds those parts as readable volumes (sockets / brow / nose / zygoma / jaw; layered tapering beard strands; guan brim + crown folds + hairpin; gravity folds + thick trim; thin-with-thickness feather vanes + veins; hands that wrap the fan handle).

**Art approval is Codex’s local review.** Screenshot count is not approval.

## Scene / figure (for reviewers)

- 宫苑, warm sunlight from upper-left, cool fill, blue-green roof tiles, stone courtyard.
- Look-down miniature, about 35–45° (`view_lookdown.png` plus front / side / back).
- Adult Zhuge Liang, ~1.8 m, ~7.35 heads, feet at Blender Z = 0. Ivory thick robe, cyan-green thick trim with a little gold, cyan-green guan, black hair and long layered beard, white feather fan.
- Single empty `ZhugeLiang_Root`. Palace under `Palace_Root`. Part names are stable for later rigging. Origins are **world-layout, not joint-centered**.

Static posed meshes only. No skin weights, no animation, no walk cycle.

## Units and budget

- Meters.
- Target ≤ 8 materials (shared: roof glaze = guan/trim cyan; shoes use hair black; iris uses hair black).
- Prefer ~20k–45k tris. If the look would clearly degrade, the generator **does not decimate** — `report.json` says so honestly.
- After export, run `validate_glb.py`. glTF is Y-up by spec. The GLB is the **character only** (no courtyard), so `min.y` is the figure, not slabs.
- `report.json` interface: `units`, `rootName`, `upAxis`, `forwardAxis`, `bbox`, `height`, `footOffset`, `skin`, `animations`. Cloud UNRUN marks GLB measurements `UNKNOWN` — do not treat generator AABB as a measured GLB.

## Run on Mac Blender 5.2.1

From this directory. `--output-dir` must come **after** `--`.

```bash
# If `blender` is on PATH:
blender -b -P build_zhuge_v2.py -- --output-dir "$(pwd)"

# Typical Mac app bundle:
/Applications/Blender.app/Contents/MacOS/Blender -b -P build_zhuge_v2.py -- --output-dir "$(pwd)"
```

Renders are slow-ish; GLB-only:

```bash
blender -b -P build_zhuge_v2.py -- --output-dir "$(pwd)" --skip-render
```

Then:

```bash
python3 validate_glb.py zhuge_liang_v2.glb
```

Expected writes **only** into `--output-dir` (overwrite of known names, never a wipe of other folders):

| File | What |
|---|---|
| `zhuge_liang_v2.glb` | Character-only Y-up glTF (`ZhugeLiang_Root`). No stage, ground, cameras, lights, or roof tiles. |
| `zhuge_liang_v2.blend` | Full scene for rendering (palace + lights + cameras stay here) |
| `view_front.png` `view_side.png` `view_back.png` | Review cameras |
| `view_lookdown.png` | ~40° 宫苑 miniature |
| `report.json` | Overwritten with `execution_kind: "real"` |

`--output-dir` defaults to this script’s directory if omitted.

## Cloud / no Blender

```bash
python3 -m py_compile build_zhuge_v2.py validate_glb.py
python3 build_zhuge_v2.py --mesh-stats --output-dir "$(pwd)"
python3 validate_glb.py zhuge_liang_v2.glb   # exits 2 if the GLB is absent (UNRUN)
```

`report.json` with `status: "UNRUN"` and `execution_kind: "expected"` is a census, not an export.

## Constraints honored

- No paid APIs, no downloaded models, no extra installs, no servers.
- Only Blender built-in `bpy` + Python stdlib.
- Does not delete files outside the target dir.
- Does not claim a walk cycle.

## Later rigging (not this version)

Keep `ZhugeLiang_Root` and the part names. Recenter origins to neck / shoulders / wrists before adding an armature. Do not ship a fake walk.
