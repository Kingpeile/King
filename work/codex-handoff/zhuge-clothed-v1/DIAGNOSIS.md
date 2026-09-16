# CT-COSTUME-DIAG-02 — stop tuning tubes

Gear kept: `72f854997468595b7492d709d8235db6cd74cf0c`. Generator `build_clothed_v1.py` **not edited**. Cloud UNRUN. Not art PASS. Not a third sculpt.

Mac on that commit: Blender exit 0, four color views seen, still **ART_FAIL**. Better: face visible, hands apart, upper arms mostly covered. Hard defects listed by Mac match the mesh construction below.

Read-only audit: `python3 diagnose_topology.py` → `out/topology_diagnosis.json`.

---

## Confirmed from CURRENT CODE (no render required)

Export builds **11 objects**. Robe and sleeves are three `add_mesh` calls. Shared vertex indices robe↔sleeve: **0**. Coincident positions sampled: **0**.

| mesh | open loops | lengths | meaning |
|---|---|---|---|
| `robe_outer` | 2 | 28, 28 | neck + hem. **No armhole.** A closed Z-loft cylinder. |
| `sleeve_l` / `_r` | 2 each | 16, 16 | tube root + cuff. Root is **not** a robe loop. |
| `guan` | 2 | 16, 16 | brim + **open crown 16-gon** |
| `shoe_l` / `_r` | 2 each | 12, 12 | open ankle + **missing sole** |
| `beard` | 2 | 16, 16 | open slab rims |

Elbow stations: bone kink **66.7°**, ring-frame twist **70.9°** (`basis_from_dir` recomputed per segment). `grid_faces` still stitches those rings as quads.

Guan cap2 is `cap1 * 0.40` in XY, not a fill. Last ring radius **0.013–0.085 m** (not a point). `covers_scalp` only tests `max(guan.z) >= scalp.z`.

Shoes are three XY hull rings, `grid_faces(3, 12)`. Enclosure check tests **toe Y** and toe-in-XY-hull only.

Beard: two 5×8 sheets, thickness `0.016 * (1-0.4t)` m (~16→10 mm), lower rows share one `y0+dy` — a plank.

Fan vanes: ±8 mm in Y (`nrm = V(0, 0.008, 0)`).

Robe: 14 horizontal Z stations, convex-hull + radial offset. Wrinkle is a sine on radius. Stiff loft, not cloth.

`build_arm_sleeve` mixes ring-0 origin 40% toward a robe-shoulder **centroid**. It never welds, never deletes torso faces, never bridges loops.

---

## Why the false-PASS checks passed

| check | what it measured | why it can PASS while pixels FAIL |
|---|---|---|
| `covers_scalp=true` | `guan_z_max >= crown_z - 5mm` | A vertex sitting high does not close the 16-gon. Lookdown still sees scalp through the hole. |
| `sleeves_cover_upper/fore=true` | body vert distance to **ideal bone axis** < interpolated radius | Infinite tube, not the triangle mesh. Does not see the 43 mm robe/sleeve gap, the missing armhole, or a camera ray hitting skin. |
| `guan_verts_in_face_front=0` | guan verts with `z∈[1.50,1.655]` and `y<0.02` | Vertex-in-band ≠ occlusion. Crown hole is z>1.70 so it never counts. Front face can be clear while lookdown fails. |
| `shoe_*.ok` | toes not in front of `shoe_y_min`; toes in sole XY hull | Side/back/ankle openings untested. Open top loop is how the body shows. |
| `stitch_gap` ~43 mm | nearest-point between two shells | Distance is not topology. Nearest-point can be “small” or “reported” and the meshes remain two islands. |

Do not treat nearest-point, `inside z≤1.47`, or axis-radius as no-intersection.

---

## Item by item (Mac ART_FAIL ↔ code)

**1. Sleeve and robe still separate hard shells** — **confirmed (code + Mac).** Three objects, zero shared verts, robe has no armhole loop.

**2. Large back shoulder-hole disconnect** — **confirmed (code + Mac).** Robe shoulder is a sealed 28-loop cylinder. Sleeve is another 16-loop tube whose root is a mixed centroid, not a cut in the robe. The camera sees the gap between shells as a hole. Back is worse because the posed arm goes forward; the tube leaves the torso hull at the rear.

**3. Elbow torn into sharp triangles** — **confirmed (code + Mac).** 67° bone kink + 71° ring-frame jump; 6+6 rings; quads across the kink.

**4. Lookdown guan hole, scalp visible** — **confirmed (code + Mac).** Open 16-gon on cap2; `covers_scalp` is maxZ.

