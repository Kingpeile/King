# CT-3D-EXPERIMENT-01 — continuous robe (one trial)

Frozen original builder stays at `ea39968852c001ef5321fa476a31b5be3921c578`. **Do not edit** `build_zhuge_v2.py`. **Do not rewrite** `report.json`. This experiment is a second entry next to the frozen script. Not art approval. Not a publish.

## Entry

`--output-dir` must come **after** `--`. Default is `experiment_out/` beside this file (refuses to write into the frozen handoff dir).

```bash
# Mac Blender 5.2.1
blender -b -P experiment_continuous_robe.py -- --output-dir "$(pwd)/experiment_out"

# GLB only
blender -b -P experiment_continuous_robe.py -- --output-dir "$(pwd)/experiment_out" --skip-render

# Cloud / no Blender (census only, UNRUN)
python3 experiment_continuous_robe.py --mesh-stats --output-dir "$(pwd)/experiment_out"
python3 validate_glb.py experiment_out/zhuge_liang_v2_experiment.glb   # exits 2 if absent
```

Writes only into `--output-dir`: `zhuge_liang_v2_experiment.glb` / `.blend`, `view_front/side/back/lookdown.png`, `experiment_report.json`, `experiment_mesh_stats.json`. Never `report.json`.

## What changed

Imports the frozen builder. Reuses head / guan / beard, hands / sleeves, fan, cameras, materials, export helpers.

**Replaces** `Robe_Body` + `Skirt_Outer`/`Skirt_Inner` + `Robe_Panel_Outer` + `Robe_Panel_ShoulderSeal` with **one** open wrap `Robe_Continuous`: interpolated neck→shoulder→chest→waist→hem rings, `thicken_sheet` 6 mm. No second shell. No horizontal shoulder-top seal. Front opening kept (frozen wrap angles; back seam width 0). Inner lining = two short inset strips at the 交领 only. Sash and hem trim follow this wrap’s waist / hem verts — no independent ellipses.

Does not move head / beard / fan / sleeve roots / wrists. No palace, no other characters.

## Unverified (Mac five-view)

Cloud has no Blender. Compare after a real Mac run:

1. Lookdown shoulder ring gone
2. Back seam no regression
3. Sash continuous
4. Natural shoulder→chest robe
5. No new intersections
