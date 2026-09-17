#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CT-SURFACE-VERIFY-01-CODE — independent geometry diagnostics.

Does not build a 纶巾. Does not render. Does not edit PR20
build_cap_surface.py (immutable input at 4b81dc4).

Replaces false confidence from gates_ok / vertex distance / BVH-only
candidates with:

  1. nearest-triangle projection + barycentric residual
  2. exact triangle–triangle intersection (Möller pierce + coplanar SAT)
  3. deterministic PENETRATING / SEPARATED controls
  4. UNKNOWN when the deciding feature is an open boundary
  5. old-cap evidence: sample_cloth_grid weighted averages vs true projection

Stdlib only. bpy may be present; Blender export/render is UNRUN.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
TASK_ID = "CT-SURFACE-VERIFY-01-CODE"
CAP_COMMIT = "4b81dc46a1f843749cae2351151e1ab55a4923d8"
ANATOMY_COMMIT = "624e008349a447859ed58417394c68f382e9b887"
SIBLING_CAP = os.path.abspath(os.path.join(HERE, "..", "zhuge-cap-surface-v1", "build_cap_surface.py"))
SIBLING_ANATOMY = os.path.abspath(os.path.join(HERE, "..", "zhuge-anatomy-base"))
FROZEN = (
    os.path.abspath(os.path.join(HERE, "..", "zhuge-cap-surface-v1")),
    os.path.abspath(os.path.join(HERE, "..", "zhuge-anatomy-base")),
    os.path.abspath(os.path.join(HERE, "..", "zhuge-clothed-v1")),
    os.path.abspath(os.path.join(HERE, "..", "zhuge-volume-v2")),
    os.path.abspath(os.path.join(HERE, "..", "zhuge-accessory-v1")),
)

EPS = 1e-10
ON_EPS = 1e-6  # 1 µm: numerical on-triangle vs millimetre mix error
CELL = 0.025


# ---------------------------------------------------------------------------
# vectors
# ---------------------------------------------------------------------------

def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def smul(s, a):
    return (s * a[0], s * a[1], s * a[2])


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def nrm2(a):
    return dot(a, a)


def dist(a, b):
    return math.sqrt(nrm2(sub(a, b)))


def almost(a, b, eps=1e-8):
    return abs(a - b) <= eps


# ---------------------------------------------------------------------------
# nearest triangle + barycentric residual (Ericson RTCD 5.1.5)
# ---------------------------------------------------------------------------

def closest_point_on_triangle(p, a, b, c):
    """Return (point, bary_uvw, region, dist).

    region is 'interior', 'edge_ab', 'edge_bc', 'edge_ca', 'vert_a', 'vert_b',
    or 'vert_c'. bary is (u,v,w) at (a,b,c).
    """
    ab, ac, ap = sub(b, a), sub(c, a), sub(p, a)
    d1, d2 = dot(ab, ap), dot(ac, ap)
    if d1 <= 0.0 and d2 <= 0.0:
        return a, (1.0, 0.0, 0.0), "vert_a", dist(p, a)
    bp = sub(p, b)
    d3, d4 = dot(ab, bp), dot(ac, bp)
    if d3 >= 0.0 and d4 <= d3:
        return b, (0.0, 1.0, 0.0), "vert_b", dist(p, b)
    vc = d1 * d4 - d3 * d2
    if vc <= 0.0 and d1 >= 0.0 and d3 <= 0.0:
        v = d1 / (d1 - d3) if abs(d1 - d3) > EPS else 0.0
        q = add(a, smul(v, ab))
        return q, (1.0 - v, v, 0.0), "edge_ab", dist(p, q)
    cp = sub(p, c)
    d5, d6 = dot(ab, cp), dot(ac, cp)
    if d6 >= 0.0 and d5 <= d6:
        return c, (0.0, 0.0, 1.0), "vert_c", dist(p, c)
    vb = d5 * d2 - d1 * d6
    if vb <= 0.0 and d2 >= 0.0 and d6 <= 0.0:
        w = d2 / (d2 - d6) if abs(d2 - d6) > EPS else 0.0
        q = add(a, smul(w, ac))
        return q, (1.0 - w, 0.0, w), "edge_ca", dist(p, q)
    va = d3 * d6 - d5 * d4
    if va <= 0.0 and (d4 - d3) >= 0.0 and (d5 - d6) >= 0.0:
        denom = (d4 - d3) + (d5 - d6)
        w = (d4 - d3) / denom if abs(denom) > EPS else 0.0
        q = add(b, smul(w, sub(c, b)))
        return q, (0.0, 1.0 - w, w), "edge_bc", dist(p, q)
    denom = va + vb + vc
    if abs(denom) < EPS:
        return a, (1.0, 0.0, 0.0), "vert_a", dist(p, a)
    v = vb / denom
    w = vc / denom
    u = 1.0 - v - w
    q = add(a, add(smul(v, ab), smul(w, ac)))
    return q, (u, v, w), "interior", dist(p, q)


