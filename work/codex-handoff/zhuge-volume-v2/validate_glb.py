#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stdlib-only GLB (glTF 2.0 binary) structure checker for CT-3D-02.
Does not render, does not score art. Missing file => exit 2 (UNRUN).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import struct
import sys

MAGIC = 0x46546C67  # 'glTF'
JSON_CHUNK = 0x4E4F534A  # 'JSON'
BIN_CHUNK = 0x004E4942  # 'BIN\0'

CT_BYTE = 5120
CT_UBYTE = 5121
CT_SHORT = 5122
CT_USHORT = 5123
CT_UINT = 5125
CT_FLOAT = 5126

COMP_SIZE = {
    CT_BYTE: 1,
    CT_UBYTE: 1,
    CT_SHORT: 2,
    CT_USHORT: 2,
    CT_UINT: 4,
    CT_FLOAT: 4,
}
VEC_N = {
    "SCALAR": 1,
    "VEC2": 2,
    "VEC3": 3,
    "VEC4": 4,
    "MAT2": 4,
    "MAT3": 9,
    "MAT4": 16,
}


def parse_args():
    p = argparse.ArgumentParser(description="Validate a GLB for Zhuge v2 handoff")
    p.add_argument("glb", nargs="?", default="zhuge_liang_v2.glb")
    p.add_argument("--json-out", default=None, help="Write the check result JSON here")
    return p.parse_args()


def read_glb(path):
    with open(path, "rb") as f:
        data = f.read()
    if len(data) < 12:
        raise ValueError("file too small for GLB header")
    magic, version, length = struct.unpack_from("<III", data, 0)
    if magic != MAGIC:
        raise ValueError("bad magic (not a GLB)")
    if version != 2:
        raise ValueError("unsupported glTF version %s" % version)
    if length != len(data):
        # some writers pad; allow larger file, forbid truncated
        if length > len(data):
            raise ValueError("header length %s > file %s" % (length, len(data)))
    offset = 12
    json_bytes = None
    bin_bytes = b""
    chunks = []
    while offset + 8 <= len(data) and offset < length:
        chunk_len, chunk_type = struct.unpack_from("<II", data, offset)
        offset += 8
        chunk = data[offset : offset + chunk_len]
        if len(chunk) < chunk_len:
            raise ValueError("truncated chunk")
        offset += chunk_len
        # 4-byte padding
        pad = (4 - (chunk_len % 4)) % 4
        offset += pad
        chunks.append({"type": chunk_type, "bytes": chunk_len})
        if chunk_type == JSON_CHUNK:
            json_bytes = chunk
        elif chunk_type == BIN_CHUNK:
            bin_bytes = chunk
    if json_bytes is None:
        raise ValueError("missing JSON chunk")
    text = json_bytes.decode("utf-8").rstrip("\x00")
    gltf = json.loads(text)
    return gltf, bin_bytes, {"version": version, "length": length, "chunks": chunks, "file_bytes": len(data)}


def mat4_ident():
    return [
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0,
    ]


def mat4_mul(a, b):
    o = [0.0] * 16
    for r in range(4):
        for c in range(4):
            o[c * 4 + r] = (
                a[0 * 4 + r] * b[c * 4 + 0]
                + a[1 * 4 + r] * b[c * 4 + 1]
                + a[2 * 4 + r] * b[c * 4 + 2]
                + a[3 * 4 + r] * b[c * 4 + 3]
            )
    return o


def mat4_from_translation(t):
    m = mat4_ident()
    m[12], m[13], m[14] = float(t[0]), float(t[1]), float(t[2])
    return m


def mat4_from_scale(s):
    m = mat4_ident()
    m[0], m[5], m[10] = float(s[0]), float(s[1]), float(s[2])
    return m


def mat4_from_quat(q):
    x, y, z, w = [float(v) for v in q]
    n = math.sqrt(x * x + y * y + z * z + w * w) or 1.0
    x, y, z, w = x / n, y / n, z / n, w / n
    xx, yy, zz = x * x, y * y, z * z
    xy, xz, yz = x * y, x * z, y * z
    wx, wy, wz = w * x, w * y, w * z
    return [
        1 - 2 * (yy + zz), 2 * (xy + wz), 2 * (xz - wy), 0.0,
        2 * (xy - wz), 1 - 2 * (xx + zz), 2 * (yz + wx), 0.0,
        2 * (xz + wy), 2 * (yz - wx), 1 - 2 * (xx + yy), 0.0,
        0.0, 0.0, 0.0, 1.0,
    ]


