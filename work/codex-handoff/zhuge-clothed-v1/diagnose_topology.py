#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CT-COSTUME-DIAG-02 — read-only topology audit of the frozen 72f85499 generator.

Does not edit build_clothed_v1.py. Does not export GLB. Cloud UNRUN.
Prints why holes exist in the mesh, not another sculpt.
"""
from __future__ import annotations

import collections
import importlib.util
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(HERE, "build_clothed_v1.py")


def load_gen():
    spec = importlib.util.spec_from_file_location("clothed_v1_frozen", GEN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def edge_key(a, b):
    return (a, b) if a < b else (b, a)


def boundary_loops(faces, nverts):
    """Walk edges used by exactly one face. Returns loop vertex lists."""
    used = collections.Counter()
    for f in faces:
        k = len(f)
        for i in range(k):
            used[edge_key(f[i], f[(i + 1) % k])] += 1
    adj = collections.defaultdict(list)
    n_bound = 0
    for (a, b), c in used.items():
        if c == 1:
            adj[a].append(b)
            adj[b].append(a)
            n_bound += 1
    seen = set()
    loops = []
    for start in range(nverts):
        if start in seen or start not in adj:
            continue
        loop = [start]
        seen.add(start)
        prev, cur = None, start
        while True:
            nxts = [n for n in adj[cur] if n != prev]
            if not nxts:
                break
            nxt = nxts[0]
            if nxt == start:
                break
            if nxt in seen:
                break
            loop.append(nxt)
            seen.add(nxt)
            prev, cur = cur, nxt
        loops.append(loop)
    return {"boundary_edge_count": n_bound, "loop_count": len(loops), "loop_lengths": [len(L) for L in loops]}


def frame_twist(C, sh, el, ha):
    ax_u = (el - sh).nrm()
    ax_f = (ha - el).nrm()
    bx_u, _ = C.basis_from_dir(ax_u)
    bx_f, _ = C.basis_from_dir(ax_f)
    dot = max(-1.0, min(1.0, bx_u.dot(bx_f)))
    ang = math.degrees(math.acos(dot))
    kink = math.degrees(math.acos(max(-1.0, min(1.0, ax_u.dot(ax_f)))))
    return {"ring_frame_twist_deg": round(ang, 2), "bone_kink_deg": round(kink, 2)}


def identical_vert_pairs(a, b, eps=1e-7):
    """Count coinciding positions (still not shared indices)."""
    n = 0
    for p in a[:: max(1, len(a) // 80)]:
        for q in b:
            if abs(p[0] - q[0]) < eps and abs(p[1] - q[1]) < eps and abs(p[2] - q[2]) < eps:
                n += 1
                break
    return n


def main():
    C = load_gen()
    src = os.path.join(C.ANATOMY_DIR, "source", "base.obj")
    built = C.build_all(src)
    ms = built["meshes"]
    names = ["robe_outer", "sleeve_l", "sleeve_r", "collar", "sash", "shoe_l", "shoe_r", "guan", "beard", "fan", "body"]
    topo = {}
    for name in names:
        m = ms[name]
        topo[name] = {
            "verts": len(m["verts"]),
            "faces": len(m["faces"]),
            "boundary": boundary_loops(m["faces"], len(m["verts"])),
        }
    robe, sl, sr = ms["robe_outer"], ms["sleeve_l"], ms["sleeve_r"]
    # guan cap2 is verts 32..47 (3 rings of 16) before the 8-vert board
    guan_cap_last = ms["guan"]["verts"][32:48]
    cap_xy_r = [math.hypot(p[0], p[1]) for p in guan_cap_last]
    pose = built["pose"]
    V = C.V
    haL, haR = V(pose["hand_l"]), V(pose["hand_r"])
    # rebuild bone points from pose dict is incomplete; use sleeve stations
    stL = sl["stations"]
    # stations[0] shoulder, stations[5] elbow-ish (6 upper rows, 0..5), then fore
    twist = None
    if len(stL) >= 7:
        o0, _ = stL[0]
        o5, _ = stL[5]
        o6, _ = stL[6]
        sh = V(o0)
        el = V(o5)
        ha = V(stL[-1][0])
        twist = frame_twist(C, sh, el, ha)
        # also kink at the actual elbow stations 5→6
        ax_a = (V(o5) - V(o0)).nrm()
        ax_b = (V(stL[-1][0]) - V(o6)).nrm() if False else (V(stL[6][0]) - V(stL[5][0])).nrm()
        kink_local = math.degrees(math.acos(max(-1.0, min(1.0, ax_a.dot(ax_b)))))
        twist["elbow_station_kink_deg"] = round(kink_local, 2)

    report = {
        "task_id": "CT-COSTUME-DIAG-02",
        "generator": "build_clothed_v1.py (read-only)",
        "gear_commit": "72f854997468595b7492d709d8235db6cd74cf0c",
        "status": "UNRUN",
        "blender_present": C.B.bpy is not None,
        "separate_shells": {
            "export_objects": [
                "Anatomy_Body",
                "Robe_Outer",
                "Robe_Sleeve_L",
                "Robe_Sleeve_R",
                "Collar_Inner",
                "Sash",
                "Shoe_L",
                "Shoe_R",
                "Guan",
                "Beard",
                "Fan",
            ],
            "robe_sleeve_shared_indices": 0,
            "robe_sleeve_L_coincident_sample": identical_vert_pairs(robe["verts"], sl["verts"]),
            "note": "Three cloth meshes. No weld. blender_export add_mesh x3.",
        },
        "topology": topo,
        "guan_crown": {
            "cap_rings": 3,
            "last_ring_n": len(guan_cap_last),
            "last_ring_r_min": round(min(cap_xy_r), 5) if cap_xy_r else None,
            "last_ring_r_max": round(max(cap_xy_r), 5) if cap_xy_r else None,
            "top_filled_fan": False,
            "covers_scalp_check_is_maxZ_only": True,
        },
        "elbow": twist,
        "false_pass_from_generator": built.get("structure", {}),
        "notes": [
            "Boundary loops on a z-loft cylinder are the two open ends (neck+hem or cuff+root or sole+ankle).",
            "A filled crown would have loop_count 0 on the cap or a single head-opening loop, not an open 16-gon on top.",
        ],
    }
    out_dir = os.path.join(HERE, "out")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "topology_diagnosis.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("objects", len(report["separate_shells"]["export_objects"]))
    for name in ("robe_outer", "sleeve_l", "guan", "shoe_l", "beard"):
        b = topo[name]["boundary"]
        print(name, "loops", b["loop_count"], "lens", b["loop_lengths"], "bedges", b["boundary_edge_count"])
    print("guan last ring r", report["guan_crown"]["last_ring_r_min"], report["guan_crown"]["last_ring_r_max"])
    print("elbow", twist)
    print("wrote", path)
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
