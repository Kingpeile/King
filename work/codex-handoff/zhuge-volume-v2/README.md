# CT-3D-02 诸葛亮真实三维人物 v2 — Codex handoff

Downloadable **draft** handoff. Not a publish. No armature. **Cannot walk.**

This folder is the exclusive work dir. Codex runs it on **Mac Blender 5.2.1**. The cloud VM that authored the script has no Blender and cannot see King’s Mac.

## What this is

Parameterized self-made meshes (Bezier / lathe-of-profile / loft / sweep / thickened sheets). It is **not** a kitbash of a few UV spheres and cones.

v1 was rejected for egg head + dotted features, cylinder beard, bucket hat, smooth cone robe, jagged overlapping cuffs, sausage feathers. v2 builds those parts as readable volumes (sockets / brow / nose / zygoma / jaw; layered tapering beard strands; guan brim + crown folds + hairpin; gravity folds + thick trim; thin-with-thickness feather vanes + veins; hands that wrap the fan handle).

**Art approval is Codex’s local review.** Screenshot count is not approval.

## Scene / figure (for reviewers)

- 宫苑, warm sunlight from upper-left, cool fill, blue-green roof tiles, stone courtyard.
- The four **review** views (`view_front/side/back/lookdown`) frame the character AABB with **10% margin**, on a **neutral ground**, with the palace stage **hidden** so railings cannot cover the feet. NDC-in-frame alone is not enough.
- `view_lookdown_palace.png` is a separate 宫苑 lookdown fusion (character + palace). It is not a review-camera substitute.
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
| `view_front.png` `view_side.png` `view_back.png` `view_lookdown.png` | Review cameras: character + neutral ground, palace hidden |
| `view_lookdown_palace.png` | Separate palace lookdown fusion |
| `report.json` | Overwritten with `execution_kind: "real"` |

`--output-dir` defaults to this script’s directory if omitted.

## Mac 5.2.1 regression (commit 64a0192)

Codex ran factory-startup background on Mac Blender 5.2.1. Mesh build succeeded. GLB export failed:

`FileNotFoundError [Errno 2] No such file or directory: ''`

`filepath` is **not** on `bpy.types.EXPORT_SCENE_OT_gltf.bl_rna.properties` but **is** on `bpy.ops.export_scene.gltf.get_rna_type().properties`. The old filter used class `bl_rna` and dropped `filepath`, so the exporter opened `''`.

This handoff filters through `bpy.ops.*.get_rna_type().properties` (gltf and `save_as_mainfile`). If `filepath` would be missing or empty after filtering, the script raises instead of calling the operator. Mac commit `9746c60` confirmed GLB/blend/four views export.

## Mac art review (commit e5282c0) — CHANGES_REQUESTED, not a publish

Mac Blender 5.2.1 exit 0 on `e5282c0bd63246ee616a19c49e8848d4496ab95c`. GLB 917288B / 39144 tris / 64 mesh / 7 materials, minY 0, no skin/animation, validator issues=[]. Front/lookdown: head+feet in frame, wrists at cuffs — real improvement. Still not published.

Remaining:
- Side/back feet hidden by foreground railing (NDC-in-frame is not enough)
- Lookdown holes / folded edges on both shoulders; chest still armor plates
- Annulus only sealed thickness rims; yoke/torso/collar were independent intersecting lofts
- Soft gravity folds, fan vane normals, beard bundles, guan crown holes

**Do not treat bbox overlap / annulus / `all_join_overlaps` as connected.**

This revision is **one ①②③ candidate**:
1. Four review views hide `Palace_Root` and show `Review_Ground`. Separate `view_lookdown_palace.png`.
2. One `Robe_Body` (no yoke+torso shells). Sleeve roots are filled disks buried in the shoulder. 交领 bands sit on the chest.
3. Gravity folds + waist transition; thinner fan sheets with consistent face normals; beard as wide bundles; guan crown capped.

**No art approval.** Cloud did not re-export (UNRUN). `construction_audit` is an inventory, not PASS.

## Mac five-view re-review (commit aae56dcd) — CHANGES_REQUESTED, not a publish

Mac Blender 5.2.1 exit 0 on `aae56dcdf517eeedee60329d77d889589c0cbce4`. GLB 816144B / 35504 tris / 66 mesh / 7 materials, minY 0, validator issues=[]. **KEEP:** shoulder holes gone, side/back feet unobstructed, side feathers visible. Still not published.

Remaining (this revision packages **only** these four; no generic polish; do not regress shoulders / review cameras / wrists):

1. Collar was a floating X ribbon (`build_collar` = arbitrary 3D path + Bishop). Now each vertex is sampled on `Robe_Body` and offset 2–4 mm along the surface normal. True 右衽 (right lapel over left) ending at the waist side — not a left-right symmetric X hanging in air.
2. Hem cyan trim was broken floating chunks (old 48-seg / 12-wave contour vs `BODY_N` 40 skirt). Trim + gold piping are lofted from the same `Skirt_Outer` bottom-ring vertices/normals.
3. Skirt front/back was a smooth cone; side waist had a step. Outer skirt now starts on the exact body waist ring. Long/short gravity folds (`cloth_fold_ring`), not 8 equal gear teeth. Full fabric volume kept.
4. Front fan was a knife-edge (face yawed sideways). Fan is rotated around the grip so front/lookdown read feather faces; side thickness kept; tips taper to a point. Beard is converging arc bundles with uneven tails, not parallel rods.

**No art approval.** Cloud did not re-export (UNRUN). Do not treat generator census as a Mac five-view.

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
