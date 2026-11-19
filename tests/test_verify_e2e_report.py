"""Test the E2E artifact assertion through the public command."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


VERIFIER = (Path(__file__).resolve().parents[1] / "skills" / "agentdock-builder" / "scripts"
            / "verify-e2e-report.py")


class E2EReportTests(unittest.TestCase):
    def check_report(self, contents: str | None) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as workdir:
            report = Path(workdir) / "report.json"
            if contents is not None:
                report.write_text(contents, encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(VERIFIER), str(report)], capture_output=True, text=True
            )

    def test_expected_browser_case_passes(self):
        result = self.check_report(json.dumps(self.passing_report()))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["result"], "passed")

    def test_zero_exit_with_wrong_result_fails(self):
        for result_changes in (
            {"file": "tests/other.e2e.ts"},
            {"targetId": "mobile"},
            {"status": "skipped"},
            {"selected": False},
            {"attempts": []},
            {"attempts": [{"status": "failed"}]},
            {"expectedFailure": {"reason": "known bug"}},
        ):
            with self.subTest(result_changes=result_changes):
                report = self.passing_report()
                report["run"]["results"][0].update(result_changes)
                result = self.check_report(json.dumps(report))
                self.assertEqual(result.returncode, 1)
                self.assertEqual(json.loads(result.stdout)["result"], "failed")

    def test_missing_or_malformed_report_fails(self):
        for contents in (None, "", "{", "[]"):
            with self.subTest(contents=contents):
                result = self.check_report(contents)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(json.loads(result.stdout)["result"], "failed")

    @staticmethod
    def passing_report():
        return {
            "schemaVersion": "report-1",
            "run": {
                "runner": {"name": "e2e", "version": "0.23.1"},
                "status": "passed",
                "exitCode": 0,
                "results": [
                    {
                        "file": "tests/smoke.e2e.ts",
                        "attempts": [{"status": "passed"}],
                        "titlePath": ["home lists the scenarios and opens one"],
                        "targetId": "web",
                        "selected": True,
                        "status": "passed",
                    },
                    {"file": "tests/other.e2e.ts", "selected": False, "status": "skipped"},
                ],
            },
        }
