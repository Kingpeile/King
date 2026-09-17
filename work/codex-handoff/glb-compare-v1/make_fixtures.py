#!/usr/bin/env python3
"""Write small honest GLB fixtures for CT-GLB-COMPARE-01. Stdlib only.

These are cubes/tetrahedra, not character deliveries. Cloud cannot see the
scholar/Kimi files; the viewer always requires an explicit user-selected GLB.
"""
from __future__ import annotations

import base64
import json
import os
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures")
MAGIC = 0x46546C67
CHUNK_JSON = 0x4E4F534A
CHUNK_BIN = 0x004E4942

CUBE_POS = (
    (0.0, 0.0, 0.0),
    (1.0, 0.0, 0.0),
    (1.0, 1.0, 0.0),
    (0.0, 1.0, 0.0),
    (0.0, 0.0, 1.0),
    (1.0, 0.0, 1.0),
    (1.0, 1.0, 1.0),
    (0.0, 1.0, 1.0),
)
CUBE_IDX = (
    1, 0, 3, 1, 3, 2,
    4, 5, 6, 4, 6, 7,
    1, 2, 6, 1, 6, 5,
    0, 4, 7, 0, 7, 3,
    3, 7, 6, 3, 6, 2,
    0, 1, 5, 0, 5, 4,
)
TET_POS = (
    (0.5, 0.5, 0.5),
    (0.5, 0.0, 0.0),
    (0.0, 0.5, 0.0),
    (0.0, 0.0, 0.5),
)
TET_IDX = (
    0, 1, 2,
    0, 2, 3,
    0, 3, 1,
    1, 3, 2,
)


def _pad4(data: bytes, pad: bytes) -> bytes:
    n = (4 - (len(data) % 4)) % 4
    return data + pad * n


def write_glb(doc: dict, bin_blob: bytes | None) -> bytes:
    js = _pad4(json.dumps(doc, separators=(",", ":")).encode("utf-8"), b" ")
    chunks = struct.pack("<II", len(js), CHUNK_JSON) + js
    if bin_blob is not None:
        raw = _pad4(bin_blob, b"\x00")
        chunks += struct.pack("<II", len(raw), CHUNK_BIN) + raw
    total = 12 + len(chunks)
    return struct.pack("<III", MAGIC, 2, total) + chunks


def pack_f32(vals) -> bytes:
    return b"".join(struct.pack("<fff", *v) for v in vals)


def pack_u16(vals) -> bytes:
    return b"".join(struct.pack("<H", i) for i in vals)


def mesh_doc(pos, idx, color, node, name, extras=None, buffer_uri=None):
    pos_b = pack_f32(pos)
    idx_b = pack_u16(idx)
    if len(idx_b) % 4:
        idx_b += b"\x00" * (4 - (len(idx_b) % 4))
    blob = pos_b + idx_b
    idx_off = len(pos_b)
    idx_len = len(idx) * 2
    buf = {"byteLength": len(blob)}
    if buffer_uri is not None:
        buf["uri"] = buffer_uri
        blob_out = None
        buf["byteLength"] = len(pos_b) + idx_len
    else:
        blob_out = blob
    doc = {
        "asset": {"version": "2.0", "generator": "CT-GLB-COMPARE-01-fixture"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [dict(node, mesh=0, name=name)],
        "meshes": [
            {
                "name": name,
                "primitives": [
                    {
                        "attributes": {"POSITION": 0},
                        "indices": 1,
                        "material": 0,
                        "mode": 4,
                    }
                ],
            }
        ],
        "materials": [
            {
                "name": name + "-mat",
                "pbrMetallicRoughness": {
                    "baseColorFactor": list(color),
                    "metallicFactor": 0.0,
                    "roughnessFactor": 0.85,
                },
            }
        ],
        "accessors": [
            {
                "bufferView": 0,
                "componentType": 5126,
                "count": len(pos),
                "type": "VEC3",
                "min": [min(p[i] for p in pos) for i in range(3)],
                "max": [max(p[i] for p in pos) for i in range(3)],
            },
            {
                "bufferView": 1,
                "componentType": 5123,
                "count": len(idx),
                "type": "SCALAR",
            },
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(pos_b), "target": 34962},
            {"buffer": 0, "byteOffset": idx_off, "byteLength": idx_len, "target": 34963},
        ],
        "buffers": [buf],
    }
    if extras:
        doc.update(extras)
    return doc, blob_out


