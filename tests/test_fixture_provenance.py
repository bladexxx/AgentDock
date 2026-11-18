"""Exercise the public fixture runner's provenance boundary."""

import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
IMAGE = "sha256:" + "a" * 64


class FixtureProvenanceTests(unittest.TestCase):
    def run_fixture(self, fixture, directory, *args):
        return subprocess.run(
            ["bash", str(ROOT / "fixtures" / fixture / "run.sh"), IMAGE, *args, str(directory)],
            text=True, capture_output=True,
        )

    def test_both_runners_require_a_host_build_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            for fixture in ("e2e", "sand3d"):
                with self.subTest(fixture=fixture):
                    result = self.run_fixture(fixture, Path(temp) / fixture)
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertIn("BUILD_RECEIPT", result.stderr)

    def test_receipt_for_another_image_cannot_verify_the_requested_image(self):
        with tempfile.TemporaryDirectory() as temp:
            receipt = Path(temp) / "receipt.json"
            receipt.write_text(json.dumps({
                "schemaVersion": "agentdock-build-1",
                "fixture": "sand3d",
                "imageId": "sha256:" + "b" * 64,
            }))
            result = self.run_fixture("sand3d", Path(temp) / "evidence", str(receipt))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("does not match the requested image", result.stderr)
