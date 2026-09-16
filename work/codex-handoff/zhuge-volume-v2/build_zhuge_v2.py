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
SHOULDER_W = 0.235
CHEST_RX, CHEST_RY = 0.205, 0.155
WAIST_RX, WAIST_RY = 0.175, 0.130

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
    "M_Hair": ((0.03, 0.025, 0.02, 1.0), 0.02, 0.38),
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


def loft_closed(rings, name, material, smooth=True):
    m = Mesh(name, material, smooth=smooth)
    m.add_grid(rings, closed_u=True, closed_v=False)
    return m


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
    n = 28
    rings = []
    for k, (rx, ry, z) in enumerate(
        [
            (0.048, 0.046, CHIN_Z + 0.004),
            (0.050, 0.048, CHIN_Z - 0.025),
            (0.062, 0.055, SHOULDER_Z + 0.055),
        ]
    ):
        rings.append(ellipse_ring(0, 0, z, rx, ry, n))
    return loft_closed(rings, "Neck", "M_Skin")


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
    """诸葛巾: brim band, folded crown, hairpin volumes. Not a bucket."""
    parts = []
    n = 36
    # Headband / brim — sweep a thick rounded-rect around an oval, sitting on hairline
    band_path = ellipse_ring(0, 0.000, BROW_Z + 0.018, 0.095, 0.100, n)
    # order path as a loop — ellipse_ring is already closed logically; duplicate first
    band_path = band_path + [band_path[0]]
    brim = sweep_profile(
        band_path,
        _rounded_rect(0.034, 0.018, 4),
        "Guan_Brim",
        "M_CyanGreen",
        closed_profile=True,
    )
    parts.append(brim)

    # Crown: loft of scalloped (folded) closed profiles — wider mid, pinched top, not a cylinder
    crown_rings = []
    specs = [
        (0.090, 0.094, BROW_Z + 0.028, 6, 0.004),
        (0.100, 0.102, BROW_Z + 0.055, 6, 0.010),
        (0.104, 0.100, BROW_Z + 0.085, 6, 0.016),  # widest, fold ridges
        (0.092, 0.088, BROW_Z + 0.112, 6, 0.012),
        (0.062, 0.058, BROW_Z + 0.132, 6, 0.006),
        (0.018, 0.016, BROW_Z + 0.140, 0, 0.0),
    ]
    for rx, ry, z, fn, fa in specs:
        crown_rings.append(ellipse_ring(0, -0.004, z, rx, ry, n, fold_n=fn, fold_amp=fa / max(rx, 1e-6)))
    crown = loft_closed(crown_rings, "Guan_Crown", "M_CyanGreen")
    parts.append(crown)

    # Extra fold ridges as small tubes on the crown (cloth creases)
    folds = []
    for k in range(6):
        a = 2 * math.pi * k / 6 + 0.2
        path = []
        for t in range(8):
            tt = t / 7
            z = lerp(BROW_Z + 0.040, BROW_Z + 0.128, tt)
            r = lerp(0.102, 0.055, tt * tt) + 0.006 * math.sin(tt * math.pi)
            path.append(V(math.cos(a) * r, math.sin(a) * r - 0.004, z))
        folds.append(tube_along(path, lambda t: 0.0045 * (1.0 - 0.3 * t), 8, "Guan_Fold_%d" % k, "M_CyanGreen"))
    parts.append(merge_meshes("Guan_Folds", folds, "M_CyanGreen"))

    # Back knot / trailing cloth
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

    # Hairpin 簪 — lathe of a pin profile, then rotated to pierce the guan
    pin_prof = [
        (0.000, -0.095),
        (0.0028, -0.090),
        (0.0026, -0.020),
        (0.0032, 0.020),
        (0.0048, 0.055),
        (0.0090, 0.068),  # ornament
        (0.0070, 0.078),
        (0.000, 0.086),
    ]
    pin = lathe_rz(pin_prof, 12, "Guan_Hairpin", "M_Gold")
    # rotate around Y then Z so it lies along +X through the crown
    ca, sa = math.cos(math.pi / 2), math.sin(math.pi / 2)
    # currently along Z; map Z->X, Y->Y, X->-Z then lift
    for i, v in enumerate(pin.verts):
        # rot around Y: (z, y, -x) after 90° : x' = z, z' = -x
        x, y, z = v.z, v.y, -v.x
        pin.verts[i] = V(x, y - 0.01, z + BROW_Z + 0.078)
    parts.append(pin)
    # small jade bead at the ornamented end
    bead_prof = [(0.0, -0.007), (0.007, -0.003), (0.008, 0.0), (0.007, 0.003), (0.0, 0.007)]
    bead = lathe_rz(bead_prof, 12, "Guan_HairpinBead", "M_Gold")
    for i, v in enumerate(bead.verts):
        bead.verts[i] = V(v.x + 0.078, v.y - 0.01, v.z + BROW_Z + 0.078)
    parts.append(bead)
    return parts


