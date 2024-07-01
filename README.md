# dagster-kube-deployment
Deployment of Dagster on Kubernetes with exposed UI through Nginx Ingress controller


## Tools version

Kubectl client version: v1.30.0
Kubernetes server version: v1.30.0
Helm client version: v3.15.2

## Local K8s Cluster
```bash
kind create cluster --config cluster-config.yml
```

## Nginx Ingress
```bash
kubectl apply -f nginx-ingress-controller/deploy.yaml
```


## Dagster Helm

```bash
helm repo add dagster https://dagster-io.github.io/helm
helm upgrade --install dagster dagster/dagster -f dagster/values.yaml
```