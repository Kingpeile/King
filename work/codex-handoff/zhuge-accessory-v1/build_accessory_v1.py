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

TASK_ID = "CT-ACCESSORY-01"
ROOT_NAME = "ZhugeAccessory_Root"
ANATOMY_COMMIT = "624e008349a447859ed58417394c68f382e9b887"
CLOTHED_PIN = "72f854997468595b7492d709d8235db6cd74cf0c"
TOPO_FAIL = "3d4a40c5350ec46b9ff54547df9af1818f2dea08"

# Face bands from pinned clothed builder (front = -Y). Do not lower the brim.
FACE_Z_MOUTH = 1.50
FACE_Z_EYE_TOP = 1.655
GUAN_MIN_Z_FRONT = 1.668

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


def build_guan(posed, parts):
    """Closed thick 纶巾. Front brim above brow. No top hole. No face board."""
    n = 24
    head = [posed[i] for i in parts["head"]]
    crown_z = max(p[2] for p in head)
    scalp_idx = [i for i in parts["head"] if posed[i][2] >= 1.70]
    hull = slice_hull(posed, scalp_idx or parts["head"], 1.72, 0.04)
    brow_band = [p for p in posed if 1.665 <= p[2] <= 1.70 and abs(p[0]) < 0.08]
    brow_y = min(p[1] for p in brow_band) if brow_band else -0.02

    # Base ring on scalp, then lift/offset by column (front stays high).
    base, center = ring_from_hull(hull, 0.012, n, 1.672)
    cx, cy = center.x, center.y

    def shaped_ring(scale, z_front, z_side, z_back, extra_r, flatten=0.0):
        row = []
        for j, v in enumerate(base):
            dx, dy = v.x - cx, v.y - cy
            L = math.hypot(dx, dy)
            a = math.atan2(dy, dx)
            front = max(0.0, -math.sin(a))
            back = max(0.0, math.sin(a))
            side = 1.0 - max(front, back)
            z = z_front * front + z_side * side + z_back * back
            # Keep the entire front third above the brow bar.
            if front > 0.28:
                z = max(z, GUAN_MIN_Z_FRONT + 0.004)
            r = (L + extra_r) * scale
            # Slightly boxier X, a bit longer back — 纶巾, not a bucket.
            r *= 1.0 + 0.06 * abs(math.cos(a)) + 0.04 * back
            x = cx + (dx / (L + 1e-12)) * r
            y = cy + (dy / (L + 1e-12)) * r
            if flatten:
                z = z * (1.0 - flatten) + (z_front * 0.35 + z_back * 0.65) * flatten
            row.append(V(x, y, z))
        return row

    outer_rows = [
        shaped_ring(1.00, 1.674, 1.598, 1.618, 0.016, 0.0),
        shaped_ring(1.06, 1.698, 1.640, 1.655, 0.022, 0.0),
        shaped_ring(1.02, 1.735, 1.710, 1.720, 0.018, 0.15),
        shaped_ring(0.78, 1.768, 1.758, 1.762, 0.010, 0.45),
        shaped_ring(0.42, crown_z + 0.028, crown_z + 0.024, crown_z + 0.026, 0.004, 0.70),
    ]
    # Inner lining: 9 mm inward, slightly lower top so the crown has real fill.
    thick = 0.009

    def inset_row(row, inward, dz=0.0):
        out = []
        for v in row:
            dx, dy = v.x - cx, v.y - cy
            L = math.hypot(dx, dy)
            if L < 1e-8:
                out.append(V(v.x, v.y, v.z + dz))
                continue
            s = max(L - inward, 0.012) / L
            out.append(V(cx + dx * s, cy + dy * s, v.z + dz))
        return out

    inner_rows = [inset_row(outer_rows[0], thick, -0.003)]
    inner_rows += [inset_row(r, thick, -0.006) for r in outer_rows[1:-1]]
    inner_rows.append(inset_row(outer_rows[-1], thick * 0.6, -0.010))

    verts = [p.xyz() for row in outer_rows for p in row]
    faces = grid_faces(len(outer_rows), n, True)
    # Closed outer crown (this is the old 巾顶洞 failure).
    apex_o = len(verts)
    top = outer_rows[-1]
    verts.append(
        (
            sum(p.x for p in top) / n,
            sum(p.y for p in top) / n,
            max(p.z for p in top) + 0.006,
        )
    )
    base_i = (len(outer_rows) - 1) * n
    for j in range(n):
        faces.append((apex_o, base_i + j, base_i + (j + 1) % n))

    inner_off = len(verts)
    verts.extend(p.xyz() for row in inner_rows for p in row)
    # Inner grid reversed so normals point into the lining cavity.
    inner_grid = grid_faces(len(inner_rows), n, True)
    for a, b, c, d in inner_grid:
        faces.append((inner_off + a, inner_off + d, inner_off + c, inner_off + b))
    apex_i = len(verts)
    itop = inner_rows[-1]
    verts.append(
        (
            sum(p.x for p in itop) / n,
            sum(p.y for p in itop) / n,
            min(p.z for p in itop) - 0.002,
        )
    )
    ibase = inner_off + (len(inner_rows) - 1) * n
    for j in range(n):
        faces.append((apex_i, ibase + (j + 1) % n, ibase + j))

    # Seal brim (outer row0 ↔ inner row0).
    for j in range(n):
        a = j
        b = (j + 1) % n
        c = inner_off + (j + 1) % n
        d = inner_off + j
        faces.append((a, b, c, d))

    # Rear 巾带 — thick cloth tails, behind the head only.
    back = [v for v in outer_rows[0] if v.y > cy + 0.01]
    if len(back) >= 2:
        left = min(back, key=lambda v: v.x)
        right = max(back, key=lambda v: v.x)
        for src, sx in ((left, -1.0), (right, 1.0)):
            a = V(src.x + 0.012 * sx, src.y + 0.006, src.z - 0.004)
            b = V(src.x + 0.018 * sx, src.y + 0.034, 1.42)
            tube = tube_between(a, b, 0.011, 0.007, segs=8, rows=5)
            off = len(verts)
            verts.extend(tube["verts"])
            faces.extend(shift_faces(tube["faces"], off))

    # Thickness samples: outer brim vs inner brim.
    thicks = []
    for j in range(n):
        o = V(verts[j])
        inn = V(verts[inner_off + j])
        thicks.append((o - inn).length())

    return {
        "verts": verts,
        "faces": faces,
        "crown_z": crown_z,
        "brow_y": brow_y,
        "inner_off": inner_off,
        "n_cols": n,
        "thickness_samples_m": thicks,
        "apex_outer_i": apex_o,
    }


