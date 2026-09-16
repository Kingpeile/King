# CT-BASE-01 — MPFB2 anatomy start (body group only)

Not a Zhuge product. **Not G1–G5. Not art PASS.** No armature. **Cannot walk.** Frozen generators in `work/codex-handoff/zhuge-volume-v2/` are untouched.

King accepted MPFB2 `base.obj` as an anatomy start. This package asks: can complete human topology serve as a high-quality production start? An empty robe must not stand in for a body.

## Pinned source (CC0)

| | |
|---|---|
| commit | `437dd513888a92399d1d3200d2e80859fae55abc` |
| path | `src/mpfb/data/3dobjs/base.obj` |
| SHA256 | `8e761e6624b8f54536409135d1636da63b32486a90d4897f84e121d144f6fb4c` |
| bytes | 1749303 |
| license | MPFB `LICENSE.md` section C + OBJ header = CC0 |

Vendored copy (data file only — **do not clone/install MPFB**): `source/base.obj`.

If you need to re-fetch:

```bash
curl -fsSL -o source/base.obj \
  "https://raw.githubusercontent.com/makehumancommunity/mpfb2/437dd513888a92399d1d3200d2e80859fae55abc/src/mpfb/data/3dobjs/base.obj"
```

The script **fails loud** if SHA256 or size does not match the pin.

## Entry

`--source-obj` and `--output-dir` come **after** `--` when launched from Blender.

```bash
cd work/codex-handoff/zhuge-anatomy-base

# Mac Blender 5.2.1
blender -b -P prepare_anatomy_base.py -- \
  --source-obj "$(pwd)/source/base.obj" \
  --output-dir "$(pwd)"

# GLB only
blender -b -P prepare_anatomy_base.py -- \
  --source-obj "$(pwd)/source/base.obj" \
  --output-dir "$(pwd)" --skip-render

# Cloud / no Blender (SHA + census, UNRUN)
python3 prepare_anatomy_base.py \
  --source-obj "$(pwd)/source/base.obj" \
  --output-dir "$(pwd)"
```

Writes only into `--output-dir`: `anatomy_base.glb` (Y-up, grey), `anatomy_base.blend`, `view_front/side/back/lookdown.png`, `anatomy_report.json`.

## Kept / dropped

- **Kept:** OBJ group `body` only (head/neck/torso/limbs/hands/feet). Face order and UVs preserved. Uniform scale to **1.78 m** height, feet at **0**. No heavy deform, no retopo.
- **Dropped:** `helper-*` and `joint-*` (not skin).
- **Not this package:** clothes, beard, fan, palace, armature, MPFB plugin, frozen Zhuge generators.

## UNRUN

This cloud has no Blender. `anatomy_report.json` with `execution_kind: "expected"` / `status: "UNRUN"` is a SHA + body-group census, not an export. Do not treat missing PNG/GLB as rendered views.
