#!/usr/bin/env bash
set -euo pipefail

if [[ $# != 2 ]]; then
    echo "Usage: bash BUILDER_SKILL_DIR/fixtures/e2e/build.sh E2E_CHECKOUT NEW_BUILD_RECEIPT" >&2
    exit 2
fi

fixture_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
skill_dir=$(cd -- "$fixture_dir/../.." && pwd)
source "$skill_dir/scripts/docker-environment.sh"

revision=783a8c94c67cfe950e62f43ff44e29177345415a
skill_tree=$(git -C "$1" rev-parse "$revision:skills/e2e")
context=$(mktemp -d)
trap 'rm -rf -- "$context"' EXIT
mkdir "$context/source"
git -C "$1" archive "$revision" | tar -xf - -C "$context/source"

DOCKER_BUILDKIT=1 docker build "${proxy_build_args[@]}" --iidfile "$context/image-id" \
    --build-arg "E2E_REVISION=$revision" \
    --build-arg "E2E_SKILL_TREE=$skill_tree" \
    --file "$fixture_dir/Dockerfile" "$context" >&2
docker image inspect --format '{{json .}}' "$(cat "$context/image-id")" | \
    python3 "$skill_dir/scripts/build-receipt.py" record e2e "$revision" "$skill_tree" "$2" \
        "$fixture_dir/Dockerfile" "$context"
