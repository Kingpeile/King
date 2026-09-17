# CT-GLB-INTAKE-01 — offline GLB delivery inspector

Small stdlib reader for **static Blender GLB v2** character deliveries. **Not a universal glTF validator. Not art PASS. Not G1–G5. Not walking.**

Does not edit the input file. Does not construct a character (Kimi). Does not test triangle intersections (Surface). Accessor `min`/`max` is never treated as measured geometry.

Can run without the final Kimi model: fixtures are generated in-process.

## Whitelist (this pack only)

- `glb_intake.py`
- `test_glb_intake.py`
- `README.md`
- `.gitignore`
- `out/glb_intake_report.json`
- `out/delivery_manifest.json`
- `out/self_test.json`

Do not commit character GLB/blend/PNG, anatomy, or other workers' trees.

## One local command

```bash
cd work/codex-handoff/glb-intake-v1
python3 glb_intake.py --self-test --output-dir out
```

To inspect a delivery GLB (read-only; writes only under `--output-dir`):

```bash
python3 glb_intake.py /path/to/character.glb --output-dir out
```

## What it reports

Exact file SHA256 and byte length; GLB v2 header/chunks; mesh, primitive, material, texture, image, skin, and animation counts; external `buffer`/`image` URIs; `extensionsRequired` (none implemented here); declared buffer and bufferView bounds.

`position_extents.status` is `DECODED` only for embedded FLOAT VEC3 POSITION with scene node world matrices applied. Any other layout is **`UNKNOWN`** with a reason. Skin and animation are counted, not applied.

## Not proven

Geometric quality, art quality, and walking are **not** proven by these checks.

## Fixtures (valid and invalid must differ)

| Control | Expect |
|---|---|
| valid cube (lying accessor min/max) | `ok`, extents `[0,0,0]–[1,1,1]`, not the lie |
| truncated buffer | malformed, bounds fail, extents `UNKNOWN` |
| external `mesh.bin` + `albedo.png` | URIs listed, extents `UNKNOWN` |
| node translate×scale cube | decoded `[10,20,30]–[12,23,34]`, not accessor min/max |

[TO_CODEX CT-GLB-INTAKE-01]
