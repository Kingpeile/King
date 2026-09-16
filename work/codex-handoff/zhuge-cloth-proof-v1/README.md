# CT-CLOTH-PROOF-01 — native Blender cloth collision / drape proof

Not a Zhuge product. **Not G1–G5. Not art PASS. Not costume 03.** Not a sleeve, robe, guan, beard, or fan. This package only asks whether Blender `CLOTH` + body `COLLISION` produces a **collision response** on a sample sheet. It does **not** claim the sheet covers the shoulder as clothing.

Frozen and **not edited**: `zhuge-anatomy-base/` (`624e008` male body), `zhuge-clothed-v1/` (pose helpers only), `zhuge-volume-v2/`. No MPFB install. No loft retune. No v3 garment. Cloth sheet, pins, collision distance, mass, quality, and frame count are **unchanged** from `e8f774d`.

## Method

1. Rebuild the frozen posed male mesh (static two-bone rest pose from clothed-v1 helpers). Body stays visible.
2. Build a **new** moderately subdivided quad sheet **above** the left shoulder / upper arm, initially non-intersecting.
3. Pin **four** medial-posterior verts (`vertex_group_mass='Pin'`). The rest of the sheet is free. Not a fully pinned fake.
4. Run the **same** rest mesh twice, sequential frames **1..60**:
   - `collision_on` — cloth object collision **enabled**
   - `collision_off` — cloth object collision **disabled** (negative control)
5. One parameter set. No grid search. No hardcoded final drapes.

Both arms use **in-memory** `PointCache` (`use_disk_cache=false`). Actual RNA is read before and after stepping and asserted equal. Cleanup frees **this object's** cache only (no input / other-file deletes). Disk isolation is **not** claimed and was **not** verified.

Coverage is a **visual** question. Verts in the shoulder XY whose z is below the shoulder apex are a **position / target-deviation** count, not inside-body. BVH overlap pairs are **candidates**; `pair_count==0` is not a no-penetration proof. `can_claim_pass` stays **false** until root visual verification. Do not relax thresholds to mint a PASS.

## Entry

`--source-obj` and `--output-dir` come **after** `--` when launched from Blender.

```bash
cd work/codex-handoff/zhuge-cloth-proof-v1

# Mac Blender 5.2.1 — factory, no autoexec, no network
# Evidence-code re-run: same parameters as e8f774d. Do not retune.
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

## Historical e8 Mac run (not this HEAD)

`e8f774d` on Mac Blender 5.2.1: exit 0, 6.89 s, 60 frames × 2, 8 PNGs. `collision_on` mean_disp 0.22919 m, finite, no explode, BVH 0 pairs. `collision_off` mean_disp 0.21029 m, BVH 65 pairs. Collision **response** existed. Visual: cloth fell **behind** the shoulder; front shoulder top still exposed — **not** target coverage. That run is **not** rewritten here.

e8 RNA defect: `use_disk_cache` actual `false` on, `true` off (filepath inherited after the first save). e8 metric defect: verts below shoulder apex labeled as through-body.

## Cloud vs Mac

This cloud has **no bpy**. `evidence.json` with `execution_kind: "expected"` / `physics_status: "UNRUN"` is a construction census, not a drape. PNG/blend/BVH are **UNRUN** until a same-parameter Mac re-run of this evidence-code HEAD.

## Not this package

Full character, costume quality, 03 still, armature, walk, shop assets, hiding the body, pinning the whole sheet, retuning frozen tubes/lofts, turning the sample sheet into a robe.