**5. Shoe side/back holes / body showing** — **confirmed (code + Mac).** Two boundary loops, no sole, no closed vamp. Toe-Y check cannot see heel/side.

**6. Beard thin long plank** — **confirmed (code + Mac).** ~16 mm slab, constant-y rows after the chin.

**7. Fan thin** — **confirmed (code + Mac).** 16 mm Y-cards.

**8. Robe stiff** — **confirmed (code + Mac).** Z-loft + sine radius. Not this pass’s fold work.

**Face visible / hands apart / upper arms mostly covered** — **confirmed Mac improvement** vs `629035d`. Matches the 72f85499 pose retarget and axis-tube covering the *arm*, not the *join*.

**Unrendered guesses (do not treat as fact):** exact pixel width of the guan hole; whether collar/sash punch on some cameras; 03-style fold quality; how ugly a scripted armhole would look before a human touches it.

---

## One production method (replaces separated tubes)

**Single garment mesh with shared armhole loops.** Not another radius mix. Not empty-robe cones. Not “buy a hanfu.”

How the panels are formed:

1. Keep the posed body as a **separate support object** (already required).
2. Build **one** cloth mesh:
   - Torso grid from neck → hem (existing Z-loft is fine as a start).
   - **Armhole:** at the shoulder row, *do not* close those U-span faces over the armpit. That span becomes a closed boundary loop (same vertex indices).
   - **Sleeve:** extra rings are extruded from **that loop**. The first sleeve ring *is* the armhole. No second object, no 40% centroid mix, no `stitch_gap`.
3. Allowed open loops on that mesh: **neck, hem, cuff L, cuff R** (four). Forbidden: a fifth loop at the shoulder (that is today’s disconnect).
4. Caps as fills, not collapsed rings: guan crown = triangle fan / n-gon fill of the last loop (loop_count on the cap = 0). Shoes = fill the sole loop; close or bind the ankle.

How to actually verify (stdlib + Mac pixels):

- Reuse `diagnose_topology.py` ideas: `island_count(robe+sleeves)==1`; garment `loop_lengths` ∈ {neck, hem, cuff, cuff}; guan has **no** 16-gon at z≈crown; shoes have a filled sole (not 2×12 open).
- Mac **lookdown** of guan: no scalp. Mac **back / lookdown** of shoulder: one cloth, no second shell, no hole. Elbow: no two-tube T-junction.
- Do **not** pass axis-radius, maxZ, or vertex face-band as coverage.

### What this Cloud can do vs Mac Blender

| | Cloud (no bpy) | Mac Blender 5.2.1 |
|---|---|---|
| Shared-loop loft + cap fills in a **new** stdlib file | yes | run it |
| Pixel lookdown / back shoulder / 03 compare | no | **must** |
| Bridge Edge Loops / Fill / sculpt folds interactively | **no** | yes, already installed |
| Cloth sim, viewport retopo | no | yes |

**Exact gap if the loft still looks like plastic:** this Cloud cannot do interactive retopology. Closing holes is a topology rewrite (script or Mac “Bridge Edge Loops” on the posed body). Making it read as 03 cloth is a **human sculpt/retopo pass in the Blender that Mac already has** — not a missing shop asset, not a paid API, not “no free clothes.”

Freeze `build_clothed_v1.py` at 72f85499. A replacement is a **new file**, not a third parameter pass on the tubes.

---

## Effort: continue this method vs change method

**Continue tubes / layered shells:** cannot create shared vertices while `blender_export` adds three meshes. Cannot fill a crown that is an open ring by raising `maxZ`. Cannot stop elbow tearing while two `basis_from_dir` frames meet at 70°. Another mix%/ease pass is the same class as `629035d` → `72f85499`: local pose/radius wins (face, hands, upper arms) and **join/hole class stays**. Diminishing returns. Do not do it.

**Change to shared armhole + filled caps:** one topology rewrite (new generator **or** one Mac retopo of armhole/crown/sole). First-order match to the defects Mac actually photographed. Folds/03 style still later. No calendar promise — the work is “new mesh identity + loop audit + Mac four-view,” not “tune until nearest-point is small.”

---

## One recommended next step (wait for 总控)

**Approve a single-mesh armhole + filled guan/shoe caps as a new file beside frozen 72f85499. Do not retune `build_clothed_v1.py`.**

Minimal acceptance sample (stop if this fails):

1. Mac **lookdown**: guan crown closed, **no scalp**.
2. Mac **back or lookdown shoulder**: **one** cloth surface, **no** second sleeve shell, **no** hole.
3. Diagnostic: robe+sleeves **one** island; garment open loops only neck/hem/cuffs; guan crown loop filled.

Do not start modeling until 总控 approves the method.
