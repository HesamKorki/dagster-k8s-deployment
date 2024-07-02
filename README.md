[![Build and Push gldas_noah Deployment Docker Image](https://github.com/HesamKorki/dagster-k8s-deployment/actions/workflows/build-gldas.yaml/badge.svg?branch=main&event=workflow_dispatch)](https://github.com/HesamKorki/dagster-k8s-deployment/actions/workflows/build-gldas.yaml)

# Dagster k8s Deployment
Deployment of Dagster (with a materialized asset) on Kubernetes with exposed UI through Nginx Ingress controller protected by basic-auth

## Table of Content
1.  [Required Tools](#required-tools)
2.  [Local K8s Cluster](#local-k8s-cluster)
3.  [Nginx Ingress Controller](#nginx-ingress-controller)
4.  [Dagster Deployment](#dagster-deployment)
    - [1. Decrypt Secrets](#1-decrypt-secrets)
    - [2. Call The Script](#2-call-the-script)
5. [Code Location](#code-location)
    - [gldas_noah Asset](#gldas_noah-asset)
6. [CI/CD](#cicd)



## Required Tools

Kubectl client version: `v1.30.0`

Kubernetes server version: `v1.30.0`

Helm client version: `v3.15.2`

## Local K8s Cluster

You may skip if you already have a k8s cluster running.
```bash
kind create cluster --config cluster-config.yaml
```

### Nginx Ingress Controller
Again please skip this also if you have Nginx-Ingress-Controller somewhere in your cluster.
```bash
kubectl apply -f nginx-ingress-controller/deploy.yaml
```


## Dagster Deployment

### 1. Decrypt Secrets
I tried to keep it simple so we don't need to install more dependencies. There's a file `dagster/secrets.yaml.enc` which is the encoded file of the secret manifest. Please use the `Password` provided to you to decrypt it first:

```bash
openssl enc -d -aes-256-cbc -salt -in dagster/secrets.yaml.enc -out dagster/secrets.yaml -k <password>
```

### 2. Call The Script
There is a simple script `dagster/upgrade.sh` to upgrade/install the dagster chart after creating namespace and the secrets. (you are welcome to skim through it before running it!)
It's also helpful for keeping track of which chart version is in production.

```bash
./dagster/upgrade.sh <namespace> <hostname>
```

- **Args**:
    - `<namespace>`: namespace to deploy dagster [Default: 'default']
    - `<hostname>`: hostname for the ingress [Default: 'localhost']


Default usage:
```bash
./dagster/upgrade.sh default localhost
```

The Dagster Webserver UI should be accessible by heading to [localhost](http://localhost) or the domain given to the script if a DNS is configured for the domain to point to the Ingress Controller Service. 

The UI is protected by **Nginx Basic Auth** and the credentials are encrypted in the secrets YAML file.

## Code Location
Each directory in the `src` represents a user deployment in Dagster with its own assets and pipelines.

### gldas_noah Asset
For demonstration purposes it sleeps for 60 seconds so we can check whether the file has been downloaded successfully in the ephemeral disk space. It also outputs the secrets and the S3 configs so we can verify their sanity.

### CI/CD
A GitHub Action tests the asset, builds the asset code location, and pushes it to Docker Hub if there are changes in the code location directory. We can use tools like ArgoCD for CD as future improvements.