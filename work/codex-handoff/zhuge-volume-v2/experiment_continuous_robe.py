#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CT-3D-EXPERIMENT-01 — one continuous robe, then stop.

Imports the FROZEN builder at ea39968852c001ef5321fa476a31b5be3921c578.
Does not edit build_zhuge_v2.py. Does not rewrite report.json.

Replaces Robe_Body + Skirt_Outer/Inner + Robe_Panel_Outer +
Robe_Panel_ShoulderSeal with ONE open wrap from neck opening to hem.
No second misaligned shell. No horizontal shoulder-top seal strip.
"""
from __future__ import annotations

import importlib.util
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FROZEN_BUILDER = os.path.join(HERE, "build_zhuge_v2.py")
FROZEN_COMMIT = "ea39968852c001ef5321fa476a31b5be3921c578"

REPLACED_PARTS = (
    "Robe_Body",
    "Skirt_Outer",
    "Skirt_Inner",
    "Robe_Panel_Outer",
    "Robe_Panel_ShoulderSeal",
)


def load_frozen_builder():
    spec = importlib.util.spec_from_file_location("zhuge_v2_frozen", FROZEN_BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen builder: %s" % FROZEN_BUILDER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


B = load_frozen_builder()
V = B.V


def _continuous_keys():
    """Neck opening → shoulder → chest → waist cinch → hem. One silhouette.

    Shoulder radii stay near the frozen Robe_Body (not the 0.228 hang ring).
    Below the chest the hanging flare of the frozen wrap is kept. Linear
    interp between these keys — no 4 mm offset shell, no 0.35 lerp jump.
    """
    S, C, W, H, HEM = B.SHOULDER_Z, B.CHEST_Z, B.WAIST_Z, B.HIP_Z, B.HEM_Z
    return [
        (0.078, 0.070, S + 0.082, 0.00, 0.000),
        (0.118, 0.100, S + 0.048, 0.00, 0.000),
        (0.168, 0.132, S + 0.008, 0.08, 0.002),
        (0.198, 0.150, S - 0.048, 0.14, 0.004),
        (0.214, 0.160, S - 0.095, 0.22, 0.006),
        (0.236, 0.178, C + 0.020, 0.38, 0.008),
        (0.226, 0.172, W + 0.030, 0.55, 0.010),
        (0.242, 0.186, W - 0.035, 0.70, 0.012),
        (0.290, 0.222, H - 0.070, 0.86, 0.014),
        (0.332, 0.250, 0.38, 1.00, 0.016),
        (0.355, 0.268, HEM + 0.038, 1.00, 0.014),
    ]


def _closed_angles(n):
    return [2.0 * math.pi * j / n for j in range(n)]


def _ring_from_angles(rx, ry, z, angles, fold_scale, outward):
    """Same fold math as frozen panel_arc_ring, but any angle list."""
    a0, a1 = angles[0], angles[-1]
    n = len(angles)
    # panel_arc_ring lerps a0→a1 over n samples; match that when angles are uniform.
    if n >= 2 and abs((a1 - a0) - (angles[1] - angles[0]) * (n - 1)) < 1e-9:
        return B.panel_arc_ring(
            0.0,
            0.012,
            z,
            rx,
            ry,
            a0,
            a1,
            n,
            B.WRAP_FOLDS,
            B.WRAP_RIDGES,
            fold_scale,
            outward,
        )
    row = []
    for a in angles:
        rmod = 1.0
        hang = 0.0
        if fold_scale > 1e-6:
            rmod += 0.022 * fold_scale * math.sin(2.4 * a + 0.35)
            for ang, width, depth in B.WRAP_FOLDS:
                d = abs(math.atan2(math.sin(a - ang), math.cos(a - ang)))
                well = math.exp(-((d / max(width, 1e-4)) ** 2))
                rmod -= (depth / max(rx, 1e-4)) * fold_scale * well
                hang += depth * fold_scale * well * 0.40
            for ang, width, height in B.WRAP_RIDGES:
                d = abs(math.atan2(math.sin(a - ang), math.cos(a - ang)))
                ridge = math.exp(-((d / max(width, 1e-4)) ** 2))
                rmod += (height / max(rx, 1e-4)) * fold_scale * ridge
        x = math.cos(a) * rx * rmod
        y = 0.012 + math.sin(a) * ry * rmod
        rad = V(math.cos(a), math.sin(a), 0.0)
        row.append(V(x, y, z - hang) + rad * outward)
    return row


def build_continuous_robe():
    """ONE open wrap, neck opening → hem. Thickened sheet only — no seal strip."""
    keys = _continuous_keys()
    nv, nu = 20, 28
    open_angles = B._wrap_angles(nu)
    closed_n = B.BODY_N
    closed_angles = _closed_angles(closed_n)
    grid = []
    closed = []
    for i in range(nv):
        t = i / max(1, nv - 1)
        rx, ry, z, fs, outw = B._interp_panel_spec(keys, t)
        grid.append(_ring_from_angles(rx, ry, z, open_angles, fs, outw))
        closed.append(_ring_from_angles(rx, ry, z, closed_angles, fs, outw))

    parts = [
        B.thicken_sheet(grid, lambda tt, uu: 0.0060, "Robe_Continuous", "M_RobeIvory")
    ]
    parts.extend(_opening_linings(grid))
    for col, tag in ((0, "R"), (-1, "L")):
        edge = [row[col] for row in grid]
        parts.append(
            B.sweep_profile(
                edge,
                B._rounded_rect(0.016, 0.005, 3),
                "Robe_PanelFacing_%s" % tag,
                "M_CyanGreen",
                True,
            )
        )
    zs = [B.ring_centroid(r).z for r in grid]
    wi = min(range(len(zs)), key=lambda i: abs(zs[i] - (B.WAIST_Z + 0.012)))
    wi = max(1, min(wi, len(grid) - 1))
    return parts, closed, grid[-1], grid[-2], grid[wi], grid[wi - 1]


def _opening_linings(grid):
    """Visible 交领 reveal only (neck→waist, a few front columns). Not an inner skirt."""
    nv, nu = len(grid), len(grid[0])
    v_end = max(3, int(nv * 0.62))
    cols = 4
    parts = []
    for tag, us in (("R", list(range(cols))), ("L", list(range(nu - cols, nu)))):
        sub = []
        for i in range(v_end):
            c = B.ring_centroid(grid[i])
            row = []
            for j in us:
                p = grid[i][j]
                radial = V(p.x - c.x, p.y - c.y, 0.0)
                nrm = radial.nrm() if radial.length() > 1e-8 else V(1.0, 0.0, 0.0)
                row.append(p - nrm * 0.010)
            sub.append(row)
        parts.append(
            B.thicken_sheet(
                sub, lambda tt, uu: 0.0035, "Robe_OpeningLining_%s" % tag, "M_RobeIvory"
            )
        )
    return parts


def build_open_trims(hem, prev, collar_centerline):
    """Cyan hem + gold follow THIS robe's open hem. Does not wrap last→first."""
    parts = []
    n = len(hem)
    c = B.ring_centroid(hem)
    inner, mid, outer, gold = [], [], [], []
    for j in range(n):
        p = hem[j]
        q = prev[j]
        j0 = max(0, j - 1)
        j1 = min(n - 1, j + 1)
        tng = hem[j1] - hem[j0]
        up = q - p
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
    hem_m = B.Mesh("Trim_Hem", "M_CyanGreen")
    hem_m.add_grid([inner, mid, outer], closed_u=False, closed_v=False)
    parts.append(hem_m)
    parts.append(
        B.sweep_profile(
            gold,
            [(math.cos(a) * 0.002, math.sin(a) * 0.002) for a in [2 * math.pi * k / 8 for k in range(8)]],
            "Trim_HemGold",
            "M_Gold",
            True,
        )
    )
    if collar_centerline and len(collar_centerline) >= 2:
        parts.append(
            B.sweep_profile(
                collar_centerline,
                B._rounded_rect(0.012, 0.004, 3),
                "Trim_Collar",
                "M_CyanGreen",
                True,
            )
        )
    return parts


