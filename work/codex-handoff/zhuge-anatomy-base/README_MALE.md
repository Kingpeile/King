# CT-BASE-02 — adult-male fuller-volume anatomy candidate

Not a Zhuge product. **Not G1–G5. Not art PASS.** No armature. **Cannot walk.** Does not touch `zhuge-volume-v2/`. Does not rewrite `prepare_anatomy_base.py`.

Mac `613317c` remains the **BASE-01 baseline** (exit 0, GLB 626508B, 26756 tri, height 1.78 m, minY 0, 14517 UVs). This candidate is a body-first morph on that same topology.

## Morph pin

See `source/targets/INVENTORY.md`. Official MPFB2 CC0 `.target.gz` from commit `437dd513888a92399d1d3200d2e80859fae55abc`. SHA-checked. No plugin install.

## Entry

`--source-obj` and `--output-dir` after `--`. Default output is `male_out/` (does not overwrite BASE-01 `anatomy_base.glb`).

```bash
cd work/codex-handoff/zhuge-anatomy-base

# Mac Blender 5.2.1 — same 4 grey cameras as BASE-01
blender -b -P apply_male_volume.py -- \
  --source-obj "$(pwd)/source/base.obj" \
  --output-dir "$(pwd)/male_out"

# Cloud / no Blender (SHA + morph + body filter, UNRUN)
python3 apply_male_volume.py \
  --source-obj "$(pwd)/source/base.obj" \
  --output-dir "$(pwd)/male_out"
```

Writes: `anatomy_male.glb` / `.blend`, `view_front/side/back/lookdown.png`, `male_volume_report.json`.

## Kept / dropped

Same as BASE-01: morph the **full** 19158-vert hm08 mesh, **then** keep OBJ group `body` only. Drop `helper-*` / `joint-*`. UV + face order preserved. Uniform height scale to 1.78 m, feet at 0. No cone robe.
