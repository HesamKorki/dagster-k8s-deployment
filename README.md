# dagster-kube-deployment
Deployment of Dagster on Kubernetes with exposed UI through Nginx Ingress controller


## Tools version

Kubectl client version: v1.30.0
Kubernetes server version: v1.30.0
Helm client version: v3.15.2

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

There is a simple script `dagster/upgrade.sh` to upgrade/install the dagster chart and apply the ingress for its UI.
`./dagster/upgrade.sh arg1 arg2`
Args:
    - arg1: namespace to deploy dagster [Default Value: 'default']
    - arg2: hostname for the ingress [Default Value: 'localhost']


```bash
./dagster/upgrade.sh default localhost
```