#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
cd "${SCRIPT_DIR}"

# Load environment variables from .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Check if Docker username is set
if [ "$DOCKER_USERNAME" = "your_dockerhub_username" ]; then
    echo "Error: Please update DOCKER_USERNAME in .env file"
    exit 1
fi

IMAGE_NAME="${DOCKER_USERNAME}/${DOCKER_IMAGE_NAME}"
TAG="${TAG}"



echo "Building multi-architecture Docker image: ${IMAGE_NAME}:${TAG}"

# Create a new builder instance if it doesn't exist
docker buildx create --name multiarch-builder --use 2>/dev/null || docker buildx use multiarch-builder

# Build and push for both arm64 and amd64
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    --tag "${IMAGE_NAME}:${TAG}" \
    --push \
    ${PWD}

echo "Successfully built and pushed ${IMAGE_NAME}:${TAG} for arm64 and amd64"
echo ""
echo "To run the image locally:"
echo "docker run -p 3000:3000 -e NUM_ASSETS=1000 ${IMAGE_NAME}:${TAG}"

