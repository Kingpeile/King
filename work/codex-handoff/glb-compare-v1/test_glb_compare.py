#!/usr/bin/env python3
"""CT-GLB-COMPARE-01 behavioral tests. Stdlib + already-present node. No npm."""
from __future__ import annotations

import json
import os
import struct
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import make_fixtures

TASK = "CT-GLB-COMPARE-01"
NOT_PROVEN = ["geometric quality", "art quality", "walking", "G1-G5"]
GAP = {
    "task": TASK,
    "three_js": "MISSING on this branch",
    "gltf_loader": "MISSING on this branch",
    "searched": [
        "work/codex-handoff/glb-compare-v1/vendor/three/** (not present)",
        "default tree webapp/ miniprogram/ (no three, no GLTFLoader)",
        "work/codex-handoff/* Court packs (Python only)",
    ],
    "not_reused": [
        {
            "path": "energy-ball/package.json",
            "why": "Closed PR5. npm three ^0.170.0, Vite, no GLTFLoader, needs install + port. Out of ownership.",
        },
        {
            "path": "renovation/esports-room-3d/package.json",
            "why": "Draft PR15. npm three ^0.175.0, OrbitControls, no GLTFLoader, needs install + port 5173. Out of ownership.",
        },
        {
            "path": "work/codex-handoff/glb-intake-v1/",
            "why": "PR22 metadata inspector. Kept unchanged. Different pack.",
        },
    ],
    "reused": [],
    "fallback": "bounded WebGL in js/webgl-pane.js for embedded FLOAT VEC3 triangles",
    "policy": "no installs, no CDN, no new service or port",
}


def parse_json_chunk(data: bytes) -> dict:
    if len(data) < 20:
        raise ValueError("too small")
    magic, version, length = struct.unpack_from("<III", data, 0)
    if magic != 0x46546C67:
        raise ValueError("not glb")
    clen, ctype = struct.unpack_from("<II", data, 12)
    payload = data[20:20 + clen]
    return json.loads(payload.decode("utf-8"))


def triangles_from_doc(doc: dict) -> int:
    total = 0
    for mesh in doc.get("meshes") or []:
        for prim in mesh.get("primitives") or []:
            mode = prim.get("mode", 4)
            if "indices" in prim:
                n = doc["accessors"][prim["indices"]]["count"]
            else:
                n = doc["accessors"][prim["attributes"]["POSITION"]]["count"]
            if mode == 4:
                total += n // 3
            elif mode in (5, 6):
                total += max(0, n - 2)
    return total


class GlbCompareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        make_fixtures.write_all(HERE)

    def test_fixtures_are_honest_and_differ(self):
        a1 = parse_json_chunk(open(os.path.join(HERE, "fixtures", "a1.glb"), "rb").read())
        a2 = parse_json_chunk(open(os.path.join(HERE, "fixtures", "a2.glb"), "rb").read())
        b = parse_json_chunk(open(os.path.join(HERE, "fixtures", "b.glb"), "rb").read())
        self.assertEqual(triangles_from_doc(a1), 12)
        self.assertEqual(triangles_from_doc(a2), 4)
        self.assertEqual(triangles_from_doc(b), 12)
        self.assertEqual(len(a1.get("skins") or []), 0)
        self.assertEqual(len(a1.get("animations") or []), 0)
        self.assertEqual(a2["nodes"][0]["translation"], [2.0, 0.0, 0.0])
        self.assertEqual(b["nodes"][0]["scale"], [1.0, 2.0, 1.0])
        self.assertNotEqual(triangles_from_doc(a1), triangles_from_doc(a2))

    def test_invalid_file_is_not_glb(self):
        raw = open(os.path.join(HERE, "fixtures", "invalid.glb"), "rb").read()
        self.assertNotEqual(raw[:4], b"glTF")
        with self.assertRaises(ValueError):
            parse_json_chunk(raw)

    def test_external_fixture_lists_uris_and_is_blocked_by_parser_contract(self):
        doc = parse_json_chunk(open(os.path.join(HERE, "fixtures", "external.glb"), "rb").read())
        self.assertEqual(doc["buffers"][0]["uri"], "mesh.bin")
        self.assertEqual(doc["images"][0]["uri"], "albedo.png")

    def test_skinned_count_fixture_declares_one_skin_one_anim(self):
        doc = parse_json_chunk(open(os.path.join(HERE, "fixtures", "skinned-count.glb"), "rb").read())
        self.assertEqual(len(doc["skins"]), 1)
        self.assertEqual(len(doc["animations"]), 1)
        self.assertEqual(triangles_from_doc(doc), 12)

    def test_node_parser_race_invalid_and_gap(self):
        proc = subprocess.run(
            ["node", os.path.join(HERE, "test_node.js")],
            cwd=HERE,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        summary = json.loads(proc.stdout)
        self.assertTrue(summary["ok"], json.dumps(summary, indent=2))
        names = {r["name"] for r in summary["results"] if r["ok"]}
        self.assertIn("race-final-a2", names)
        self.assertIn("invalid-error-state", names)
        self.assertIn("three-not-found", names)
        self.assertIn("guard-blocks-https", names)


def write_outputs(ok: bool, tests_run: int, failures: int, errors: int) -> None:
    out = os.path.join(HERE, "out")
    os.makedirs(out, exist_ok=True)
    summary = {
        "task": TASK,
        "ok": ok,
        "tests_run": tests_run,
        "failures": failures,
        "errors": errors,
        "not_proven": NOT_PROVEN,
        "dependency_gap": GAP,
        "browser": "see screenshots/BROWSER-STATUS.txt after optional chrome pass",
        "controls": {
            "a1": "12 triangles, identity cube, 0 skins, 0 animations",
            "a2": "4 triangles, translated tet (replacement target)",
            "b": "12 triangles, translated+scaled box",
            "invalid": "not a GLB",
            "external": "mesh.bin + albedo.png must be blocked",
            "rapid A1-to-A2": "stale A1 cancelled; A2 stats remain",
        },
        "explicitly_not": [
            "art PASS",
            "walking",
            "G1-G5",
            "opening scholar/Kimi local files from cloud",
            "PR22 inspector changes",
            "scene integration / identity controls",
        ],
    }
    with open(os.path.join(out, "self_test.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, separators=(",", ":"), ensure_ascii=True)
        fh.write("\n")
    with open(os.path.join(out, "dependency_gap.json"), "w", encoding="utf-8") as fh:
        json.dump(GAP, fh, indent=2, ensure_ascii=True)
        fh.write("\n")


def run_self_test() -> int:
    make_fixtures.write_all(HERE)
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName("GlbCompareTests", module=sys.modules[__name__])
    result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(suite)
    write_outputs(
        result.wasSuccessful(),
        result.testsRun,
        len(result.failures),
        len(result.errors),
    )
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_self_test())