def _profile_xy(rx, ry, n, scallop, front_bias):
    row = []
    for j in range(n):
        a = 2.0 * math.pi * j / n
        # a=0 → +X; we use local (side, depth) then map later
        wobble = 1.0 + scallop * math.cos(6.0 * a) * (0.55 + 0.45 * max(0.0, math.cos(a)))
        x = rx * math.cos(a) * wobble
        y = ry * math.sin(a) * (1.0 + front_bias * max(0.0, -math.sin(a)))
        row.append((x, y))
    return row


def _place_profile(center, axis, local_xy, xaxis=None):
    axis = axis.nrm()
    if xaxis is None:
        sx, sy = basis_from_dir(axis)
    else:
        sx = xaxis.nrm()
        sy = axis.cross(sx).nrm()
        sx = sy.cross(axis).nrm()
    return [(center + sx * xy[0] + sy * xy[1]).xyz() for xy in local_xy]


def build_beard(posed, parts):
    """Closed hair-mass from the chin. Bundled silhouette, real Y depth, not a plate or 3 tubes."""
    chins = [posed[i] for i in parts["chin"] if posed[i][1] < 0.02]
    if len(chins) < 4:
        chins = [p for p in posed if 1.52 < p[2] < 1.57 and p[1] < 0.02 and abs(p[0]) < 0.06]
    chins = sorted(chins, key=lambda p: p[0])
    n_attach = 9
    xs = [chins[int(round(k * (len(chins) - 1) / float(n_attach - 1)))] for k in range(n_attach)]
    chin_c = V(
        sum(p[0] for p in xs) / n_attach,
        sum(p[1] for p in xs) / n_attach,
        sum(p[2] for p in xs) / n_attach,
    )
    # Grow down and slightly forward; stay off the mouth plane.
    tip = V(0.0, chin_c.y - 0.046, 1.325)
    axis = tip - chin_c
    side_x = V(1, 0, 0)
    nprof = 16
    stations = (
        (0.00, 0.038, 0.018, 0.10, 0.15),
        (0.12, 0.040, 0.024, 0.14, 0.22),
        (0.28, 0.036, 0.032, 0.16, 0.28),
        (0.46, 0.030, 0.036, 0.16, 0.22),
        (0.64, 0.022, 0.030, 0.14, 0.12),
        (0.80, 0.014, 0.020, 0.12, 0.06),
        (0.93, 0.008, 0.012, 0.08, 0.02),
        (1.00, 0.004, 0.007, 0.04, 0.00),
    )
    rings = []
    for t, rx, ry, scallop, fbias in stations:
        c = chin_c + axis * t
        # Root station sits on the real chin samples (natural grow-out).
        if t == 0.0:
            c = V(chin_c.x, chin_c.y - 0.002, chin_c.z - 0.002)
        local = _profile_xy(rx, ry, nprof, scallop, fbias)
        rings.append(_place_profile(c, axis if t > 0.02 else V(0.0, -0.15, -0.85), local, side_x))
    main = loft_closed(rings, cap_start=True, cap_end=True)
    # Pull the first-ring verts toward actual chin samples so it grows out of skin.
    for j in range(n_attach):
        # map attach samples onto the first ring's front-ish verts
        src = xs[j]
        best = None
        best_d = 1e9
        for i in range(nprof):
            p = main["verts"][i]
            d = (p[0] - src[0]) ** 2 + (p[2] - src[2]) ** 2
            if d < best_d:
                best_d = d
                best = i
        if best is not None:
            q = main["verts"][best]
            main["verts"][best] = (src[0], src[1] - 0.003, src[2] - 0.001)
            # keep a back-of-root counterpart for thickness
            _ = q

    # Mustache: short volume under the nose, not a mouth cover.
    nose_band = [p for p in posed if 1.528 < p[2] < 1.548 and abs(p[0]) < 0.03 and p[1] < 0.00]
    if nose_band:
        mz = sum(p[2] for p in nose_band) / len(nose_band)
        my = min(p[1] for p in nose_band)
    else:
        mz, my = 1.536, chin_c.y - 0.012
    m0 = V(0.0, my - 0.002, mz)
    m1 = V(0.0, my - 0.018, 1.498)
    m_axis = m1 - m0
    m_rings = []
    for t, rx, ry in ((0.0, 0.028, 0.008), (0.45, 0.024, 0.011), (1.0, 0.010, 0.006)):
        c = m0 + m_axis * t
        local = _profile_xy(rx, ry, 12, 0.08, 0.2)
        m_rings.append(_place_profile(c, m_axis if t > 0.05 else V(0, -0.4, -0.9), local, V(1, 0, 0)))
    must = loft_closed(m_rings, True, True)

    # Cheek connectors: jaw corners → chin mass (one visual 三缕, still volume).
    jaw_l = min(xs, key=lambda p: p[0])
    jaw_r = max(xs, key=lambda p: p[0])
    out = {"verts": list(main["verts"]), "faces": list(main["faces"])}
    append_mesh(out, must)
    for jaw, sx in ((jaw_l, -1.0), (jaw_r, 1.0)):
        a = V(jaw[0], jaw[1] - 0.004, jaw[2] + 0.006)
        b = V(jaw[0] * 0.35, chin_c.y - 0.020, chin_c.z - 0.055)
        tube = tube_between(a, b, 0.009, 0.012, segs=8, rows=5)
        append_mesh(out, tube)
    out["chin_c"] = chin_c.xyz()
    out["attach"] = xs
    return out