def _beard_strand(origin, mid, tip, w0, th0, name, n_path=14, n_u=8):
    path = bezier([origin, origin.lerp(mid, 0.35) + V(0, 0.01, 0), mid, tip], n_path - 1)
    # slight gravity sag already in mid
    def rad(t):
        return max(0.0012, w0 * (1.0 - 0.88 * (t ** 1.15)))

    # flattened ellipse profile
    profile = []
    for j in range(n_u):
        a = 2 * math.pi * j / n_u
        profile.append((math.cos(a) * 1.0, math.sin(a) * (th0 / max(w0, 1e-6))))
    return sweep_profile(path, profile, name, "M_Hair", closed_profile=True, scale_fn=rad)


def build_beard():
    """Tapering bundled strands in layers. Not a cylinder."""
    parts = []
    # Layer A: mustache (two bundles)
    for bi, side in enumerate((1.0, -1.0)):
        for k in range(4):
            ox = side * (0.010 + k * 0.006)
            origin = V(ox, -0.078, MOUTH_Z - 0.004)
            mid = V(ox * 1.6 + side * 0.012, -0.055, MOUTH_Z - 0.045 - k * 0.008)
            tip = V(ox * 1.8 + side * 0.02, -0.030, MOUTH_Z - 0.085 - k * 0.012)
            parts.append(_beard_strand(origin, mid, tip, 0.0045, 0.0024, "Beard_Mustache_%d_%d" % (bi, k)))
    # Layer B: cheek connectors
    for bi, side in enumerate((1.0, -1.0)):
        for k in range(3):
            origin = V(side * (0.042 + k * 0.006), -0.050, MOUTH_Z + 0.012)
            mid = V(side * (0.050 + k * 0.004), -0.040, MOUTH_Z - 0.04)
            tip = V(side * (0.036 + k * 0.004), -0.028, MOUTH_Z - 0.09)
            parts.append(_beard_strand(origin, mid, tip, 0.004, 0.0022, "Beard_Cheek_%d_%d" % (bi, k)))
    # Layer C: the three long scholarly bundles (center + two)
    bundles = [
        (0.0, 0.0, 7),
        (0.018, 0.2, 6),
        (-0.018, -0.2, 6),
    ]
    for bi, (xoff, ph, nstr) in enumerate(bundles):
        for k in range(nstr):
            fx = xoff + (k - (nstr - 1) * 0.5) * 0.0065
            origin = V(fx * 0.7, -0.070, CHIN_Z + 0.012)
            sag = 0.04 + 0.012 * math.sin(k + ph)
            mid = V(fx * 1.4, -0.045 - sag * 0.3, CHEST_Z + 0.12 + 0.02 * math.cos(k))
            tip = V(fx * 1.8 + 0.01 * math.sin(k * 1.3), -0.02 - sag, CHEST_Z - 0.02 - 0.03 * (k % 3))
            w0 = 0.0055 if bi == 0 else 0.0048
            parts.append(_beard_strand(origin, mid, tip, w0, 0.0026, "Beard_Long_%d_%d" % (bi, k), n_path=16))
    # Layer D: short chin under-layer
    for k in range(5):
        fx = (k - 2) * 0.008
        origin = V(fx, -0.060, CHIN_Z + 0.004)
        tip = V(fx * 1.2, -0.048, CHIN_Z - 0.055)
        mid = origin.lerp(tip, 0.5) + V(0, -0.01, 0)
        parts.append(_beard_strand(origin, mid, tip, 0.0038, 0.002, "Beard_ChinUnder_%d" % k))
    return [
        merge_meshes("Beard_Mustache", [m for m in parts if m.name.startswith("Beard_Mustache")]),
        merge_meshes("Beard_Cheek", [m for m in parts if m.name.startswith("Beard_Cheek")]),
        merge_meshes("Beard_Long", [m for m in parts if m.name.startswith("Beard_Long")]),
        merge_meshes("Beard_ChinUnder", [m for m in parts if m.name.startswith("Beard_ChinUnder")]),
    ]


