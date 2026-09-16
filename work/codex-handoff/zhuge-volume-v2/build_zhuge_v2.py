#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CT-3D-02  诸葛亮真实三维人物 v2
Parameterized self-made meshes (profiles / Bezier / loft / sweep).
Not a UV-sphere / cone kitbash. Static posed volume — no armature, cannot walk.

Run inside Blender 5.2.1:
  blender -b -P build_zhuge_v2.py -- --output-dir /path

This script never deletes files outside --output-dir.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from datetime import datetime, timezone

try:
    import bpy  # type: ignore
except ImportError:
    bpy = None


# ---------------------------------------------------------------------------
# Identity / proportions (meters, Blender Z-up)
# ---------------------------------------------------------------------------
TASK_ID = "CT-3D-02"
HEIGHT = 1.80
HEADS = 7.35
HEAD_H = HEIGHT / HEADS  # ~0.245 m
CROWN_Z = HEIGHT
CHIN_Z = HEIGHT - HEAD_H
EYE_Z = CHIN_Z + HEAD_H * 0.54
BROW_Z = EYE_Z + 0.028
NOSE_TIP_Z = CHIN_Z + HEAD_H * 0.32
MOUTH_Z = CHIN_Z + HEAD_H * 0.22
NECK_TOP_Z = CHIN_Z - 0.012
SHOULDER_Z = 1.385
CHEST_Z = 1.22
WAIST_Z = 0.97
HIP_Z = 0.88
HEM_Z = 0.038
FOOT_Z = 0.0
SHOULDER_W = 0.235  # visual robe half-width; sleeve ROOT sits on the torso (~0.148), not out here
CHEST_RX, CHEST_RY = 0.205, 0.155
WAIST_RX, WAIST_RY = 0.175, 0.130
BODY_N = 40  # shared longitude count for robe body + skirt (waist transition)
FOLD_PHASE = 0.12
FOLD_COUNT = 8

# Face toward -Y (Blender front camera).
FACE_Y = -1.0

MATERIALS = (
    "M_Skin",
    "M_Hair",
    "M_RobeIvory",
    "M_CyanGreen",
    "M_Gold",
    "M_Feather",
    "M_Stone",
    "M_Wood",
)

MAT_COLORS = {
    "M_Skin": ((0.78, 0.60, 0.48, 1.0), 0.0, 0.48),
    "M_Hair": ((0.03, 0.025, 0.02, 1.0), 0.0, 0.82),
    "M_RobeIvory": ((0.90, 0.84, 0.72, 1.0), 0.0, 0.52),
    "M_CyanGreen": ((0.18, 0.42, 0.38, 1.0), 0.08, 0.34),
    "M_Gold": ((0.72, 0.52, 0.18, 1.0), 0.85, 0.22),
    "M_Feather": ((0.93, 0.93, 0.90, 1.0), 0.0, 0.28),
    "M_Stone": ((0.55, 0.50, 0.44, 1.0), 0.0, 0.72),
    "M_Wood": ((0.32, 0.20, 0.11, 1.0), 0.0, 0.55),
}


# ---------------------------------------------------------------------------
# CLI — --output-dir MUST work after Blender's `--`
# ---------------------------------------------------------------------------
def argv_after_dash():
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1 :]
    return sys.argv[1:]


def parse_cli():
    p = argparse.ArgumentParser(description="Build Zhuge Liang volume v2")
    p.add_argument(
        "--output-dir",
        default=None,
        help="Write GLB/blend/png/report only here. Never cleans other dirs.",
    )
    p.add_argument("--mesh-stats", action="store_true", help="Pure-python mesh census (no bpy)")
    p.add_argument("--skip-render", action="store_true")
    args, _unknown = p.parse_known_args(argv_after_dash())
    if not args.output_dir:
        args.output_dir = os.path.dirname(os.path.abspath(__file__))
    args.output_dir = os.path.abspath(args.output_dir)
    return args


def safe_join(output_dir, name):
    """Refuse any path that would escape the output directory."""
    output_dir = os.path.abspath(output_dir)
    if ".." in name.replace("\\", "/").split("/"):
        raise ValueError("refusing relative-parent filename: %s" % name)
    path = os.path.abspath(os.path.join(output_dir, name))
    try:
        common = os.path.commonpath([output_dir, path])
    except ValueError as exc:
        raise ValueError("output path escapes target dir") from exc
    if common != output_dir:
        raise ValueError("output path escapes target dir: %s" % path)
    return path


# ---------------------------------------------------------------------------
# Tiny vector / mesh kernel (stdlib only)
# ---------------------------------------------------------------------------
class V:
    __slots__ = ("x", "y", "z")

    def __init__(self, x, y=None, z=None):
        if y is None:
            if isinstance(x, V):
                self.x, self.y, self.z = x.x, x.y, x.z
            else:
                self.x, self.y, self.z = float(x[0]), float(x[1]), float(x[2])
        else:
            self.x, self.y, self.z = float(x), float(y), float(z)

    def __add__(self, o):
        return V(self.x + o.x, self.y + o.y, self.z + o.z)

    def __sub__(self, o):
        return V(self.x - o.x, self.y - o.y, self.z - o.z)

    def __mul__(self, s):
        return V(self.x * s, self.y * s, self.z * s)

    def __rmul__(self, s):
        return self.__mul__(s)

    def __truediv__(self, s):
        return V(self.x / s, self.y / s, self.z / s)

    def __neg__(self):
        return V(-self.x, -self.y, -self.z)

    def dot(self, o):
        return self.x * o.x + self.y * o.y + self.z * o.z

    def cross(self, o):
        return V(
            self.y * o.z - self.z * o.y,
            self.z * o.x - self.x * o.z,
            self.x * o.y - self.y * o.x,
        )

    def length(self):
        return math.sqrt(self.dot(self))

    def nrm(self, default=None):
        L = self.length()
        if L < 1e-12:
            return default if default is not None else V(0, 0, 1)
        return self / L

    def lerp(self, o, t):
        return self + (o - self) * t

    def xyz(self):
        return (self.x, self.y, self.z)

    def copy(self):
        return V(self.x, self.y, self.z)


def lerp(a, b, t):
    return a + (b - a) * t


def clamp(x, a, b):
    return a if x < a else b if x > b else x


def smoothstep(t):
    t = clamp(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def bezier(pts, n):
    """Sample an open polyline as cubic/quadratic/linear Bezier chain (groups of 4)."""
    if len(pts) == 2:
        return [pts[0].lerp(pts[1], i / n) for i in range(n + 1)]
    if len(pts) == 3:
        out = []
        for i in range(n + 1):
            t = i / n
            u = 1.0 - t
            out.append(pts[0] * (u * u) + pts[1] * (2 * u * t) + pts[2] * (t * t))
        return out
    # cubic
    if len(pts) == 4:
        out = []
        for i in range(n + 1):
            t = i / n
            u = 1.0 - t
            out.append(
                pts[0] * (u * u * u)
                + pts[1] * (3 * u * u * t)
                + pts[2] * (3 * u * t * t)
                + pts[3] * (t * t * t)
            )
        return out
    # chain of polyline samples
    out = []
    segs = len(pts) - 1
    for i in range(n + 1):
        t = i / n * segs
        k = min(int(t), segs - 1)
        f = t - k
        if not out or i == n:
            out.append(pts[k].lerp(pts[k + 1], f))
        else:
            out.append(pts[k].lerp(pts[k + 1], f))
    return out


def poly_bezier(ctrl, n_per):
    """ctrl is a list of V; sample Catmull-like cubic through points."""
    if len(ctrl) < 2:
        return list(ctrl)
    pts = []
    for i in range(len(ctrl) - 1):
        p0 = ctrl[i - 1] if i > 0 else ctrl[i]
        p1 = ctrl[i]
        p2 = ctrl[i + 1]
        p3 = ctrl[i + 2] if i + 2 < len(ctrl) else ctrl[i + 1]
        c1 = p1 + (p2 - p0) * 0.22
        c2 = p2 - (p3 - p1) * 0.22
        seg = bezier([p1, c1, c2, p2], n_per)
        if pts:
            seg = seg[1:]
        pts.extend(seg)
    return pts


def sample_polyline(pts, n):
    if n <= 1 or len(pts) < 2:
        return list(pts)
    lengths = [0.0]
    for i in range(1, len(pts)):
        lengths.append(lengths[-1] + (pts[i] - pts[i - 1]).length())
    total = lengths[-1] or 1.0
    out = []
    j = 0
    for i in range(n):
        d = total * i / (n - 1)
        while j + 1 < len(lengths) and lengths[j + 1] < d:
            j += 1
        if j + 1 >= len(pts):
            out.append(pts[-1])
            continue
        span = lengths[j + 1] - lengths[j]
        t = 0.0 if span < 1e-12 else (d - lengths[j]) / span
        out.append(pts[j].lerp(pts[j + 1], t))
    return out


def bishop_frames(path):
    """Rotation-minimizing frames along a polyline. Returns (T, N, B) per point."""
    n = len(path)
    T = [V(0, 0, 1)] * n
    for i in range(n):
        if i == 0:
            T[i] = (path[1] - path[0]).nrm()
        elif i == n - 1:
            T[i] = (path[i] - path[i - 1]).nrm()
        else:
            T[i] = (path[i + 1] - path[i - 1]).nrm()
    # pick a stable up
    up = V(0, 0, 1)
    if abs(T[0].dot(up)) > 0.9:
        up = V(0, 1, 0)
    N = [None] * n
    B = [None] * n
    N[0] = T[0].cross(up).cross(T[0]).nrm()
    B[0] = T[0].cross(N[0]).nrm()
    for i in range(1, n):
        v = path[i] - path[i - 1]
        vl2 = v.dot(v)
        if vl2 < 1e-16:
            N[i] = N[i - 1]
            B[i] = B[i - 1]
            continue
        ri_l = N[i - 1] - v * (2.0 * v.dot(N[i - 1]) / vl2)
        ti_l = T[i - 1] - v * (2.0 * v.dot(T[i - 1]) / vl2)
        v2 = T[i] - ti_l
        v2l2 = v2.dot(v2)
        if v2l2 < 1e-16:
            N[i] = ri_l.nrm()
        else:
            N[i] = (ri_l - v2 * (2.0 * v2.dot(ri_l) / v2l2)).nrm()
        B[i] = T[i].cross(N[i]).nrm()
    return T, N, B


class Mesh:
    def __init__(self, name, material, smooth=True):
        self.name = name
        self.material = material
        self.smooth = smooth
        self.verts = []  # list[V]
        self.faces = []  # list[tuple[int,...]]

    def add(self, v):
        self.verts.append(v if isinstance(v, V) else V(v))
        return len(self.verts) - 1

    def add_grid(self, grid, closed_u=False, closed_v=False, flip=False):
        """grid: nv rows of nu V each. Quad faces."""
        nv = len(grid)
        nu = len(grid[0])
        base = len(self.verts)
        for row in grid:
            if len(row) != nu:
                raise ValueError("ragged grid")
            for p in row:
                self.add(p)
        nu_f = nu if closed_u else nu - 1
        nv_f = nv if closed_v else nv - 1

        def vid(i, j):
            return base + (i % nv) * nu + (j % nu)

        for i in range(nv_f):
            i2 = (i + 1) % nv if closed_v else i + 1
            for j in range(nu_f):
                j2 = (j + 1) % nu if closed_u else j + 1
                a, b, c, d = vid(i, j), vid(i, j2), vid(i2, j2), vid(i2, j)
                self.faces.append((a, d, c, b) if flip else (a, b, c, d))
        return base

    def cap_ring(self, start, count, center, flip=False):
        ci = self.add(center)
        for i in range(count):
            a = start + i
            b = start + (i + 1) % count
            self.faces.append((ci, b, a) if flip else (ci, a, b))

    def translate(self, off):
        for i, v in enumerate(self.verts):
            self.verts[i] = v + off
        return self

    def tri_count(self):
        return sum(len(f) - 2 for f in self.faces)

    def bbox(self):
        if not self.verts:
            return None
        xs = [v.x for v in self.verts]
        ys = [v.y for v in self.verts]
        zs = [v.z for v in self.verts]
        return (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))


def merge_meshes(name, meshes, material=None):
    if not meshes:
        return Mesh(name, material or "M_Skin")
    out = Mesh(name, material or meshes[0].material, smooth=meshes[0].smooth)
    for m in meshes:
        base = len(out.verts)
        for v in m.verts:
            out.add(v)
        for f in m.faces:
            out.faces.append(tuple(i + base for i in f))
    return out


def ellipse_ring(cx, cy, cz, rx, ry, n, z=None, fold_n=0, fold_amp=0.0, fold_phase=0.0):
    z = cz if z is None else z
    ring = []
    for i in range(n):
        a = 2.0 * math.pi * i / n
        rmod = 1.0
        if fold_n:
            rmod += fold_amp * abs(math.sin(fold_n * 0.5 * a + fold_phase))
        ring.append(V(cx + math.cos(a) * rx * rmod, cy + math.sin(a) * ry * rmod, z))
    return ring


def gravity_fold_ring(cx, cy, cz, rx, ry, n, amp=0.0, n_folds=FOLD_COUNT, back_extra=0.0, phase=FOLD_PHASE):
    """Closed ring with hanging gravity wells at stable longitudes. Not a smooth cone."""
    ring = []
    for i in range(n):
        a = 2.0 * math.pi * i / n
        well = abs(math.sin(n_folds * 0.5 * a + phase)) ** 1.55
        rmod = 1.0 - amp * well
        if math.sin(a) > 0.0:
            rmod += back_extra
        z = cz - amp * well * 0.28
        ring.append(V(cx + math.cos(a) * rx * rmod, cy + math.sin(a) * ry * rmod, z))
    return ring


# Long/short hanging folds (radians). Not 8 equal gear teeth.
# a=0 +X (wearer's right), a=π/2 +Y back, a=π -X left, a=-π/2 -Y front.
CLOTH_FOLDS = (
    (-1.48, 0.40, 0.036),  # front, long
    (-1.95, 0.26, 0.018),  # front-right, shorter
    (-0.92, 0.30, 0.024),  # front-left
    (1.18, 0.42, 0.032),  # back, long
    (2.10, 0.24, 0.014),  # back-left short
    (0.42, 0.22, 0.012),  # back-right short
)
CLOTH_RIDGES = (
    (-1.70, 0.12, 0.014),
    (-1.15, 0.11, 0.012),
    (0.80, 0.13, 0.016),
    (1.55, 0.12, 0.014),
)


def cloth_fold_ring(cx, cy, cz, rx, ry, n, fold_scale=1.0):
    """Full-volume skirt/body ring. Local long/short folds + ridges, not a cone and not a gear."""
    ring = []
    for i in range(n):
        a = 2.0 * math.pi * i / n
        rmod = 1.0
        hang = 0.0
        if fold_scale > 1e-6:
            rmod += 0.008 * fold_scale * math.sin(2.0 * a + 0.55)
            for ang, width, depth in CLOTH_FOLDS:
                d = abs(math.atan2(math.sin(a - ang), math.cos(a - ang)))
                well = math.exp(-((d / max(width, 1e-4)) ** 2))
                rmod -= (depth / max(rx, 1e-4)) * fold_scale * well
                hang += depth * fold_scale * well * 0.22
            for ang, width, height in CLOTH_RIDGES:
                d = abs(math.atan2(math.sin(a - ang), math.cos(a - ang)))
                ridge = math.exp(-((d / max(width, 1e-4)) ** 2))
                rmod += (height / max(rx, 1e-4)) * fold_scale * ridge
        ring.append(V(cx + math.cos(a) * rx * rmod, cy + math.sin(a) * ry * rmod, cz - hang))
    return ring


def superellipse_ring(cx, cy, cz, rx, ry, n, p=3.6):
    """Boxy rounded-rect ring (p>2). Used for partitioned 诸葛巾 boards, not a barrel."""
    ring = []
    e = 2.0 / max(p, 1.01)
    for i in range(n):
        a = 2.0 * math.pi * i / n
        c, s = math.cos(a), math.sin(a)
        x = math.copysign(abs(c) ** e, c) * rx
        y = math.copysign(abs(s) ** e, s) * ry
        ring.append(V(cx + x, cy + y, cz))
    return ring


def panel_arc_ring(cx, cy, cz, rx, ry, a0, a1, n, folds, ridges, fold_scale, outward=0.0):
    """Open longitude arc. Wells + ridges so lookdown gets shading turns, not ring noise."""
    ring = []
    for i in range(n):
        t = i / max(1, n - 1)
        a = lerp(a0, a1, t)
        rmod = 1.0
        hang = 0.0
        if fold_scale > 1e-6:
            rmod += 0.022 * fold_scale * math.sin(2.4 * a + 0.35)
            for ang, width, depth in folds:
                d = abs(math.atan2(math.sin(a - ang), math.cos(a - ang)))
                well = math.exp(-((d / max(width, 1e-4)) ** 2))
                rmod -= (depth / max(rx, 1e-4)) * fold_scale * well
                hang += depth * fold_scale * well * 0.40
            for ang, width, height in ridges:
                d = abs(math.atan2(math.sin(a - ang), math.cos(a - ang)))
                ridge = math.exp(-((d / max(width, 1e-4)) ** 2))
                rmod += (height / max(rx, 1e-4)) * fold_scale * ridge
        x = cx + math.cos(a) * rx * rmod
        y = cy + math.sin(a) * ry * rmod
        rad = V(math.cos(a), math.sin(a), 0.0)
        ring.append(V(x, y, cz - hang) + rad * outward)
    return ring


