# CT-COSTUME-01 — standing clothed candidate

Not a Zhuge product. **Not G1–G5. Not art PASS. Not fusion PASS.** No palace. No armature. **Cannot walk.**

Frozen and unread for writes: `zhuge-anatomy-base/` (`613317c` prep, `624e008349a447859ed58417394c68f382e9b887` male) and `zhuge-volume-v2/` empty-robe generators. This package only **reads** the male body pipeline.

Mac `629035d` front still is ART FAIL (guan on the face, bare shoulders). This directory holds the **structural fix**. **Not G1–G5. Not art PASS.**

## Method

Posed-arm **tube sleeves** (shoulder → elbow → wrist on the real posed bones) plus a body-hull robe. Guan from crown/brow. Hands apart on a thick fan handle. Not empty-robe cones. Static posed body kept.

Clothes and body stay **separate objects**.

## Entry

`--source-obj` and `--output-dir` after `--` when launched from Blender. Default output is `out/` in this directory.

```bash
cd work/codex-handoff/zhuge-clothed-v1

# Mac Blender 5.2.1 — color 4-view + grey/clay 4-view
blender -b -P build_clothed_v1.py -- \
  --source-obj "$(pwd)/../zhuge-anatomy-base/source/base.obj" \
  --output-dir "$(pwd)/out"

# Cloud / no Blender (body + cloth census, UNRUN)
python3 build_clothed_v1.py \
  --source-obj "$(pwd)/../zhuge-anatomy-base/source/base.obj" \
  --output-dir "$(pwd)/out"
```

Writes: `zhuge_clothed_v1.glb` / `.blend`, `view_front/side/back/lookdown.png`, `clay_front/side/back/lookdown.png`, `clothed_report.json`.