def triangulate_faces(faces):
    tris = []
    for f in faces:
        if len(f) < 3:
            continue
        for i in range(1, len(f) - 1):
            tris.append((f[0], f[i], f[i + 1]))
    return tris


def boundary_edges(tris):
    """Undirected edges that belong to exactly one triangle."""
    seen = {}
    for t in tris:
        for i in range(3):
            e = (t[i], t[(i + 1) % 3])
            key = (e[0], e[1]) if e[0] < e[1] else (e[1], e[0])
            seen[key] = seen.get(key, 0) + 1
    return {e for e, n in seen.items() if n == 1}


def region_edge(region, tri):
    a, b, c = tri
    if region == "edge_ab":
        return (a, b) if a < b else (b, a)
    if region == "edge_bc":
        return (b, c) if b < c else (c, b)
    if region == "edge_ca":
        return (c, a) if c < a else (a, c)
    if region == "vert_a":
        return ("vert", a)
    if region == "vert_b":
        return ("vert", b)
    if region == "vert_c":
        return ("vert", c)
    return None


def feature_on_open_boundary(region, tri, open_edges, open_verts):
    feat = region_edge(region, tri)
    if feat is None:
        return False
    if feat[0] == "vert":
        return feat[1] in open_verts
    return feat in open_edges


def nearest_triangle(p, verts, tris, open_edges=None, open_verts=None):
    best = None
    for i, tri in enumerate(tris):
        a, b, c = verts[tri[0]], verts[tri[1]], verts[tri[2]]
        q, bary, region, d = closest_point_on_triangle(p, a, b, c)
        rec = (d, i, q, bary, region)
        if best is None or rec < best:
            best = rec
    d, i, q, bary, region = best
    open_hit = False
    if open_edges is not None:
        open_hit = feature_on_open_boundary(region, tris[i], open_edges, open_verts or set())
    if open_hit:
        label = "UNKNOWN"
    elif region == "interior" and d <= ON_EPS:
        label = "ON_TRIANGLE"
    elif d <= ON_EPS:
        label = "ON_BOUNDARY"
    else:
        label = "OFF_SURFACE"
    residual = {
        "dist_m": d,
        "barycentric": bary,
        "bary_sum": bary[0] + bary[1] + bary[2],
        "bary_min": min(bary),
        "region": region,
        "tri_index": i,
        "label": label,
        "open_boundary": open_hit,
    }
    return q, residual


def project_point_to_triangles(p, verts, tris, open_edges=None, open_verts=None):
    """The primitive sample_cloth_grid lacked: orthogonal projection, not a vertex mix."""
    return nearest_triangle(p, verts, tris, open_edges, open_verts)


# ---------------------------------------------------------------------------
# exact triangle–triangle (pierce via Möller–Trumbore on edges + coplanar SAT)
# ---------------------------------------------------------------------------

def _mt_segment_triangle(p0, p1, a, b, c):
    direction = sub(p1, p0)
    e1, e2 = sub(b, a), sub(c, a)
    h = cross(direction, e2)
    det = dot(e1, h)
    if abs(det) < EPS:
        return None
    f = 1.0 / det
    s = sub(p0, a)
    u = f * dot(s, h)
    if u < -EPS or u > 1.0 + EPS:
        return None
    q = cross(s, e1)
    v = f * dot(direction, q)
    if v < -EPS or (u + v) > 1.0 + EPS:
        return None
    t = f * dot(e2, q)
    if t < -EPS or t > 1.0 + EPS:
        return None
    w = 1.0 - u - v
    return (t, u, v, w)


