#!/usr/bin/env python3
"""CT-GLB-INTAKE-01: offline GLB v2 delivery inspector (Python stdlib only).

Reads a GLB. Never writes the input. Does not judge art, topology quality,
or walking. Surface intersection and character construction are out of scope.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import struct
import sys
from typing import Any

TASK = "CT-GLB-INTAKE-01"
MAGIC = 0x46546C67  # glTF
CHUNK_JSON = 0x4E4F534A
CHUNK_BIN = 0x004E4942
CHUNK_NAMES = {CHUNK_JSON: "JSON", CHUNK_BIN: "BIN"}

COMPONENT_BYTES = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}
TYPE_COMPONENTS = {
    "SCALAR": 1,
    "VEC2": 2,
    "VEC3": 3,
    "VEC4": 4,
    "MAT2": 4,
    "MAT3": 9,
    "MAT4": 16,
}
FLOAT = 5126
POSITION_BLOCKERS = {
    "KHR_draco_mesh_compression",
    "EXT_meshopt_compression",
    "KHR_mesh_quantization",
}
NOT_PROVEN = (
    "geometric quality",
    "art quality",
    "walking",
)


def _u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def _f32(data: bytes, offset: int) -> float:
    return struct.unpack_from("<f", data, offset)[0]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def identity4() -> list[list[float]]:
    return [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]


def matmul(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    out = [[0.0] * 4 for _ in range(4)]
    for i in range(4):
        for j in range(4):
            out[i][j] = (
                a[i][0] * b[0][j]
                + a[i][1] * b[1][j]
                + a[i][2] * b[2][j]
                + a[i][3] * b[3][j]
            )
    return out


def mat_from_column_major(arr: list[float]) -> list[list[float]]:
    m = identity4()
    for col in range(4):
        for row in range(4):
            m[row][col] = float(arr[col * 4 + row])
    return m


def translation_mat(t: list[float]) -> list[list[float]]:
    m = identity4()
    m[0][3], m[1][3], m[2][3] = float(t[0]), float(t[1]), float(t[2])
    return m


def scale_mat(s: list[float]) -> list[list[float]]:
    m = identity4()
    m[0][0], m[1][1], m[2][2] = float(s[0]), float(s[1]), float(s[2])
    return m


def rotation_mat(q: list[float]) -> list[list[float]]:
    x, y, z, w = (float(q[0]), float(q[1]), float(q[2]), float(q[3]))
    xx, yy, zz = x * x, y * y, z * z
    xy, xz, yz = x * y, x * z, y * z
    wx, wy, wz = w * x, w * y, w * z
    return [
        [1 - 2 * (yy + zz), 2 * (xy - wz), 2 * (xz + wy), 0.0],
        [2 * (xy + wz), 1 - 2 * (xx + zz), 2 * (yz - wx), 0.0],
        [2 * (xz - wy), 2 * (yz + wx), 1 - 2 * (xx + yy), 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]


def node_local_matrix(node: dict[str, Any]) -> list[list[float]]:
    if "matrix" in node:
        arr = node["matrix"]
        if not isinstance(arr, list) or len(arr) != 16:
            raise ValueError("node.matrix must be 16 floats")
        return mat_from_column_major(arr)
    t = node.get("translation") or [0.0, 0.0, 0.0]
    r = node.get("rotation") or [0.0, 0.0, 0.0, 1.0]
    s = node.get("scale") or [1.0, 1.0, 1.0]
    if len(t) != 3 or len(r) != 4 or len(s) != 3:
        raise ValueError("node TRS length")
    return matmul(translation_mat(t), matmul(rotation_mat(r), scale_mat(s)))


def xform_point(m: list[list[float]], p: tuple[float, float, float]) -> tuple[float, float, float]:
    x, y, z = p
    return (
        m[0][0] * x + m[0][1] * y + m[0][2] * z + m[0][3],
        m[1][0] * x + m[1][1] * y + m[1][2] * z + m[1][3],
        m[2][0] * x + m[2][1] * y + m[2][2] * z + m[2][3],
    )


def empty_report(path: str, data: bytes | None = None) -> dict[str, Any]:
    file_meta = {
        "path": path,
        "sha256": sha256_bytes(data) if data is not None else None,
        "bytes": len(data) if data is not None else None,
    }
    return {
        "task": TASK,
        "ok": False,
        "input_modified": False,
        "file": file_meta,
        "header": None,
        "chunks": [],
        "counts": None,
        "external_resources": [],
        "unsupported_required_extensions": [],
        "buffer_bounds": {"ok": False, "issues": []},
        "position_extents": {
            "status": "UNKNOWN",
            "reason": "not decoded",
            "min": None,
            "max": None,
            "vertex_count": 0,
            "used_accessor_minmax": False,
        },
        "malformed": [],
        "not_proven": list(NOT_PROVEN),
    }


def note(rep: dict[str, Any], msg: str) -> None:
    if msg not in rep["malformed"]:
        rep["malformed"].append(msg)


def bounds_issue(rep: dict[str, Any], msg: str) -> None:
    issues = rep["buffer_bounds"]["issues"]
    if msg not in issues:
        issues.append(msg)
    rep["buffer_bounds"]["ok"] = False
    note(rep, msg)


def parse_chunks(data: bytes, rep: dict[str, Any]) -> list[tuple[str, bytes]]:
    if len(data) < 12:
        note(rep, "truncated header: file shorter than 12 bytes")
        return []
    magic, version, length = struct.unpack_from("<III", data, 0)
    magic_s = "glTF" if magic == MAGIC else "0x%08X" % magic
    header = {
        "magic": magic_s,
        "version": version,
        "length": length,
        "length_matches_file": length == len(data),
    }
    rep["header"] = header
    if magic != MAGIC:
        note(rep, "bad magic: expected glTF (0x46546C67)")
    if version != 2:
        note(rep, "unsupported GLB version: %s (need 2)" % version)
    if length != len(data):
        note(
            rep,
            "header.length %s != file bytes %s" % (length, len(data)),
        )
    if length > len(data):
        note(rep, "truncated file vs header.length")
    chunks: list[tuple[str, bytes]] = []
    offset = 12
    limit = min(length, len(data))
    while offset + 8 <= limit:
        chunk_len = _u32(data, offset)
        chunk_type = _u32(data, offset + 4)
        start = offset + 8
        end = start + chunk_len
        if end > len(data):
            note(
                rep,
                "truncated chunk: type=0x%08X declared=%s file_left=%s"
                % (chunk_type, chunk_len, max(0, len(data) - start)),
            )
            break
        if end > limit:
            note(rep, "chunk overruns header.length")
            break
        name = CHUNK_NAMES.get(chunk_type, "0x%08X" % chunk_type)
        payload = data[start:end]
        chunks.append((name, payload))
        rep["chunks"].append({"type": name, "length": chunk_len})
        offset = end
        if chunk_len % 4 != 0:
            note(rep, "chunk length not 4-byte aligned: %s" % name)
    if offset < limit and not any("truncated chunk" in m for m in rep["malformed"]):
        leftover = limit - offset
        if leftover:
            note(rep, "trailing bytes after last chunk: %s" % leftover)
    return chunks


def is_data_uri(uri: str) -> bool:
    return uri.startswith("data:")


def is_external_uri(uri: Any) -> bool:
    return isinstance(uri, str) and uri != "" and not is_data_uri(uri)


def decode_data_uri(uri: str) -> bytes | None:
    # data:[<mediatype>][;base64],<data>
    if not uri.startswith("data:") or "," not in uri:
        return None
    header, payload = uri.split(",", 1)
    if ";base64" in header.lower():
        import base64

        try:
            return base64.b64decode(payload, validate=False)
        except Exception:
            return None
    try:
        from urllib.parse import unquote_to_bytes

        return unquote_to_bytes(payload)
    except Exception:
        return None


def collect_external(doc: dict[str, Any]) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for i, buf in enumerate(doc.get("buffers") or []):
        if isinstance(buf, dict) and is_external_uri(buf.get("uri")):
            found.append({"kind": "buffer", "index": i, "uri": buf["uri"]})
    for i, img in enumerate(doc.get("images") or []):
        if isinstance(img, dict) and is_external_uri(img.get("uri")):
            found.append({"kind": "image", "index": i, "uri": img["uri"]})
    return found


def count_doc(doc: dict[str, Any]) -> dict[str, int]:
    meshes = doc.get("meshes") or []
    primitives = 0
    for mesh in meshes:
        if isinstance(mesh, dict):
            primitives += len(mesh.get("primitives") or [])
    return {
        "meshes": len(meshes) if isinstance(meshes, list) else 0,
        "primitives": primitives,
        "materials": len(doc.get("materials") or []),
        "textures": len(doc.get("textures") or []),
        "images": len(doc.get("images") or []),
        "skins": len(doc.get("skins") or []),
        "animations": len(doc.get("animations") or []),
        "nodes": len(doc.get("nodes") or []),
        "scenes": len(doc.get("scenes") or []),
        "cameras": len(doc.get("cameras") or []),
        "accessors": len(doc.get("accessors") or []),
        "bufferViews": len(doc.get("bufferViews") or []),
        "buffers": len(doc.get("buffers") or []),
    }


def resolve_buffers(
    doc: dict[str, Any],
    bin_payloads: list[bytes],
    rep: dict[str, Any],
) -> list[bytes | None]:
    buffers = doc.get("buffers") or []
    out: list[bytes | None] = []
    glb_bin = bin_payloads[0] if bin_payloads else b""
    for i, buf in enumerate(buffers):
        if not isinstance(buf, dict):
            bounds_issue(rep, "buffers[%s] is not an object" % i)
            out.append(None)
            continue
        declared = buf.get("byteLength")
        if not isinstance(declared, int) or declared < 0:
            bounds_issue(rep, "buffers[%s].byteLength missing or invalid" % i)
            declared = 0
        uri = buf.get("uri")
        blob: bytes | None
        if uri is None or uri == "":
            if i != 0:
                bounds_issue(
                    rep,
                    "buffers[%s] has no uri (only buffer 0 may use GLB BIN)" % i,
                )
                blob = None
            elif not bin_payloads:
                bounds_issue(rep, "GLB BIN chunk missing for buffers[0]")
                blob = None
            else:
                blob = glb_bin
                if declared > len(glb_bin):
                    bounds_issue(
                        rep,
                        "truncated buffer: buffers[0].byteLength %s > BIN bytes %s"
                        % (declared, len(glb_bin)),
                    )
        elif is_data_uri(uri):
            blob = decode_data_uri(uri)
            if blob is None:
                bounds_issue(rep, "buffers[%s] data URI could not be decoded" % i)
            elif declared > len(blob):
                bounds_issue(
                    rep,
                    "truncated buffer: buffers[%s].byteLength %s > data URI bytes %s"
                    % (i, declared, len(blob)),
                )
        else:
            blob = None  # external; not loaded
        if blob is not None and declared <= len(blob):
            blob = blob[:declared]
        out.append(blob)
    return out


def check_buffer_views(
    doc: dict[str, Any],
    blobs: list[bytes | None],
    rep: dict[str, Any],
) -> None:
    views = doc.get("bufferViews") or []
    buffers = doc.get("buffers") or []
    for i, view in enumerate(views):
        if not isinstance(view, dict):
            bounds_issue(rep, "bufferViews[%s] is not an object" % i)
            continue
        bi = view.get("buffer", 0)
        if not isinstance(bi, int) or bi < 0 or bi >= len(buffers):
            bounds_issue(rep, "bufferViews[%s].buffer index out of range" % i)
            continue
        declared = buffers[bi].get("byteLength") if isinstance(buffers[bi], dict) else None
        if not isinstance(declared, int):
            continue
        offset = view.get("byteOffset", 0)
        length = view.get("byteLength")
        if not isinstance(offset, int) or offset < 0:
            bounds_issue(rep, "bufferViews[%s].byteOffset invalid" % i)
            continue
        if not isinstance(length, int) or length < 0:
            bounds_issue(rep, "bufferViews[%s].byteLength invalid" % i)
            continue
        if offset + length > declared:
            bounds_issue(
                rep,
                "bufferViews[%s] overruns buffers[%s]: offset+length %s > byteLength %s"
                % (i, bi, offset + length, declared),
            )
        blob = blobs[bi] if bi < len(blobs) else None
        if blob is not None and offset + length > len(blob):
            bounds_issue(
                rep,
                "truncated bufferView: bufferViews[%s] needs %s bytes, buffer has %s"
                % (i, offset + length, len(blob)),
            )
        stride = view.get("byteStride")
        if stride is not None and (
            not isinstance(stride, int) or stride < 4 or stride > 252 or stride % 4 != 0
        ):
            bounds_issue(rep, "bufferViews[%s].byteStride invalid" % i)


def check_accessor_bounds(doc: dict[str, Any], rep: dict[str, Any]) -> None:
    accessors = doc.get("accessors") or []
    views = doc.get("bufferViews") or []
    for i, acc in enumerate(accessors):
        if not isinstance(acc, dict):
            bounds_issue(rep, "accessors[%s] is not an object" % i)
            continue
        if "bufferView" not in acc:
            continue
        vi = acc.get("bufferView")
        if not isinstance(vi, int) or vi < 0 or vi >= len(views):
            bounds_issue(rep, "accessors[%s].bufferView out of range" % i)
            continue
        view = views[vi]
        if not isinstance(view, dict):
            continue
        view_len = view.get("byteLength")
        if not isinstance(view_len, int):
            continue
        ctype = acc.get("componentType")
        typ = acc.get("type")
        count = acc.get("count")
        off = acc.get("byteOffset", 0)
        if ctype not in COMPONENT_BYTES or typ not in TYPE_COMPONENTS:
            continue
        if not isinstance(count, int) or count < 1 or not isinstance(off, int) or off < 0:
            bounds_issue(rep, "accessors[%s] count/byteOffset invalid" % i)
            continue
        elem = COMPONENT_BYTES[ctype] * TYPE_COMPONENTS[typ]
        stride = view.get("byteStride") or elem
        if not isinstance(stride, int) or stride < elem:
            bounds_issue(rep, "accessors[%s] stride smaller than element" % i)
            continue
        need = off + (count - 1) * stride + elem
        if need > view_len:
            bounds_issue(
                rep,
                "accessors[%s] overruns bufferViews[%s]: need %s > byteLength %s"
                % (i, vi, need, view_len),
            )


def primitive_blocks_position(prim: dict[str, Any]) -> str | None:
    ext = prim.get("extensions") or {}
    if not isinstance(ext, dict):
        return None
    for name in POSITION_BLOCKERS:
        if name in ext:
            return name
    return None


def buffer_view_blocks(view: dict[str, Any]) -> str | None:
    ext = view.get("extensions") or {}
    if not isinstance(ext, dict):
        return None
    for name in POSITION_BLOCKERS:
        if name in ext:
            return name
    return None


def scene_mesh_instances(
    doc: dict[str, Any],
    rep: dict[str, Any],
) -> tuple[list[tuple[int, list[list[float]]]], str | None]:
    nodes = doc.get("nodes") or []
    scenes = doc.get("scenes") or []
    if not isinstance(nodes, list) or not isinstance(scenes, list):
        return [], "nodes/scenes are not arrays"
    if not scenes:
        return [], "no scenes; cannot apply scene node transforms"
    scene_ids: list[int]
    if "scene" in doc and isinstance(doc["scene"], int):
        scene_ids = [doc["scene"]]
    else:
        scene_ids = list(range(len(scenes)))
    roots: list[int] = []
    for sid in scene_ids:
        if sid < 0 or sid >= len(scenes) or not isinstance(scenes[sid], dict):
            return [], "scene index out of range"
        for n in scenes[sid].get("nodes") or []:
            if isinstance(n, int):
                roots.append(n)
    if not roots:
        return [], "scene has no root nodes"
    world: dict[int, list[list[float]]] = {}
    visiting: set[int] = set()

    def walk(idx: int, parent: list[list[float]]) -> str | None:
        if idx in visiting:
            return "node cycle"
        if idx < 0 or idx >= len(nodes) or not isinstance(nodes[idx], dict):
            return "node index out of range"
        visiting.add(idx)
        try:
            local = node_local_matrix(nodes[idx])
        except (ValueError, TypeError, IndexError) as exc:
            visiting.remove(idx)
            return "node transform invalid: %s" % exc
        w = matmul(parent, local)
        world[idx] = w
        for child in nodes[idx].get("children") or []:
            if not isinstance(child, int):
                visiting.remove(idx)
                return "child index not int"
            err = walk(child, w)
            if err:
                visiting.remove(idx)
                return err
        visiting.remove(idx)
        return None

    for r in roots:
        err = walk(r, identity4())
        if err:
            return [], err
    inst: list[tuple[int, list[list[float]]]] = []
    for idx, w in world.items():
        mesh = nodes[idx].get("mesh")
        if isinstance(mesh, int):
            inst.append((mesh, w))
    if not inst:
        return [], "no mesh nodes in scene"
    return inst, None


def decode_position_accessor(
    doc: dict[str, Any],
    blobs: list[bytes | None],
    acc_index: int,
    rep: dict[str, Any],
) -> tuple[list[tuple[float, float, float]] | None, str]:
    accessors = doc.get("accessors") or []
    views = doc.get("bufferViews") or []
    if acc_index < 0 or acc_index >= len(accessors) or not isinstance(accessors[acc_index], dict):
        return None, "POSITION accessor index out of range"
    acc = accessors[acc_index]
    if acc.get("sparse") is not None:
        return None, "sparse POSITION accessor (not a static Blender layout we decode)"
    if acc.get("normalized"):
        return None, "normalized POSITION (not decoded)"
    if acc.get("componentType") != FLOAT or acc.get("type") != "VEC3":
        return None, "POSITION not FLOAT VEC3"
    if "bufferView" not in acc:
        return None, "POSITION accessor has no bufferView"
    vi = acc["bufferView"]
    if not isinstance(vi, int) or vi < 0 or vi >= len(views) or not isinstance(views[vi], dict):
        return None, "POSITION bufferView missing"
    view = views[vi]
    blocked = buffer_view_blocks(view)
    if blocked:
        return None, "POSITION bufferView uses %s" % blocked
    bi = view.get("buffer", 0)
    if not isinstance(bi, int) or bi < 0 or bi >= len(blobs):
        return None, "POSITION buffer index invalid"
    blob = blobs[bi]
    if blob is None:
        return None, "POSITION buffer not embedded"
    count = acc.get("count")
    off_a = acc.get("byteOffset", 0)
    off_v = view.get("byteOffset", 0)
    if not isinstance(count, int) or count < 1:
        return None, "POSITION count invalid"
    if not isinstance(off_a, int) or not isinstance(off_v, int) or off_a < 0 or off_v < 0:
        return None, "POSITION offsets invalid"
    elem = 12
    stride = view.get("byteStride") or elem
    if not isinstance(stride, int) or stride < elem:
        return None, "POSITION stride invalid"
    start = off_v + off_a
    need = start + (count - 1) * stride + elem
    if need > len(blob):
        bounds_issue(
            rep,
            "truncated POSITION buffer: accessor %s needs %s bytes, buffer has %s"
            % (acc_index, need, len(blob)),
        )
        return None, "truncated POSITION buffer"
    pts: list[tuple[float, float, float]] = []
    for n in range(count):
        o = start + n * stride
        pts.append((_f32(blob, o), _f32(blob, o + 4), _f32(blob, o + 8)))
    return pts, "decoded"


def extents_unknown(reason: str, vertex_count: int = 0) -> dict[str, Any]:
    return {
        "status": "UNKNOWN",
        "reason": reason,
        "min": None,
        "max": None,
        "vertex_count": vertex_count,
        "used_accessor_minmax": False,
    }


def decode_scene_position_extents(
    doc: dict[str, Any],
    blobs: list[bytes | None],
    required_ext: list[str],
    rep: dict[str, Any],
) -> dict[str, Any]:
    blockers = [e for e in required_ext if e in POSITION_BLOCKERS]
    if blockers:
        return extents_unknown(
            "required extension blocks POSITION decode: %s" % ", ".join(blockers)
        )
    inst, err = scene_mesh_instances(doc, rep)
    if err:
        return extents_unknown(err)
    meshes = doc.get("meshes") or []
    mins = [math.inf, math.inf, math.inf]
    maxs = [-math.inf, -math.inf, -math.inf]
    nvert = 0
    seen_mesh = set()
    for mesh_index, world in inst:
        if mesh_index < 0 or mesh_index >= len(meshes) or not isinstance(meshes[mesh_index], dict):
            return extents_unknown("mesh index out of range")
        seen_mesh.add(mesh_index)
        for p_i, prim in enumerate(meshes[mesh_index].get("primitives") or []):
            if not isinstance(prim, dict):
                return extents_unknown("primitive is not an object")
            blocked = primitive_blocks_position(prim)
            if blocked:
                return extents_unknown("primitive uses %s" % blocked)
            attrs = prim.get("attributes") or {}
            if not isinstance(attrs, dict) or "POSITION" not in attrs:
                return extents_unknown(
                    "primitive meshes[%s].primitives[%s] has no POSITION" % (mesh_index, p_i)
                )
            pts, why = decode_position_accessor(doc, blobs, attrs["POSITION"], rep)
            if pts is None:
                return extents_unknown(why)
            for p in pts:
                wp = xform_point(world, p)
                nvert += 1
                for k in range(3):
                    if wp[k] < mins[k]:
                        mins[k] = wp[k]
                    if wp[k] > maxs[k]:
                        maxs[k] = wp[k]
    for i, mesh in enumerate(meshes):
        if i not in seen_mesh and isinstance(mesh, dict) and mesh.get("primitives"):
            return extents_unknown(
                "mesh %s is not instanced by the scene; node transforms unavailable" % i
            )
    if nvert == 0:
        return extents_unknown("no POSITION vertices")
    return {
        "status": "DECODED",
        "reason": "FLOAT VEC3 POSITION x scene node world matrix (skin/animation not applied)",
        "min": [mins[0], mins[1], mins[2]],
        "max": [maxs[0], maxs[1], maxs[2]],
        "vertex_count": nvert,
        "used_accessor_minmax": False,
    }


def inspect_bytes(data: bytes, path: str) -> dict[str, Any]:
    rep = empty_report(path, data)
    chunks = parse_chunks(data, rep)
    if not chunks:
        return rep
    if chunks[0][0] != "JSON":
        note(rep, "first chunk is not JSON")
        return rep
    json_bytes = chunks[0][1]
    try:
        doc = json.loads(json_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        note(rep, "JSON chunk is not valid JSON: %s" % exc)
        return rep
    if not isinstance(doc, dict):
        note(rep, "JSON root is not an object")
        return rep
    bin_payloads = [payload for name, payload in chunks if name == "BIN"]
    extra = [name for name, _ in chunks[1:] if name not in ("BIN",)]
    for name in extra:
        note(rep, "unsupported extra chunk: %s" % name)

    rep["counts"] = count_doc(doc)
    rep["external_resources"] = collect_external(doc)
    req = [e for e in (doc.get("extensionsRequired") or []) if isinstance(e, str)]
    # This inspector implements no glTF extensions.
    rep["unsupported_required_extensions"] = list(req)

    if not (doc.get("asset") or {}).get("version", "").startswith("2"):
        note(rep, "asset.version is not 2.x")

    blobs = resolve_buffers(doc, bin_payloads, rep)
    check_buffer_views(doc, blobs, rep)
    check_accessor_bounds(doc, rep)
    if not rep["buffer_bounds"]["issues"]:
        rep["buffer_bounds"]["ok"] = True

    rep["position_extents"] = decode_scene_position_extents(doc, blobs, req, rep)
    header_ok = (
        rep["header"] is not None
        and rep["header"]["magic"] == "glTF"
        and rep["header"]["version"] == 2
        and rep["header"]["length_matches_file"]
    )
    rep["ok"] = header_ok and not rep["malformed"] and rep["buffer_bounds"]["ok"]
    return rep


def inspect_file(path: str) -> dict[str, Any]:
    try:
        with open(path, "rb") as fh:
            data = fh.read()
    except OSError as exc:
        rep = empty_report(path, None)
        note(rep, "unreadable input: %s" % exc)
        return rep
    return inspect_bytes(data, path)


def compact_json(obj: Any) -> str:
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=True)


def delivery_manifest(rep: dict[str, Any], report_rel: str) -> dict[str, Any]:
    return {
        "task": TASK,
        "inspector": "glb_intake.py",
        "input": rep.get("file"),
        "report": report_rel,
        "ok": rep.get("ok"),
        "input_modified": False,
        "checks": [
            "GLB v2 header",
            "chunk layout + JSON",
            "SHA256 and byte length of the exact file",
            "mesh/primitive/material/texture/image/skin/animation counts",
            "external buffer/image uri",
            "extensionsRequired (none implemented)",
            "declared buffer and bufferView bounds",
            "decoded FLOAT VEC3 POSITION extents with scene node transforms",
        ],
        "explicitly_not": [
            "accessor min/max is not measured geometry",
            "no triangle intersection (Surface owns that)",
            "no character construction (Kimi owns that)",
            "geometric quality not proven",
            "art quality not proven",
            "walking not proven",
        ],
        "not_proven": list(NOT_PROVEN),
        "position_extents_status": (rep.get("position_extents") or {}).get("status"),
        "external_resource_count": len(rep.get("external_resources") or []),
        "malformed": rep.get("malformed") or [],
    }


def write_outputs(rep: dict[str, Any], output_dir: str) -> tuple[str, str]:
    os.makedirs(output_dir, exist_ok=True)
    report_name = "glb_intake_report.json"
    manifest_name = "delivery_manifest.json"
    report_path = os.path.join(output_dir, report_name)
    manifest_path = os.path.join(output_dir, manifest_name)
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write(compact_json(rep))
        fh.write("\n")
    man = delivery_manifest(rep, report_name)
    with open(manifest_path, "w", encoding="utf-8") as fh:
        fh.write(compact_json(man))
        fh.write("\n")
    return report_path, manifest_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Offline GLB v2 delivery inspector (CT-GLB-INTAKE-01)."
    )
    parser.add_argument("glb", nargs="?", help="Path to a .glb file (read-only).")
    parser.add_argument(
        "--output-dir",
        default="out",
        help="Directory for compact JSON report + delivery manifest.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run bundled fixture tests instead of inspecting a file.",
    )
    args = parser.parse_args(argv)
    if args.self_test:
        from test_glb_intake import run_self_test

        return run_self_test(args.output_dir)
    if not args.glb:
        parser.error("glb path required (or pass --self-test)")
    before = None
    try:
        with open(args.glb, "rb") as fh:
            before = fh.read()
    except OSError:
        before = None
    rep = inspect_file(args.glb)
    if before is not None:
        with open(args.glb, "rb") as fh:
            after = fh.read()
        if after != before:
            note(rep, "INTERNAL: input bytes changed; inspector must never write the GLB")
            rep["ok"] = False
            rep["input_modified"] = True
    write_outputs(rep, args.output_dir)
    sys.stdout.write(compact_json(rep) + "\n")
    return 0 if rep["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
