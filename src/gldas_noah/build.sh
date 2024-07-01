#!/bin/bash

# ==========================================================================================
# This script builds the Docker image for the GLDAS Noah example and pushes it to Docker Hub.
# ==========================================================================================

IMAGE_REGISTRY=hesamkorki/dagster-asset
IMAGE_TAG=v0.4
DAGSTER_VERSION=1.7.12


SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

docker build --build-arg DAGSTER_VERSION=${DAGSTER_VERSION} -t ${IMAGE_REGISTRY}:${IMAGE_TAG} $SCRIPT_DIR

docker push ${IMAGE_REGISTRY}:${IMAGE_TAG}