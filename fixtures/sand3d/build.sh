#!/usr/bin/env bash
set -euo pipefail

if [[ $# != 1 ]]; then
    echo "Usage: bash fixtures/sand3d/build.sh SAND3D_CHECKOUT" >&2
    exit 2
fi

fixture_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
skill="$fixture_dir/../../skills/cli-anything-sand3d/SKILL.md"
harness="$fixture_dir/agent-harness"
cmp "$skill" "$harness/cli_anything/sand3d/skills/SKILL.md"
skill_sha256=$(python3 -c 'import hashlib, pathlib, sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())' "$skill")

revision=5cdb54e4aef76377ad1a8bbc11e257eee8fc2341
context=$(mktemp -d)
trap 'rm -rf -- "$context"' EXIT
mkdir "$context/source" "$context/wheel"
if [[ -n ${SAND3D_BPY_WHEEL:-} ]]; then
    cp -- "$SAND3D_BPY_WHEEL" "$context/wheel/bpy-4.5.16-cp311-cp311-manylinux_2_28_x86_64.whl"
fi
git -C "$1" archive "$revision" | tar -xf - -C "$context/source"
cp -R "$harness" "$context/agent-harness"

docker build --platform linux/amd64 --iidfile "$context/image-id" \
    --build-arg "SAND3D_REVISION=$revision" \
    --build-arg "SAND3D_SKILL_SHA256=$skill_sha256" \
    --file "$fixture_dir/Dockerfile" "$context" >&2
cat "$context/image-id"
