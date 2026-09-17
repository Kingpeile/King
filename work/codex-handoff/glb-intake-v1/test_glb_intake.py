#!/usr/bin/env python3
"""Fixture tests for CT-GLB-INTAKE-01. Stdlib only. Does not modify inspected GLBs."""
from __future__ import annotations

import hashlib
import json
import os
import struct
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import glb_intake

CUBE_VERTS = (
    (0.0, 0.0, 0.0),
    (1.0, 0.0, 0.0),
    (1.0, 1.0, 0.0),
    (0.0, 1.0, 0.0),
    (0.0, 0.0, 1.0),
    (1.0, 0.0, 1.0),
    (1.0, 1.0, 1.0),
    (0.0, 1.0, 1.0),
)
LIE_MIN = [-99.0, -99.0, -99.0]
LIE_MAX = [99.0, 99.0, 99.0]


def _pad4(data: bytes, pad: bytes) -> bytes:
    n = (4 - (len(data) % 4)) % 4
    return data + pad * n


def write_glb(doc: dict, bin_blob: bytes | None) -> bytes:
    js = _pad4(json.dumps(doc, separators=(",", ":")).encode("utf-8"), b" ")
    chunks = struct.pack("<II", len(js), glb_intake.CHUNK_JSON) + js
    if bin_blob is not None:
        raw = _pad4(bin_blob, b"\x00")
        chunks += struct.pack("<II", len(raw), glb_intake.CHUNK_BIN) + raw
    total = 12 + len(chunks)
    return struct.pack("<III", glb_intake.MAGIC, 2, total) + chunks


def pack_verts(verts=CUBE_VERTS) -> bytes:
    return b"".join(struct.pack("<fff", *v) for v in verts)


def cube_doc(node=None, buffer_byte_length=None, uri=None, extra=None):
    blob = pack_verts()
    n = buffer_byte_length if buffer_byte_length is not None else len(blob)
    buf = {"byteLength": n}
    if uri is not None:
        buf["uri"] = uri
    node = dict(node or {})
    node["mesh"] = 0
    doc = {
        "asset": {"version": "2.0", "generator": "CT-GLB-INTAKE-01-fixture"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [node],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}}]}],
        "accessors": [
            {
                "bufferView": 0,
                "componentType": 5126,
                "count": 8,
                "type": "VEC3",
                "min": list(LIE_MIN),
                "max": list(LIE_MAX),
            }
        ],
        "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": n}],
        "buffers": [buf],
    }
    if extra:
        doc.update(extra)
    return doc, blob


def valid_cube_glb():
    doc, blob = cube_doc()
    return write_glb(doc, blob)


def truncated_buffer_glb():
    doc, blob = cube_doc()
    return write_glb(doc, blob[:12])


def external_resource_glb():
    doc, _blob = cube_doc(uri="mesh.bin")
    doc["images"] = [{"uri": "albedo.png", "mimeType": "image/png"}]
    doc["textures"] = [{"source": 0}]
    return write_glb(doc, None)


def transformed_mesh_glb():
    doc, blob = cube_doc(node={"translation": [10.0, 20.0, 30.0], "scale": [2.0, 3.0, 4.0]})
    return write_glb(doc, blob)


def inspect_temp(payload: bytes) -> tuple[dict, str]:
    fd, path = tempfile.mkstemp(suffix=".glb")
    os.close(fd)
    try:
        with open(path, "wb") as fh:
            fh.write(payload)
        before = open(path, "rb").read()
        digest_before = hashlib.sha256(before).hexdigest()
        mtime_before = os.stat(path).st_mtime_ns
        rep = glb_intake.inspect_file(path)
        after = open(path, "rb").read()
        assert after == before, "inspector mutated the GLB bytes"
        assert hashlib.sha256(after).hexdigest() == digest_before
        assert os.stat(path).st_mtime_ns == mtime_before
        assert rep["file"]["sha256"] == digest_before
        assert rep["file"]["bytes"] == len(before)
        assert rep["input_modified"] is False
        return rep, path
    finally:
        os.remove(path)


