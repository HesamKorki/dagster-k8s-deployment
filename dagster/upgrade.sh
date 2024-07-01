#!/bin/bash

# ====================================================================
# This script upgrades the Dagster Helm release to the latest version.
# ====================================================================

# Usage: ./upgrade.sh [namespace] [ingress_host]

# Example: ./upgrade.sh dagster dagster.example.com
# [Will install Dagster in 'dagster' namespace and expects 'dagster.example.com' to be pointing to the Ingress Controller Service]

NAMESPACE=${1:-default}
INGRESS_HOST=${2:-localhost}

RELEASE_NAME="dagster"
HELM_REPO="https://dagster-io.github.io/helm"
HELM_CHART="dagster/dagster"
CHART_VERSION="1.7.12" 

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
VALUES_FILE="$SCRIPT_DIR/values.yaml"
INGRESS_FILE="$SCRIPT_DIR/dagster-ingress.yaml"

# Add the Helm repository
helm repo add dagster $HELM_REPO

# Update Helm repositories
helm repo update

# Install or upgrade the Dagster release

echo "Upgrading Dagster Helm release..."
helm upgrade --install $RELEASE_NAME $HELM_CHART \
--namespace $NAMESPACE \
--version $CHART_VERSION \
--values $VALUES_FILE


echo "Applying the Ingress"
envsubst < "$INGRESS_FILE" | kubectl apply -f -

# Print the status of the release
helm status $RELEASE_NAME -n $NAMESPACE


