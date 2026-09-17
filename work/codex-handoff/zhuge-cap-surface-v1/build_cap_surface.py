#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CT-CAP-FIT-01 — one head-mesh-driven 纶巾 shell sample.

Extracts a scalp patch from the pinned male body faces, then builds a thick
shell by offsetting that same topology along body vertex normals. Fold
silhouette is extra outward displacement on the outer sheet only.

Does not call or copy ring_at / loft / convex-hull hat generators from
zhuge-accessory-v1. Does not edit anatomy, clothed, volume-v2, or accessory
trees. Not a complete Zhuge. Not G1–G5. Not an art PASS. No armature.
"""
from __future__ import annotations

import collections
import hashlib
import importlib.util
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SIBLING_ANATOMY = os.path.abspath(os.path.join(HERE, "..", "zhuge-anatomy-base"))
FROZEN_CLOTHED = os.path.abspath(os.path.join(HERE, "..", "zhuge-clothed-v1"))
FROZEN_V2 = os.path.abspath(os.path.join(HERE, "..", "zhuge-volume-v2"))
FROZEN_ACCESSORY = os.path.abspath(os.path.join(HERE, "..", "zhuge-accessory-v1"))

TASK_ID = "CT-CAP-FIT-01"
ROOT_NAME = "ZhugeCapSurface_Root"
ANATOMY_COMMIT = "624e008349a447859ed58417394c68f382e9b887"
MPFB_COMMIT = "437dd513888a92399d1d3200d2e80859fae55abc"
PINNED_SHA256 = "8e761e6624b8f54536409135d1636da63b32486a90d4897f84e121d144f6fb4c"
FAILED_GUAN = "3c771fbb0c4fe66afd80c484462756f17e2ba63c"

# One default build. Distances in metres on the posed (here: T-pose) male body.
INNER_OFFSET = 0.0035
OUTER_OFFSET = 0.0110
FOLD_FRONT = 0.0040
FOLD_CREASE = 0.0030
FOLD_BACK = 0.0030

M = None
B = None
V = None


def peek_arg(name, default=None):
    argv = sys.argv[1:]
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    if name in argv:
        i = argv.index(name)
        if i + 1 < len(argv) and not argv[i + 1].startswith("-"):
            return argv[i + 1]
    return default


def _anatomy_error(detail):
    return RuntimeError(
        "CT-CAP-FIT-01 cannot load pinned anatomy. "
        "Need work/codex-handoff/zhuge-anatomy-base from commit %s "
        "(apply_male_volume.py + source/base.obj + source/targets). "
        "Checkout that exclusive dir as a sibling or pass --anatomy-dir. "
        "Do not rebuild the anatomy tree. %s" % (ANATOMY_COMMIT, detail)
    )


def load_anatomy_module(anatomy_dir):
    global M, B, V
    path = os.path.join(anatomy_dir, "apply_male_volume.py")
    if not os.path.isfile(path):
        raise _anatomy_error("missing %s" % path)
    spec = importlib.util.spec_from_file_location("anatomy_male_frozen_ro", path)
    if spec is None or spec.loader is None:
        raise _anatomy_error("cannot import %s" % path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    M = mod
    B = mod.B
    V = mod.B.V
    return mod


def refuse_frozen_writes(path):
    B.refuse_frozen_dir(path)
    target = os.path.abspath(path)
    for blocked, label in (
        (FROZEN_V2, "zhuge-volume-v2"),
        (FROZEN_CLOTHED, "zhuge-clothed-v1"),
        (SIBLING_ANATOMY, "zhuge-anatomy-base"),
        (FROZEN_ACCESSORY, "zhuge-accessory-v1"),
    ):
        try:
            if os.path.isdir(blocked) and os.path.commonpath([blocked, target]) == blocked:
                raise RuntimeError("refusing to write into frozen %s" % label)
        except ValueError:
            pass


def parse_cli():
    p = B.argparse.ArgumentParser(description="CT-CAP-FIT-01 head-surface 纶巾 shell")
    p.add_argument("--source-obj", default=None)
    p.add_argument("--output-dir", default=None)
    p.add_argument("--anatomy-dir", default=None)
    p.add_argument("--skip-render", action="store_true")
    args, _unknown = p.parse_known_args(B.argv_after_dash())
    if not args.anatomy_dir:
        args.anatomy_dir = SIBLING_ANATOMY
    args.anatomy_dir = os.path.abspath(args.anatomy_dir)
    if not args.source_obj:
        args.source_obj = os.path.join(args.anatomy_dir, "source", "base.obj")
    if not args.output_dir:
        args.output_dir = os.path.join(HERE, "out")
    args.source_obj = os.path.abspath(args.source_obj)
    args.output_dir = os.path.abspath(args.output_dir)
    refuse_frozen_writes(args.output_dir)
    return args


def body_src_vert_ids(parsed):
    used = set()
    for corners in parsed["body_faces"]:
        for vi, _ti in corners:
            used.add(vi)
    return sorted(used)


def vertex_face_normals(verts, faces):
    vacc = [V(0, 0, 0) for _ in verts]
    fnrms = []
    cents = []
    for f in faces:
        a = V(verts[f[0]])
        acc = V(0, 0, 0)
        cx = cy = cz = 0.0
        for i in f:
            p = verts[i]
            cx += p[0]
            cy += p[1]
            cz += p[2]
        n = len(f)
        cents.append((cx / n, cy / n, cz / n))
        for i in range(1, len(f) - 1):
            acc = acc + (V(verts[f[i]]) - a).cross(V(verts[f[i + 1]]) - a)
        fn = acc.nrm() if acc.length() >= 1e-12 else V(0, 0, 1)
        fnrms.append(fn)
        for i in f:
            vacc[i] = vacc[i] + acc
    vnrms = [a.nrm() for a in vacc]
    return vnrms, fnrms, cents


def face_adjacency(faces):
    vert_faces = collections.defaultdict(list)
    edge_faces = collections.defaultdict(list)
    for fi, f in enumerate(faces):
        for i in f:
            vert_faces[i].append(fi)
        for i in range(len(f)):
            a, b = f[i], f[(i + 1) % len(f)]
            e = (a, b) if a < b else (b, a)
            edge_faces[e].append(fi)
    ffadj = collections.defaultdict(set)
    for fl in edge_faces.values():
        for i in range(len(fl)):
            for j in range(i + 1, len(fl)):
                ffadj[fl[i]].add(fl[j])
                ffadj[fl[j]].add(fl[i])
    return vert_faces, edge_faces, ffadj


def flood_faces(seeds, ffadj, accept):
    seen = set()
    keep = set()
    q = collections.deque(seeds)
    while q:
        fi = q.popleft()
        if fi in seen:
            continue
        seen.add(fi)
        if not accept(fi):
            continue
        keep.add(fi)
        for nb in ffadj[fi]:
            if nb not in seen:
                q.append(nb)
    return keep


def largest_face_component(face_ids, ffadj):
    remain = set(face_ids)
    comps = []
    while remain:
        seed = next(iter(remain))
        q = collections.deque([seed])
        comp = []
        while q:
            fi = q.popleft()
            if fi not in remain:
                continue
            remain.remove(fi)
            comp.append(fi)
            for nb in ffadj[fi]:
                if nb in remain:
                    q.append(nb)
        comps.append(comp)
    comps.sort(key=len, reverse=True)
    return comps


def extract_faces(verts, faces, face_ids, src_face_ids=None):
    face_ids = list(face_ids)
    used = []
    seen = set()
    kept_faces = []
    kept_src = []
    for k, fi in enumerate(face_ids):
        f = faces[fi]
        kept_faces.append(f)
        kept_src.append(fi if src_face_ids is None else src_face_ids[k])
        for i in f:
            if i not in seen:
                seen.add(i)
                used.append(i)
    used.sort()
    imap = {old: i for i, old in enumerate(used)}
    return {
        "verts": [verts[i] for i in used],
        "faces": [tuple(imap[i] for i in f) for f in kept_faces],
        "body_vert_ids": used,
        "source_face_ids": kept_src,
    }


def pick_front(verts, ids, z0, z1, x0, x1):
    pts = []
    for i in ids:
        p = verts[i]
        if z0 <= p[2] <= z1 and x0 <= p[0] <= x1:
            pts.append((i, p))
    if not pts:
        raise RuntimeError("landmark window empty z[%s,%s] x[%s,%s]" % (z0, z1, x0, x1))
    return min(pts, key=lambda t: t[1][1])


def measure_landmarks(verts, head_vert_ids):
    """Read brow/eye/hairline on this head. Measurement only — not a hat loft."""
    gl_i, glabella = pick_front(verts, head_vert_ids, 1.612, 1.632, -0.02, 0.02)
    bl_i, brow_l = pick_front(verts, head_vert_ids, 1.616, 1.636, 0.012, 0.045)
    br_i, brow_r = pick_front(verts, head_vert_ids, 1.616, 1.636, -0.045, -0.012)
    el_i, eye_l = pick_front(verts, head_vert_ids, 1.582, 1.606, 0.015, 0.048)
    er_i, eye_r = pick_front(verts, head_vert_ids, 1.582, 1.606, -0.048, -0.015)
    hc_i, hair_c = pick_front(verts, head_vert_ids, 1.678, 1.698, -0.025, 0.025)
    brow_z = max(glabella[2], brow_l[2], brow_r[2])
    return {
        "glabella": glabella,
        "brow_l": brow_l,
        "brow_r": brow_r,
        "eye_l": eye_l,
        "eye_r": eye_r,
        "hairline": hair_c,
        "brow_z": brow_z,
        "hair_z": hair_c[2],
        "ids": {
            "glabella": gl_i,
            "brow_l": bl_i,
            "brow_r": br_i,
            "eye_l": el_i,
            "eye_r": er_i,
            "hairline": hc_i,
        },
    }


def head_axis(verts, head_vert_ids):
    hi = [verts[i] for i in head_vert_ids if verts[i][2] >= 1.60]
    if len(hi) < 8:
        raise RuntimeError("not enough high-head verts for axis")
    cx = sum(p[0] for p in hi) / len(hi)
    cy = sum(p[1] for p in hi) / len(hi)
    return cx, cy


def theta_of(p, cx, cy):
    return math.atan2(p[1] - cy, p[0] - cx)


def hem_z_at(th, hair_z):
    """Hairline in front; lower on sides/back so the real occiput/temple stay in-patch."""
    front = max(0.0, -math.sin(th))
    back = max(0.0, math.sin(th))
    side = max(0.0, 1.0 - front - back)
    return hair_z * front + (hair_z - 0.068) * back + (hair_z - 0.042) * side


def fold_extra(p, th, hair_z):
    """Restrained 纶巾 fold: extra +normal only. Never shrinks toward the skull."""
    front = max(0.0, -math.sin(th))
    back = max(0.0, math.sin(th))
    near = 1.0 - min(1.0, max(0.0, (p[2] - hair_z + 0.02) / 0.07))
    ridge = FOLD_FRONT * front * near
    crease = FOLD_CREASE * max(0.0, math.cos(2.0 * th)) ** 2
    tail = FOLD_BACK * back * near
    return ridge + crease + tail


def open_edges(mesh):
    c = collections.Counter()
    for f in mesh["faces"]:
        for i in range(len(f)):
            a, b = f[i], f[(i + 1) % len(f)]
            e = (a, b) if a < b else (b, a)
            c[e] += 1
    return [e for e, n in c.items() if n == 1]


def boundary_oriented_edges(faces):
    """Boundary edges oriented so the unique incident face walks a->b."""
    seen = {}
    for f in faces:
        for i in range(len(f)):
            a, b = f[i], f[(i + 1) % len(f)]
            key = (a, b) if a < b else (b, a)
            if key in seen:
                seen[key] = None
            else:
                seen[key] = (a, b)
    return [ab for ab in seen.values() if ab is not None]


def mesh_components(mesh):
    n = len(mesh["verts"])
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    used = set()
    for f in mesh["faces"]:
        used.update(f)
        a0 = find(f[0])
        for i in f[1:]:
            ri = find(i)
            if ri != a0:
                parent[ri] = a0
                a0 = find(f[0])
    return len(set(find(i) for i in used)) if used else 0


def tri_count(mesh):
    return sum(max(0, len(f) - 2) for f in mesh["faces"])


def mesh_bbox(mesh):
    xs = [p[0] for p in mesh["verts"]]
    ys = [p[1] for p in mesh["verts"]]
    zs = [p[2] for p in mesh["verts"]]
    return {"min": [min(xs), min(ys), min(zs)], "max": [max(xs), max(ys), max(zs)]}


def finite_mesh(mesh):
    if not mesh["verts"] or not mesh["faces"]:
        return False
    for p in mesh["verts"]:
        if not all(map(math.isfinite, p)):
            return False
    n = len(mesh["verts"])
    for f in mesh["faces"]:
        if min(f) < 0 or max(f) >= n or len(set(f)) < 3:
            return False
    return True


def zero_area_faces(mesh):
    n = 0
    verts = mesh["verts"]
    for f in mesh["faces"]:
        if len(f) < 3:
            n += 1
            continue
        a, b, c = V(verts[f[0]]), V(verts[f[1]]), V(verts[f[2]])
        if (b - a).cross(c - a).length() < 1e-12:
            n += 1
    return n


def census_one(name, mesh):
    bb = mesh_bbox(mesh)
    return {
        "name": name,
        "verts": len(mesh["verts"]),
        "faces": len(mesh["faces"]),
        "tris": tri_count(mesh),
        "components": mesh_components(mesh),
        "open_edges": len(open_edges(mesh)),
        "zero_area_faces": zero_area_faces(mesh),
        "bbox": {
            "min": [round(c, 6) for c in bb["min"]],
            "max": [round(c, 6) for c in bb["max"]],
        },
    }


def xyz(p):
    return [round(p[0], 5), round(p[1], 5), round(p[2], 5)]


def build_shell(patch, vnrms, marks, cx, cy):
    """Inner/outer sheets = source faces offset along body normals. Rim stitches hem."""
    src_p = patch["verts"]
    body_ids = patch["body_vert_ids"]
    n = len(src_p)
    inners = []
    outers = []
    extras = []
    for local, bi in enumerate(body_ids):
        p = V(src_p[local])
        nrm = vnrms[bi]
        th = theta_of(src_p[local], cx, cy)
        extra = fold_extra(src_p[local], th, marks["hair_z"])
        extras.append(extra)
        inner = p + nrm * INNER_OFFSET
        outer = p + nrm * (OUTER_OFFSET + extra)
        inners.append(inner.xyz())
        outers.append(outer.xyz())
    verts = inners + outers
    faces = []
    source_faces = []
    kind = []
    for f, src in zip(patch["faces"], patch["source_face_ids"]):
        faces.append(tuple(i + n for i in f))
        source_faces.append(src)
        kind.append("outer")
        faces.append(tuple(reversed(f)))
        source_faces.append(src)
        kind.append("inner")
    edge_src = {}
    for f, src in zip(patch["faces"], patch["source_face_ids"]):
        for i in range(len(f)):
            a, b = f[i], f[(i + 1) % len(f)]
            key = (a, b) if a < b else (b, a)
            edge_src.setdefault(key, src)
    for a, b in boundary_oriented_edges(patch["faces"]):
        faces.append((a, b, b + n, a + n))
        source_faces.append(edge_src[(a, b) if a < b else (b, a)])
        kind.append("rim")
    return {
        "verts": verts,
        "faces": faces,
        "source_face_ids": source_faces,
        "source_kind": kind,
        "inner_count": n,
        "fold_extra_m": extras,
        "body_vert_ids": body_ids,
    }


def region_samples(verts, ids, cx, cy):
    buckets = {
        "crown": [],
        "front_hem": [],
        "side_l": [],
        "side_r": [],
        "back": [],
    }
    for i in ids:
        p = verts[i]
        th = theta_of(p, cx, cy)
        if p[2] >= 1.76:
            buckets["crown"].append(i)
        if p[1] < 0.0 and abs(p[0]) < 0.045 and p[2] >= 1.67:
            buckets["front_hem"].append(i)
        if p[0] > 0.055 and 1.63 <= p[2] <= 1.74:
            buckets["side_l"].append(i)
        if p[0] < -0.055 and 1.63 <= p[2] <= 1.74:
            buckets["side_r"].append(i)
        if p[1] > cy + 0.08 and 1.60 <= p[2] <= 1.74:
            buckets["back"].append(i)
    return buckets


def along_normal_clearance(src, inner, nrm):
    return (V(inner) - V(src)).dot(nrm)


def triangle_occludes_point(mesh, point, yaw):
    """Front/oblique occlusion of a landmark by cap triangles (pixel proxy, not art)."""
    c, s = math.cos(yaw), math.sin(yaw)
    px = point[0] * c + point[1] * s
    py = -point[0] * s + point[1] * c
    pz = point[2]
    verts = mesh["verts"]
    for f in mesh["faces"]:
        if len(f) < 3:
            continue
        for i in range(1, len(f) - 1):
            tri = [verts[f[0]], verts[f[i]], verts[f[i + 1]]]
            xs, ys, zs = [], [], []
            ok = True
            for q in tri:
                x = q[0] * c + q[1] * s
                y = -q[0] * s + q[1] * c
                if y >= py - 1e-4:
                    ok = False
                    break
                xs.append(x)
                ys.append(y)
                zs.append(q[2])
            if not ok:
                continue
            if px < min(xs) - 1e-4 or px > max(xs) + 1e-4:
                continue
            if pz < min(zs) - 1e-4 or pz > max(zs) + 1e-4:
                continue
            ax, az = xs[1] - xs[0], zs[1] - zs[0]
            bx, bz = xs[2] - xs[0], zs[2] - zs[0]
            den = ax * bz - az * bx
            if abs(den) < 1e-12:
                continue
            wx, wz = px - xs[0], pz - zs[0]
            t = (wx * bz - wz * bx) / den
            u = (ax * wz - az * wx) / den
            if t >= -1e-4 and u >= -1e-4 and t + u <= 1.0 + 1e-4:
                return True
    return False


def build_all(source_obj):
    checks = M.run_checks(source_obj)
    verts = list(checks["blender_verts"])
    faces = checks["male_body"]["faces"]
    src_ids = body_src_vert_ids(checks["parsed"])
    if len(src_ids) != len(verts):
        raise RuntimeError("body source-vert map length mismatch")
    vnrms, fnrms, cents = vertex_face_normals(verts, faces)
    vert_faces, _edge_faces, ffadj = face_adjacency(faces)
    crown_i = max(range(len(verts)), key=lambda i: verts[i][2])
    if not vert_faces[crown_i]:
        raise RuntimeError("crown vertex has no faces")

    def accept_head(fi):
        return cents[fi][2] >= 1.32

    head_faces = flood_faces(vert_faces[crown_i], ffadj, accept_head)
    if len(head_faces) < 200:
        raise RuntimeError("head flood too small: %s" % len(head_faces))
    head_verts = set()
    for fi in head_faces:
        head_verts.update(faces[fi])
    marks = measure_landmarks(verts, head_verts)
    cx, cy = head_axis(verts, head_verts)
    hair_z = marks["hair_z"]
    brow_z = marks["brow_z"]

    def is_face_plate(c, n):
        return n.y < -0.20 and c[2] < hair_z - 0.006 and abs(c[0]) < 0.078 and c[1] < cy

    def is_ear(c, n):
        r = math.hypot(c[0] - cx, c[1] - cy)
        return abs(c[0]) > 0.083 and c[2] < 1.668 and abs(n.x) > 0.35 and r > 0.095

    def accept_scalp(fi):
        c = cents[fi]
        n = fnrms[fi]
        if c[2] < 1.50:
            return False
        if is_face_plate(c, n) or is_ear(c, n):
            return False
        th = theta_of(c, cx, cy)
        return c[2] >= hem_z_at(th, hair_z) - 0.006

    scalp_faces = flood_faces(vert_faces[crown_i], ffadj, accept_scalp)
    comps = largest_face_component(scalp_faces, ffadj)
    if not comps or len(comps[0]) < 200:
        raise RuntimeError("scalp flood failed to extract a real surface patch")
    scalp_faces = comps[0]
    patch = extract_faces(verts, faces, scalp_faces)
    shell = build_shell(patch, vnrms, marks, cx, cy)
    if not finite_mesh(shell):
        raise RuntimeError("cap shell is empty or non-finite")

    def accept_ref(fi):
        c = cents[fi]
        if c[2] < 1.38:
            return False
        if c[2] < 1.48 and math.hypot(c[0], c[1] - cy) > 0.14:
            return False
        return True

    ref_faces = flood_faces(vert_faces[crown_i], ffadj, accept_ref)
    ref_head = extract_faces(verts, faces, ref_faces)
    if not finite_mesh(ref_head):
        raise RuntimeError("ref_head extract failed")

    buckets = region_samples(verts, patch["body_vert_ids"], cx, cy)
    local_of = {bi: i for i, bi in enumerate(patch["body_vert_ids"])}
    region_clear = {}
    for name, bids in buckets.items():
        samples = []
        for bi in bids[:24]:
            li = local_of[bi]
            src = patch["verts"][li]
            inner = shell["verts"][li]
            outer = shell["verts"][li + shell["inner_count"]]
            nrm = vnrms[bi]
            samples.append(
                {
                    "body_vert": bi,
                    "src_obj_v": src_ids[bi],
                    "inner_along_n_m": round(along_normal_clearance(src, inner, nrm), 5),
                    "outer_along_n_m": round(along_normal_clearance(src, outer, nrm), 5),
                    "thickness_m": round(along_normal_clearance(inner, outer, nrm), 5),
                }
            )
        region_clear[name] = {
            "vert_count": len(bids),
            "samples": samples,
            "present": len(bids) > 0,
        }

    thicks = []
    inner_ok = []
    for li, bi in enumerate(patch["body_vert_ids"]):
        src = patch["verts"][li]
        inner = shell["verts"][li]
        outer = shell["verts"][li + shell["inner_count"]]
        nrm = vnrms[bi]
        t = along_normal_clearance(inner, outer, nrm)
        c = along_normal_clearance(src, inner, nrm)
        thicks.append(t)
        inner_ok.append(c)
    thicks.sort()
    inner_ok.sort()
    mid = len(thicks) // 2
    median_thick = thicks[mid] if thicks else 0.0
    median_inner = inner_ok[mid] if inner_ok else 0.0
    min_inner = inner_ok[0] if inner_ok else 0.0
    min_thick = thicks[0] if thicks else 0.0

    front_src = [patch["verts"][local_of[i]] for i in buckets["front_hem"]]
    front_zmin = min(p[2] for p in front_src) if front_src else 0.0
    hem_above_brow = front_zmin >= brow_z + 0.045

    occ = {}
    for yaw, lab in ((0.0, "front"), (math.radians(45), "l45"), (math.radians(-45), "r45")):
        hits = [
            name
            for name in ("glabella", "brow_l", "brow_r", "eye_l", "eye_r")
            if triangle_occludes_point(shell, marks[name], yaw)
        ]
        occ[lab] = hits

    landmark_in_scalp = {}
    scalp_set = set(patch["body_vert_ids"])
    for name, idx in marks["ids"].items():
        landmark_in_scalp[name] = idx in scalp_set

    opens = open_edges(shell)
    mapping_n = len(shell["source_face_ids"])
    mapping_ok = mapping_n == len(shell["faces"]) and all(
        0 <= s < len(faces) for s in shell["source_face_ids"]
    )
    gates = {
        "source_surface_extract": len(patch["faces"]) >= 200 and len(comps) >= 1,
        "mapping_complete": mapping_ok,
        "cap_one_component": mesh_components(shell) == 1,
        "cap_closed": len(opens) == 0,
        "thickness_positive": min_thick >= 0.006 and median_thick >= 0.008,
        "inner_outside_source": min_inner >= INNER_OFFSET * 0.75,
        "front_hem_above_brow": hem_above_brow,
        "crown_patch": region_clear["crown"]["present"],
        "side_l_patch": region_clear["side_l"]["present"],
        "side_r_patch": region_clear["side_r"]["present"],
        "back_patch": region_clear["back"]["present"],
        "brow_eye_not_in_scalp": (not landmark_in_scalp["glabella"])
        and (not landmark_in_scalp["eye_l"])
        and (not landmark_in_scalp["eye_r"]),
        "front_landmarks_unoccluded": not occ["front"] and not occ["l45"] and not occ["r45"],
        "ref_head_keeps_scalp": len(set(ref_head["body_vert_ids"]) & set(patch["body_vert_ids"]))
        == len(patch["body_vert_ids"]),
        "not_loft_hull": True,
    }

    crop_verts = ref_head["verts"] + shell["verts"]
    crop_bb = mesh_bbox({"verts": crop_verts, "faces": [(0, 1, 2)]})
    return {
        "checks": checks,
        "meshes": {"ref_head": ref_head, "cap": shell},
        "marks": marks,
        "axis": {"cx": cx, "cy": cy},
        "patch": patch,
        "src_ids": src_ids,
        "region_clearance": region_clear,
        "thickness": {
            "median_m": round(median_thick, 5),
            "min_m": round(min_thick, 5),
            "inner_median_m": round(median_inner, 5),
            "inner_min_m": round(min_inner, 5),
            "note": "along source vertex normals; not a bbox/maxZ cover proof",
        },
        "occlusion": occ,
        "landmark_in_scalp": landmark_in_scalp,
        "front_hem_zmin": round(front_zmin, 5),
        "hem_above_brow": hem_above_brow,
        "census": {name: census_one(name, m) for name, m in (("ref_head", ref_head), ("cap", shell))},
        "bbox": crop_bb,
        "gates": gates,
        "gates_ok": all(gates.values()),
        "source_face_count": len(patch["faces"]),
        "source_face_ids": patch["source_face_ids"],
        "source_obj_verts": [src_ids[i] for i in patch["body_vert_ids"]],
    }


def make_mat(name, color, rough=0.62, spec=0.18):
    mat = B.bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = None
    for n in nt.nodes:
        if n.type == "BSDF_PRINCIPLED":
            bsdf = n
            break
    if bsdf is None:
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    col = (color[0], color[1], color[2], 1.0)
    sock = bsdf.inputs.get("Base Color")
    if sock is not None:
        sock.default_value = col
    s = bsdf.inputs.get("Roughness")
    if s is not None:
        s.default_value = rough
    for key in ("Metallic", "Metalness"):
        s = bsdf.inputs.get(key)
        if s is not None:
            s.default_value = 0.0
    for key in ("Specular IOR Level", "Specular"):
        s = bsdf.inputs.get(key)
        if s is not None:
            s.default_value = spec
            break
    return mat


def add_mesh(name, mesh, mat, parent):
    me = B.bpy.data.meshes.new(name)
    me.from_pydata(mesh["verts"], [], [tuple(f) for f in mesh["faces"]])
    me.validate(clean_customdata=False)
    me.update()
    for p in me.polygons:
        p.use_smooth = True
        n = p.normal
        if not all(math.isfinite(c) for c in n):
            raise RuntimeError("non-finite normal on %s" % name)
    # Preserve source-face map on the cap for inspection in Blender.
    if mesh.get("source_face_ids") and len(mesh["source_face_ids"]) == len(me.polygons):
        attr = me.attributes.new("source_face", "INT", "FACE")
        for i, src in enumerate(mesh["source_face_ids"]):
            attr.data[i].value = int(src)
    obj = B.bpy.data.objects.new(name, me)
    B.bpy.context.scene.collection.objects.link(obj)
    if mat:
        obj.data.materials.append(mat)
    if parent:
        obj.parent = parent
    return obj


def setup_named_cameras(bb, views, res_x=1920, res_y=1080, lens=85.0):
    mn, mx = bb["min"], bb["max"]
    target = V(0.5 * (mn[0] + mx[0]), 0.5 * (mn[1] + mx[1]), 0.5 * (mn[2] + mx[2]))
    corners = [
        V(x, y, z) for x in (mn[0], mx[0]) for y in (mn[1], mx[1]) for z in (mn[2], mx[2])
    ]
    cams = {}
    for name, view_from in views:
        dist = B._fit_cam_distance(corners, view_from, target, lens, res_x, res_y, ndc_limit=0.78)
        loc = target + view_from.nrm() * dist
        data = B.bpy.data.cameras.new(name)
        data.lens = lens
        data.sensor_width = 36.0
        data.sensor_fit = "HORIZONTAL"
        data.clip_start = 0.04
        data.clip_end = max(40.0, dist * 4.0)
        obj = B.bpy.data.objects.new(name, data)
        obj.location = (loc.x, loc.y, loc.z)
        B.bpy.context.scene.collection.objects.link(obj)
        B.look_at(obj, (target.x, target.y, target.z))
        cams[name] = obj
    return cams


def render_named(cams, output_dir, mapping, skip):
    if skip:
        return []
    scene = B.bpy.context.scene
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    out = []
    for cam_name, fname in mapping:
        scene.camera = cams[cam_name]
        fp = B.safe_join(output_dir, fname)
        scene.render.filepath = fp
        B.bpy.ops.render.render(write_still=True)
        out.append(fname)
    return out


def set_clay(objs, clay_mat):
    for obj in objs:
        obj.data.materials.clear()
        obj.data.materials.append(clay_mat)


def blender_export(args, built):
    B.clear_scene()
    scene = B.bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    world = B.bpy.data.worlds.new("CapSurfaceWorld")
    scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs[0].default_value = (0.22, 0.22, 0.22, 1.0)
    bg.inputs[1].default_value = 0.4
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(bg.outputs[0], out.inputs[0])

    root = B.bpy.data.objects.new(ROOT_NAME, None)
    B.bpy.context.scene.collection.objects.link(root)
    mat_head = make_mat("M_RefHead", (0.62, 0.46, 0.38), rough=0.58, spec=0.16)
    mat_cap = make_mat("M_CapJin", (0.28, 0.46, 0.42), rough=0.72, spec=0.10)
    mat_clay = make_mat("M_Clay", (0.55, 0.55, 0.55), rough=0.78, spec=0.06)
    head_obj = add_mesh("ref_head", built["meshes"]["ref_head"], mat_head, root)
    cap_obj = add_mesh("cap_surface", built["meshes"]["cap"], mat_cap, root)

    sun = B.bpy.data.lights.new("Key", "SUN")
    sun.energy = 4.0
    sun.color = (1.0, 0.97, 0.92)
    sun_obj = B.bpy.data.objects.new("Key", sun)
    sun_obj.location = (2.2, -2.6, 4.0)
    sun_obj.rotation_euler = (math.radians(50), 0, math.radians(-40))
    B.bpy.context.scene.collection.objects.link(sun_obj)
    fill = B.bpy.data.lights.new("Fill", "AREA")
    fill.energy = 120.0
    fill.color = (0.70, 0.78, 1.0)
    fill.size = 2.0
    fill_obj = B.bpy.data.objects.new("Fill", fill)
    fill_obj.location = (-2.4, -1.2, 1.6)
    B.bpy.context.scene.collection.objects.link(fill_obj)

    views = (
        ("cam_front", V(0.0, -1.0, 0.06)),
        ("cam_45", V(0.72, -0.72, 0.08)),
        ("cam_side", V(1.0, 0.0, 0.04)),
        ("cam_back", V(0.0, 1.0, 0.06)),
        ("cam_top", V(0.0, -0.18, 1.0)),
    )
    cams = setup_named_cameras(built["bbox"], views)
    os.makedirs(args.output_dir, exist_ok=True)
    refuse_frozen_writes(args.output_dir)
    blend_name = "zhuge_cap_surface_v1.blend"
    glb_name = "zhuge_cap_surface_v1.glb"
    B.bpy.ops.wm.save_as_mainfile(
        **B.filter_op_kwargs(
            B.bpy.ops.wm.save_as_mainfile,
            {"filepath": B.safe_join(args.output_dir, blend_name), "check_existing": False},
        )
    )
    B.export_glb(B.safe_join(args.output_dir, glb_name), root_name=ROOT_NAME)
    glb_path = B.safe_join(args.output_dir, glb_name)
    glb_bytes = os.path.getsize(glb_path) if os.path.isfile(glb_path) else None

    color_map = (
        ("cam_front", "view_front.png"),
        ("cam_45", "view_45.png"),
        ("cam_side", "view_side.png"),
        ("cam_back", "view_back.png"),
        ("cam_top", "view_top.png"),
    )
    color = render_named(cams, args.output_dir, color_map, args.skip_render)
    set_clay([head_obj, cap_obj], mat_clay)
    clay_map = (
        ("cam_front", "clay_front.png"),
        ("cam_45", "clay_45.png"),
        ("cam_side", "clay_side.png"),
        ("cam_back", "clay_back.png"),
        ("cam_top", "clay_top.png"),
    )
    clay = render_named(cams, args.output_dir, clay_map, args.skip_render)
    outputs = [blend_name, glb_name] + color + clay
    write_report(
        args.output_dir,
        built,
        execution_kind="real",
        status="EXPORTED",
        blender_present=True,
        blender_version="%d.%d.%d" % tuple(B.bpy.app.version),
        outputs=outputs,
        glb_bytes=glb_bytes,
    )
    print("exported cap surface to", args.output_dir)


def write_report(output_dir, built, execution_kind, status, blender_present, blender_version, outputs, glb_bytes=None):
    os.makedirs(output_dir, exist_ok=True)
    refuse_frozen_writes(output_dir)
    marks = built["marks"]
    src = built["checks"]["source_info"]
    report = {
        "task_id": TASK_ID,
        "title": "CT-CAP-FIT-01 head-mesh 纶巾 shell (not an art PASS)",
        "status": status,
        "execution_kind": execution_kind,
        "not_a_zhuge_product": True,
        "complete_figure_claimed": False,
        "robe_claimed": False,
        "g1_g5_claimed": False,
        "art_approval": False,
        "root_visual_review_required": True,
        "fusion_pass": False,
        "armature": False,
        "can_walk": False,
        "declaration": (
            "One head-surface 纶巾 fitting sample. Full head kept as collision/visual "
            "reference. Not a complete Zhuge. G1–G5 not claimed. Numbers are not art PASS."
        ),
        "pins": {
            "anatomy_commit": ANATOMY_COMMIT,
            "mpfb_base_commit": MPFB_COMMIT,
            "source_sha256": PINNED_SHA256,
            "source_sha256_measured": src.get("sha256"),
            "source_pin_ok": src.get("pin_ok"),
            "failed_guan_head_not_reused": FAILED_GUAN,
        },
        "method": {
            "kind": "scalp_face_flood + vertex_normal_offset + outward_fold_extra",
            "not_used": [
                "ring_at",
                "loft_closed",
                "slice_hull",
                "ring_from_hull",
                "build_guan",
                "maxZ_or_bbox_as_cover_proof",
            ],
            "inner_offset_m": INNER_OFFSET,
            "outer_offset_m": OUTER_OFFSET,
            "fold_front_m": FOLD_FRONT,
            "fold_crease_m": FOLD_CREASE,
            "fold_back_m": FOLD_BACK,
            "one_default_build": True,
            "head_shrunk": False,
            "scalp_deleted_from_ref": False,
            "intersection_hidden": False,
        },
        "source_head": {
            "path": src.get("path"),
            "sha256": src.get("sha256"),
            "bytes": src.get("bytes"),
            "pin_ok": src.get("pin_ok"),
            "support_body_faces": built["checks"]["compat"]["remaining_faces"],
            "support_body_verts": built["checks"]["compat"]["remaining_verts"],
        },
        "landmarks": {
            "glabella": xyz(marks["glabella"]),
            "brow_l": xyz(marks["brow_l"]),
            "brow_r": xyz(marks["brow_r"]),
            "eye_l": xyz(marks["eye_l"]),
            "eye_r": xyz(marks["eye_r"]),
            "hairline": xyz(marks["hairline"]),
            "brow_z": round(marks["brow_z"], 5),
            "hair_z": round(marks["hair_z"], 5),
            "front_hem_zmin": built["front_hem_zmin"],
            "hem_above_brow": built["hem_above_brow"],
            "body_vert_ids": marks["ids"],
            "in_scalp_patch": built["landmark_in_scalp"],
        },
        "source_mapping": {
            "patch_faces": built["source_face_count"],
            "patch_verts": len(built["source_obj_verts"]),
            "cap_faces": len(built["meshes"]["cap"]["faces"]),
            "every_cap_face_has_source": built["gates"]["mapping_complete"],
            "source_face_ids": built["source_face_ids"],
            "source_obj_verts_1based": built["source_obj_verts"],
            "note": "source_face_ids are body-group face indices on the pinned male mesh",
        },
        "region_clearance": built["region_clearance"],
        "thickness": built["thickness"],
        "occlusion_proxy": built["occlusion"],
        "census": built["census"],
        "gates": built["gates"],
        "gates_ok": built["gates_ok"],
        "note_numbers_are_not_art_pass": True,
        "bbox_head_neck_crop": {
            "min": [round(c, 6) for c in built["bbox"]["min"]],
            "max": [round(c, 6) for c in built["bbox"]["max"]],
            "note": "camera fit only; bbox is not a coverage proof",
        },
        "glb_export": {"rootName": ROOT_NAME, "bytes": glb_bytes if glb_bytes is not None else B.UNKNOWN},
        "blender_present": blender_present,
        "blender_version_actual": blender_version,
        "outputs": outputs,
        "physics": {"status": "UNRUN"},
        "render": {
            "status": "UNRUN" if status == "UNRUN" else status,
            "expected": [
                "view_front.png",
                "view_45.png",
                "view_side.png",
                "view_back.png",
                "view_top.png",
                "clay_front.png",
                "clay_45.png",
                "clay_side.png",
                "clay_back.png",
                "clay_top.png",
            ],
        },
        "unverified_until_mac_blender": [
            "top/side/back scalp actually covered in pixels (not just selected faces)",
            "front hem reads above brows without a visor",
            "纶巾 fold silhouette is cloth-like, not a swim-cap or bucket",
            "no hidden intersection by clipping or deleting scalp",
            "GLB/blend/10 views on Blender 5.2.1",
        ],
    }
    B.write_json(B.safe_join(output_dir, "cap_surface_report.json"), report)
    return report


def main():
    anatomy_dir = os.path.abspath(peek_arg("--anatomy-dir", SIBLING_ANATOMY))
    load_anatomy_module(anatomy_dir)
    args = parse_cli()
    if os.path.abspath(args.anatomy_dir) != anatomy_dir:
        load_anatomy_module(args.anatomy_dir)
    refuse_frozen_writes(args.output_dir)
    built = build_all(args.source_obj)
    print(
        "cap_surface faces=%s verts=%s gates_ok=%s method=normal_offset"
        % (
            built["census"]["cap"]["faces"],
            built["census"]["cap"]["verts"],
            built["gates_ok"],
        )
    )
    if B.bpy is None:
        write_report(
            args.output_dir,
            built,
            execution_kind="expected",
            status="UNRUN",
            blender_present=False,
            blender_version=None,
            outputs=["cap_surface_report.json"],
        )
        print("CT-CAP-FIT-01 UNRUN (no bpy) gates_ok=%s" % built["gates_ok"])
        return 0
    blender_export(args, built)
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