class GlbIntakeTests(unittest.TestCase):
    def test_valid_control_decodes_and_ignores_accessor_minmax(self):
        rep, _ = inspect_temp(valid_cube_glb())
        self.assertTrue(rep["ok"], rep["malformed"])
        self.assertEqual(rep["malformed"], [])
        self.assertEqual(rep["external_resources"], [])
        self.assertEqual(rep["unsupported_required_extensions"], [])
        self.assertTrue(rep["buffer_bounds"]["ok"])
        ext = rep["position_extents"]
        self.assertEqual(ext["status"], "DECODED")
        self.assertFalse(ext["used_accessor_minmax"])
        self.assertEqual(ext["vertex_count"], 8)
        self.assertEqual(ext["min"], [0.0, 0.0, 0.0])
        self.assertEqual(ext["max"], [1.0, 1.0, 1.0])
        self.assertNotEqual(ext["min"], LIE_MIN)
        self.assertNotEqual(ext["max"], LIE_MAX)
        c = rep["counts"]
        self.assertEqual(c["meshes"], 1)
        self.assertEqual(c["primitives"], 1)
        self.assertEqual(c["skins"], 0)
        self.assertEqual(c["animations"], 0)
        self.assertEqual(rep["header"]["version"], 2)
        self.assertEqual(rep["not_proven"], ["geometric quality", "art quality", "walking"])

    def test_truncated_buffer_is_malformed(self):
        valid, _ = inspect_temp(valid_cube_glb())
        bad, _ = inspect_temp(truncated_buffer_glb())
        self.assertTrue(valid["ok"])
        self.assertFalse(bad["ok"])
        self.assertNotEqual(valid["ok"], bad["ok"])
        self.assertNotEqual(valid["malformed"], bad["malformed"])
        joined = " ".join(bad["malformed"] + bad["buffer_bounds"]["issues"])
        self.assertIn("truncated buffer", joined)
        self.assertFalse(bad["buffer_bounds"]["ok"])
        self.assertEqual(bad["position_extents"]["status"], "UNKNOWN")
        self.assertNotEqual(valid["position_extents"]["status"], bad["position_extents"]["status"])

    def test_external_resource_is_reported_extents_unknown(self):
        valid, _ = inspect_temp(valid_cube_glb())
        ext_rep, _ = inspect_temp(external_resource_glb())
        self.assertNotEqual(valid["external_resources"], ext_rep["external_resources"])
        uris = {(e["kind"], e["uri"]) for e in ext_rep["external_resources"]}
        self.assertIn(("buffer", "mesh.bin"), uris)
        self.assertIn(("image", "albedo.png"), uris)
        self.assertEqual(ext_rep["position_extents"]["status"], "UNKNOWN")
        self.assertIn("not embedded", ext_rep["position_extents"]["reason"])
        self.assertNotEqual(valid["position_extents"]["status"], ext_rep["position_extents"]["status"])
        self.assertEqual(ext_rep["counts"]["textures"], 1)
        self.assertEqual(ext_rep["counts"]["images"], 1)
        self.assertEqual(valid["counts"]["textures"], 0)

    def test_transformed_mesh_uses_node_trs_not_accessor_minmax(self):
        identity, _ = inspect_temp(valid_cube_glb())
        moved, _ = inspect_temp(transformed_mesh_glb())
        self.assertTrue(moved["ok"], moved["malformed"])
        ext = moved["position_extents"]
        self.assertEqual(ext["status"], "DECODED")
        self.assertFalse(ext["used_accessor_minmax"])
        # T * S of unit cube: x' = 2x+10, y' = 3y+20, z' = 4z+30
        self.assertEqual(ext["min"], [10.0, 20.0, 30.0])
        self.assertEqual(ext["max"], [12.0, 23.0, 34.0])
        self.assertNotEqual(ext["min"], identity["position_extents"]["min"])
        self.assertNotEqual(ext["max"], identity["position_extents"]["max"])
        self.assertNotEqual(ext["min"], LIE_MIN)
        self.assertNotEqual(ext["max"], LIE_MAX)
        self.assertNotEqual(ext["min"], [0.0, 0.0, 0.0])
        self.assertNotEqual(ext["max"], [1.0, 1.0, 1.0])

    def test_required_extension_listed_and_blocks_extents(self):
        doc, blob = cube_doc(extra={"extensionsRequired": ["KHR_draco_mesh_compression"]})
        rep, _ = inspect_temp(write_glb(doc, blob))
        self.assertEqual(rep["unsupported_required_extensions"], ["KHR_draco_mesh_compression"])
        self.assertEqual(rep["position_extents"]["status"], "UNKNOWN")
        self.assertIn("KHR_draco_mesh_compression", rep["position_extents"]["reason"])

    def test_valid_and_invalid_controls_differ(self):
        valid, _ = inspect_temp(valid_cube_glb())
        trunc, _ = inspect_temp(truncated_buffer_glb())
        external, _ = inspect_temp(external_resource_glb())
        moved, _ = inspect_temp(transformed_mesh_glb())
        self.assertTrue(valid["ok"])
        self.assertFalse(trunc["ok"])
        self.assertEqual(valid["position_extents"]["status"], "DECODED")
        self.assertEqual(trunc["position_extents"]["status"], "UNKNOWN")
        self.assertEqual(external["position_extents"]["status"], "UNKNOWN")
        self.assertTrue(moved["ok"])
        self.assertNotEqual(valid["file"]["sha256"], trunc["file"]["sha256"])
        self.assertNotEqual(valid["file"]["sha256"], external["file"]["sha256"])
        self.assertNotEqual(valid["file"]["sha256"], moved["file"]["sha256"])
        fingerprint = lambda r: (
            r["ok"],
            tuple(r["malformed"]),
            tuple((e["kind"], e["uri"]) for e in r["external_resources"]),
            r["position_extents"]["status"],
            tuple(r["position_extents"]["min"] or ()),
            tuple(r["position_extents"]["max"] or ()),
        )
        self.assertNotEqual(fingerprint(valid), fingerprint(trunc))
        self.assertNotEqual(fingerprint(valid), fingerprint(external))
        self.assertNotEqual(fingerprint(valid), fingerprint(moved))
        self.assertNotEqual(fingerprint(trunc), fingerprint(external))


def run_self_test(output_dir: str) -> int:
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName("GlbIntakeTests", module=sys.modules[__name__])
    result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(suite)
    os.makedirs(output_dir, exist_ok=True)
    valid_rep = glb_intake.inspect_bytes(valid_cube_glb(), "fixtures/valid_cube.glb")
    glb_intake.write_outputs(valid_rep, output_dir)
    summary = {
        "task": glb_intake.TASK,
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "ok": result.wasSuccessful(),
        "not_proven": list(glb_intake.NOT_PROVEN),
        "controls": {
            "valid_cube": "DECODED extents, ignores accessor min/max",
            "truncated_buffer": "malformed, bounds fail, extents UNKNOWN",
            "external_resource": "uri listed, extents UNKNOWN",
            "transformed_mesh": "DECODED after node TRS, not accessor min/max",
        },
    }
    with open(os.path.join(output_dir, "self_test.json"), "w", encoding="utf-8") as fh:
        fh.write(glb_intake.compact_json(summary))
        fh.write("\n")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    out = "out"
    if len(sys.argv) > 1 and sys.argv[1] == "--output-dir":
        out = sys.argv[2]
        sys.argv = [sys.argv[0]]
    sys.exit(run_self_test(out))