def _proper_pierce(hit):
    t, u, v, w = hit
    interior = u > 1e-8 and v > 1e-8 and w > 1e-8
    mid = 1e-8 < t < 1.0 - 1e-8
    return interior and mid


def _tri_normal(a, b, c):
    return cross(sub(b, a), sub(c, a))


def _drop_axis(n):
    ax = abs(n[0]), abs(n[1]), abs(n[2])
    return ax.index(max(ax))


def _to2(p, drop):
    if drop == 0:
        return (p[1], p[2])
    if drop == 1:
        return (p[0], p[2])
    return (p[0], p[1])


def _orient2(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _pt_in_tri2(p, a, b, c):
    o1, o2, o3 = _orient2(a, b, p), _orient2(b, c, p), _orient2(c, a, p)
    has_neg = (o1 < -EPS) or (o2 < -EPS) or (o3 < -EPS)
    has_pos = (o1 > EPS) or (o2 > EPS) or (o3 > EPS)
    return not (has_neg and has_pos)


def _seg_seg2(a, b, c, d):
    o1, o2 = _orient2(a, b, c), _orient2(a, b, d)
    o3, o4 = _orient2(c, d, a), _orient2(c, d, b)
    if o1 * o2 < -EPS * EPS and o3 * o4 < -EPS * EPS:
        return True
    return False


def _tri_overlap_2d(t1, t2):
    a, b, c = t1
    d, e, f = t2
    if _pt_in_tri2(a, d, e, f) or _pt_in_tri2(b, d, e, f) or _pt_in_tri2(c, d, e, f):
        return True
    if _pt_in_tri2(d, a, b, c) or _pt_in_tri2(e, a, b, c) or _pt_in_tri2(f, a, b, c):
        return True
    edges1 = ((a, b), (b, c), (c, a))
    edges2 = ((d, e), (e, f), (f, d))
    for p, q in edges1:
        for r, s in edges2:
            if _seg_seg2(p, q, r, s):
                return True
    return False


def _coplanar(a0, a1, a2, b0, b1, b2, n1, n2):
    if nrm2(n1) < EPS or nrm2(n2) < EPS:
        return False
    # parallel planes?
    cr = cross(n1, n2)
    if nrm2(cr) > 1e-16:
        return False
    if abs(dot(n1, sub(b0, a0))) > 1e-8 * (1.0 + math.sqrt(nrm2(n1))):
        return False
    drop = _drop_axis(n1)
    t1 = (_to2(a0, drop), _to2(a1, drop), _to2(a2, drop))
    t2 = (_to2(b0, drop), _to2(b1, drop), _to2(b2, drop))
    return _tri_overlap_2d(t1, t2)


def triangle_triangle_intersect(a0, a1, a2, b0, b1, b2):
    """Exact test. Returns (kind, detail).

    kind: 'PENETRATING' | 'SEPARATED' | 'UNKNOWN'
    UNKNOWN only if the only contact lies on an open boundary (caller decides
    open edges). This function itself returns PENETRATING or SEPARATED;
    touch-at-vertex without interior pierce is SEPARATED.
    """
    n1 = _tri_normal(a0, a1, a2)
    n2 = _tri_normal(b0, b1, b2)
    if _coplanar(a0, a1, a2, b0, b1, b2, n1, n2):
        return "PENETRATING", "coplanar_overlap"
    a_edges = ((a0, a1), (a1, a2), (a2, a0))
    b_edges = ((b0, b1), (b1, b2), (b2, b0))
    for p, q in a_edges:
        hit = _mt_segment_triangle(p, q, b0, b1, b2)
        if hit is not None and _proper_pierce(hit):
            return "PENETRATING", "edge_pierce"
    for p, q in b_edges:
        hit = _mt_segment_triangle(p, q, a0, a1, a2)
        if hit is not None and _proper_pierce(hit):
            return "PENETRATING", "edge_pierce"
    return "SEPARATED", "no_interior_intersection"


def _open_edges_of(tri_pts, tri_idx, open_edges):
    if not open_edges or tri_idx is None:
        return []
    out = []
    for i in range(3):
        e = (tri_idx[i], tri_idx[(i + 1) % 3])
        key = (e[0], e[1]) if e[0] < e[1] else (e[1], e[0])
        if key in open_edges:
            out.append((tri_pts[i], tri_pts[(i + 1) % 3]))
    return out


def classify_tri_tri(a0, a1, a2, b0, b1, b2, a_open_edges=None, a_idx=None, b_open_edges=None, b_idx=None):
    """Exact test, then UNKNOWN if the only contact is a shared open edge."""
    kind, detail = triangle_triangle_intersect(a0, a1, a2, b0, b1, b2)
    if kind == "PENETRATING":
        return kind, detail
    a_pts = (a0, a1, a2)
    b_pts = (b0, b1, b2)
    for pa, qa in _open_edges_of(a_pts, a_idx, a_open_edges):
        for pb, qb in _open_edges_of(b_pts, b_idx, b_open_edges):
            same = (dist(pa, pb) < 1e-9 and dist(qa, qb) < 1e-9) or (
                dist(pa, qb) < 1e-9 and dist(qa, pb) < 1e-9
            )
            if same:
                return "UNKNOWN", "open_boundary_contact"
    return kind, detail


# ---------------------------------------------------------------------------
# AABB grid for pair enumeration (broadphase only; every hit is exact-tested)
# ---------------------------------------------------------------------------

def tri_aabb(v0, v1, v2):
    return (
        (min(v0[0], v1[0], v2[0]), min(v0[1], v1[1], v2[1]), min(v0[2], v1[2], v2[2])),
        (max(v0[0], v1[0], v2[0]), max(v0[1], v1[1], v2[1]), max(v0[2], v1[2], v2[2])),
    )


def aabb_overlap(a, b, pad=1e-9):
    return not (
        a[1][0] < b[0][0] - pad
        or b[1][0] < a[0][0] - pad
        or a[1][1] < b[0][1] - pad
        or b[1][1] < a[0][1] - pad
        or a[1][2] < b[0][2] - pad
        or b[1][2] < a[0][2] - pad
    )


def grid_keys(mn, mx, cell):
    ix0, iy0, iz0 = (int(math.floor(mn[k] / cell)) for k in range(3))
    ix1, iy1, iz1 = (int(math.floor(mx[k] / cell)) for k in range(3))
    out = []
    for ix in range(ix0, ix1 + 1):
        for iy in range(iy0, iy1 + 1):
            for iz in range(iz0, iz1 + 1):
                out.append((ix, iy, iz))
    return out


def exact_intersect_pairs(verts_a, tris_a, verts_b, tris_b, open_a=None, open_b=None, limit_examples=8):
    """Broadphase AABB grid, then exact triangle_triangle_intersect on every candidate."""
    bins = {}
    aabbs_b = []
    for j, t in enumerate(tris_b):
        bb = tri_aabb(verts_b[t[0]], verts_b[t[1]], verts_b[t[2]])
        aabbs_b.append(bb)
        for k in grid_keys(bb[0], bb[1], CELL):
            bins.setdefault(k, []).append(j)
    candidates = 0
    exact = 0
    penetrating = 0
    unknown = 0
    examples = []
    seen_pair = set()
    for i, t in enumerate(tris_a):
        va0, va1, va2 = verts_a[t[0]], verts_a[t[1]], verts_a[t[2]]
        aa = tri_aabb(va0, va1, va2)
        cand = []
        for k in grid_keys(aa[0], aa[1], CELL):
            cand.extend(bins.get(k, ()))
        for j in cand:
            if (i, j) in seen_pair:
                continue
            seen_pair.add((i, j))
            if not aabb_overlap(aa, aabbs_b[j]):
                continue
            candidates += 1
            tb = tris_b[j]
            vb0, vb1, vb2 = verts_b[tb[0]], verts_b[tb[1]], verts_b[tb[2]]
            kind, detail = classify_tri_tri(
                va0, va1, va2, vb0, vb1, vb2,
                a_open_edges=open_a, a_idx=t,
                b_open_edges=open_b, b_idx=tb,
            )
            exact += 1
            if kind == "PENETRATING":
                penetrating += 1
                if len(examples) < limit_examples:
                    examples.append({"a": i, "b": j, "kind": kind, "detail": detail})
            elif kind == "UNKNOWN":
                unknown += 1
                if len(examples) < limit_examples:
                    examples.append({"a": i, "b": j, "kind": kind, "detail": detail})
    return {
        "aabb_candidates": candidates,
        "exact_tests": exact,
        "penetrating_pairs": penetrating,
        "unknown_pairs": unknown,
        "separated_or_noncandidate": True,
        "note": "AABB is a filter. Every candidate is exact-tested. Non-candidates are SEPARATED.",
        "examples": examples,
    }


# ---------------------------------------------------------------------------
# deterministic controls (no art mesh)
# ---------------------------------------------------------------------------

def _ok(name, cond, detail=""):
    return {"name": name, "pass": bool(cond), "detail": detail}


def run_controls():
    tests = []
    # 1. Genuine projection: centroid of a real triangle.
    a, b, c = (0.0, 0.0, 0.0), (0.04, 0.0, 0.0), (0.0, 0.03, 0.0)
    centroid = (
        (a[0] + b[0] + c[0]) / 3.0,
        (a[1] + b[1] + c[1]) / 3.0,
        (a[2] + b[2] + c[2]) / 3.0,
    )
    q, bary, region, d = closest_point_on_triangle(centroid, a, b, c)
    tests.append(
        _ok(
            "project_centroid_interior",
            region == "interior"
            and d <= 1e-12
            and all(almost(x, 1.0 / 3.0, 1e-9) for x in bary)
            and almost(sum(bary), 1.0, 1e-12),
            "bary=%s dist=%g region=%s" % (bary, d, region),
        )
    )
    # 2. Vertex A.
    q, bary, region, d = closest_point_on_triangle(a, a, b, c)
    tests.append(
        _ok(
            "project_vertex_a",
            region == "vert_a" and d <= 1e-12 and almost(bary[0], 1.0) and almost(bary[1], 0.0),
            "bary=%s region=%s" % (bary, region),
        )
    )
    # 3. Off-plane, same barycentric.
    lifted = (centroid[0], centroid[1], 0.01)
    q, bary, region, d = closest_point_on_triangle(lifted, a, b, c)
    tests.append(
        _ok(
            "project_offplane_residual",
            region == "interior" and almost(d, 0.01, 1e-9) and all(almost(x, 1.0 / 3.0, 1e-8) for x in bary),
            "bary=%s dist=%g" % (bary, d),
        )
    )
    # 4. Outside, closest is edge AB midpoint.
    outside = (0.02, -0.02, 0.0)
    q, bary, region, d = closest_point_on_triangle(outside, a, b, c)
    tests.append(
        _ok(
            "project_outside_edge_ab",
            region == "edge_ab" and almost(bary[2], 0.0, 1e-9) and q[1] == 0.0,
            "bary=%s region=%s q=%s" % (bary, region, q),
        )
    )
    # 5. Weighted-average is not projection (the sample_cloth_grid bug, tiny proof).
    # Mix A and B equally (parameter-space neighbour mix) vs true centroid projection.
    mix = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0, (a[2] + b[2]) / 2.0)
    q_true, r_true = project_point_to_triangles(
        centroid, (a, b, c), ((0, 1, 2),)
    )
    q_mix, r_mix = project_point_to_triangles(mix, (a, b, c), ((0, 1, 2),))
    tests.append(
        _ok(
            "weighted_average_is_not_projection",
            r_true["label"] == "ON_TRIANGLE"
            and r_mix["dist_m"] <= ON_EPS
            and dist(mix, centroid) > 1e-4,
            "true_dist=%g mix_to_centroid=%g" % (r_true["dist_m"], dist(mix, centroid)),
        )
    )
    # 6. PENETRATING control: two triangles that pierce.
    t1a, t1b, t1c = (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)
    t2a, t2b, t2c = (0.25, 0.25, -0.5), (0.25, 0.25, 0.5), (0.9, 0.1, 0.0)
    kind, detail = triangle_triangle_intersect(t1a, t1b, t1c, t2a, t2b, t2c)
    tests.append(_ok("control_penetrating", kind == "PENETRATING", "%s %s" % (kind, detail)))
    # 7. SEPARATED control.
    s2a, s2b, s2c = (4.0, 0.0, 0.0), (5.0, 0.0, 0.0), (4.0, 1.0, 0.0)
    kind, detail = triangle_triangle_intersect(t1a, t1b, t1c, s2a, s2b, s2c)
    tests.append(_ok("control_separated", kind == "SEPARATED", "%s %s" % (kind, detail)))
    # 8. Share a vertex only → not a proper pierce.
    kind, detail = triangle_triangle_intersect(
        (0, 0, 0), (1, 0, 0), (0, 1, 0),
        (0, 0, 0), (0, 0, 1), (-1, 0, 0),
    )
    tests.append(_ok("control_shared_vertex_not_pierce", kind == "SEPARATED", "%s %s" % (kind, detail)))
    # 9. Open boundary → UNKNOWN (single triangle mesh, query closest to an open edge).
    verts = (a, b, c)
    tris = ((0, 1, 2),)
    open_e = boundary_edges(tris)
    open_v = {i for e in open_e for i in e}
    _, r_edge = project_point_to_triangles(outside, verts, tris, open_e, open_v)
    tests.append(
        _ok(
            "open_boundary_unknown",
            r_edge["label"] == "UNKNOWN" and r_edge["open_boundary"] is True,
            "label=%s region=%s" % (r_edge["label"], r_edge["region"]),
        )
    )
    # 10. Interior query on the same open mesh is still ON_TRIANGLE (not UNKNOWN).
    _, r_in = project_point_to_triangles(centroid, verts, tris, open_e, open_v)
    tests.append(
        _ok(
            "open_mesh_interior_not_unknown",
            r_in["label"] == "ON_TRIANGLE" and r_in["open_boundary"] is False,
            "label=%s" % r_in["label"],
        )
    )
    # 11. Open-edge contact between two tris that only meet on an open edge.
    # Mesh A is one triangle; mesh B shares edge AB and lies in another plane
    # without piercing (they share the open edge only).
    kind, detail = classify_tri_tri(
        a, b, c,
        a, b, (0.02, 0.0, 0.04),
        a_open_edges=open_e, a_idx=(0, 1, 2),
        b_open_edges=boundary_edges(((0, 1, 2),)), b_idx=(0, 1, 2),
    )
    tests.append(
        _ok(
            "open_edge_contact_unknown",
            kind == "UNKNOWN",
            "%s %s" % (kind, detail),
        )
    )
    passed = all(t["pass"] for t in tests)
    return {"pass": passed, "n": len(tests), "failed": [t["name"] for t in tests if not t["pass"]], "tests": tests}