def build_torso_robe():
    """Ivory robe body with gravity folds. Not a smooth cone."""
    n = 40
    specs = [
        (0.155, 0.120, SHOULDER_Z + 0.04, 8, 0.008, 0.2),
        (0.185, 0.138, SHOULDER_Z - 0.04, 10, 0.012, 0.15),
        (CHEST_RX + 0.02, CHEST_RY + 0.012, CHEST_Z + 0.04, 10, 0.016, 0.1),
        (0.200, 0.155, CHEST_Z - 0.02, 10, 0.020, 0.18),
        (0.195, 0.150, CHEST_Z - 0.08, 10, 0.018, 0.15),
        (WAIST_RX + 0.028, WAIST_RY + 0.022, WAIST_Z + 0.08, 11, 0.017, 0.05),
        (WAIST_RX + 0.025, WAIST_RY + 0.02, WAIST_Z + 0.02, 10, 0.016, 0.0),
        (WAIST_RX + 0.03, WAIST_RY + 0.022, WAIST_Z - 0.02, 12, 0.018, 0.1),
    ]
    rings = []
    for rx, ry, z, fn, fa, ph in specs:
        rings.append(ellipse_ring(0, 0.01, z, rx, ry, n, fold_n=fn, fold_amp=fa / rx, fold_phase=ph))
    return loft_closed(rings, "Robe_Torso", "M_RobeIvory")


def build_collar():
    """交领 cross-collar, left panel on top (右衽), thick cyan-green edge later."""
    parts = []
    n = 18
    # two lapel strips as sweeps of thick cloth profile
    for name, side, y_sign, z_off in (
        ("Collar_Under_R", -1.0, 1.0, 0.0),
        ("Collar_Over_L", 1.0, 1.0, 0.006),
    ):
        path = poly_bezier(
            [
                V(side * 0.02, -0.11, SHOULDER_Z + 0.02),
                V(side * 0.08, -0.14, CHEST_Z + 0.08),
                V(side * 0.04, -0.16, CHEST_Z - 0.02),
                V(-side * 0.03, -0.10, WAIST_Z + 0.12),
            ],
            7,
        )
        parts.append(
            sweep_profile(
                path,
                _rounded_rect(0.055, 0.014, 3),
                name,
                "M_RobeIvory",
                closed_profile=True,
            )
        )
    return parts