def node_local_matrix(node):
    if "matrix" in node:
        m = [float(x) for x in node["matrix"]]
        if len(m) != 16:
            raise ValueError("node matrix must have 16 values")
        return m
    t = node.get("translation") or [0, 0, 0]
    r = node.get("rotation") or [0, 0, 0, 1]
    s = node.get("scale") or [1, 1, 1]
    return mat4_mul(mat4_from_translation(t), mat4_mul(mat4_from_quat(r), mat4_from_scale(s)))


def xform_point(m, p):
    x, y, z = p
    w = m[3] * x + m[7] * y + m[11] * z + m[15]
    w = 1.0 if abs(w) < 1e-12 else w
    return (
        (m[0] * x + m[4] * y + m[8] * z + m[12]) / w,
        (m[1] * x + m[5] * y + m[9] * z + m[13]) / w,
        (m[2] * x + m[6] * y + m[10] * z + m[14]) / w,
    )


def accessor_bytes(gltf, blob, acc_index):
    acc = gltf["accessors"][acc_index]
    bv = gltf["bufferViews"][acc["bufferView"]]
    b0 = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
    n = acc["count"]
    ncomp = VEC_N[acc["type"]]
    csize = COMP_SIZE[acc["componentType"]]
    stride = bv.get("byteStride") or (ncomp * csize)
    return acc, b0, n, ncomp, csize, stride


def unpack_one(ctype, buf, off):
    if ctype == CT_FLOAT:
        return struct.unpack_from("<f", buf, off)[0]
    if ctype == CT_USHORT:
        return struct.unpack_from("<H", buf, off)[0]
    if ctype == CT_UINT:
        return struct.unpack_from("<I", buf, off)[0]
    if ctype == CT_SHORT:
        return struct.unpack_from("<h", buf, off)[0]
    if ctype == CT_BYTE:
        return struct.unpack_from("<b", buf, off)[0]
    if ctype == CT_UBYTE:
        return struct.unpack_from("<B", buf, off)[0]
    raise ValueError("componentType %s" % ctype)


def read_vec3s(gltf, blob, acc_index):
    acc, b0, n, ncomp, csize, stride = accessor_bytes(gltf, blob, acc_index)
    out = []
    for i in range(n):
        off = b0 + i * stride
        out.append(tuple(unpack_one(acc["componentType"], blob, off + k * csize) for k in range(ncomp)))
    return out


def read_indices(gltf, blob, acc_index):
    acc, b0, n, ncomp, csize, stride = accessor_bytes(gltf, blob, acc_index)
    return [int(unpack_one(acc["componentType"], blob, b0 + i * stride)) for i in range(n)]


def tri_count_of_primitive(prim, gltf, blob):
    mode = prim.get("mode", 4)  # TRIANGLES
    indices = prim.get("indices")
    pos = prim.get("attributes", {}).get("POSITION")
    if pos is None:
        return 0, 0
    nvert = gltf["accessors"][pos]["count"]
    if indices is not None:
        nidx = gltf["accessors"][indices]["count"]
    else:
        nidx = nvert
    if mode == 4:
        tris = nidx // 3
    elif mode == 5:  # triangle strip
        tris = max(0, nidx - 2)
    elif mode == 6:  # triangle fan
        tris = max(0, nidx - 2)
    else:
        tris = 0
    return nvert, tris


def gather_world(gltf):
    nodes = gltf.get("nodes") or []
    scenes = gltf.get("scenes") or []
    scene_i = gltf.get("scene", 0)
    roots = scenes[scene_i]["nodes"] if scenes else list(range(len(nodes)))
    world = [None] * len(nodes)

    def walk(i, parent):
        local = node_local_matrix(nodes[i])
        world[i] = mat4_mul(parent, local) if parent else local
        for ch in nodes[i].get("children") or []:
            walk(ch, world[i])

    parented = set()
    for n in nodes:
        for ch in n.get("children") or []:
            parented.add(ch)
    for r in roots:
        walk(r, None)
    for i in range(len(nodes)):
        if world[i] is None:
            walk(i, None)
    return world