def assemble_experiment():
    """Frozen figure, with only the robe stack replaced. No palace."""
    char = []
    char.append(B.build_head())
    char.extend(B.build_eyes())
    char.extend(B.build_ears())
    char.append(B.build_neck())
    robe, closed, hem, hem_prev, sash_ring, sash_prev = build_continuous_robe()
    char.extend(robe)
    char.extend(B.build_hair())
    char.extend(B.build_guan())
    char.extend(B.build_beard())
    collar_parts, collar_edge = B.build_collar(closed)
    char.extend(collar_parts)
    char.extend(B.build_standing_collar())
    char.extend(B.build_sash(sash_ring, sash_prev, closed))
    char.extend(B.build_sleeves())
    char.extend(build_open_trims(hem, hem_prev, collar_edge))
    char.extend(B.build_shoes())
    char.extend(B.build_hands())
    char.extend(B.build_fan())
    names = [m.name for m in char]
    for banned in REPLACED_PARTS:
        if banned in names:
            raise RuntimeError("experiment still contains replaced part %s" % banned)
    if "Robe_Continuous" not in names:
        raise RuntimeError("experiment missing Robe_Continuous")
    return char, []


def parse_cli():
    p = B.argparse.ArgumentParser(description="CT-3D-EXPERIMENT-01 continuous robe")
    p.add_argument(
        "--output-dir",
        default=None,
        help="Write experiment GLB/blend/png/JSON only here. Never cleans other dirs.",
    )
    p.add_argument("--mesh-stats", action="store_true")
    p.add_argument("--skip-render", action="store_true")
    args, _unknown = p.parse_known_args(B.argv_after_dash())
    if not args.output_dir:
        args.output_dir = os.path.join(HERE, "experiment_out")
    args.output_dir = os.path.abspath(args.output_dir)
    return args


