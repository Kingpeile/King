#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CT-BASE-01 — MPFB2 base.obj anatomy start (body group only).

Not a Zhuge product. Does not claim G1–G5 or art PASS.
No armature. Cannot walk. Frozen zhuge-volume-v2 generators are not used.

Mac Blender 5.2.1:
  blender -b -P prepare_anatomy_base.py -- --source-obj SOURCE --output-dir DIR

Cloud / no bpy:
  python3 prepare_anatomy_base.py --source-obj SOURCE --output-dir DIR
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from datetime import datetime, timezone

try:
    import bpy  # type: ignore
except ImportError:
    bpy = None


TASK_ID = "CT-BASE-01"
PINNED_COMMIT = "437dd513888a92399d1d3200d2e80859fae55abc"
PINNED_REPO_PATH = "src/mpfb/data/3dobjs/base.obj"
PINNED_SHA256 = "8e761e6624b8f54536409135d1636da63b32486a90d4897f84e121d144f6fb4c"
PINNED_BYTES = 1749303
PINNED_RAW_URL = (
    "https://raw.githubusercontent.com/makehumancommunity/mpfb2/"
    + PINNED_COMMIT
    + "/"
    + PINNED_REPO_PATH
)
TARGET_HEIGHT_M = 1.78
KEEP_GROUP = "body"
ROOT_NAME = "AnatomyBase_Root"
UNKNOWN = "UNKNOWN"

HERE = os.path.dirname(os.path.abspath(__file__))


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

    def nrm(self):
        L = self.length()
        if L < 1e-12:
            return V(0, 0, 1)
        return V(self.x / L, self.y / L, self.z / L)

    def xyz(self):
        return (self.x, self.y, self.z)


def argv_after_dash():
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1 :]
    return sys.argv[1:]


def parse_cli():
    p = argparse.ArgumentParser(description="CT-BASE-01 anatomy base from pinned MPFB2 body group")
    p.add_argument("--source-obj", default=None, help="Path to pinned base.obj (SHA256 checked)")
    p.add_argument("--output-dir", default=None, help="Write GLB/blend/png/JSON only here")
    p.add_argument("--skip-render", action="store_true")
    args, _unknown = p.parse_known_args(argv_after_dash())
    if not args.source_obj:
        args.source_obj = os.path.join(HERE, "source", "base.obj")
    if not args.output_dir:
        args.output_dir = os.path.join(HERE, "output")
    args.source_obj = os.path.abspath(args.source_obj)
    args.output_dir = os.path.abspath(args.output_dir)
    return args


def safe_join(output_dir, name):
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


def refuse_frozen_dir(path):
    frozen = os.path.abspath(os.path.join(HERE, "..", "zhuge-volume-v2"))
    target = os.path.abspath(path)
    try:
        if os.path.commonpath([frozen, target]) == frozen:
            raise RuntimeError("refusing to write into frozen dir %s" % frozen)
    except ValueError:
        pass


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def verify_source(path):
    if not os.path.isfile(path):
        raise RuntimeError(
            "source OBJ missing: %s\nDownload the pinned file (data only, do not clone MPFB):\n  %s\nExpected SHA256 %s (%d bytes)"
            % (path, PINNED_RAW_URL, PINNED_SHA256, PINNED_BYTES)
        )
    size = os.path.getsize(path)
    digest = sha256_file(path)
    if size != PINNED_BYTES or digest != PINNED_SHA256:
        raise RuntimeError(
            "SOURCE SHA MISMATCH (refusing to continue).\n"
            "  path: %s\n"
            "  got bytes=%d sha256=%s\n"
            "  pin bytes=%d sha256=%s\n"
            "  commit %s  %s"
            % (path, size, digest, PINNED_BYTES, PINNED_SHA256, PINNED_COMMIT, PINNED_REPO_PATH)
        )
    return {"path": path, "bytes": size, "sha256": digest, "pin_ok": True}


