# CT-CLOTH-PROOF-01 — native Blender cloth collision / drape proof

Not a Zhuge product. **Not G1–G5. Not art PASS. Not costume 03.** Not a sleeve, robe, guan, beard, or fan. This package only answers: can Blender `CLOTH` + body `COLLISION` drape a **new** sample sheet over one posed shoulder/upper arm?

Frozen and **not edited**: `zhuge-anatomy-base/` (`624e008` male body), `zhuge-clothed-v1/` (pose helpers only), `zhuge-volume-v2/`. No MPFB install. No loft retune. No v3 garment.

## Method

1. Rebuild the frozen posed male mesh (static two-bone rest pose from clothed-v1 helpers). Body stays visible.
2. Build a **new** moderately subdivided quad sheet **above** the left shoulder / upper arm, initially non-intersecting.
3. Pin **four** medial-posterior verts (`vertex_group_mass='Pin'`). The rest of the sheet is free. Not a fully pinned fake.
4. Run the **same** rest mesh twice, isolated caches, sequential frames **1..60**:
   - `collision_on` — cloth object collision **enabled**
   - `collision_off` — cloth object collision **disabled** (negative control)
5. One parameter set. No grid search. No hardcoded final drapes.

If `collision_off` cannot be told apart from `collision_on`, the check has **no discriminating power** — do not claim PASS.

## Entry

`--source-obj` and `--output-dir` come **after** `--` when launched from Blender.

```bash
cd work/codex-handoff/zhuge-cloth-proof-v1

# Mac Blender 5.2.1 — factory, no autoexec, no network
blender --factory-startup --background --disable-autoexec \
  -P run_cloth_proof.py -- \
  --source-obj "$(pwd)/../zhuge-anatomy-base/source/base.obj" \
  --output-dir "$(pwd)/out"

# Cloud / no bpy (construction + UNRUN evidence only)
python3 run_cloth_proof.py \
  --source-obj "$(pwd)/../zhuge-anatomy-base/source/base.obj" \
  --output-dir "$(pwd)/out"
```

Wall-clock budget for the physics pair: **120 s**. Timeout / failure is reported; the script does **not** pick another parameter set.

## Writes (only under `--output-dir`)

| File | What |
|---|---|
| `evidence.json` | construction, params, pair verdict, UNRUN vs real |
| `collision_on/proof.blend` | on-run scene after last frame |
| `collision_off/proof.blend` | off-run scene after last frame |
| `collision_*/view_{front,side,back,lookdown}.png` | **same** local cameras |
| `collision_*/frames.json` | per-frame COM / minz / speed / displacement |
| `collision_*/timing.json` | seconds, frame count, timeout flag |

No GLB. No animation publish.

## Cloud vs Mac

This cloud has **no bpy**. `evidence.json` with `execution_kind: "expected"` / `physics_status: "UNRUN"` is a construction census, not a drape. PNG/blend/BVH overlap are **UNRUN** until Mac Blender 5.2.1.

BVH overlap pairs (when Mac fills them) are **candidates**, not an exact penetration proof.

## Not this package

Full character, costume quality, 03 still, armature, walk, shop assets, hiding the body, pinning the whole sheet, retuning frozen tubes/lofts.
