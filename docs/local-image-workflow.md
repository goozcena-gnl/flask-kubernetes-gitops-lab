# Local image workflow without a private registry

This path provides a recruiter-friendly demonstration that does not require access to the private GitLab Container Registry. It keeps Git and Argo CD as the desired-state and reconciliation path, while the OCI image is loaded directly into the single-node Minikube profile.

## Preconditions

- bootstrap the `flask-gitops` Minikube profile and Argo CD;
- do not run the private-registry and local Argo CD Applications at the same time;
- run these commands from the repository root.

## Build and load the image

```bash
docker build -t flask-k8s-lab:local .
minikube image load flask-k8s-lab:local --profile flask-gitops
minikube image ls --profile flask-gitops | grep flask-k8s-lab
```

The `minikube-local` overlay removes the registry pull Secret and renders `flask-k8s-lab:local` with the base `IfNotPresent` pull policy.

Verify the rendered image before reconciliation:

```bash
python scripts/check-rendered-image.py \
  --overlay deploy/kubernetes/overlays/minikube-local
```

## Reconcile with Argo CD

After this overlay exists on the `main` revision watched by Argo CD:

```bash
kubectl apply -f deploy/argocd/application-minikube-local.yaml
kubectl -n argocd wait \
  --for=jsonpath='{.status.health.status}'=Healthy \
  application/flask-k8s-lab-minikube-local \
  --timeout=300s
kubectl -n flask-k8s-lab rollout status deployment/flask-k8s-lab --timeout=300s
```

If the regular `flask-k8s-lab-minikube` Application already exists, delete that Application first and let its finalizer remove the managed resources before applying the local variant.

## What this proves

- the container can be built from the repository;
- the image can run in the documented Minikube environment;
- Kustomize renders the expected local reference;
- Argo CD reconciles the repository path without registry credentials.

It does not prove a multi-node image distribution strategy or a production registry workflow.

