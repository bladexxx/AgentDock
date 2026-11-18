"""Exercise the independent bracket verifier through its CLI."""

import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "verify-sand3d-glb.py"
MEASUREMENT = ROOT / "docs/v0.1-measurement"


def bracket_glb(width=0.080, node_scale=None, holes=True, closed=True, slot=False):
    scale = node_scale or 1
    x_values = [-width / 2, -0.028, -0.022, 0.022, 0.028, width / 2]
    z_values = [-0.020, -0.003, 0.003, 0.020]
    points, faces = [], []
    cells = {
        (x, z) for x in range(len(x_values) - 1) for z in range(len(z_values) - 1)
        if not (holes and x in (1, 3) and (z == 1 or slot and z == 0))
    }

    def quad(corners):
        i = len(points)
        points.extend(corners)
        faces.extend([i, i + 1, i + 2, i, i + 2, i + 3])

    for x_index, (left, right) in enumerate(zip(x_values, x_values[1:])):
        for z_index, (near, far) in enumerate(zip(z_values, z_values[1:])):
            if (x_index, z_index) not in cells:
                continue
            bottom = [(left, 0, near), (right, 0, near), (right, 0, far), (left, 0, far)]
            top = [(x, 0.006, z) for x, _, z in bottom]
            quad(bottom)
            quad(top[::-1])
            if closed:
                neighbours = [(x_index, z_index - 1), (x_index + 1, z_index),
                              (x_index, z_index + 1), (x_index - 1, z_index)]
                for edge, neighbour in enumerate(neighbours):
                    if neighbour not in cells:
                        following = (edge + 1) % len(bottom)
                        quad([bottom[following], bottom[edge], top[edge], top[following]])
    vertices = b"".join(struct.pack("<fff", *(value / scale for value in point)) for point in points)
    triangles = struct.pack(f"<{len(faces)}H", *faces)
    binary = vertices + triangles
    doc = {
        "asset": {"version": "2.0"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"name": "plate", "mesh": 0}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
        "buffers": [{"byteLength": len(binary)}],
        "bufferViews": [
            {"buffer": 0, "byteLength": len(vertices)},
            {"buffer": 0, "byteOffset": len(vertices), "byteLength": len(triangles)},
        ],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "type": "VEC3", "count": len(points)},
            {"bufferView": 1, "componentType": 5123, "type": "SCALAR", "count": len(faces)},
        ],
    }
    if node_scale is not None:
        doc["nodes"][0]["scale"] = [node_scale] * 3
    # Declare the expected extrema even in the wrong-width case. The verifier must inspect BIN.
    doc["accessors"][0].update(min=[-0.040, 0, -0.020], max=[0.040, 0.006, 0.020])
    encoded = json.dumps(doc).encode()
    encoded += b" " * (-len(encoded) % 4)
    chunks = struct.pack("<I4s", len(encoded), b"JSON") + encoded
    chunks += struct.pack("<I4s", len(binary), b"BIN\0") + binary
    return struct.pack("<4sII", b"glTF", 2, 12 + len(chunks)) + chunks


class Sand3DGlbTests(unittest.TestCase):
    def verify(self, contents):
        with tempfile.TemporaryDirectory() as workdir:
            path = Path(workdir) / "bracket.glb"
            path.write_bytes(contents)
            return subprocess.run([sys.executable, str(VERIFIER), str(path)],
                                  capture_output=True, text=True)

    def test_blender_export_passes(self):
        contents = (MEASUREMENT / "bracket.glb").read_bytes()
        result = self.verify(contents)
        self.assertEqual(result.returncode, 0, result.stderr)
        evidence = json.loads(result.stdout)
        self.assertEqual(evidence["result"], "passed")
        self.assertEqual(evidence["artifactSha256"], hashlib.sha256(contents).hexdigest())
        self.assertEqual(evidence["plate"]["triangles"], 1220)

    def test_open_faces_with_correct_dimensions_and_clear_hole_rays_fail(self):
        result = self.verify(bracket_glb(closed=False))
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("closed surface", json.loads(result.stdout)["error"])

    def test_edge_slots_with_correct_dimensions_and_clear_hole_rays_fail(self):
        result = self.verify(bracket_glb(slot=True))
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("enclosed through holes", json.loads(result.stdout)["error"])

    def test_blender_export_of_wrong_width_fails(self):
        result = self.verify((MEASUREMENT / "sand3d-negative.glb").read_bytes())
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("Wrong plate dimensions", json.loads(result.stdout)["error"])

    def test_bracket_node_may_scale_mesh_millimetres_to_metres(self):
        result = self.verify(bracket_glb(node_scale=0.001))
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_wrong_plate_dimensions_fail_even_with_expected_metadata(self):
        result = self.verify(bracket_glb(width=0.070, node_scale=0.001))
        self.assertEqual(result.returncode, 1)
        self.assertIn("Wrong plate dimensions", json.loads(result.stdout)["error"])

    def test_truncated_glb_fails(self):
        result = self.verify(bracket_glb()[:-4])
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["result"], "failed")


    def test_solid_plate_with_same_dimensions_fails(self):
        result = self.verify(bracket_glb(holes=False))
        self.assertEqual(result.returncode, 1)
        self.assertIn("through holes", json.loads(result.stdout)["error"])