def parse_obj_groups(path):
    """Keep face order and UV indices. Do not rebuild topology."""
    verts = []
    uvs = []
    groups = {}
    current = "(none)"
    groups[current] = 0
    body_faces = []  # list of list[(vi, ti)] 1-based
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            parts = s.split()
            k = parts[0]
            if k == "v":
                verts.append((float(parts[1]), float(parts[2]), float(parts[3])))
            elif k == "vt":
                uvs.append((float(parts[1]), float(parts[2])))
            elif k in ("g", "o"):
                current = parts[1] if len(parts) > 1 else ""
                groups.setdefault(current, 0)
            elif k == "f":
                groups[current] = groups.get(current, 0) + 1
                if current != KEEP_GROUP:
                    continue
                corners = []
                for tok in parts[1:]:
                    bits = tok.split("/")
                    vi = int(bits[0])
                    ti = int(bits[1]) if len(bits) > 1 and bits[1] else None
                    corners.append((vi, ti))
                if len(corners) < 3:
                    raise RuntimeError("body face with <3 corners")
                body_faces.append(corners)
    if KEEP_GROUP not in groups or groups[KEEP_GROUP] == 0:
        raise RuntimeError("OBJ has no faces in group %r" % KEEP_GROUP)
    if len(body_faces) != groups[KEEP_GROUP]:
        raise RuntimeError("body face count mismatch")
    dropped = {g: c for g, c in groups.items() if g != KEEP_GROUP and c}
    return {
        "verts": verts,
        "uvs": uvs,
        "body_faces": body_faces,
        "group_counts": groups,
        "dropped_groups": dropped,
        "source_vert_count": len(verts),
        "source_face_count": sum(groups.values()),
        "source_uv_count": len(uvs),
    }


def _finite3(t):
    return all(math.isfinite(c) for c in t)


def extract_body(parsed):
    faces = parsed["body_faces"]
    src_v = parsed["verts"]
    src_uv = parsed["uvs"]
    used_v = set()
    used_t = set()
    for corners in faces:
        for vi, ti in corners:
            if vi == 0:
                raise RuntimeError("OBJ index 0 is invalid")
            used_v.add(vi)
            if ti is not None:
                if ti == 0:
                    raise RuntimeError("UV index 0 is invalid")
                used_t.add(ti)
    # compact unused helper verts; body vertex order is the original order of used indices
    v_old = sorted(used_v)
    t_old = sorted(used_t) if used_t else []
    v_map = {old: i for i, old in enumerate(v_old)}
    t_map = {old: i for i, old in enumerate(t_old)}
    verts = []
    for old in v_old:
        if old < 0:
            idx = len(src_v) + old + 1
        else:
            idx = old
        if idx < 1 or idx > len(src_v):
            raise RuntimeError("body vertex index out of range: %s" % old)
        p = src_v[idx - 1]
        if not _finite3(p):
            raise RuntimeError("non-finite source vertex %s" % (p,))
        verts.append(p)
    uvs = []
    for old in t_old:
        if old < 0:
            idx = len(src_uv) + old + 1
        else:
            idx = old
        if idx < 1 or idx > len(src_uv):
            raise RuntimeError("body UV index out of range: %s" % old)
        uv = src_uv[idx - 1]
        if not all(math.isfinite(c) for c in uv):
            raise RuntimeError("non-finite UV %s" % (uv,))
        uvs.append(uv)
    out_faces = []
    uv_loops = []
    for corners in faces:
        fidx = []
        uloop = []
        for vi, ti in corners:
            fidx.append(v_map[vi])
            uloop.append(None if ti is None else t_map[ti])
        if len(set(fidx)) < 3:
            raise RuntimeError("degenerate body face")
        out_faces.append(tuple(fidx))
        uv_loops.append(tuple(uloop))
    return {
        "verts": verts,
        "uvs": uvs,
        "faces": out_faces,
        "uv_loops": uv_loops,
        "remaining_face_count": len(out_faces),
        "remaining_vert_count": len(verts),
        "remaining_uv_count": len(uvs),
    }


