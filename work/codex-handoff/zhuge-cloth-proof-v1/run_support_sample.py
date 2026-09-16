#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CT-CLOTH-SUPPORT-02 — bounded left-shoulder support sample.

Thin entry: read-only reuse of run_cloth_proof.py. Does not edit that file,
its out/, or frozen anatomy/clothed trees. Physics params unchanged.
Not a garment. Not 03. Not art PASS.
"""
from __future__ import annotations

import importlib.util
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "cloth_proof_frozen", os.path.join(HERE, "run_cloth_proof.py")
)
P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P)

TASK_ID = "CT-CLOTH-SUPPORT-02"
PROOF_HEAD = "24c90a2de7a709af5369b0a408083101d52ed485"
Y0 = 0.06
Y1 = 0.21
PIN_TARGETS = (0.10, 0.17)
DEFAULT_OUT = os.path.join(HERE, "support-sample-02")
BLOCKED_WRITE = (
    os.path.join(HERE, "out"),
    os.path.abspath(os.path.join(HERE, "run_cloth_proof.py")),
    os.path.abspath(os.path.join(HERE, "README.md")),
    os.path.abspath(os.path.join(HERE, "PATTERN-DIAG.md")),
)


def refuse_legacy_writes(path):
    P.refuse_frozen_writes(path)
    target = os.path.abspath(path)
    for blocked in BLOCKED_WRITE:
        blocked = os.path.abspath(blocked)
        if target == blocked:
            raise RuntimeError("refusing to write frozen proof path %s" % blocked)
        try:
            if os.path.isdir(blocked) and os.path.commonpath([blocked, target]) == blocked:
                raise RuntimeError("refusing to write into frozen proof dir %s" % blocked)
        except ValueError:
            pass


def parse_cli():
    p = P.B.argparse.ArgumentParser(description="CT-CLOTH-SUPPORT-02 bounded support sample")
    p.add_argument("--source-obj", default=None)
    p.add_argument("--output-dir", default=None)
    p.add_argument("--skip-render", action="store_true")
    args, _unknown = p.parse_known_args(P.B.argv_after_dash())
    if not args.source_obj:
        args.source_obj = os.path.join(P.ANATOMY_DIR, "source", "base.obj")
    if not args.output_dir:
        args.output_dir = DEFAULT_OUT
    args.source_obj = os.path.abspath(args.source_obj)
    args.output_dir = os.path.abspath(args.output_dir)
    refuse_legacy_writes(args.output_dir)
    return args


def adjacent_rows(ys, target):
    for i in range(len(ys) - 1):
        if ys[i] <= target <= ys[i + 1]:
            return (i, i + 1)
    raise RuntimeError("no adjacent rows straddle y=%s" % target)


def build_support_cloth(body):
    old = P.build_sample_cloth(body)
    ov = old["verts"]
    x0, x1, z = ov[0][0], ov[P.SEGS_U][0], ov[0][2]
    nu, nv = P.SEGS_U + 1, P.SEGS_V + 1
    ys = [Y0 + (Y1 - Y0) * i / float(P.SEGS_V) for i in range(nv)]
    verts = []
    for i in range(nv):
        for j in range(nu):
            u = j / float(P.SEGS_U)
            verts.append((x0 + (x1 - x0) * u, ys[i], z))
    faces = P.grid_quads(nu, nv)
    rows = []
    groups = []
    for target in PIN_TARGETS:
        pair = adjacent_rows(ys, target)
        rows.extend(pair)
        groups.append({"target_y": target, "rows": list(pair), "ys": [ys[pair[0]], ys[pair[1]]]})
    pin_indices = [i * nu + 0 for i in rows]
    if len(set(pin_indices)) != 4:
        raise RuntimeError("pins must be 4 distinct medial verts, got %s" % pin_indices)
    pin_xyz = [verts[i] for i in pin_indices]
    return {
        "verts": verts,
        "faces": faces,
        "pin_indices": pin_indices,
        "placement": {
            "side": "left",
            "plane": "world XY, gravity -Z",
            "x0": x0,
            "x1": x1,
            "y0": Y0,
            "y1": Y1,
            "z": z,
            "x_z_from": "24c90a2d build_sample_cloth rest x/z (unrounded)",
            "y_fixed": [Y0, Y1],
            "segs_u": P.SEGS_U,
            "segs_v": P.SEGS_V,
            "vert_n": len(verts),
            "quad_n": len(faces),
            "pin_rule": (
                "4 distinct medial (u=0) verts; two adjacent rows nearest y=0.10 "
                "and two adjacent rows nearest y=0.17. Not the full sheet."
            ),
            "pin_groups": groups,
            "pin_indices": pin_indices,
            "pin_xyz": [[float(c) for c in p] for p in pin_xyz],
            "historical_baseline_pins": old["placement"]["pin_indices"],
            "historical_baseline_not_this_control": True,
        },
    }


def geometry_selfcheck(old, cloth):
    pl = cloth["placement"]
    ys = sorted(set(p[1] for p in cloth["verts"]))
    xs = sorted(set(p[0] for p in cloth["verts"]))
    zs = sorted(set(p[2] for p in cloth["verts"]))
    blockers = []
    if abs(min(ys) - Y0) > 1e-12 or abs(max(ys) - Y1) > 1e-12:
        blockers.append("Y range %s %s != %s %s" % (min(ys), max(ys), Y0, Y1))
    if abs(min(xs) - old["verts"][0][0]) > 1e-12 or abs(max(xs) - old["verts"][P.SEGS_U][0]) > 1e-12:
        blockers.append("X does not match frozen sample")
    if abs(min(zs) - old["verts"][0][2]) > 1e-12 or abs(max(zs) - old["verts"][0][2]) > 1e-12:
        blockers.append("Z does not match frozen sample")
    if pl["vert_n"] != 221 or pl["quad_n"] != 192:
        blockers.append("grid %s/%s != 221/192" % (pl["vert_n"], pl["quad_n"]))
    if len(pl["pin_indices"]) != 4 or len(set(pl["pin_indices"])) != 4:
        blockers.append("need 4 distinct pins")
    if set(pl["pin_indices"]) == set(old["placement"]["pin_indices"]):
        blockers.append("pins identical to historical posterior set")
    if len(pl["pin_indices"]) >= pl["vert_n"] * 0.5:
        blockers.append("too many pins")
    for idx in pl["pin_indices"]:
        if idx % (P.SEGS_U + 1) != 0:
            blockers.append("pin %s is not medial u=0" % idx)
    if P.PARAMS["ClothSettings"]["mass"] != 0.3 or P.PARAMS["frames"] != [1, 60]:
        blockers.append("physics params drifted from frozen proof")
    return {"ok": not blockers, "blockers": blockers, "pin_indices": pl["pin_indices"], "pin_xyz": pl["pin_xyz"]}


def run_support_arm(label, use_collision, body, cloth, local_bb, out_dir, skip_render, deadline):
    """Reuse P.run_one_arm; extra frame01 render via eval hook."""
    box = {}
    orig_setup = P.B.setup_cameras
    orig_eval = P.eval_mesh_verts
    orig_render = P.render_local

    def setup_keep(bb, *a, **k):
        cams = orig_setup(bb, *a, **k)
        box["cams"] = cams
        return cams

    def eval_hook(obj):
        verts = orig_eval(obj)
        fr = P.B.bpy.context.scene.frame_current
        if fr == P.FRAME_START and box.get("cams") and not box.get("frame01"):
            arm_dir = P.B.safe_join(out_dir, label)
            orig_render(box["cams"], P.B.safe_join(arm_dir, "frame01"), skip_render)
            box["frame01"] = True
        return verts

    def render_end(cams, arm_dir, skip):
        names = orig_render(cams, os.path.join(arm_dir, "frame60"), skip)
        return ["frame60/" + n for n in names]

    P.B.setup_cameras = setup_keep
    P.eval_mesh_verts = eval_hook
    P.render_local = render_end
    try:
        return P.run_one_arm(
            label, use_collision, body, cloth, local_bb, out_dir, skip_render, deadline
        )
    finally:
        P.B.setup_cameras = orig_setup
        P.eval_mesh_verts = orig_eval
        P.render_local = orig_render


def write_payload(output_dir, body, cloth, selfcheck, geom, local_bb, blender_present, blender_version, physics):
    pair = P.interpret_pair(
        None if physics is None else physics.get("collision_on"),
        None if physics is None else physics.get("collision_off"),
    )
    physics_status = "UNRUN"
    kind = "expected"
    if physics is not None:
        kind = "real"
        if physics.get("timed_out"):
            physics_status = "TIMEOUT"
        elif physics.get("failed"):
            physics_status = "FAIL"
        else:
            physics_status = pair["verdict"]
    payload = {
        "task_id": TASK_ID,
        "title": "Bounded left-shoulder support sample (not a garment)",
        "status": physics_status if blender_present else "UNRUN",
        "execution_kind": kind,
        "physics_status": physics_status,
        "not_a_zhuge_product": True,
        "costume_03_claimed": False,
        "full_garment": False,
        "can_claim_pass": False,
        "physics_response_observed": pair["physics_response_observed"],
        "target_coverage_needs_visual_review": True,
        "declaration": (
            "Same posed male, left sheet only. Physics copied from 24c90a2d. "
            "Y and 4 medial pins changed. Not 03 / not art PASS."
        ),
        "historical_baseline": {
            "head": PROOF_HEAD,
            "scheme": "posterior 4 pins y=0.191-0.248, cloth y=-0.057-0.248",
            "not_this_run_control": True,
            "note": "24c90a2d Mac pair is history, not the on/off of this sample.",
        },
        "diag_note": (
            "PATTERN-DIAG claim that the sheet first hits the back shoulder and "
            "cannot crest the apex is inference (no per-frame contact). "
            "Old PATTERN-DIAG.md was not rewritten. Support split is the testable hypothesis."
        ),
        "input": {
            "pr17_head": P.INPUT_HEAD,
            "support_body_commit": P.SUPPORT_BODY_COMMIT,
            "proof_physics_head": PROOF_HEAD,
            "source_read_only": True,
        },
        "params": P.PARAMS,
        "cloth_placement": cloth["placement"],
        "geometry_selfcheck": geom,
        "construction_selfcheck": selfcheck,
        "local_camera_bbox": local_bb,
        "pair_verdict": pair,
        "physics": physics,
        "blender_present": blender_present,
        "blender_version_actual": blender_version,
        "expected_outputs": [
            "collision_on|off/proof.blend",
            "collision_on|off/frame01/view_{front,side,back,lookdown}.png",
            "collision_on|off/frame60/view_{front,side,back,lookdown}.png",
            "collision_on|off/frames.json",
            "collision_on|off/timing.json",
            "evidence.json",
        ],
        "unverified_until_mac_blender": [
            "one same-param CLOTH pair; memory cache false/false both arms",
            "frame01+frame60 4-views: front-apex-back cover, free verts move, no explode",
            "if front/apex still exposed: stop this geometry; no retune, no robe",
        ],
    }
    refuse_legacy_writes(output_dir)
    P.write_evidence(output_dir, payload)
    return payload


def main():
    args = parse_cli()
    if not os.path.isfile(args.source_obj):
        raise RuntimeError("source obj missing: %s" % args.source_obj)
    src_stat = os.stat(args.source_obj)
    body = P.build_posed_body(args.source_obj)
    old = P.build_sample_cloth(body)
    cloth = build_support_cloth(body)
    geom = geometry_selfcheck(old, cloth)
    selfcheck = P.construction_selfcheck(body, cloth)
    local_bb = P.local_bbox(cloth, body)
    print(
        "support-02 geom_ok=%s construct_ok=%s verts=%s pins=%s"
        % (geom["ok"], selfcheck["ok"], cloth["placement"]["vert_n"], cloth["placement"]["pin_indices"])
    )
    if not geom["ok"] or not selfcheck["ok"]:
        payload = write_payload(args.output_dir, body, cloth, selfcheck, geom, local_bb, False, None, None)
        payload["status"] = "CONSTRUCTION_BLOCKED"
        P.write_evidence(args.output_dir, payload)
        raise RuntimeError("support sample blocked: %s %s" % (geom["blockers"], selfcheck["blockers"]))
    if P.B.bpy is None:
        payload = write_payload(args.output_dir, body, cloth, selfcheck, geom, local_bb, False, None, None)
        print("support-02 UNRUN pins=%s" % payload["cloth_placement"]["pin_indices"])
        after = os.stat(args.source_obj)
        if (after.st_mtime, after.st_size) != (src_stat.st_mtime, src_stat.st_size):
            raise RuntimeError("source obj was modified")
        return 0

    deadline = time.monotonic() + P.TIME_BUDGET_S
    physics = {"timed_out": False, "failed": False, "collision_on": None, "collision_off": None}
    keys = (
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
    try:
        on_run = run_support_arm(
            "collision_on", True, body, cloth, local_bb, args.output_dir, args.skip_render, deadline
        )
        physics["collision_on"] = {k: on_run[k] for k in keys}
        physics["collision_on"]["frame_n"] = len(on_run["frames"])
        physics["timed_out"] = on_run["timed_out"]
        if not on_run["timed_out"]:
            off_run = run_support_arm(
                "collision_off", False, body, cloth, local_bb, args.output_dir, args.skip_render, deadline
            )
            physics["collision_off"] = {k: off_run[k] for k in keys}
            physics["collision_off"]["frame_n"] = len(off_run["frames"])
            physics["timed_out"] = physics["timed_out"] or off_run["timed_out"]
        else:
            physics["failed"] = True
            physics["note"] = "collision_on hit 120s; off not started. No param retry."
    except Exception as exc:
        physics["failed"] = True
        physics["error"] = str(exc)
        write_payload(
            args.output_dir,
            body,
            cloth,
            selfcheck,
            geom,
            local_bb,
            True,
            "%d.%d.%d" % tuple(P.B.bpy.app.version),
            physics,
        )
        raise
    payload = write_payload(
        args.output_dir,
        body,
        cloth,
        selfcheck,
        geom,
        local_bb,
        True,
        "%d.%d.%d" % tuple(P.B.bpy.app.version),
        physics,
    )
    after = os.stat(args.source_obj)
    if (after.st_mtime, after.st_size) != (src_stat.st_mtime, src_stat.st_size):
        raise RuntimeError("source obj was modified")
    print("support-02 physics_status=%s" % payload["physics_status"])
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
