# CT-COSTUME-TOPO-01 — shared-armhole sample

Not a Zhuge product. **Not G1–G5. Not art PASS.** Not a third tube-tune.

Frozen unread: `build_clothed_v1.py` at `72f854997468595b7492d709d8235db6cd74cf0c`, anatomy, empty-robe v2. This sample is **new files only**. Independent output: `out-topology-v2/`.

## Contract

One garment mesh replaces `Robe_Outer` + two sleeve objects. Sleeve ring 0 **is** the torso armhole loop (same vertex indices). Allowed open loops: neck, hem, cuff L, cuff R. Guan crown and shoe soles are filled faces. Body kept. Feet min Z = 0.

## Run

```bash
cd work/codex-handoff/zhuge-clothed-v1

# Cloud / no Blender — mesh + self-check (UNRUN for GLB/views)
python3 build_clothed_topology_v2.py \
  --source-obj "$(pwd)/../zhuge-anatomy-base/source/base.obj" \
  --output-dir "$(pwd)/out-topology-v2"

python3 check_clothed_topology.py

# Mac Blender 5.2.1 — GLB + color 4-view + clay 4-view (same cameras as v1)
blender -b -P build_clothed_topology_v2.py -- \
  --source-obj "$(pwd)/../zhuge-anatomy-base/source/base.obj" \
  --output-dir "$(pwd)/out-topology-v2"
```

Self-check must PASS on the constructed mesh. Frozen v1 three-shell robe+sleeves and open guan crown must FAIL (negative control).
