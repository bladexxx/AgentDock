#!/usr/bin/env bash
set -euo pipefail

if [[ $# != 2 || ! "$1" =~ ^sha256:[a-f0-9]{64}$ ]]; then
    echo "Usage: bash fixtures/sand3d/run.sh IMAGE_ID NEW_EVIDENCE_DIRECTORY" >&2
    exit 2
fi

repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
verifier="$repo_dir/verify-sand3d-glb.py"
mkdir -- "$2"
docker image inspect --format '{{json .}}' "$1" | python3 -c '
import hashlib
import json
from pathlib import Path
import sys

image = json.load(sys.stdin)
labels = image["Config"]["Labels"]
json.dump({
    "source": labels["org.opencontainers.image.source"],
    "sourceRevision": labels["org.opencontainers.image.revision"],
    "imageId": image["Id"],
    "baseImage": labels["org.opencontainers.image.base.name"],
    "platform": "/".join((image["Os"], image["Architecture"])),
    "cli": "cli-anything-sand3d",
    "cliVersion": labels["io.agentdock.sand3d.cli-version"],
    "cliAnythingRevision": labels["io.agentdock.cli-anything.revision"],
    "skill": {
        "path": "skills/cli-anything-sand3d/SKILL.md",
        "sha256": labels["io.agentdock.sand3d.skill-sha256"],
    },
    "verifierSha256": hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest(),
}, sys.stdout, indent=2)
print()
' "$verifier" > "$2/package.json"

status=0
docker run --rm --platform linux/amd64 --network none --cap-drop ALL \
    --security-opt no-new-privileges --read-only --tmpfs /tmp:rw,size=64m \
    --memory 2g --cpus 2 --pids-limit 256 --entrypoint /bin/sh \
    "$1" -ec 'cli-anything-sand3d --json bracket --output /tmp/bracket.glb >&2
               cat /tmp/bracket.glb' > "$2/bracket.glb" 2> "$2/run.log" || status=$?
printf '%s\n' "$status" > "$2/exit-status"
if (( status != 0 )); then
    echo "Container exited with status $status. See $2/run.log." >&2
    exit 1
fi
python3 "$verifier" "$2/bracket.glb" | tee "$2/artifact-check.json"