def obj_to_blender_meters(verts):
    """MH OBJ is Y-up (decimeter-class units). Uniform scale + translate only.

    Blender Z-up, feet at Z=0, height = 1.78 m. +Z_obj (MH forward) -> -Y_blender
    so a front camera on -Y sees the face, matching the rest of this repo.
    """
    ys = [p[1] for p in verts]
    ymin, ymax = min(ys), max(ys)
    height = ymax - ymin
    if height < 1e-8:
        raise RuntimeError("body height is zero")
    scale = TARGET_HEIGHT_M / height
    raw = []
    for x, y, z in verts:
        bx = x * scale
        by = -z * scale
        bz = (y - ymin) * scale
        raw.append((bx, by, bz))
    xs = [p[0] for p in raw]
    ys2 = [p[1] for p in raw]
    zs = [p[2] for p in raw]
    cx = 0.5 * (min(xs) + max(xs))
    cy = 0.5 * (min(ys2) + max(ys2))
    out = [(p[0] - cx, p[1] - cy, p[2]) for p in raw]
    zs = [p[2] for p in out]
    xs = [p[0] for p in out]
    ys2 = [p[1] for p in out]
    bbox = {
        "min": [min(xs), min(ys2), min(zs)],
        "max": [max(xs), max(ys2), max(zs)],
    }
    measured_h = bbox["max"][2] - bbox["min"][2]
    if abs(measured_h - TARGET_HEIGHT_M) > 1e-6:
        raise RuntimeError("height after scale is %s, want %s" % (measured_h, TARGET_HEIGHT_M))
    if abs(bbox["min"][2]) > 1e-8:
        raise RuntimeError("feet are not at 0 (min z=%s)" % bbox["min"][2])
    return out, bbox, scale, ymin


def face_normals(verts, faces):
    nrms = []
    bad = 0
    for f in faces:
        acc = V(0, 0, 0)
        for i in range(1, len(f) - 1):
            a = V(verts[f[0]])
            b = V(verts[f[i]])
            c = V(verts[f[i + 1]])
            acc = acc + (b - a).cross(c - a)
        if acc.length() < 1e-12:
            bad += 1
            nrms.append(V(0, 0, 1))
        else:
            n = acc.nrm()
            if not _finite3(n.xyz()):
                raise RuntimeError("non-finite normal")
            nrms.append(n)
    return nrms, bad


def bbox_of(verts):
    xs = [p[0] for p in verts]
    ys = [p[1] for p in verts]
    zs = [p[2] for p in verts]
    return {"min": [min(xs), min(ys), min(zs)], "max": [max(xs), max(ys), max(zs)]}


def write_json(path, payload):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def build_report(source_info, parsed, body, blender_verts, bbox, scale, y_min_obj, nrm_bad, execution_kind, status, blender_present, blender_version, outputs, glb_bytes=None, notes=None):
    dropped = parsed["dropped_groups"]
    return {
        "task_id": TASK_ID,
        "title": "MPFB2 body-group anatomy base (not Zhuge)",
        "status": status,
        "execution_kind": execution_kind,
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "not_a_zhuge_product": True,
        "g1_g5_claimed": False,
        "art_approval": False,
        "art_pass": False,
        "hand_sculpt_path_c_is_not_proven": True,
        "empty_robe_is_not_a_body": True,
        "armature": False,
        "skin": False,
        "animations": False,
        "can_walk": False,
        "can_move": False,
        "declaration": "Static anatomy mesh only. No armature. Do not claim it can walk or move.",
        "pinned_source": {
            "commit": PINNED_COMMIT,
            "repo_path": PINNED_REPO_PATH,
            "raw_url": PINNED_RAW_URL,
            "sha256": PINNED_SHA256,
            "bytes": PINNED_BYTES,
            "license": "MPFB LICENSE.md section C + obj header = CC0 base mesh",
        },
        "source_verified": source_info,
        "keep_group": KEEP_GROUP,
        "dropped_groups": dropped,
        "dropped_face_count": int(sum(dropped.values())),
        "source_counts": {
            "verts": parsed["source_vert_count"],
            "faces": parsed["source_face_count"],
            "uvs": parsed["source_uv_count"],
            "body_group_faces_in_file": parsed["group_counts"].get(KEEP_GROUP),
        },
        "remaining_face_count_measured": body["remaining_face_count"],
        "remaining_vert_count_measured": body["remaining_vert_count"],
        "remaining_uv_count_measured": body["remaining_uv_count"],
        "topology": {
            "rebuilt": False,
            "heavy_deform": False,
            "uniform_scale_and_translate_only": True,
            "uv_preserved": True,
            "face_order_preserved": True,
        },
        "units": "meters",
        "rootName": ROOT_NAME,
        "upAxis": {
            "expected_blender": "Z",
            "expected_glb": "Y",
            "measured_glb": UNKNOWN if execution_kind != "real" else "Y",
        },
        "height": {
            "target_m": TARGET_HEIGHT_M,
            "expected_blender_m": round(bbox["max"][2] - bbox["min"][2], 6),
            "footOffset_blender_z_min": round(bbox["min"][2], 6),
            "obj_y_up_height_before_scale": round(TARGET_HEIGHT_M / scale, 6),
            "uniform_scale": scale,
            "obj_y_min_before_scale": y_min_obj,
        },
        "bbox": {
            "expected_blender_zup": {
                "min": [round(c, 6) for c in bbox["min"]],
                "max": [round(c, 6) for c in bbox["max"]],
            },
            "measured_glb_yup": UNKNOWN,
        },
        "finite_checks": {
            "verts": True,
            "indices": True,
            "normals": True,
            "zero_area_faces": nrm_bad,
        },
        "glb_export": {
            "contents": "anatomy_body_only",
            "rootName": ROOT_NAME,
            "grey_shader": True,
            "yup": True,
            "bytes": glb_bytes if glb_bytes is not None else UNKNOWN,
        },
        "blender_present": blender_present,
        "blender_version_expected": "5.2.1",
        "blender_version_actual": blender_version,
        "outputs": outputs,
        "notes": notes
        or [
            "Anatomy start only. Not clothes, beard, fan, or palace.",
            "G1–G5 remain later gates. This package does not claim them.",
            "Cloud UNRUN means no GLB/PNG were written by Blender.",
        ],
        "unverified_until_mac_blender": [
            "Y-up GLB import in Blender 5.2.1",
            "four review views of the grey body",
            "feet at 0 and height 1.78 m after exporter",
            "UV still attached after glTF",
        ],
    }