def _experiment_notes():
    return [
        "CT-3D-EXPERIMENT-01. Frozen builder ea39968852c001ef5321fa476a31b5be3921c578 is imported, not edited.",
        "ONE continuous robe (Robe_Continuous) from neck opening to hem. No Robe_Body / Skirt_Outer / Robe_Panel_Outer / shoulder seal strip.",
        "Head/guan/beard, hands/sleeves, fan, cameras, materials, export helpers reused from the frozen builder.",
        "No palace / courtyard in this experiment. Not art approval. Cloud UNRUN without Blender.",
        "Does not rewrite report.json in the handoff dir. Writes experiment_report.json / experiment_mesh_stats.json.",
        "Static posed meshes. No armature. Cannot walk.",
    ]


def _experiment_meta(char_stats):
    names = [p["name"] for p in (char_stats.get("parts") or []) if p.get("name")]
    s = set(names)
    return {
        "id": "CT-3D-EXPERIMENT-01",
        "frozen_builder": "build_zhuge_v2.py",
        "frozen_commit": FROZEN_COMMIT,
        "replaces": list(REPLACED_PARTS),
        "surface": "Robe_Continuous",
        "construction": (
            "Single open wrap: panel_arc_ring / WRAP_FOLDS on one interpolated key list "
            "neck→shoulder→chest→waist→hem, then thicken_sheet 6 mm. "
            "Front opening = frozen PANEL_A_FRONT_R/L (back seam width 0). "
            "No strip_between. No second body/skirt/panel shell. "
            "Opening lining = two short inset strips neck→waist. "
            "Sash = frozen build_sash on this wrap's waist verts. "
            "Hem trim = open loft on this wrap's last two rings."
        ),
        "absent_replaced_parts": {n: (n not in s) for n in REPLACED_PARTS},
        "has_Robe_Continuous": "Robe_Continuous" in s,
        "has_shoulder_seal": "Robe_Panel_ShoulderSeal" in s,
        "part_names": names,
        "unverified_mac_five_view": [
            "lookdown shoulder ring gone (no horizontal seal at SHOULDER_Z)",
            "back seam no regression (still width 0, wrap around back)",
            "sash continuous on this robe waist",
            "natural shoulder→chest robe transition",
            "no new intersections (sleeves/collar/fan/beard untouched in pose)",
        ],
        "art_approval": False,
        "cloud_status": "UNRUN",
    }


def write_experiment_report(output_dir, stats, execution_kind, status, blender_present, blender_version, engine, outputs, glb_measured=None):
    os.makedirs(output_dir, exist_ok=True)
    guards = B.source_guards(os.path.abspath(__file__))
    compile_ok = True
    compile_err = None
    try:
        import py_compile

        py_compile.compile(os.path.abspath(__file__), doraise=True)
        py_compile.compile(FROZEN_BUILDER, doraise=True)
        py_compile.compile(os.path.join(HERE, "validate_glb.py"), doraise=True)
    except Exception as exc:
        compile_ok = False
        compile_err = str(exc)
    report = B.build_report_payload(
        execution_kind=execution_kind,
        status=status,
        blender_present=blender_present,
        blender_version=blender_version,
        engine=engine,
        stats=stats,
        outputs=outputs,
        notes=_experiment_notes(),
        static_checks={
            "mesh_stats": "experiment_mesh_stats.json",
            "py_compile": "pass" if compile_ok else "fail",
            "py_compile_error": compile_err,
            "source_guards": guards,
            "filepath_guard": B._selftest_filepath_guard(),
            "did_not_rewrite_frozen_report_json": True,
        },
        glb_measured=glb_measured,
    )
    report["experiment"] = _experiment_meta(stats.get("character") or {})
    report["title"] = "CT-3D-EXPERIMENT-01 连续袍面（不改冻结 builder）"
    B.write_report(B.safe_join(output_dir, "experiment_report.json"), report)
    return report


