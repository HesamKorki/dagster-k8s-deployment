#!/bin/bash

# ==========================================================================================
# This script builds the Docker image for the GLDAS Noah example and pushes it to Docker Hub.
# ==========================================================================================

set -e

IMAGE_REGISTRY=hesamkorki/dagster-asset
IMAGE_TAG=v0.8
DAGSTER_VERSION=1.11.16

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

echo "Building multi-architecture Docker image: ${IMAGE_REGISTRY}:${IMAGE_TAG}"
echo "Dagster version: ${DAGSTER_VERSION}"

# Create a new builder instance if it doesn't exist
docker buildx create --name multiarch-builder --use 2>/dev/null || docker buildx use multiarch-builder

# Build and push for both arm64 and amd64
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    --build-arg DAGSTER_VERSION=${DAGSTER_VERSION} \
    --tag "${IMAGE_REGISTRY}:${IMAGE_TAG}" \
    --push \
    ${SCRIPT_DIR}

echo ""
echo "Successfully built and pushed ${IMAGE_REGISTRY}:${IMAGE_TAG} for arm64 and amd64"
echo ""
echo "To run the image:"
echo "docker run -p 3000:3000 ${IMAGE_REGISTRY}:${IMAGE_TAG}"