def _feather(pivot, angle, length, width, thick, camber, y_off, segs_u=8, segs_v=6):
    """Closed cambered vane with a rachis ridge. Not a single plane."""
    # Fan plane is XZ; visible face toward -Y (front camera).
    direction = V(math.sin(angle), 0.0, math.cos(angle) * 0.92)
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
    # Two surfaces (front/back) + edge stitch. v across [-1,1], u along [0,1].
    nu, nv = segs_u, segs_v
    for side_sign in (1.0, -1.0):
        for i in range(nu):
            u = i / float(nu - 1)
            # teardrop planform: narrow root, wide mid, pointed tip
            w = width * (0.34 + 0.66 * math.sin(math.pi * min(1.0, u * 1.05))) * (1.0 - 0.72 * u ** 2.1)
            w = max(w, 0.006)
            for j in range(nv):
                v = j / float(nv - 1) * 2.0 - 1.0
                # thicker at rachis, real edge thickness
                half_t = thick * (0.38 + 0.62 * (1.0 - v * v) ** 0.55)
                half_t = max(half_t, 0.0016)
                bow = camber * math.sin(math.pi * u) * (1.0 - 0.35 * v * v)
                p = (
                    pivot
                    + direction * (length * u)
                    + side * (w * v)
                    + face * (bow + side_sign * half_t)
                )
                verts.append(p.xyz())
    # front grid
    def idx(surf, i, j):
        return surf * (nu * nv) + i * nv + j

    for i in range(nu - 1):
        for j in range(nv - 1):
            a, b, c, d = idx(0, i, j), idx(0, i, j + 1), idx(0, i + 1, j + 1), idx(0, i + 1, j)
            faces.append((a, b, c, d))
            a, b, c, d = idx(1, i, j), idx(1, i + 1, j), idx(1, i + 1, j + 1), idx(1, i, j + 1)
            faces.append((a, b, c, d))
    # sides, root, tip
    for i in range(nu - 1):
        faces.append((idx(0, i, 0), idx(0, i + 1, 0), idx(1, i + 1, 0), idx(1, i, 0)))
        faces.append((idx(0, i, nv - 1), idx(1, i, nv - 1), idx(1, i + 1, nv - 1), idx(0, i + 1, nv - 1)))
    for j in range(nv - 1):
        faces.append((idx(0, 0, j), idx(1, 0, j), idx(1, 0, j + 1), idx(0, 0, j + 1)))
        faces.append((idx(0, nu - 1, j), idx(0, nu - 1, j + 1), idx(1, nu - 1, j + 1), idx(1, nu - 1, j)))
    # rachis as a real midrib
    rachis = tube_between(
        (pivot + direction * 0.012).xyz(),
        (pivot + direction * (length * 0.96)).xyz(),
        0.0028,
        0.0014,
        segs=6,
        rows=5,
    )
    append_mesh({"verts": verts, "faces": faces}, rachis)
    return {"verts": verts, "faces": faces}