def ring_centroid(ring):
    s = V(0, 0, 0)
    for p in ring:
        s = s + p
    return s * (1.0 / len(ring))


def lerp_ring(a, b, t):
    return [a[i].lerp(b[i], t) for i in range(len(a))]


def interp_body_ring(rings, z):
    zs = [ring_centroid(r).z for r in rings]
    if z >= zs[0]:
        return list(rings[0]), 0
    if z <= zs[-1]:
        return list(rings[-1]), max(0, len(rings) - 2)
    for i in range(len(zs) - 1):
        if zs[i] >= z >= zs[i + 1]:
            span = zs[i] - zs[i + 1]
            t = 0.0 if span < 1e-9 else (zs[i] - z) / span
            return lerp_ring(rings[i], rings[i + 1], t), i
    return list(rings[-1]), max(0, len(rings) - 2)


def sample_body_surface(rings, z, angle):
    """Point and outward normal on Robe_Body at height z and longitude angle."""
    ring, idx = interp_body_ring(rings, z)
    n = len(ring)
    u = (angle / (2.0 * math.pi)) % 1.0
    f = u * n
    j0 = int(math.floor(f)) % n
    t = f - math.floor(f)
    j1 = (j0 + 1) % n
    p = ring[j0].lerp(ring[j1], t)
    idx2 = min(idx + 1, len(rings) - 1)
    ring_b = rings[idx2]
    p_down = ring_b[j0].lerp(ring_b[j1], t)
    down = p_down - p
    if down.length() < 1e-8:
        down = V(0, 0, -1)
    tangent = ring[j1] - ring[j0]
    nrm = tangent.cross(down)
    c = ring_centroid(ring)
    radial = V(p.x - c.x, p.y - c.y, 0.0)
    if nrm.dot(radial) < 0:
        nrm = -nrm
    nrm = nrm.nrm()
    return p, nrm


def loft_closed(rings, name, material, smooth=True):
    m = Mesh(name, material, smooth=smooth)
    m.add_grid(rings, closed_u=True, closed_v=False)
    return m


def annulus_between(ring_a, ring_b, name, material, flip=False, outward=None):
    """Stitch two equal-length loops into a closed band (sleeve/neck caps)."""
    if len(ring_a) != len(ring_b) or len(ring_a) < 3:
        raise ValueError("annulus needs matching rings")
    m = Mesh(name, material)
    n = len(ring_a)
    for p in ring_a:
        m.add(p)
    for p in ring_b:
        m.add(p)
    for j in range(n):
        j2 = (j + 1) % n
        a, b, c, d = j, j2, n + j2, n + j
        m.faces.append((a, d, c, b) if flip else (a, b, c, d))
    if outward is not None and m.faces:
        acc = V(0, 0, 0)
        for fa in m.faces:
            acc = acc + (m.verts[fa[1]] - m.verts[fa[0]]).cross(m.verts[fa[2]] - m.verts[fa[0]])
        if acc.dot(outward) < 0:
            m.faces = [tuple(reversed(f)) for f in m.faces]
    return m


def strip_between(ring_a, ring_b, name, material, outward=None):
    """Open stitch (does not wrap last→first). Shoulder-top seal without closing the front opening."""
    if len(ring_a) != len(ring_b) or len(ring_a) < 2:
        raise ValueError("strip needs matching open rings")
    m = Mesh(name, material)
    n = len(ring_a)
    for p in ring_a:
        m.add(p)
    for p in ring_b:
        m.add(p)
    for j in range(n - 1):
        j2 = j + 1
        a, b, c, d = j, j2, n + j2, n + j
        m.faces.append((a, b, c, d))
    if outward is not None and m.faces:
        acc = V(0, 0, 0)
        for fa in m.faces:
            acc = acc + (m.verts[fa[1]] - m.verts[fa[0]]).cross(m.verts[fa[2]] - m.verts[fa[0]])
        if acc.dot(outward) < 0:
            m.faces = [tuple(reversed(f)) for f in m.faces]
    return m


def disk_from_ring(ring, name, material, outward=None):
    """Filled disk (not an annulus rim). Closes a tube root so there is no inner hole."""
    if len(ring) < 3:
        raise ValueError("disk needs a ring")
    m = Mesh(name, material)
    c = V(0, 0, 0)
    for p in ring:
        m.add(p)
        c = c + p
    c = c * (1.0 / len(ring))
    m.cap_ring(0, len(ring), c, flip=False)
    if outward is not None and m.faces:
        acc = V(0, 0, 0)
        for fa in m.faces:
            acc = acc + (m.verts[fa[1]] - m.verts[fa[0]]).cross(m.verts[fa[2]] - m.verts[fa[0]])
        if acc.dot(outward) < 0:
            m.faces = [tuple(reversed(f)) for f in m.faces]
    return m


def rotate_around(v, axis, ang):
    axis = axis.nrm()
    c, s = math.cos(ang), math.sin(ang)
    return v * c + axis.cross(v) * s + axis * axis.dot(v) * (1.0 - c)


def lathe_rz(profile_rz, n_seg, name, material, axis_y_face=True):
    """profile_rz: list of (r, z). Lathe around Z. theta=0 at +X, face (-Y) at -pi/2."""
    m = Mesh(name, material)
    grid = []
    for r, z in profile_rz:
        row = []
        for i in range(n_seg):
            a = 2.0 * math.pi * i / n_seg
            x = r * math.cos(a)
            y = r * math.sin(a)
            row.append(V(x, y, z))
        grid.append(row)
    m.add_grid(grid, closed_u=True, closed_v=False)
    return m


def sweep_profile(path, profile2d, name, material, closed_profile=True, scale_fn=None):
    """profile2d: list of (u, v) in the N-B plane of each path frame."""
    T, N, B = bishop_frames(path)
    grid = []
    for i, p in enumerate(path):
        s = 1.0 if scale_fn is None else scale_fn(i / max(1, len(path) - 1))
        row = []
        for u, v in profile2d:
            row.append(p + N[i] * (u * s) + B[i] * (v * s))
        grid.append(row)
    m = Mesh(name, material)
    m.add_grid(grid, closed_u=closed_profile, closed_v=False)
    return m


def tube_along(path, radius_fn, n_u, name, material, hemi=None):
    T, N, B = bishop_frames(path)
    grid = []
    nu = n_u
    for i, p in enumerate(path):
        t = i / max(1, len(path) - 1)
        r = radius_fn(t) if callable(radius_fn) else radius_fn
        row = []
        for j in range(nu):
            a = 2.0 * math.pi * j / nu
            if hemi == "posv" and math.sin(a) < 0:
                a = 0.0 if math.cos(a) > 0 else math.pi
            row.append(p + N[i] * (math.cos(a) * r) + B[i] * (math.sin(a) * r))
        grid.append(row)
    m = Mesh(name, material)
    m.add_grid(grid, closed_u=True, closed_v=False)
    # caps
    if len(path) >= 2:
        r0 = radius_fn(0.0) if callable(radius_fn) else radius_fn
        r1 = radius_fn(1.0) if callable(radius_fn) else radius_fn
        if r0 > 1e-5:
            m.cap_ring(0, nu, path[0], flip=True)
        if r1 > 1e-5:
            m.cap_ring(nu * (len(path) - 1), nu, path[-1], flip=False)
    return m


def thicken_sheet(grid_top, thickness_fn, name, material):
    """grid_top[v][u]; build a closed thin solid with a bottom offset along estimated normals."""
    nv, nu = len(grid_top), len(grid_top[0])

    def vert(i, j):
        return grid_top[i][j]

    normals = [[V(0, 0, 1) for _ in range(nu)] for _ in range(nv)]
    for i in range(nv):
        for j in range(nu):
            i0 = max(0, i - 1)
            i1 = min(nv - 1, i + 1)
            j0 = max(0, j - 1)
            j1 = min(nu - 1, j + 1)
            du = vert(i, j1) - vert(i, j0)
            dv = vert(i1, j) - vert(i0, j)
            normals[i][j] = dv.cross(du).nrm()
    top = grid_top
    bot = []
    for i in range(nv):
        row = []
        for j in range(nu):
            t = i / max(1, nv - 1)
            u = j / max(1, nu - 1)
            th = thickness_fn(t, u) if callable(thickness_fn) else thickness_fn
            row.append(top[i][j] - normals[i][j] * th)
        bot.append(row)
    m = Mesh(name, material)
    m.add_grid(top, closed_u=False, closed_v=False)
    m.add_grid(bot, closed_u=False, closed_v=False, flip=True)
    # stitch edges
    def gid(which, i, j):
        base = 0 if which == 0 else nv * nu
        return base + i * nu + j

    for j in range(nu - 1):
        m.faces.append((gid(0, 0, j), gid(0, 0, j + 1), gid(1, 0, j + 1), gid(1, 0, j)))
        m.faces.append(
            (gid(0, nv - 1, j + 1), gid(0, nv - 1, j), gid(1, nv - 1, j), gid(1, nv - 1, j + 1))
        )
    for i in range(nv - 1):
        m.faces.append((gid(0, i + 1, 0), gid(0, i, 0), gid(1, i, 0), gid(1, i + 1, 0)))
        m.faces.append(
            (
                gid(0, i, nu - 1),
                gid(0, i + 1, nu - 1),
                gid(1, i + 1, nu - 1),
                gid(1, i, nu - 1),
            )
        )
    return m


def bump(p, c, rx, ry, rz, amount, direction):
    q = p - c
    n = (q.x / rx) ** 2 + (q.y / ry) ** 2 + (q.z / rz) ** 2
    if n >= 1.0:
        return V(0, 0, 0)
    w = (1.0 - n) ** 2
    return direction.nrm() * (amount * w)