def cloud_prepare(args, source_info):
    parsed = parse_obj_groups(args.source_obj)
    body = extract_body(parsed)
    blender_verts, bbox, scale, y_min = obj_to_blender_meters(body["verts"])
    nrms, nrm_bad = face_normals(blender_verts, body["faces"])
    del nrms
    os.makedirs(args.output_dir, exist_ok=True)
    refuse_frozen_dir(args.output_dir)
    compile_ok = True
    compile_err = None
    try:
        import py_compile

        py_compile.compile(os.path.abspath(__file__), doraise=True)
    except Exception as exc:
        compile_ok = False
        compile_err = str(exc)
    report = build_report(
        source_info,
        parsed,
        body,
        blender_verts,
        bbox,
        scale,
        y_min,
        nrm_bad,
        execution_kind="expected",
        status="UNRUN",
        blender_present=False,
        blender_version=None,
        outputs=[],
        notes=[
            "Generator census only. bpy missing — no GLB/blend/png written.",
            "SHA256 pin matched. Remaining faces measured from the OBJ body group.",
            "Not a Zhuge product. G1–G5 not claimed. No armature; cannot walk.",
            "py_compile: %s" % ("pass" if compile_ok else "fail: %s" % compile_err),
        ],
    )
    report["static_checks"] = {
        "py_compile": "pass" if compile_ok else "fail",
        "py_compile_error": compile_err,
        "sha256_pin": "match",
        "filepath_guard": _selftest_filepath_guard(),
    }
    write_json(safe_join(args.output_dir, "anatomy_report.json"), report)
    print(
        "anatomy UNRUN remaining_faces=%s verts=%s height=%.4f foot_z=%.4f"
        % (
            body["remaining_face_count"],
            body["remaining_vert_count"],
            bbox["max"][2] - bbox["min"][2],
            bbox["min"][2],
        )
    )
    return report, parsed, body, blender_verts, bbox, scale, y_min, nrm_bad


def _op_label(op):
    if op is None:
        return "operator"
    for attr in ("idname", "bl_idname"):
        val = getattr(op, attr, None)
        if val:
            return str(val)
    return repr(op)


def operator_property_ids(op):
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
    for key in required:
        if key not in original:
            continue
        orig = original.get(key)
        got = filtered.get(key)
        orig_empty = orig is None or (isinstance(orig, str) and not str(orig).strip())
        got_empty = got is None or (isinstance(got, str) and not str(got).strip())
        if orig_empty:
            raise RuntimeError("%s: required %r is empty (%r)." % (op_label, key, orig))
        if key not in filtered or got_empty:
            raise RuntimeError(
                "%s: required %r dropped by RNA filter (got %r). Use get_rna_type()."
                % (op_label, key, got)
            )
    return filtered