def build_fan(ha_l, ha_r):
    """Wide layered 羽扇: cambered vanes + thick handle. Below the face."""
    hx = 0.5 * (ha_l.x + ha_r.x)
    hy = 0.5 * (ha_l.y + ha_r.y) - 0.010
    hz = 0.5 * (ha_l.z + ha_r.z)
    handle_l = V(min(ha_l.x, ha_r.x) - 0.028, hy, hz)
    handle_r = V(max(ha_l.x, ha_r.x) + 0.028, hy, hz)
    handle = tube_between(handle_l, handle_r, 0.0085, 0.0085, segs=12, rows=7)
    # Pommel + ferrule volume
    mid = V(hx, hy, hz)
    pommel = tube_between((hx, hy, hz - 0.012), (hx, hy, hz + 0.012), 0.011, 0.011, segs=10, rows=4)
    ferrule = tube_between((hx - 0.016, hy, hz), (hx + 0.016, hy, hz), 0.012, 0.012, segs=10, rows=3)
    out = {"verts": list(handle["verts"]), "faces": list(handle["faces"])}
    append_mesh(out, pommel)
    append_mesh(out, ferrule)

    pivot = (hx, hy - 0.012, hz + 0.016)
    n_vanes = 13
    spread = 1.34  # radians — wide sector, not a stick
    for i in range(n_vanes):
        t = i / float(n_vanes - 1)
        ang = (t - 0.5) * spread
        # side feathers keep length so the planform stays wide
        length = 0.228 + 0.042 * math.cos(ang)
        width = 0.036 + 0.006 * math.cos(ang)
        thick = 0.0036
        camber = 0.012
        y_off = 0.0045 * math.cos(i * 1.7) + (0.003 if i % 2 else -0.003)
        vane = _feather(pivot, ang, length, width, thick, camber, y_off)
        append_mesh(out, vane)
    out["center"] = (hx, hy - 0.02, hz + 0.10)
    out["handle"] = (hx, hy, hz)
    out["pivot"] = pivot
    out["vane_n"] = n_vanes
    return out


