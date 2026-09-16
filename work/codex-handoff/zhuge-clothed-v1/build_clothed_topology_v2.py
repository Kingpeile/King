#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CT-COSTUME-TOPO-01 — single garment with shared armhole indices.

Frozen and unread for writes: build_clothed_v1.py @ 72f854997468595b7492d709d8235db6cd74cf0c,
zhuge-anatomy-base/, zhuge-volume-v2/. Read-only import of v1 for body/pose/cameras/export helpers.

Replaces Robe_Outer + Robe_Sleeve_L + Robe_Sleeve_R with ONE mesh.
Armhole loops are the same vertex indices as sleeve ring 0. Not a join-by-distance.
"""
from __future__ import annotations

import importlib.util
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ANATOMY_DIR = os.path.abspath(os.path.join(HERE, "..", "zhuge-anatomy-base"))
FROZEN_V2 = os.path.abspath(os.path.join(HERE, "..", "zhuge-volume-v2"))
FROZEN_V1_PATH = os.path.join(HERE, "build_clothed_v1.py")
FROZEN_V1_COMMIT = "72f854997468595b7492d709d8235db6cd74cf0c"

_spec = importlib.util.spec_from_file_location("clothed_v1_frozen", FROZEN_V1_PATH)
C = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C)
B = C.B
V = C.V

TASK_ID = "CT-COSTUME-TOPO-01"
ROOT_NAME = "ZhugeTopoV2_Root"
NROWS = 14
NCOLS = C.COLS  # 28
ARMHOLE_R0 = 1  # collar row
ARMHOLE_R1 = 4  # chest2 row (vert index)
ARMHOLE_SPAN = 6  # vert columns → 5 skipped face-cols
SLEEVE_STATIONS = 12


def refuse_frozen_writes(path):
    C.refuse_frozen_writes(path)
    target = os.path.abspath(path)
    blocked = os.path.abspath(os.path.join(HERE, "out"))
    try:
        if os.path.commonpath([blocked, target]) == blocked:
            raise RuntimeError("refusing to write into frozen v1 out/")
    except ValueError:
        pass


def parse_cli():
    p = B.argparse.ArgumentParser(description="CT-COSTUME-TOPO-01 shared-armhole sample")
    p.add_argument("--source-obj", default=None)
    p.add_argument("--output-dir", default=None)
    p.add_argument("--skip-render", action="store_true")
    args, _unknown = p.parse_known_args(B.argv_after_dash())
    if not args.source_obj:
        args.source_obj = os.path.join(ANATOMY_DIR, "source", "base.obj")
    if not args.output_dir:
        args.output_dir = os.path.join(HERE, "out-topology-v2")
    args.source_obj = os.path.abspath(args.source_obj)
    args.output_dir = os.path.abspath(args.output_dir)
    refuse_frozen_writes(args.output_dir)
    return args


def centroid(pts):
    n = float(len(pts))
    return V(
        sum(p.x for p in pts) / n,
        sum(p.y for p in pts) / n,
        sum(p.z for p in pts) / n,
    )


def bezier2(p0, p1, p2, n):
    out = []
    for i in range(n):
        t = i / float(n - 1) if n > 1 else 0.0
        u = 1.0 - t
        out.append(p0 * (u * u) + p1 * (2.0 * u * t) + p2 * (t * t))
    return out


def parallel_transport(dirs):
    """One continuous frame along the centerline. No per-segment basis_from_dir."""
    d0 = dirs[0]
    bx, by = C.basis_from_dir(d0)
    frames = [(bx, by)]
    twists = [0.0]
    for i in range(1, len(dirs)):
        prev, cur = dirs[i - 1], dirs[i]
        axis = prev.cross(cur)
        dp = max(-1.0, min(1.0, prev.dot(cur)))
        ang = math.acos(dp)
        if axis.length() < 1e-8 or ang < 1e-8:
            frames.append(frames[-1])
            twists.append(0.0)
            continue
        axis = axis.nrm()
        px, py = frames[-1]
        bx = C.rot(px, V(0, 0, 0), axis, ang)
        by = C.rot(py, V(0, 0, 0), axis, ang)
        bx = (bx - cur * cur.dot(bx)).nrm()
        by = cur.cross(bx).nrm()
        frames.append((bx, by))
        twists.append(math.degrees(ang))
    return frames, twists


def col_window(center, span, ncols):
    half = span // 2
    return [(center - half + i) % ncols for i in range(span)]


def rect_hole_loop(r0, r1, cols, ncols):
    """CCW loop of the rectangular hole. No interior verts on the loop."""
    loop = []
    for c in cols:
        loop.append(r0 * ncols + c)
    last = cols[-1]
    first = cols[0]
    for r in range(r0 + 1, r1 + 1):
        loop.append(r * ncols + last)
    for c in reversed(cols[:-1]):
        loop.append(r1 * ncols + c)
    for r in range(r1 - 1, r0, -1):
        loop.append(r * ncols + first)
    return loop


def compact_mesh(verts, faces):
    used = sorted({i for f in faces for i in f})
    remap = {old: new for new, old in enumerate(used)}
    nv = [verts[i] for i in used]
    nf = [tuple(remap[i] for i in f) for f in faces]
    return nv, nf, remap


def shift_all(meshes, dz):
    if abs(dz) < 1e-12:
        return
    for m in meshes.values():
        m["verts"] = [(p[0], p[1], p[2] + dz) for p in m["verts"]]


def build_shared_garment(posed, parts, bones):
    """One mesh. Sleeve ring 0 IS the torso armhole loop (same indices)."""
    robe = C.build_torso_robe(posed, parts)
    rows = robe["rows"]
    verts = [v.xyz() for row in rows for v in row]
    holes = []
    skip = set()
    for side in bones:
        sign = side["sign"]
        jmid = max(range(NCOLS), key=lambda j: rows[2][j].x * sign)
        cols = col_window(jmid, ARMHOLE_SPAN, NCOLS)
        for i in range(len(cols) - 1):
            c = cols[i]
            nxt = cols[i + 1]
            if nxt != (c + 1) % NCOLS:
                raise RuntimeError("armhole columns not contiguous")
            for r in range(ARMHOLE_R0, ARMHOLE_R1):
                skip.add((r, c))
        loop = rect_hole_loop(ARMHOLE_R0, ARMHOLE_R1, cols, NCOLS)
        holes.append({"loop": loop, "cols": cols, "sign": sign, "side": side})

    faces = []
    for r in range(NROWS - 1):
        for c in range(NCOLS):
            if (r, c) in skip:
                continue
            a = r * NCOLS + c
            b = r * NCOLS + (c + 1) % NCOLS
            d = (r + 1) * NCOLS + c
            e = (r + 1) * NCOLS + (c + 1) % NCOLS
            faces.append((a, b, e, d))

    frame_twists = []
    shared = []
    for hole in holes:
        loop = list(hole["loop"])
        shared.append(list(loop))
        side = hole["side"]
        sh, el, ha = side["sh"], side["el"], side["ha"]
        ru, rf = side["r_upper"], side["r_fore"]
        pts0 = [V(verts[i]) for i in loop]
        c0 = centroid(pts0)
        away = V(c0.x, c0.y, 0.0)
        if away.length() < 1e-8:
            away = V(hole["sign"], 0, 0)
        away = away.nrm()
        p0 = c0 + away * 0.012
        p1 = el + away * 0.04
        p2 = ha + away * 0.01
        stations = bezier2(p0, p1, p2, SLEEVE_STATIONS)
        dirs = []
        for i in range(len(stations)):
            if i < len(stations) - 1:
                dirs.append((stations[i + 1] - stations[i]).nrm())
            else:
                dirs.append(dirs[-1])
        frames, twists = parallel_transport(dirs)
        frame_twists.extend(twists)
        x0, y0 = frames[0]
        d0 = dirs[0]
        polar = []
        for p in pts0:
            off = p - stations[0]
            polar.append((off.dot(x0), off.dot(y0), off.dot(d0)))
        r_sh = ru + 0.050
        r_el = max(ru, rf) + 0.055
        r_ha = rf + 0.042
        rings = [loop]
        n = len(loop)
        for s in range(1, len(stations)):
            t = s / float(len(stations) - 1)
            if t < 0.45:
                rt = r_sh + (r_el - r_sh) * (t / 0.45)
            else:
                rt = r_el + (r_ha - r_el) * ((t - 0.45) / 0.55)
            circ = t * t * (3.0 - 2.0 * t)
            origin = stations[s]
            bx, by = frames[s]
            d = dirs[s]
            ring = []
            for k in range(n):
                ox, oy, oz = polar[k]
                L = math.hypot(ox, oy) or 1e-6
                rad = L * (1.0 - circ) + rt * circ
                ux, uy = ox / L * rad, oy / L * rad
                p = origin + bx * ux + by * uy + d * (oz * (1.0 - t))
                ring.append(len(verts))
                verts.append(p.xyz())
            prev = rings[-1]
            for k in range(n):
                a, b = prev[k], prev[(k + 1) % n]
                c, e = ring[(k + 1) % n], ring[k]
                faces.append((a, b, c, e))
            rings.append(ring)
        hole["rings"] = rings
        hole["twists"] = twists

    verts, faces, remap = compact_mesh(verts, faces)
    shared_after = [[remap[i] for i in loop if i in remap] for loop in shared]
    return {
        "verts": verts,
        "faces": faces,
        "armhole_loops_before_compact": shared,
        "armhole_loops": shared_after,
        "n_holes": len(holes),
        "skipped_torso_faces": len(skip),
        "max_ring_twist_deg": round(max(frame_twists) if frame_twists else 0.0, 2),
        "mean_ring_twist_deg": round(sum(frame_twists) / max(1, len(frame_twists)), 2),
        "shared_indices": all(len(s) == len(set(s)) and len(s) >= 8 for s in shared),
    }


def build_guan_filled(posed, parts):
    """Loft + real crown fill. Boundary sits at the brim, not the crown."""
    head = [posed[i] for i in parts["head"]]
    crown_z = max(p[2] for p in head)
    scalp_idx = [i for i in parts["head"] if posed[i][2] >= 1.70]
    hull = C.slice_hull(posed, scalp_idx or parts["head"], 1.72, 0.04)
    cap0 = C.ring_from_hull(hull, 0.010, 16, 0.02, 1.705, 0.0)
    cap1 = C.ring_from_hull(hull, 0.014, 16, 0.02, crown_z + 0.008, 0.0)
    cap2 = [V(v.x * 0.88, v.y * 0.88, crown_z + 0.018) for v in cap1]
    verts = [v.xyz() for v in cap0 + cap1 + cap2]
    faces = C.grid_faces(3, 16, True)
    cx = sum(v.x for v in cap2) / 16.0
    cy = sum(v.y for v in cap2) / 16.0
    cz = crown_z + 0.024
    center = len(verts)
    verts.append((cx, cy, cz))
    # fan uses the last ring (verts 32..47) so those edges become interior
    for j in range(16):
        a = 32 + j
        b = 32 + ((j + 1) % 16)
        faces.append((a, b, center))
    brow_band = [p for p in posed if 1.665 <= p[2] <= 1.70 and abs(p[0]) < 0.07]
    brow_y = min(p[1] for p in brow_band) if brow_band else -0.02
    z0, z1 = C.GUAN_MIN_Z, crown_z + 0.012
    czb = 0.5 * (z0 + z1)
    board_v, board_f = C.quad_box(0.0, brow_y - 0.012, czb, 0.10, 0.016, z1 - z0)
    verts.extend(board_v)
    faces.extend(C.shift_faces(board_f, 16 * 3 + 1))
    return {
        "verts": verts,
        "faces": faces,
        "crown_z": crown_z,
        "brow_y": brow_y,
        "board_z_min": z0,
        "board_z_max": z1,
        "crown_filled": True,
        "fill_center": (cx, cy, cz),
    }


def build_shoes_filled(posed, parts, sign):
    """Side walls + filled sole. Ankle loop stays open."""
    idx = [i for i in parts["foot"] if posed[i][0] * sign > 0.02]
    if not idx:
        idx = [i for i in parts["foot"] if posed[i][0] * sign >= 0.0]
    pts = [posed[i] for i in idx]
    toe_y = min(p[1] for p in pts)
    extra = [(p[0], toe_y - 0.018) for p in pts if p[1] < toe_y + 0.02]
    lo_pts = [(p[0], p[1]) for p in pts if p[2] < 0.03] + extra
    hi_pts = [(p[0], p[1]) for p in pts if p[2] > 0.04] + extra
    lo = C.convex_hull(lo_pts) or lo_pts[:3]
    hi = C.convex_hull(hi_pts) or hi_pts[:3]
    r0 = C.ring_from_hull(lo, 0.016, 12, 0.0, 0.002, 0.0)
    r1 = C.ring_from_hull(lo, 0.018, 12, 0.0, 0.040, 0.0)
    r2 = C.ring_from_hull(hi, 0.016, 12, 0.0, 0.090, 0.0)
    verts = [v.xyz() for v in r0 + r1 + r2]
    faces = C.grid_faces(3, 12, True)
    cx = sum(v.x for v in r0) / 12.0
    cy = sum(v.y for v in r0) / 12.0
    cz = 0.002
    center = len(verts)
    verts.append((cx, cy, cz))
    for j in range(12):
        a = j
        b = (j + 1) % 12
        # winding so the sole sits under the foot
        faces.append((a, center, b))
    return {"verts": verts, "faces": faces, "toe_y": toe_y, "sole_filled": True}


def pose_support(source_obj):
    checks = C.M.run_checks(source_obj)
    tpose = list(checks["blender_verts"])
    xf = C.blender_xf_params(checks)
    _src_verts, groups = C.parse_groups(source_obj)
    morphed = checks["parsed"]["verts"]
    Lsh = C.joint_centroid(groups, morphed, "joint-l-shoulder", xf)
    Lel = C.joint_centroid(groups, morphed, "joint-l-elbow", xf)
    Lha = C.joint_centroid(groups, morphed, "joint-l-hand", xf)
    Rsh = C.joint_centroid(groups, morphed, "joint-r-shoulder", xf)
    Rel = C.joint_centroid(groups, morphed, "joint-r-elbow", xf)
    Rha = C.joint_centroid(groups, morphed, "joint-r-hand", xf)
    armL = C.classify_arm_bones(tpose, Lsh, Lel, Lha, +1)
    armR = C.classify_arm_bones(tpose, Rsh, Rel, Rha, -1)
    posed, elL, haL, poseL = C.skin_arm(tpose, Lsh, Lel, Lha, +1)
    posed, elR, haR, poseR = C.skin_arm(posed, Rsh, Rel, Rha, -1)
    parts = C.classify_indices(tpose)
    rU_L = C.bone_radius(posed, armL["upper"], Lsh, elL)
    rF_L = C.bone_radius(posed, armL["fore"], elL, haL)
    rU_R = C.bone_radius(posed, armR["upper"], Rsh, elR)
    rF_R = C.bone_radius(posed, armR["fore"], elR, haR)
    return {
        "checks": checks,
        "posed": posed,
        "parts": parts,
        "armL": armL,
        "armR": armR,
        "poseL": poseL,
        "poseR": poseR,
        "haL": haL,
        "haR": haR,
        "bones": [
            {"sign": +1, "sh": Lsh, "el": elL, "ha": haL, "r_upper": rU_L, "r_fore": rF_L},
            {"sign": -1, "sh": Rsh, "el": elR, "ha": haR, "r_upper": rU_R, "r_fore": rF_R},
        ],
    }


def build_all(source_obj):
    P = pose_support(source_obj)
    posed, parts = P["posed"], P["parts"]
    checks = P["checks"]
    garment = build_shared_garment(posed, parts, P["bones"])
    robe_rows = C.build_torso_robe(posed, parts)["rows"]
    collar = C.build_collar(robe_rows)
    sash = C.build_sash(robe_rows)
    shoe_l = build_shoes_filled(posed, parts, +1)
    shoe_r = build_shoes_filled(posed, parts, -1)
    guan = build_guan_filled(posed, parts)
    beard = C.build_beard(posed, parts)
    fan = C.build_fan(P["haL"], P["haR"])
    meshes = {
        "body": {
            "verts": posed,
            "faces": checks["male_body"]["faces"],
            "uvs": checks["male_body"]["uvs"],
            "uv_loops": checks["male_body"]["uv_loops"],
        },
        "garment": garment,
        "collar": collar,
        "sash": sash,
        "shoe_l": shoe_l,
        "shoe_r": shoe_r,
        "guan": guan,
        "beard": beard,
        "fan": fan,
    }
    for name, m in meshes.items():
        if not C.finite_mesh(m):
            raise RuntimeError("non-finite or bad indices in %s" % name)
    min_z = min(p[2] for m in meshes.values() for p in m["verts"])
    if min_z < -1e-9:
        shift_all(meshes, -min_z)
        min_z = 0.0
    elif min_z > 1e-6:
        # keep body feet on 0; do not lift
        pass
    bb = C.mesh_bbox(meshes.values())
    census = {
        name: {"verts": len(m["verts"]), "faces": len(m["faces"]), "tris": C.tri_count(m)}
        for name, m in meshes.items()
    }
    export_objects = [
        "Anatomy_Body",
        "Robe_Garment",
        "Collar_Inner",
        "Sash",
        "Shoe_L",
        "Shoe_R",
        "Guan",
        "Beard",
        "Fan",
    ]
    return {
        "checks": checks,
        "meshes": meshes,
        "bbox": bb,
        "census": census,
        "pose": {"left": P["poseL"], "right": P["poseR"], "hand_l": P["haL"].xyz(), "hand_r": P["haR"].xyz()},
        "armhole_join": {
            "shared_indices": garment["shared_indices"],
            "n_holes": garment["n_holes"],
            "skipped_torso_faces": garment["skipped_torso_faces"],
            "armhole_loop_lengths": [len(x) for x in garment["armhole_loops"]],
            "method": "sleeve ring 0 uses torso hole vertex indices; compact remaps together",
        },
        "sleeve_frame": {
            "max_ring_twist_deg": garment["max_ring_twist_deg"],
            "mean_ring_twist_deg": garment["mean_ring_twist_deg"],
            "stations": SLEEVE_STATIONS,
            "centerline": "quadratic bezier + parallel transport",
        },
        "export_objects": export_objects,
        "feet_min_z": round(min(p[2] for m in meshes.values() for p in m["verts"]), 8),
        "body_kept": True,
        "frozen_v1": FROZEN_V1_COMMIT,
        "support_faces": checks["compat"]["remaining_faces"],
        "support_uvs": checks["compat"]["remaining_uvs"],
    }


def write_report(output_dir, built, topo, execution_kind, status, blender_present, blender_version, outputs, glb_bytes=None):
    os.makedirs(output_dir, exist_ok=True)
    refuse_frozen_writes(output_dir)
    bb = built["bbox"]
    report = {
        "task_id": TASK_ID,
        "title": "Shared-armhole garment sample (not art PASS)",
        "status": status,
        "execution_kind": execution_kind,
        "not_a_zhuge_product": True,
        "g1_g5_claimed": False,
        "art_approval": False,
        "fusion_pass": False,
        "palace_mesh": False,
        "armature": False,
        "can_walk": False,
        "declaration": "Static topology sample. One garment mesh with shared armhole indices. Body kept. No armature.",
        "method": {
            "used": "single garment; armhole = torso hole loop = sleeve ring 0 (same indices); guan/shoe filled; bezier+parallel-transport sleeves",
            "empty_robe_generators": False,
            "frozen_v1_generator": FROZEN_V1_COMMIT,
            "not_a_third_tube_tune": True,
        },
        "export_objects": built["export_objects"],
        "census": built["census"],
        "armhole_join": built["armhole_join"],
        "sleeve_frame": built["sleeve_frame"],
        "topology": topo,
        "feet_min_z": built["feet_min_z"],
        "bbox": {"min": [round(c, 6) for c in bb["min"]], "max": [round(c, 6) for c in bb["max"]]},
        "height_m": round(bb["max"][2] - bb["min"][2], 6),
        "glb_export": {"rootName": ROOT_NAME, "yup": True, "bytes": glb_bytes if glb_bytes is not None else B.UNKNOWN},
        "blender_present": blender_present,
        "blender_version_actual": blender_version,
        "outputs": outputs,
        "unverified_until_mac_blender": [
            "Mac lookdown: guan crown closed, no scalp",
            "Mac back/lookdown shoulder: one cloth, no second sleeve shell, no hole",
            "pixel G1–G5 (not claimed)",
        ],
    }
    B.write_json(B.safe_join(output_dir, "clothed_topology_v2_report.json"), report)
    return report


def blender_export(args, built):
    B.clear_scene()
    scene = B.bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    world = B.bpy.data.worlds.new("TopoV2World")
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
        "skin": C.make_mat("M_Skin", (0.62, 0.48, 0.40), 0.55, 0.22),
        "robe": C.make_mat("M_Robe", (0.86, 0.83, 0.74), 0.72, 0.12),
        "cyan": C.make_mat("M_Cyan", (0.22, 0.42, 0.44), 0.55, 0.16),
        "hair": C.make_mat("M_Hair", (0.12, 0.08, 0.06), 0.78, 0.08),
        "fan": C.make_mat("M_Fan", (0.90, 0.88, 0.80), 0.48, 0.20),
        "grey": B.make_grey(),
    }
    ms = built["meshes"]
    body_pack = {
        "faces": ms["body"]["faces"],
        "uvs": ms["body"]["uvs"],
        "uv_loops": ms["body"]["uv_loops"],
    }
    B.build_mesh_object(ms["body"]["verts"], body_pack, root, mats["skin"])
    C.add_mesh("Robe_Garment", ms["garment"], mats["robe"], root)
    C.add_mesh("Collar_Inner", ms["collar"], mats["cyan"], root)
    C.add_mesh("Sash", ms["sash"], mats["cyan"], root)
    C.add_mesh("Shoe_L", ms["shoe_l"], mats["cyan"], root)
    C.add_mesh("Shoe_R", ms["shoe_r"], mats["cyan"], root)
    C.add_mesh("Guan", ms["guan"], mats["cyan"], root)
    C.add_mesh("Beard", ms["beard"], mats["hair"], root)
    C.add_mesh("Fan", ms["fan"], mats["fan"], root)

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
    blend_name = "zhuge_clothed_topology_v2.blend"
    glb_name = "zhuge_clothed_topology_v2.glb"
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
    return outputs, glb_bytes


def run_selfcheck(built):
    chk_path = os.path.join(HERE, "check_clothed_topology.py")
    spec = importlib.util.spec_from_file_location("check_clothed_topology", chk_path)
    K = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(K)
    return K.audit_v2_built(built)


def main():
    args = parse_cli()
    built = build_all(args.source_obj)
    topo = run_selfcheck(built)
    print(
        "topo garment_ok=%s components=%s loops=%s guan_ok=%s feet_min_z=%s twist=%s shared=%s"
        % (
            topo["garment"]["ok"],
            topo["garment"]["components"],
            topo["garment"]["loop_count"],
            topo["guan"]["ok"],
            built["feet_min_z"],
            built["sleeve_frame"]["max_ring_twist_deg"],
            built["armhole_join"]["shared_indices"],
        )
    )
    if not topo["ok"]:
        write_report(
            args.output_dir,
            built,
            topo,
            execution_kind="expected",
            status="TOPO_FAIL",
            blender_present=B.bpy is not None,
            blender_version=None if B.bpy is None else "%d.%d.%d" % tuple(B.bpy.app.version),
            outputs=[],
        )
        raise RuntimeError("CT-COSTUME-TOPO-01 mesh contract failed; not minting another version")
    if B.bpy is None:
        write_report(
            args.output_dir,
            built,
            topo,
            execution_kind="expected",
            status="UNRUN",
            blender_present=False,
            blender_version=None,
            outputs=[],
        )
        print("topology v2 UNRUN tris=%s" % sum(c["tris"] for c in built["census"].values()))
        return 0
    outputs, glb_bytes = blender_export(args, built)
    write_report(
        args.output_dir,
        built,
        topo,
        execution_kind="real",
        status="EXPORTED",
        blender_present=True,
        blender_version="%d.%d.%d" % tuple(B.bpy.app.version),
        outputs=outputs,
        glb_bytes=glb_bytes,
    )
    print("exported topology v2 to", args.output_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