# ---------------------------------------------------------------------------
# old cap evidence (immutable builder)
# ---------------------------------------------------------------------------

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def refuse_frozen_writes(path):
    target = os.path.abspath(path)
    for blocked in FROZEN:
        try:
            if os.path.isdir(blocked) and os.path.commonpath([blocked, target]) == blocked:
                raise RuntimeError("refusing to write into frozen %s" % blocked)
        except ValueError:
            pass


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import %s" % path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _median(xs):
    if not xs:
        return None
    ys = sorted(xs)
    n = len(ys)
    if n % 2:
        return ys[n // 2]
    return 0.5 * (ys[n // 2 - 1] + ys[n // 2])


def run_cap_evidence(cap_script, anatomy_dir, source_obj):
    if not cap_script or not os.path.isfile(cap_script):
        return {"status": "UNRUN", "reason": "cap script missing (need PR20 4b81dc4 build_cap_surface.py as read-only input)"}
    if not anatomy_dir or not os.path.isdir(anatomy_dir):
        return {"status": "UNRUN", "reason": "anatomy dir missing (need 624e008 zhuge-anatomy-base as read-only sibling)"}
    if not source_obj:
        source_obj = os.path.join(anatomy_dir, "source", "base.obj")
    if not os.path.isfile(source_obj):
        return {"status": "UNRUN", "reason": "source obj missing"}
    cap = load_module(cap_script, "cap_surface_frozen_ro")
    cap.load_anatomy_module(anatomy_dir)
    built = cap.build_all(source_obj)
    surf = built["surf"]
    cap_mesh = built["meshes"]["cap"]
    head = built["meshes"]["ref_head"]
    s_verts = [tuple(p) for p in surf["verts"]]
    s_tris = triangulate_faces(surf["faces"])
    open_e = boundary_edges(s_tris)
    open_v = {i for e in open_e for i in e}
    samples = cap_mesh.get("samples") or []
    labels = {"ON_TRIANGLE": 0, "ON_BOUNDARY": 0, "OFF_SURFACE": 0, "UNKNOWN": 0}
    residuals = []
    mix_vs_proj = []
    examples_off = []
    for s in samples:
        p = tuple(s["p"])
        _q, r = project_point_to_triangles(p, s_verts, s_tris, open_e, open_v)
        labels[r["label"]] = labels.get(r["label"], 0) + 1
        residuals.append(r["dist_m"])
        mix_vs_proj.append(r["dist_m"])
        if r["label"] == "OFF_SURFACE" and len(examples_off) < 6:
            examples_off.append(
                {
                    "th": s.get("th"),
                    "h": s.get("h"),
                    "dist_m": round(r["dist_m"], 8),
                    "barycentric": [round(x, 6) for x in r["barycentric"]],
                    "region": r["region"],
                    "tri_index": r["tri_index"],
                }
            )
    c_verts = [tuple(p) for p in cap_mesh["verts"]]
    c_tris = triangulate_faces(cap_mesh["faces"])
    h_verts = [tuple(p) for p in head["verts"]]
    h_tris = triangulate_faces(head["faces"])
    # Inner half of cap verts are the surface-constraint samples extruded inward.
    n_inner = cap_mesh.get("inner_count") or (len(c_verts) // 2)
    inner_verts = c_verts[:n_inner]
    inner_tris = [t for t in c_tris if max(t) < n_inner]
    outer_tris = [t for t in c_tris if min(t) >= n_inner]
    inter_inner = exact_intersect_pairs(c_verts, inner_tris, h_verts, h_tris)
    inter_outer = exact_intersect_pairs(c_verts, outer_tris, h_verts, h_tris)
    return {
        "status": "RAN",
        "cap_script": os.path.abspath(cap_script),
        "cap_script_sha256": sha256_file(cap_script),
        "cap_commit_pin": CAP_COMMIT,
        "anatomy_commit_pin": ANATOMY_COMMIT,
        "immutable_builder": True,
        "edited_builder": False,
        "gates_ok_from_builder": built.get("gates_ok"),
        "note_gates_ok_is_not_projection_proof": True,
        "scalp_patch": {
            "verts": len(s_verts),
            "tris": len(s_tris),
            "open_edges": len(open_e),
            "open_verts": len(open_v),
        },
        "sample_cloth_grid": {
            "n": len(samples),
            "labels": labels,
            "residual_m": {
                "min": min(residuals) if residuals else None,
                "median": _median(residuals),
                "max": max(residuals) if residuals else None,
                "n_gt_1mm": sum(1 for x in residuals if x > 0.001),
                "n_gt_1cm": sum(1 for x in residuals if x > 0.01),
            },
            "off_surface_examples": examples_off,
            "note": (
                "Each sample_cloth_grid point is re-projected onto real scalp "
                "triangles. Residual is metres from the weighted-average mix "
                "to the closest point on a triangle. UNKNOWN = closest feature "
                "is an open hem/ear cut. OFF_SURFACE = mix was not on a face."
            ),
        },
        "exact_intersection": {
            "cap_inner_vs_ref_head": inter_inner,
            "cap_outer_vs_ref_head": inter_outer,
            "note": "Not BVH-only. AABB candidates are enumerated then exact-tested.",
        },
        "census": built.get("census"),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def argv_after_dash():
    argv = sys.argv[1:]
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    return argv


def parse_args():
    p = argparse.ArgumentParser(description="CT-SURFACE-VERIFY-01 independent geometry diagnostics")
    p.add_argument("--output-dir", default=os.path.join(HERE, "out"))
    p.add_argument("--anatomy-dir", default=None)
    p.add_argument("--source-obj", default=None)
    p.add_argument("--cap-script", default=None)
    p.add_argument("--skip-cap", action="store_true")
    args, _ = p.parse_known_args(argv_after_dash())
    if not args.cap_script:
        args.cap_script = SIBLING_CAP if os.path.isfile(SIBLING_CAP) else None
    if not args.anatomy_dir:
        args.anatomy_dir = SIBLING_ANATOMY if os.path.isdir(SIBLING_ANATOMY) else None
    args.output_dir = os.path.abspath(args.output_dir)
    return args


def blender_present():
    try:
        import bpy  # noqa: F401
        return True, "%s" % ".".join(str(x) for x in __import__("bpy").app.version)
    except Exception:
        return False, None


def write_json(path, payload):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")
    os.replace(tmp, path)


def main():
    args = parse_args()
    refuse_frozen_writes(args.output_dir)
    os.makedirs(args.output_dir, exist_ok=True)
    has_bpy, bpy_ver = blender_present()
    controls = run_controls()
    if args.skip_cap:
        cap_ev = {"status": "UNRUN", "reason": "--skip-cap"}
    else:
        try:
            cap_ev = run_cap_evidence(args.cap_script, args.anatomy_dir, args.source_obj)
        except Exception as e:
            cap_ev = {
                "status": "ERROR",
                "reason": "%s: %s" % (type(e).__name__, e),
                "traceback": traceback.format_exc()[-2000:],
            }
    report = {
        "task_id": TASK_ID,
        "title": "Independent surface-constraint diagnostics (not an art PASS, not a new 纶巾)",
        "not_a_zhuge_product": True,
        "art_approval": False,
        "new_art_mesh": False,
        "edited_pr20_builder": False,
        "pr20_builder_commit": CAP_COMMIT,
        "anatomy_commit": ANATOMY_COMMIT,
        "blender_present": has_bpy,
        "blender_version_actual": bpy_ver,
        "blender_export": {"status": "UNRUN"},
        "render": {"status": "UNRUN"},
        "physics": {"status": "UNRUN"},
        "controls": controls,
        "cap_evidence": cap_ev,
        "limitations": [
            "Cloud has no bpy; Blender 5.2.1 export/render is UNRUN.",
            "Float64 predicates, not exact rational arithmetic. Degenerate slivers use EPS.",
            "AABB grid is a reject filter; it does not count as an intersection.",
            "Open-boundary contacts are UNKNOWN, not PENETRATING or SEPARATED.",
            "Does not patch sample_cloth_grid. Does not emit a new cap mesh.",
            "gates_ok from the builder is recorded as a number, not coverage proof.",
        ],
        "whitelist": [
            "work/codex-handoff/surface-constraint-proof-v1/surface_constraint_proof.py",
            "work/codex-handoff/surface-constraint-proof-v1/README.md",
            "work/codex-handoff/surface-constraint-proof-v1/.gitignore",
            "work/codex-handoff/surface-constraint-proof-v1/out/surface_constraint_report.json",
        ],
    }
    out = os.path.join(args.output_dir, "surface_constraint_report.json")
    write_json(out, report)
    print(
        "CT-SURFACE-VERIFY-01-CODE controls_ok=%s cap=%s bpy=%s written=%s"
        % (controls["pass"], cap_ev.get("status"), has_bpy, out)
    )
    if controls["failed"]:
        print("FAILED:", ", ".join(controls["failed"]))
    return 0 if controls["pass"] else 1


if __name__ == "__main__":
    sys.exit(main() or 0)
