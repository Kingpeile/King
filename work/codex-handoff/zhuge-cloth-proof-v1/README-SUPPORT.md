# CT-CLOTH-SUPPORT-02 — bounded support sample

Not a garment. **Not 03. Not art PASS.** Proof at `24c90a2de7a709af5369b0a408083101d52ed485` is **frozen** (`run_cloth_proof.py`, `out/`, `PATTERN-DIAG.md` unread for writes).

This file is the new experiment. Old posterior-pin proof is a **historical baseline**, not this run’s on/off control.

## What changed vs 24c90a2d (geometry only)

| | Frozen proof | This sample |
|---|---|---|
| Body | same posed male, visible | same |
| Grid | 12×16, 221 verts, 192 quads | same |
| Rest X / Z | x[0.15087, 0.34612] z=1.53379 | **same** (unrounded from frozen builder) |
| Rest Y | [−0.05750, 0.24835] | **fixed [0.06, 0.21]** |
| Pins | medial u=0, **posterior 4 rows** y=0.191–0.248 (idx 169,182,195,208) | medial u=0, **2+2 adjacent rows** at y≈0.10 / 0.17 |
| Physics | quality 8, mass 0.3, pin_stiffness 20, bending 0.5, distance_min 12 mm, frames 1..60, memory cache | **copied, not retuned** |

Pin indices / xyz (pure Python): **52** (0.151, 0.0975, 1.534), **65** (0.151, 0.106875, 1.534), **143** (0.151, 0.163125, 1.534), **156** (0.151, 0.1725, 1.534). Four distinct collar verts. Not whole-sheet pin. Body stays visible. No hardcoded final drape.

PATTERN-DIAG “先碰后肩、不能翻过肩顶” is **inference** (no per-frame contact). That old report was **not** rewritten. The testable claim here is only the support split.

## Command

Writes **only** `--output-dir` (default `support-sample-02/`). Refuses `out/` and frozen scripts.

```bash
cd work/codex-handoff/zhuge-cloth-proof-v1

blender --factory-startup --background --disable-autoexec \
  -P run_support_sample.py -- \
  --source-obj "$(pwd)/../zhuge-anatomy-base/source/base.obj" \
  --output-dir "$(pwd)/support-sample-02"

# Cloud / no bpy
python3 run_support_sample.py \
  --source-obj "$(pwd)/../zhuge-anatomy-base/source/base.obj" \
  --output-dir "$(pwd)/support-sample-02"
```

Same rest mesh, `collision_on` / `collision_off`. Memory cache actual false before/after, asserted. 60 frames, 120 s wall. No GLB. No param search.

Outputs per arm: `proof.blend`, `frames.json`, `timing.json`, `frame01/` + `frame60/` each `view_{front,side,back,lookdown}.png`. Plus `evidence.json`.

## Cloud

No bpy. `evidence.json` with `physics_status: UNRUN` is construction + pin census, not a drape.

## Mac (one run)

Root: one same-param physics pass. Accept if 4-views show cloth over **front–apex–back**, free verts actually move, no explode. If the shoulder is still bare: **stop this geometry**. No same-scheme retune. No robe.