def a1_glb() -> bytes:
    doc, blob = mesh_doc(
        CUBE_POS, CUBE_IDX, (0.82, 0.22, 0.16, 1.0),
        {}, "a1-cube",
    )
    return write_glb(doc, blob)


def a2_glb() -> bytes:
    doc, blob = mesh_doc(
        TET_POS, TET_IDX, (0.18, 0.42, 0.86, 1.0),
        {"translation": [2.0, 0.0, 0.0]}, "a2-tet",
    )
    return write_glb(doc, blob)


def b_glb() -> bytes:
    doc, blob = mesh_doc(
        CUBE_POS, CUBE_IDX, (0.20, 0.62, 0.32, 1.0),
        {"translation": [-2.0, 0.0, 0.0], "scale": [1.0, 2.0, 1.0]}, "b-box",
    )
    return write_glb(doc, blob)


def external_glb() -> bytes:
    doc, _blob = mesh_doc(
        CUBE_POS, CUBE_IDX, (0.5, 0.5, 0.5, 1.0),
        {}, "external-cube",
        extras={"images": [{"uri": "albedo.png", "mimeType": "image/png"}]},
        buffer_uri="mesh.bin",
    )
    return write_glb(doc, None)


def skinned_count_glb() -> bytes:
    extras = {
        "skins": [{"joints": [0], "name": "count-only-skin"}],
        "animations": [{"name": "count-only-anim", "channels": [], "samplers": []}],
    }
    doc, blob = mesh_doc(
        CUBE_POS, CUBE_IDX, (0.7, 0.7, 0.2, 1.0),
        {}, "skinned-count", extras=extras,
    )
    return write_glb(doc, blob)


def invalid_bytes() -> bytes:
    return b"INVALID GLB\x00this is not a glTF binary container\n"


FIXTURES = {
    "a1.glb": a1_glb,
    "a2.glb": a2_glb,
    "b.glb": b_glb,
    "external.glb": external_glb,
    "skinned-count.glb": skinned_count_glb,
    "invalid.glb": invalid_bytes,
}

# Honest expected stats (bind-pose triangles; skins/anims counted, not applied).
EXPECTED = {
    "a1.glb": {"triangles": 12, "skins": 0, "animations": 0, "external": 0},
    "a2.glb": {"triangles": 4, "skins": 0, "animations": 0, "external": 0},
    "b.glb": {"triangles": 12, "skins": 0, "animations": 0, "external": 0},
    "external.glb": {"triangles": None, "skins": 0, "animations": 0, "external": 2},
    "skinned-count.glb": {"triangles": 12, "skins": 1, "animations": 1, "external": 0},
    "invalid.glb": {"ok": False},
}


def write_all(root: str | None = None) -> dict[str, str]:
    root = root or HERE
    fix = os.path.join(root, "fixtures")
    os.makedirs(fix, exist_ok=True)
    names = {}
    for name, fn in FIXTURES.items():
        path = os.path.join(fix, name)
        data = fn()
        with open(path, "wb") as fh:
            fh.write(data)
        names[name] = path
    js_path = os.path.join(root, "js", "embedded-fixtures.js")
    os.makedirs(os.path.dirname(js_path), exist_ok=True)
    payload = {}
    for name, fn in FIXTURES.items():
        payload[name] = {
            "name": name,
            "b64": base64.b64encode(fn()).decode("ascii"),
        }
    body = (
        "/* Generated by make_fixtures.py. Honest cubes/tets, not characters. */\n"
        "window.GLB_COMPARE_FIXTURES = "
        + json.dumps(payload, separators=(",", ":"))
        + ";\n"
    )
    with open(js_path, "w", encoding="utf-8") as fh:
        fh.write(body)
    return names


if __name__ == "__main__":
    write_all()
    print("wrote", ", ".join(sorted(FIXTURES)))
