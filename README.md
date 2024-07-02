[![Build and Push gldas_noah Deployment Docker Image](https://github.com/HesamKorki/dagster-k8s-deployment/actions/workflows/build-gldas.yaml/badge.svg?branch=main&event=workflow_dispatch)](https://github.com/HesamKorki/dagster-k8s-deployment/actions/workflows/build-gldas.yaml)

# dagster-kube-deployment
Deployment of Dagster on Kubernetes with exposed UI through Nginx Ingress controller


## Tools version

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
./dagster/upgrade.sh arg1 arg2

Args:
    - arg1: namespace to deploy dagster [Default Value: 'default']
    - arg2: hostname for the ingress [Default Value: 'localhost']

```
Default usage:
```bash
./dagster/upgrade.sh default localhost
```

The Dagster Webserver UI should be accessible by heading to [localhost](http://localhost) or the domain given to the script if a DNS is configured for the domain to point to the Ingress Controller Service. 

The UI is protected by nginx basic-auth which is also encrypted in the secrets yaml file.

## Code Location
Each directory in the `src` is going to be a user deployment in dagster with its own assets and pipelines. Here we just have a single dummy asset to demonstrate. 

### gldas_noah Asset
For demonstration purposes it sleeps for 60 seconds so we can check whether the file has been downloaded successfully in the ephemeral disk space. It also outputs the secrets and the S3 configs so we can verify their sanity.

### CI/CD
I also made a simple github action that would test the asset, then build the asset code location and pushes it to docker hub if there is any change in the code location directoy. This is fine for our CI, the CD however, needs another tool like ArgoCD.