# CT-COSTUME-01 — standing clothed candidate

Not a Zhuge product. **Not G1–G5. Not art PASS. Not fusion PASS.** No palace. No armature. **Cannot walk.**

Frozen and unread for writes: `zhuge-anatomy-base/` (`613317c` prep, `624e008349a447859ed58417394c68f382e9b887` male) and `zhuge-volume-v2/` empty-robe generators. This package only **reads** the male body pipeline.

Mac accepted `624e008` as the clothing **support body** (exit 0, 626508B / 26756 tri, 1.78 m, minY 0). Still too athletic-slender vs the 03 still — clothes next, on that real body.

## Method

**Body-hull-offset continuous panels** around the posed male mesh, plus hanging wide sleeves from the source OBJ `joint-l/r-shoulder` centroids.

Not a licensed MHCLO fit: there is no CC0 adult-male 交领袍 for hm08 without installing MPFB. The female 襦裙 is excluded. Not the frozen cone/ring/tube empty-robe path.

Static two-bone rest pose (hands in front of the chest). That is not an armature.

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
