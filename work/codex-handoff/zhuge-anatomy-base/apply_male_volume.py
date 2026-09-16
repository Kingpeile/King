#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CT-BASE-02 — one adult-male fuller-volume candidate on the pinned hm08 base.

Imports prepare_anatomy_base helpers. Does not rewrite that file.
Morph full 19158 source verts, then the same body-group keep/drop as BASE-01.
Not a Zhuge product. Not G1–G5. No armature. Cannot walk.
"""
from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "anatomy_base_frozen", os.path.join(HERE, "prepare_anatomy_base.py")
)
B = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(B)

TASK_ID = "CT-BASE-02"
ROOT_NAME = "AnatomyMale_Root"
TARGET_DIR = os.path.join(HERE, "source", "targets")
PINNED_COMMIT = B.PINNED_COMMIT
EXPECTED_SOURCE_VERTS = 19158

# Official MPFB2 macro endpoints (CC0). Weights are the MH slider endpoints, not an X-scale.
MORPHS = (
    {
        "file": "asian-male-young.target.gz",
        "repo_path": "src/mpfb/data/targets/macrodetails/asian-male-young.target.gz",
        "sha256": "0928ed8b9f08f60afb9884cf9e9f33a939ed3a85d7f136de9ccc88a76981d6d7",
        "bytes": 130005,
        "weight": 1.0,
    },
    {
        "file": "universal-male-young-maxmuscle-averageweight.target.gz",
        "repo_path": "src/mpfb/data/targets/macrodetails/universal-male-young-maxmuscle-averageweight.target.gz",
        "sha256": "833caafc302bd9306de494f32ee1bc51d3a2e6641183329b031ac06ef0f4277e",
        "bytes": 45597,
        "weight": 1.0,
    },
)
LICENSE_PIN = {
    "file": "LICENSE.md",
    "repo_path": "LICENSE.md",
    "sha256": "5cefb60680cb9efd4550a2e65d719021cfbec9dad3658481d11d48ae863ce04d",
    "bytes": 3188,
    "note": "Section C: bundled targets/modifiers are CC0 1.0",
}

BASELINE_MAC_613317C = {
    "commit": "613317c710e4e339dda3663365dedb54871e4f14",
    "blender": "5.2.1",
    "exit": 0,
    "glb_bytes": 626508,
    "mesh": 1,
    "tris": 26756,
    "height_m": 1.77999997,
    "minY": 0,
    "uvs": 14517,
    "finite_indices": True,
    "keep_for_comparison": True,
}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_pin(path, spec):
    if not os.path.isfile(path):
        raise RuntimeError("missing morph/license file: %s" % path)
    size = os.path.getsize(path)
    digest = sha256_file(path)
    if size != spec["bytes"] or digest != spec["sha256"]:
        raise RuntimeError(
            "MORPH SHA MISMATCH %s\n  got bytes=%d sha256=%s\n  pin bytes=%d sha256=%s"
            % (path, size, digest, spec["bytes"], spec["sha256"])
        )
    return {"path": path, "bytes": size, "sha256": digest, "pin_ok": True}


def load_target_gz(path, nverts):
    """MakeHuman/MPFB target: `index dx dy dz` on hm08. 0-based indices."""
    rows = 0
    vmax = -1
    deltas = {}
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            parts = s.split()
            if len(parts) != 4:
                raise RuntimeError("bad target line in %s: %r" % (path, s))
            idx = int(parts[0])
            if idx < 0 or idx >= nverts:
                raise RuntimeError(
                    "target index %s out of range for %s verts in %s" % (idx, nverts, path)
                )
            dx, dy, dz = float(parts[1]), float(parts[2]), float(parts[3])
            if not all(map(math.isfinite, (dx, dy, dz))):
                raise RuntimeError("non-finite delta at %s in %s" % (idx, path))
            deltas[idx] = (dx, dy, dz)
            rows += 1
            if idx > vmax:
                vmax = idx
    return {"deltas": deltas, "rows": rows, "max_index": vmax}


def apply_morphs(verts, morph_payloads):
    """Accumulate official targets on the FULL source vertex list. No axis scale."""
    out = [list(p) for p in verts]
    applied = []
    for spec, payload in zip(MORPHS, morph_payloads):
        w = float(spec["weight"])
        n = 0
        for idx, (dx, dy, dz) in payload["deltas"].items():
            out[idx][0] += dx * w
            out[idx][1] += dy * w
            out[idx][2] += dz * w
            n += 1
        applied.append({"file": spec["file"], "weight": w, "rows": n, "max_index": payload["max_index"]})
    for p in out:
        if not all(map(math.isfinite, p)):
            raise RuntimeError("non-finite vertex after morph")
    return [tuple(p) for p in out], applied


def not_uniform_x_widen(base_body_verts, male_body_verts):
    """Reject a single X scale. Gender/muscle targets must move Y/Z too."""
    if len(base_body_verts) != len(male_body_verts):
        raise RuntimeError("body vert count changed")
    dx, dy, dz, xs = [], [], [], []
    for a, b in zip(base_body_verts, male_body_verts):
        dx.append(b[0] - a[0])
        dy.append(b[1] - a[1])
        dz.append(b[2] - a[2])
        xs.append(a[0])
    xx = sum(x * x for x in xs)
    xdx = sum(x * d for x, d in zip(xs, dx))
    a = (xdx / xx) if xx > 1e-12 else 0.0
    resid = [d - a * x for d, x in zip(dx, xs)]
    var_dx = sum(d * d for d in dx) / len(dx)
    var_r = sum(r * r for r in resid) / len(resid)
    r2 = 1.0 - (var_r / var_dx) if var_dx > 1e-18 else 0.0
    dy_std = math.sqrt(sum((d - sum(dy) / len(dy)) ** 2 for d in dy) / len(dy))
    dz_std = math.sqrt(sum((d - sum(dz) / len(dz)) ** 2 for d in dz) / len(dz))
    max_abs = max(max(abs(v) for v in dx), max(abs(v) for v in dy), max(abs(v) for v in dz))
    ok = max_abs > 1e-4 and (r2 < 0.98 or dy_std > 1e-3 or dz_std > 1e-3)
    return {
        "ok": ok,
        "max_abs_delta": max_abs,
        "dx_vs_x_r2": round(r2, 6),
        "dy_std": round(dy_std, 6),
        "dz_std": round(dz_std, 6),
        "note": "ok means not a uniform X-widen",
    }


def parse_cli():
    p = B.argparse.ArgumentParser(description="CT-BASE-02 adult-male fuller-volume candidate")
    p.add_argument("--source-obj", default=None)
    p.add_argument("--output-dir", default=None)
    p.add_argument("--skip-render", action="store_true")
    args, _unknown = p.parse_known_args(B.argv_after_dash())
    if not args.source_obj:
        args.source_obj = os.path.join(HERE, "source", "base.obj")
    if not args.output_dir:
        args.output_dir = os.path.join(HERE, "male_out")
    args.source_obj = os.path.abspath(args.source_obj)
    args.output_dir = os.path.abspath(args.output_dir)
    return args


def run_checks(source_obj):
    source_info = B.verify_source(source_obj)
    parsed = B.parse_obj_groups(source_obj)
    nverts = len(parsed["verts"])
    if nverts != EXPECTED_SOURCE_VERTS:
        raise RuntimeError("source vert count %s != %s" % (nverts, EXPECTED_SOURCE_VERTS))
    license_info = verify_pin(os.path.join(TARGET_DIR, LICENSE_PIN["file"]), LICENSE_PIN)
    morph_payloads = []
    morph_info = []
    for spec in MORPHS:
        path = os.path.join(TARGET_DIR, spec["file"])
        pin = verify_pin(path, spec)
        payload = load_target_gz(path, nverts)
        morph_payloads.append(payload)
        morph_info.append({**pin, "repo_path": spec["repo_path"], "weight": spec["weight"], "rows": payload["rows"], "max_index": payload["max_index"]})
    morphed_verts, applied = apply_morphs(parsed["verts"], morph_payloads)
    parsed_male = dict(parsed)
    parsed_male["verts"] = morphed_verts
    base_body = B.extract_body(parsed)
    male_body = B.extract_body(parsed_male)
    if male_body["remaining_face_count"] != base_body["remaining_face_count"]:
        raise RuntimeError("face count changed — topology was rebuilt")
    if male_body["remaining_uv_count"] != base_body["remaining_uv_count"]:
        raise RuntimeError("UV count changed")
    xcheck = not_uniform_x_widen(base_body["verts"], male_body["verts"])
    if not xcheck["ok"]:
        raise RuntimeError("morph looks like uniform X-widen: %s" % xcheck)
    blender_verts, bbox, scale, y_min = B.obj_to_blender_meters(male_body["verts"])
    _nrms, nrm_bad = B.face_normals(blender_verts, male_body["faces"])
    return {
        "source_info": source_info,
        "license_info": license_info,
        "morph_info": morph_info,
        "applied": applied,
        "parsed": parsed_male,
        "base_body": base_body,
        "male_body": male_body,
        "blender_verts": blender_verts,
        "bbox": bbox,
        "scale": scale,
        "y_min": y_min,
        "nrm_bad": nrm_bad,
        "xcheck": xcheck,
        "compat": {
            "source_verts": nverts,
            "target_index_range_ok": all(p["max_index"] < nverts for p in morph_payloads),
            "remaining_faces": male_body["remaining_face_count"],
            "remaining_verts": male_body["remaining_vert_count"],
            "remaining_uvs": male_body["remaining_uv_count"],
            "baseline_faces": base_body["remaining_face_count"],
            "uv_preserved": True,
            "topology_preserved": True,
        },
    }


def write_report(output_dir, checks, execution_kind, status, blender_present, blender_version, outputs, glb_bytes=None):
    os.makedirs(output_dir, exist_ok=True)
    B.refuse_frozen_dir(output_dir)
    body = checks["male_body"]
    bbox = checks["bbox"]
    report = {
        "task_id": TASK_ID,
        "title": "Adult-male fuller-volume anatomy candidate (not Zhuge)",
        "status": status,
        "execution_kind": execution_kind,
        "not_a_zhuge_product": True,
        "g1_g5_claimed": False,
        "art_approval": False,
        "armature": False,
        "can_walk": False,
        "declaration": "Static anatomy mesh only. No armature. Do not claim it can walk.",
        "baseline_mac_613317c": BASELINE_MAC_613317C,
        "pinned_base_obj": B.PINNED_SHA256,
        "pinned_commit": PINNED_COMMIT,
        "morphs": checks["morph_info"],
        "license": checks["license_info"],
        "applied": checks["applied"],
        "source_vert_compatibility": checks["compat"],
        "not_uniform_x_widen": checks["xcheck"],
        "remaining_face_count_measured": body["remaining_face_count"],
        "remaining_vert_count_measured": body["remaining_vert_count"],
        "remaining_uv_count_measured": body["remaining_uv_count"],
        "height": {
            "target_m": B.TARGET_HEIGHT_M,
            "expected_blender_m": round(bbox["max"][2] - bbox["min"][2], 6),
            "footOffset_blender_z_min": round(bbox["min"][2], 6),
            "uniform_scale": checks["scale"],
        },
        "bbox": {"expected_blender_zup": {"min": [round(c, 6) for c in bbox["min"]], "max": [round(c, 6) for c in bbox["max"]]}},
        "finite_checks": {"verts": True, "indices": True, "normals": True, "zero_area_faces": checks["nrm_bad"]},
        "glb_export": {"rootName": ROOT_NAME, "grey_shader": True, "yup": True, "bytes": glb_bytes if glb_bytes is not None else B.UNKNOWN},
        "blender_present": blender_present,
        "blender_version_actual": blender_version,
        "outputs": outputs,
        "notes": [
            "Morph full hm08 verts then body-group filter. Cloud does not run Blender.",
            "Not a Zhuge product. G1–G5 not claimed. Compare grey views to BASE-01.",
        ],
        "unverified_until_mac_blender": [
            "grey 4-view vs BASE-01 chest/waist/hip read as adult male",
            "Y-up GLB import, height 1.78 m, minY 0 after exporter",
            "UV still attached after glTF",
        ],
    }
    B.write_json(B.safe_join(output_dir, "male_volume_report.json"), report)
    return report


def blender_export(args, checks):
    B.clear_scene()
    scene = B.bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    world = B.bpy.data.worlds.new("AnatomyMaleWorld")
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
    mat = B.make_grey()
    B.build_mesh_object(checks["blender_verts"], checks["male_body"], root, mat)

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

    cams = B.setup_cameras(checks["bbox"])
    os.makedirs(args.output_dir, exist_ok=True)
    B.refuse_frozen_dir(args.output_dir)
    blend_name = "anatomy_male.blend"
    glb_name = "anatomy_male.glb"
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
    outputs = [blend_name, glb_name] + renders
    write_report(
        args.output_dir,
        checks,
        execution_kind="real",
        status="EXPORTED",
        blender_present=True,
        blender_version="%d.%d.%d" % tuple(B.bpy.app.version),
        outputs=outputs,
        glb_bytes=glb_bytes,
    )
    print("exported male anatomy to", args.output_dir)


def main():
    args = parse_cli()
    B.refuse_frozen_dir(args.output_dir)
    checks = run_checks(args.source_obj)
    print(
        "checks source_verts=%s remaining_faces=%s uvs=%s not_uniform_x=%s r2=%s"
        % (
            checks["compat"]["source_verts"],
            checks["compat"]["remaining_faces"],
            checks["compat"]["remaining_uvs"],
            checks["xcheck"]["ok"],
            checks["xcheck"]["dx_vs_x_r2"],
        )
    )
    if B.bpy is None:
        write_report(
            args.output_dir,
            checks,
            execution_kind="expected",
            status="UNRUN",
            blender_present=False,
            blender_version=None,
            outputs=[],
        )
        print("male volume UNRUN remaining_faces=%s" % checks["compat"]["remaining_faces"])
        return 0
    blender_export(args, checks)
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