# ---------------------------------------------------------------------------
# Character parts
# ---------------------------------------------------------------------------
def _rz_profile(pairs, n):
    """pairs: list of (r,z), resampled."""
    pts = [V(r, 0, z) for r, z in pairs]
    sm = poly_bezier(pts, max(2, n // (len(pts) - 1)))
    return [(p.x, p.z) for p in sm]


def build_head():
    """Lathe of front/back Bezier silhouettes + feature displacements. Not a UV sphere."""
    n_u, n_v = 48, 36
    chin, crown = CHIN_Z, CROWN_Z
    # Side-view radius from axis (front silhouette, scholarly adult — not an egg).
    front = _rz_profile(
        [
            (0.011, chin),
            (0.034, chin + 0.018),
            (0.048, chin + 0.040),
            (0.062, chin + 0.070),
            (0.078, chin + 0.100),
            (0.088, chin + 0.125),  # zygoma
            (0.080, chin + 0.148),  # eye line (pre-socket)
            (0.086, chin + 0.168),  # brow
            (0.080, chin + 0.195),
            (0.068, chin + 0.220),
            (0.028, crown),
        ],
        n_v,
    )
    back = _rz_profile(
        [
            (0.030, chin),
            (0.055, chin + 0.030),
            (0.082, chin + 0.070),
            (0.096, chin + 0.120),
            (0.100, chin + 0.165),
            (0.092, chin + 0.205),
            (0.028, crown),
        ],
        n_v,
    )
    # resample both to n_v
    def resamp(prof, n):
        zs = [crown - (crown - chin) * i / (n - 1) for i in range(n)]
        # prof is listed chin->crown; interpolate r by z
        out = []
        for z in zs:
            # find
            r = prof[0][0]
            for a, b in zip(prof, prof[1:]):
                z0, z1 = a[1], b[1]
                if (z0 <= z <= z1) or (z1 <= z <= z0):
                    t = 0 if abs(z1 - z0) < 1e-9 else (z - z0) / (z1 - z0)
                    r = lerp(a[0], b[0], t)
                    break
            else:
                r = prof[-1][0] if z >= prof[-1][1] else prof[0][0]
            out.append((r, z))
        return out

    # front/back listed chin->crown; rings should go chin->crown too
    front = resamp(
        [(r, z) for r, z in _rz_profile(
            [
                (0.011, chin),
                (0.034, chin + 0.018),
                (0.048, chin + 0.040),
                (0.062, chin + 0.070),
                (0.078, chin + 0.100),
                (0.088, chin + 0.125),
                (0.080, chin + 0.148),
                (0.086, chin + 0.168),
                (0.080, chin + 0.195),
                (0.068, chin + 0.220),
                (0.028, crown),
            ],
            24,
        )],
        n_v,
    )
    back = resamp(
        [(r, z) for r, z in _rz_profile(
            [
                (0.030, chin),
                (0.055, chin + 0.030),
                (0.082, chin + 0.070),
                (0.096, chin + 0.120),
                (0.100, chin + 0.165),
                (0.092, chin + 0.205),
                (0.028, crown),
            ],
            24,
        )],
        n_v,
    )

    grid = []
    for i in range(n_v):
        rf, z = front[i]
        rb, _ = back[i]
        row = []
        for j in range(n_u):
            a = 2.0 * math.pi * j / n_u
            # s=0 face (-Y), s=1 back (+Y)
            s = 0.5 * (1.0 + math.sin(a))
            s = s * s * (3 - 2 * s)
            r = lerp(rf, rb, s)
            # slightly wider skull in X than depth in Y
            x = r * math.cos(a) * 1.04
            y = r * math.sin(a)
            if y < 0:
                y *= 0.90  # flatter face plane
            p = V(x, y, z)
            row.append(p)
        grid.append(row)

    # Feature displacements — readable sockets / brow / nose / zygoma / jaw
    for i in range(n_v):
        for j in range(n_u):
            p = grid[i][j]
            # jaw angles
            p = p + bump(p, V(0.062, 0.010, chin + 0.038), 0.04, 0.05, 0.04, 0.012, V(1, 0.1, -0.05))
            p = p + bump(p, V(-0.062, 0.010, chin + 0.038), 0.04, 0.05, 0.04, 0.012, V(-1, 0.1, -0.05))
            # chin forward
            p = p + bump(p, V(0, -0.04, chin + 0.008), 0.028, 0.04, 0.022, 0.016, V(0, -1, -0.2))
            # zygoma
            p = p + bump(p, V(0.070, -0.028, chin + 0.118), 0.032, 0.04, 0.028, 0.014, V(1, -0.4, 0.1))
            p = p + bump(p, V(-0.070, -0.028, chin + 0.118), 0.032, 0.04, 0.028, 0.014, V(-1, -0.4, 0.1))
            # eye sockets (indent)
            p = p + bump(p, V(0.033, -0.068, EYE_Z), 0.026, 0.022, 0.016, 0.017, V(0, 1, 0.15))
            p = p + bump(p, V(-0.033, -0.068, EYE_Z), 0.026, 0.022, 0.016, 0.017, V(0, 1, 0.15))
            # brow ridge
            p = p + bump(p, V(0.030, -0.072, BROW_Z), 0.028, 0.018, 0.012, 0.011, V(0, -1, 0.6))
            p = p + bump(p, V(-0.030, -0.072, BROW_Z), 0.028, 0.018, 0.012, 0.011, V(0, -1, 0.6))
            p = p + bump(p, V(0.0, -0.070, BROW_Z + 0.004), 0.018, 0.016, 0.010, 0.007, V(0, -0.4, 1))
            # nose bridge + tip + alae
            p = p + bump(p, V(0, -0.078, EYE_Z - 0.012), 0.012, 0.04, 0.028, 0.022, V(0, -1, 0))
            p = p + bump(p, V(0, -0.095, NOSE_TIP_Z), 0.012, 0.022, 0.016, 0.018, V(0, -1, -0.2))
            p = p + bump(p, V(0.012, -0.082, NOSE_TIP_Z + 0.006), 0.010, 0.016, 0.010, 0.008, V(1, -0.6, 0))
            p = p + bump(p, V(-0.012, -0.082, NOSE_TIP_Z + 0.006), 0.010, 0.016, 0.010, 0.008, V(-1, -0.6, 0))
            # mouth valley + lips
            p = p + bump(p, V(0, -0.072, MOUTH_Z), 0.022, 0.014, 0.008, 0.007, V(0, 1, 0))
            p = p + bump(p, V(0, -0.080, MOUTH_Z + 0.007), 0.020, 0.012, 0.006, 0.006, V(0, -1, 0.4))
            p = p + bump(p, V(0, -0.078, MOUTH_Z - 0.007), 0.018, 0.012, 0.006, 0.005, V(0, -1, -0.3))
            # philtrum
            p = p + bump(p, V(0, -0.086, (MOUTH_Z + NOSE_TIP_Z) * 0.5), 0.006, 0.016, 0.014, 0.004, V(0, 1, 0))
            grid[i][j] = p

    m = Mesh("Head", "M_Skin")
    m.add_grid(grid, closed_u=True, closed_v=False)
    # neck hole already open at chin ring; cap crown
    crown_ring_start = n_u * (n_v - 1)
    m.cap_ring(crown_ring_start, n_u, V(0, 0, crown + 0.002), flip=False)
    return m


def _almond_grid(center, x_axis, y_axis, n_u, n_v, bulge):
    """Parametric almond (two parabolas) with bulge along normal = x×y."""
    nrm = x_axis.cross(y_axis).nrm()
    grid = []
    for i in range(n_v):
        v = i / (n_v - 1)  # 0 lower lid .. 1 upper
        row = []
        for j in range(n_u):
            u = j / (n_u - 1) * 2.0 - 1.0  # -1..1
            # almond height envelope
            env = 1.0 - u * u
            yk = (v - 0.5) * 2.0 * env  # -1..1 scaled
            # slightly pointed corners
            p = center + x_axis * u + y_axis * (yk * 0.50)
            p = p + nrm * (bulge * env * math.sin(v * math.pi))
            row.append(p)
        grid.append(row)
    return grid


def build_eyes():
    parts = []
    for side, name in ((1.0, "Eye_L"), (-1.0, "Eye_R")):
        c = V(0.033 * side, -0.074, EYE_Z)
        x_ax = V(0.015 * side, 0.002, 0)
        y_ax = V(0, 0.002, 0.008)
        grid = _almond_grid(c + V(0, -0.004, 0), x_ax, y_ax, 14, 8, 0.007)
        sclera = Mesh(name + "_Sclera", "M_Skin")
        sclera.add_grid(grid, closed_u=False, closed_v=False)
        iris = []
        ir = 0.0055
        nrm = V(0, -1, 0.08).nrm()
        right = V(side, 0, 0)
        up = nrm.cross(right).nrm()
        right = up.cross(nrm).nrm()
        for i in range(6):
            rr = ir * i / 5
            row = []
            for j in range(12):
                a = 2 * math.pi * j / 12
                row.append(
                    c + nrm * 0.006 + right * (math.cos(a) * rr * 0.9) + up * (math.sin(a) * rr * 0.7)
                )
            iris.append(row)
        im = Mesh(name + "_Iris", "M_Hair")
        im.add_grid(iris, closed_u=True, closed_v=False)
        lids = []
        for zsig, yoff in ((1.0, -0.001), (-1.0, 0.001)):
            path = []
            for k in range(8):
                t = k / 7 * 2 - 1
                env = 1 - t * t
                path.append(c + V(0.016 * t * side, -0.002 + yoff, 0.0075 * zsig * env))
            lids.append(
                sweep_profile(
                    path,
                    _rounded_rect(0.0042, 0.0020, 3),
                    name + "_Lid",
                    "M_Skin",
                    closed_profile=True,
                )
            )
        parts.append(merge_meshes(name, [sclera] + lids, "M_Skin"))
        parts.append(im)
    return parts


def _rounded_rect(w, h, n_per=3):
    """Closed 2d profile in (u,v), n_per points per corner."""
    hw, hh = w * 0.5, h * 0.5
    r = min(hw, hh) * 0.55
    corners = [
        (hw - r, hh - r, 0.0),
        (-hw + r, hh - r, math.pi * 0.5),
        (-hw + r, -hh + r, math.pi),
        (hw - r, -hh + r, math.pi * 1.5),
    ]
    pts = []
    for cx, cy, a0 in corners:
        for i in range(n_per):
            a = a0 + (math.pi * 0.5) * i / n_per
            pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pts


def build_ears():
    parts = []
    for side, name in ((1.0, "Ear_L"), (-1.0, "Ear_R")):
        # Loft of 4 ear profiles in a plane offset from the skull
        profiles = []
        # local: u along height, v along width, extruded in X
        shapes = [
            # (width, height_offset, depth, z)
            (0.012, 0.006, 0.010, EYE_Z - 0.010),
            (0.022, 0.014, 0.016, EYE_Z + 0.008),
            (0.018, 0.018, 0.014, EYE_Z + 0.028),
            (0.008, 0.008, 0.008, EYE_Z + 0.048),
        ]
        n = 16
        for w, h, d, z in shapes:
            ring = []
            for i in range(n):
                a = 2 * math.pi * i / n
                # ear-like: pinched lobe at bottom
                rr_w = w * (0.75 + 0.25 * math.cos(a))
                rr_h = h * (1.0 if math.sin(a) > 0 else 0.7)
                ly = math.sin(a) * rr_h
                lz = math.cos(a) * rr_w * 0.15
                lx = (0.5 + 0.5 * math.cos(a)) * d
                ring.append(V(side * (0.086 + lx), ly * 0.3 - 0.01, z + math.sin(a) * h))
            profiles.append(ring)
        m = loft_closed(profiles, name, "M_Skin")
        parts.append(m)
    return parts


def build_neck():
    """Skin column into the robe neck opening. Bottom is a filled disk, not an open tube."""
    n = 32
    rings = [
        ellipse_ring(0, 0.0, CHIN_Z + 0.008, 0.048, 0.046, n),
        ellipse_ring(0, 0.0, CHIN_Z - 0.035, 0.052, 0.050, n),
        ellipse_ring(0, 0.002, SHOULDER_Z + 0.08, 0.062, 0.056, n),
        ellipse_ring(0, 0.006, SHOULDER_Z + 0.02, 0.070, 0.062, n),
        ellipse_ring(0, 0.008, SHOULDER_Z - 0.03, 0.074, 0.064, n),
    ]
    m = loft_closed(rings, "Neck", "M_Skin")
    m.cap_ring(n * (len(rings) - 1), n, V(0, 0.008, SHOULDER_Z - 0.038), flip=False)
    return m


def robe_body_rings():
    """Neck → waist. Shoulder rings stay nearly smooth (do not regress closed shoulders)."""
    n = BODY_N
    cy = 0.012
    specs = [
        (0.074, 0.068, SHOULDER_Z + 0.082, 0.00),
        (0.118, 0.100, SHOULDER_Z + 0.048, 0.00),
        (0.178, 0.138, SHOULDER_Z + 0.008, 0.02),
        (0.208, 0.152, SHOULDER_Z - 0.048, 0.03),
        (0.218, 0.160, SHOULDER_Z - 0.095, 0.05),
        (0.214, 0.158, CHEST_Z + 0.02, 0.10),
        (0.205, 0.152, CHEST_Z - 0.06, 0.16),
        (0.198, 0.148, CHEST_Z - 0.12, 0.22),
        (0.200, 0.150, WAIST_Z + 0.06, 0.28),
        (0.204, 0.154, WAIST_Z + 0.01, 0.32),
        (0.208, 0.158, WAIST_Z - 0.02, 0.36),
    ]
    rings = []
    for rx, ry, z, fs in specs:
        rings.append(cloth_fold_ring(0.0, cy, z, rx, ry, n, fold_scale=fs))
    return rings


def build_robe_body():
    """ONE continuous ivory surface: neck opening → shoulders → chest → waist."""
    return loft_closed(robe_body_rings(), "Robe_Body", "M_RobeIvory")


def _you_ren_paths():
    """右衽: outer lapel from the jaw/neck, across the front, to the left waist side.
    Inner lapel is shorter, under the right, not a mirror X hanging in air.
    Angles: 0=+X right, -π/2=-Y front, π=-X left.
    """
    right = (
        (SHOULDER_Z + 0.078, -0.38),
        (SHOULDER_Z + 0.030, -0.70),
        (CHEST_Z + 0.090, -1.15),
        (CHEST_Z + 0.010, -1.55),
        (CHEST_Z - 0.070, -2.05),
        (WAIST_Z + 0.070, -2.55),
        (WAIST_Z + 0.015, -3.05),
    )
    left = (
        (SHOULDER_Z + 0.076, -2.75),
        (SHOULDER_Z + 0.020, -2.38),
        (CHEST_Z + 0.080, -1.95),
        (CHEST_Z - 0.020, -1.62),
        (CHEST_Z - 0.080, -1.42),
    )
    return right, left


def _resample_za(pairs, n):
    zs = [p[0] for p in pairs]
    aas = [p[1] for p in pairs]
    out = []
    for i in range(n):
        t = i / max(1, n - 1) * (len(pairs) - 1)
        k = min(int(t), len(pairs) - 2)
        f = t - k
        out.append((lerp(zs[k], zs[k + 1], f), lerp(aas[k], aas[k + 1], f)))
    return out


def _lapel_on_body(rings, za_pairs, offset, width0, width1, name, n_path=20, nu=7):
    """Every grid vertex is sampled on Robe_Body, then offset 2–4 mm along that vertex's normal."""
    samples = _resample_za(za_pairs, n_path)
    grid = []
    centerline = []
    for i, (z, a) in enumerate(samples):
        t = i / max(1, len(samples) - 1)
        p, n = sample_body_surface(rings, z, a)
        centerline.append(p + n * offset)
        ring, _ = interp_body_ring(rings, z)
        c = ring_centroid(ring)
        local_r = max(0.04, math.hypot(p.x - c.x, p.y - c.y))
        dang = lerp(width0, width1, t) / local_r
        row = []
        for j in range(nu):
            aa = a + lerp(-dang, dang, j / max(1, nu - 1))
            pj, nj = sample_body_surface(rings, z, aa)
            row.append(pj + nj * offset)
        grid.append(row)
    # ~1.6 mm sheet so the solid stays in the 2–4 mm offset band
    return thicken_sheet(grid, lambda tt, uu: 0.0016, name, "M_RobeIvory"), centerline


def build_collar(body_rings):
    """交领 projected onto Robe_Body (2–4 mm along the chest normal). True 右衽, not a floating X."""
    right_za, left_za = _you_ren_paths()
    outer, outer_pts = _lapel_on_body(body_rings, right_za, 0.0035, 0.032, 0.050, "Collar_R")
    inner, _ = _lapel_on_body(body_rings, left_za, 0.0022, 0.028, 0.042, "Collar_L")
    return [inner, outer], outer_pts


def _neck_arc_ring(z, rx, ry, a0, a1, n):
    ring = []
    for i in range(n):
        a = lerp(a0, a1, i / max(1, n - 1))
        ring.append(V(math.cos(a) * rx, math.sin(a) * ry, z))
    return ring


def build_standing_collar():
    """High 交领 wrapping the neck column up to the jaw so lookdown is not a long bare neck."""
    n = 16
    # Right outer stands from robe neck opening up to the jaw, wrapping front.
    right_specs = [
        (SHOULDER_Z + 0.070, 0.082, 0.074, -0.28, -3.05),
        (CHIN_Z - 0.070, 0.070, 0.064, -0.32, -3.00),
        (CHIN_Z - 0.012, 0.062, 0.058, -0.38, -2.92),
        (CHIN_Z + 0.022, 0.058, 0.054, -0.45, -2.80),
    ]
    left_specs = [
        (SHOULDER_Z + 0.070, 0.080, 0.072, -2.72, -0.95),
        (CHIN_Z - 0.070, 0.068, 0.062, -2.65, -1.05),
        (CHIN_Z - 0.012, 0.060, 0.056, -2.55, -1.15),
        (CHIN_Z + 0.016, 0.056, 0.052, -2.48, -1.22),
    ]
    parts = []
    for name, specs, offset, mat, thick in (
        ("CollarStand_R", right_specs, 0.006, "M_RobeIvory", 0.0045),
        ("CollarStand_L", left_specs, 0.0035, "M_RobeIvory", 0.0038),
        ("CollarStandInner_R", right_specs, 0.0018, "M_CyanGreen", 0.0022),
        ("CollarStandInner_L", left_specs, 0.0012, "M_CyanGreen", 0.0018),
    ):
        grid = []
        for z, rx, ry, a0, a1 in specs:
            row = _neck_arc_ring(z, rx + offset, ry + offset, a0, a1, n)
            grid.append(row)
        parts.append(thicken_sheet(grid, lambda tt, uu: thick, name, mat))
    return parts


WRAP_FOLDS = (
    (-0.55, 0.30, 0.052),
    (0.15, 0.22, 0.030),
    (0.85, 0.34, 0.056),
    (1.40, 0.20, 0.024),
    (-2.20, 0.30, 0.050),
    (-2.85, 0.22, 0.028),
    (-3.55, 0.34, 0.054),
    (2.18, 0.20, 0.022),
)
WRAP_RIDGES = (
    (-0.90, 0.14, 0.024),
    (0.48, 0.13, 0.020),
    (1.12, 0.15, 0.026),
    (-1.85, 0.14, 0.022),
    (-2.50, 0.13, 0.018),
    (2.90, 0.15, 0.024),
)

# Front opening of the outer robe (keep). Wrap goes the long way around the back.
# Back seam width is 0 because there is no back split.
PANEL_A_FRONT_R = -1.18
PANEL_A_FRONT_L = -1.92  # wrap end = this + 2π


def _panel_hang_keyframes():
    """Hanging silhouette BELOW the body-sampled shoulder. Do not float a 0.305 ring at the neck."""
    return [
        (0.228, 0.172, SHOULDER_Z - 0.085, 0.22, 0.006),
        (0.248, 0.188, CHEST_Z + 0.020, 0.38, 0.008),
        (0.226, 0.172, WAIST_Z + 0.030, 0.55, 0.010),
        (0.242, 0.186, WAIST_Z - 0.035, 0.70, 0.012),
        (0.290, 0.222, HIP_Z - 0.070, 0.86, 0.014),
        (0.332, 0.250, 0.38, 1.00, 0.016),
        (0.355, 0.268, HEM_Z + 0.038, 1.00, 0.014),
    ]


def _interp_panel_spec(keys, t):
    u = t * (len(keys) - 1)
    k = min(int(u), len(keys) - 2)
    f = u - k
    a, b = keys[k], keys[k + 1]
    return tuple(lerp(a[i], b[i], f) for i in range(5))


def _wrap_angles(nu):
    a0 = PANEL_A_FRONT_R
    a1 = PANEL_A_FRONT_L + 2.0 * math.pi
    return [lerp(a0, a1, j / max(1, nu - 1)) for j in range(nu)]


def _body_arc(body_rings, z, angles, offset):
    row = []
    for a in angles:
        p, n = sample_body_surface(body_rings, z, a)
        row.append(p + n * offset)
    return row


def build_outer_panels(body_rings):
    """One wrap-around outer robe, front opening only. Shoulder top grown from Robe_Body.
    Back center is continuous (seam width 0). Not two floating barrels.
    """
    keys = _panel_hang_keyframes()
    nv, nu = 16, 28
    cy = 0.012
    angles = _wrap_angles(nu)
    grid = []
    # Ring 0: actual neck/shoulder surface + 4 mm. Seals the lookdown barrel.
    grid.append(_body_arc(body_rings, SHOULDER_Z + 0.008, angles, 0.004))
    # Ring 1: transition still on the body, slightly further out.
    body_t = _body_arc(body_rings, SHOULDER_Z - 0.055, angles, 0.006)
    hang0 = panel_arc_ring(
        0.0, cy, keys[0][2], keys[0][0], keys[0][1], angles[0], angles[-1], nu, WRAP_FOLDS, WRAP_RIDGES, keys[0][3], keys[0][4]
    )
    grid.append(lerp_ring(body_t, hang0, 0.35))
    for i in range(2, nv):
        t = (i - 2) / max(1, nv - 3)
        rx, ry, z, fs, outw = _interp_panel_spec(keys, t)
        grid.append(panel_arc_ring(0.0, cy, z, rx, ry, angles[0], angles[-1], nu, WRAP_FOLDS, WRAP_RIDGES, fs, outw))

    parts = [thicken_sheet(grid, lambda tt, uu: 0.0070, "Robe_Panel_Outer", "M_RobeIvory")]
    # Stitch the open top onto the inner shoulder so lookdown cannot see into a hollow barrel.
    body_rim = _body_arc(body_rings, SHOULDER_Z + 0.008, angles, 0.0008)
    parts.append(strip_between(grid[0], body_rim, "Robe_Panel_ShoulderSeal", "M_RobeIvory", outward=V(0, 0, 1)))

    for col, tag in ((0, "R"), (-1, "L")):
        edge = [row[col] for row in grid]
        parts.append(
            sweep_profile(
                edge,
                _rounded_rect(0.016, 0.005, 3),
                "Robe_PanelFacing_%s" % tag,
                "M_CyanGreen",
                True,
            )
        )
    parts.append(
        sweep_profile(
            grid[-1][:],
            _rounded_rect(0.028, 0.010, 3),
            "Robe_PanelHem",
            "M_CyanGreen",
            True,
        )
    )
    # Waist cross-section of THIS wrap — sash must follow these verts, not a new ellipse.
    zs = [ring_centroid(r).z for r in grid]
    wi = min(range(len(zs)), key=lambda i: abs(zs[i] - (WAIST_Z + 0.012)))
    wi = max(1, min(wi, len(grid) - 1))
    return parts, grid[wi], grid[wi - 1], angles


def _close_front_bridge(open_ring, body_rings, z, angles, offset, n_bridge=6):
    """Open wrap + short front bridge on the body, so a sash can be a closed band."""
    a_r, a_l = PANEL_A_FRONT_R, PANEL_A_FRONT_L
    bridge = []
    for i in range(1, n_bridge):
        a = lerp(a_l, a_r, i / n_bridge)
        p, n = sample_body_surface(body_rings, z, a)
        bridge.append(p + n * offset)
    # wrap ends at L-opening; bridge L → front → R, then closed_u meets wrap start.
    return list(open_ring) + bridge


def build_sash(waist_ring, waist_prev, body_rings):
    """Cyan sash lofted from the outer-robe waist verts (same method as hem-on-skirt-ring).
    Independent ellipse was punching through the panels as broken chunks.
    """
    z = ring_centroid(waist_ring).z
    closed = _close_front_bridge(waist_ring, body_rings, z, None, 0.008)
    closed_prev = _close_front_bridge(waist_prev, body_rings, ring_centroid(waist_prev).z, None, 0.006)
    n = len(closed)
    if len(closed_prev) != n:
        closed_prev = closed_prev[:n] if len(closed_prev) > n else closed_prev + [closed_prev[-1]] * (n - len(closed_prev))
    c = ring_centroid(closed)
    inner, mid, outer = [], [], []
    for j in range(n):
        p = closed[j]
        prev = closed_prev[j]
        tng = closed[(j + 1) % n] - closed[(j - 1) % n]
        up = prev - p
        nrm = tng.cross(up)
        radial = V(p.x - c.x, p.y - c.y, 0.0)
        if nrm.dot(radial) < 0:
            nrm = -nrm
        nrm = nrm.nrm()
        upn = up.nrm() if up.length() > 1e-8 else V(0, 0, 1)
        inner.append(p + nrm * 0.0015 + upn * 0.008)
        mid.append(p + nrm * 0.012 - upn * 0.002)
        outer.append(p + nrm * 0.018 - upn * 0.012)
    parts = [loft_closed([inner, mid, outer], "Sash_Band", "M_CyanGreen")]
    fy = min(closed, key=lambda v: v.y)
    knot = Mesh("Sash_Knot", "M_CyanGreen")
    krings = [
        ellipse_ring(fy.x, fy.y + 0.006, fy.z + 0.014, 0.024, 0.014, 12),
        ellipse_ring(fy.x, fy.y - 0.004, fy.z + 0.000, 0.030, 0.016, 12),
        ellipse_ring(fy.x, fy.y + 0.002, fy.z - 0.014, 0.022, 0.012, 12),
    ]
    knot.add_grid(krings, closed_u=True, closed_v=False)
    knot.cap_ring(0, 12, V(fy.x, fy.y + 0.008, fy.z + 0.020), flip=True)
    knot.cap_ring(24, 12, V(fy.x, fy.y, fy.z - 0.020), flip=False)
    parts.append(knot)
    tassel_path = poly_bezier(
        [
            V(fy.x, fy.y - 0.006, fy.z - 0.010),
            V(fy.x + 0.008, fy.y - 0.016, fy.z - 0.068),
            V(fy.x + 0.002, fy.y - 0.012, fy.z - 0.125),
            V(fy.x - 0.002, fy.y - 0.008, fy.z - 0.168),
        ],
        6,
    )
    parts.append(
        sweep_profile(
            tassel_path,
            _rounded_rect(0.014, 0.007, 3),
            "Sash_Tassel",
            "M_CyanGreen",
            True,
            scale_fn=lambda t: 1.0 - 0.45 * t,
        )
    )
    return parts


def build_skirt(waist_ring):
    """Outer skirt starts on the exact body waist ring. Inner is inset. Same longitudes to the hem."""
    n = len(waist_ring)
    cy = 0.012
    nv = 16
    hem_outer = cloth_fold_ring(0.0, cy, HEM_Z + 0.026, 0.282, 0.218, n, fold_scale=1.0)
    outer_rings = []
    for i in range(nv):
        t = i / (nv - 1)
        ease = t ** 0.78
        outer_rings.append(lerp_ring(waist_ring, hem_outer, ease))
    waist_c = ring_centroid(waist_ring)
    inner_waist = [waist_c + (p - waist_c) * 0.94 + V(0, 0, -0.012) for p in waist_ring]
    hem_inner = cloth_fold_ring(0.0, cy, HEM_Z + 0.010, 0.268, 0.206, n, fold_scale=0.92)
    inner_rings = []
    for i in range(nv):
        t = i / (nv - 1)
        inner_rings.append(lerp_ring(inner_waist, hem_inner, t ** 0.78))
    parts = [
        loft_closed(inner_rings, "Skirt_Inner", "M_RobeIvory"),
        loft_closed(outer_rings, "Skirt_Outer", "M_RobeIvory"),
    ]
    return parts, outer_rings[-1], outer_rings[-2]


def build_hair():
    """Black hair cap with hairline, temple locks, nape volume — under the guan."""
    n_u, n_v = 40, 16
    chin, crown = CHIN_Z, CROWN_Z
    grid = []
    for i in range(n_v):
        t = i / (n_v - 1)  # 0 hairline/nape mix -> 1 crown
        z = lerp(chin + 0.095, crown + 0.012, t)
        row = []
        for j in range(n_u):
            a = 2 * math.pi * j / n_u
            # hairline rises at forehead (-Y)
            face = 0.5 * (1.0 - math.sin(a))  # 1 at -Y
            z_hl = z
            if t < 0.35:
                z_hl = lerp(chin + 0.155, z, t / 0.35) * face + z * (1 - face)
                if face > 0.7 and t < 0.2:
                    # keep forehead mostly clear; hairline as a band
                    z_hl = chin + 0.168 + (z - (chin + 0.095)) * 0.15
            r = 0.092 + 0.012 * t + 0.008 * math.sin(a)  # more volume at back
            if math.sin(a) < 0:
                r *= 0.96
            x = r * math.cos(a)
            y = r * math.sin(a)
            # nape longer
            if t < 0.25 and math.sin(a) > 0.3:
                z_hl = lerp(chin + 0.02, z_hl, t / 0.25)
            row.append(V(x, y, z_hl))
        grid.append(row)
    cap = Mesh("Hair_Cap", "M_Hair")
    cap.add_grid(grid, closed_u=True, closed_v=False)
    cap.cap_ring(n_u * (n_v - 1), n_u, V(0, 0, crown + 0.016), flip=False)
    parts = [cap]
    # temple locks
    for side in (1.0, -1.0):
        path = poly_bezier(
            [
                V(side * 0.078, -0.040, EYE_Z + 0.02),
                V(side * 0.090, -0.028, EYE_Z - 0.02),
                V(side * 0.086, -0.010, CHIN_Z + 0.04),
                V(side * 0.070, 0.008, CHIN_Z - 0.01),
            ],
            6,
        )
        parts.append(
            tube_along(
                path,
                lambda t: 0.012 * (1.0 - 0.55 * t),
                10,
                "Hair_Lock_%s" % ("L" if side > 0 else "R"),
                "M_Hair",
            )
        )
    return parts


def build_guan():
    """诸葛巾 as partitioned boards: brim, boxy crown, sagittal/side boards. Not a plastic barrel."""
    parts = []
    n = 36
    band_path = ellipse_ring(0, 0.000, BROW_Z + 0.018, 0.095, 0.100, n)
    band_path = band_path + [band_path[0]]
    parts.append(
        sweep_profile(
            band_path,
            _rounded_rect(0.034, 0.018, 4),
            "Guan_Brim",
            "M_CyanGreen",
            closed_profile=True,
        )
    )

    # Flat-top superellipse boards — pinched dome was the barrel.
    crown_rings = []
    specs = [
        (0.090, 0.096, BROW_Z + 0.026, 3.4),
        (0.102, 0.106, BROW_Z + 0.052, 3.8),
        (0.100, 0.102, BROW_Z + 0.078, 4.2),
        (0.092, 0.094, BROW_Z + 0.100, 4.0),
        (0.080, 0.082, BROW_Z + 0.116, 3.6),
    ]
    for rx, ry, z, p in specs:
        crown_rings.append(superellipse_ring(0, -0.004, z, rx, ry, n, p))
    crown = loft_closed(crown_rings, "Guan_Crown", "M_CyanGreen")
    crown.cap_ring(0, n, V(0, -0.004, BROW_Z + 0.022), flip=True)
    crown.cap_ring(n * (len(crown_rings) - 1), n, V(0, -0.004, BROW_Z + 0.122), flip=False)
    parts.append(crown)

    # Sagittal partition (center fold board)
    sag_grid = []
    for z, y0, y1, xw in (
        (BROW_Z + 0.028, -0.090, 0.088, 0.0),
        (BROW_Z + 0.072, -0.100, 0.096, 0.0),
        (BROW_Z + 0.112, -0.084, 0.078, 0.0),
    ):
        sag_grid.append([V(0.0, lerp(y0, y1, j / 7.0), z) for j in range(8)])
    parts.append(thicken_sheet(sag_grid, lambda tt, uu: 0.008, "Guan_Board_Center", "M_CyanGreen"))

    # Front board
    front_grid = []
    for z, rx, rz_off in (
        (BROW_Z + 0.028, 0.078, 0.0),
        (BROW_Z + 0.068, 0.082, 0.0),
        (BROW_Z + 0.100, 0.070, 0.0),
    ):
        row = []
        for j in range(8):
            a = lerp(-0.85, 0.85, j / 7.0) - math.pi * 0.5
            row.append(V(math.cos(a) * rx, math.sin(a) * 0.100, z))
        front_grid.append(row)
    parts.append(thicken_sheet(front_grid, lambda tt, uu: 0.007, "Guan_Board_Front", "M_CyanGreen"))

    # Side boards
    for side, tag in ((1.0, "R"), (-1.0, "L")):
        grid = []
        for z, ry in (
            (BROW_Z + 0.030, 0.078),
            (BROW_Z + 0.072, 0.082),
            (BROW_Z + 0.108, 0.070),
        ):
            row = []
            for j in range(6):
                y = lerp(-0.055, 0.055, j / 5.0)
                row.append(V(side * 0.102, y, z))
            grid.append(row)
        parts.append(thicken_sheet(grid, lambda tt, uu: 0.007, "Guan_Board_%s" % tag, "M_CyanGreen"))

    knot_path = poly_bezier(
        [
            V(0.0, 0.095, BROW_Z + 0.040),
            V(0.0, 0.110, BROW_Z + 0.010),
            V(0.018, 0.100, CHIN_Z + 0.05),
            V(0.028, 0.080, CHIN_Z - 0.02),
        ],
        5,
    )
    parts.append(
        sweep_profile(
            knot_path,
            _rounded_rect(0.028, 0.008, 3),
            "Guan_Trail",
            "M_CyanGreen",
            closed_profile=True,
            scale_fn=lambda t: 1.0 - 0.35 * t,
        )
    )

    pin_prof = [
        (0.000, -0.095),
        (0.0028, -0.090),
        (0.0026, -0.020),
        (0.0032, 0.020),
        (0.0048, 0.055),
        (0.0090, 0.068),
        (0.0070, 0.078),
        (0.000, 0.086),
    ]
    pin = lathe_rz(pin_prof, 12, "Guan_Hairpin", "M_Gold")
    for i, v in enumerate(pin.verts):
        x, y, z = v.z, v.y, -v.x
        pin.verts[i] = V(x, y - 0.01, z + BROW_Z + 0.078)
    parts.append(pin)
    bead_prof = [(0.0, -0.007), (0.007, -0.003), (0.008, 0.0), (0.007, 0.003), (0.0, 0.007)]
    bead = lathe_rz(bead_prof, 12, "Guan_HairpinBead", "M_Gold")
    for i, v in enumerate(bead.verts):
        bead.verts[i] = V(v.x + 0.078, v.y - 0.01, v.z + BROW_Z + 0.078)
    parts.append(bead)
    return parts


def _beard_strand(origin, mid, tip, w0, th0, name, n_path=14, n_u=12):
    """Flat spindle (not a closed circular tube). Tapers; no 12 mm radius floor."""
    path = bezier([origin, origin.lerp(mid, 0.35) + V(0, 0.008, 0), mid, tip], n_path - 1)

    def rad(t):
        if t < 0.12:
            return w0 * lerp(0.40, 1.0, t / 0.12)
        if t < 0.52:
            return w0 * (1.0 + 0.06 * math.sin((t - 0.12) / 0.40 * math.pi))
        u = (t - 0.52) / 0.48
        return max(0.0022, w0 * ((1.0 - u) ** 1.35))

    profile = []
    for j in range(n_u):
        a = 2.0 * math.pi * j / n_u
        cu, sv = math.cos(a), math.sin(a)
        # spindle: flatter than an ellipse so it does not read as a shiny pipe
        profile.append(
            (
                math.copysign(abs(cu) ** 1.25, cu),
                math.copysign(abs(sv) ** 1.55, sv) * (th0 / max(w0, 1e-6)),
            )
        )
    return sweep_profile(path, profile, name, "M_Hair", closed_profile=True, scale_fn=rad)


def build_beard():
    """Three flat-spindle bundles, tapered uneven ends. No extra tail tubes."""
    parts = []
    for side, tag in ((1.0, "R"), (-1.0, "L")):
        origin = V(side * 0.016, -0.078, MOUTH_Z - 0.002)
        mid = V(side * 0.034, -0.092, MOUTH_Z - 0.042)
        tip = V(side * 0.038, -0.084, MOUTH_Z - 0.072)
        parts.append(_beard_strand(origin, mid, tip, 0.016, 0.0055, "Beard_Mustache_%s" % tag, n_path=12, n_u=12))
    bundles = (
        (
            "C",
            V(0.000, -0.074, CHIN_Z + 0.010),
            V(0.008, -0.142, CHEST_Z + 0.12),
            V(0.014, -0.155, CHEST_Z + 0.02),
            0.034,
            0.009,
        ),
        (
            "L",
            V(-0.034, -0.066, CHIN_Z + 0.006),
            V(-0.050, -0.128, CHEST_Z + 0.16),
            V(-0.044, -0.132, CHEST_Z + 0.06),
            0.028,
            0.0075,
        ),
        (
            "R",
            V(0.034, -0.066, CHIN_Z + 0.006),
            V(0.052, -0.132, CHEST_Z + 0.14),
            V(0.046, -0.140, CHEST_Z + 0.04),
            0.030,
            0.008,
        ),
    )
    for tag, origin, mid, tip, w0, th0 in bundles:
        parts.append(_beard_strand(origin, mid, tip, w0, th0, "Beard_Long_%s" % tag, n_path=16, n_u=12))
    return [
        merge_meshes("Beard_Mustache", [m for m in parts if m.name.startswith("Beard_Mustache")]),
        merge_meshes("Beard_Long", [m for m in parts if m.name.startswith("Beard_Long")]),
    ]


def arm_chain(side, raised):
    """Shoulder root buried in Robe_Body → wrist at the cuff. Shared by sleeves and hands."""
    sh = V(side * 0.122, 0.012, SHOULDER_Z - 0.040)
    if raised:
        mid = V(side * 0.22, -0.01, SHOULDER_Z - 0.10)
        el = V(side * 0.255, -0.07, CHEST_Z + 0.05)
        wr = V(side * 0.225, -0.155, CHEST_Z - 0.02)
    else:
        mid = V(side * 0.22, 0.03, SHOULDER_Z - 0.12)
        el = V(side * 0.30, -0.02, WAIST_Z + 0.18)
        wr = V(side * 0.335, -0.08, HIP_Z + 0.12)
    return [sh, mid, el, wr]


def fan_pose():
    wr = arm_chain(1.0, True)[-1]
    axis = V(-0.10, -0.38, 0.20).nrm()
    origin = wr + V(0.012, -0.018, 0.008) - axis * 0.05
    return origin, axis


FAN_HANDLE_LEN = 0.22
FAN_HANDLE_R = 0.009


def _sleeve_path(side, raised):
    return poly_bezier(arm_chain(side, raised), 8)


def build_sleeves():
    """Cloth tubes that join Robe_Body. Root is a FILLED disk buried in the shoulder — not an annulus rim."""
    parts = []
    for side, raised, tag in ((1.0, True, "R"), (-1.0, False, "L")):
        path = _sleeve_path(side, raised)
        n_u = 24
        T, N, B = bishop_frames(path)
        grid_outer = []
        r_end = 0.16 if not raised else 0.108
        ry_end = 0.112 if not raised else 0.076
        for i, p in enumerate(path):
            t = i / max(1, len(path) - 1)
            # Small buried root, then flare after leaving the body
            grow = 0.0 if t < 0.18 else ((t - 0.18) / 0.82) ** 0.85
            rx = lerp(0.034, r_end, grow)
            ry = lerp(0.028, ry_end, grow)
            row_o = []
            for j in range(n_u):
                a = 2 * math.pi * j / n_u
                fold = 1.0 + 0.10 * abs(math.sin(4.0 * a + t * 2.0)) * grow
                world_down = V(0, 0, -1)
                q = N[i] * math.cos(a) + B[i] * math.sin(a)
                hang = 0.0
                if q.dot(world_down) > 0:
                    hang = 0.032 * grow * q.dot(world_down)
                po = p + N[i] * (math.cos(a) * rx * fold) + B[i] * (math.sin(a) * ry * fold) + world_down * hang
                row_o.append(po)
            grid_outer.append(row_o)
        outer = Mesh("Sleeve_%s" % tag, "M_RobeIvory")
        outer.add_grid(grid_outer, closed_u=True, closed_v=False)
        parts.append(outer)
        # Filled disk at the buried root — closes the tube. Annulus rims left inner holes.
        parts.append(disk_from_ring(grid_outer[0], "SleeveRootCap_%s" % tag, "M_RobeIvory", outward=-T[0]))
        # Inner lining only near the cuff so lookdown cannot see a shoulder hole
        inner_from = int(len(path) * 0.62)
        grid_inner = []
        for i in range(inner_from, len(path)):
            t = i / max(1, len(path) - 1)
            grow = 0.0 if t < 0.18 else ((t - 0.18) / 0.82) ** 0.85
            rx = lerp(0.034, r_end, grow) - 0.011
            ry = lerp(0.028, ry_end, grow) - 0.009
            p = path[i]
            row_i = []
            for j in range(n_u):
                a = 2 * math.pi * j / n_u
                fold = 1.0 + 0.08 * abs(math.sin(4.0 * a + t * 2.0)) * grow
                row_i.append(
                    p + N[i] * (math.cos(a) * max(0.012, rx) * fold) + B[i] * (math.sin(a) * max(0.010, ry) * fold)
                )
            grid_inner.append(row_i)
        inner = Mesh("SleeveInner_%s" % tag, "M_RobeIvory")
        inner.add_grid(grid_inner, closed_u=True, closed_v=False, flip=True)
        parts.append(inner)
        parts.append(disk_from_ring(grid_inner[0], "SleeveInnerCap_%s" % tag, "M_RobeIvory", outward=-T[inner_from]))
        parts.append(annulus_between(grid_outer[-1], grid_inner[-1], "SleeveCapCuff_%s" % tag, "M_RobeIvory", outward=T[-1]))
        cuff_path = grid_outer[-1] + [grid_outer[-1][0]]
        parts.append(
            sweep_profile(
                cuff_path,
                _rounded_rect(0.038, 0.016, 4),
                "Cuff_%s" % tag,
                "M_CyanGreen",
                closed_profile=True,
            )
        )
        for pi, scale in enumerate((1.02, 0.92)):
            c0 = V(0, 0, 0)
            for q in grid_outer[-1]:
                c0 = c0 + q
            c0 = c0 * (1.0 / len(grid_outer[-1]))
            ring_pts = [c0 + (q - c0) * scale for q in grid_outer[-1]]
            ring_pts.append(ring_pts[0])
            parts.append(
                sweep_profile(
                    ring_pts,
                    [(math.cos(a) * 0.0022, math.sin(a) * 0.0022) for a in [2 * math.pi * k / 8 for k in range(8)]],
                    "CuffGold_%s_%d" % (tag, pi),
                    "M_Gold",
                    closed_profile=True,
                )
            )
    return parts


def build_trims(hem_ring, hem_prev, collar_centerline):
    """Hem cyan + gold follow Skirt_Outer bottom-ring vertices/normals. Collar trim follows 右衽."""
    parts = []
    n = len(hem_ring)
    c = ring_centroid(hem_ring)
    inner, mid, outer, gold = [], [], [], []
    for j in range(n):
        p = hem_ring[j]
        prev = hem_prev[j]
        tng = hem_ring[(j + 1) % n] - hem_ring[(j - 1) % n]
        up = prev - p
        nrm = tng.cross(up)
        radial = V(p.x - c.x, p.y - c.y, 0.0)
        if nrm.dot(radial) < 0:
            nrm = -nrm
        nrm = nrm.nrm()
        upn = up.nrm() if up.length() > 1e-8 else V(0, 0, 1)
        inner.append(p + nrm * 0.0015 + upn * 0.008)
        mid.append(p + nrm * 0.012 - upn * 0.006)
        outer.append(p + nrm * 0.018 - upn * 0.020)
        gold.append(p + nrm * 0.0195 + upn * 0.012)
    parts.append(loft_closed([inner, mid, outer], "Trim_Hem", "M_CyanGreen"))
    gold_path = gold + [gold[0]]
    parts.append(
        sweep_profile(
            gold_path,
            [(math.cos(a) * 0.002, math.sin(a) * 0.002) for a in [2 * math.pi * k / 8 for k in range(8)]],
            "Trim_HemGold",
            "M_Gold",
            True,
        )
    )
    if collar_centerline and len(collar_centerline) >= 2:
        parts.append(
            sweep_profile(
                collar_centerline,
                _rounded_rect(0.012, 0.004, 3),
                "Trim_Collar",
                "M_CyanGreen",
                True,
            )
        )
    return parts


def build_shoes():
    parts = []
    for side, tag in ((1.0, "L"), (-1.0, "R")):
        # 云头履 volume peeking under hem
        rings = []
        n = 16
        for rx, ry, z, lift in (
            (0.045, 0.10, 0.002, 0.0),
            (0.048, 0.11, 0.028, 0.0),
            (0.030, 0.08, 0.055, 0.02),
        ):
            ring = ellipse_ring(side * 0.09, -0.02, z, rx, ry, n)
            if lift:
                for k, p in enumerate(ring):
                    # cloud toe lifts at -Y
                    w = max(0, -p.y)
                    ring[k] = V(p.x, p.y, p.z + lift * w * 8)
            rings.append(ring)
        m = loft_closed(rings, "Shoe_%s" % tag, "M_Hair")
        # cap sole
        m.cap_ring(0, n, V(side * 0.09, -0.02, FOOT_Z), flip=True)
        parts.append(m)
        # gold cloud tip
        tip = tube_along(
            [
                V(side * 0.09, -0.12, 0.04),
                V(side * 0.09, -0.14, 0.055),
                V(side * 0.09, -0.13, 0.07),
            ],
            lambda t: 0.012 * (1 - 0.3 * t),
            8,
            "ShoeCloud_%s" % tag,
            "M_Gold",
        )
        parts.append(tip)
    return parts


def build_hands():
    """Hands emerge from cuffs. Right is a C-grip palm+phalanges, not a torus around the handle."""
    parts = []
    origin, axis = fan_pose()

    def palm_slab(wrist, along, nrm, across, length, width, thick, name):
        n = 12
        rings = []
        specs = (
            (0.00, width * 0.32, thick * 0.65),
            (0.22, width * 0.46, thick * 0.90),
            (0.55, width * 0.52, thick * 1.00),
            (0.82, width * 0.48, thick * 0.88),
            (1.00, width * 0.40, thick * 0.72),
        )
        along = along.nrm()
        nrm = nrm.nrm()
        across = across.nrm()
        for t, rx, ry in specs:
            c = wrist + along * (length * t)
            ring = []
            for j in range(n):
                a = 2.0 * math.pi * j / n
                ring.append(c + across * (math.cos(a) * rx) + nrm * (math.sin(a) * ry))
            rings.append(ring)
        m = loft_closed(rings, name, "M_Skin")
        m.cap_ring(0, n, wrist - along * 0.008, flip=True)
        knuckle = wrist + along * length
        return m, knuckle

    def phalanges(root, dir0, lengths, curls, bend_axis, rad0, name):
        pts = [root]
        d = dir0.nrm()
        p = root
        for L, ang in zip(lengths, curls):
            d = rotate_around(d, bend_axis, ang).nrm()
            p = p + d * L
            pts.append(p)
        path = sample_polyline(pts, 7)
        return tube_along(path, lambda t, r=rad0: r * (1.0 - 0.42 * t), 8, name, "M_Skin")

    # ----- Right: wrist inside cuff, palm slab, C-grip fingers -----
    r_chain = arm_chain(1.0, True)
    r_wr = r_chain[-1]
    r_el = r_chain[-2]
    along = (r_wr - r_el).nrm()
    # palm faces the handle
    nrm = axis.cross(along)
    if nrm.length() < 1e-6:
        nrm = V(0, -1, 0)
    nrm = nrm.nrm()
    handle_mid = origin + axis * (FAN_HANDLE_LEN * 0.38)
    if (handle_mid - r_wr).dot(nrm) < 0:
        nrm = -nrm
    across = along.cross(nrm).nrm()
    palm, knuckles = palm_slab(r_wr, along, nrm, across, 0.088, 0.072, 0.024, "Hand_R_Palm")
    parts.append(palm)
    parts.append(
        tube_along(
            sample_polyline([r_el.lerp(r_wr, 0.35), r_wr], 5),
            lambda t: 0.030 - 0.006 * t,
            10,
            "Hand_R_Wrist",
            "M_Skin",
        )
    )
    finger_specs = (
        ("Index", 0.026, [0.026, 0.020, 0.016], [0.28, 0.48, 0.38], 0.0074),
        ("Middle", 0.008, [0.030, 0.022, 0.016], [0.32, 0.52, 0.40], 0.0078),
        ("Ring", -0.010, [0.028, 0.020, 0.015], [0.30, 0.50, 0.36], 0.0072),
        ("Pinky", -0.026, [0.022, 0.016, 0.012], [0.26, 0.44, 0.32], 0.0060),
    )
    bend = across
    for name, off, lens, curls, rad in finger_specs:
        root = knuckles + across * off + nrm * (rad * 0.4) + along * 0.004
        parts.append(phalanges(root, along * 0.4 + nrm * 0.6, lens, curls, bend, rad, "Hand_R_%s" % name))
    th_root = r_wr + along * 0.028 - across * 0.028 + nrm * 0.008
    th_dir = (across * 0.2 + along * 0.3 + nrm * 0.7).nrm()
    parts.append(
        phalanges(th_root, th_dir, [0.026, 0.018], [0.40, 0.45], (along * 0.4 + across * 0.6).nrm(), 0.008, "Hand_R_Thumb")
    )

    # ----- Left: wrist + palm emerge from hanging cuff -----
    l_chain = arm_chain(-1.0, False)
    l_wr = l_chain[-1]
    l_el = l_chain[-2]
    l_along = (l_wr - l_el).nrm()
    l_nrm = V(0, -1, 0.15).nrm()
    l_across = l_along.cross(l_nrm).nrm()
    l_nrm = l_across.cross(l_along).nrm()
    lp, lkn = palm_slab(l_wr, l_along, l_nrm, l_across, 0.080, 0.066, 0.022, "Hand_L_Palm")
    parts.append(lp)
    parts.append(
        tube_along(
            sample_polyline([l_el.lerp(l_wr, 0.35), l_wr], 5),
            lambda t: 0.028 - 0.006 * t,
            10,
            "Hand_L_Wrist",
            "M_Skin",
        )
    )
    relaxed = (
        ("Index", 0.022, [0.024, 0.018, 0.014], [0.12, 0.18, 0.14], 0.0070),
        ("Middle", 0.006, [0.026, 0.019, 0.014], [0.14, 0.20, 0.15], 0.0074),
        ("Ring", -0.010, [0.024, 0.017, 0.013], [0.12, 0.18, 0.14], 0.0068),
        ("Pinky", -0.024, [0.020, 0.014, 0.011], [0.10, 0.16, 0.12], 0.0058),
    )
    for name, off, lens, curls, rad in relaxed:
        root = lkn + l_across * off + l_nrm * (rad * 0.3)
        parts.append(phalanges(root, l_along * 0.7 + l_nrm * 0.2, lens, curls, l_across, rad, "Hand_L_%s" % name))
    parts.append(
        phalanges(
            l_wr + l_along * 0.022 - l_across * 0.024 + l_nrm * 0.006,
            (l_across * 0.3 + l_along * 0.4 + l_nrm * 0.5).nrm(),
            [0.022, 0.016],
            [0.25, 0.22],
            l_along,
            0.0075,
            "Hand_L_Thumb",
        )
    )
    return parts


def build_fan():
    """White feather fan: thin vanes with thickness + veins. No sausage cylinders."""
    parts = []
    p0, axis = fan_pose()
    p1 = p0 + axis * FAN_HANDLE_LEN
    # handle from lathe of a tapering profile, then oriented
    hprof = [
        (0.011, 0.0),
        (0.009, FAN_HANDLE_LEN * 0.15),
        (0.008, FAN_HANDLE_LEN * 0.7),
        (0.007, FAN_HANDLE_LEN * 0.95),
        (0.0, FAN_HANDLE_LEN),
    ]
    handle = lathe_rz(hprof, 12, "Fan_Handle", "M_Wood")
    zax = axis
    # Vane FACE toward front (-Y) and a bit +X / +Z so front, side, and lookdown all read feathers.
    # Not forced onto the grip-perp plane: the handle already points mostly -Y, so a grip-perp
    # normal cannot face the front camera (that was the knife-edge).
    fan_normal = V(0.48, -0.84, 0.24).nrm()
    roll_n = (fan_normal - zax * fan_normal.dot(zax)).nrm()
    yax = zax.cross(roll_n).nrm()
    xax = yax.cross(zax).nrm()
    if xax.dot(roll_n) < 0:
        xax = -xax
        yax = -yax
    for i, v in enumerate(handle.verts):
        handle.verts[i] = p0 + xax * v.x + yax * v.y + zax * v.z
    parts.append(handle)
    # gold ferrule
    fprof = [(0.012, FAN_HANDLE_LEN * 0.88), (0.013, FAN_HANDLE_LEN * 0.93), (0.011, FAN_HANDLE_LEN * 0.99)]
    fer = lathe_rz(fprof, 12, "Fan_Ferrule", "M_Gold")
    for i, v in enumerate(fer.verts):
        fer.verts[i] = p0 + xax * v.x + yax * v.y + zax * v.z
    parts.append(fer)

    # Feathers: thin quill, full upper belly, blunt ROUND tips. Short layer over long.
    # Facing kept toward front (-Y) + a bit +X/+Z. Do not taper 0.05→0 (that was the needle spike).
    rachis_zero = yax * 0.62 + zax * 0.32 + V(0, 0, 1) * 0.14
    rachis_zero = (rachis_zero - fan_normal * rachis_zero.dot(fan_normal)).nrm()
    hinge = p1 - zax * 0.01
    vanes = []
    # 2f8abf7 long vanes were 0.385 / ~84 mm belly and covered the face like lotus petals.
    VANE_SCALE = 0.26 / 0.385

    def _one_vane(fi, t, length, stack, spread, tag):
        ang = (t - 0.5) * spread
        ca, sa = math.cos(ang), math.sin(ang)
        rdir = rachis_zero * ca + fan_normal.cross(rachis_zero) * sa + fan_normal * fan_normal.dot(rachis_zero) * (1 - ca)
        rdir = rdir.nrm()
        rachis = bezier(
            [
                hinge + stack,
                hinge + stack + rdir * (length * 0.32) + V(0, 0, 0.008),
                hinge + stack + rdir * (length * 0.68) + V(0, 0, -0.008),
                hinge + stack + rdir * length + V(0, 0, -0.018),
            ],
            14,
        )
        T, N, B = bishop_frames(rachis)
        nu, nv = 11, len(rachis)

        def width_at(tt):
            # quill → full belly → blunt round, scaled with the shorter vane
            s = VANE_SCALE
            if tt < 0.16:
                return lerp(0.0055, 0.074, (tt / 0.16) ** 0.72) * s
            if tt < 0.68:
                u = (tt - 0.16) / 0.52
                return (0.074 + 0.014 * math.sin(u * math.pi)) * s
            u = (tt - 0.68) / 0.32
            return lerp(0.084, 0.022, 0.5 - 0.5 * math.cos(min(1.0, u) * math.pi)) * s

        grid = []
        prev_side = None
        for i, p in enumerate(rachis):
            tt = i / max(1, nv - 1)
            w = width_at(tt)
            side = T[i].cross(fan_normal)
            if side.length() < 1e-6:
                side = T[i].cross(V(0, 0, 1) if abs(T[i].z) < 0.85 else V(0, 1, 0))
            side = side.nrm()
            if prev_side is not None and side.dot(prev_side) < 0:
                side = -side
            face = side.cross(T[i]).nrm()
            if face.dot(fan_normal) < 0:
                face = -face
                side = -side
            prev_side = side
            row = []
            for j in range(nu):
                u = j / (nu - 1) * 2.0 - 1.0
                # rounder cross-section at the tip
                round_u = math.sqrt(max(0.0, 1.0 - 0.22 * u * u))
                ww = w * round_u
                th = 0.00055 * (1.0 - 0.45 * abs(u)) * (1.0 - 0.10 * tt)
                if abs(u) < 0.10:
                    th += 0.0014 * (1.0 - abs(u) / 0.10)  # thin mid-rib
                row.append(p + side * (u * ww) + face * (th * 0.5))
            grid.append(row)
        # blunt round cap: 4 extra rows that close as a semicircle, not a point-spike
        tip_p = rachis[-1]
        tip_T = T[-1]
        tip_side = prev_side
        tip_face = tip_side.cross(tip_T).nrm()
        if tip_face.dot(fan_normal) < 0:
            tip_face = -tip_face
        w_end = width_at(1.0)
        for k in range(1, 5):
            s = k / 4.0
            cap_w = w_end * math.sqrt(max(0.0, 1.0 - s * s))
            cap_p = tip_p + tip_T * (0.020 * s)
            row = []
            for j in range(nu):
                u = j / (nu - 1) * 2.0 - 1.0
                row.append(cap_p + tip_side * (u * cap_w * math.sqrt(max(0.0, 1.0 - 0.3 * u * u))) + tip_face * 0.0003)
            grid.append(row)

        def thick(tt, uu):
            u = uu * 2 - 1
            base = 0.0009 * (1.0 - 0.35 * abs(u)) * (1.0 - 0.08 * tt)
            if abs(u) < 0.1:
                base += 0.0014 * (1.0 - abs(u) / 0.1)
            return max(0.00055, base)

        return thicken_sheet(grid, thick, "Fan_Feather_%s_%d" % (tag, fi), "M_Feather")

    spread_long = math.radians(118)
    spread_short = math.radians(102)
    # long back layer
    n_long = 7
    for fi in range(n_long):
        t = fi / (n_long - 1)
        length = 0.26 - 0.015 * abs(t - 0.5)
        stack = fan_normal * (-0.0036)
        vanes.append(_one_vane(fi, t, length, stack, spread_long, "L"))
    # short over long (complete fan)
    n_short = 6
    for fi in range(n_short):
        t = fi / (n_short - 1)
        length = 0.20 - 0.019 * abs(t - 0.48)
        stack = fan_normal * (0.0032 + 0.0012 * (fi % 2))
        vanes.append(_one_vane(fi, t, length, stack, spread_short, "S"))
    parts.append(merge_meshes("Fan_Vanes", vanes, "M_Feather"))
    return parts


# ---------------------------------------------------------------------------
# Palace courtyard (宫苑) — volumetric tiles, not PNG planes as the body
# ---------------------------------------------------------------------------
def build_courtyard():
    parts = []
    # stone slabs
    nx, ny = 9, 9
    size, gap, thick = 0.56, 0.025, 0.07
    origin = -0.5 * (nx * (size + gap) - gap)
    verts_all = Mesh("Courtyard_Stones", "M_Stone", smooth=False)
    for iy in range(ny):
        for ix in range(nx):
            hjit = 0.004 * math.sin(ix * 1.7 + iy * 0.9)
            x0 = origin + ix * (size + gap)
            y0 = origin + iy * (size + gap) + 0.35
            x1, y1 = x0 + size, y0 + size
            z0, z1 = -thick + hjit, 0.0 + hjit
            # box
            vs = [
                V(x0, y0, z0),
                V(x1, y0, z0),
                V(x1, y1, z0),
                V(x0, y1, z0),
                V(x0, y0, z1),
                V(x1, y0, z1),
                V(x1, y1, z1),
                V(x0, y1, z1),
            ]
            b = len(verts_all.verts)
            for v in vs:
                verts_all.add(v)
            faces = (
                (0, 1, 2, 3),
                (4, 7, 6, 5),
                (0, 4, 5, 1),
                (1, 5, 6, 2),
                (2, 6, 7, 3),
                (3, 7, 4, 0),
            )
            for f in faces:
                verts_all.faces.append(tuple(b + k for k in f))
    parts.append(verts_all)

    # low stone railing (+Y and ±X inner)
    def box_mesh(name, x0, y0, z0, x1, y1, z1, mat="M_Stone"):
        m = Mesh(name, mat, smooth=False)
        vs = [
            V(x0, y0, z0),
            V(x1, y0, z0),
            V(x1, y1, z0),
            V(x0, y1, z0),
            V(x0, y0, z1),
            V(x1, y0, z1),
            V(x1, y1, z1),
            V(x0, y1, z1),
        ]
        for v in vs:
            m.add(v)
        for f in (
            (0, 1, 2, 3),
            (4, 7, 6, 5),
            (0, 4, 5, 1),
            (1, 5, 6, 2),
            (2, 6, 7, 3),
            (3, 7, 4, 0),
        ):
            m.faces.append(f)
        return m

    parts.append(box_mesh("Rail_Back", -2.2, 2.35, 0.0, 2.2, 2.50, 0.42))
    parts.append(box_mesh("Rail_L", -2.50, -1.6, 0.0, -2.35, 2.50, 0.42))
    parts.append(box_mesh("Rail_R", 2.35, -1.6, 0.0, 2.50, 2.50, 0.42))
    return parts


def build_pavilion():
    parts = []
    cols = [(-1.15, 1.55), (1.15, 1.55), (-1.15, 2.55), (1.15, 2.55)]
    for i, (x, y) in enumerate(cols):
        path = [V(x, y, 0.0), V(x, y, 0.9), V(x, y, 1.85)]
        parts.append(tube_along(path, lambda t: 0.075 - 0.008 * t, 14, "Column_%d" % i, "M_Wood"))
        # plinth
        pl = Mesh("Plinth_%d" % i, "M_Stone", smooth=False)
        s = 0.14
        vs = [
            V(x - s, y - s, 0),
            V(x + s, y - s, 0),
            V(x + s, y + s, 0),
            V(x - s, y + s, 0),
            V(x - s, y - s, 0.12),
            V(x + s, y - s, 0.12),
            V(x + s, y + s, 0.12),
            V(x - s, y + s, 0.12),
        ]
        for v in vs:
            pl.add(v)
        for f in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
            pl.faces.append(f)
        parts.append(pl)

    # beams
    def beam(name, a, b, r=0.055):
        path = sample_polyline([a, b], 5)
        return tube_along(path, r, 10, name, "M_Wood")

    z_b = 1.88
    parts.append(beam("Beam_Front", V(-1.25, 1.55, z_b), V(1.25, 1.55, z_b)))
    parts.append(beam("Beam_Back", V(-1.25, 2.55, z_b), V(1.25, 2.55, z_b)))
    parts.append(beam("Beam_L", V(-1.15, 1.45, z_b), V(-1.15, 2.65, z_b)))
    parts.append(beam("Beam_R", V(1.15, 1.45, z_b), V(1.15, 2.65, z_b)))

    # Roof: two-slope with 筒瓦 as swept arc profiles (not a single plane)
    # ridge from x=-1.45 to 1.45 at y=2.05, z=2.55
    tiles = Mesh("Roof_Tiles", "M_CyanGreen", smooth=True)
    n_tile_x = 12
    n_tile_y = 8
    for iy in range(n_tile_y):
        ty = iy / (n_tile_y - 1)
        for ix in range(n_tile_x):
            tx = ix / (n_tile_x - 1)
            x = lerp(-1.45, 1.45, tx)
            # two slopes meeting at y=2.05
            y_front = lerp(1.25, 2.05, ty)
            y_back = lerp(2.85, 2.05, ty)
            z_front = lerp(2.05, 2.58, ty)
            z_back = lerp(2.05, 2.58, ty)
            # 筒瓦 cross-section: half-pipe on each slope, as a small lofted barrel
            for y0, z0, slope_sign in ((y_front, z_front, 1.0), (y_back, z_back, -1.0)):
                # skip double-counting ridge row
                if iy == n_tile_y - 1 and slope_sign < 0:
                    continue
                profile = []
                for k in range(6):
                    a = math.pi * k / 5  # 0..pi
                    profile.append(V(x + math.cos(a) * 0.055, y0, z0 + math.sin(a) * 0.038))
                # extrude a little along slope
                dy = 0.10 * slope_sign
                dz = 0.055
                grid = [profile, [V(p.x, p.y + dy, p.z + dz) for p in profile]]
                tiles.add_grid(grid, closed_u=False, closed_v=False)
    parts.append(tiles)

    # ridge beam
    ridge = tube_along(
        [V(-1.50, 2.05, 2.60), V(0, 2.05, 2.66), V(1.50, 2.05, 2.60)],
        lambda t: 0.05,
        12,
        "Roof_Ridge",
        "M_CyanGreen",
    )
    parts.append(ridge)
    # eave end discs (瓦当) as lathed profiles
    wadang = []
    for x in (-1.45, -0.7, 0.0, 0.7, 1.45):
        for y, z, ny in ((1.22, 2.02, -1), (2.88, 2.02, 1)):
            prof = [(0.0, -0.012), (0.046, -0.008), (0.050, 0.0), (0.040, 0.01), (0.0, 0.012)]
            d = lathe_rz(prof, 12, "Wadang_%s_%s" % (x, y), "M_CyanGreen")
            for i, v in enumerate(d.verts):
                d.verts[i] = V(v.x + x, y + v.z * ny * 0.2, v.y + z)
            wadang.append(d)
    parts.append(merge_meshes("Roof_Wadang", wadang, "M_CyanGreen"))
    return parts


# ---------------------------------------------------------------------------
# Assemble
# ---------------------------------------------------------------------------
def assemble_all():
    char = []
    char.append(build_head())
    char.extend(build_eyes())
    char.extend(build_ears())
    char.append(build_neck())
    body_rings = robe_body_rings()
    char.append(loft_closed(body_rings, "Robe_Body", "M_RobeIvory"))
    char.extend(build_hair())
    char.extend(build_guan())
    char.extend(build_beard())
    collar_parts, collar_edge = build_collar(body_rings)
    char.extend(collar_parts)
    char.extend(build_standing_collar())
    skirt_parts, hem_ring, hem_prev = build_skirt(body_rings[-1])
    char.extend(skirt_parts)
    panel_parts, sash_ring, sash_prev, _angs = build_outer_panels(body_rings)
    char.extend(panel_parts)
    char.extend(build_sash(sash_ring, sash_prev, body_rings))
    char.extend(build_sleeves())
    char.extend(build_trims(hem_ring, hem_prev, collar_edge))
    char.extend(build_shoes())
    char.extend(build_hands())
    char.extend(build_fan())
    env = []
    env.extend(build_courtyard())
    env.extend(build_pavilion())
    return char, env


def snap_feet(meshes):
    zs = []
    for m in meshes:
        bb = m.bbox()
        if bb:
            zs.append(bb[2])
    if not zs:
        return 0.0
    dz = min(zs)
    if abs(dz) > 1e-6:
        off = V(0, 0, -dz)
        for m in meshes:
            m.translate(off)
    return dz


def census(meshes):
    mats = {}
    verts = 0
    tris = 0
    parts = []
    for m in meshes:
        mats[m.material] = mats.get(m.material, 0) + 1
        verts += len(m.verts)
        tris += m.tri_count()
        bb = m.bbox()
        parts.append(
            {
                "name": m.name,
                "material": m.material,
                "verts": len(m.verts),
                "tris": m.tri_count(),
                "bbox": None if not bb else [round(x, 4) for x in bb],
            }
        )
    return {
        "part_count": len(meshes),
        "verts": verts,
        "tris": tris,
        "materials_used": sorted(mats.keys()),
        "material_count": len(mats),
        "parts": parts,
    }


# ---------------------------------------------------------------------------
# Blender I/O
# ---------------------------------------------------------------------------
def _op_label(op):
    if op is None:
        return "operator"
    for attr in ("idname", "bl_idname"):
        val = getattr(op, attr, None)
        if val:
            return str(val)
    return repr(op)


def operator_property_ids(op):
    """Ids from the *live operator* RNA.

    Blender 5.2.1 (Mac, verified): ``filepath`` is NOT on
    ``bpy.types.EXPORT_SCENE_OT_gltf.bl_rna.properties`` but IS on
    ``bpy.ops.export_scene.gltf.get_rna_type().properties``. Filtering the
    class ``bl_rna`` silently drops ``filepath`` and the exporter opens ``''``.
    """
    if op is None:
        return None
    getter = getattr(op, "get_rna_type", None)
    if not callable(getter):
        return None
    try:
        rna = getter()
    except Exception:
        return None
    props = getattr(rna, "properties", None) if rna is not None else None
    if props is None:
        return None
    ids = set()
    keys_fn = getattr(props, "keys", None)
    if callable(keys_fn):
        for ident in keys_fn():
            if ident != "rna_type":
                ids.add(ident)
        return ids
    for p in props:
        ident = getattr(p, "identifier", None)
        if ident and ident != "rna_type":
            ids.add(ident)
    return ids


def assert_required_paths(op_label, original, filtered, required=("filepath",)):
    """Never call export/save with a silently dropped or empty filepath."""
    for key in required:
        if key not in original:
            continue
        orig = original.get(key)
        got = filtered.get(key)
        orig_empty = orig is None or (isinstance(orig, str) and not str(orig).strip())
        got_empty = got is None or (isinstance(got, str) and not str(got).strip())
        if orig_empty:
            raise RuntimeError(
                "%s: required %r is empty (%r). Refusing to call with ''."
                % (op_label, key, orig)
            )
        if key not in filtered or got_empty:
            raise RuntimeError(
                "%s: required %r was dropped or emptied by RNA filter "
                "(got %r). Use bpy.ops.*.get_rna_type().properties, not "
                "Operator class bl_rna. Refusing to call with ''."
                % (op_label, key, got)
            )
    return filtered


def filter_op_kwargs(op, kwargs, required=("filepath",)):
    """Keep kwargs the live operator RNA accepts. Never drop a required path."""
    ids = operator_property_ids(op)
    if not ids:
        filtered = dict(kwargs)
    else:
        filtered = {k: v for k, v in kwargs.items() if k in ids}
    return assert_required_paths(_op_label(op), kwargs, filtered, required)


def _selftest_filepath_guard():
    try:
        assert_required_paths("gltf", {"filepath": "/tmp/x.glb"}, {}, ("filepath",))
        return "fail_did_not_raise_on_drop"
    except RuntimeError:
        pass
    try:
        assert_required_paths("gltf", {"filepath": "/tmp/x.glb"}, {"filepath": ""}, ("filepath",))
        return "fail_did_not_raise_on_empty"
    except RuntimeError:
        pass
    kept = assert_required_paths(
        "gltf", {"filepath": "/tmp/x.glb"}, {"filepath": "/tmp/x.glb"}, ("filepath",)
    )
    if kept.get("filepath") != "/tmp/x.glb":
        return "fail_did_not_keep"
    return "pass"


def make_principled(name, color, metallic, roughness):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = None
    for n in nt.nodes:
        if n.type == "BSDF_PRINCIPLED":
            bsdf = n
            break
    if bsdf is None:
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    def set_sock(keys, value):
        for k in keys:
            sock = bsdf.inputs.get(k)
            if sock is not None:
                sock.default_value = value
                return
    set_sock(("Base Color", "Base Color"), color)
    set_sock(("Metallic",), metallic)
    set_sock(("Roughness",), roughness)
    spec = 0.45 if metallic < 0.5 else 0.8
    if name == "M_Hair":
        spec = 0.08
    set_sock(("Specular IOR Level", "Specular"), spec)
    if "M_Robe" in name or name == "M_CyanGreen":
        set_sock(("Sheen Weight", "Sheen"), 0.25)
        set_sock(("Sheen Roughness",), 0.4)
    if name == "M_Feather":
        set_sock(("Sheen Weight", "Sheen"), 0.35)
        set_sock(("Coat Weight", "Clearcoat"), 0.08)
    if name == "M_Gold":
        set_sock(("Coat Weight", "Clearcoat"), 0.2)
    return mat


def mesh_to_object(m, mat_map, parent):
    verts = [v.xyz() for v in m.verts]
    faces = [tuple(f) for f in m.faces if len(f) >= 3]
    me = bpy.data.meshes.new(m.name)
    me.from_pydata(verts, [], faces)
    me.validate(clean_customdata=False)
    me.update()
    if m.smooth:
        for p in me.polygons:
            p.use_smooth = True
    try:
        uv = me.uv_layers.new(name="UVMap")
        if uv is not None:
            bb = m.bbox() or (0, 0, 0, 1, 1, 1)
            dx = bb[3] - bb[0] or 1.0
            dz = bb[5] - bb[2] or 1.0
            for loop in me.loops:
                co = me.vertices[loop.vertex_index].co
                uv.data[loop.index].uv = ((co.x - bb[0]) / dx, (co.z - bb[2]) / dz)
    except Exception:
        pass
    obj = bpy.data.objects.new(m.name, me)
    bpy.context.scene.collection.objects.link(obj)
    mat = mat_map.get(m.material)
    if mat:
        obj.data.materials.append(mat)
    if parent:
        obj.parent = parent
    return obj


def clear_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)
    for cam in list(bpy.data.cameras):
        bpy.data.cameras.remove(cam)
    for light in list(bpy.data.lights):
        bpy.data.lights.remove(light)


def look_at(obj, target):
    from mathutils import Vector

    loc = Vector(obj.location)
    tgt = Vector(target)
    direction = tgt - loc
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def setup_world(scene):
    world = bpy.data.worlds.new("PalaceWorld")
    scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs[0].default_value = (0.62, 0.55, 0.42, 1.0)
    bg.inputs[1].default_value = 0.35
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(bg.outputs[0], out.inputs[0])


def setup_lights():
    # Warm key from upper-left of a front (-Y) camera: +X, -Y, +Z
    def sun(name, loc, rot_deg, energy, color):
        data = bpy.data.lights.new(name, "SUN")
        data.energy = energy
        data.color = color
        obj = bpy.data.objects.new(name, data)
        obj.location = loc
        obj.rotation_euler = tuple(math.radians(a) for a in rot_deg)
        bpy.context.scene.collection.objects.link(obj)
        return obj

    def area(name, loc, size, energy, color, target):
        data = bpy.data.lights.new(name, "AREA")
        data.energy = energy
        data.color = color
        data.size = size
        obj = bpy.data.objects.new(name, data)
        obj.location = loc
        bpy.context.scene.collection.objects.link(obj)
        look_at(obj, target)
        return obj

    sun("Key_Warm", (2.4, -2.8, 4.2), (50, 0, -40), 5.2, (1.0, 0.91, 0.74))
    area("Fill_Cool", (-2.6, -1.4, 1.8), 2.4, 180.0, (0.55, 0.68, 1.0), (0, 0, 1.0))
    area("Rim_Warm", (0.6, 2.8, 2.4), 1.6, 90.0, (1.0, 0.85, 0.65), (0, 0, 1.1))


def _camera_basis(location, target):
    fwd = (target - location).nrm()
    up_w = V(0, 0, 1)
    right = fwd.cross(up_w)
    if right.length() < 1e-6:
        right = fwd.cross(V(0, 1, 0))
    right = right.nrm()
    up = right.cross(fwd).nrm()
    return fwd, right, up


def _fit_cam_distance(corners, view_from, target, lens_mm, res_x, res_y, sensor_w=36.0, ndc_limit=0.80):
    """Distance along view_from so the character AABB sits in the frame with 10% margin each side.

    ndc_limit 0.80 = 10% of the image empty on left/right/top/bottom.
    """
    aspect = res_x / float(res_y)
    fov_h = 2.0 * math.atan((sensor_w * 0.5) / float(lens_mm))
    tan_h = math.tan(fov_h * 0.5)
    tan_v = tan_h / aspect
    view_from = view_from.nrm()
    target = V(target)

    def fits(dist):
        loc = target + view_from * dist
        fwd, right, up = _camera_basis(loc, target)
        for p in corners:
            rel = p - loc
            z = rel.dot(fwd)
            if z < 0.08:
                return False
            ndc_x = (rel.dot(right) / z) / tan_h
            ndc_y = (rel.dot(up) / z) / tan_v
            if abs(ndc_x) > ndc_limit or abs(ndc_y) > ndc_limit:
                return False
        return True

    lo, hi = 0.5, 48.0
    if not fits(hi):
        return hi
    for _ in range(28):
        mid = 0.5 * (lo + hi)
        if fits(mid):
            hi = mid
        else:
            lo = mid
    return hi * 1.03


def _aabb_corners(bb):
    mn, mx = bb["min"], bb["max"]
    return [V(x, y, z) for x in (mn[0], mx[0]) for y in (mn[1], mx[1]) for z in (mn[2], mx[2])]


def _project_ndc(corners, loc, target, lens_mm, res_x, res_y, sensor_w=36.0):
    """Project AABB corners into camera NDC. |ndc|<=1 is the film; 0.80 is a 10% margin."""
    aspect = res_x / float(res_y)
    fov_h = 2.0 * math.atan((sensor_w * 0.5) / float(lens_mm))
    tan_h = math.tan(fov_h * 0.5)
    tan_v = tan_h / aspect
    loc = V(loc)
    target = V(target)
    fwd, right, up = _camera_basis(loc, target)
    xs, ys = [], []
    behind = 0
    for p in corners:
        rel = p - loc
        z = rel.dot(fwd)
        if z < 0.08:
            behind += 1
            continue
        xs.append(abs((rel.dot(right) / z) / tan_h))
        ys.append(abs((rel.dot(up) / z) / tan_v))
    max_x = max(xs) if xs else None
    max_y = max(ys) if ys else None
    in_margin = bool(xs) and behind == 0 and max_x <= 0.80 + 1e-6 and max_y <= 0.80 + 1e-6
    return {
        "max_abs_ndc_x": None if max_x is None else round(max_x, 4),
        "max_abs_ndc_y": None if max_y is None else round(max_y, 4),
        "behind_count": behind,
        "in_frame_10pct_margin": in_margin,
    }


def review_camera_plan(bb, res_x=1920, res_y=1080):
    """No-bpy preview of the four review cameras. Does not touch the palace stage."""
    if not bb or "min" not in bb or "max" not in bb:
        return None
    mn, mx = bb["min"], bb["max"]
    target = V(0.5 * (mn[0] + mx[0]), 0.5 * (mn[1] + mx[1]), 0.5 * (mn[2] + mx[2]))
    corners = _aabb_corners(bb)
    lens = 50.0
    el = math.radians(40.0)
    az = math.radians(22.0)
    lookdown_from = V(math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el))
    views = (
        ("Cam_Front", V(0.0, -1.0, 0.0)),
        ("Cam_Side", V(1.0, 0.0, 0.0)),
        ("Cam_Back", V(0.0, 1.0, 0.0)),
        ("Cam_LookDown", lookdown_from),
    )
    planned = {}
    for name, view_from in views:
        dist = _fit_cam_distance(corners, view_from, target, lens, res_x, res_y)
        loc = target + view_from.nrm() * dist
        ndc = _project_ndc(corners, loc, target, lens, res_x, res_y)
        planned[name] = {
            "distance_m": round(dist, 4),
            "location": [round(loc.x, 4), round(loc.y, 4), round(loc.z, 4)],
            "target": [round(target.x, 4), round(target.y, 4), round(target.z, 4)],
            "lens_mm": lens,
            **ndc,
        }
    # 9746c60 hardcoded cameras looked at z=0.95 with 55mm — guan/feet sat outside the film.
    legacy_front = _project_ndc(
        corners, V(0.0, -3.15, 1.55), V(0.0, 0.15, 0.95), 55.0, res_x, res_y
    )
    return {
        "margin": "10% on all four sides (ndc_limit 0.80)",
        "frames": "character AABB including guan and feet",
        "stage_enlarged_to_hide_crop": False,
        "palace_hidden_on_review_views": True,
        "neutral_ground": True,
        "palace_lookdown_extra": "view_lookdown_palace.png",
        "ndc_in_frame_is_not_enough": True,
        "views": planned,
        "legacy_9746c60_Cam_Front": {
            "location": [0.0, -3.15, 1.55],
            "target": [0.0, 0.15, 0.95],
            "lens_mm": 55.0,
            **legacy_front,
            "note": "Cropped guan/feet on Mac art review. Replaced by bbox-fit cameras.",
        },
    }


