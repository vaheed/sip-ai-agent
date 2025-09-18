#!/usr/bin/env bash
set -euo pipefail

# Default image registry path. Override with IMAGE_REGISTRY env var.
IMAGE_REGISTRY=${IMAGE_REGISTRY:-ghcr.io/vaheed/sip-ai-agent-backend}

# Determine Git commit SHA to embed in the image tag.
if [[ $# -gt 0 && -n "${1:-}" ]]; then
  GIT_SHA="$1"
  shift
elif git -C "$(dirname "${BASH_SOURCE[0]}")/.." rev-parse HEAD >/dev/null 2>&1; then
  GIT_SHA=$(git -C "$(dirname "${BASH_SOURCE[0]}")/.." rev-parse HEAD)
else
  echo "Unable to determine git commit SHA. Pass it as the first argument." >&2
  exit 1
fi

IMAGE_SHA_TAG="sha-${GIT_SHA}"
LATEST_TAG=${LATEST_TAG:-latest}

BUILD_CONTEXT=${BUILD_CONTEXT:-$(dirname "${BASH_SOURCE[0]}")/..}

echo "Building Docker image ${IMAGE_REGISTRY}:${IMAGE_SHA_TAG}" >&2

EXTRA_BUILD_ARGS=("$@")

docker build \
  "${EXTRA_BUILD_ARGS[@]}" \
  -t "${IMAGE_REGISTRY}:${IMAGE_SHA_TAG}" \
  -t "${IMAGE_REGISTRY}:${LATEST_TAG}" \
  "${BUILD_CONTEXT}"
