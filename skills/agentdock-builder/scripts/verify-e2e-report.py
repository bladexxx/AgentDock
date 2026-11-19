"""Check the expected browser result in the pinned E2E fixture's report."""

import argparse
import hashlib
import json
from pathlib import Path


FIXTURE_VERSION = "e2e-web-smoke-1"


def check_report(report: object) -> None:
    if not isinstance(report, dict) or report.get("schemaVersion") != "report-1":
        raise ValueError("Expected an E2E report-1 document")
    run = report.get("run")
    if not isinstance(run, dict) or run.get("runner") != {"name": "e2e", "version": "0.23.1"}:
        raise ValueError("Expected E2E runner version 0.23.1")
    if run.get("status") != "passed" or type(run.get("exitCode")) is not int or run["exitCode"] != 0:
        raise ValueError("The E2E run did not report a successful exit")
    results = run.get("results")
    if not isinstance(results, list) or any(not isinstance(result, dict) for result in results):
        raise ValueError("Invalid browser test results")
    selected = [result for result in results if result.get("selected") is True]
    if len(selected) != 1:
        raise ValueError("Expected exactly one selected browser test")
    result = selected[0]
    if (
        result.get("file") != "tests/smoke.e2e.ts"
        or result.get("titlePath") != ["home lists the scenarios and opens one"]
        or result.get("targetId") != "web"
        or result.get("status") != "passed"
        or "expectedFailure" in result
    ):
        raise ValueError("The expected web smoke test did not pass")
    attempts = result.get("attempts")
    if (
        not isinstance(attempts, list)
        or len(attempts) != 1
        or not isinstance(attempts[0], dict)
        or attempts[0].get("status") != "passed"
    ):
        raise ValueError("Expected exactly one successful smoke-test attempt")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="path to the E2E report.json")
    args = parser.parse_args()
    try:
        with args.report.open("rb") as report_file:
            contents = report_file.read(4 * 1024 * 1024 + 1)
        if len(contents) > 4 * 1024 * 1024:
            raise ValueError("Report exceeds the fixture's 4 MiB limit")
        check_report(json.loads(contents))
    except (OSError, ValueError, RecursionError) as error:
        print(json.dumps({"fixtureVersion": FIXTURE_VERSION, "result": "failed", "error": str(error)}))
        return 1
    print(json.dumps({"fixtureVersion": FIXTURE_VERSION, "result": "passed", "reportSha256": hashlib.sha256(contents).hexdigest()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