def setup_cameras(bb, res_x=1920, res_y=1080):
    """Review cameras (view_front/side/back/lookdown). Frame character bbox + 10% margin.

    Occlusion is handled at render time: palace is hidden, a neutral ground is shown.
    NDC-in-frame alone does not prevent railing from covering the feet.
    """
    if not bb:
        raise RuntimeError("setup_cameras requires the character bbox")
    mn, mx = bb["min"], bb["max"]
    target = V(0.5 * (mn[0] + mx[0]), 0.5 * (mn[1] + mx[1]), 0.5 * (mn[2] + mx[2]))
    corners = [
        V(x, y, z) for x in (mn[0], mx[0]) for y in (mn[1], mx[1]) for z in (mn[2], mx[2])
    ]
    lens = 50.0
    el = math.radians(40.0)
    az = math.radians(22.0)
    lookdown_from = V(math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el))
    views = (
        ("Cam_Front", V(0.0, -1.0, 0.0)),
        ("Cam_Side", V(1.0, 0.0, 0.0)),
        ("Cam_Back", V(0.0, 1.0, 0.0)),
        ("Cam_LookDown", lookdown_from),
    )
    cams = {}
    for name, view_from in views:
        dist = _fit_cam_distance(corners, view_from, target, lens, res_x, res_y)
        loc = target + view_from.nrm() * dist
        data = bpy.data.cameras.new(name)
        data.lens = lens
        data.sensor_width = 36.0
        data.sensor_fit = "HORIZONTAL"
        data.clip_start = 0.05
        data.clip_end = max(40.0, dist * 4.0)
        obj = bpy.data.objects.new(name, data)
        obj.location = (loc.x, loc.y, loc.z)
        bpy.context.scene.collection.objects.link(obj)
        look_at(obj, (target.x, target.y, target.z))
        cams[name] = obj
    return cams


