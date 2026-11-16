#!/usr/bin/env bash
set -euo pipefail

if [[ $# != 1 ]]; then
    echo "Usage: bash fixtures/e2e/build.sh E2E_CHECKOUT" >&2
    exit 2
fi

fixture_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
revision=783a8c94c67cfe950e62f43ff44e29177345415a
skill_tree=$(git -C "$1" rev-parse "$revision:skills/e2e")
context=$(mktemp -d)
trap 'rm -rf -- "$context"' EXIT
mkdir "$context/source"
git -C "$1" archive "$revision" | tar -xf - -C "$context/source"

docker build --iidfile "$context/image-id" \
    --build-arg "E2E_REVISION=$revision" \
    --build-arg "E2E_SKILL_TREE=$skill_tree" \
    --file "$fixture_dir/Dockerfile" "$context" >&2
cat "$context/image-id"
