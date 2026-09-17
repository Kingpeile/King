# CT-SURFACE-VERIFY-01-CODE — surface constraint proof

Independent geometry diagnostics. **Not a 纶巾. Not a new art mesh. Not G1–G5. Not an art PASS.**  
Does not edit PR20 `build_cap_surface.py` (`4b81dc46a1f843749cae2351151e1ab55a4923d8`).

`sample_cloth_grid` mixes nearby scalp vertices in (θ,h). That is not triangle projection. `gates_ok` does not measure barycentric residual or exact triangle intersection.

## Whitelist (this pack only)

- `surface_constraint_proof.py`
- `README.md`
- `.gitignore`
- `out/surface_constraint_report.json`

Do not commit anatomy, PR20 cap tree, PNG, GLB, or blend.

Read-only inputs (checkout as siblings, do not add to this PR):

- `../zhuge-anatomy-base` @ `624e008349a447859ed58417394c68f382e9b887`
- `../zhuge-cap-surface-v1/build_cap_surface.py` @ `4b81dc46a1f843749cae2351151e1ab55a4923d8`

## One Mac command

```bash
cd work/codex-handoff/surface-constraint-proof-v1
blender --factory-startup --background --disable-autoexec \
  -P surface_constraint_proof.py -- \
  --anatomy-dir "$(pwd)/../zhuge-anatomy-base" \
  --cap-script "$(pwd)/../zhuge-cap-surface-v1/build_cap_surface.py" \
  --output-dir "$(pwd)/out"
```

Same tests run under `python3` if bpy is missing. Blender export/render stays **UNRUN**.

## Cloud result (no bpy)

`python3 surface_constraint_proof.py --anatomy-dir … --cap-script … --output-dir out`  
exit 0. `controls_ok=true` (11/11). `blender_present=false`. export/render **UNRUN**.

| Control | Result |
|---|---|
| centroid → bary (1/3,1/3,1/3), residual 0 | PASS |
| off-plane residual = 10 mm | PASS |
| weighted vertex mix ≠ projection | PASS |
| piercing pair → PENETRATING | PASS |
| far pair → SEPARATED | PASS |
| shared vertex only → not pierce | PASS |
| closest feature is open edge → UNKNOWN | PASS |
| interior on an open mesh still ON_TRIANGLE | PASS |
| shared open edge → UNKNOWN | PASS |

Old cap `4b81dc4` evidence (builder `gates_ok=true`):

| Check | Number |
|---|---|
| cloth-grid samples | 197 |
| ON_TRIANGLE | 1 |
| ON_BOUNDARY | 2 |
| UNKNOWN (open hem/ear cut) | 4 |
| OFF_SURFACE | 190 |
| residual median / max | 3.31 mm / 24.6 mm |
| residual > 1 mm / > 1 cm | 169 / 22 |
| exact inner∩head (AABB 4130, all exact-tested) | 548 PENETRATING |
| exact outer∩head (AABB 2659, all exact-tested) | 174 PENETRATING |
| unknown intersection pairs | 0 (both meshes closed) |

Numbers are not art PASS. They show why `gates_ok` was false confidence.

## Limitations

- Float64 predicates, not exact rationals. EPS on slivers.
- AABB is a reject filter; every candidate is exact-tested. Non-candidates are SEPARATED.
- Open-boundary contact is UNKNOWN, never PENETRATING/SEPARATED.
- Does not patch `sample_cloth_grid`. Does not emit a new cap.
- Cloud has no bpy. Mac command still does not export GLB/PNG.

[TO_CODEX CT-SURFACE-VERIFY-01-CODE]