def choose_eevee(scene):
    items = []
    try:
        items = [e.identifier for e in scene.render.bl_rna.properties["engine"].enum_items]
    except Exception:
        items = []
    for cand in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "CYCLES"):
        if not items or cand in items:
            scene.render.engine = cand
            return cand
    return scene.render.engine


def _under_root(obj, root):
    p = obj
    while p is not None:
        if p == root:
            return True
        p = p.parent
    return False


def export_glb_character_only(path, root_name="ZhugeLiang_Root"):
    """GLB is the independent character. Stage/cameras/lights stay in the .blend only."""
    root = bpy.data.objects.get(root_name)
    if root is None:
        raise RuntimeError("missing %s; cannot export a character-only GLB" % root_name)
    scene_col = bpy.context.scene.collection
    parked = []
    for obj in list(scene_col.objects):
        if not _under_root(obj, root):
            scene_col.objects.unlink(obj)
            parked.append(obj)
    try:
        if not path:
            raise RuntimeError("export_glb_character_only: filepath is empty; refusing to call gltf with ''")
        kwargs = filter_op_kwargs(
            bpy.ops.export_scene.gltf,
            {
                "filepath": path,
                "export_format": "GLB",
                "export_yup": True,
                "export_apply": True,
                "export_materials": "EXPORT",
                "export_cameras": False,
                "export_lights": False,
                "export_skins": False,
                "export_animations": False,
                "export_extras": False,
                "export_texcoords": True,
                "export_normals": True,
                "use_selection": False,
            },
        )
        bpy.ops.export_scene.gltf(**kwargs)
    finally:
        for obj in parked:
            try:
                scene_col.objects.link(obj)
            except RuntimeError:
                pass