def build_skirt():
    n = 48
    parts = []
    for layer, (z0, z1, rx0, ry0, rx1, ry1, folds, amp, name, mat) in enumerate(
        [
            (WAIST_Z - 0.01, HEM_Z + 0.012, WAIST_RX + 0.04, WAIST_RY + 0.03, 0.28, 0.22, 12, 0.045, "Skirt_Inner", "M_RobeIvory"),
            (WAIST_Z + 0.01, HEM_Z + 0.028, WAIST_RX + 0.05, WAIST_RY + 0.035, 0.265, 0.205, 12, 0.052, "Skirt_Outer", "M_RobeIvory"),
        ]
    ):
        rings = []
        nv = 14
        for i in range(nv):
            t = i / (nv - 1)
            # gravity: more flare and fold toward hem
            z = lerp(z0, z1, t)
            rx = lerp(rx0, rx1, t ** 0.85)
            ry = lerp(ry0, ry1, t ** 0.85)
            fa = (amp / rx) * (t ** 1.1)
            # extra back volume
            ring = []
            for j in range(n):
                a = 2 * math.pi * j / n
                rmod = 1.0 + fa * (0.35 + 0.65 * abs(math.sin(folds * 0.5 * a)))
                if math.sin(a) > 0:
                    rmod += 0.04 * t  # back drape
                ring.append(V(math.cos(a) * rx * rmod, math.sin(a) * ry * rmod + 0.02, z))
            rings.append(ring)
        m = loft_closed(rings, name, mat)
        parts.append(m)
    return parts


def _sleeve_path(side, raised):
    sh = V(side * SHOULDER_W, 0.02, SHOULDER_Z)
    if raised:
        # right arm holding fan — elbow forward-down, wrist at fan
        elbow = V(side * 0.32, -0.10, CHEST_Z - 0.02)
        wrist = V(side * 0.26, -0.16, CHEST_Z - 0.08)
        return poly_bezier([sh, V(side * 0.28, -0.02, SHOULDER_Z - 0.08), elbow, wrist], 8)
    # hanging left sleeve with gravity
    elbow = V(side * 0.38, -0.04, WAIST_Z + 0.12)
    cuff = V(side * 0.42, -0.08, HIP_Z + 0.02)
    return poly_bezier([sh, V(side * 0.30, 0.04, SHOULDER_Z - 0.12), elbow, cuff], 8)


def build_sleeves():
    parts = []
    for side, raised, tag in ((1.0, True, "R"), (-1.0, False, "L")):
        path = _sleeve_path(side, raised)
        # oval profile grows toward cuff, with fold waves
        n_u = 24
        T, N, B = bishop_frames(path)
        grid_outer = []
        grid_inner = []
        for i, p in enumerate(path):
            t = i / max(1, len(path) - 1)
            rx = lerp(0.055, 0.13 if not raised else 0.10, t ** 0.8)
            ry = lerp(0.045, 0.09 if not raised else 0.07, t ** 0.8)
            row_o, row_i = [], []
            for j in range(n_u):
                a = 2 * math.pi * j / n_u
                fold = 1.0 + 0.10 * abs(math.sin(4.0 * a + t * 2.0)) * (0.4 + 0.6 * t)
                # gravity hang: extra +down on lower half of sleeve
                hang = 0.0
                # B is roughly binormal; add a downward bias on the lower side
                world_down = V(0, 0, -1)
                q = N[i] * math.cos(a) + B[i] * math.sin(a)
                if q.dot(world_down) > 0:
                    hang = 0.012 * t * q.dot(world_down)
                po = p + N[i] * (math.cos(a) * rx * fold) + B[i] * (math.sin(a) * ry * fold) + world_down * hang
                pi = p + N[i] * (math.cos(a) * (rx * fold - 0.012)) + B[i] * (math.sin(a) * (ry * fold - 0.010))
                row_o.append(po)
                row_i.append(pi)
            grid_outer.append(row_o)
            grid_inner.append(row_i)
        outer = Mesh("Sleeve_%s" % tag, "M_RobeIvory")
        outer.add_grid(grid_outer, closed_u=True, closed_v=False)
        inner = Mesh("SleeveInner_%s" % tag, "M_RobeIvory")
        inner.add_grid(grid_inner, closed_u=True, closed_v=False, flip=True)
        parts.extend([outer, inner])
        # Clear cuff — single swept band, no jagged overlapping shells
        cuff_path = grid_outer[-1] + [grid_outer[-1][0]]
        # recenter slightly outward
        cuff = sweep_profile(
            cuff_path,
            _rounded_rect(0.038, 0.016, 4),
            "Cuff_%s" % tag,
            "M_CyanGreen",
            closed_profile=True,
        )
        parts.append(cuff)
        # gold piping rings at cuff outer edges (thin)
        for pi, scale in enumerate((1.02, 0.92)):
            ring_pts = []
            c0 = V(0, 0, 0)
            for q in grid_outer[-1]:
                c0 = c0 + q
            c0 = c0 * (1.0 / len(grid_outer[-1]))
            for q in grid_outer[-1]:
                ring_pts.append(c0 + (q - c0) * scale)
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


