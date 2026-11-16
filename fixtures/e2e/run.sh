#!/usr/bin/env bash
set -euo pipefail

if [[ $# != 2 || ! "$1" =~ ^sha256:[a-f0-9]{64}$ ]]; then
    echo "Usage: bash fixtures/e2e/run.sh IMAGE_ID NEW_EVIDENCE_DIRECTORY" >&2
    exit 2
fi

repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
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
    "skill": {"path": "skills/e2e", "gitTree": labels["io.agentdock.e2e.skill-tree"]},
    "verifierSha256": hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest(),
}, sys.stdout, indent=2)
print()
' "$repo_dir/verify-e2e-report.py" > "$2/package.json"
status=0
docker run --rm --network none --cap-drop ALL --security-opt no-new-privileges \
    --memory 2g --cpus 2 --pids-limit 256 \
    "$1" > "$2/report.json" 2> "$2/run.log" || status=$?
printf '%s\n' "$status" > "$2/exit-status"
if (( status != 0 )); then
    echo "Container exited with status $status. See $2/run.log." >&2
    exit 1
fi
python3 "$repo_dir/verify-e2e-report.py" "$2/report.json" | tee "$2/artifact-check.json"