def _set_hierarchy_hide_render(obj, hide):
    if obj is None:
        return
    stack = [obj]
    while stack:
        cur = stack.pop()
        cur.hide_render = hide
        stack.extend(list(cur.children))


def build_review_ground():
    """Flat disc under the figure. No railings. Not parented to the character (stays out of the GLB)."""
    n = 48
    m = Mesh("Review_Ground", "M_Stone", smooth=False)
    ci = m.add(V(0.0, 0.0, -0.002))
    ring = []
    for i in range(n):
        a = 2.0 * math.pi * i / n
        ring.append(m.add(V(math.cos(a) * 1.55, math.sin(a) * 1.55, -0.002)))
    for i in range(n):
        m.faces.append((ci, ring[i], ring[(i + 1) % n]))
    return m


def render_views(cams, output_dir, skip, palace=None, review=None):
    written = []
    if skip:
        return written
    scene = bpy.context.scene
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    mapping = (
        ("Cam_Front", "view_front.png"),
        ("Cam_Side", "view_side.png"),
        ("Cam_Back", "view_back.png"),
        ("Cam_LookDown", "view_lookdown.png"),
    )
    # Four review views: hide occluding palace (railings covered side/back feet). Neutral ground only.
    _set_hierarchy_hide_render(palace, True)
    _set_hierarchy_hide_render(review, False)
    for cam_name, fname in mapping:
        scene.camera = cams[cam_name]
        fp = safe_join(output_dir, fname)
        scene.render.filepath = fp
        bpy.ops.render.render(write_still=True)
        written.append(fname)
    # Separate palace lookdown fusion (character + 宫苑). Not a review-camera substitute.
    _set_hierarchy_hide_render(palace, False)
    _set_hierarchy_hide_render(review, True)
    scene.camera = cams["Cam_LookDown"]
    palace_name = "view_lookdown_palace.png"
    scene.render.filepath = safe_join(output_dir, palace_name)
    bpy.ops.render.render(write_still=True)
    written.append(palace_name)
    _set_hierarchy_hide_render(palace, False)
    _set_hierarchy_hide_render(review, False)
    return written


