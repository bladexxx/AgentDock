"""Write and check local fixture provenance outside the Docker build context."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import runpy
import sys


SCHEMA = "agentdock-build-1"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record(fixture, revision, skill_identity, path, dockerfile, context):
    image = json.load(sys.stdin)
    image_id = image["Id"]
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", image_id):
        raise ValueError("Docker did not return a full local image ID")
    base_image = re.search(r"^ARG \w+_IMAGE=(\S+@sha256:[0-9a-f]{64})$", dockerfile.read_text(), re.M)[1]
    if fixture == "e2e":
        package = json.loads((context / "source/packages/e2e/package.json").read_text())
        cli, cli_version = package["name"], package["version"]
        source = "https://github.com/e2e-inc/e2e"
        skill = {"path": "skills/e2e", "gitTree": skill_identity}
    else:
        cli, cli_version = "cli-anything-sand3d", "0.1.0"
        source = "https://github.com/Sandflow-ai/sand3d"
        skill = {"path": "skills/cli-anything-sand3d/SKILL.md", "sha256": skill_identity}

    receipt = {
        "schemaVersion": SCHEMA,
        "fixture": fixture,
        "imageId": image_id,
        "platform": "/".join((image["Os"], image["Architecture"])),
        "source": source,
        "sourceRevision": revision,
        "baseImage": base_image,
        "dockerfileSha256": sha256(dockerfile),
        "cli": cli,
        "cliVersion": cli_version,
        "skill": skill,
    }
    if fixture == "sand3d":
        receipt["cliAnythingRevision"] = "34f519533bc175d2fe287ab8316b0dd99bb9cc43"

    # An existing receipt is never overwritten, including under concurrent builds.
    with path.open("x") as stream:
        json.dump(receipt, stream, indent=2)
        stream.write("\n")
    print(image_id)


def check(fixture, image_id, path, verifier):
    contents = path.read_bytes()
    receipt = json.loads(contents)
    if receipt.get("schemaVersion") != SCHEMA or receipt.get("fixture") != fixture:
        raise ValueError("Expected the host build receipt for " + fixture)
    if receipt.get("imageId") != image_id:
        raise ValueError("Host build receipt does not match the requested image")
    for key in ("source", "sourceRevision", "baseImage", "platform", "dockerfileSha256", "cli", "cliVersion", "skill"):
        if not receipt.get(key):
            raise ValueError("Host build receipt is missing " + key)
    evidence = {
        **receipt,
        "fixtureVersion": runpy.run_path(str(verifier))["FIXTURE_VERSION"],
        "verifierSha256": sha256(verifier),
        "buildReceiptSha256": hashlib.sha256(contents).hexdigest(),
    }
    print(json.dumps(evidence, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    for action in ("record", "check"):
        command = commands.add_parser(action)
        command.add_argument("fixture", choices=("e2e", "sand3d"))
        if action == "record":
            command.add_argument("revision")
            command.add_argument("skill_identity")
            command.add_argument("path", type=Path)
            command.add_argument("dockerfile", type=Path)
            command.add_argument("context", type=Path)
        else:
            command.add_argument("image_id")
            command.add_argument("path", type=Path)
            command.add_argument("verifier", type=Path)
        command.set_defaults(handler=record if action == "record" else check)
    args = vars(parser.parse_args())
    args.pop("action")
    handler = args.pop("handler")
    try:
        handler(**args)
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as error:
        print(f"Build receipt: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
