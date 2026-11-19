#!/usr/bin/env bash
set -euo pipefail

if [[ $# != 2 ]]; then
    echo "Usage: bash BUILDER_SKILL_DIR/fixtures/sand3d/build.sh SAND3D_CHECKOUT NEW_BUILD_RECEIPT" >&2
    exit 2
fi

fixture_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
skill_dir=$(cd -- "$fixture_dir/../.." && pwd)
skill="$fixture_dir/agent-harness/cli_anything/sand3d/skills/SKILL.md"
harness="$fixture_dir/agent-harness"
skill_sha256=$(python3 -c 'import hashlib, pathlib, sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())' "$skill")

source "$skill_dir/scripts/docker-environment.sh"

revision=5cdb54e4aef76377ad1a8bbc11e257eee8fc2341
context=$(mktemp -d)
trap 'rm -rf -- "$context"' EXIT
mkdir "$context/source" "$context/wheel"
if [[ -n ${SAND3D_BPY_WHEEL:-} ]]; then
    cp -- "$SAND3D_BPY_WHEEL" "$context/wheel/bpy-4.5.16-cp311-cp311-manylinux_2_28_x86_64.whl"
fi
git -C "$1" archive "$revision" | tar -xf - -C "$context/source"
cp -R "$harness" "$context/agent-harness"

DOCKER_BUILDKIT=1 docker build "${proxy_build_args[@]}" --platform linux/amd64 --iidfile "$context/image-id" \
    --build-arg "SAND3D_REVISION=$revision" \
    --build-arg "SAND3D_SKILL_SHA256=$skill_sha256" \
    --file "$fixture_dir/Dockerfile" "$context" >&2
docker image inspect --format '{{json .}}' "$(cat "$context/image-id")" | \
    python3 "$skill_dir/scripts/build-receipt.py" record sand3d "$revision" "$skill_sha256" "$2" \
        "$fixture_dir/Dockerfile" "$context"
