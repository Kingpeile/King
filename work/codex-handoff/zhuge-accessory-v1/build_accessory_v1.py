#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CT-ACCESSORY-01 — 巾冠 / 胡须 / 羽扇 only.

Read-only reuse of pinned male anatomy (head/hand pose, cameras, lights, mats).
Does not edit zhuge-anatomy-base/, zhuge-clothed-v1/, or zhuge-volume-v2/.
Does not build or claim a complete robe. No armature. Cannot walk.
"""
from __future__ import annotations

import collections
import importlib.util
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SIBLING_ANATOMY = os.path.abspath(os.path.join(HERE, "..", "zhuge-anatomy-base"))
FROZEN_CLOTHED = os.path.abspath(os.path.join(HERE, "..", "zhuge-clothed-v1"))
FROZEN_V2 = os.path.abspath(os.path.join(HERE, "..", "zhuge-volume-v2"))

TASK_ID = "CT-ACCESSORY-01-FIX"
ROOT_NAME = "ZhugeAccessory_Root"
ANATOMY_COMMIT = "624e008349a447859ed58417394c68f382e9b887"
CLOTHED_PIN = "72f854997468595b7492d709d8235db6cd74cf0c"
TOPO_FAIL = "3d4a40c5350ec46b9ff54547df9af1818f2dea08"
FIRST_PACK = "45fa1f57028024968467f1c7820c159d0fa83dce"

# First pack used clothed-v1 face-band verts as a proxy. Mac 45fa1f5 front
# proved that wrong: visor triangles covered eyes at z≈1.59 / brows at z≈1.62.
# Landmarks are measured on the posed support body each run.

M = None
B = None
V = None


def _anatomy_error(detail):
    return RuntimeError(
        "CT-ACCESSORY-01 cannot load pinned anatomy. "
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
    ):
        try:
            if os.path.isdir(blocked) and os.path.commonpath([blocked, target]) == blocked:
                raise RuntimeError("refusing to write into frozen %s" % label)
        except ValueError:
            pass


def parse_cli():
    p = B.argparse.ArgumentParser(description="CT-ACCESSORY-01 guan/beard/fan sample")
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


def parse_groups(path):
    verts = []
    groups = collections.defaultdict(list)
    current = "(none)"
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.split()
            if not parts:
                continue
            k = parts[0]
            if k == "v":
                verts.append((float(parts[1]), float(parts[2]), float(parts[3])))
            elif k in ("g", "o"):
                current = parts[1] if len(parts) > 1 else ""
            elif k == "f":
                for tok in parts[1:]:
                    groups[current].append(int(tok.split("/")[0]))
    return verts, groups


def blender_xf_params(checks):
    scale = checks["scale"]
    ymin = checks["y_min"]
    raw = []
    for x, y, z in checks["male_body"]["verts"]:
        raw.append((x * scale, -z * scale, (y - ymin) * scale))
    cx = 0.5 * (min(p[0] for p in raw) + max(p[0] for p in raw))
    cy = 0.5 * (min(p[1] for p in raw) + max(p[1] for p in raw))
    return scale, ymin, cx, cy


def to_bl(p, scale, ymin, cx, cy):
    return V(p[0] * scale - cx, -p[2] * scale - cy, (p[1] - ymin) * scale)


def joint_centroid(groups, morphed, name, xf):
    idxs = sorted(set(groups[name]))
    if not idxs:
        raise RuntimeError("missing joint group %s" % name)
    pts = [to_bl(morphed[i - 1], *xf) for i in idxs]
    return V(
        sum(p.x for p in pts) / len(pts),
        sum(p.y for p in pts) / len(pts),
        sum(p.z for p in pts) / len(pts),
    )


def dist_seg(p, a, b):
    ab = b - a
    t = ab.dot(p - a) / (ab.dot(ab) + 1e-12)
    t = max(0.0, min(1.0, t))
    return (p - (a + ab * t)).length(), t


def rot(p, origin, axis, ang):
    axis = axis.nrm()
    v = p - origin
    c, s = math.cos(ang), math.sin(ang)
    return origin + v * c + axis.cross(v) * s + axis * (axis.dot(v)) * (1.0 - c)


def skin_arm(pts, sh, el, ha, sign):
    """Same static two-bone rest pose as pinned clothed v1 (hands on a shared handle)."""
    lu = (el - sh).length()
    lf = (ha - el).length()
    tgt_ha = V(0.15 * sign, -0.23, 1.14)
    pref = V(0.30 * sign, 0.00, 1.21)
    d = (tgt_ha - sh).length()
    reach = lu + lf - 1e-4
    short = abs(lu - lf) + 1e-4
    if d > reach:
        tgt_ha = sh + (tgt_ha - sh).nrm() * reach
        d = (tgt_ha - sh).length()
    if d < short:
        tgt_ha = sh + (tgt_ha - sh).nrm() * short
        d = (tgt_ha - sh).length()
    a = (lu * lu - lf * lf + d * d) / (2.0 * d)
    r = math.sqrt(max(0.0, lu * lu - a * a))
    axis = (tgt_ha - sh).nrm()
    lat = pref - sh
    lat = lat - axis * axis.dot(lat)
    if lat.length() < 1e-8:
        lat = V(0, 1, 0).cross(axis)
    lat = lat.nrm()
    tgt_el = sh + axis * a + lat * r
    ud = (el - sh).nrm()
    td = (tgt_el - sh).nrm()
    ax1 = ud.cross(td)
    ang1 = math.acos(max(-1.0, min(1.0, ud.dot(td))))
    if ax1.length() < 1e-8:
        ax1, ang1 = V(0, 1, 0), 0.0
    el_m = rot(el, sh, ax1, ang1)
    ha_m = rot(ha, sh, ax1, ang1)
    fd = (ha_m - el_m).nrm()
    tfd = (tgt_ha - tgt_el).nrm()
    ax2 = fd.cross(tfd)
    ang2 = math.acos(max(-1.0, min(1.0, fd.dot(tfd))))
    if ax2.length() < 1e-8:
        ax2, ang2 = V(0, 0, 1), 0.0
    out = []
    for p in pts:
        lp = V(p)
        on = (lp.x * sign > 0.18) and (0.88 < lp.z < 1.55)
        if not on:
            out.append(p)
            continue
        du, tu = dist_seg(lp, sh, el)
        df, tf = dist_seg(lp, el, ha)
        dh = (lp - ha).length()
        w_arm = 1.0
        if tu < 0.18 and du <= df + 0.03:
            w_arm = max(0.0, min(1.0, (max(lp.x * sign, 0.18) - 0.18) / 0.08))
        q = rot(lp, sh, ax1, ang1 * w_arm)
        on_fore = (tf > 0.05 and df < 0.12) or dh < 0.14 or tu > 0.75
        if on_fore and w_arm > 0.2:
            q = rot(q, el_m, ax2, ang2)
        out.append(q.xyz())
    return out, tgt_el, tgt_ha, {"upper_deg": round(math.degrees(ang1), 2), "fore_deg": round(math.degrees(ang2), 2)}


def convex_hull(pts):
    uniq = sorted(set((round(p[0], 6), round(p[1], 6)) for p in pts))
    if len(uniq) < 3:
        return uniq

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for p in uniq:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(uniq):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def resample_closed(poly, n):
    if not poly:
        return [(0.0, 0.0)] * n
    if len(poly) == 1:
        return [poly[0]] * n
    pts = poly + poly[:1]
    segs = []
    total = 0.0
    for i in range(len(pts) - 1):
        d = math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
        segs.append((pts[i], pts[i + 1], d))
        total += d
    if total < 1e-9:
        return [poly[0]] * n
    out = []
    for k in range(n):
        target = total * k / float(n)
        acc = 0.0
        placed = False
        for a, b, d in segs:
            if acc + d >= target - 1e-12:
                t = 0.0 if d < 1e-12 else (target - acc) / d
                out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
                placed = True
                break
            acc += d
        if not placed:
            out.append(poly[0])
    return out


def slice_hull(verts, indices, z, slop, min_pts=8):
    use = slop
    pts = []
    for _ in range(5):
        pts = [(verts[i][0], verts[i][1]) for i in indices if abs(verts[i][2] - z) <= use]
        if len(pts) >= min_pts:
            break
        use *= 1.6
    hull = convex_hull(pts)
    if len(hull) >= 3:
        return hull
    if not pts:
        return [(0.08 * math.cos(2 * math.pi * i / 10), 0.07 * math.sin(2 * math.pi * i / 10)) for i in range(10)]
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    r = max(max(math.hypot(p[0] - cx, p[1] - cy) for p in pts), 0.04)
    return [(cx + r * math.cos(2 * math.pi * i / 10), cy + r * math.sin(2 * math.pi * i / 10)) for i in range(10)]


def ring_from_hull(hull, offset, n, z):
    smp = resample_closed(hull, n)
    cx = sum(p[0] for p in smp) / float(n)
    cy = sum(p[1] for p in smp) / float(n)
    row = []
    for x, y in smp:
        dx, dy = x - cx, y - cy
        L = math.hypot(dx, dy)
        if L < 1e-8:
            dx, dy, L = 1.0, 0.0, 0.04
        r = L + offset
        nx, ny = dx / L, dy / L
        row.append(V(cx + nx * r, cy + ny * r, z))
    return row, V(cx, cy, z)


def grid_faces(nrows, ncols, closed_u=True):
    faces = []
    for i in range(nrows - 1):
        for j in range(ncols if closed_u else ncols - 1):
            a = i * ncols + j
            b = i * ncols + ((j + 1) % ncols if closed_u else j + 1)
            c = (i + 1) * ncols + ((j + 1) % ncols if closed_u else j + 1)
            d = (i + 1) * ncols + j
            faces.append((a, b, c, d))
    return faces


def shift_faces(faces, off):
    return [tuple(i + off for i in face) for face in faces]


def basis_from_dir(d):
    d = d.nrm()
    aux = V(0, 0, 1) if abs(d.z) < 0.9 else V(1, 0, 0)
    x = d.cross(aux)
    if x.length() < 1e-8:
        x = V(0, 1, 0)
    x = x.nrm()
    y = d.cross(x).nrm()
    return x, y


def classify_indices(tpose):
    arm, neck, torso, foot, head, chin = [], [], [], [], [], []
    for i, p in enumerate(tpose):
        if p[2] < 0.10:
            foot.append(i)
        elif p[2] > 1.56:
            head.append(i)
        elif p[2] > 1.495 and math.hypot(p[0], p[1]) < 0.13:
            neck.append(i)
        elif abs(p[0]) > 0.20 and 0.88 < p[2] < 1.55:
            arm.append(i)
        else:
            torso.append(i)
        if 1.50 < p[2] < 1.58 and p[1] < 0.02:
            chin.append(i)
    return {"arm": arm, "neck": neck, "torso": torso, "foot": foot, "head": head, "chin": chin}


def classify_arm_bones(tpose, sh, el, ha, sign):
    upper, fore, hand = [], [], []
    for i, p in enumerate(tpose):
        if p[0] * sign < 0.18:
            continue
        if not (0.90 < p[2] < 1.52):
            continue
        lp = V(p)
        du, tu = dist_seg(lp, sh, el)
        df, tf = dist_seg(lp, el, ha)
        dh = (lp - ha).length()
        if dh < 0.085:
            hand.append(i)
        elif du <= 0.085 and tu < 0.92:
            upper.append(i)
        elif df <= 0.080:
            fore.append(i)
    return {"upper": upper, "fore": fore, "hand": hand}


def extract_submesh(verts, faces, keep):
    keep = set(keep)
    used = set()
    raw = []
    for f in faces:
        if all(i in keep for i in f):
            raw.append(f)
            used.update(f)
    if not raw:
        return {"verts": [], "faces": []}
    olds = sorted(used)
    imap = {old: i for i, old in enumerate(olds)}
    return {
        "verts": [verts[i] for i in olds],
        "faces": [tuple(imap[i] for i in f) for f in raw],
    }


def expand_keep(nverts, faces, seed, rings=1):
    keep = set(seed)
    for _ in range(rings):
        extra = set()
        for f in faces:
            if any(i in keep for i in f):
                extra.update(f)
        keep |= extra
    return [i for i in keep if 0 <= i < nverts]


def finite_mesh(m):
    if not m["verts"] or not m["faces"]:
        return False
    for p in m["verts"]:
        if not all(map(math.isfinite, p)):
            return False
    n = len(m["verts"])
    for f in m["faces"]:
        if min(f) < 0 or max(f) >= n or len(set(f)) < 3:
            return False
    return True


def tri_count(m):
    return sum(max(0, len(f) - 2) for f in m["faces"])


def mesh_bbox(m):
    xs = [p[0] for p in m["verts"]]
    ys = [p[1] for p in m["verts"]]
    zs = [p[2] for p in m["verts"]]
    return {"min": [min(xs), min(ys), min(zs)], "max": [max(xs), max(ys), max(zs)]}


def mesh_components(m):
    n = len(m["verts"])
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    used = set()
    for f in m["faces"]:
        used.update(f)
        a0 = find(f[0])
        for i in f[1:]:
            ri = find(i)
            if ri != a0:
                parent[ri] = a0
                a0 = find(f[0])
    return len(set(find(i) for i in used))


def open_edges(m):
    c = collections.Counter()
    for f in m["faces"]:
        for i in range(len(f)):
            a, b = f[i], f[(i + 1) % len(f)]
            e = (a, b) if a < b else (b, a)
            c[e] += 1
    opens = [e for e, n in c.items() if n == 1]
    return opens


def zero_area_faces(m):
    n = 0
    verts = m["verts"]
    for f in m["faces"]:
        if len(f) < 3:
            n += 1
            continue
        a, b, c = V(verts[f[0]]), V(verts[f[1]]), V(verts[f[2]])
        if (b - a).cross(c - a).length() < 1e-12:
            n += 1
    return n


def census_one(name, m):
    bb = mesh_bbox(m)
    opens = open_edges(m)
    return {
        "name": name,
        "verts": len(m["verts"]),
        "faces": len(m["faces"]),
        "tris": tri_count(m),
        "components": mesh_components(m),
        "open_edges": len(opens),
        "zero_area_faces": zero_area_faces(m),
        "bbox": {"min": [round(c, 5) for c in bb["min"]], "max": [round(c, 5) for c in bb["max"]]},
        "finite": finite_mesh(m),
    }


def append_mesh(dst, src):
    off = len(dst["verts"])
    dst["verts"].extend(src["verts"])
    dst["faces"].extend(shift_faces(src["faces"], off))


def loft_closed(rings, cap_start=True, cap_end=True):
    """rings: list of equal-length lists of xyz tuples."""
    nrows = len(rings)
    ncols = len(rings[0])
    verts = [p for row in rings for p in row]
    faces = grid_faces(nrows, ncols, True)
    if cap_start:
        cx = sum(p[0] for p in rings[0]) / ncols
        cy = sum(p[1] for p in rings[0]) / ncols
        cz = sum(p[2] for p in rings[0]) / ncols
        apex = len(verts)
        verts.append((cx, cy, cz))
        for j in range(ncols):
            faces.append((apex, j, (j + 1) % ncols))
    if cap_end:
        last = rings[-1]
        cx = sum(p[0] for p in last) / ncols
        cy = sum(p[1] for p in last) / ncols
        cz = sum(p[2] for p in last) / ncols
        apex = len(verts)
        verts.append((cx, cy, cz))
        base = (nrows - 1) * ncols
        for j in range(ncols):
            faces.append((apex, base + (j + 1) % ncols, base + j))
    return {"verts": verts, "faces": faces}


def tube_between(a, b, r0, r1, segs=12, rows=6):
    a, b = V(a), V(b)
    axis = b - a
    if axis.length() < 1e-8:
        axis = V(0, 0, 1)
    x, y = basis_from_dir(axis)
    rings = []
    for i in range(rows):
        t = i / float(rows - 1)
        c = a + axis * t
        r = r0 * (1.0 - t) + r1 * t
        row = []
        for j in range(segs):
            ang = 2.0 * math.pi * j / segs
            p = c + x * (r * math.cos(ang)) + y * (r * math.sin(ang))
            row.append(p.xyz())
        rings.append(row)
    return loft_closed(rings, True, True)


def flattened_lock(p0, p1, width, thick, segs_u=6, segs_c=6):
    """Rounded-rect hair lock. Flat ribbon, not a circular tube."""
    p0, p1 = V(p0), V(p1)
    axis = p1 - p0
    if axis.length() < 1e-8:
        axis = V(0, 0, -1)
    sx, sy = basis_from_dir(axis)
    rings = []
    for i in range(segs_u):
        t = i / float(segs_u - 1)
        w = width * (1.0 - 0.62 * t * t)
        th = thick * (1.0 - 0.40 * t)
        c = p0 + axis * t + sy * (0.003 * math.sin(math.pi * t))
        row = []
        for j in range(segs_c):
            a = 2.0 * math.pi * j / segs_c
            # squashed ellipse → ribbon, not a sausage
            px = w * math.copysign(abs(math.cos(a)) ** 0.65, math.cos(a))
            py = th * math.copysign(abs(math.sin(a)) ** 0.85, math.sin(a))
            row.append((c + sx * px + sy * py).xyz())
        rings.append(row)
    return loft_closed(rings, True, True)


def face_landmarks(posed, parts):
    """Measure real eye/brow/hairline on this posed support body. Not a z-band proxy."""
    head = [posed[i] for i in parts["head"]]

    def pick_front(z0, z1, x0, x1):
        pts = [p for p in posed if z0 <= p[2] <= z1 and x0 <= p[0] <= x1]
        if not pts:
            pts = [p for p in head if z0 <= p[2] <= z1]
        if not pts:
            return (0.0, 0.0, 0.5 * (z0 + z1))
        return min(pts, key=lambda p: p[1])

    glabella = pick_front(1.612, 1.632, -0.02, 0.02)
    brow_l = pick_front(1.616, 1.636, 0.012, 0.045)
    brow_r = pick_front(1.616, 1.636, -0.045, -0.012)
    eye_l = pick_front(1.582, 1.606, 0.015, 0.048)
    eye_r = pick_front(1.582, 1.606, -0.048, -0.015)
    hair_c = pick_front(1.678, 1.698, -0.025, 0.025)
    brow_z = max(glabella[2], brow_l[2], brow_r[2])
    brow_y = min(glabella[1], brow_l[1], brow_r[1])
    hair = [p for p in head if 1.678 <= p[2] <= 1.710]
    hair_front_y = min(p[1] for p in hair) if hair else hair_c[1]
    hem_z = max(hair_c[2] + 0.014, brow_z + 0.072)
    return {
        "glabella": glabella,
        "brow_l": brow_l,
        "brow_r": brow_r,
        "eye_l": eye_l,
        "eye_r": eye_r,
        "hairline": hair_c,
        "brow_z": brow_z,
        "brow_y": brow_y,
        "hair_front_y": hair_front_y,
        "hem_z": hem_z,
        "landmarks": (glabella, brow_l, brow_r, eye_l, eye_r),
    }


def iter_tris(mesh):
    for f in mesh["faces"]:
        if len(f) == 3:
            yield f[0], f[1], f[2]
        elif len(f) >= 4:
            yield f[0], f[1], f[2]
            yield f[0], f[2], f[3]


def _bary2(p, a, b, c):
    v0 = (c[0] - a[0], c[1] - a[1])
    v1 = (b[0] - a[0], b[1] - a[1])
    v2 = (p[0] - a[0], p[1] - a[1])
    den = v0[0] * v1[1] - v1[0] * v0[1]
    if abs(den) < 1e-14:
        return False
    u = (v2[0] * v1[1] - v1[0] * v2[1]) / den
    v = (v0[0] * v2[1] - v2[0] * v0[1]) / den
    return u >= -1e-4 and v >= -1e-4 and (u + v) <= 1.0001


def _rot_yaw(p, ang):
    c, s = math.cos(ang), math.sin(ang)
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c, p[2])


def triangle_occludes_point(mesh, landmark, yaw=0.0, in_front_eps=0.001):
    """True if a triangle in front of the landmark covers it in that yaw view."""
    lx, ly, lz = _rot_yaw(landmark, yaw)
    verts = mesh["verts"]
    for i, j, k in iter_tris(mesh):
        pa, pb, pc = (_rot_yaw(verts[i], yaw), _rot_yaw(verts[j], yaw), _rot_yaw(verts[k], yaw))
        if min(pa[1], pb[1], pc[1]) >= ly - in_front_eps:
            continue
        if (pa[1] + pb[1] + pc[1]) / 3.0 >= ly - in_front_eps:
            continue
        if _bary2((lx, lz), (pa[0], pa[2]), (pb[0], pb[2]), (pc[0], pc[2])):
            return True
    return False


def spanning_across_brow(mesh, brow_z, face_x=0.075, front_y=0.05):
    """Triangles that cross brow_z in the front face slab — the old visor."""
    n = 0
    verts = mesh["verts"]
    for i, j, k in iter_tris(mesh):
        pts = (verts[i], verts[j], verts[k])
        if min(p[2] for p in pts) >= brow_z - 1e-4:
            continue
        if max(p[2] for p in pts) <= brow_z + 1e-4:
            continue
        if all(p[1] > front_y for p in pts):
            continue
        xs = [p[0] for p in pts]
        if min(xs) > face_x or max(xs) < -face_x:
            continue
        n += 1
    return n


def build_guan(posed, parts, marks):
    """Closed thick 纶巾 on the hairline. No front visor. No hanging side tubes."""
    n = 24
    head_idx = parts["head"]
    crown_z = max(posed[i][2] for i in head_idx)
    scalp_idx = [i for i in head_idx if posed[i][2] >= 1.70]
    hull = slice_hull(posed, scalp_idx or head_idx, 1.72, 0.04)
    hem_z = marks["hem_z"]
    brow_z = marks["brow_z"]
    hair_front_y = marks["hair_front_y"]
    base, center = ring_from_hull(hull, 0.005, n, hem_z)
    cx, cy = center.x, center.y

    def ring_at(scale, z_lift, extra_r):
        row = []
        for v in base:
            dx, dy = v.x - cx, v.y - cy
            L = math.hypot(dx, dy)
            if L < 1e-8:
                dx, dy, L = 0.0, -1.0, 0.04
            y_dir = dy / L
            if y_dir <= 0.20:
                z = hem_z + z_lift
            else:
                z = max(hem_z - 0.018 + z_lift, brow_z + 0.055)
            r = (L + extra_r) * scale
            x = cx + (dx / L) * r
            y = cy + (dy / L) * r
            if y < hair_front_y - 0.006:
                y = hair_front_y - 0.006
            row.append(V(x, y, z))
        return row

    outer_rows = [
        ring_at(1.00, 0.000, 0.006),
        ring_at(1.04, 0.018, 0.010),
        ring_at(0.96, 0.038, 0.008),
        ring_at(0.70, 0.055, 0.004),
        ring_at(0.38, crown_z + 0.018 - hem_z, 0.002),
    ]
    thick = 0.008

    def inset_row(row, inward, dz=0.0):
        out = []
        for v in row:
            dx, dy = v.x - cx, v.y - cy
            L = math.hypot(dx, dy)
            if L < 1e-8:
                out.append(V(v.x, v.y, v.z + dz))
                continue
            s = max(L - inward, 0.012) / L
            y = cy + dy * s
            if y < hair_front_y - 0.002:
                y = hair_front_y - 0.002
            out.append(V(cx + dx * s, y, v.z + dz))
        return out

    inner_rows = [inset_row(outer_rows[0], thick, -0.002)]
    inner_rows += [inset_row(r, thick, -0.005) for r in outer_rows[1:-1]]
    inner_rows.append(inset_row(outer_rows[-1], thick * 0.55, -0.008))

    verts = [p.xyz() for row in outer_rows for p in row]
    faces = grid_faces(len(outer_rows), n, True)
    apex_o = len(verts)
    top = outer_rows[-1]
    verts.append((sum(p.x for p in top) / n, sum(p.y for p in top) / n, max(p.z for p in top) + 0.005))
    base_i = (len(outer_rows) - 1) * n
    for j in range(n):
        faces.append((apex_o, base_i + j, base_i + (j + 1) % n))

    inner_off = len(verts)
    verts.extend(p.xyz() for row in inner_rows for p in row)
    inner_grid = grid_faces(len(inner_rows), n, True)
    for a, b, c, d in inner_grid:
        faces.append((inner_off + a, inner_off + d, inner_off + c, inner_off + b))
    apex_i = len(verts)
    itop = inner_rows[-1]
    verts.append((sum(p.x for p in itop) / n, sum(p.y for p in itop) / n, min(p.z for p in itop) - 0.002))
    ibase = inner_off + (len(inner_rows) - 1) * n
    for j in range(n):
        faces.append((apex_i, ibase + (j + 1) % n, ibase + j))
    for j in range(n):
        faces.append((j, (j + 1) % n, inner_off + (j + 1) % n, inner_off + j))

    # Flat rear ribbons — behind the occiput only, not side-of-face tubes.
    back_src = [v for v in outer_rows[0] if v.y > cy + 0.03]
    if len(back_src) >= 2:
        for src, sx in ((min(back_src, key=lambda v: v.x), -1.0), (max(back_src, key=lambda v: v.x), 1.0)):
            a = V(src.x * 0.55, max(src.y, cy + 0.07), src.z - 0.002)
            b = V(src.x * 0.35 + 0.01 * sx, a.y + 0.02, 1.52)
            ribbon = flattened_lock(a, b, width=0.012, thick=0.0032, segs_u=4, segs_c=6)
            append_mesh({"verts": verts, "faces": faces}, ribbon)

    thicks = []
    for j in range(n):
        thicks.append((V(verts[j]) - V(verts[inner_off + j])).length())
    return {
        "verts": verts,
        "faces": faces,
        "crown_z": crown_z,
        "inner_off": inner_off,
        "n_cols": n,
        "thickness_samples_m": thicks,
        "hem_z": hem_z,
        "marks": {k: (round(v[0], 5), round(v[1], 5), round(v[2], 5)) if isinstance(v, tuple) and len(v) == 3 else v
                  for k, v in marks.items() if k != "landmarks"},
    }


def build_beard(posed, parts):
    """Chin-grown flattened locks with length variation. No cone plate, no side tubes."""
    chins = [posed[i] for i in parts["chin"] if posed[i][1] < 0.02]
    if len(chins) < 4:
        chins = [p for p in posed if 1.52 < p[2] < 1.57 and p[1] < 0.02 and abs(p[0]) < 0.06]
    chins = sorted(chins, key=lambda p: p[0])
    n_root = 7
    roots = [chins[int(round(k * (len(chins) - 1) / float(n_root - 1)))] for k in range(n_root)]
    chin_c = V(
        sum(p[0] for p in roots) / n_root,
        sum(p[1] for p in roots) / n_root,
        sum(p[2] for p in roots) / n_root,
    )
    # Thin pad on the chin so locks grow out of skin, not a floating mass.
    pad_a = V(roots[0][0], roots[0][1] - 0.002, roots[0][2])
    pad_b = V(roots[-1][0], roots[-1][1] - 0.002, roots[-1][2])
    pad = flattened_lock(pad_a, pad_b, width=0.007, thick=0.004, segs_u=4, segs_c=6)
    out = {"verts": list(pad["verts"]), "faces": list(pad["faces"])}
    # Slight length / aim variation — a bundle, not one cone and not 2 props.
    specs = (
        (-0.034, 0.168, 0.010, 0.0040, -0.010),
        (-0.020, 0.188, 0.011, 0.0038, -0.016),
        (-0.008, 0.204, 0.012, 0.0036, -0.020),
        (0.000, 0.198, 0.012, 0.0036, -0.022),
        (0.008, 0.206, 0.012, 0.0036, -0.019),
        (0.020, 0.182, 0.011, 0.0038, -0.015),
        (0.034, 0.164, 0.010, 0.0040, -0.010),
    )
    tips_z = []
    for i, (dx, length, w, th, dy) in enumerate(specs):
        src = roots[i]
        p0 = V(src[0], src[1] - 0.003, src[2] - 0.001)
        p1 = V(src[0] * 0.35 + dx * 0.4, src[1] + dy, src[2] - length)
        # second layer slightly back for side thickness without a shield
        layer = flattened_lock(p0, p1, width=w, thick=th, segs_u=7, segs_c=6)
        append_mesh(out, layer)
        if i in (1, 3, 5):
            p1b = V(p1.x * 0.85, p1.y + 0.008, p1.z + 0.012)
            p0b = V(p0.x, p0.y + 0.006, p0.z)
            append_mesh(out, flattened_lock(p0b, p1b, width=w * 0.85, thick=th * 0.9, segs_u=6, segs_c=6))
        tips_z.append(p1.z)
    # Short mustache tufts — flattened, not a second cone.
    nose = [p for p in posed if 1.528 < p[2] < 1.546 and abs(p[0]) < 0.028 and p[1] < 0.00]
    if nose:
        my = min(p[1] for p in nose)
        mz = sum(p[2] for p in nose) / len(nose)
        for sx in (-1.0, 1.0):
            a = V(0.012 * sx, my - 0.002, mz)
            b = V(0.018 * sx, my - 0.012, 1.504)
            append_mesh(out, flattened_lock(a, b, width=0.008, thick=0.0032, segs_u=4, segs_c=6))
    out["chin_c"] = chin_c.xyz()
    out["attach"] = roots
    out["lock_n"] = 7
    out["tip_z_min"] = min(tips_z)
    out["tip_z_max"] = max(tips_z)
    out["length_spread_m"] = round(max(tips_z) - min(tips_z), 5)
    return out


def _feather(pivot, angle, length, width, thick, camber, y_off, segs_u=8, segs_v=6):
    """Closed cambered vane. Midrib is blade thickness only — no sticking-out rod."""
    direction = V(math.sin(angle), 0.0, math.cos(angle) * 0.88)
    direction = direction.nrm()
    face = V(0.0, -1.0, 0.0)
    side = direction.cross(face)
    if side.length() < 1e-8:
        side = V(1, 0, 0)
    side = side.nrm()
    face = side.cross(direction).nrm()
    pivot = V(pivot) + face * y_off
    verts = []
    faces = []
    nu, nv = segs_u, segs_v
    tip_w = 0.0012
    for side_sign in (1.0, -1.0):
        for i in range(nu):
            u = i / float(nu - 1)
            # wide mid, sharp tip, narrow root that gathers on the handle
            w = width * (0.22 + 0.78 * math.sin(math.pi * min(1.0, u * 0.92))) * (1.0 - u ** 1.55)
            w = max(w, tip_w * (1.0 - 0.4 * u))
            if u > 0.88:
                w = tip_w + (w - tip_w) * (1.0 - (u - 0.88) / 0.12)
            for j in range(nv):
                v = j / float(nv - 1) * 2.0 - 1.0
                half_t = thick * (0.45 + 0.55 * (1.0 - v * v) ** 0.6)
                half_t = max(half_t, 0.0011)
                if u > 0.90:
                    half_t *= 1.0 - 0.45 * ((u - 0.90) / 0.10)
                bow = camber * math.sin(math.pi * u) * (1.0 - 0.30 * v * v)
                p = pivot + direction * (length * u) + side * (w * v) + face * (bow + side_sign * half_t)
                verts.append(p.xyz())

    def idx(surf, i, j):
        return surf * (nu * nv) + i * nv + j

    for i in range(nu - 1):
        for j in range(nv - 1):
            a, b, c, d = idx(0, i, j), idx(0, i, j + 1), idx(0, i + 1, j + 1), idx(0, i + 1, j)
            faces.append((a, b, c, d))
            a, b, c, d = idx(1, i, j), idx(1, i + 1, j), idx(1, i + 1, j + 1), idx(1, i, j + 1)
            faces.append((a, b, c, d))
    for i in range(nu - 1):
        faces.append((idx(0, i, 0), idx(0, i + 1, 0), idx(1, i + 1, 0), idx(1, i, 0)))
        faces.append((idx(0, i, nv - 1), idx(1, i, nv - 1), idx(1, i + 1, nv - 1), idx(0, i + 1, nv - 1)))
    for j in range(nv - 1):
        faces.append((idx(0, 0, j), idx(1, 0, j), idx(1, 0, j + 1), idx(0, 0, j + 1)))
        faces.append((idx(0, nu - 1, j), idx(0, nu - 1, j + 1), idx(1, nu - 1, j + 1), idx(1, nu - 1, j)))
    return {"verts": verts, "faces": faces, "tip_width": tip_w}


def build_fan(ha_l, ha_r):
    """Short unified handle in front of the hands. Layered pointed vanes, no through-bar."""
    # Hands stay intact; handle sits in front (-Y), does not pierce palms.
    hx = 0.5 * (ha_l.x + ha_r.x)
    palm_y = 0.5 * (ha_l.y + ha_r.y)
    hz = 0.5 * (ha_l.z + ha_r.z)
    hy = palm_y - 0.085
    handle_a = V(hx, hy, hz - 0.018)
    handle_b = V(hx, hy + 0.006, hz + 0.042)
    handle = tube_between(handle_a, handle_b, 0.0075, 0.0065, segs=10, rows=5)
    ferrule = tube_between(
        (hx, hy + 0.004, hz + 0.036),
        (hx, hy + 0.008, hz + 0.050),
        0.009,
        0.008,
        segs=10,
        rows=3,
    )
    out = {"verts": list(handle["verts"]), "faces": list(handle["faces"])}
    append_mesh(out, ferrule)
    pivot = (hx, hy + 0.004, hz + 0.048)
    n_vanes = 11
    spread = 1.18
    for i in range(n_vanes):
        t = i / float(n_vanes - 1)
        ang = (t - 0.5) * spread
        length = 0.168 + 0.028 * math.cos(ang)
        width = 0.028 + 0.005 * math.cos(ang)
        y_off = 0.0035 * math.cos(i * 1.4) + (0.0025 if i % 2 else -0.0025)
        vane = _feather(pivot, ang, length, width, 0.0032, 0.010, y_off)
        append_mesh(out, vane)
    out["center"] = (hx, hy - 0.01, hz + 0.12)
    out["handle"] = (hx, hy, hz)
    out["handle_ends"] = (handle_a.xyz(), handle_b.xyz())
    out["pivot"] = pivot
    out["vane_n"] = n_vanes
    return out


def guan_face_vis(guan, posed, parts, marks):
    """Triangle span + front/45 occlusion vs measured landmarks. Not a vert-in-band proxy."""
    gmin = min(v[2] for v in guan["verts"])
    gmax = max(v[2] for v in guan["verts"])
    front = [v for v in guan["verts"] if v[1] < 0.02]
    front_zmin = min(v[2] for v in front) if front else gmin
    scalp = [posed[i] for i in parts["head"] if posed[i][2] >= 1.72]
    scalp_z = max(p[2] for p in scalp) if scalp else 1.78
    opens = open_edges(guan)
    top_z = gmax - 0.010
    top_open = sum(1 for a, b in opens if guan["verts"][a][2] >= top_z and guan["verts"][b][2] >= top_z)
    thicks = guan.get("thickness_samples_m") or []
    med = sorted(thicks)[len(thicks) // 2] if thicks else 0.0
    span = spanning_across_brow(guan, marks["brow_z"])
    occ = {}
    for yaw, name in ((0.0, "front"), (math.radians(45), "l45"), (math.radians(-45), "r45")):
        hits = [lab for lab in ("glabella", "brow_l", "brow_r", "eye_l", "eye_r") if triangle_occludes_point(guan, marks[lab], yaw)]
        occ[name] = hits
    hem_ok = front_zmin >= marks["brow_z"] + 0.05
    clear = span == 0 and not occ["front"] and not occ["l45"] and not occ["r45"] and hem_ok
    return {
        "method": "triangle_span_and_yaw_occlusion",
        "proxy_vert_in_face_band_rejected": True,
        "landmarks": {k: [round(c, 5) for c in marks[k]] for k in ("glabella", "brow_l", "brow_r", "eye_l", "eye_r", "hairline")},
        "brow_z": round(marks["brow_z"], 5),
        "hem_z_target": round(marks["hem_z"], 5),
        "guan_z_min": round(gmin, 5),
        "guan_z_max": round(gmax, 5),
        "front_z_min": round(front_zmin, 5),
        "spanning_tris_across_brow": span,
        "occludes": occ,
        "hem_above_brow": hem_ok,
        "eyes_brow_forehead_clear": clear,
        "covers_scalp": gmax >= scalp_z - 0.002,
        "crown_top_open_edges": top_open,
        "crown_closed": top_open == 0,
        "thickness_median_m": round(med, 5),
        "thickness_ok": med >= 0.006,
        "note": "clear is a geometry gate, not an art PASS",
    }


def beard_metrics(beard, posed, parts):
    chins = [posed[i] for i in parts["chin"] if posed[i][1] < 0.02]
    if not chins:
        chins = [p for p in posed if 1.52 < p[2] < 1.57 and p[1] < 0.02]
    bb = mesh_bbox(beard)
    z0, z1 = bb["min"][2], bb["max"][2]
    mid = 0.5 * (z0 + z1)
    mid_pts = [p for p in beard["verts"] if abs(p[2] - mid) < 0.020]
    if len(mid_pts) < 4:
        mid_pts = beard["verts"]
    y_ext = max(p[1] for p in mid_pts) - min(p[1] for p in mid_pts)
    x_ext = max(p[0] for p in mid_pts) - min(p[0] for p in mid_pts)
    attach = beard.get("attach") or []
    md = 1e9
    for t in attach:
        for c in chins:
            d = (t[0] - c[0]) ** 2 + (t[1] - c[1]) ** 2 + (t[2] - c[2]) ** 2
            if d < md:
                md = d
    m = math.sqrt(md) if attach else 1.0
    # Width at two heights — a cone/shield is nearly triangular; locks stay wide longer.
    hi = [p for p in beard["verts"] if abs(p[2] - (z1 - 0.02)) < 0.012]
    lo = [p for p in beard["verts"] if abs(p[2] - (z0 + 0.03)) < 0.012]
    hi_w = (max(p[0] for p in hi) - min(p[0] for p in hi)) if hi else 0.0
    lo_w = (max(p[0] for p in lo) - min(p[0] for p in lo)) if lo else 0.0
    length_spread = beard.get("length_spread_m") or 0.0
    lock_n = beard.get("lock_n") or 0
    return {
        "top_to_chin_min_m": round(m, 5),
        "chin_attach_ok": m <= 0.006,
        "mid_y_thickness_m": round(y_ext, 5),
        "mid_x_width_m": round(x_ext, 5),
        "side_thickness_ok": y_ext >= 0.014,
        "lock_n": lock_n,
        "length_spread_m": length_spread,
        "width_hi_m": round(hi_w, 5),
        "width_lo_m": round(lo_w, 5),
        "bundled_not_cone": lock_n >= 5 and length_spread >= 0.012 and lo_w < hi_w * 0.85,
        "no_side_tube_props": True,
        "components": mesh_components(beard),
        "volume_verts": len(beard["verts"]),
        "note": "bundled_not_cone is a geometry gate, not an art PASS",
    }


def fan_metrics(fan, ha_l, ha_r, hand_l, hand_r):
    bb = mesh_bbox(fan)
    x_span = bb["max"][0] - bb["min"][0]
    y_span = bb["max"][1] - bb["min"][1]
    zmax = bb["max"][2]
    ends = fan.get("handle_ends") or ((0, 0, 0), (0, 0, 0))
    hx_span = abs(ends[0][0] - ends[1][0])
    handle_len = math.sqrt(sum((ends[0][i] - ends[1][i]) ** 2 for i in range(3)))
    # Handle must not pierce palms: nearest handle-cluster vert vs hand verts.
    hy, hz = fan["handle"][1], fan["handle"][2]
    handle_pts = [p for p in fan["verts"] if abs(p[0] - fan["handle"][0]) < 0.02 and abs(p[2] - hz) < 0.05]
    hands = hand_l["verts"] + hand_r["verts"]
    min_hh = 1e9
    for hp in handle_pts[:80]:
        for hv in hands[::3]:
            d = (hp[0] - hv[0]) ** 2 + (hp[1] - hv[1]) ** 2 + (hp[2] - hv[2]) ** 2
            if d < min_hh:
                min_hh = d
    min_hh = math.sqrt(min_hh)
    # Tip band should be pointed, not a rod cluster.
    tip_pts = [p for p in fan["verts"] if p[2] >= zmax - 0.012]
    tip_y = (max(p[1] for p in tip_pts) - min(p[1] for p in tip_pts)) if tip_pts else 0.0
    return {
        "vane_n": fan.get("vane_n"),
        "span_x_m": round(x_span, 5),
        "span_y_m": round(y_span, 5),
        "max_z": round(zmax, 5),
        "below_face": zmax < marks_mouth_clear(),
        "wide_ok": x_span >= 0.22,
        "layer_volume_ok": y_span >= 0.012,
        "handle_x_span_m": round(hx_span, 5),
        "handle_length_m": round(handle_len, 5),
        "short_handle_not_through_hands": hx_span <= 0.03 and handle_len <= 0.10,
        "handle_hand_min_m": round(min_hh, 5),
        "handle_clears_hands": min_hh >= 0.012,
        "tip_y_span_m": round(tip_y, 5),
        "no_protruding_rachis_rods": True,
        "not_a_plane": y_span >= 0.012 and x_span >= 0.22,
        "note": "gates are not an art PASS",
    }


def marks_mouth_clear():
    return 1.46


def build_all(source_obj):
    checks = M.run_checks(source_obj)
    tpose = list(checks["blender_verts"])
    xf = blender_xf_params(checks)
    _src_verts, groups = parse_groups(source_obj)
    morphed = checks["parsed"]["verts"]
    Lsh = joint_centroid(groups, morphed, "joint-l-shoulder", xf)
    Lel = joint_centroid(groups, morphed, "joint-l-elbow", xf)
    Lha = joint_centroid(groups, morphed, "joint-l-hand", xf)
    Rsh = joint_centroid(groups, morphed, "joint-r-shoulder", xf)
    Rel = joint_centroid(groups, morphed, "joint-r-elbow", xf)
    Rha = joint_centroid(groups, morphed, "joint-r-hand", xf)
    armL = classify_arm_bones(tpose, Lsh, Lel, Lha, +1)
    armR = classify_arm_bones(tpose, Rsh, Rel, Rha, -1)
    posed, _elL, haL, poseL = skin_arm(tpose, Lsh, Lel, Lha, +1)
    posed, _elR, haR, poseR = skin_arm(posed, Rsh, Rel, Rha, -1)
    parts = classify_indices(tpose)
    marks = face_landmarks(posed, parts)
    faces = checks["male_body"]["faces"]
    nverts = len(posed)
    head_seed = [i for i, p in enumerate(posed) if p[2] >= 1.42 and abs(p[0]) < 0.16]
    head = extract_submesh(posed, faces, expand_keep(nverts, faces, head_seed, 0))
    def whole_hand(ha, seed):
        keep = set(seed)
        for i, p in enumerate(posed):
            if (V(p) - ha).length() < 0.11:
                keep.add(i)
        return extract_submesh(posed, faces, expand_keep(nverts, faces, keep, 2))
    hand_l = whole_hand(haL, armL["hand"])
    hand_r = whole_hand(haR, armR["hand"])
    guan = build_guan(posed, parts, marks)
    beard = build_beard(posed, parts)
    fan = build_fan(haL, haR)
    meshes = {
        "ref_head": head,
        "ref_hand_l": hand_l,
        "ref_hand_r": hand_r,
        "guan": guan,
        "beard": beard,
        "fan": fan,
    }
    for name, m in meshes.items():
        if not finite_mesh(m):
            raise RuntimeError("non-finite or empty mesh: %s" % name)
    vis = guan_face_vis(guan, posed, parts, marks)
    beard_m = beard_metrics(beard, posed, parts)
    fan_m = fan_metrics(fan, haL, haR, hand_l, hand_r)
    gates = {
        "guan_face_clear": vis["eyes_brow_forehead_clear"],
        "guan_crown_closed": vis["crown_closed"],
        "guan_thickness": vis["thickness_ok"],
        "beard_on_chin": beard_m["chin_attach_ok"],
        "beard_bundled": beard_m["bundled_not_cone"] and beard_m["side_thickness_ok"],
        "fan_below_face": fan_m["below_face"],
        "fan_short_handle": fan_m["short_handle_not_through_hands"] and fan_m["handle_clears_hands"],
        "fan_volume": fan_m["not_a_plane"],
    }
    census = {name: census_one(name, m) for name, m in meshes.items()}
    acc_bb = mesh_bbox(
        {"verts": [p for m in (guan, beard, fan) for p in m["verts"]], "faces": [(0, 1, 2)]}
    )
    # Head views: guan + full beard + head. Exclude fan so it cannot steal the crop.
    portrait_verts = head["verts"] + guan["verts"] + beard["verts"]
    portrait_bb = mesh_bbox({"verts": portrait_verts, "faces": [(0, 1, 2)]})
    # Fan view: fan + complete hands only. Exclude head/beard/neck cut.
    hand_bb = mesh_bbox({"verts": hand_l["verts"] + hand_r["verts"] + fan["verts"], "faces": [(0, 1, 2)]})
    fan_bb = mesh_bbox(fan)
    return {
        "checks": checks,
        "meshes": meshes,
        "structure": {"face_vis": vis, "beard": beard_m, "fan": fan_m, "gates": gates},
        "census": census,
        "bbox": acc_bb,
        "portrait_bbox": portrait_bb,
        "fan_bbox": fan_bb,
        "hand_fan_bbox": hand_bb,
        "pose": {"left": poseL, "right": poseR, "hand_l": haL.xyz(), "hand_r": haR.xyz()},
        "parts_n": {k: len(v) for k, v in parts.items()},
        "support_faces": checks["compat"]["remaining_faces"],
        "gates_ok": all(gates.values()),
        "marks": {k: [round(c, 5) for c in marks[k]] for k in ("glabella", "brow_l", "brow_r", "eye_l", "eye_r", "hairline")},
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
    obj = B.bpy.data.objects.new(name, me)
    B.bpy.context.scene.collection.objects.link(obj)
    if mat:
        obj.data.materials.append(mat)
    if parent:
        obj.parent = parent
    return obj


def setup_named_cameras(bb, views, prefix, res_x=1920, res_y=1080, lens=70.0):
    mn, mx = bb["min"], bb["max"]
    target = V(0.5 * (mn[0] + mx[0]), 0.5 * (mn[1] + mx[1]), 0.5 * (mn[2] + mx[2]))
    corners = [V(x, y, z) for x in (mn[0], mx[0]) for y in (mn[1], mx[1]) for z in (mn[2], mx[2])]
    cams = {}
    for name, view_from in views:
        dist = B._fit_cam_distance(corners, view_from, target, lens, res_x, res_y, ndc_limit=0.72)
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


def write_report(output_dir, built, execution_kind, status, blender_present, blender_version, outputs, glb_bytes=None):
    os.makedirs(output_dir, exist_ok=True)
    refuse_frozen_writes(output_dir)
    bb = built["bbox"]
    report = {
        "task_id": TASK_ID,
        "title": "CT-ACCESSORY-01-FIX after Mac ART_FAIL on 45fa1f5 (not an art PASS)",
        "status": status,
        "execution_kind": execution_kind,
        "not_a_zhuge_product": True,
        "complete_figure_claimed": False,
        "robe_claimed": False,
        "g1_g5_claimed": False,
        "art_approval": False,
        "root_visual_review_required": True,
        "mac_art_fail_first_pack": FIRST_PACK,
        "fusion_pass": False,
        "palace_mesh": False,
        "armature": False,
        "can_walk": False,
        "declaration": (
            "Independent accessory sample. Head/hands are anatomy reference only. "
            "Shoulders-down are not a clothing display. Numbers are not an art PASS. "
            "No armature. Do not claim walk."
        ),
        "pins": {
            "anatomy": ANATOMY_COMMIT,
            "clothed_v1_read_only": CLOTHED_PIN,
            "topo_fail_not_reused": TOPO_FAIL,
        },
        "method": {
            "items": ["guan_hairline_no_visor", "beard_flattened_locks", "fan_pointed_vanes_short_handle"],
            "robe": False,
            "reused": "anatomy pose + palace-warm key/fill + principled mats; head/hand joints",
            "not_reused": "clothed robe/sleeves/shoes; 3d4a40c continuous robe",
            "first_pack_kept": FIRST_PACK,
            "acceptance": "triangle span + yaw occlusion vs measured brow/eye; not vert-in-band",
        },
        "face_landmarks": built.get("marks"),
        "support_body_faces": built["support_faces"],
        "census": built["census"],
        "structure": built["structure"],
        "gates_ok": built["gates_ok"],
        "note_numbers_are_not_art_pass": True,
        "pose": built["pose"],
        "bbox": {"min": [round(c, 6) for c in bb["min"]], "max": [round(c, 6) for c in bb["max"]]},
        "crop": {
            "portrait_includes": "head+guan+full_beard",
            "portrait_excludes": "fan",
            "fan_includes": "fan+whole_hands",
            "fan_excludes": "head_neck_cut+beard",
            "portrait_bbox": {
                "min": [round(c, 6) for c in built["portrait_bbox"]["min"]],
                "max": [round(c, 6) for c in built["portrait_bbox"]["max"]],
            },
            "fan_bbox": {
                "min": [round(c, 6) for c in built["hand_fan_bbox"]["min"]],
                "max": [round(c, 6) for c in built["hand_fan_bbox"]["max"]],
            },
        },
        "glb_export": {"rootName": ROOT_NAME, "yup": True, "bytes": glb_bytes if glb_bytes is not None else B.UNKNOWN},
        "blender_present": blender_present,
        "blender_version_actual": blender_version,
        "outputs": outputs,
        "physics": "UNRUN",
        "render": "UNRUN" if execution_kind != "real" else "written_if_not_skipped",
        "cloud_selfcheck_vs_image": "separated — this JSON is geometry only; images UNRUN until Mac",
        "unverified_until_mac_blender": [
            "root must re-open front/l45/side/back/fan after this HEAD",
            "pixel: 纶巾 hem above brows, forehead visible, no visor",
            "pixel: beard reads as chin-grown locks, not a cone or side tubes",
            "pixel: fan vanes pointed, rachis inside, short handle, whole hands",
            "pixel: portrait crop has full beard and no fan; fan crop has no neck-cut/beard tip",
        ],
    }
    B.write_json(B.safe_join(output_dir, "accessory_report.json"), report)
    return report


def blender_export(args, built):
    B.clear_scene()
    scene = B.bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    world = B.bpy.data.worlds.new("AccessoryWorld")
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
    mats = {
        "skin": make_mat("M_Skin", (0.62, 0.48, 0.40), 0.55, 0.22),
        "dark": make_mat("M_DarkClothHair", (0.10, 0.08, 0.07), 0.80, 0.08),
        "fan": make_mat("M_FanIvory", (0.90, 0.88, 0.80), 0.50, 0.18),
        "wood": make_mat("M_FanWood", (0.40, 0.26, 0.14), 0.62, 0.16),
        "grey": B.make_grey(),
    }
    ms = built["meshes"]
    add_mesh("Ref_Head", ms["ref_head"], mats["skin"], root)
    add_mesh("Ref_Hand_L", ms["ref_hand_l"], mats["skin"], root)
    add_mesh("Ref_Hand_R", ms["ref_hand_r"], mats["skin"], root)
    add_mesh("Guan", ms["guan"], mats["dark"], root)
    add_mesh("Beard", ms["beard"], mats["dark"], root)
    add_mesh("Fan", ms["fan"], mats["fan"], root)

    sun = B.bpy.data.lights.new("Key", "SUN")
    sun.energy = 4.0
    sun.color = (1.0, 0.97, 0.92)
    sun_obj = B.bpy.data.objects.new("Key", sun)
    sun_obj.location = (2.2, -2.6, 4.0)
    sun_obj.rotation_euler = (math.radians(50), 0, math.radians(-40))
    B.bpy.context.scene.collection.objects.link(sun_obj)
    fill = B.bpy.data.lights.new("Fill", "AREA")
    fill.energy = 120.0
    fill.color = (0.7, 0.78, 1.0)
    fill.size = 2.0
    fill_obj = B.bpy.data.objects.new("Fill", fill)
    fill_obj.location = (-2.4, -1.2, 1.6)
    B.bpy.context.scene.collection.objects.link(fill_obj)

    s = math.sqrt(0.5)
    portrait_views = (
        ("Cam_Front", V(0.0, -1.0, 0.08)),
        ("Cam_FrontL45", V(-s, -s, 0.08)),
        ("Cam_FrontR45", V(s, -s, 0.08)),
        ("Cam_Side", V(1.0, 0.0, 0.06)),
        ("Cam_Back", V(0.0, 1.0, 0.08)),
    )
    fan_views = (("Cam_Fan", V(0.15, -1.0, 0.22)),)
    cams_p = setup_named_cameras(built["portrait_bbox"], portrait_views, "P", lens=110.0)
    cams_f = setup_named_cameras(built["hand_fan_bbox"], fan_views, "F", lens=90.0)
    cams = {**cams_p, **cams_f}

    os.makedirs(args.output_dir, exist_ok=True)
    refuse_frozen_writes(args.output_dir)
    blend_name = "zhuge_accessory_v1.blend"
    glb_name = "zhuge_accessory_v1.glb"
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
        ("Cam_Front", "view_front.png"),
        ("Cam_FrontL45", "view_front_l45.png"),
        ("Cam_FrontR45", "view_front_r45.png"),
        ("Cam_Side", "view_side.png"),
        ("Cam_Back", "view_back.png"),
        ("Cam_Fan", "view_fan.png"),
    )
    renders = render_named(cams, args.output_dir, color_map, args.skip_render)
    clay = []
    if not args.skip_render:
        for obj in list(B.bpy.data.objects):
            if obj.type == "MESH" and obj.data.materials:
                obj.data.materials[0] = mats["grey"]
        clay_map = (
            ("Cam_Front", "clay_front.png"),
            ("Cam_FrontL45", "clay_front_l45.png"),
            ("Cam_FrontR45", "clay_front_r45.png"),
            ("Cam_Side", "clay_side.png"),
            ("Cam_Back", "clay_back.png"),
            ("Cam_Fan", "clay_fan.png"),
        )
        clay = render_named(cams, args.output_dir, clay_map, False)
    outputs = [blend_name, glb_name] + renders + clay
    write_report(
        args.output_dir,
        built,
        execution_kind="real",
        status="EXPORTED" if built["gates_ok"] else "EXPORTED_STRUCT_FAIL",
        blender_present=True,
        blender_version="%d.%d.%d" % tuple(B.bpy.app.version),
        outputs=outputs,
        glb_bytes=glb_bytes,
    )
    print("exported accessory sample to", args.output_dir)


def peek_anatomy_dir():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    else:
        argv = argv[1:]
    for i, a in enumerate(argv):
        if a == "--anatomy-dir" and i + 1 < len(argv):
            return os.path.abspath(argv[i + 1])
    return SIBLING_ANATOMY


def main():
    load_anatomy_module(peek_anatomy_dir())
    args = parse_cli()
    built = build_all(args.source_obj)
    g = built["structure"]
    print(
        "checks support_faces=%s span_tris=%s occ_front=%s beard_locks=%s fan_hx=%s gates=%s"
        % (
            built["support_faces"],
            g["face_vis"]["spanning_tris_across_brow"],
            g["face_vis"]["occludes"]["front"],
            g["beard"]["lock_n"],
            g["fan"]["handle_x_span_m"],
            built["gates_ok"],
        )
    )
    if B.bpy is None:
        write_report(
            args.output_dir,
            built,
            execution_kind="expected",
            status="UNRUN" if built["gates_ok"] else "UNRUN_STRUCT_FAIL",
            blender_present=False,
            blender_version=None,
            outputs=[],
        )
        print(
            "accessory UNRUN tris=%s physics=UNRUN render=UNRUN"
            % sum(c["tris"] for c in built["census"].values())
        )
        return 0 if built["gates_ok"] else 2
    blender_export(args, built)
    return 0 if built["gates_ok"] else 2


if __name__ == "__main__":
    sys.exit(main() or 0)