def guan_face_vis(guan, posed, parts):
    hits = [
        v
        for v in guan["verts"]
        if FACE_Z_MOUTH <= v[2] <= FACE_Z_EYE_TOP and v[1] < 0.02 and abs(v[0]) < 0.075
    ]
    gmin = min(v[2] for v in guan["verts"])
    gmax = max(v[2] for v in guan["verts"])
    front = [v for v in guan["verts"] if v[1] < 0.00 and abs(v[0]) < 0.08]
    front_zmin = min(v[2] for v in front) if front else gmin
    scalp = [posed[i] for i in parts["head"] if posed[i][2] >= 1.72]
    scalp_z = max(p[2] for p in scalp) if scalp else 1.78
    opens = open_edges(guan)
    top_z = gmax - 0.010
    top_open = 0
    for a, b in opens:
        pa, pb = guan["verts"][a], guan["verts"][b]
        if pa[2] >= top_z and pb[2] >= top_z:
            top_open += 1
    thicks = guan.get("thickness_samples_m") or []
    med = sorted(thicks)[len(thicks) // 2] if thicks else 0.0
    return {
        "face_z_clear": [FACE_Z_MOUTH, FACE_Z_EYE_TOP],
        "guan_z_min": round(gmin, 5),
        "guan_z_max": round(gmax, 5),
        "front_z_min": round(front_zmin, 5),
        "guan_min_z_bar": GUAN_MIN_Z_FRONT,
        "guan_verts_in_face_front": len(hits),
        "eyes_brow_forehead_clear": len(hits) == 0 and front_zmin >= GUAN_MIN_Z_FRONT - 0.002,
        "covers_scalp": gmax >= scalp_z - 0.002,
        "crown_top_open_edges": top_open,
        "crown_closed": top_open == 0,
        "thickness_median_m": round(med, 5),
        "thickness_ok": med >= 0.006,
        "brow_y": round(guan.get("brow_y", 0.0), 5),
    }


def beard_metrics(beard, posed, parts):
    chins = [posed[i] for i in parts["chin"] if posed[i][1] < 0.02]
    if not chins:
        chins = [p for p in posed if 1.52 < p[2] < 1.57 and p[1] < 0.02]
    bb = mesh_bbox(beard)
    z0, z1 = bb["min"][2], bb["max"][2]
    mid = 0.5 * (z0 + z1)
    mid_pts = [p for p in beard["verts"] if abs(p[2] - mid) < 0.025]
    if len(mid_pts) < 4:
        mid_pts = beard["verts"]
    y_ext = max(p[1] for p in mid_pts) - min(p[1] for p in mid_pts)
    x_ext = max(p[0] for p in mid_pts) - min(p[0] for p in mid_pts)
    top = [p for p in beard["verts"] if p[2] >= z1 - 0.012]
    md = 1e9
    for t in top:
        for c in chins:
            d = (t[0] - c[0]) ** 2 + (t[1] - c[1]) ** 2 + (t[2] - c[2]) ** 2
            if d < md:
                md = d
    m = math.sqrt(md)
    plate = y_ext < 0.022 or (x_ext > 1e-6 and y_ext / x_ext < 0.28)
    return {
        "top_to_chin_min_m": round(m, 5),
        "chin_attach_ok": m <= 0.010,
        "mid_y_thickness_m": round(y_ext, 5),
        "mid_x_width_m": round(x_ext, 5),
        "side_thickness_ok": y_ext >= 0.028,
        "not_a_plate": (not plate) and y_ext >= 0.028,
        "components": mesh_components(beard),
        "volume_verts": len(beard["verts"]),
    }


def fan_metrics(fan):
    bb = mesh_bbox(fan)
    x_span = bb["max"][0] - bb["min"][0]
    y_span = bb["max"][1] - bb["min"][1]
    z_span = bb["max"][2] - bb["min"][2]
    zmax = bb["max"][2]
    # Handle verts are the first tube (~12*7 + caps). Use bbox of low-z cluster near handle.
    hy = fan["handle"][1]
    hz = fan["handle"][2]
    handle_pts = [p for p in fan["verts"] if abs(p[2] - hz) < 0.02 and abs(p[1] - hy) < 0.02]
    if handle_pts:
        hy_ext = max(p[1] for p in handle_pts) - min(p[1] for p in handle_pts)
        hz_ext = max(p[2] for p in handle_pts) - min(p[2] for p in handle_pts)
        handle_thick = min(hy_ext, hz_ext)
    else:
        handle_thick = 0.0
    return {
        "vane_n": fan.get("vane_n"),
        "span_x_m": round(x_span, 5),
        "span_y_m": round(y_span, 5),
        "span_z_m": round(z_span, 5),
        "max_z": round(zmax, 5),
        "below_face": zmax < FACE_Z_MOUTH - 0.04,
        "wide_ok": x_span >= 0.30,
        "layer_volume_ok": y_span >= 0.018,
        "handle_thickness_m": round(handle_thick, 5),
        "handle_ok": handle_thick >= 0.012,
        "not_a_plane": y_span >= 0.018 and x_span >= 0.30,
    }


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
    faces = checks["male_body"]["faces"]
    nverts = len(posed)
    head_seed = [i for i, p in enumerate(posed) if p[2] >= 1.42 and abs(p[0]) < 0.16]
    head = extract_submesh(posed, faces, expand_keep(nverts, faces, head_seed, 0))
    hand_l = extract_submesh(posed, faces, expand_keep(nverts, faces, armL["hand"], 1))
    hand_r = extract_submesh(posed, faces, expand_keep(nverts, faces, armR["hand"], 1))
    guan = build_guan(posed, parts)
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
    vis = guan_face_vis(guan, posed, parts)
    beard_m = beard_metrics(beard, posed, parts)
    fan_m = fan_metrics(fan)
    gates = {
        "guan_face_clear": vis["eyes_brow_forehead_clear"],
        "guan_crown_closed": vis["crown_closed"],
        "guan_thickness": vis["thickness_ok"],
        "beard_on_chin": beard_m["chin_attach_ok"],
        "beard_side_volume": beard_m["side_thickness_ok"] and beard_m["not_a_plate"],
        "fan_below_face": fan_m["below_face"],
        "fan_wide_volume": fan_m["not_a_plane"] and fan_m["handle_ok"],
    }
    census = {name: census_one(name, m) for name, m in meshes.items()}
    acc_bb = mesh_bbox(
        {"verts": [p for m in (guan, beard, fan) for p in m["verts"]], "faces": [(0, 1, 2)]}
    )
    portrait_verts = head["verts"] + guan["verts"] + [p for p in beard["verts"] if p[2] > 1.40]
    portrait_bb = mesh_bbox({"verts": portrait_verts, "faces": [(0, 1, 2)]})
    fan_bb = mesh_bbox(fan)
    hand_bb = mesh_bbox({"verts": hand_l["verts"] + hand_r["verts"] + fan["verts"], "faces": [(0, 1, 2)]})
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


def write_report(output_dir, built, execution_kind, status, blender_present, blender_version, outputs, glb_bytes=None):
    os.makedirs(output_dir, exist_ok=True)
    refuse_frozen_writes(output_dir)
    bb = built["bbox"]
    report = {
        "task_id": TASK_ID,
        "title": "Zhuge accessory sample — guan / beard / fan only (not a clothed PASS)",
        "status": status,
        "execution_kind": execution_kind,
        "not_a_zhuge_product": True,
        "complete_figure_claimed": False,
        "robe_claimed": False,
        "g1_g5_claimed": False,
        "art_approval": False,
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
            "items": ["guan_closed_thick", "beard_chin_volume", "fan_layered_vanes"],
            "robe": False,
            "reused": "anatomy pose + palace-warm key/fill + principled mats; head/hand joints",
            "not_reused": "clothed robe/sleeves/shoes; 3d4a40c continuous robe",
        },
        "support_body_faces": built["support_faces"],
        "census": built["census"],
        "structure": built["structure"],
        "gates_ok": built["gates_ok"],
        "note_numbers_are_not_art_pass": True,
        "pose": built["pose"],
        "bbox": {"min": [round(c, 6) for c in bb["min"]], "max": [round(c, 6) for c in bb["max"]]},
        "glb_export": {"rootName": ROOT_NAME, "yup": True, "bytes": glb_bytes if glb_bytes is not None else B.UNKNOWN},
        "blender_present": blender_present,
        "blender_version_actual": blender_version,
        "outputs": outputs,
        "physics": "UNRUN",
        "render": "UNRUN" if execution_kind != "real" else "written_if_not_skipped",
        "unverified_until_mac_blender": [
            "pixel: 纶巾 closed top / brow clear / no face board",
            "pixel: beard side thickness reads as hair mass, not a plate",
            "pixel: fan vanes layered with handle, not a card",
            "Y-up GLB import of accessory-only scene",
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
    cams_p = setup_named_cameras(built["portrait_bbox"], portrait_views, "P", lens=85.0)
    cams_f = setup_named_cameras(built["hand_fan_bbox"], fan_views, "F", lens=70.0)
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
        "checks support_faces=%s guan_face_hits=%s crown_open=%s beard_y=%s fan_span=%s gates=%s"
        % (
            built["support_faces"],
            g["face_vis"]["guan_verts_in_face_front"],
            g["face_vis"]["crown_top_open_edges"],
            g["beard"]["mid_y_thickness_m"],
            g["fan"]["span_x_m"],
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
