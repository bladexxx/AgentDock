#!/usr/bin/env bash
set -euo pipefail

if [[ $# != 3 || ! "$1" =~ ^sha256:[a-f0-9]{64}$ ]]; then
    echo "Usage: bash BUILDER_SKILL_DIR/fixtures/e2e/run.sh IMAGE_ID BUILD_RECEIPT NEW_EVIDENCE_DIRECTORY" >&2
    exit 2
fi

fixture_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
skill_dir=$(cd -- "$fixture_dir/../.." && pwd)
verifier="$skill_dir/scripts/verify-e2e-report.py"
source "$skill_dir/scripts/docker-environment.sh"
package=$(python3 "$skill_dir/scripts/build-receipt.py" check e2e "$1" "$2" "$verifier")
mkdir -- "$3"
printf '%s\n' "$package" > "$3/package.json"

status=0
docker run --rm --pull=never "${proxy_run_args[@]}" --network none --cap-drop ALL --security-opt no-new-privileges \
    --memory 2g --cpus 2 --pids-limit 256 \
    "$1" > "$3/report.json" 2> "$3/run.log" || status=$?
printf '%s\n' "$status" > "$3/exit-status"
if (( status != 0 )); then
    echo "Container exited with status $status. See $3/run.log." >&2
    exit 1
fi
python3 "$verifier" "$3/report.json" | tee "$3/artifact-check.json"
