#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CT-COSTUME-01 — one standing clothed candidate on the frozen male anatomy body.

Imports frozen anatomy helpers (read-only). Does not edit zhuge-anatomy-base/.
Does not import zhuge-volume-v2 empty-robe generators.

Method: body-hull-offset continuous panels around the real posed body,
hanging wide sleeves from shoulder joints. Not licensed MHCLO (none available
for an adult-male 交领袍 without plugins). Not an armature. Cannot walk.
"""
from __future__ import annotations

import collections
import importlib.util
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ANATOMY_DIR = os.path.abspath(os.path.join(HERE, "..", "zhuge-anatomy-base"))
FROZEN_V2 = os.path.abspath(os.path.join(HERE, "..", "zhuge-volume-v2"))

_spec = importlib.util.spec_from_file_location(
    "anatomy_male_frozen", os.path.join(ANATOMY_DIR, "apply_male_volume.py")
)
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)
B = M.B
V = B.V

TASK_ID = "CT-COSTUME-01-FIX"
ROOT_NAME = "ZhugeClothed_Root"
SUPPORT_BODY_COMMIT = "624e008349a447859ed58417394c68f382e9b887"
MAC_FAIL_COMMIT = "629035d21489e1e6b2bf75d813a67367061ff592"
MAC_SUPPORT_BODY = {
    "commit": SUPPORT_BODY_COMMIT,
    "exit": 0,
    "glb_bytes": 626508,
    "tris": 26756,
    "height_m": 1.78,
    "minY": 0,
    "note": "Mac accepted as clothing support body. Still too athletic-slender vs 03. Not Zhuge PASS.",
}

# Face bands measured on the posed hm08 head (front = -Y).
FACE_Z_MOUTH = 1.50
FACE_Z_EYE_TOP = 1.655
GUAN_MIN_Z = 1.668  # above eyes/brow; board must not drop below this

COLS = 28
TORSO_Z = (
    (1.505, "neck", 0.014, False),
    (1.460, "collar", 0.024, False),
    (1.405, "shoulder", 0.040, True),
    (1.330, "chest", 0.048, True),
    (1.230, "chest2", 0.052, True),
    (1.120, "lower_chest", 0.054, True),
    (1.020, "waist", 0.058, True),
    (0.920, "hip", 0.072, True),
    (0.780, "thigh", 0.088, True),
    (0.620, "knee_hi", 0.102, True),
    (0.460, "knee", 0.116, True),
    (0.300, "shin", 0.128, True),
    (0.160, "hem", 0.138, True),
    (0.095, "hem_lip", 0.124, True),
)
SLEEVE_COLS = 16
SLEEVE_UPPER_ROWS = 6
SLEEVE_FORE_ROWS = 6


def refuse_frozen_writes(path):
    B.refuse_frozen_dir(path)
    target = os.path.abspath(path)
    for blocked, label in ((FROZEN_V2, "zhuge-volume-v2"), (ANATOMY_DIR, "zhuge-anatomy-base")):
        try:
            if os.path.commonpath([blocked, target]) == blocked:
                raise RuntimeError("refusing to write into frozen %s" % label)
        except ValueError:
            pass


def parse_cli():
    p = B.argparse.ArgumentParser(description="CT-COSTUME-01 standing clothed candidate")
    p.add_argument("--source-obj", default=None)
    p.add_argument("--output-dir", default=None)
    p.add_argument("--skip-render", action="store_true")
    args, _unknown = p.parse_known_args(B.argv_after_dash())
    if not args.source_obj:
        args.source_obj = os.path.join(ANATOMY_DIR, "source", "base.obj")
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
    """Static two-bone rest pose. Hands stay apart and grip a shared handle."""
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


def wrinkle_delta(a, mag, offset):
    d = mag * offset * (0.40 * math.sin(3.1 * a + 0.35) + 0.16 * math.sin(6.7 * a + 1.1))
    for ang, width, depth in ((-1.15, 0.38, 0.006), (0.55, 0.32, 0.005), (2.35, 0.34, 0.005)):
        da = abs(math.atan2(math.sin(a - ang), math.cos(a - ang)))
        d -= depth * math.exp(-((da / width) ** 2))
    return d


def slice_hull(verts, indices, z, slop, min_pts=8):
    use = slop
    pts = []
    for _ in range(4):
        pts = [(verts[i][0], verts[i][1]) for i in indices if abs(verts[i][2] - z) <= use]
        if len(pts) >= min_pts:
            break
        use *= 1.6
    hull = convex_hull(pts)
    if len(hull) < 3:
        # fallback: circle from whatever we have
        if not pts:
            return [(0.08 * math.cos(2 * math.pi * i / 8), 0.07 * math.sin(2 * math.pi * i / 8)) for i in range(8)]
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        r = max(math.hypot(p[0] - cx, p[1] - cy) for p in pts)
        r = max(r, 0.04)
        return [(cx + r * math.cos(2 * math.pi * i / 10), cy + r * math.sin(2 * math.pi * i / 10)) for i in range(10)]
    return hull


def ring_from_hull(hull, offset, n, wrinkle_mag, z, zhang_scale):
    smp = resample_closed(hull, n)
    cx = sum(p[0] for p in smp) / float(n)
    cy = sum(p[1] for p in smp) / float(n)
    row = []
    for x, y in smp:
        dx, dy = x - cx, y - cy
        L = math.hypot(dx, dy)
        if L < 1e-8:
            dx, dy, L = 1.0, 0.0, 0.04
        a = math.atan2(dy, dx)
        r = L + offset + wrinkle_delta(a, wrinkle_mag, offset)
        r = max(r, L + offset * 0.65)
        hang = max(0.0, (L + offset) - r) * 0.4 * zhang_scale
        nx, ny = dx / L, dy / L
        row.append(V(cx + nx * r, cy + ny * r, z - hang))
    return row


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


def basis_from_dir(d):
    d = d.nrm()
    aux = V(0, 0, 1) if abs(d.z) < 0.9 else V(1, 0, 0)
    x = d.cross(aux)
    if x.length() < 1e-8:
        x = V(0, 1, 0)
    x = x.nrm()
    y = d.cross(x).nrm()
    return x, y


def quad_box(cx, cy, cz, sx, sy, sz):
    hx, hy, hz = sx * 0.5, sy * 0.5, sz * 0.5
    v = [
        (cx - hx, cy - hy, cz - hz),
        (cx + hx, cy - hy, cz - hz),
        (cx + hx, cy + hy, cz - hz),
        (cx - hx, cy + hy, cz - hz),
        (cx - hx, cy - hy, cz + hz),
        (cx + hx, cy - hy, cz + hz),
        (cx + hx, cy + hy, cz + hz),
        (cx - hx, cy + hy, cz + hz),
    ]
    f = [
        (0, 1, 2, 3),
        (4, 7, 6, 5),
        (0, 4, 5, 1),
        (1, 5, 6, 2),
        (2, 6, 7, 3),
        (3, 7, 4, 0),
    ]
    return v, f


def shift_faces(faces, off):
    return [tuple(i + off for i in face) for face in faces]


def nearest_dist(src, dst):
    if not src or not dst:
        return None
    inv = 18.0
    grid = collections.defaultdict(list)
    for p in dst:
        grid[(int(p[0] * inv), int(p[1] * inv), int(p[2] * inv))].append(p)
    best = 1e9
    hits = 0
    inside = 0
    for p in src:
        key = (int(p[0] * inv), int(p[1] * inv), int(p[2] * inv))
        cand = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    cand.extend(grid[(key[0] + dx, key[1] + dy, key[2] + dz)])
        if not cand:
            cand = dst
            # subsample if huge
            if len(cand) > 2500:
                cand = cand[:: max(1, len(cand) // 2500)]
        md = 1e9
        for q in cand:
            d = (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 + (p[2] - q[2]) ** 2
            if d < md:
                md = d
        md = math.sqrt(md)
        if md < best:
            best = md
        if md < 0.006:
            hits += 1
        pr = math.hypot(p[0], p[1])
        # crude inside: closer to origin than nearest body in-band
        if md < 0.04 and pr + 0.004 < math.hypot(cand[0][0], cand[0][1]) and pr < 0.12:
            inside += 1
    return {"min_m": round(best, 5), "verts_closer_than_6mm": hits, "src_n": len(src)}


def point_in_hull(pt, hull):
    if len(hull) < 3:
        return False
    x, y = pt[0], pt[1]
    inside = False
    j = len(hull) - 1
    for i, (xi, yi) in enumerate(hull):
        xj, yj = hull[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / ((yj - yi) + 1e-16) + xi):
            inside = not inside
        j = i
    return inside


def body_inside_count(cloth, posed, parts, zslop=0.035):
    """Cloth verts that fall inside a body slice hull (true intersections)."""
    idx = parts["torso"] + parts["neck"] + parts["foot"] + parts["head"]
    n = 0
    worst = 0.0
    for p in cloth:
        if p[2] > 1.47:
            continue
        hull = slice_hull(posed, idx, p[2], zslop, min_pts=6)
        if len(hull) < 3:
            continue
        if point_in_hull(p, hull):
            n += 1
            md = 1e9
            for i, a in enumerate(hull):
                b = hull[(i + 1) % len(hull)]
                ax, ay = p[0] - a[0], p[1] - a[1]
                bx, by = b[0] - a[0], b[1] - a[1]
                t = max(0.0, min(1.0, (ax * bx + ay * by) / (bx * bx + by * by + 1e-12)))
                d = math.hypot(ax - bx * t, ay - by * t)
                if d < md:
                    md = d
            if md > worst:
                worst = md
    return {"intersecting_verts": n, "worst_penetration_m": round(worst, 5)}


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
    """T-pose membership vs original bones. Used after pose for coverage."""
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


def bone_radius(verts, idxs, a, b):
    if not idxs:
        return 0.05
    return max(dist_seg(V(verts[i]), a, b)[0] for i in idxs)


def lerp_v(a, b, t):
    return a + (b - a) * t


def tube_stations(sh, el, ha, r_sh, r_el, r_ha):
    """Shoulder → elbow → wrist stations. Radius must exceed posed arm radius."""
    st = []
    nu, nf = SLEEVE_UPPER_ROWS, SLEEVE_FORE_ROWS
    for i in range(nu):
        t = i / float(nu - 1) if nu > 1 else 0.0
        st.append((lerp_v(sh, el, t), r_sh + (r_el - r_sh) * t, (el - sh).nrm()))
    for i in range(1, nf):
        t = i / float(nf - 1) if nf > 1 else 1.0
        st.append((lerp_v(el, ha, t), r_el + (r_ha - r_el) * t, (ha - el).nrm()))
    return st


def build_arm_sleeve(sh, el, ha, r_upper, r_fore, robe_shoulder_row, sign):
    """Sleeve CHANNEL follows the posed arm. Hands leave only at the cuff."""
    ease_u = 0.048
    ease_f = 0.055
    r_sh = r_upper + ease_u
    r_el = max(r_upper, r_fore) + ease_f
    r_ha = r_fore + 0.040
    stations = tube_stations(sh, el, ha, r_sh, r_el, r_ha)
    # snap first ring toward robe shoulder so the channel joins the robe body
    side = [v for v in robe_shoulder_row if v.x * sign > 0.04]
    if side:
        cx = sum(v.x for v in side) / len(side)
        cy = sum(v.y for v in side) / len(side)
        cz = sum(v.z for v in side) / len(side)
        # mix 40% robe shoulder into ring 0 origin so it sits on the robe, not in empty space
        o0, r0, ax0 = stations[0]
        mix = V(cx, cy, cz) * 0.4 + o0 * 0.6
        stations[0] = (mix, r_sh, ax0)
    verts = []
    radii = []
    for origin, radius, axis in stations:
        bx, by = basis_from_dir(axis)
        radii.append(radius)
        for j in range(SLEEVE_COLS):
            a = 2.0 * math.pi * j / SLEEVE_COLS
            fold = 1.0 + 0.06 * math.sin(3.0 * a + 0.4 * sign)
            p = origin + bx * (math.cos(a) * radius * fold) + by * (math.sin(a) * radius * fold)
            verts.append(p.xyz())
    faces = grid_faces(len(stations), SLEEVE_COLS, True)
    return {
        "verts": verts,
        "faces": faces,
        "stations": [(o.xyz(), r) for o, r, _ in stations],
        "r_sh": r_sh,
        "r_el": r_el,
        "r_ha": r_ha,
    }


def sleeve_covers(posed, idxs, sh, el, ha, r_a, r_b, which):
    """Body vert is inside the sleeve tube iff dist(axis) < radius(t) - 2mm."""
    uncovered = 0
    worst = 0.0
    n = 0
    for i in idxs:
        p = V(posed[i])
        if which == "upper":
            d, t = dist_seg(p, sh, el)
            r = r_a + (r_b - r_a) * t
        else:
            d, t = dist_seg(p, el, ha)
            r = r_a + (r_b - r_a) * t
        n += 1
        slack = r - d
        if slack < 0.002:
            uncovered += 1
            if -slack > worst:
                worst = -slack
    frac = 1.0 if n == 0 else (n - uncovered) / float(n)
    return {
        "n": n,
        "uncovered": uncovered,
        "covered_frac": round(frac, 4),
        "covers": uncovered == 0,
        "worst_outside_m": round(worst, 5),
    }


def stitch_gap(sleeve, torso_row, sign):
    sv = sleeve["verts"][:SLEEVE_COLS]
    tv = [v.xyz() for v in torso_row if v.x * sign > 0.0]
    return nearest_dist(sv, tv)


def build_torso_robe(posed, parts):
    rows = []
    meta = []
    for z, name, off, wr in TORSO_Z:
        if name == "neck":
            idx = parts["neck"] or parts["head"]
            slop = 0.025
        elif name in ("collar",):
            idx = parts["neck"] + parts["torso"]
            slop = 0.03
        else:
            idx = parts["torso"] + parts["foot"]
            slop = 0.04
        hull = slice_hull(posed, idx, z, slop)
        mag = 0.35 if wr else 0.08
        hang = 0.008 if wr else 0.002
        row = ring_from_hull(hull, off, COLS, mag, z, hang)
        rows.append(row)
        rs = [math.hypot(v.x, v.y) for v in row]
        meta.append({"z": z, "name": name, "offset": off, "r_mean": round(sum(rs) / len(rs), 4), "r_min": round(min(rs), 4), "r_max": round(max(rs), 4)})
    verts = [v.xyz() for row in rows for v in row]
    faces = grid_faces(len(rows), COLS, True)
    return {"verts": verts, "faces": faces, "rows": rows, "meta": meta}


def offset_row(row, extra):
    cx = sum(v.x for v in row) / len(row)
    cy = sum(v.y for v in row) / len(row)
    out = []
    for v in row:
        dx, dy = v.x - cx, v.y - cy
        L = math.hypot(dx, dy) or 1e-6
        out.append(V(cx + dx / L * (L + extra), cy + dy / L * (L + extra), v.z))
    return out


def build_collar(robe_rows):
    """Cyan collar sits on the robe neck/collar rings, not through the body."""
    inner = offset_row(robe_rows[0], 0.010)
    outer = offset_row(robe_rows[1], 0.012)
    verts = []
    for row in (inner, outer):
        for v in row:
            a = math.atan2(v.y, v.x)
            front = math.exp(-((a + math.pi / 2) / 0.65) ** 2)
            verts.append((v.x, v.y - 0.004 * front, v.z - 0.018 * front))
    faces = grid_faces(2, COLS, True)
    return {"verts": verts, "faces": faces}


def build_sash(robe_rows):
    """Sash sits outside the robe waist. Tassel hangs in front, not through the robe."""
    waist = robe_rows[6]
    hip = robe_rows[7]
    top = offset_row(waist, 0.012)
    mid = offset_row(waist, 0.014)
    bot = offset_row(hip, 0.012)
    top = [V(v.x, v.y, v.z + 0.018) for v in top]
    bot = [V(v.x, v.y, v.z - 0.01) for v in bot]
    verts = [p.xyz() for p in top + mid + bot]
    faces = grid_faces(3, COLS, True)
    fi = min(range(COLS), key=lambda j: mid[j].y)
    fx, fy, fz = mid[fi].xyz()
    # tassel in -Y (in front of robe), short, not a through-slab
    tv, tf = quad_box(fx, fy - 0.028, fz - 0.05, 0.022, 0.010, 0.08)
    verts.extend(tv)
    faces.extend(shift_faces(tf, COLS * 3))
    return {"verts": verts, "faces": faces}


def build_shoes(posed, parts, sign):
    idx = [i for i in parts["foot"] if posed[i][0] * sign > 0.02]
    if not idx:
        idx = [i for i in parts["foot"] if posed[i][0] * sign >= 0.0]
    pts = [posed[i] for i in idx]
    toe_y = min(p[1] for p in pts)
    # include a point in front of every toe so the hull encloses them
    extra = [(p[0], toe_y - 0.016) for p in pts if p[1] < toe_y + 0.02]
    lo_pts = [(p[0], p[1]) for p in pts if p[2] < 0.03] + extra
    hi_pts = [(p[0], p[1]) for p in pts if p[2] > 0.04] + extra
    lo = convex_hull(lo_pts) or lo_pts[:3]
    hi = convex_hull(hi_pts) or hi_pts[:3]
    r0 = ring_from_hull(lo, 0.014, 12, 0.0, 0.004, 0.0)
    r1 = ring_from_hull(lo, 0.016, 12, 0.0, 0.040, 0.0)
    r2 = ring_from_hull(hi, 0.014, 12, 0.0, 0.088, 0.0)
    verts = [v.xyz() for v in r0 + r1 + r2]
    faces = grid_faces(3, 12, True)
    return {"verts": verts, "faces": faces, "toe_y": toe_y}


def build_guan(posed, parts):
    """Cap on the crown. Front board above the brow. Face stays visible."""
    head = [posed[i] for i in parts["head"]]
    crown_z = max(p[2] for p in head)
    scalp_idx = [i for i in parts["head"] if posed[i][2] >= 1.70]
    hull = slice_hull(posed, scalp_idx or parts["head"], 1.72, 0.04)
    cap0 = ring_from_hull(hull, 0.010, 16, 0.02, 1.705, 0.0)
    cap1 = ring_from_hull(hull, 0.014, 16, 0.02, crown_z + 0.008, 0.0)
    cap2 = [(v.x * 0.40, v.y * 0.40, crown_z + 0.018) for v in cap1]
    verts = [v.xyz() for v in cap0 + cap1] + cap2
    faces = grid_faces(3, 16, True)
    brow_band = [p for p in posed if 1.665 <= p[2] <= 1.70 and abs(p[0]) < 0.07]
    brow_y = min(p[1] for p in brow_band) if brow_band else -0.02
    z0, z1 = GUAN_MIN_Z, crown_z + 0.012
    cz = 0.5 * (z0 + z1)
    board_v, board_f = quad_box(0.0, brow_y - 0.012, cz, 0.10, 0.016, z1 - z0)
    verts.extend(board_v)
    faces.extend(shift_faces(board_f, 16 * 3))
    return {
        "verts": verts,
        "faces": faces,
        "crown_z": crown_z,
        "brow_y": brow_y,
        "board_z_min": z0,
        "board_z_max": z1,
    }


def build_beard(posed, parts):
    """Volume attached to actual chin verts — not a floating triangle."""
    chins = [posed[i] for i in parts["chin"] if posed[i][1] < 0.01]
    if len(chins) < 4:
        chins = [p for p in posed if 1.52 < p[2] < 1.57 and p[1] < 0.01 and abs(p[0]) < 0.05]
    chins = sorted(chins, key=lambda p: p[0])
    # 8 samples across chin x
    xs = [chins[int(round(k * (len(chins) - 1) / 7.0))] for k in range(8)]
    y0 = min(p[1] for p in xs)
    z0 = sum(p[2] for p in xs) / 8.0
    rows_front = []
    rows_back = []
    for t, dz, dy, wscale in (
        (0.0, 0.000, 0.000, 1.00),
        (0.25, -0.035, -0.012, 0.95),
        (0.55, -0.080, -0.018, 0.80),
        (0.85, -0.125, -0.014, 0.55),
        (1.00, -0.155, -0.008, 0.22),
    ):
        rf, rb = [], []
        half = 0.028 * wscale
        thick = 0.016 * (1.0 - 0.4 * t)
        for j in range(8):
            x = xs[j][0] * (0.55 + 0.45 * wscale)
            # row 0 uses the real chin sample
            if t == 0.0:
                x, y, z = xs[j]
                rf.append((x, y - 0.003, z))
                rb.append((x, y + 0.010, z))
            else:
                rf.append((x, y0 + dy, z0 + dz))
                rb.append((x, y0 + dy + thick, z0 + dz))
            _ = half
        rows_front.append(rf)
        rows_back.append(rb)
    verts = [p for row in rows_front for p in row] + [p for row in rows_back for p in row]
    faces = grid_faces(5, 8, False)
    faces += shift_faces(grid_faces(5, 8, False), 5 * 8)
    # side stitches
    for i in range(4):
        for s in (0, 7):
            a = i * 8 + s
            b = (i + 1) * 8 + s
            c = 40 + (i + 1) * 8 + s
            d = 40 + i * 8 + s
            faces.append((a, b, c, d))
    return {"verts": verts, "faces": faces, "chin_z": z0, "chin_y": y0}


def build_fan(ha_l, ha_r):
    """Handle between the two hands. Thick vanes, not a paper card. Below the face."""
    hx = 0.5 * (ha_l.x + ha_r.x)
    hy = 0.5 * (ha_l.y + ha_r.y) - 0.012
    hz = 0.5 * (ha_l.z + ha_r.z)
    span = abs(ha_l.x - ha_r.x) + 0.04
    hv, hf = quad_box(hx, hy, hz, max(span, 0.16), 0.018, 0.018)
    verts = list(hv)
    faces = list(hf)
    c = V(hx, hy - 0.01, hz + 0.02)
    n_vanes = 9
    for i in range(n_vanes):
        t = i / float(n_vanes - 1) - 0.5
        ang = t * 0.95
        length = 0.20
        dx = math.sin(ang) * length
        dz = math.cos(ang) * length * 0.85
        dy = -0.03 - 0.02 * math.cos(ang)
        a = c + V(dx * 0.12, -0.004, dz * 0.12)
        b = c + V(dx, dy, dz)
        w = V(-math.cos(ang), 0.0, math.sin(ang)) * 0.016
        nrm = V(0.0, 0.008, 0.0)
        base = len(verts)
        verts.extend(
            [
                (a.x + w.x, a.y + nrm.y, a.z + w.z),
                (a.x - w.x, a.y + nrm.y, a.z - w.z),
                (b.x - w.x, b.y + nrm.y, b.z - w.z),
                (b.x + w.x, b.y + nrm.y, b.z + w.z),
                (a.x + w.x, a.y - nrm.y, a.z + w.z),
                (a.x - w.x, a.y - nrm.y, a.z - w.z),
                (b.x - w.x, b.y - nrm.y, b.z - w.z),
                (b.x + w.x, b.y - nrm.y, b.z + w.z),
            ]
        )
        faces.extend(
            [
                (base, base + 1, base + 2, base + 3),
                (base + 4, base + 7, base + 6, base + 5),
                (base, base + 3, base + 7, base + 4),
                (base + 1, base + 5, base + 6, base + 2),
            ]
        )
    return {"verts": verts, "faces": faces, "center": c.xyz(), "handle": (hx, hy, hz)}


def mesh_bbox(meshes):
    xs, ys, zs = [], [], []
    for m in meshes:
        for p in m["verts"]:
            xs.append(p[0]); ys.append(p[1]); zs.append(p[2])
    return {"min": [min(xs), min(ys), min(zs)], "max": [max(xs), max(ys), max(zs)]}


def finite_mesh(m):
    for p in m["verts"]:
        if not all(map(math.isfinite, p)):
            return False
    for f in m["faces"]:
        if min(f) < 0 or max(f) >= len(m["verts"]):
            return False
    return True


def tri_count(m):
    n = 0
    for f in m["faces"]:
        n += max(0, len(f) - 2)
    return n


def cloth_in_robe(cloth_verts, robe_rows):
    """Punch-through vs the local robe sample (not mean radius — that false-flags ovals)."""
    n = 0
    worst = 0.0
    for p in cloth_verts:
        best_i = min(range(len(robe_rows)), key=lambda i: abs(robe_rows[i][0].z - p[2]))
        row = robe_rows[best_i]
        rv = min(row, key=lambda v: (p[0] - v.x) ** 2 + (p[1] - v.y) ** 2)
        cx = sum(v.x for v in row) / len(row)
        cy = sum(v.y for v in row) / len(row)
        pr = math.hypot(p[0] - cx, p[1] - cy)
        rr = math.hypot(rv.x - cx, rv.y - cy)
        if rr > 1e-6 and pr < rr - 0.006:
            n += 1
            pen = rr - 0.006 - pr
            if pen > worst:
                worst = pen
    return {"punch_through_verts": n, "worst_m": round(worst, 5), "ok": n == 0}


def guan_face_vis(guan, posed, parts):
    hits = [
        v
        for v in guan["verts"]
        if FACE_Z_MOUTH <= v[2] <= FACE_Z_EYE_TOP and v[1] < 0.02
    ]
    gmin = min(v[2] for v in guan["verts"])
    gmax = max(v[2] for v in guan["verts"])
    scalp = [posed[i] for i in parts["head"] if posed[i][2] >= 1.72]
    scalp_z = max(p[2] for p in scalp) if scalp else 1.78
    return {
        "face_z_clear": [FACE_Z_MOUTH, FACE_Z_EYE_TOP],
        "guan_z_min": round(gmin, 5),
        "guan_z_max": round(gmax, 5),
        "guan_min_z_bar": GUAN_MIN_Z,
        "guan_verts_in_face_front": len(hits),
        "eyes_nose_mouth_clear": len(hits) == 0 and gmin >= GUAN_MIN_Z - 0.002,
        "covers_scalp": gmax >= scalp_z - 0.005,
        "board_z_min": round(guan.get("board_z_min", gmin), 5),
        "crown_z": round(guan.get("crown_z", scalp_z), 5),
    }


def hand_separation(posed, left_idx, right_idx):
    if not left_idx or not right_idx:
        return {"min_m": None, "ok": False}
    best = 1e9
    for i in left_idx:
        li = posed[i]
        for j in right_idx:
            rj = posed[j]
            d = (li[0] - rj[0]) ** 2 + (li[1] - rj[1]) ** 2 + (li[2] - rj[2]) ** 2
            if d < best:
                best = d
    m = math.sqrt(best)
    return {"min_m": round(m, 5), "ok": m >= 0.02}


def shoe_enclosure(posed, foot_idx, shoe, sign):
    feet = [posed[i] for i in foot_idx if posed[i][0] * sign > 0.02]
    if not feet:
        return {"ok": False, "toe_verts_outside_y": None}
    shoe_y_min = min(v[1] for v in shoe["verts"])
    toes = [p for p in feet if p[1] <= min(q[1] for q in feet) + 0.012]
    outside = [p for p in toes if p[1] < shoe_y_min + 0.002]
    # XY hull of shoe at sole
    hull = convex_hull([(v[0], v[1]) for v in shoe["verts"] if v[2] < 0.05])
    xy_out = [p for p in toes if hull and not point_in_hull(p, hull)]
    return {
        "toe_n": len(toes),
        "toe_y_min": round(min(p[1] for p in toes), 5),
        "shoe_y_min": round(shoe_y_min, 5),
        "toes_in_front_of_shoe": len(outside),
        "toes_outside_xy_hull": len(xy_out),
        "ok": len(outside) == 0 and len(xy_out) == 0,
    }


def beard_on_chin(beard, posed, parts):
    chins = [posed[i] for i in parts["chin"] if posed[i][1] < 0.01]
    if not chins or not beard["verts"]:
        return {"ok": False}
    top = beard["verts"][:8]
    md = 1e9
    for t in top:
        for c in chins:
            d = (t[0] - c[0]) ** 2 + (t[1] - c[1]) ** 2 + (t[2] - c[2]) ** 2
            if d < md:
                md = d
    m = math.sqrt(md)
    return {"top_to_chin_min_m": round(m, 5), "ok": m <= 0.012, "volume_verts": len(beard["verts"])}


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
    posed, elL, haL, poseL = skin_arm(tpose, Lsh, Lel, Lha, +1)
    posed, elR, haR, poseR = skin_arm(posed, Rsh, Rel, Rha, -1)
    parts = classify_indices(tpose)
    rU_L = bone_radius(posed, armL["upper"], Lsh, elL)
    rF_L = bone_radius(posed, armL["fore"], elL, haL)
    rU_R = bone_radius(posed, armR["upper"], Rsh, elR)
    rF_R = bone_radius(posed, armR["fore"], elR, haR)
    robe = build_torso_robe(posed, parts)
    sl = build_arm_sleeve(Lsh, elL, haL, rU_L, rF_L, robe["rows"][2], +1)
    sr = build_arm_sleeve(Rsh, elR, haR, rU_R, rF_R, robe["rows"][2], -1)
    collar = build_collar(robe["rows"])
    sash = build_sash(robe["rows"])
    shoe_l = build_shoes(posed, parts, +1)
    shoe_r = build_shoes(posed, parts, -1)
    guan = build_guan(posed, parts)
    beard = build_beard(posed, parts)
    fan = build_fan(haL, haR)
    meshes = {
        "body": {"verts": posed, "faces": checks["male_body"]["faces"], "uvs": checks["male_body"]["uvs"], "uv_loops": checks["male_body"]["uv_loops"]},
        "robe_outer": robe,
        "sleeve_l": sl,
        "sleeve_r": sr,
        "collar": collar,
        "sash": sash,
        "shoe_l": shoe_l,
        "shoe_r": shoe_r,
        "guan": guan,
        "beard": beard,
        "fan": fan,
    }
    for name, m in meshes.items():
        if not finite_mesh(m):
            raise RuntimeError("non-finite or bad indices in %s" % name)
    cov_u_l = sleeve_covers(posed, armL["upper"], Lsh, elL, haL, sl["r_sh"], sl["r_el"], "upper")
    cov_f_l = sleeve_covers(posed, armL["fore"], Lsh, elL, haL, sl["r_el"], sl["r_ha"], "fore")
    cov_u_r = sleeve_covers(posed, armR["upper"], Rsh, elR, haR, sr["r_sh"], sr["r_el"], "upper")
    cov_f_r = sleeve_covers(posed, armR["fore"], Rsh, elR, haR, sr["r_el"], sr["r_ha"], "fore")
    vis = guan_face_vis(guan, posed, parts)
    hands = hand_separation(posed, armL["hand"], armR["hand"])
    sh_l = shoe_enclosure(posed, parts["foot"], shoe_l, +1)
    sh_r = shoe_enclosure(posed, parts["foot"], shoe_r, -1)
    fan_max_z = max(p[2] for p in fan["verts"])
    structure = {
        "face_vis": vis,
        "sleeves_cover_upper_arm": cov_u_l["covers"] and cov_u_r["covers"],
        "sleeves_cover_forearm": cov_f_l["covers"] and cov_f_r["covers"],
        "sleeve_upper_L": cov_u_l,
        "sleeve_fore_L": cov_f_l,
        "sleeve_upper_R": cov_u_r,
        "sleeve_fore_R": cov_f_r,
        "sleeve_join_L": stitch_gap(sl, robe["rows"][2], +1),
        "sleeve_join_R": stitch_gap(sr, robe["rows"][2], -1),
        "hand_separation": hands,
        "shoe_L": sh_l,
        "shoe_R": sh_r,
        "collar_on_robe": cloth_in_robe(collar["verts"], robe["rows"]),
        "sash_on_robe": cloth_in_robe(sash["verts"], robe["rows"]),
        "beard_chin": beard_on_chin(beard, posed, parts),
        "fan_max_z": round(fan_max_z, 5),
        "fan_below_face": fan_max_z < FACE_Z_MOUTH - 0.04,
        "fan_vane_n": 9,
        "posed_arm_radius_m": {"L_upper": round(rU_L, 5), "L_fore": round(rF_L, 5), "R_upper": round(rU_R, 5), "R_fore": round(rF_R, 5)},
    }
    bb = mesh_bbox(meshes.values())
    census = {
        name: {"verts": len(m["verts"]), "faces": len(m["faces"]), "tris": tri_count(m)}
        for name, m in meshes.items()
    }
    return {
        "checks": checks,
        "meshes": meshes,
        "structure": structure,
        "bbox": bb,
        "census": census,
        "pose": {"left": poseL, "right": poseR, "hand_l": haL.xyz(), "hand_r": haR.xyz()},
        "parts_n": {k: len(v) for k, v in parts.items()},
        "support_faces": checks["compat"]["remaining_faces"],
        "support_uvs": checks["compat"]["remaining_uvs"],
        "robe_meta": robe["meta"],
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
    for key, val in (("Roughness", rough),):
        s = bsdf.inputs.get(key)
        if s is not None:
            s.default_value = val
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


def write_report(output_dir, built, execution_kind, status, blender_present, blender_version, outputs, glb_bytes=None):
    os.makedirs(output_dir, exist_ok=True)
    refuse_frozen_writes(output_dir)
    bb = built["bbox"]
    report = {
        "task_id": TASK_ID,
        "title": "Structural fix of Mac 629035d front fail (not art PASS)",
        "status": status,
        "execution_kind": execution_kind,
        "not_a_zhuge_product": True,
        "g1_g5_claimed": False,
        "art_approval": False,
        "fusion_pass": False,
        "palace_mesh": False,
        "armature": False,
        "can_walk": False,
        "declaration": "Static clothed mesh. Clothes and body are separate objects. No armature. Do not claim walk or fusion PASS.",
        "mac_fail_seen": {
            "commit": MAC_FAIL_COMMIT,
            "blender": "5.2.1",
            "exit": 0,
            "pixel": "ct-costume-01-mac-front-fail.png",
            "visible": "guan board on face; bare shoulders; arms punch sleeve sides; hands fused; paper fan; floating triangle beard; barrel robe + sash slab; toes out of shoes",
        },
        "method": {
            "used": "posed-arm tube sleeves (shoulder→elbow→wrist) + body-hull robe; guan from crown/brow; not empty-robe cones",
            "empty_robe_generators": False,
            "support_body": MAC_SUPPORT_BODY,
            "pose": "static two-bone rest pose (not a rig); hands apart on fan handle",
        },
        "support_body_faces": built["support_faces"],
        "support_body_uvs": built["support_uvs"],
        "census": built["census"],
        "pose": built["pose"],
        "structure": built["structure"],
        "robe_rings": built["robe_meta"],
        "bbox": {"min": [round(c, 6) for c in bb["min"]], "max": [round(c, 6) for c in bb["max"]]},
        "height_m": round(bb["max"][2] - bb["min"][2], 6),
        "glb_export": {"rootName": ROOT_NAME, "yup": True, "bytes": glb_bytes if glb_bytes is not None else B.UNKNOWN},
        "blender_present": blender_present,
        "blender_version_actual": blender_version,
        "outputs": outputs,
        "unverified_until_mac_blender": [
            "Mac front vs 629035d fail still: guan off the face, sleeves covering upper arm/forearm, hands apart on fan",
            "Y-up GLB import, feet on z=0 after exporter",
            "pixel G1–G5 (not claimed)",
            "armpit crease from static fold",
        ],
    }
    B.write_json(B.safe_join(output_dir, "clothed_report.json"), report)
    return report


def blender_export(args, built):
    B.clear_scene()
    scene = B.bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    world = B.bpy.data.worlds.new("ClothedWorld")
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
        "robe": make_mat("M_Robe", (0.86, 0.83, 0.74), 0.72, 0.12),
        "cyan": make_mat("M_Cyan", (0.22, 0.42, 0.44), 0.55, 0.16),
        "hair": make_mat("M_Hair", (0.12, 0.08, 0.06), 0.78, 0.08),
        "fan": make_mat("M_Fan", (0.90, 0.88, 0.80), 0.48, 0.20),
        "grey": B.make_grey(),
    }
    ms = built["meshes"]
    body_pack = {
        "faces": ms["body"]["faces"],
        "uvs": ms["body"]["uvs"],
        "uv_loops": ms["body"]["uv_loops"],
    }
    B.build_mesh_object(ms["body"]["verts"], body_pack, root, mats["skin"])
    add_mesh("Robe_Outer", ms["robe_outer"], mats["robe"], root)
    add_mesh("Robe_Sleeve_L", ms["sleeve_l"], mats["robe"], root)
    add_mesh("Robe_Sleeve_R", ms["sleeve_r"], mats["robe"], root)
    add_mesh("Collar_Inner", ms["collar"], mats["cyan"], root)
    add_mesh("Sash", ms["sash"], mats["cyan"], root)
    add_mesh("Shoe_L", ms["shoe_l"], mats["cyan"], root)
    add_mesh("Shoe_R", ms["shoe_r"], mats["cyan"], root)
    add_mesh("Guan", ms["guan"], mats["cyan"], root)
    add_mesh("Beard", ms["beard"], mats["hair"], root)
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

    cams = B.setup_cameras(built["bbox"])
    os.makedirs(args.output_dir, exist_ok=True)
    refuse_frozen_writes(args.output_dir)
    blend_name = "zhuge_clothed_v1.blend"
    glb_name = "zhuge_clothed_v1.glb"
    B.bpy.ops.wm.save_as_mainfile(
        **B.filter_op_kwargs(
            B.bpy.ops.wm.save_as_mainfile,
            {"filepath": B.safe_join(args.output_dir, blend_name), "check_existing": False},
        )
    )
    B.export_glb(B.safe_join(args.output_dir, glb_name), root_name=ROOT_NAME)
    glb_path = B.safe_join(args.output_dir, glb_name)
    glb_bytes = os.path.getsize(glb_path) if os.path.isfile(glb_path) else None
    renders = B.render_views(cams, args.output_dir, args.skip_render)
    clay = []
    if not args.skip_render:
        for obj in list(B.bpy.data.objects):
            if obj.type == "MESH" and obj.data.materials:
                obj.data.materials[0] = mats["grey"]
        mapping = (
            ("Cam_Front", "clay_front.png"),
            ("Cam_Side", "clay_side.png"),
            ("Cam_Back", "clay_back.png"),
            ("Cam_LookDown", "clay_lookdown.png"),
        )
        scene = B.bpy.context.scene
        for cam_name, fname in mapping:
            scene.camera = cams[cam_name]
            fp = B.safe_join(args.output_dir, fname)
            scene.render.filepath = fp
            B.bpy.ops.render.render(write_still=True)
            clay.append(fname)
    outputs = [blend_name, glb_name] + renders + clay
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
    print("exported clothed candidate to", args.output_dir)


def main():
    args = parse_cli()
    built = build_all(args.source_obj)
    s = built["structure"]
    print(
        "checks support_faces=%s upper=%s fore=%s hands=%s guan_face_hits=%s shoes=%s"
        % (
            built["support_faces"],
            s["sleeves_cover_upper_arm"],
            s["sleeves_cover_forearm"],
            s["hand_separation"]["min_m"],
            s["face_vis"]["guan_verts_in_face_front"],
            s["shoe_L"]["ok"] and s["shoe_R"]["ok"],
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
            outputs=[],
        )
        print("clothed UNRUN tris=%s" % sum(c["tris"] for c in built["census"].values()))
        return 0
    blender_export(args, built)
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