def build_trims():
    """Cyan-green thick hem + collar trim, little gold piping."""
    parts = []
    n = 48
    # hem band around outer skirt bottom
    z = HEM_Z + 0.042
    path = []
    for j in range(n):
        a = 2 * math.pi * j / n
        rmod = 1.0 + 0.18 * abs(math.sin(6.0 * a))
        path.append(V(math.cos(a) * 0.268 * rmod, math.sin(a) * 0.208 * rmod + 0.02, z))
    path.append(path[0])
    parts.append(
        sweep_profile(path, _rounded_rect(0.048, 0.014, 3), "Trim_Hem", "M_CyanGreen", True)
    )
    # gold piping on hem
    path_g = [V(p.x * 1.01, p.y * 1.01, p.z + 0.018) for p in path]
    parts.append(
        sweep_profile(
            path_g,
            [(math.cos(a) * 0.002, math.sin(a) * 0.002) for a in [2 * math.pi * k / 8 for k in range(8)]],
            "Trim_HemGold",
            "M_Gold",
            True,
        )
    )
    # collar trim along over-lapel
    cpath = poly_bezier(
        [
            V(0.02, -0.125, SHOULDER_Z + 0.03),
            V(0.09, -0.155, CHEST_Z + 0.09),
            V(0.05, -0.175, CHEST_Z - 0.01),
            V(-0.02, -0.12, WAIST_Z + 0.14),
        ],
        7,
    )
    parts.append(
        sweep_profile(cpath, _rounded_rect(0.022, 0.010, 3), "Trim_Collar", "M_CyanGreen", True)
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


# Fan handle placement — right hand grips this
FAN_ORIGIN = V(0.22, -0.18, CHEST_Z - 0.02)
FAN_DIR = V(-0.12, -0.42, 0.18).nrm()  # toward body/up, feathers fan the other way
FAN_HANDLE_LEN = 0.22
FAN_HANDLE_R = 0.009


def build_hands():
    """Fingers actually wrap the fan handle (right). Left relaxed on the robe."""
    parts = []
    # ----- Right hand: grip -----
    handle_p0 = FAN_ORIGIN
    axis = FAN_DIR
    # palm sits on +X side of handle
    radial = V(1, 0, 0)
    radial = (radial - axis * radial.dot(axis)).nrm()
    palm_c = handle_p0 + axis * (FAN_HANDLE_LEN * 0.42) + radial * (FAN_HANDLE_R + 0.018)
    # palm loft
    n = 16
    palm_rings = []
    for k, (rx, ry, along, out) in enumerate(
        [
            (0.028, 0.016, 0.01, 0.012),
            (0.038, 0.022, 0.04, 0.018),
            (0.032, 0.018, 0.07, 0.014),
        ]
    ):
        across = axis.cross(radial).nrm()
        c = handle_p0 + axis * (FAN_HANDLE_LEN * 0.28 + along) + radial * out
        ring = []
        for j in range(n):
            a = 2 * math.pi * j / n
            ring.append(c + across * (math.cos(a) * rx) + axis * (math.sin(a) * ry))
        palm_rings.append(ring)
    palm = loft_closed(palm_rings, "Hand_R_Palm", "M_Skin")
    parts.append(palm)

    def wrap_finger(name, start, start_radial, arc, lengths, rad0):
        # Fingertips march around the handle cylinder so the grip is a wrap, not a poke.
        r0 = (start - (handle_p0 + axis * axis.dot(start - handle_p0))).nrm()
        along0 = axis.dot(start - handle_p0)
        reach = FAN_HANDLE_R + rad0 + 0.004
        pts = []
        acc = 0.0
        dist_acc = 0.0
        pts.append(handle_p0 + axis * along0 + r0 * reach)
        for L in lengths:
            acc += arc / len(lengths)
            ca, sa = math.cos(acc), math.sin(acc)
            rvec = r0 * ca + axis.cross(r0) * sa + axis * r0.dot(axis) * (1 - ca)
            dist_acc += L
            along = along0 + dist_acc * 0.05
            pts.append(handle_p0 + axis * along + rvec.nrm() * reach)
        path = sample_polyline(pts, 8)
        return tube_along(path, lambda t: rad0 * (1.0 - 0.45 * t), 8, name, "M_Skin")

    # finger roots along palm (across axis)
    across = axis.cross(radial).nrm()
    roots = [
        ("Index", 0.028, 1.35, [0.028, 0.022, 0.018], 0.0075),
        ("Middle", 0.008, 1.50, [0.032, 0.024, 0.018], 0.0080),
        ("Ring", -0.012, 1.38, [0.028, 0.022, 0.016], 0.0072),
        ("Pinky", -0.030, 1.15, [0.022, 0.016, 0.012], 0.0060),
    ]
    base = handle_p0 + axis * (FAN_HANDLE_LEN * 0.38) + radial * (FAN_HANDLE_R + 0.016)
    for name, off, arc, lens, rad in roots:
        st = base + across * off + axis * 0.02
        parts.append(wrap_finger("Hand_R_%s" % name, st, radial, arc, lens, rad))
    # thumb opposes
    th_start = handle_p0 + axis * (FAN_HANDLE_LEN * 0.34) - across * 0.018 + radial * 0.01
    parts.append(wrap_finger("Hand_R_Thumb", th_start, -across * 0.4 + radial * 0.6, 1.2, [0.024, 0.018], 0.008))

    # ----- Left hand: relaxed, resting on abdomen -----
    lc = V(-0.12, -0.14, WAIST_Z + 0.14)
    lrings = []
    for rx, ry, z in ((0.026, 0.016, 0.0), (0.034, 0.020, 0.035), (0.028, 0.016, 0.065)):
        lrings.append(ellipse_ring(lc.x, lc.y, lc.z + z, rx, ry, 14))
    parts.append(loft_closed(lrings, "Hand_L_Palm", "M_Skin"))
    for i, (name, dx, dy) in enumerate(
        (("Index", 0.018, -0.02), ("Middle", 0.006, -0.028), ("Ring", -0.008, -0.022), ("Pinky", -0.020, -0.012), ("Thumb", 0.028, 0.012))
    ):
        path = [
            V(lc.x + dx, lc.y + dy * 0.2, lc.z + 0.06),
            V(lc.x + dx * 1.2, lc.y + dy, lc.z + 0.03),
            V(lc.x + dx * 1.3, lc.y + dy * 1.15, lc.z + 0.005),
        ]
        parts.append(tube_along(path, lambda t, r=0.007 if "Pinky" not in name else 0.0055: r * (1 - 0.4 * t), 8, "Hand_L_%s" % name, "M_Skin"))
    return parts


def build_fan():
    """White feather fan: thin vanes with thickness + veins. No sausage cylinders."""
    parts = []
    p0 = FAN_ORIGIN
    axis = FAN_DIR
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
    # map local Z-up cylinder onto FAN_DIR, origin at p0
    # build orthonormal
    zax = axis
    xax = V(1, 0, 0)
    if abs(zax.dot(xax)) > 0.9:
        xax = V(0, 1, 0)
    xax = zax.cross(xax).cross(zax).nrm()
    yax = zax.cross(xax).nrm()
    for i, v in enumerate(handle.verts):
        handle.verts[i] = p0 + xax * v.x + yax * v.y + zax * v.z
    parts.append(handle)
    # gold ferrule
    fprof = [(0.012, FAN_HANDLE_LEN * 0.88), (0.013, FAN_HANDLE_LEN * 0.93), (0.011, FAN_HANDLE_LEN * 0.99)]
    fer = lathe_rz(fprof, 12, "Fan_Ferrule", "M_Gold")
    for i, v in enumerate(fer.verts):
        fer.verts[i] = p0 + xax * v.x + yax * v.y + zax * v.z
    parts.append(fer)

    # Feathers radiate from ferrule, stacked by a small normal offset so vanes do not intersect
    n_feathers = 9
    spread = math.radians(78)
    fan_normal = xax  # stacking direction
    vane_up = (zax * 0.2 + V(0, 0, 1) * 0.8).nrm()
    # rebuild a plane: rachis mostly -Y / up from ferrule
    rachis_zero = (V(0, -0.15, 0.55)).nrm()
    # align rachis_zero to be roughly along -Y+Z from ferrule
    hinge = p1 - zax * 0.01
    vanes = []
    for fi in range(n_feathers):
        t = fi / (n_feathers - 1)  # 0..1
        ang = (t - 0.5) * spread
        # rotate rachis_zero around fan_normal
        ca, sa = math.cos(ang), math.sin(ang)
        rdir = rachis_zero * ca + fan_normal.cross(rachis_zero) * sa + fan_normal * fan_normal.dot(rachis_zero) * (1 - ca)
        rdir = rdir.nrm()
        stack = fan_normal * ((fi - (n_feathers - 1) * 0.5) * 0.0032)
        length = 0.34 - 0.02 * abs(t - 0.5)
        # rachis curve with slight droop
        rachis = bezier(
            [
                hinge + stack,
                hinge + stack + rdir * (length * 0.35) + V(0, 0, 0.01),
                hinge + stack + rdir * (length * 0.7) + V(0, 0, -0.01),
                hinge + stack + rdir * length + V(0, 0, -0.025),
            ],
            12,
        )
        T, N, B = bishop_frames(rachis)
        nu, nv = 10, len(rachis)

        def width_at(tt):
            # real vane envelope: narrow quill, max ~0.38, taper to a point
            if tt < 0.12:
                return lerp(0.006, 0.028, tt / 0.12)
            env = math.sin(math.pi * ((tt - 0.12) / 0.88) ** 0.75)
            return 0.028 + 0.038 * env

        grid = []
        for i, p in enumerate(rachis):
            tt = i / max(1, nv - 1)
            w = width_at(tt)
            # flatten: use a side vector perpendicular to T, mostly in horizontal fan
            side = B[i]
            if abs(side.dot(V(0, 0, 1))) > 0.7:
                side = N[i]
            # keep side in plane perpendicular to T
            side = T[i].cross(V(0, 0, 1) if abs(T[i].z) < 0.9 else fan_normal).nrm()
            nrm = T[i].cross(side).nrm()
            row = []
            for j in range(nu):
                u = j / (nu - 1) * 2.0 - 1.0  # -1..1
                # vane outline slightly pointed
                ww = w * math.sqrt(max(0.0, 1.0 - 0.15 * u * u))
                # vein ridge: thinner at edges
                th = 0.00115 * (1.0 - 0.55 * abs(u)) * (1.0 - 0.25 * tt)
                if abs(u) < 0.10:
                    th += 0.0018 * (1.0 - abs(u) / 0.10)  # rachis vein
                row.append(p + side * (u * ww) + nrm * (th * 0.5))
            grid.append(row)

        def thick(tt, uu):
            u = uu * 2 - 1
            base = 0.0013 * (1.0 - 0.5 * abs(u)) * (1.0 - 0.2 * tt)
            if abs(u) < 0.1:
                base += 0.0020 * (1.0 - abs(u) / 0.1)
            return base

        vanes.append(thicken_sheet(grid, thick, "Fan_Feather_%d" % fi, "M_Feather"))
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
    char.extend(build_hair())
    char.extend(build_guan())
    char.extend(build_beard())
    char.append(build_torso_robe())
    char.extend(build_collar())
    char.extend(build_skirt())
    char.extend(build_sleeves())
    char.extend(build_trims())
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
def filter_op_kwargs(type_name, kwargs):
    cls = getattr(bpy.types, type_name, None) if bpy else None
    if cls is None:
        return kwargs
    valid = {p.identifier for p in cls.bl_rna.properties if p.identifier != "rna_type"}
    return {k: v for k, v in kwargs.items() if k in valid}


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
    set_sock(("Specular IOR Level", "Specular"), 0.45 if metallic < 0.5 else 0.8)
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


def setup_cameras():
    cams = {}
    specs = {
        "Cam_Front": ((0.0, -3.15, 1.55), (0.0, 0.15, 0.95), 55),
        "Cam_Side": ((3.2, -0.15, 1.45), (0.0, 0.0, 0.95), 55),
        "Cam_Back": ((0.0, 3.35, 1.55), (0.0, 0.4, 0.95), 55),
        "Cam_LookDown": ((1.55, -2.15, 2.45), (0.0, 0.25, 0.85), 50),
    }
    for name, (loc, tgt, lens) in specs.items():
        data = bpy.data.cameras.new(name)
        data.lens = lens
        obj = bpy.data.objects.new(name, data)
        obj.location = loc
        bpy.context.scene.collection.objects.link(obj)
        look_at(obj, tgt)
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


def export_glb(path):
    kwargs = filter_op_kwargs(
        "EXPORT_SCENE_OT_gltf",
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


def render_views(cams, output_dir, skip):
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
    for cam_name, fname in mapping:
        scene.camera = cams[cam_name]
        fp = safe_join(output_dir, fname)
        scene.render.filepath = fp
        bpy.ops.render.render(write_still=True)
        written.append(fname)
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

    for m in char:
        mesh_to_object(m, mat_map, root)
    for m in env:
        mesh_to_object(m, mat_map, palace)

    setup_lights()
    cams = setup_cameras()
    engine = choose_eevee(scene)

    os.makedirs(args.output_dir, exist_ok=True)
    blend_name = "zhuge_liang_v2.blend"
    glb_name = "zhuge_liang_v2.glb"
    blend_path = safe_join(args.output_dir, blend_name)
    glb_path = safe_join(args.output_dir, glb_name)

    bpy.ops.wm.save_as_mainfile(**filter_op_kwargs("WM_OT_save_as_mainfile", {"filepath": blend_path, "check_existing": False}))
    export_glb(glb_path)
    renders = render_views(cams, args.output_dir, args.skip_render)

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
        ],
    )
    write_report(safe_join(args.output_dir, "report.json"), report)
    return report


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
):
    char_stats = stats.get("character", {})
    all_stats = stats.get("all", {})
    tris = all_stats.get("tris")
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
            tris_note = "Inside 20k–45k target band."
    unfinished = [
        "No armature / no walk cycle (intentional for this static first version).",
        "Object origins are world-layout, not joint-centered — recenter before rigging.",
        "Roof glaze shares M_CyanGreen with robe trim/guan to stay at 8 materials.",
    ]
    if execution_kind != "real":
        unfinished.append("Cloud VM has no Blender; visual sign-off is Codex on Mac.")
        unfinished.append("GLB / .blend / view PNGs are absent until Blender 5.2.1 is run.")
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
        "units": "meters",
        "height_m": HEIGHT,
        "heads": HEADS,
        "feet_z_blender": FOOT_Z,
        "glb_yup_expected": True,
        "root": "ZhugeLiang_Root",
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
        },
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
        ],
        static_checks={
            "mesh_stats": "written",
            "py_compile": "pass" if compile_ok else "fail",
            "py_compile_error": compile_err,
            "source_guards": guards,
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
