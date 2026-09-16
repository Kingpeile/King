#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CT-CLOTH-PROOF-01 — one native Blender cloth collision/drape proof.

Reads frozen anatomy + clothed-v1 pose helpers. Does not edit those trees.
Does not install MPFB, does not loft a sleeve, does not hide the body.
Not a Zhuge product. Not G1–G5. Not costume 03.
"""
from __future__ import annotations

import collections
import importlib.util
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ANATOMY_DIR = os.path.abspath(os.path.join(HERE, "..", "zhuge-anatomy-base"))
CLOTHED_DIR = os.path.abspath(os.path.join(HERE, "..", "zhuge-clothed-v1"))
FROZEN_V2 = os.path.abspath(os.path.join(HERE, "..", "zhuge-volume-v2"))

_spec = importlib.util.spec_from_file_location(
    "clothed_v1_frozen_pose", os.path.join(CLOTHED_DIR, "build_clothed_v1.py")
)
C = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C)
M = C.M
B = C.B
V = C.V

TASK_ID = "CT-CLOTH-PROOF-01"
SUPPORT_BODY_COMMIT = "624e008349a447859ed58417394c68f382e9b887"
INPUT_HEAD = "3d4a40c5350ec46b9ff54547df9af1818f2dea08"
ROOT_NAME = "ClothProof_Root"
SIDE = "left"

# Single parameter set. Not a search.
FRAME_START = 1
FRAME_END = 60
FPS = 24
TIME_BUDGET_S = 120.0
CLOTH_QUALITY = 8
CLOTH_MASS = 0.3
PIN_STIFFNESS = 20.0
BENDING_STIFFNESS = 0.5
COLLISION_DISTANCE_MIN = 0.012
COLLISION_QUALITY = 3
USE_SELF_COLLISION = True
SELF_DISTANCE_MIN = 0.008
BODY_THICKNESS_OUTER = 0.010
GRAVITY = (0.0, 0.0, -9.81)
SEGS_U = 12
SEGS_V = 16
PIN_COUNT = 4
CLEARANCE_M = 0.060
MIN_CLEAR_M = 0.025
EXPLODE_DISP_M = 1.50
EXPLODE_SPEED_M_S = 40.0
COVER_Z_SLACK_M = 0.030
THROUGH_Z_BELOW_M = 0.040

PARAMS = {
    "frames": [FRAME_START, FRAME_END],
    "fps": FPS,
    "time_budget_s": TIME_BUDGET_S,
    "ClothSettings": {
        "quality": CLOTH_QUALITY,
        "mass": CLOTH_MASS,
        "vertex_group_mass": "Pin",
        "pin_stiffness": PIN_STIFFNESS,
        "bending_stiffness": BENDING_STIFFNESS,
        "effector_weights.gravity": 1.0,
    },
    "ClothCollisionSettings": {
        "distance_min": COLLISION_DISTANCE_MIN,
        "collision_quality": COLLISION_QUALITY,
        "use_self_collision": USE_SELF_COLLISION,
        "self_distance_min": SELF_DISTANCE_MIN,
    },
    "body_COLLISION": {"thickness_outer": BODY_THICKNESS_OUTER},
    "note": "One set. collision_on vs collision_off only flips cloth use_collision.",
}


def refuse_frozen_writes(path):
    B.refuse_frozen_dir(path)
    target = os.path.abspath(path)
    for blocked, label in (
        (FROZEN_V2, "zhuge-volume-v2"),
        (ANATOMY_DIR, "zhuge-anatomy-base"),
        (CLOTHED_DIR, "zhuge-clothed-v1"),
    ):
        try:
            if os.path.commonpath([blocked, target]) == blocked:
                raise RuntimeError("refusing to write into frozen %s" % label)
        except ValueError:
            pass


def parse_cli():
    p = B.argparse.ArgumentParser(description="CT-CLOTH-PROOF-01 native cloth collision proof")
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


def finite3(p):
    return all(math.isfinite(float(c)) for c in p)


def bbox_of(verts):
    xs = [p[0] for p in verts]
    ys = [p[1] for p in verts]
    zs = [p[2] for p in verts]
    return {"min": [min(xs), min(ys), min(zs)], "max": [max(xs), max(ys), max(zs)]}


def grid_quads(nu, nv):
    faces = []
    for i in range(nv - 1):
        for j in range(nu - 1):
            a = i * nu + j
            b = a + 1
            c = a + nu + 1
            d = a + nu
            faces.append((a, b, c, d))
    return faces


def hashed_min_dist(src, dst, inv=18.0):
    if not src or not dst:
        return {"min_m": None, "verts_closer_than_clearance": 0, "src_n": len(src)}
    grid = collections.defaultdict(list)
    for p in dst:
        grid[(int(p[0] * inv), int(p[1] * inv), int(p[2] * inv))].append(p)
    best = 1e9
    close = 0
    for p in src:
        key = (int(p[0] * inv), int(p[1] * inv), int(p[2] * inv))
        cand = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    cand.extend(grid[(key[0] + dx, key[1] + dy, key[2] + dz)])
        if not cand:
            cand = dst
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
        if md < MIN_CLEAR_M:
            close += 1
    return {
        "min_m": round(best, 5),
        "verts_closer_than_clearance": close,
        "clearance_m": MIN_CLEAR_M,
        "src_n": len(src),
    }


def hull_inside_count(cloth, posed, parts, zslop=0.04):
    idx = parts["torso"] + parts["neck"] + parts["head"] + parts["arm"]
    n = 0
    worst = 0.0
    for p in cloth:
        hull = C.slice_hull(posed, idx, p[2], zslop, min_pts=6)
        if len(hull) < 3:
            continue
        if C.point_in_hull(p, hull):
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
    return {"intersecting_verts": n, "worst_in_hull_m": round(worst, 5)}


def left_shoulder_arm_points(posed, Lsh, elL):
    out = []
    for p in posed:
        lp = V(p)
        d, t = C.dist_seg(lp, Lsh, elL)
        near_sh = (lp - Lsh).length() < 0.10
        on_upper = d < 0.08 and t < 0.75
        if near_sh or on_upper:
            out.append(p)
    if len(out) < 20:
        raise RuntimeError("too few left shoulder/upper-arm verts: %s" % len(out))
    return out


def build_posed_body(source_obj):
    checks = M.run_checks(source_obj)
    tpose = list(checks["blender_verts"])
    xf = C.blender_xf_params(checks)
    _src, groups = C.parse_groups(source_obj)
    morphed = checks["parsed"]["verts"]
    Lsh = C.joint_centroid(groups, morphed, "joint-l-shoulder", xf)
    Lel = C.joint_centroid(groups, morphed, "joint-l-elbow", xf)
    Lha = C.joint_centroid(groups, morphed, "joint-l-hand", xf)
    Rsh = C.joint_centroid(groups, morphed, "joint-r-shoulder", xf)
    Rel = C.joint_centroid(groups, morphed, "joint-r-elbow", xf)
    Rha = C.joint_centroid(groups, morphed, "joint-r-hand", xf)
    posed, elL, haL, poseL = C.skin_arm(tpose, Lsh, Lel, Lha, +1)
    posed, elR, haR, poseR = C.skin_arm(posed, Rsh, Rel, Rha, -1)
    for p in posed:
        if not finite3(p):
            raise RuntimeError("non-finite posed body vertex")
    parts = C.classify_indices(tpose)
    return {
        "checks": checks,
        "posed": posed,
        "faces": checks["male_body"]["faces"],
        "uvs": checks["male_body"]["uvs"],
        "uv_loops": checks["male_body"]["uv_loops"],
        "parts": parts,
        "joints": {
            "Lsh": Lsh.xyz(),
            "Lel": elL.xyz(),
            "Lha": haL.xyz(),
            "Rsh": Rsh.xyz(),
            "Rel": elR.xyz(),
            "Rha": haR.xyz(),
        },
        "pose": {"left": poseL, "right": poseR},
        "Lsh": Lsh,
        "elL": elL,
        "support_faces": checks["compat"]["remaining_faces"],
        "support_verts": checks["compat"]["remaining_verts"],
        "support_uvs": checks["compat"]["remaining_uvs"],
    }


def build_sample_cloth(body):
    region = left_shoulder_arm_points(body["posed"], body["Lsh"], body["elL"])
    xs = [p[0] for p in region]
    ys = [p[1] for p in region]
    zs = [p[2] for p in region]
    x0 = max(0.10, min(xs) + 0.04)
    x1 = max(xs) + 0.045
    y0 = min(ys) - 0.04
    y1 = max(ys) + 0.04
    z = max(zs) + CLEARANCE_M
    if x1 - x0 < 0.10 or y1 - y0 < 0.10:
        raise RuntimeError(
            "cloth sheet too small to be a drape sample: dx=%s dy=%s" % (x1 - x0, y1 - y0)
        )
    nu, nv = SEGS_U + 1, SEGS_V + 1
    verts = []
    for i in range(nv):
        v = i / float(SEGS_V)
        for j in range(nu):
            u = j / float(SEGS_U)
            verts.append((x0 + (x1 - x0) * u, y0 + (y1 - y0) * v, z))
    for p in verts:
        if not finite3(p):
            raise RuntimeError("non-finite cloth rest vertex")
    faces = grid_quads(nu, nv)
    medial = [i * nu + 0 for i in range(nv)]
    pin_indices = medial[-PIN_COUNT:]
    pin_xyz = [verts[i] for i in pin_indices]
    placement = {
        "side": SIDE,
        "plane": "world XY, gravity -Z",
        "x0": round(x0, 5),
        "x1": round(x1, 5),
        "y0": round(y0, 5),
        "y1": round(y1, 5),
        "z": round(z, 5),
        "clearance_above_region_m": CLEARANCE_M,
        "segs_u": SEGS_U,
        "segs_v": SEGS_V,
        "vert_n": len(verts),
        "quad_n": len(faces),
        "region_n": len(region),
        "region_bbox": bbox_of(region),
        "pin_rule": (
            "Exactly 4 verts on the medial column (u=0, neck side), "
            "posterior end (largest Y). vertex_group_mass Pin weight 1.0. "
            "Not the full sheet."
        ),
        "pin_indices": pin_indices,
        "pin_xyz": [[round(c, 5) for c in p] for p in pin_xyz],
    }
    return {"verts": verts, "faces": faces, "pin_indices": pin_indices, "placement": placement}


def construction_selfcheck(body, cloth):
    dist = hashed_min_dist(cloth["verts"], body["posed"])
    hull = hull_inside_count(cloth["verts"], body["posed"], body["parts"])
    blockers = []
    if dist["min_m"] is None:
        blockers.append("no body verts to test clearance")
    elif dist["min_m"] < MIN_CLEAR_M:
        blockers.append(
            "initial cloth-body vert distance %s m < %s m" % (dist["min_m"], MIN_CLEAR_M)
        )
    if dist["verts_closer_than_clearance"] > 0:
        blockers.append(
            "%s cloth verts closer than clearance to body" % dist["verts_closer_than_clearance"]
        )
    if hull["intersecting_verts"] > 0:
        blockers.append(
            "initial cloth verts inside body slice hull: %s" % hull["intersecting_verts"]
        )
    if len(cloth["pin_indices"]) != PIN_COUNT:
        blockers.append("pin count %s != %s" % (len(cloth["pin_indices"]), PIN_COUNT))
    if len(cloth["pin_indices"]) >= len(cloth["verts"]) * 0.5:
        blockers.append("too many pins — would fake physics")
    ok = not blockers
    return {
        "ok": ok,
        "blockers": blockers,
        "min_dist_to_body": dist,
        "hull_at_cloth_z": hull,
        "note": "Slice-hull + vert distance. Not an exact triangle penetration proof.",
    }


def local_bbox(cloth, body):
    bb = bbox_of(cloth["verts"])
    region = left_shoulder_arm_points(body["posed"], body["Lsh"], body["elL"])
    rb = bbox_of(region)
    mn = [min(bb["min"][i], rb["min"][i]) - 0.06 for i in range(3)]
    mx = [max(bb["max"][i], rb["max"][i]) + 0.06 for i in range(3)]
    mn[2] = min(mn[2], 1.10)
    mx[2] = max(mx[2], 1.62)
    return {"min": mn, "max": mx}


def cover_metrics(cloth_verts, body, rest_verts):
    Lsh, elL = body["Lsh"], body["elL"]
    region = left_shoulder_arm_points(body["posed"], Lsh, elL)
    rx0 = min(p[0] for p in region)
    rx1 = max(p[0] for p in region)
    ry0 = min(p[1] for p in region)
    ry1 = max(p[1] for p in region)
    top_z = max(p[2] for p in region)
    over = []
    through = []
    disp = []
    finite = True
    for i, p in enumerate(cloth_verts):
        if not finite3(p):
            finite = False
            continue
        r = rest_verts[i]
        d = math.sqrt((p[0] - r[0]) ** 2 + (p[1] - r[1]) ** 2 + (p[2] - r[2]) ** 2)
        disp.append(d)
        in_xy = (rx0 - 0.02) <= p[0] <= (rx1 + 0.02) and (ry0 - 0.02) <= p[1] <= (ry1 + 0.02)
        if in_xy and p[2] >= top_z - COVER_Z_SLACK_M:
            over.append(i)
        if in_xy and p[2] <= top_z - THROUGH_Z_BELOW_M:
            through.append(i)
    max_disp = max(disp) if disp else 0.0
    mean_disp = sum(disp) / float(len(disp) if disp else 1)
    com = (
        sum(p[0] for p in cloth_verts) / len(cloth_verts),
        sum(p[1] for p in cloth_verts) / len(cloth_verts),
        sum(p[2] for p in cloth_verts) / len(cloth_verts),
    )
    rest_com_z = sum(p[2] for p in rest_verts) / len(rest_verts)
    return {
        "finite": finite,
        "max_disp_m": round(max_disp, 5),
        "mean_disp_m": round(mean_disp, 5),
        "real_displacement": mean_disp > 0.015 and max_disp > 0.020,
        "exploded": (not finite) or max_disp > EXPLODE_DISP_M,
        "cover_vert_n": len(over),
        "through_vert_n": len(through),
        "shoulder_top_z": round(top_z, 5),
        "com": [round(c, 5) for c in com],
        "com_drop_m": round(rest_com_z - com[2], 5),
        "min_z": round(min(p[2] for p in cloth_verts), 5),
        "max_z": round(max(p[2] for p in cloth_verts), 5),
    }


def interpret_pair(on_run, off_run):
    """Only for real physics. Cloud must not call this as PASS."""
    if on_run is None or off_run is None:
        return {
            "ready": False,
            "verdict": "UNRUN",
            "can_claim_pass": False,
            "reason": "physics not executed",
        }
    on = on_run["cover"]
    off = off_run["cover"]
    reasons = []
    on_ok = (
        on["finite"]
        and not on["exploded"]
        and on["real_displacement"]
        and on["cover_vert_n"] >= 8
        and on["through_vert_n"] <= max(2, on["cover_vert_n"] // 8)
    )
    off_shows_miss = off["through_vert_n"] >= 8 and (
        off["through_vert_n"] > on["through_vert_n"] + 4
        or off["min_z"] < on["min_z"] - 0.03
        or off["com_drop_m"] > on["com_drop_m"] + 0.03
    )
    if not on["finite"] or on["exploded"]:
        reasons.append("collision_on exploded or non-finite")
    if not on["real_displacement"]:
        reasons.append("collision_on had no real drape displacement")
    if on["cover_vert_n"] < 8:
        reasons.append("collision_on did not cover the shoulder (cover_vert_n=%s)" % on["cover_vert_n"])
    if on["through_vert_n"] > max(2, on["cover_vert_n"] // 8):
        reasons.append("collision_on still has through-body candidates %s" % on["through_vert_n"])
    if not off_shows_miss:
        reasons.append(
            "collision_off did not expose missing collision "
            "(through_on=%s through_off=%s minz_on=%s minz_off=%s) — check has no discriminating power"
            % (on["through_vert_n"], off["through_vert_n"], on["min_z"], off["min_z"])
        )
    can_pass = on_ok and off_shows_miss
    return {
        "ready": True,
        "collision_on_ok": on_ok,
        "collision_off_exposes_gap": off_shows_miss,
        "can_claim_pass": can_pass,
        "verdict": "PHYSICS_PAIR_PASS" if can_pass else "PHYSICS_PAIR_FAIL",
        "reasons": reasons,
        "caveat": (
            "through/cover use XY occupancy vs shoulder AABB + z vs shoulder top. "
            "BVH overlap is a candidate list, not exact penetration. "
            "Not a Zhuge / 03 quality claim."
        ),
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
    sock = bsdf.inputs.get("Base Color")
    if sock is not None:
        sock.default_value = (color[0], color[1], color[2], 1.0)
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


def add_mesh(name, verts, faces, mat, parent):
    me = B.bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.validate(clean_customdata=False)
    me.update()
    for p in me.polygons:
        p.use_smooth = True
    obj = B.bpy.data.objects.new(name, me)
    B.bpy.context.scene.collection.objects.link(obj)
    if mat:
        obj.data.materials.append(mat)
    if parent:
        obj.parent = parent
    obj.hide_render = False
    obj.hide_viewport = False
    return obj


def apply_cloth_settings(cloth_mod, use_collision):
    s = cloth_mod.settings
    s.quality = CLOTH_QUALITY
    s.mass = CLOTH_MASS
    s.vertex_group_mass = "Pin"
    s.pin_stiffness = PIN_STIFFNESS
    s.bending_stiffness = BENDING_STIFFNESS
    if hasattr(s, "effector_weights") and s.effector_weights is not None:
        s.effector_weights.gravity = 1.0
    cs = cloth_mod.collision_settings
    cs.use_collision = bool(use_collision)
    cs.distance_min = COLLISION_DISTANCE_MIN
    cs.collision_quality = COLLISION_QUALITY
    cs.use_self_collision = USE_SELF_COLLISION
    cs.self_distance_min = SELF_DISTANCE_MIN
    pc = cloth_mod.point_cache
    pc.frame_start = FRAME_START
    pc.frame_end = FRAME_END
    if hasattr(pc, "use_disk_cache"):
        pc.use_disk_cache = True
    return {
        "use_collision_actual": bool(cs.use_collision),
        "quality": int(s.quality),
        "mass": float(s.mass),
        "vertex_group_mass": str(s.vertex_group_mass),
        "pin_stiffness": float(s.pin_stiffness),
        "bending_stiffness": float(s.bending_stiffness),
        "distance_min": float(cs.distance_min),
        "collision_quality": int(cs.collision_quality),
        "use_self_collision": bool(cs.use_self_collision),
        "self_distance_min": float(cs.self_distance_min),
        "cache_frame_start": int(pc.frame_start),
        "cache_frame_end": int(pc.frame_end),
        "use_disk_cache": bool(getattr(pc, "use_disk_cache", False)),
    }


def setup_world_and_lights(root):
    scene = B.bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    scene.use_gravity = True
    scene.gravity = GRAVITY
    scene.frame_start = FRAME_START
    scene.frame_end = FRAME_END
    scene.render.fps = FPS
    world = B.bpy.data.worlds.new("ClothProofWorld")
    scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs[0].default_value = (0.18, 0.18, 0.18, 1.0)
    bg.inputs[1].default_value = 0.35
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(bg.outputs[0], out.inputs[0])
    sun = B.bpy.data.lights.new("Key", "SUN")
    sun.energy = 4.0
    sun.color = (1.0, 0.97, 0.92)
    sun_obj = B.bpy.data.objects.new("Key", sun)
    sun_obj.location = (2.0, -2.2, 3.4)
    sun_obj.rotation_euler = (math.radians(50), 0, math.radians(-35))
    B.bpy.context.scene.collection.objects.link(sun_obj)
    fill = B.bpy.data.lights.new("Fill", "AREA")
    fill.energy = 90.0
    fill.color = (0.7, 0.78, 1.0)
    fill.size = 1.4
    fill_obj = B.bpy.data.objects.new("Fill", fill)
    fill_obj.location = (-1.6, -1.0, 1.8)
    B.bpy.context.scene.collection.objects.link(fill_obj)
    sun_obj.parent = root
    fill_obj.parent = root
    engine = scene.render.engine
    items = []
    try:
        items = [e.identifier for e in scene.render.bl_rna.properties["engine"].enum_items]
    except Exception:
        items = []
    for cand in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES"):
        if cand in items:
            scene.render.engine = cand
            engine = cand
            break
    return engine


def eval_mesh_verts(obj):
    dg = B.bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    me = ev.to_mesh()
    verts = [tuple(v.co) for v in me.vertices]
    ev.to_mesh_clear()
    return verts


def bvh_overlap_candidates(cloth_obj, body_obj):
    from mathutils.bvhtree import BVHTree

    dg = B.bpy.context.evaluated_depsgraph_get()
    try:
        t_c = BVHTree.FromObject(cloth_obj, dg)
        t_b = BVHTree.FromObject(body_obj, dg)
    except TypeError:
        t_c = BVHTree.FromObject(cloth_obj, dg, epsilon=0.0)
        t_b = BVHTree.FromObject(body_obj, dg, epsilon=0.0)
    pairs = t_c.overlap(t_b) or []
    sample = [[int(a), int(b)] for a, b in pairs[:24]]
    return {
        "pair_count": len(pairs),
        "sample_pairs": sample,
        "not_exact_penetration": True,
        "note": "BVHTree.overlap polygon index pairs. Candidates only, not a watertight penetration test.",
    }


def render_local(cams, out_dir, skip):
    os.makedirs(out_dir, exist_ok=True)
    names = []
    mapping = (
        ("Cam_Front", "view_front.png"),
        ("Cam_Side", "view_side.png"),
        ("Cam_Back", "view_back.png"),
        ("Cam_LookDown", "view_lookdown.png"),
    )
    if skip:
        return names
    scene = B.bpy.context.scene
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    for cam_name, fname in mapping:
        scene.camera = cams[cam_name]
        fp = B.safe_join(out_dir, fname)
        scene.render.filepath = fp
        B.bpy.ops.render.render(write_still=True)
        names.append(fname)
    return names


def run_one_arm(label, use_collision, body, cloth, local_bb, out_dir, skip_render, budget_deadline):
    B.clear_scene()
    scene = B.bpy.context.scene
    root = B.bpy.data.objects.new(ROOT_NAME, None)
    B.bpy.context.scene.collection.objects.link(root)
    engine = setup_world_and_lights(root)
    mats = {
        "skin": make_mat("M_Skin", (0.62, 0.48, 0.40), 0.55, 0.22),
        "cloth": make_mat("M_SampleCloth", (0.86, 0.78, 0.42), 0.74, 0.10),
    }
    body_pack = {
        "faces": body["faces"],
        "uvs": body["uvs"],
        "uv_loops": body["uv_loops"],
    }
    body_obj = B.build_mesh_object(body["posed"], body_pack, root, mats["skin"])
    body_obj.name = "CollisionBody"
    body_obj.hide_render = False
    body_obj.hide_viewport = False
    col = body_obj.modifiers.new("Collision", "COLLISION")
    if hasattr(body_obj, "collision") and body_obj.collision is not None:
        if hasattr(body_obj.collision, "thickness_outer"):
            body_obj.collision.thickness_outer = BODY_THICKNESS_OUTER
        if hasattr(body_obj.collision, "use"):
            body_obj.collision.use = True
    cloth_obj = add_mesh("SampleCloth", cloth["verts"], cloth["faces"], mats["cloth"], root)
    vg = cloth_obj.vertex_groups.new(name="Pin")
    free = set(range(len(cloth["verts"])))
    for idx in cloth["pin_indices"]:
        vg.add([idx], 1.0, "REPLACE")
        free.discard(idx)
    for idx in sorted(free):
        vg.add([idx], 0.0, "REPLACE")
    cloth_mod = cloth_obj.modifiers.new("Cloth", "CLOTH")
    rna = apply_cloth_settings(cloth_mod, use_collision)
    rna["collision_modifier"] = col.type if col is not None else None
    rna["body_hidden"] = bool(body_obj.hide_render)
    rna["pin_weight_1_n"] = len(cloth["pin_indices"])
    rna["free_vert_n"] = len(free)
    cams = B.setup_cameras(local_bb)
    arm_dir = B.safe_join(out_dir, label)
    os.makedirs(arm_dir, exist_ok=True)
    refuse_frozen_writes(arm_dir)
    blend_path = B.safe_join(arm_dir, "proof.blend")
    B.bpy.ops.wm.save_as_mainfile(
        **B.filter_op_kwargs(
            B.bpy.ops.wm.save_as_mainfile,
            {"filepath": blend_path, "check_existing": False},
        )
    )
    frames = []
    prev = None
    timed_out = False
    t0 = time.monotonic()
    dt = 1.0 / float(FPS)
    last_verts = None
    for frame in range(FRAME_START, FRAME_END + 1):
        if time.monotonic() > budget_deadline:
            timed_out = True
            break
        scene.frame_set(frame)
        verts = eval_mesh_verts(cloth_obj)
        last_verts = verts
        finite = all(finite3(p) for p in verts)
        com = (
            sum(p[0] for p in verts) / len(verts),
            sum(p[1] for p in verts) / len(verts),
            sum(p[2] for p in verts) / len(verts),
        )
        max_speed = 0.0
        if prev is not None and len(prev) == len(verts):
            for a, b in zip(prev, verts):
                s = math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) / dt
                if s > max_speed:
                    max_speed = s
        max_disp = 0.0
        for a, b in zip(cloth["verts"], verts):
            d = math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)
            if d > max_disp:
                max_disp = d
        frames.append(
            {
                "frame": frame,
                "t_s": round(time.monotonic() - t0, 4),
                "finite": finite,
                "com": [round(c, 5) for c in com],
                "min_z": round(min(p[2] for p in verts), 5),
                "max_z": round(max(p[2] for p in verts), 5),
                "max_speed_m_s": round(max_speed, 4),
                "max_disp_from_rest_m": round(max_disp, 5),
                "speed_exploded": max_speed > EXPLODE_SPEED_M_S,
            }
        )
        prev = verts
    elapsed = time.monotonic() - t0
    if last_verts is None:
        last_verts = list(cloth["verts"])
    cover = cover_metrics(last_verts, body, cloth["verts"])
    speed_exploded = any(f["speed_exploded"] or not f["finite"] for f in frames)
    cover["exploded"] = bool(cover["exploded"] or speed_exploded)
    cover["finite"] = bool(cover["finite"] and all(f["finite"] for f in frames))
    overlap = None
    if not timed_out or last_verts is not None:
        try:
            overlap = bvh_overlap_candidates(cloth_obj, body_obj)
        except Exception as exc:
            overlap = {"pair_count": None, "error": str(exc), "not_exact_penetration": True}
    B.bpy.ops.wm.save_as_mainfile(
        **B.filter_op_kwargs(
            B.bpy.ops.wm.save_as_mainfile,
            {"filepath": blend_path, "check_existing": False},
        )
    )
    pngs = render_local(cams, arm_dir, skip_render)
    timing = {
        "label": label,
        "use_collision": use_collision,
        "elapsed_s": round(elapsed, 3),
        "frames_recorded": len(frames),
        "frames_requested": FRAME_END - FRAME_START + 1,
        "timed_out": timed_out,
        "budget_s": TIME_BUDGET_S,
        "render_engine": engine,
    }
    B.write_json(B.safe_join(arm_dir, "frames.json"), {"frames": frames, "rna": rna})
    B.write_json(B.safe_join(arm_dir, "timing.json"), timing)
    return {
        "label": label,
        "use_collision": use_collision,
        "rna": rna,
        "frames": frames,
        "cover": cover,
        "overlap": overlap,
        "timing": timing,
        "outputs": ["proof.blend"] + pngs + ["frames.json", "timing.json"],
        "timed_out": timed_out,
        "body_visible": (not body_obj.hide_render) and (not body_obj.hide_viewport),
        "pin_n": len(cloth["pin_indices"]),
        "free_n": len(free),
    }


def write_evidence(output_dir, payload):
    os.makedirs(output_dir, exist_ok=True)
    refuse_frozen_writes(output_dir)
    path = B.safe_join(output_dir, "evidence.json")
    B.write_json(path, payload)
    return path


def cloud_payload(body, cloth, selfcheck, local_bb, blender_present, blender_version, physics):
    pair = interpret_pair(
        None if physics is None else physics.get("collision_on"),
        None if physics is None else physics.get("collision_off"),
    )
    physics_status = "UNRUN"
    execution_kind = "expected"
    if physics is not None:
        execution_kind = "real"
        if physics.get("timed_out"):
            physics_status = "TIMEOUT"
        elif physics.get("failed"):
            physics_status = "FAIL"
        else:
            physics_status = pair["verdict"]
    return {
        "task_id": TASK_ID,
        "title": "Native Blender cloth collision / drape proof (not costume 03)",
        "status": physics_status if blender_present else "UNRUN",
        "execution_kind": execution_kind,
        "physics_status": physics_status,
        "not_a_zhuge_product": True,
        "g1_g5_claimed": False,
        "art_approval": False,
        "costume_03_claimed": False,
        "full_character": False,
        "armature": False,
        "can_walk": False,
        "declaration": (
            "Sample cloth sheet on frozen posed male body. Decides whether the "
            "CLOTH+COLLISION route is usable. Not a Zhuge quality or 03 pass."
        ),
        "input": {
            "pr17_head": INPUT_HEAD,
            "support_body_commit": SUPPORT_BODY_COMMIT,
            "pose": "static two-bone rest pose from clothed-v1 helpers (read-only)",
            "source_read_only": True,
            "mpfb_install": False,
        },
        "method": {
            "new_sheet": True,
            "not_loft_retune": True,
            "body_hidden": False,
            "whole_sheet_pinned": False,
            "pin_n": PIN_COUNT,
            "pair": ["collision_on", "collision_off"],
            "cache": "isolated per-arm blend + disk cache; sequential frame_set 1..60",
            "param_search": False,
        },
        "params": PARAMS,
        "support_body_faces": body["support_faces"],
        "support_body_verts": body["support_verts"],
        "support_body_uvs": body["support_uvs"],
        "pose": body["pose"],
        "joints": body["joints"],
        "cloth_placement": cloth["placement"],
        "construction_selfcheck": selfcheck,
        "local_camera_bbox": local_bb,
        "pair_verdict": pair,
        "physics": physics,
        "blender_present": blender_present,
        "blender_version_actual": blender_version,
        "unverified_until_mac_blender": [
            "CLOTH + COLLISION drape on posed shoulder (images + BVH candidates)",
            "collision_off actually falls through vs on resting on shoulder",
            "120s wall clock on Mac Blender 5.2.1",
        ],
    }


def main():
    args = parse_cli()
    if not os.path.isfile(args.source_obj):
        raise RuntimeError("source obj missing: %s" % args.source_obj)
    # Do not modify the input file.
    src_stat = os.stat(args.source_obj)
    body = build_posed_body(args.source_obj)
    cloth = build_sample_cloth(body)
    selfcheck = construction_selfcheck(body, cloth)
    local_bb = local_bbox(cloth, body)
    print(
        "construction ok=%s faces=%s cloth_verts=%s min_dist=%s hull_hits=%s pins=%s"
        % (
            selfcheck["ok"],
            body["support_faces"],
            cloth["placement"]["vert_n"],
            selfcheck["min_dist_to_body"]["min_m"],
            selfcheck["hull_at_cloth_z"]["intersecting_verts"],
            cloth["placement"]["pin_indices"],
        )
    )
    if not selfcheck["ok"]:
        payload = cloud_payload(body, cloth, selfcheck, local_bb, False, None, None)
        payload["status"] = "CONSTRUCTION_BLOCKED"
        payload["physics_status"] = "UNRUN"
        write_evidence(args.output_dir, payload)
        raise RuntimeError("initial non-intersecting cloth sheet failed: %s" % selfcheck["blockers"])
    if B.bpy is None:
        payload = cloud_payload(body, cloth, selfcheck, local_bb, False, None, None)
        write_evidence(args.output_dir, payload)
        print("cloth proof UNRUN construction_ok=%s" % selfcheck["ok"])
        after = os.stat(args.source_obj)
        if (after.st_mtime, after.st_size) != (src_stat.st_mtime, src_stat.st_size):
            raise RuntimeError("source obj was modified")
        return 0

    deadline = time.monotonic() + TIME_BUDGET_S
    physics = {"timed_out": False, "failed": False, "collision_on": None, "collision_off": None}
    try:
        on_run = run_one_arm(
            "collision_on", True, body, cloth, local_bb, args.output_dir, args.skip_render, deadline
        )
        physics["collision_on"] = {
            k: on_run[k]
            for k in (
                "label",
                "use_collision",
                "rna",
                "cover",
                "overlap",
                "timing",
                "outputs",
                "timed_out",
                "body_visible",
                "pin_n",
                "free_n",
            )
        }
        physics["collision_on"]["frame_n"] = len(on_run["frames"])
        physics["timed_out"] = physics["timed_out"] or on_run["timed_out"]
        if not on_run["timed_out"]:
            off_run = run_one_arm(
                "collision_off",
                False,
                body,
                cloth,
                local_bb,
                args.output_dir,
                args.skip_render,
                deadline,
            )
            physics["collision_off"] = {
                k: off_run[k]
                for k in (
                    "label",
                    "use_collision",
                    "rna",
                    "cover",
                    "overlap",
                    "timing",
                    "outputs",
                    "timed_out",
                    "body_visible",
                    "pin_n",
                    "free_n",
                )
            }
            physics["collision_off"]["frame_n"] = len(off_run["frames"])
            physics["timed_out"] = physics["timed_out"] or off_run["timed_out"]
        else:
            physics["failed"] = True
            physics["collision_off"] = None
            physics["note"] = "collision_on hit the 120s budget; collision_off not started. No param retry."
    except Exception as exc:
        physics["failed"] = True
        physics["error"] = str(exc)
        payload = cloud_payload(
            body,
            cloth,
            selfcheck,
            local_bb,
            True,
            "%d.%d.%d" % tuple(B.bpy.app.version),
            physics,
        )
        write_evidence(args.output_dir, payload)
        raise
    payload = cloud_payload(
        body,
        cloth,
        selfcheck,
        local_bb,
        True,
        "%d.%d.%d" % tuple(B.bpy.app.version),
        physics,
    )
    write_evidence(args.output_dir, payload)
    after = os.stat(args.source_obj)
    if (after.st_mtime, after.st_size) != (src_stat.st_mtime, src_stat.st_size):
        raise RuntimeError("source obj was modified")
    print(
        "cloth proof physics_status=%s on_timeout=%s"
        % (payload["physics_status"], physics["timed_out"])
    )
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