def filter_op_kwargs(op, kwargs, required=("filepath",)):
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


def look_at(obj, target):
    from mathutils import Vector

    loc = Vector(obj.location)
    tgt = Vector(target)
    obj.rotation_euler = (tgt - loc).to_track_quat("-Z", "Y").to_euler()


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


def setup_cameras(bb, res_x=1920, res_y=1080):
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


def make_grey():
    mat = bpy.data.materials.new("M_AnatomyGrey")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = None
    for n in nt.nodes:
        if n.type == "BSDF_PRINCIPLED":
            bsdf = n
            break
    if bsdf is None:
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    col = (0.46, 0.46, 0.46, 1.0)
    for key in ("Base Color", "Base Color"):
        sock = bsdf.inputs.get(key)
        if sock is not None:
            sock.default_value = col
            break
    for key in ("Roughness",):
        sock = bsdf.inputs.get(key)
        if sock is not None:
            sock.default_value = 0.62
    for key in ("Metallic", "Metalness"):
        sock = bsdf.inputs.get(key)
        if sock is not None:
            sock.default_value = 0.0
    for key in ("Specular IOR Level", "Specular"):
        sock = bsdf.inputs.get(key)
        if sock is not None:
            sock.default_value = 0.18
            break
    return mat


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


def build_mesh_object(blender_verts, body, parent, mat):
    me = bpy.data.meshes.new("Anatomy_Body")
    me.from_pydata(blender_verts, [], [tuple(f) for f in body["faces"]])
    me.validate(clean_customdata=False)
    me.update()
    if len(me.polygons) != len(body["faces"]):
        raise RuntimeError(
            "Blender changed face count (%s -> %s); refusing topology rebuild"
            % (len(body["faces"]), len(me.polygons))
        )
    for p in me.polygons:
        p.use_smooth = True
    uv = me.uv_layers.new(name="UVMap")
    if uv is None:
        raise RuntimeError("failed to create UVMap")
    uvs = body["uvs"]
    loops = body["uv_loops"]
    if len(me.loops) != sum(len(f) for f in body["faces"]):
        raise RuntimeError("loop count != face corners; refusing to invent UVs")
    li = 0
    for uloop in loops:
        for ti in uloop:
            if ti is None:
                uv.data[li].uv = (0.0, 0.0)
            else:
                u, v = uvs[ti]
                uv.data[li].uv = (u, v)
            li += 1
    for p in me.polygons:
        n = p.normal
        if not all(math.isfinite(c) for c in n):
            raise RuntimeError("non-finite Blender polygon normal")
    obj = bpy.data.objects.new("Anatomy_Body", me)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(mat)
    if parent:
        obj.parent = parent
    return obj


def _under_root(obj, root):
    p = obj
    while p is not None:
        if p == root:
            return True
        p = p.parent
    return False


def export_glb(path, root_name=ROOT_NAME):
    root = bpy.data.objects.get(root_name)
    if root is None:
        raise RuntimeError("missing %s" % root_name)
    scene_col = bpy.context.scene.collection
    parked = []
    for obj in list(scene_col.objects):
        if not _under_root(obj, root):
            scene_col.objects.unlink(obj)
            parked.append(obj)
    try:
        if not path:
            raise RuntimeError("export_glb: empty filepath")
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