def write_report(path, payload):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def blender_build(args, char, env, stats):
    clear_scene()
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    setup_world(scene)
    mat_map = {}
    for name in MATERIALS:
        col, metal, rough = MAT_COLORS[name]
        mat_map[name] = make_principled(name, col, metal, rough)

    root = bpy.data.objects.new("ZhugeLiang_Root", None)
    bpy.context.scene.collection.objects.link(root)
    palace = bpy.data.objects.new("Palace_Root", None)
    bpy.context.scene.collection.objects.link(palace)
    review_root = bpy.data.objects.new("Review_Root", None)
    bpy.context.scene.collection.objects.link(review_root)

    for m in char:
        mesh_to_object(m, mat_map, root)
    for m in env:
        mesh_to_object(m, mat_map, palace)
    mesh_to_object(build_review_ground(), mat_map, review_root)

    setup_lights()
    char_bb = union_bbox_from_census(stats.get("character") or {})
    cams = setup_cameras(char_bb)
    engine = choose_eevee(scene)

    os.makedirs(args.output_dir, exist_ok=True)
    blend_name = "zhuge_liang_v2.blend"
    glb_name = "zhuge_liang_v2.glb"
    blend_path = safe_join(args.output_dir, blend_name)
    glb_path = safe_join(args.output_dir, glb_name)

    bpy.ops.wm.save_as_mainfile(
        **filter_op_kwargs(
            bpy.ops.wm.save_as_mainfile,
            {"filepath": blend_path, "check_existing": False},
        )
    )
    # Blend already has palace + cameras + lights. GLB unlinks those for the write only.
    export_glb_character_only(glb_path, "ZhugeLiang_Root")
    glb_measured = try_measure_glb(glb_path)
    renders = render_views(cams, args.output_dir, args.skip_render, palace=palace, review=review_root)

    report = build_report_payload(
        execution_kind="real",
        status="EXPORTED",
        blender_present=True,
        blender_version="%d.%d.%d" % tuple(bpy.app.version),
        engine=engine,
        stats=stats,
        outputs=[blend_name, glb_name] + renders,
        notes=[
            "Static posed meshes parented to ZhugeLiang_Root. No armature, no skin, no animation.",
            "Do not claim this character can walk.",
            "Screenshot count is not art approval; Codex reviews on Mac Blender 5.2.1.",
            "GLB is character-only (ZhugeLiang_Root). Stage/ground/cameras/lights/roof remain in the .blend.",
            "Review views hide Palace_Root and use Review_Ground. view_lookdown_palace.png is the 宫苑 fusion.",
            "Mac 2f8abf7 five-view: panels+cinch appeared. Overall FAIL — shoulder barrel, back gap, huge lotus fan, tube beard. This revision seals wrap+sash, scales vanes, flattens beard. Not a publish.",
        ],
        glb_measured=glb_measured,
    )
    write_report(safe_join(args.output_dir, "report.json"), report)
    return report


UNKNOWN = "UNKNOWN"


def union_bbox_from_census(cs):
    parts = cs.get("parts") or []
    mins = [None, None, None]
    maxs = [None, None, None]
    for p in parts:
        b = p.get("bbox")
        if not b or len(b) != 6:
            continue
        for i in range(3):
            mins[i] = b[i] if mins[i] is None else min(mins[i], b[i])
            maxs[i] = b[i + 3] if maxs[i] is None else max(maxs[i], b[i + 3])
    if mins[0] is None:
        return None
    return {"min": [round(v, 4) for v in mins], "max": [round(v, 4) for v in maxs]}


def construction_audit(char_stats):
    """Inventory of how the figure is built. NOT a connection proof. NOT art PASS.

    Mac e5282c0: bbox overlap / annulus / all_join_overlaps were treated as connected.
    Those are explicitly not used as pass criteria here.
    """
    names = [p["name"] for p in (char_stats.get("parts") or []) if p.get("name")]
    s = set(names)

    def has(n):
        return n in s

    return {
        "bbox_overlap_is_not_connection": True,
        "annulus_is_not_a_closed_root": True,
        "all_join_overlaps_is_not_pass": True,
        "do_not_claim_pass_from_this_audit": True,
        "one_robe_body": has("Robe_Body") and not has("Robe_Yoke") and not has("Robe_Torso"),
        "has_Robe_Body": has("Robe_Body"),
        "has_Robe_Yoke": has("Robe_Yoke"),
        "has_Robe_Torso": has("Robe_Torso"),
        "duplicate_shoulder_shells": has("Robe_Yoke") or has("Robe_Torso"),
        "sleeve_root_disk_caps": has("SleeveRootCap_L") and has("SleeveRootCap_R"),
        "no_shoulder_annulus_caps": not has("SleeveCapShoulder_L") and not has("SleeveCapShoulder_R"),
        "collar_chest_bands": has("Collar_L") and has("Collar_R") and "Collar" not in s,
        "collar_projected_on_robe_body": has("Collar_L") and has("Collar_R"),
        "standing_collar_covers_neck": has("CollarStand_R") and has("CollarStand_L"),
        "outer_robe_wrap": has("Robe_Panel_Outer"),
        "outer_shoulder_seal": has("Robe_Panel_ShoulderSeal"),
        "no_split_back_panels": not has("Robe_Panel_L") and not has("Robe_Panel_R"),
        "waist_sash": has("Sash_Band"),
        "hem_trim_from_skirt_outer": has("Trim_Hem") and has("Skirt_Outer"),
        "board_guan": has("Guan_Board_Center") and has("Guan_Board_Front"),
        "guan_crown": has("Guan_Crown"),
        "part_names": names,
        "note": (
            "Construction inventory only. Cloud has no Blender. "
            "This is not a Mac render and not art approval."
        ),
    }