def position_aabb(gltf, blob):
    nodes = gltf.get("nodes") or []
    meshes = gltf.get("meshes") or []
    world = gather_world(gltf)
    mins = [float("inf")] * 3
    maxs = [float("-inf")] * 3
    used = False
    for ni, node in enumerate(nodes):
        mi = node.get("mesh")
        if mi is None:
            continue
        M = world[ni] or mat4_ident()
        for prim in meshes[mi].get("primitives") or []:
            pos = prim.get("attributes", {}).get("POSITION")
            if pos is None:
                continue
            for p in read_vec3s(gltf, blob, pos):
                x, y, z = xform_point(M, p[:3])
                used = True
                if x < mins[0]:
                    mins[0] = x
                if y < mins[1]:
                    mins[1] = y
                if z < mins[2]:
                    mins[2] = z
                if x > maxs[0]:
                    maxs[0] = x
                if y > maxs[1]:
                    maxs[1] = y
                if z > maxs[2]:
                    maxs[2] = z
    if not used:
        return None
    return {"min": mins, "max": maxs}


def check(gltf, blob, header, path):
    issues = []
    mats = gltf.get("materials") or []
    meshes = gltf.get("meshes") or []
    nodes = gltf.get("nodes") or []
    skins = gltf.get("skins") or []
    anims = gltf.get("animations") or []
    n_prim = 0
    n_verts = 0
    n_tris = 0
    for mesh in meshes:
        for prim in mesh.get("primitives") or []:
            n_prim += 1
            v, t = tri_count_of_primitive(prim, gltf, blob)
            n_verts += v
            n_tris += t
    names = [n.get("name") for n in nodes if n.get("name")]
    has_root = any(n == "ZhugeLiang_Root" for n in names)
    if not has_root:
        issues.append("missing node ZhugeLiang_Root")
    if len(mats) > 8:
        issues.append("material count %d > 8" % len(mats))
    aabb = None
    try:
        aabb = position_aabb(gltf, blob)
    except Exception as exc:
        issues.append("aabb failed: %s" % exc)
        aabb = None
    yup_note = (
        "glTF is Y-up. After Blender export_yup, character feet should sit near min.y ≈ 0 "
        "(courtyard slabs may go slightly negative)."
    )
    feet_y = None if not aabb else aabb["min"][1]
    result = {
        "ok": not issues,
        "path": os.path.abspath(path),
        "file_bytes": header["file_bytes"],
        "gltf_asset": gltf.get("asset"),
        "materials": len(mats),
        "material_names": [m.get("name") for m in mats],
        "meshes": len(meshes),
        "primitives": n_prim,
        "verts_position_accessors_sum": n_verts,
        "tris_estimated": n_tris,
        "nodes": len(nodes),
        "node_names_sample": names[:40],
        "has_ZhugeLiang_Root": has_root,
        "skins": len(skins),
        "animations": len(anims),
        "can_walk": False,
        "aabb_world_yup": aabb,
        "feet_min_y": feet_y,
        "yup_note": yup_note,
        "issues": issues,
        "art_approval": False,
        "note": "Structure only. Screenshot/primitive count is not art approval.",
    }
    return result


def main():
    args = parse_args()
    path = args.glb
    if not os.path.isfile(path):
        payload = {
            "ok": False,
            "status": "UNRUN",
            "path": os.path.abspath(path),
            "error": "GLB not found. Cloud did not run Blender; Codex must export locally.",
            "art_approval": False,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        if args.json_out:
            with open(args.json_out, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
                f.write("\n")
        return 2
    try:
        gltf, blob, header = read_glb(path)
        result = check(gltf, blob, header, path)
    except Exception as exc:
        result = {"ok": False, "status": "INVALID", "path": os.path.abspath(path), "error": str(exc), "art_approval": False}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            f.write("\n")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