def blender_prepare(args, source_info, parsed, body, blender_verts, bbox, scale, y_min, nrm_bad):
    clear_scene()
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    world = bpy.data.worlds.new("AnatomyWorld")
    scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs[0].default_value = (0.22, 0.22, 0.22, 1.0)
    bg.inputs[1].default_value = 0.4
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(bg.outputs[0], out.inputs[0])

    root = bpy.data.objects.new(ROOT_NAME, None)
    bpy.context.scene.collection.objects.link(root)
    mat = make_grey()
    build_mesh_object(blender_verts, body, root, mat)

    sun = bpy.data.lights.new("Key", "SUN")
    sun.energy = 4.0
    sun.color = (1.0, 0.97, 0.92)
    sun_obj = bpy.data.objects.new("Key", sun)
    sun_obj.location = (2.2, -2.6, 4.0)
    sun_obj.rotation_euler = (math.radians(50), 0, math.radians(-40))
    bpy.context.scene.collection.objects.link(sun_obj)
    fill = bpy.data.lights.new("Fill", "AREA")
    fill.energy = 120.0
    fill.color = (0.7, 0.78, 1.0)
    fill.size = 2.0
    fill_obj = bpy.data.objects.new("Fill", fill)
    fill_obj.location = (-2.4, -1.2, 1.6)
    bpy.context.scene.collection.objects.link(fill_obj)

    cams = setup_cameras(bbox)
    engine = scene.render.engine
    try:
        items = [e.identifier for e in scene.render.bl_rna.properties["engine"].enum_items]
    except Exception:
        items = []
    for cand in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "CYCLES"):
        if not items or cand in items:
            scene.render.engine = cand
            engine = cand
            break

    os.makedirs(args.output_dir, exist_ok=True)
    refuse_frozen_dir(args.output_dir)
    blend_name = "anatomy_base.blend"
    glb_name = "anatomy_base.glb"
    blend_path = safe_join(args.output_dir, blend_name)
    glb_path = safe_join(args.output_dir, glb_name)
    bpy.ops.wm.save_as_mainfile(
        **filter_op_kwargs(
            bpy.ops.wm.save_as_mainfile,
            {"filepath": blend_path, "check_existing": False},
        )
    )
    export_glb(glb_path)
    glb_bytes = os.path.getsize(glb_path) if os.path.isfile(glb_path) else None
    renders = render_views(cams, args.output_dir, args.skip_render)
    outputs = [blend_name, glb_name] + renders
    report = build_report(
        source_info,
        parsed,
        body,
        blender_verts,
        bbox,
        scale,
        y_min,
        nrm_bad,
        execution_kind="real",
        status="EXPORTED",
        blender_present=True,
        blender_version="%d.%d.%d" % tuple(bpy.app.version),
        outputs=outputs,
        glb_bytes=glb_bytes,
        notes=[
            "Blender exported grey anatomy GLB. Not a Zhuge product.",
            "G1–G5 not claimed. No armature; cannot walk.",
            "Review views are the grey body only — no palace, no clothes.",
        ],
    )
    report["render_engine"] = engine
    write_json(safe_join(args.output_dir, "anatomy_report.json"), report)
    print("exported anatomy to", args.output_dir)
    return report


def v_copy_selftest():
    """Pure-Python type-boundary check. No bpy. Camera numbers unchanged."""
    a = V(1.0, 2.0, 3.0)
    try:
        float(a[0])
        print("repro: FAILED to raise")
        return 1
    except TypeError as exc:
        print("repro: %s: %s" % (type(exc).__name__, exc))
    copied = V(a)
    print("pass: V<-V (%s, %s, %s)" % (copied.x, copied.y, copied.z))
    from_tuple = V((0.0, 0.0, 0.0))
    print("pass: tuple->V (%s, %s, %s)" % (from_tuple.x, from_tuple.y, from_tuple.z))
    corners = [
        V(x, y, z) for x in (-0.2, 0.2) for y in (-0.2, 0.2) for z in (0.0, 1.78)
    ]
    dist = _fit_cam_distance(corners, V(0.0, -1.0, 0.0), V(0.0, 0.0, 0.89), 50.0, 1920, 1080)
    ok = math.isfinite(dist) and dist > 0.0
    print("pass: _fit_cam_distance V target dist=%s finite_positive=%s" % (dist, ok))
    return 0 if ok else 1


def main():
    if "--v-copy-selftest" in argv_after_dash():
        return v_copy_selftest()
    args = parse_cli()
    refuse_frozen_dir(args.output_dir)
    source_info = verify_source(args.source_obj)
    if bpy is None:
        cloud_prepare(args, source_info)
        return 0
    parsed = parse_obj_groups(args.source_obj)
    body = extract_body(parsed)
    blender_verts, bbox, scale, y_min = obj_to_blender_meters(body["verts"])
    _nrms, nrm_bad = face_normals(blender_verts, body["faces"])
    blender_prepare(args, source_info, parsed, body, blender_verts, bbox, scale, y_min, nrm_bad)
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
