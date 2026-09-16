#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CT-COSTUME-TOPO-01 — topology audit on constructed verts/faces.

Pure Python. Operates on real mesh arrays (not slogans, not ideal-axis).
Negative control: frozen 72f85499 three-shell robe+sleeves MUST FAIL.
"""
from __future__ import annotations

import collections
import importlib.util
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FROZEN_V1 = os.path.join(HERE, "build_clothed_v1.py")
FROZEN_V1_COMMIT = "72f854997468595b7492d709d8235db6cd74cf0c"
V2 = os.path.join(HERE, "build_clothed_topology_v2.py")


def load_mod(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def edge_key(a, b):
    return (a, b) if a < b else (b, a)


def face_area3(verts, i, j, k):
    ax, ay, az = verts[i]
    bx, by, bz = verts[j]
    cx, cy, cz = verts[k]
    ux, uy, uz = bx - ax, by - ay, bz - az
    vx, vy, vz = cx - ax, cy - ay, cz - az
    nx = uy * vz - uz * vy
    ny = uz * vx - ux * vz
    nz = ux * vy - uy * vx
    return 0.5 * math.sqrt(nx * nx + ny * ny + nz * nz)


def face_centroid(verts, face):
    n = float(len(face))
    return (
        sum(verts[i][0] for i in face) / n,
        sum(verts[i][1] for i in face) / n,
        sum(verts[i][2] for i in face) / n,
    )


def edge_use(faces):
    used = collections.Counter()
    for f in faces:
        k = len(f)
        for i in range(k):
            used[edge_key(f[i], f[(i + 1) % k])] += 1
    return used


def walk_boundary_loops(faces, nverts):
    used = edge_use(faces)
    adj = collections.defaultdict(list)
    n_bound = 0
    for (a, b), c in used.items():
        if c == 1:
            adj[a].append(b)
            adj[b].append(a)
            n_bound += 1
    bound_degree = {v: len(neigh) for v, neigh in adj.items()}
    seen = set()
    loops = []
    open_chains = 0
    for start in range(nverts):
        if start in seen or start not in adj:
            continue
        loop = [start]
        seen.add(start)
        prev, cur = None, start
        closed = False
        while True:
            nxts = [n for n in adj[cur] if n != prev]
            if not nxts:
                open_chains += 1
                break
            nxt = nxts[0]
            if nxt == start:
                closed = True
                break
            if nxt in seen:
                break
            loop.append(nxt)
            seen.add(nxt)
            prev, cur = cur, nxt
        loops.append({"verts": loop, "closed": closed, "length": len(loop)})
    return {
        "used": used,
        "boundary_edge_count": n_bound,
        "loop_count": len(loops),
        "loops": loops,
        "bound_degree": bound_degree,
        "open_chains": open_chains,
    }


def connected_face_components(faces):
    """Flood-fill faces that share an edge. Isolated verts ignored."""
    edge_to_faces = collections.defaultdict(list)
    for fi, f in enumerate(faces):
        k = len(f)
        for i in range(k):
            edge_to_faces[edge_key(f[i], f[(i + 1) % k])].append(fi)
    adj = collections.defaultdict(set)
    for flist in edge_to_faces.values():
        for i in range(len(flist)):
            for j in range(i + 1, len(flist)):
                adj[flist[i]].add(flist[j])
                adj[flist[j]].add(flist[i])
    seen = set()
    comps = 0
    for i in range(len(faces)):
        if i in seen:
            continue
        comps += 1
        stack = [i]
        seen.add(i)
        while stack:
            u = stack.pop()
            for v in adj[u]:
                if v not in seen:
                    seen.add(v)
                    stack.append(v)
    return comps


def loop_stats(verts, loop):
    pts = [verts[i] for i in loop["verts"]]
    n = max(1, len(pts))
    mx = sum(p[0] for p in pts) / n
    my = sum(p[1] for p in pts) / n
    mz = sum(p[2] for p in pts) / n
    rs = [math.hypot(p[0] - mx, p[1] - my) for p in pts]
    return {
        "length": loop["length"],
        "closed": loop["closed"],
        "mean_x": round(mx, 5),
        "mean_y": round(my, 5),
        "mean_z": round(mz, 5),
        "max_z": round(max(p[2] for p in pts), 5) if pts else None,
        "min_z": round(min(p[2] for p in pts), 5) if pts else None,
        "mean_radius": round(sum(rs) / n, 5),
    }


def label_garment_loops(verts, loops):
    """Neck / hem / cuff L / cuff R from coordinates, not names."""
    if len(loops) != 4:
        return {"ok": False, "reason": "loop_count=%s" % len(loops), "labeled": {}}
    stats = [loop_stats(verts, L) for L in loops]
    order_z = sorted(range(4), key=lambda i: stats[i]["mean_z"])
    hem_i = order_z[0]
    neck_i = order_z[-1]
    rest = [i for i in range(4) if i not in (hem_i, neck_i)]
    if len(rest) != 2:
        return {"ok": False, "reason": "could not split cuffs", "labeled": {}}
    a, b = rest
    if stats[a]["mean_x"] >= stats[b]["mean_x"]:
        l_i, r_i = a, b
    else:
        l_i, r_i = b, a
    labeled = {
        "neck": stats[neck_i],
        "hem": stats[hem_i],
        "cuff_l": stats[l_i],
        "cuff_r": stats[r_i],
    }
    ok = (
        labeled["neck"]["mean_z"] > labeled["hem"]["mean_z"] + 0.4
        and labeled["cuff_l"]["mean_x"] > 0.02
        and labeled["cuff_r"]["mean_x"] < -0.02
        and labeled["neck"]["mean_z"] > 1.35
        and labeled["hem"]["mean_z"] < 0.25
    )
    return {"ok": ok, "labeled": labeled, "reason": None if ok else "coordinate labels inconsistent"}


def audit_manifold(verts, faces):
    nverts = len(verts)
    used = edge_use(faces)
    bound = walk_boundary_loops(faces, nverts)
    non_manifold = []
    for e, c in used.items():
        if c > 2:
            non_manifold.append({"edge": e, "faces": c})
    interior_ok = all(c == 2 for e, c in used.items() if c != 1)
    # boundary verts: degree 2 on the boundary graph
    bad_deg = {int(v): d for v, d in bound["bound_degree"].items() if d != 2}
    # duplicate faces
    seen_f = collections.Counter()
    dup = 0
    degenerate = 0
    tiny = 0
    for f in faces:
        key = tuple(sorted(f))
        seen_f[key] += 1
        uniq = set(f)
        if len(uniq) < 3:
            degenerate += 1
            continue
        area = 0.0
        for i in range(1, len(f) - 1):
            area += face_area3(verts, f[0], f[i], f[i + 1])
        if area < 1e-10:
            tiny += 1
    dup = sum(1 for n in seen_f.values() if n > 1)
    # obvious spikes: very long edges on a human-scale mesh
    long_edges = 0
    for (a, b), c in used.items():
        pa, pb = verts[a], verts[b]
        L = math.hypot(pa[0] - pb[0], pa[1] - pb[1])
        L = math.hypot(L, pa[2] - pb[2])
        if L > 0.38:
            long_edges += 1
    return {
        "components": connected_face_components(faces),
        "loop_count": bound["loop_count"],
        "loop_lengths": [L["length"] for L in bound["loops"]],
        "loops_closed": all(L["closed"] for L in bound["loops"]),
        "open_chains": bound["open_chains"],
        "non_boundary_edges_have_2_faces": interior_ok and not non_manifold,
        "non_manifold_edges": non_manifold[:8],
        "boundary_verts_degree_2": len(bad_deg) == 0,
        "boundary_degree_bad_n": len(bad_deg),
        "duplicate_faces": dup,
        "degenerate_faces": degenerate,
        "tiny_area_faces": tiny,
        "long_edges_gt_38cm": long_edges,
        "no_duplicate_or_degenerate": dup == 0 and degenerate == 0 and tiny == 0,
        "no_obvious_spikes": long_edges == 0,
        "bound": bound,
    }


def audit_garment(verts, faces):
    man = audit_manifold(verts, faces)
    labels = label_garment_loops(verts, man["bound"]["loops"])
    ok = (
        man["components"] == 1
        and man["loop_count"] == 4
        and man["loops_closed"]
        and man["non_boundary_edges_have_2_faces"]
        and man["boundary_verts_degree_2"]
        and man["no_duplicate_or_degenerate"]
        and man["no_obvious_spikes"]
        and labels["ok"]
    )
    out = {k: v for k, v in man.items() if k != "bound"}
    out["labels"] = labels
    out["ok"] = ok
    return out


def audit_guan_crown(verts, faces):
    """Crown fill is about WHERE the boundary sits, not loop_count alone."""
    n = len(verts)
    bound = walk_boundary_loops(faces, n)
    zmax = max(p[2] for p in verts)
    zmin = min(p[2] for p in verts)
    loop_st = [loop_stats(verts, L) for L in bound["loops"]]
    # A crown hole: a boundary loop living at the top of the cap.
    crown_loops = [s for s in loop_st if s["mean_z"] >= zmax - 0.02]
    brim_loops = [s for s in loop_st if s["mean_z"] <= zmin + 0.08]
    # Fill faces: centroid near the top, interior of the highest ring.
    top_band = [i for i, p in enumerate(verts) if p[2] >= zmax - 0.012]
    if top_band:
        cx = sum(verts[i][0] for i in top_band) / len(top_band)
        cy = sum(verts[i][1] for i in top_band) / len(top_band)
        rmax = max(math.hypot(verts[i][0] - cx, verts[i][1] - cy) for i in top_band)
    else:
        cx = cy = 0.0
        rmax = 0.0
    fill_faces = 0
    for f in faces:
        c = face_centroid(verts, f)
        if c[2] >= zmax - 0.015:
            rr = math.hypot(c[0] - cx, c[1] - cy)
            if rr <= rmax * 0.85 + 1e-6:
                fill_faces += 1
    # Boundary must not sit on the crown. Brim/head opening is lower.
    boundary_on_crown = len(crown_loops) > 0
    ok = (not boundary_on_crown) and fill_faces >= 1
    return {
        "ok": ok,
        "zmax": round(zmax, 5),
        "zmin": round(zmin, 5),
        "loop_count": bound["loop_count"],
        "loop_mean_z": [s["mean_z"] for s in loop_st],
        "crown_boundary_loops": len(crown_loops),
        "brim_boundary_loops": len(brim_loops),
        "fill_faces_at_crown": fill_faces,
        "boundary_sits_on_crown": boundary_on_crown,
        "note": "PASS only if no boundary loop at crown z AND at least one face covers the crown interior",
    }


def audit_shoe(verts, faces):
    zmin = min(p[2] for p in verts)
    zmax = max(p[2] for p in verts)
    bound = walk_boundary_loops(faces, len(verts))
    loop_st = [loop_stats(verts, L) for L in bound["loops"]]
    sole_faces = 0
    for f in faces:
        zs = [verts[i][2] for i in f]
        if max(zs) <= zmin + 0.028:
            sole_faces += 1
    # ankle opening should remain (a loop near zmax, not a closed boot)
    ankle_loops = [s for s in loop_st if s["mean_z"] >= zmax - 0.03]
    sole_open = [s for s in loop_st if s["mean_z"] <= zmin + 0.02]
    return {
        "ok": sole_faces >= 1 and len(sole_open) == 0 and len(ankle_loops) >= 1,
        "sole_faces": sole_faces,
        "sole_open_loops": len(sole_open),
        "ankle_loops": len(ankle_loops),
        "loop_count": bound["loop_count"],
        "loop_mean_z": [s["mean_z"] for s in loop_st],
        "zmin": round(zmin, 5),
        "zmax": round(zmax, 5),
    }


def concat_meshes(meshes):
    verts = []
    faces = []
    for m in meshes:
        off = len(verts)
        verts.extend(m["verts"])
        for f in m["faces"]:
            faces.append(tuple(i + off for i in f))
    return verts, faces


def negative_control_v1(source_obj):
    C = load_mod(FROZEN_V1, "clothed_v1_frozen_topo")
    built = C.build_all(source_obj)
    ms = built["meshes"]
    gv, gf = concat_meshes([ms["robe_outer"], ms["sleeve_l"], ms["sleeve_r"]])
    g = audit_garment(gv, gf)
    guan = audit_guan_crown(ms["guan"]["verts"], ms["guan"]["faces"])
    shoe = audit_shoe(ms["shoe_l"]["verts"], ms["shoe_l"]["faces"])
    # Frozen 72 MUST fail separate shells and open crown.
    fail_shells = g["components"] != 1
    fail_crown = guan["boundary_sits_on_crown"] or guan["fill_faces_at_crown"] == 0
    return {
        "generator": "build_clothed_v1.py",
        "frozen_commit": FROZEN_V1_COMMIT,
        "garment": {
            "components": g["components"],
            "loop_count": g["loop_count"],
            "ok": g["ok"],
        },
        "guan": guan,
        "shoe_l": shoe,
        "must_fail_separate_sleeves": fail_shells,
        "must_fail_open_guan_crown": fail_crown,
        "negative_control_ok": fail_shells and fail_crown,
    }


def audit_v2_built(built):
    ms = built["meshes"]
    g = audit_garment(ms["garment"]["verts"], ms["garment"]["faces"])
    guan = audit_guan_crown(ms["guan"]["verts"], ms["guan"]["faces"])
    sh_l = audit_shoe(ms["shoe_l"]["verts"], ms["shoe_l"]["faces"])
    sh_r = audit_shoe(ms["shoe_r"]["verts"], ms["shoe_r"]["faces"])
    body_z = min(p[2] for p in ms["body"]["verts"])
    all_z = []
    for m in ms.values():
        for p in m["verts"]:
            all_z.append(p[2])
    min_z = min(all_z)
    join = built.get("armhole_join", {})
    max_twist = built.get("sleeve_frame", {}).get("max_ring_twist_deg")
    # Armhole verts must be interior (2-face edges), not leftover hole rims.
    from_mesh = ms["garment"].get("armhole_loops") or []
    ah = [i for loop in from_mesh for i in loop]
    bound = walk_boundary_loops(ms["garment"]["faces"], len(ms["garment"]["verts"]))
    bset = {v for L in bound["loops"] for v in L["verts"]}
    nverts = len(ms["garment"]["verts"])
    join_interior = bool(ah) and all(0 <= i < nverts and i not in bset for i in ah)
    join = dict(join)
    join["armhole_verts_not_on_boundary"] = join_interior
    join["armhole_vert_n"] = len(ah)
    ok = (
        g["ok"]
        and guan["ok"]
        and sh_l["ok"]
        and sh_r["ok"]
        and abs(min_z) <= 1e-6
        and join.get("shared_indices") is True
        and join_interior
        and (max_twist is None or max_twist < 25.0)
        and "body" in ms
        and len(ms["body"]["verts"]) > 10000
    )
    return {
        "ok": ok,
        "garment": g,
        "guan": guan,
        "shoe_l": sh_l,
        "shoe_r": sh_r,
        "feet_min_z": round(min_z, 8),
        "body_min_z": round(body_z, 8),
        "body_kept": len(ms["body"]["verts"]),
        "armhole_join": join,
        "sleeve_frame": built.get("sleeve_frame"),
        "export_objects": built.get("export_objects"),
    }


def main():
    src = os.path.join(HERE, "..", "zhuge-anatomy-base", "source", "base.obj")
    if len(sys.argv) > 1:
        src = sys.argv[1]
    src = os.path.abspath(src)
    V2mod = load_mod(V2, "clothed_topology_v2")
    built = V2mod.build_all(src)
    v2 = audit_v2_built(built)
    neg = negative_control_v1(src)
    report = {
        "task_id": "CT-COSTUME-TOPO-01",
        "source_obj": src,
        "v2": v2,
        "negative_control_v1": neg,
        "ok": v2["ok"] and neg["negative_control_ok"],
    }
    out_dir = os.path.join(HERE, "out-topology-v2")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "topology_selfcheck.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("v2_ok", v2["ok"], "garment_components", v2["garment"]["components"], "loops", v2["garment"]["loop_count"])
    print("guan_ok", v2["guan"]["ok"], "crown_boundary", v2["guan"]["crown_boundary_loops"], "fill", v2["guan"]["fill_faces_at_crown"])
    print("neg_shells_fail", neg["must_fail_separate_sleeves"], "neg_crown_fail", neg["must_fail_open_guan_crown"])
    print("wrote", path)
    if not report["ok"]:
        print("SELFCHECK_FAIL")
        return 1
    print("SELFCHECK_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