def try_measure_glb(path):
    """Parse an exported GLB if present. Never invent numbers when the file is missing."""
    if not path or not os.path.isfile(path):
        return None
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    try:
        import validate_glb as vg

        gltf, blob, header = vg.read_glb(path)
        result = vg.check(gltf, blob, header, path)
        return {
            "upAxis": "Y",
            "upAxis_source": "gltf2_spec_convention",
            "forwardAxis": UNKNOWN,
            "bbox": result.get("aabb_world_yup") or UNKNOWN,
            "height": (
                round(result["aabb_world_yup"]["max"][1] - result["aabb_world_yup"]["min"][1], 4)
                if result.get("aabb_world_yup")
                else UNKNOWN
            ),
            "footOffset": (
                round(result["aabb_world_yup"]["min"][1], 4)
                if result.get("aabb_world_yup")
                else UNKNOWN
            ),
            "skin": bool(result.get("skins")),
            "animations": bool(result.get("animations")),
            "stage_nodes": result.get("stage_nodes") or [],
            "excludes_stage": not result.get("stage_nodes"),
            "rootName": "ZhugeLiang_Root" if result.get("has_ZhugeLiang_Root") else UNKNOWN,
        }
    except Exception:
        return None


def build_interface(char_stats, glb_measured=None):
    """Report contract: expected = generator/spec; measured_glb = UNKNOWN without a real GLB."""
    bb = union_bbox_from_census(char_stats)
    height_expected = None
    foot_expected = None
    if bb:
        height_expected = round(bb["max"][2] - bb["min"][2], 4)
        foot_expected = round(bb["min"][2], 4)
    m = glb_measured or {}

    def mget(key):
        if not m or key not in m:
            return UNKNOWN
        val = m[key]
        return UNKNOWN if val is None else val

    return {
        "units": "meters",
        "rootName": "ZhugeLiang_Root",
        "upAxis": {
            "expected_blender": "Z",
            "expected_glb": "Y",
            "measured_glb": mget("upAxis"),
            "measured_glb_source": m.get("upAxis_source", UNKNOWN) if m else UNKNOWN,
        },
        "forwardAxis": {
            "expected_blender": "-Y",
            "expected_glb": "+Z",
            "expected_note": "Face is built on Blender -Y. Blender glTF export_yup maps (X,Y,Z)_blender -> (X,Z,-Y)_gltf, so expected glTF forward is +Z. Not read from a GLB extra.",
            "measured_glb": mget("forwardAxis"),
        },
        "bbox": {
            "expected_blender_zup": bb if bb else UNKNOWN,
            "expected_note": "Generator vertex AABB in Blender Z-up meters. Not a GLB measurement.",
            "measured_glb_yup": mget("bbox"),
        },
        "height": {
            "expected_blender_m": height_expected if height_expected is not None else UNKNOWN,
            "expected_note": "generator max.z - min.z (includes guan). Design crown height is 1.8 m.",
            "measured_glb_m": mget("height"),
        },
        "footOffset": {
            "expected_blender_z_min": foot_expected if foot_expected is not None else UNKNOWN,
            "expected_note": "Interface snapshot of generator min Z. Foot-zero policy is owned by another Codex developer; this builder does not change that path.",
            "measured_glb_y_min": mget("footOffset"),
        },
        "skin": {
            "expected": False,
            "measured_glb": mget("skin") if m else UNKNOWN,
        },
        "animations": {
            "expected": False,
            "measured_glb": mget("animations") if m else UNKNOWN,
        },
        "glb_export": {
            "contents": "character_only",
            "rootName": "ZhugeLiang_Root",
            "includes_stage": False,
            "includes_ground": False,
            "includes_cameras": False,
            "includes_lights": False,
            "includes_roof_tiles": False,
            "stage_remains_in_blend": True,
            "excludes_stage_expected": True,
            "excludes_stage_measured": mget("excludes_stage") if m else UNKNOWN,
        },
    }


def build_report_payload(
    execution_kind,
    status,
    blender_present,
    blender_version,
    engine,
    stats,
    outputs,
    notes,
    static_checks=None,
    glb_measured=None,
):
    char_stats = stats.get("character", {})
    all_stats = stats.get("all", {})
    iface = build_interface(char_stats, glb_measured)
    # GLB is character-only; band applies to the character census, not the blend stage.
    tris = char_stats.get("tris")
    band = [20000, 45000]
    tris_note = None
    if isinstance(tris, int):
        if tris < band[0]:
            tris_note = "Under 20k tris — silhouette still has part volume; do not fake density."
        elif tris > band[1]:
            tris_note = (
                "Over 45k tris (%d). Kept fold/strand/vane density rather than decimating the look. Honest, not a fake mobile win."
                % tris
            )
        else:
            tris_note = "Inside 20k–45k target band (character GLB census; stage is .blend-only)."
    unfinished = [
        "No armature / no walk cycle (intentional for this static first version).",
        "Object origins are world-layout, not joint-centered — recenter before rigging.",
        "Roof glaze shares M_CyanGreen with robe trim/guan to stay at 8 materials (blend stage only).",
    ]
    if execution_kind != "real":
        unfinished.append("Cloud VM has no Blender; visual sign-off is Codex on Mac.")
        unfinished.append("GLB / .blend / view PNGs are absent until Blender 5.2.1 is re-run on this revision.")
        unfinished.append("GLB interface measured_* fields are UNKNOWN until a real export exists.")
        unfinished.append(
            "Mac 2f8abf7 exported (976024B, 42940 tris, 80 mesh, minY 0, issues=[]). "
            "KEEP: shoulder-sleeve inner closure, cameras, wrists/grip, output interface. "
            "Panels+cinch appeared. FAIL: lookdown outer barrel + back through-gap; fan covers face as lotus petals; "
            "beard is 3 shiny tubes with extra tail sticks. This handoff is those three items only. "
            "Cloud UNRUN. Structure inventory is not art PASS."
        )
    if tris_note and "Over 45k" in tris_note:
        unfinished.append(tris_note)
    return {
        "task_id": TASK_ID,
        "title": "诸葛亮真实三维人物 v2",
        "status": status,
        "execution_kind": execution_kind,
        "execution_kind_meaning": {
            "real": "This JSON was written by a Blender run that exported files.",
            "expected": "Cloud/static path. Codex must run Blender locally; numbers below are generator census or placeholders.",
        }[execution_kind if execution_kind in ("real", "expected") else "expected"],
        "blender_present": blender_present,
        "blender_version_expected": "5.2.1",
        "blender_version_actual": blender_version,
        "render_engine": engine,
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "mac_real_run": {
            "filepath_bug_commit": "64a0192232c16f94e3d162c0098986fecbfe0827",
            "export_ok_commit": "9746c6099a40168bbd87ee5d2c65f7bfd4276be2",
            "art_fail_then_framing_commit": "e5282c0bd63246ee616a19c49e8848d4496ab95c",
            "aae56dcd_commit": "aae56dcdf517eeedee60329d77d889589c0cbce4",
            "sculpt_base_commit": "176c7f39224d7d8aee203a66c7b79eb05ec1984b",
            "fail_2f8abf7_commit": "2f8abf7ef430c01af4dd0cae76ccc7baf9de1915",
            "blender": "5.2.1",
            "environment": "Mac factory-startup, background, independent output-dir",
            "mac_2f8abf7": {
                "exit": 0,
                "glb_bytes": 976024,
                "tris": 42940,
                "mesh": 80,
                "materials": 7,
                "minY": 0,
                "validator_issues": [],
                "keep": "shoulder-sleeve inner closure; cameras; wrists/grip; output interface",
                "appeared": "outer panels + waist cinch",
                "art_review": "FAIL",
                "published": False,
            },
            "mac_176c7f3": {
                "exit": 0,
                "glb_bytes": 780188,
                "tris": 33760,
                "mesh": 66,
                "materials": 7,
                "minY": 0,
                "validator_issues": [],
                "keep": "shoulder-sleeve closure; review cameras; wrists; output interface",
                "confirmed_better": "collar-on-chest; continuous cyan hem; front-readable fan",
                "art_review": "FAIL",
                "published": False,
            },
            "aae56dcd_mac": {
                "exit": 0,
                "glb_bytes": 816144,
                "tris": 35504,
                "mesh": 66,
                "materials": 7,
                "minY": 0,
                "validator_issues": [],
                "keep": "shoulder holes gone; side/back feet unobstructed; side feathers visible",
                "art_review": "CHANGES_REQUESTED",
                "published": False,
            },
            "e5282c0_mac": {
                "exit": 0,
                "glb_bytes": 917288,
                "tris": 39144,
                "mesh": 64,
                "materials": 7,
                "minY": 0,
                "skin": False,
                "animation": False,
                "validator_issues": [],
                "front_lookdown": "head+feet in frame, wrists at cuffs — real improvement",
                "art_review": "CHANGES_REQUESTED",
                "published": False,
            },
            "art_review": "FAIL",
            "art_approval": False,
            "art_rejection_176c7f3": [
                "Narrow column + smooth cone skirt — lookdown has no fold shading turns",
                "Fan vanes taper 0.05→0 as needle spikes",
                "Long bare neck",
                "Plastic barrel guan",
                "Wire / ponytail beard, not 3 volumetric bundles",
            ],
            "art_rejection_e5282c0": [
                "Side/back feet hidden by foreground railing — NDC-in-frame is not enough",
                "Lookdown still holes/folded edges on both shoulders",
                "Chest still large armor plates",
                "Annulus only sealed thickness rims; inner holes remain",
                "yoke/torso/collar independent lofts intersecting",
                "Soft gravity robe folds + waist transition still needed",
                "Fan spread / thin vanes; some side vanes disappear (normals)",
                "Beard still wires, not natural bundles",
                "Guan crown must not show holes",
            ],
            "art_rejection_aae56dcd": [
                "Collar is a floating X ribbon — not on Robe_Body",
                "Hem cyan trim broken floating chunks — old 48-seg contour vs BODY_N40 skirt",
                "Skirt front/back still a smooth cone; side waist has a step",
                "Front fan is a knife-edge (face yawed sideways); square stacked plates",
                "Beard still parallel hard rods",
            ],
            "art_rejection_2f8abf7": [
                "Lookdown outer robe: huge open barrel at shoulder top; two back panels with a through-gap",
                "Sash ellipse punched through panels as broken chunks",
                "Fan 0.385 m vanes cover mouth/nose, read as lotus petals",
                "Beard is 3 shiny thick tubes with extra long straight tail sticks",
            ],
            "this_commit_scope": "Three items only: (1) outer wrap grown from Robe_Body shoulder + back seam width 0 + sash on wrap waist ring; (2) long vane 0.385→0.26, width scaled, rachis tilted at hinge, wrist/grip untouched; (3) 3 flat-spindle beard bundles, delete tail tubes, M_Hair lower specular/higher roughness. KEEP inner shoulder-sleeve, cameras, wrists, interface. Not art approval. Recommend stop further enlargement of this class.",
            "this_cloud_status": "UNRUN",
            "valid_glb_on_cloud": False,
            "note": "2f8abf7 Mac export was real and overall art FAIL (barrel/gap/lotus fan/tube beard). This cloud did not re-export. Do not treat UNRUN JSON as art approval or as a new measured GLB.",
        },
        "units": iface["units"],
        "rootName": iface["rootName"],
        "root": iface["rootName"],
        "upAxis": iface["upAxis"],
        "forwardAxis": iface["forwardAxis"],
        "bbox": iface["bbox"],
        "height": iface["height"],
        "footOffset": iface["footOffset"],
        "skin": iface["skin"],
        "animations": iface["animations"],
        "glb_export": iface["glb_export"],
        "heads": HEADS,
        "height_m": HEIGHT,
        "feet_z_blender": FOOT_Z,
        "glb_yup_expected": True,
        "armature": {
            "present": False,
            "skins": False,
            "animations": False,
            "can_walk": False,
            "declaration": "Static first version. No armature. Do not claim it can walk.",
        },
        "materials_max": 8,
        "materials": list(MATERIALS),
        "tris_target_band": band,
        "tris_policy": "If look would clearly degrade to hit the band, keep quality and report honestly.",
        "tris_note": tris_note,
        "stats_character": {k: char_stats[k] for k in ("part_count", "verts", "tris", "material_count", "materials_used") if k in char_stats},
        "stats_all": {k: all_stats[k] for k in ("part_count", "verts", "tris", "material_count", "materials_used") if k in all_stats},
        "v1_baseline_planning_only": {
            "glb_bytes": 1722920,
            "primitives": 102,
            "materials": 8,
            "verts": 50313,
            "tris": 85068,
            "skin_animation": False,
            "blender_z_min": 0.14,
            "note": "v1 floated (Z min 0.14). v2 snaps character min Z to 0.",
        },
        "v1_rejection_addressed_in_construction": [
            "Head is dual-profile lathe + sockets/brow/nose/zygoma/jaw bumps — not an egg with geometric dots.",
            "Beard is layered tapering strand sweeps — not a cylinder.",
            "Guan has brim, crown folds, trail, hairpin — not a bucket.",
            "Robe is lofted with gravity folds + inner/outer skirt — not a smooth cone.",
            "Cuffs are a single swept band + gold piping — not jagged overlapping shells.",
            "Feathers are thin sheets with thickness and a vein ridge — not white sausages.",
        ],
        "art_approval": {
            "screenshot_count_is_not_approval": True,
            "this_handoff_claims_approval": False,
            "approval_authority": "Codex local review on Mac Blender 5.2.1",
            "mac_9746c60_art_review": "FAILED",
            "mac_e5282c0_art_review": "CHANGES_REQUESTED",
            "mac_aae56dcd_art_review": "CHANGES_REQUESTED",
            "mac_176c7f3_art_review": "FAIL",
            "mac_2f8abf7_art_review": "FAIL",
            "this_revision_art_approval": False,
            "structure_pass_is_not_art_pass": True,
        },
        "review_cameras": review_camera_plan(iface["bbox"].get("expected_blender_zup")),
        "construction_audit": construction_audit(char_stats),
        "outputs": outputs,
        "static_checks": static_checks or {},
        "notes": notes,
        "unfinished": unfinished,
    }


def source_guards(script_path):
    with open(script_path, "r", encoding="utf-8") as f:
        src = f.read()
    banned = (
        "primitive_uv_sphere" + "_add",
        "primitive_cone" + "_add",
        "primitive_cylinder" + "_add",
        "os" + ".remove(",
        "shutil" + ".rmtree(",
    )
    hits = [b for b in banned if b in src]
    return {
        "has_output_dir_flag": "--output-dir" in src,
        "has_dash_dash_argv": "argv_after_dash" in src,
        "banned_api_hits": hits,
        "root_name": "ZhugeLiang_Root" in src,
        "declares_no_walk": "can_walk" in src,
        "character_only_glb": "export_glb_character_only" in src,
        "uses_get_rna_type_filter": "get_rna_type" in src and "assert_required_paths" in src,
    }


def mesh_stats_main(args):
    char, env = assemble_all()
    dz = snap_feet(char)
    cs = census(char)
    es = census(env)
    allm = census(char + env)
    stats = {"character": cs, "environment": es, "all": allm, "snap_dz": dz}
    os.makedirs(args.output_dir, exist_ok=True)
    write_report(safe_join(args.output_dir, "mesh_stats.json"), stats)
    guards = source_guards(os.path.abspath(__file__))
    compile_ok = True
    compile_err = None
    try:
        import py_compile

        py_compile.compile(os.path.abspath(__file__), doraise=True)
        py_compile.compile(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "validate_glb.py"),
            doraise=True,
        )
    except Exception as exc:
        compile_ok = False
        compile_err = str(exc)
    report = build_report_payload(
        execution_kind="expected",
        status="UNRUN",
        blender_present=False,
        blender_version=None,
        engine=None,
        stats=stats,
        outputs=[],
        notes=[
            "Generator census only. No GLB/blend/png written because this was --mesh-stats or bpy is missing.",
            "Static posed meshes. No armature. Cannot walk.",
            "Mac 2f8abf7 overall art FAIL. This revision: wrap-seal + sash-on-ring, vane 0.26, flat-spindle beard. Cloud UNRUN.",
        ],
        static_checks={
            "mesh_stats": "written",
            "py_compile": "pass" if compile_ok else "fail",
            "py_compile_error": compile_err,
            "source_guards": guards,
            "filepath_guard": _selftest_filepath_guard(),
        },
    )
    write_report(safe_join(args.output_dir, "report.json"), report)
    print("mesh_stats character tris=%s verts=%s parts=%s" % (cs["tris"], cs["verts"], cs["part_count"]))
    print("mesh_stats all      tris=%s verts=%s mats=%s" % (allm["tris"], allm["verts"], allm["material_count"]))
    print("snap_dz", dz)
    return stats


def main():
    args = parse_cli()
    if args.mesh_stats or bpy is None:
        if bpy is None and not args.mesh_stats:
            print(
                "bpy not found. This script must run inside Blender 5.2.1:\n"
                "  blender -b -P build_zhuge_v2.py -- --output-dir DIR\n"
                "For a generator census without Blender:\n"
                "  python3 build_zhuge_v2.py --mesh-stats --output-dir DIR",
                file=sys.stderr,
            )
            # still emit census so the handoff is inspectable
            args.mesh_stats = True
        stats = mesh_stats_main(args)
        if bpy is None:
            return 0 if args.mesh_stats else 2
        # if blender + --mesh-stats, continue to export unless user only wanted stats
        if args.mesh_stats and not os.environ.get("ZHUGE_FORCE_EXPORT"):
            return 0

    char, env = assemble_all()
    snap_feet(char)
    stats = {
        "character": census(char),
        "environment": census(env),
        "all": census(char + env),
    }
    blender_build(args, char, env, stats)
    print("exported to", args.output_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
