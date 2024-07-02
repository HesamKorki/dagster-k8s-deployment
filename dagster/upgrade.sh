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
SECRET_FILE="$SCRIPT_DIR/secrets.yaml"

if [ ! -f "$SECRET_FILE" ]; then
    echo "Error: File '$SECRET_FILE' not found! Maybe you forgot to decrypt it?"
    exit 1
fi

# Ensure the namespace exists
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Create the secrets
envsubst < "$SECRET_FILE" | kubectl apply -f -

# Add the Helm repository
helm repo add dagster $HELM_REPO
helm repo update

# Install or upgrade the Dagster release

echo "Upgrading Dagster Helm release..."

envsubst < "$VALUES_FILE" | helm upgrade --install $RELEASE_NAME $HELM_CHART \
--namespace $NAMESPACE \
--version $CHART_VERSION \
--values -

# Print the status of the release
helm status $RELEASE_NAME -n $NAMESPACE