def mesh_stats_experiment(args):
    char, env = assemble_experiment()
    dz = B.snap_feet(char)
    cs = B.census(char)
    es = B.census(env)
    allm = B.census(char + env)
    stats = {"character": cs, "environment": es, "all": allm, "snap_dz": dz}
    os.makedirs(args.output_dir, exist_ok=True)
    B.write_report(B.safe_join(args.output_dir, "experiment_mesh_stats.json"), stats)
    write_experiment_report(
        args.output_dir,
        stats,
        execution_kind="expected",
        status="UNRUN",
        blender_present=False,
        blender_version=None,
        engine=None,
        outputs=[],
    )
    print(
        "experiment mesh_stats character tris=%s verts=%s parts=%s"
        % (cs["tris"], cs["verts"], cs["part_count"])
    )
    print("snap_dz", dz)
    print("replaced_absent", {n: n not in [p["name"] for p in cs["parts"]] for n in REPLACED_PARTS})
    return stats


def blender_experiment(args, char, env, stats):
    B.clear_scene()
    scene = B.bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    B.setup_world(scene)
    mat_map = {}
    for name in B.MATERIALS:
        col, metal, rough = B.MAT_COLORS[name]
        mat_map[name] = B.make_principled(name, col, metal, rough)

    root = B.bpy.data.objects.new("ZhugeLiang_Root", None)
    B.bpy.context.scene.collection.objects.link(root)
    review_root = B.bpy.data.objects.new("Review_Root", None)
    B.bpy.context.scene.collection.objects.link(review_root)

    for m in char:
        B.mesh_to_object(m, mat_map, root)
    B.mesh_to_object(B.build_review_ground(), mat_map, review_root)

    B.setup_lights()
    char_bb = B.union_bbox_from_census(stats.get("character") or {})
    cams = B.setup_cameras(char_bb)
    engine = B.choose_eevee(scene)

    os.makedirs(args.output_dir, exist_ok=True)
    blend_name = "zhuge_liang_v2_experiment.blend"
    glb_name = "zhuge_liang_v2_experiment.glb"
    blend_path = B.safe_join(args.output_dir, blend_name)
    glb_path = B.safe_join(args.output_dir, glb_name)

    B.bpy.ops.wm.save_as_mainfile(
        **B.filter_op_kwargs(
            B.bpy.ops.wm.save_as_mainfile,
            {"filepath": blend_path, "check_existing": False},
        )
    )
    B.export_glb_character_only(glb_path, "ZhugeLiang_Root")
    glb_measured = B.try_measure_glb(glb_path)
    renders = B.render_views(cams, args.output_dir, args.skip_render, palace=None, review=review_root)
    outputs = [blend_name, glb_name] + renders
    write_experiment_report(
        args.output_dir,
        stats,
        execution_kind="real",
        status="EXPORTED",
        blender_present=True,
        blender_version="%d.%d.%d" % tuple(B.bpy.app.version),
        engine=engine,
        outputs=outputs,
        glb_measured=glb_measured,
    )
    return outputs


def main():
    args = parse_cli()
    if args.output_dir.rstrip(os.sep) == os.path.abspath(HERE).rstrip(os.sep):
        print(
            "refusing to write experiment files into the frozen handoff dir; "
            "use --output-dir after -- pointing at a subdirectory (default experiment_out)",
            file=sys.stderr,
        )
        return 2
    if args.mesh_stats or B.bpy is None:
        if B.bpy is None and not args.mesh_stats:
            print(
                "bpy not found. Run inside Blender 5.2.1:\n"
                "  blender -b -P experiment_continuous_robe.py -- --output-dir DIR\n"
                "Census without Blender:\n"
                "  python3 experiment_continuous_robe.py --mesh-stats --output-dir DIR",
                file=sys.stderr,
            )
            args.mesh_stats = True
        mesh_stats_experiment(args)
        if B.bpy is None:
            return 0
        if args.mesh_stats and not os.environ.get("ZHUGE_FORCE_EXPORT"):
            return 0

    char, env = assemble_experiment()
    B.snap_feet(char)
    stats = {
        "character": B.census(char),
        "environment": B.census(env),
        "all": B.census(char + env),
    }
    blender_experiment(args, char, env, stats)
    print("exported experiment to", args.output_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
