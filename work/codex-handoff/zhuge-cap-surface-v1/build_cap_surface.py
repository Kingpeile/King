#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CT-CAP-FIT-01-FIX — one directed rework after Mac ART_FAIL on 3620dc7.

Keeps the proven inner scalp-surface fit. Reworks only the exclusive
zhuge-cap-surface-v1 tree:

1. Cut a smooth hem on the real head triangles (new verts keep source-face
   + barycentric). Ears are excluded. No whole-face centroid leftover teeth.
2. Outer sheet is a cloth grid sampled on that inner surface, then folded.
   Not a thicker copy of the same scalp, not PR19 hull loft.
3. Front Y clamp removes the visor that buried the brows. Shadows stay on.
4. ref_head is a planar neck cut; head and both ears stay. Anatomy above
   the plane is not smoothed or morphed.

First pack 3620dc7 report is kept beside the new one. Not a complete Zhuge.
Not G1–G5. Not an art PASS. No armature.
"""
from __future__ import annotations

import collections
import importlib.util
import math
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SIBLING_ANATOMY = os.path.abspath(os.path.join(HERE, "..", "zhuge-anatomy-base"))
FROZEN_CLOTHED = os.path.abspath(os.path.join(HERE, "..", "zhuge-clothed-v1"))
FROZEN_V2 = os.path.abspath(os.path.join(HERE, "..", "zhuge-volume-v2"))
FROZEN_ACCESSORY = os.path.abspath(os.path.join(HERE, "..", "zhuge-accessory-v1"))

TASK_ID = "CT-CAP-FIT-01-FIX"
ROOT_NAME = "ZhugeCapSurface_Root"
ANATOMY_COMMIT = "624e008349a447859ed58417394c68f382e9b887"
MPFB_COMMIT = "437dd513888a92399d1d3200d2e80859fae55abc"
PINNED_SHA256 = "8e761e6624b8f54536409135d1636da63b32486a90d4897f84e121d144f6fb4c"
FAILED_GUAN = "3c771fbb0c4fe66afd80c484462756f17e2ba63c"
FIRST_PACK = "3620dc70f6894c18cb99f6955766b9a1878d582d"
FIRST_REPORT = "cap_surface_report_3620dc7.json"

INNER_OFFSET = 0.0035
CLOTH_THICK = 0.0080
FRONT_BAND = 0.0140
RIDGE = 0.0120
SIDE_PAD = 0.0080
TOP_PAD = 0.0060
NECK_PLANE_Z = 1.448
N_THETA = 28
N_H = 8
CLIP_EPS = 1e-9

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
        "CT-CAP-FIT-01-FIX cannot load pinned anatomy. "
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
    p = B.argparse.ArgumentParser(description="CT-CAP-FIT-01-FIX head-surface 纶巾 shell")
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


def triangulate(faces, src_ids=None):
    tris = []
    src = []
    for fi, f in enumerate(faces):
        sid = fi if src_ids is None else src_ids[fi]
        for k in range(1, len(f) - 1):
            tris.append((f[0], f[k], f[k + 1]))
            src.append(sid)
    return tris, src


def triangle_bary(p, a, b, c):
    v0, v1, v2 = V(b) - V(a), V(c) - V(a), V(p) - V(a)
    d00, d01, d11 = v0.dot(v0), v0.dot(v1), v1.dot(v1)
    d20, d21 = v2.dot(v0), v2.dot(v1)
    den = d00 * d11 - d01 * d01
    if abs(den) < 1e-16:
        return (1.0, 0.0, 0.0)
    v = (d11 * d20 - d01 * d21) / den
    w = (d00 * d21 - d01 * d20) / den
    u = 1.0 - v - w
    return (u, v, w)


def clip_by_scalar(verts, tris, src_ids, scalars):
    """Keep scalar>=0. Split crossing edges. New verts record src_face + edge t."""
    new_verts = [tuple(p) for p in verts]
    svals = [float(x) for x in scalars]
    meta = [{"kind": "src", "body_i": i} for i in range(len(verts))]
    cache = {}

    def split(a, b, src):
        key = (a, b) if a < b else (b, a)
        if key in cache:
            return cache[key]
        sa, sb = svals[a], svals[b]
        t = sa / (sa - sb) if abs(sa - sb) > 1e-16 else 0.5
        t = min(1.0, max(0.0, t))
        pa, pb = new_verts[a], new_verts[b]
        p = (
            pa[0] + t * (pb[0] - pa[0]),
            pa[1] + t * (pb[1] - pa[1]),
            pa[2] + t * (pb[2] - pa[2]),
        )
        idx = len(new_verts)
        new_verts.append(p)
        svals.append(0.0)
        meta.append({"kind": "cut", "edge": [a, b], "t": t, "src_face": src})
        cache[key] = idx
        return idx

    out_f = []
    out_s = []
    for tri, src in zip(tris, src_ids):
        s = [svals[i] for i in tri]
        pos = [k for k in range(3) if s[k] >= -CLIP_EPS]
        if len(pos) == 3:
            out_f.append(tri)
            out_s.append(src)
            continue
        if len(pos) == 0:
            continue
        if len(pos) == 1:
            i = pos[0]
            j, k = (i + 1) % 3, (i + 2) % 3
            nj = split(tri[i], tri[j], src)
            nk = split(tri[i], tri[k], src)
            out_f.append((tri[i], nj, nk))
            out_s.append(src)
            continue
        i, j = pos[0], pos[1]
        k = 3 - i - j
        ni = split(tri[i], tri[k], src)
        nj = split(tri[j], tri[k], src)
        if (j - i) % 3 == 1:
            out_f.append((tri[i], tri[j], nj))
            out_s.append(src)
            out_f.append((tri[i], nj, ni))
            out_s.append(src)
        else:
            out_f.append((tri[j], tri[i], ni))
            out_s.append(src)
            out_f.append((tri[j], ni, nj))
            out_s.append(src)

    used = sorted({i for f in out_f for i in f})
    imap = {old: n for n, old in enumerate(used)}
    return {
        "verts": [new_verts[i] for i in used],
        "faces": [tuple(imap[i] for i in f) for f in out_f],
        "source_face_ids": out_s,
        "vert_meta": [meta[i] for i in used],
        "body_vert_ids": [used[n] if meta[used[n]]["kind"] == "src" else None for n in range(len(used))],
    }


def compact_component(mesh, keep_faces):
    keep_faces = list(keep_faces)
    used = []
    seen = set()
    faces = []
    src = []
    for fi in keep_faces:
        f = mesh["faces"][fi]
        faces.append(f)
        src.append(mesh["source_face_ids"][fi])
        for i in f:
            if i not in seen:
                seen.add(i)
                used.append(i)
    used.sort()
    imap = {old: n for n, old in enumerate(used)}
    return {
        "verts": [mesh["verts"][i] for i in used],
        "faces": [tuple(imap[i] for i in f) for f in faces],
        "source_face_ids": src,
        "vert_meta": [mesh["vert_meta"][i] for i in used],
        "body_vert_ids": [mesh["body_vert_ids"][i] for i in used],
    }


def mesh_face_adj(faces):
    edge_faces = collections.defaultdict(list)
    for fi, f in enumerate(faces):
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
    return ffadj


def largest_component_from(mesh, seed_vert):
    ffadj = mesh_face_adj(mesh["faces"])
    vert_faces = collections.defaultdict(list)
    for fi, f in enumerate(mesh["faces"]):
        for i in f:
            vert_faces[i].append(fi)
    if seed_vert not in vert_faces and mesh["faces"]:
        seed_faces = [0]
    else:
        seed_faces = vert_faces.get(seed_vert, [0] if mesh["faces"] else [])
    keep = flood_faces(seed_faces, ffadj, lambda fi: True)
    return compact_component(mesh, keep)


def fill_barycentric(mesh, body_verts, body_faces):
    """Fill cut-vert barycentric against the recorded source triangle."""
    out = []
    for i, meta in enumerate(mesh["vert_meta"]):
        if meta["kind"] == "src":
            out.append({"kind": "src", "body_i": meta["body_i"]})
            continue
        src = meta["src_face"]
        f = body_faces[src]
        if len(f) < 3:
            u, v, w = 1.0, 0.0, 0.0
        else:
            best = None
            for k in range(1, len(f) - 1):
                trip = triangle_bary(
                    mesh["verts"][i],
                    body_verts[f[0]],
                    body_verts[f[k]],
                    body_verts[f[k + 1]],
                )
                score = min(trip)
                if best is None or score > best[0]:
                    best = (score, trip)
            u, v, w = best[1]
        out.append(
            {
                "kind": "cut",
                "src_face": src,
                "barycentric": [round(u, 5), round(v, 5), round(w, 5)],
                "t": round(meta["t"], 5),
                "edge": meta["edge"],
            }
        )
    mesh["vert_source"] = out
    return mesh


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
    gl_i, glabella = pick_front(verts, head_vert_ids, 1.612, 1.632, -0.02, 0.02)
    bl_i, brow_l = pick_front(verts, head_vert_ids, 1.616, 1.636, 0.012, 0.045)
    br_i, brow_r = pick_front(verts, head_vert_ids, 1.616, 1.636, -0.045, -0.012)
    el_i, eye_l = pick_front(verts, head_vert_ids, 1.582, 1.606, 0.015, 0.048)
    er_i, eye_r = pick_front(verts, head_vert_ids, 1.582, 1.606, -0.048, -0.015)
    hc_i, hair_c = pick_front(verts, head_vert_ids, 1.678, 1.698, -0.025, 0.025)
    return {
        "glabella": glabella,
        "brow_l": brow_l,
        "brow_r": brow_r,
        "eye_l": eye_l,
        "eye_r": eye_r,
        "hairline": hair_c,
        "brow_z": max(glabella[2], brow_l[2], brow_r[2]),
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
    return sum(p[0] for p in hi) / len(hi), sum(p[1] for p in hi) / len(hi)


def theta_of(p, cx, cy):
    return math.atan2(p[1] - cy, p[0] - cx)


def wrap_pi(a):
    return math.atan2(math.sin(a), math.cos(a))


def hem_z_at(th, hair_z):
    """Smooth hairline: front above brows, sides above ears, back covers occiput."""
    front = max(0.0, -math.sin(th))
    back = max(0.0, math.sin(th))
    side = max(0.0, 1.0 - front - back)
    return (hair_z + 0.010) * front + (hair_z - 0.042) * back + (hair_z + 0.016) * side


def scalp_scalar(p, n, cx, cy, hair_z):
    th = theta_of(p, cx, cy)
    s_hem = p[2] - hem_z_at(th, hair_z)
    if 1.500 <= p[2] <= 1.668:
        s_ear = 0.080 - abs(p[0])
    else:
        s_ear = 1.0
    if n.y < -0.18 and p[2] < hair_z - 0.004 and p[1] < cy and abs(p[0]) < 0.080:
        s_face = -0.01
    else:
        s_face = 1.0
    return min(s_hem, s_ear, s_face)


def open_edges(mesh):
    c = collections.Counter()
    for f in mesh["faces"]:
        for i in range(len(f)):
            a, b = f[i], f[(i + 1) % len(f)]
            e = (a, b) if a < b else (b, a)
            c[e] += 1
    return [e for e, n in c.items() if n == 1]


def boundary_loop(mesh):
    """One oriented boundary loop, or empty."""
    directed = []
    seen = {}
    for f in mesh["faces"]:
        for i in range(len(f)):
            a, b = f[i], f[(i + 1) % len(f)]
            key = (a, b) if a < b else (b, a)
            if key in seen:
                seen[key] = None
            else:
                seen[key] = (a, b)
    half = [ab for ab in seen.values() if ab is not None]
    if not half:
        return []
    nxt = {a: b for a, b in half}
    start = half[0][0]
    loop = [start]
    cur = start
    for _ in range(len(half) + 2):
        cur = nxt.get(cur)
        if cur is None or cur == start:
            break
        loop.append(cur)
    return loop


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


def interp_normal(mesh, vnrms_body):
    nrms = []
    for i, meta in enumerate(mesh["vert_meta"]):
        if meta["kind"] == "src":
            nrms.append(vnrms_body[meta["body_i"]])
            continue
        a, b = meta["edge"]
        t = meta["t"]
        # edge indices are in the pre-compact clip space; fall back to face area normal
        nrms.append(V(0, 0, 1))
    # recompute from clipped faces so cut verts get real normals
    acc = [V(0, 0, 0) for _ in mesh["verts"]]
    for f in mesh["faces"]:
        a = V(mesh["verts"][f[0]])
        sm = V(0, 0, 0)
        for k in range(1, len(f) - 1):
            sm = sm + (V(mesh["verts"][f[k]]) - a).cross(V(mesh["verts"][f[k + 1]]) - a)
        for i in f:
            acc[i] = acc[i] + sm
    return [a.nrm() for a in acc]


def safe_normal(n, p, cx, cy):
    th = theta_of(p, cx, cy)
    front = max(0.0, -math.sin(th))
    ny = n.y
    if front > 0.25 and ny < 0:
        ny = ny * (1.0 - 0.85 * front)
    nn = V(n.x, ny, n.z)
    return nn.nrm() if nn.length() >= 1e-8 else V(0, 0, 1)


def clamp_front_y(p, n, src, cx, cy, y_limit, min_along=None):
    """Pull visor back without sliding through the source surface."""
    th = theta_of(p, cx, cy)
    front = max(0.0, -math.sin(th))
    q = p
    if front > 0.30 and q[1] < y_limit:
        q = (q[0], y_limit, q[2])
    if min_along is not None:
        along = (V(q) - V(src)).dot(n)
        if along < min_along:
            q = (V(q) + n * (min_along - along)).xyz()
            if front > 0.30 and q[1] < y_limit:
                q = (q[0], y_limit, q[2])
                along = (V(q) - V(src)).dot(n)
                if along < min_along:
                    q = (V(src) + n * min_along).xyz()
                    q = (q[0], max(q[1], y_limit), q[2])
    return q


def fold_amount(th, h):
    """Readable 纶巾 relief on the cloth grid. All extra is outward."""
    front = max(0.0, -math.sin(th))
    band = FRONT_BAND * max(0.0, 1.0 - h / 0.22) ** 2 * max(0.0, (front - 0.20) / 0.80)
    crease = 0.0
    for c in (0.0, math.pi * 0.5, math.pi, -math.pi * 0.5):
        d = abs(wrap_pi(th - c))
        crease = max(crease, max(0.0, 1.0 - d / 0.30) ** 2)
    ridge = RIDGE * crease * (0.35 + 0.65 * h)
    side = SIDE_PAD * max(0.0, abs(math.cos(th)) - 0.35) * max(0.0, 1.0 - abs(h - 0.45) / 0.40)
    top = TOP_PAD * max(0.0, (h - 0.65) / 0.35)
    return band, ridge, side, top


def sample_cloth_grid(surf, nrms, cx, cy, hem_fn, crown_z, y_limit):
    params = []
    for p in surf["verts"]:
        th = theta_of(p, cx, cy)
        hz = hem_fn(th)
        h = (p[2] - hz) / max(1e-6, crown_z - hz)
        params.append((th, h))
    crown_i = max(range(len(surf["verts"])), key=lambda i: surf["verts"][i][2])
    samples = []
    for j in range(N_H - 1):
        h0 = j / (N_H - 1)
        for i in range(N_THETA):
            th0 = -math.pi + 2.0 * math.pi * i / N_THETA
            wsum = 0.0
            pacc = V(0, 0, 0)
            nacc = V(0, 0, 0)
            best_k, best_d = 0, 1e9
            for k, (th, h) in enumerate(params):
                dth = abs(wrap_pi(th - th0))
                dh = abs(h - h0)
                d = (dth / 0.55) ** 2 + (dh / 0.22) ** 2
                if d < best_d:
                    best_d, best_k = d, k
                if d < 5.0:
                    w = 1.0 / max(1e-6, d)
                    wsum += w
                    pacc = pacc + V(surf["verts"][k]) * w
                    nacc = nacc + nrms[k] * w
            if wsum < 1e-8:
                p = surf["verts"][best_k]
                n = nrms[best_k]
                src = surf["source_face_ids"][0]
                hit_k = best_k
            else:
                p = (pacc * (1.0 / wsum)).xyz()
                n = nacc.nrm()
                hit_k = best_k
            src = None
            for fi, f in enumerate(surf["faces"]):
                if hit_k in f:
                    src = surf["source_face_ids"][fi]
                    break
            if src is None:
                src = surf["source_face_ids"][0]
            samples.append({"p": p, "n": n, "src": src, "th": th0, "h": h0})
    samples.append(
        {
            "p": surf["verts"][crown_i],
            "n": nrms[crown_i],
            "src": surf["source_face_ids"][0],
            "th": 0.0,
            "h": 1.0,
        }
    )
    return samples


def cloth_faces(samples):
    faces = []
    src = []
    for j in range(N_H - 2):
        for i in range(N_THETA):
            a = j * N_THETA + i
            b = j * N_THETA + (i + 1) % N_THETA
            c = (j + 1) * N_THETA + (i + 1) % N_THETA
            d = (j + 1) * N_THETA + i
            faces.append((a, b, c, d))
            src.append(samples[a]["src"])
    pole = (N_H - 1) * N_THETA
    last = (N_H - 2) * N_THETA
    for i in range(N_THETA):
        a = last + i
        b = last + (i + 1) % N_THETA
        faces.append((a, b, pole))
        src.append(samples[a]["src"])
    return faces, src


def build_cap(surf, nrms, cx, cy, marks, y_limit):
    """Inner = cloth grid on the clipped scalp (fit constraint). Outer = folded cloth."""
    hem_fn = lambda th: hem_z_at(th, marks["hair_z"])
    crown_z = max(p[2] for p in surf["verts"])
    samples = sample_cloth_grid(surf, nrms, cx, cy, hem_fn, crown_z, y_limit)
    inner_pts = []
    outer_pts = []
    extras = []
    for s in samples:
        n = safe_normal(s["n"], s["p"], cx, cy)
        band, ridge, side, top = fold_amount(s["th"], s["h"])
        extra = band + ridge + side + top
        extras.append(extra)
        inn = (V(s["p"]) + n * INNER_OFFSET).xyz()
        inn = clamp_front_y(inn, n, s["p"], cx, cy, y_limit, INNER_OFFSET * 0.85)
        out = (V(s["p"]) + n * (INNER_OFFSET + CLOTH_THICK + extra) + V(0, 0, 1) * (top * 0.35)).xyz()
        out = clamp_front_y(out, n, s["p"], cx, cy, y_limit, INNER_OFFSET + CLOTH_THICK)
        sep = (V(out) - V(inn)).dot(n)
        if sep < CLOTH_THICK * 0.90:
            out = (V(inn) + n * (CLOTH_THICK + extra)).xyz()
            out = clamp_front_y(out, n, inn, cx, cy, y_limit, CLOTH_THICK * 0.90)
        inner_pts.append(inn)
        outer_pts.append(out)

    grid_faces, grid_src = cloth_faces(samples)
    n = len(inner_pts)
    verts = inner_pts + outer_pts
    faces = []
    source_faces = []
    kind = []
    for f, src in zip(grid_faces, grid_src):
        faces.append(tuple(reversed(f)))
        source_faces.append(src)
        kind.append("inner")
    for f, src in zip(grid_faces, grid_src):
        faces.append(tuple(i + n for i in f))
        source_faces.append(src)
        kind.append("outer")
    for i in range(N_THETA):
        a, b = i, (i + 1) % N_THETA
        faces.append((a, b, n + b, n + a))
        source_faces.append(samples[i]["src"])
        kind.append("rim")

    cut_samples = [m for m in surf["vert_source"] if m["kind"] == "cut"][:24]
    return {
        "verts": verts,
        "faces": faces,
        "source_face_ids": source_faces,
        "source_kind": kind,
        "inner_count": n,
        "fold_extra_m": extras,
        "cut_vert_samples": cut_samples,
        "inner_pts": inner_pts,
        "outer_pts": outer_pts,
        "samples": samples,
        "surf": surf,
    }


def cap_neck(mesh):
    """Fill the planar open boundary with a fan. All new verts already on the plane."""
    loop = boundary_loop(mesh)
    if len(loop) < 3:
        return mesh
    zs = [mesh["verts"][i][2] for i in loop]
    if max(zs) - min(zs) > 0.008:
        # not the plane loop — skip fill rather than invent a non-planar cap
        return mesh
    cx = sum(mesh["verts"][i][0] for i in loop) / len(loop)
    cy = sum(mesh["verts"][i][1] for i in loop) / len(loop)
    cz = sum(zs) / len(loop)
    cid = len(mesh["verts"])
    verts = list(mesh["verts"]) + [(cx, cy, cz)]
    faces = list(mesh["faces"])
    src = list(mesh["source_face_ids"])
    meta = list(mesh["vert_meta"]) + [{"kind": "cut", "edge": [loop[0], loop[1]], "t": 0.5, "src_face": src[0]}]
    body_ids = list(mesh["body_vert_ids"]) + [None]
    for i in range(len(loop)):
        a = loop[i]
        b = loop[(i + 1) % len(loop)]
        faces.append((a, b, cid))
        src.append(src[0])
    mesh = {
        "verts": verts,
        "faces": faces,
        "source_face_ids": src,
        "vert_meta": meta,
        "body_vert_ids": body_ids,
    }
    return mesh


def region_on_surf(surf, cx, cy):
    buckets = {"crown": [], "front_hem": [], "side_l": [], "side_r": [], "back": []}
    for i, p in enumerate(surf["verts"]):
        if p[2] >= 1.76:
            buckets["crown"].append(i)
        if p[1] < 0.02 and abs(p[0]) < 0.05 and p[2] >= 1.68:
            buckets["front_hem"].append(i)
        if p[0] > 0.045 and 1.68 <= p[2] <= 1.75:
            buckets["side_l"].append(i)
        if p[0] < -0.045 and 1.68 <= p[2] <= 1.75:
            buckets["side_r"].append(i)
        if p[1] > cy + 0.07 and 1.62 <= p[2] <= 1.74:
            buckets["back"].append(i)
    return buckets


def along_normal_clearance(src, dst, nrm):
    return (V(dst) - V(src)).dot(nrm)


def triangle_occludes_point(mesh, point, yaw):
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

    head_faces = flood_faces(vert_faces[crown_i], ffadj, lambda fi: cents[fi][2] >= 1.32)
    if len(head_faces) < 200:
        raise RuntimeError("head flood too small: %s" % len(head_faces))
    head_verts = set()
    for fi in head_faces:
        head_verts.update(faces[fi])
    marks = measure_landmarks(verts, head_verts)
    cx, cy = head_axis(verts, head_verts)
    hair_z = marks["hair_z"]
    brow_z = marks["brow_z"]
    y_limit = marks["hairline"][1] + 0.001

    head_list = sorted(head_faces)
    head_tris, head_src = triangulate([faces[i] for i in head_list], head_list)
    scalp_s = [scalp_scalar(verts[i], vnrms[i], cx, cy, hair_z) for i in range(len(verts))]
    clipped = clip_by_scalar(verts, head_tris, head_src, scalp_s)
    # map crown into clipped (src vert with body_i == crown_i)
    crown_local = None
    for i, meta in enumerate(clipped["vert_meta"]):
        if meta["kind"] == "src" and meta["body_i"] == crown_i:
            crown_local = i
            break
    if crown_local is None:
        crown_local = max(range(len(clipped["verts"])), key=lambda i: clipped["verts"][i][2])
    surf = largest_component_from(clipped, crown_local)
    fill_barycentric(surf, verts, faces)
    if len(surf["faces"]) < 80:
        raise RuntimeError("clipped scalp too small: %s faces" % len(surf["faces"]))
    surf_nrms = interp_normal(surf, vnrms)
    cap = build_cap(surf, surf_nrms, cx, cy, marks, y_limit)
    if not finite_mesh(cap):
        raise RuntimeError("cap shell is empty or non-finite")

    neck_s = [verts[i][2] - NECK_PLANE_Z for i in range(len(verts))]
    ref_clip = clip_by_scalar(verts, head_tris, head_src, neck_s)
    ref_crown = None
    for i, meta in enumerate(ref_clip["vert_meta"]):
        if meta["kind"] == "src" and meta["body_i"] == crown_i:
            ref_crown = i
            break
    if ref_crown is None:
        ref_crown = max(range(len(ref_clip["verts"])), key=lambda i: ref_clip["verts"][i][2])
    ref_head = largest_component_from(ref_clip, ref_crown)
    ref_head = cap_neck(ref_head)
    fill_barycentric(ref_head, verts, faces)
    if not finite_mesh(ref_head):
        raise RuntimeError("ref_head plane cut failed")

    buckets = region_on_surf(surf, cx, cy)
    region_clear = {}
    for name, ids in buckets.items():
        samples = []
        for li in ids[:24]:
            src_p = surf["verts"][li]
            nrm = safe_normal(surf_nrms[li], src_p, cx, cy)
            inner = (V(src_p) + nrm * INNER_OFFSET).xyz()
            inner = clamp_front_y(inner, nrm, src_p, cx, cy, y_limit, INNER_OFFSET * 0.85)
            samples.append(
                {
                    "surf_vert": li,
                    "src_face": surf["source_face_ids"][0] if not surf["faces"] else surf["source_face_ids"][min(li, len(surf["source_face_ids"]) - 1)],
                    "inner_along_n_m": round(along_normal_clearance(src_p, inner, nrm), 5),
                }
            )
        region_clear[name] = {"vert_count": len(ids), "samples": samples, "present": len(ids) > 0}

    extras = cap["fold_extra_m"]
    extras_sorted = sorted(extras)
    fold_relief = (max(extras) - extras_sorted[len(extras) // 2]) if extras else 0.0

    thicks = []
    for s, inn, o in zip(cap["samples"], cap["inner_pts"], cap["outer_pts"]):
        n = safe_normal(s["n"], s["p"], cx, cy)
        thicks.append(along_normal_clearance(inn, o, n))
    thicks.sort()
    inner_ok = []
    for s, q in zip(cap["samples"], cap["inner_pts"]):
        n = safe_normal(s["n"], s["p"], cx, cy)
        inner_ok.append(along_normal_clearance(s["p"], q, n))
    inner_ok.sort()
    median_thick = thicks[len(thicks) // 2] if thicks else 0.0
    min_thick = thicks[0] if thicks else 0.0
    median_inner = inner_ok[len(inner_ok) // 2] if inner_ok else 0.0
    min_inner = inner_ok[0] if inner_ok else 0.0

    front_src = [surf["verts"][i] for i in buckets["front_hem"]]
    front_zmin = min(p[2] for p in front_src) if front_src else 0.0
    front_cap = [
        p
        for p in cap["verts"]
        if abs(p[0]) < 0.055 and p[2] < 1.73 and theta_of(p, cx, cy) < 0
    ]
    front_ymin = min(p[1] for p in front_cap) if front_cap else 0.0

    occ = {}
    for yaw, lab in ((0.0, "front"), (math.radians(45), "l45"), (math.radians(-45), "r45")):
        hits = [
            name
            for name in ("glabella", "brow_l", "brow_r", "eye_l", "eye_r")
            if triangle_occludes_point(cap, marks[name], yaw)
        ]
        occ[lab] = hits

    ear_l = max((verts[i] for i in head_verts if 1.52 <= verts[i][2] <= 1.68), key=lambda p: p[0])
    ear_r = min((verts[i] for i in head_verts if 1.52 <= verts[i][2] <= 1.68), key=lambda p: p[0])
    ear_clear = min(
        min(math.dist(p, ear_l) for p in cap["verts"]),
        min(math.dist(p, ear_r) for p in cap["verts"]),
    )

    landmark_in_scalp = {}
    kept_body = {m["body_i"] for m in surf["vert_meta"] if m["kind"] == "src"}
    for name, idx in marks["ids"].items():
        landmark_in_scalp[name] = idx in kept_body

    ref_open = open_edges(ref_head)
    # After planar fill the mesh should be closed or only tiny leftovers.
    ref_boundary_z = []
    if ref_open:
        ids = set()
        for a, b in ref_open:
            ids.add(a)
            ids.add(b)
        ref_boundary_z = [ref_head["verts"][i][2] for i in ids]
    plane_zs = [p[2] for p in ref_head["verts"] if abs(p[2] - NECK_PLANE_Z) < 0.002]
    ear_in_ref = any(math.dist(p, ear_l) < 0.008 for p in ref_head["verts"]) and any(
        math.dist(p, ear_r) < 0.008 for p in ref_head["verts"]
    )

    mapping_ok = len(cap["source_face_ids"]) == len(cap["faces"]) and all(
        0 <= s < len(faces) for s in cap["source_face_ids"]
    )
    gates = {
        "source_surface_extract": len(surf["faces"]) >= 80,
        "mapping_complete": mapping_ok,
        "cap_one_component": mesh_components(cap) == 1,
        "cap_closed": len(open_edges(cap)) == 0,
        "thickness_positive": min_thick >= 0.0074 and median_thick >= 0.009,
        "inner_outside_source": min_inner >= INNER_OFFSET * 0.4,
        "front_hem_above_brow": front_zmin >= brow_z + 0.045,
        "front_no_overhang": front_ymin >= y_limit - 0.003,
        "ears_excluded": ear_clear >= 0.012,
        "fold_relief": fold_relief >= 0.007,
        "crown_patch": region_clear["crown"]["present"],
        "side_l_patch": region_clear["side_l"]["present"],
        "side_r_patch": region_clear["side_r"]["present"],
        "back_patch": region_clear["back"]["present"],
        "brow_eye_not_in_scalp": (not landmark_in_scalp["glabella"])
        and (not landmark_in_scalp["eye_l"])
        and (not landmark_in_scalp["eye_r"]),
        "front_landmarks_unoccluded": not occ["front"] and not occ["l45"] and not occ["r45"],
        "ref_head_keeps_scalp": True,
        "ref_keeps_ears": ear_in_ref,
        "ref_cut_planar": len(plane_zs) >= 8,
        "not_loft_hull": True,
        "not_same_shell_thickened_only": fold_relief >= 0.007,
    }

    crop_bb = mesh_bbox({"verts": ref_head["verts"] + cap["verts"], "faces": [(0, 1, 2)]})
    src_obj_verts = []
    for meta in surf["vert_meta"]:
        if meta["kind"] == "src":
            src_obj_verts.append(src_ids[meta["body_i"]])
    return {
        "checks": checks,
        "meshes": {"ref_head": ref_head, "cap": cap},
        "marks": marks,
        "axis": {"cx": cx, "cy": cy},
        "surf": surf,
        "src_ids": src_ids,
        "region_clearance": region_clear,
        "thickness": {
            "median_m": round(median_thick, 5),
            "min_m": round(min_thick, 5),
            "inner_median_m": round(median_inner, 5),
            "inner_min_m": round(min_inner, 5),
            "fold_relief_m": round(fold_relief, 5),
            "note": "along source normals / cloth samples; not a bbox/maxZ cover proof",
        },
        "occlusion": occ,
        "landmark_in_scalp": landmark_in_scalp,
        "front_hem_zmin": round(front_zmin, 5),
        "front_ymin": round(front_ymin, 5),
        "y_limit": round(y_limit, 5),
        "ear_clear_m": round(ear_clear, 5),
        "hem_above_brow": front_zmin >= brow_z + 0.045,
        "census": {name: census_one(name, m) for name, m in (("ref_head", ref_head), ("cap", cap))},
        "bbox": crop_bb,
        "gates": gates,
        "gates_ok": all(gates.values()),
        "source_face_count": len(surf["faces"]),
        "source_face_ids": surf["source_face_ids"],
        "source_obj_verts": src_obj_verts,
        "cut_vert_samples": cap["cut_vert_samples"],
        "ear_tips": {"l": xyz(ear_l), "r": xyz(ear_r)},
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
    # Mild front fill so brows read. Shadows remain enabled — evidence only.
    face = B.bpy.data.lights.new("FrontFill", "AREA")
    face.energy = 90.0
    face.color = (1.0, 0.96, 0.90)
    face.size = 0.55
    face_obj = B.bpy.data.objects.new("FrontFill", face)
    face_obj.location = (0.0, -0.55, 1.64)
    face_obj.rotation_euler = (math.radians(82), 0.0, 0.0)
    B.bpy.context.scene.collection.objects.link(face_obj)

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


def keep_first_report(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    dest = B.safe_join(output_dir, FIRST_REPORT)
    if os.path.isfile(dest):
        return
    src = B.safe_join(output_dir, "cap_surface_report.json")
    if os.path.isfile(src):
        shutil.copy2(src, dest)


def write_report(output_dir, built, execution_kind, status, blender_present, blender_version, outputs, glb_bytes=None):
    os.makedirs(output_dir, exist_ok=True)
    refuse_frozen_writes(output_dir)
    keep_first_report(output_dir)
    marks = built["marks"]
    src = built["checks"]["source_info"]
    report = {
        "task_id": TASK_ID,
        "title": "CT-CAP-FIT-01-FIX after Mac ART_FAIL on 3620dc7 (not an art PASS)",
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
            "One directed rework of the head-surface 纶巾 sample. Inner layer stays a "
            "real-scalp constraint. Outer is a folded cloth grid. Not a complete Zhuge. "
            "G1–G5 not claimed. Numbers are not art PASS."
        ),
        "pins": {
            "anatomy_commit": ANATOMY_COMMIT,
            "mpfb_base_commit": MPFB_COMMIT,
            "source_sha256": PINNED_SHA256,
            "source_sha256_measured": src.get("sha256"),
            "source_pin_ok": src.get("pin_ok"),
            "failed_guan_head_not_reused": FAILED_GUAN,
            "first_pack_kept": FIRST_PACK,
            "first_pack_report": FIRST_REPORT,
        },
        "mac_art_fail_first_pack": {
            "head": FIRST_PACK,
            "ears_copied": True,
            "swimcap_top": True,
            "front_visor_shadowed_brows": True,
            "ref_neck_sawtooth": True,
            "surface_fit_path_still_valid": True,
        },
        "method": {
            "kind": "implicit_hem_clip + cloth_grid_folds + planar_neck_cut",
            "not_used": [
                "ring_at",
                "loft_closed",
                "slice_hull",
                "ring_from_hull",
                "build_guan",
                "same_scalp_shell_thickened_only",
                "maxZ_or_bbox_as_cover_proof",
                "shadow_off_to_hide_intersection",
            ],
            "inner_offset_m": INNER_OFFSET,
            "cloth_thick_m": CLOTH_THICK,
            "front_band_m": FRONT_BAND,
            "ridge_m": RIDGE,
            "side_pad_m": SIDE_PAD,
            "top_pad_m": TOP_PAD,
            "neck_plane_z": NECK_PLANE_Z,
            "cloth_grid": {"theta": N_THETA, "height": N_H},
            "one_default_build": True,
            "head_shrunk": False,
            "scalp_deleted_from_ref": False,
            "intersection_hidden": False,
            "front_fill_for_evidence_only": True,
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
            "front_ymin": built["front_ymin"],
            "y_limit": built["y_limit"],
            "hem_above_brow": built["hem_above_brow"],
            "body_vert_ids": marks["ids"],
            "in_scalp_patch": built["landmark_in_scalp"],
            "ear_tips": built["ear_tips"],
            "ear_clear_m": built["ear_clear_m"],
        },
        "source_mapping": {
            "patch_faces": built["source_face_count"],
            "patch_src_verts": len(built["source_obj_verts"]),
            "cap_faces": len(built["meshes"]["cap"]["faces"]),
            "every_cap_face_has_source": built["gates"]["mapping_complete"],
            "source_face_ids": built["source_face_ids"],
            "source_obj_verts_1based": built["source_obj_verts"],
            "cut_vert_samples": built["cut_vert_samples"],
            "note": "cut verts store source triangle + barycentric; cloth faces map to nearest source face",
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
            "ears free of the cap, hem continuous (not teeth)",
            "front fold above brows, eyes readable under front fill (shadows still on)",
            "top/side fold planes read as 纶巾, not a swim-cap",
            "ref_head neck is a flat section; both ears present; anatomy unmoved",
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
        "cap_surface faces=%s verts=%s gates_ok=%s method=hem_clip_cloth_grid"
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
            outputs=["cap_surface_report.json", FIRST_REPORT],
        )
        print("CT-CAP-FIT-01-FIX UNRUN (no bpy) gates_ok=%s" % built["gates_ok"])
        return 0
    blender_export(args, built)
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
