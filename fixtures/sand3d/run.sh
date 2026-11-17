#!/usr/bin/env bash
set -euo pipefail

if [[ $# != 3 || ! "$1" =~ ^sha256:[a-f0-9]{64}$ ]]; then
    echo "Usage: bash fixtures/sand3d/run.sh IMAGE_ID BUILD_RECEIPT NEW_EVIDENCE_DIRECTORY" >&2
    exit 2
fi

repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
verifier="$repo_dir/verify-sand3d-glb.py"
source "$repo_dir/fixtures/docker-environment.sh"
package=$(python3 "$repo_dir/fixtures/build-receipt.py" check sand3d "$1" "$2" "$verifier")
mkdir -- "$3"
printf '%s\n' "$package" > "$3/package.json"

status=0
docker run --rm "${proxy_run_args[@]}" --platform linux/amd64 --network none --cap-drop ALL \
    --security-opt no-new-privileges --read-only --tmpfs /tmp:rw,size=64m \
    --memory 2g --cpus 2 --pids-limit 256 --entrypoint /bin/sh \
    "$1" -ec 'cli-anything-sand3d --json bracket --output /tmp/bracket.glb >&2
               cat /tmp/bracket.glb' > "$3/bracket.glb" 2> "$3/run.log" || status=$?
printf '%s\n' "$status" > "$3/exit-status"
if (( status != 0 )); then
    echo "Container exited with status $status. See $3/run.log." >&2
    exit 1
fi
python3 "$verifier" "$3/bracket.glb" | tee "$3/artifact-check.json"
