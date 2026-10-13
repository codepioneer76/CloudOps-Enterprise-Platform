# CloudOps Enterprise Platform - Kubernetes Manifests

Production-grade Kubernetes manifests for deploying the **CloudOps Enterprise Platform** and its PostgreSQL database backend.

---

## Architecture Overview

```mermaid
graph TD
    Client["Client / Browser"] -->|HTTP / DNS: cloudops.example.com| Ingress["Ingress Controller (NGINX)<br/>cloudops-ingress"]
    Ingress -->|Port 80| ApiService["ClusterIP Service<br/>cloudops-api-service:80"]
    ApiService -->|Port 8000| PodApi1["Pod: cloudops-api (Replica 1)"]
    ApiService -->|Port 8000| PodApi2["Pod: cloudops-api (Replica 2)"]
    
    PodApi1 -->|Config & Secrets| CM["ConfigMap: cloudops-config<br/>Secret: cloudops-secrets"]
    PodApi2 -->|Config & Secrets| CM
    
    PodApi1 -->|TCP 5432| PgService["ClusterIP Service<br/>postgres-service:5432"]
    PodApi2 -->|TCP 5432| PgService
    
    PgService -->|Port 5432| PgPod["Pod: postgres:16-alpine"]
    PgPod -->|Mount: /var/lib/postgresql/data| PVC["PersistentVolumeClaim<br/>postgres-pvc (5Gi)"]
```

---

## File Manifest Index

| Manifest File | Kind / API Version | Description |
| :--- | :--- | :--- |
| `namespace.yaml` | `Namespace` (`v1`) | Creates the isolated `cloudops` namespace |
| `configmap.yaml` | `ConfigMap` (`v1`) | Non-sensitive runtime application configuration |
| `secret.yaml` | `Secret` (`v1`) | Base64-encoded credentials for database & cloud storage |
| `postgres-deployment.yaml` | `PVC` (`v1`) & `Deployment` (`apps/v1`) | PostgreSQL 16 database and 5Gi persistent volume claim |
| `postgres-service.yaml` | `Service` (`v1`) | Internal ClusterIP service exposing PostgreSQL on port 5432 |
| `deployment.yaml` | `Deployment` (`apps/v1`) | CloudOps API (2 replicas, resource limits, health probes) |
| `service.yaml` | `Service` (`v1`) | Internal ClusterIP service exposing the API on port 80 |
| `ingress.yaml` | `Ingress` (`networking.k8s.io/v1`) | NGINX Ingress routing `cloudops.example.com` to the API service |

---

## Prerequisites

Before deploying, ensure you have the following ready:

1. **Kubernetes Cluster**: A running cluster (v1.24+) such as minikube, kind, k3s, EKS, AKS, or GKE.
2. **`kubectl` CLI**: Installed and configured to interact with your cluster:
   ```bash
   kubectl cluster-info
   ```
3. **NGINX Ingress Controller**:
   The ingress resource (`ingress.yaml`) uses the `nginx` ingress class (`kubernetes.io/ingress.class: "nginx"` and `spec.ingressClassName: nginx`). Ensure the NGINX Ingress Controller is installed in your cluster.
   - For Minikube:
     ```bash
     minikube addons enable ingress
     ```
   - For generic / cloud clusters:
     ```bash
     kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.10.0/deploy/static/provider/cloud/deploy.yaml
     ```

---

## Customizing Secrets

> [!WARNING]
> The included `secret.yaml` contains placeholder base64 strings (`Q0hBTkdFX01F` which translates to `CHANGE_ME`). **You must update these with your actual credentials before applying to production.**

### Base64 Encoding Instructions

Kubernetes secrets require all values under `data:` to be encoded in standard base64 without trailing newlines.

#### Linux / macOS (bash / zsh):
```bash
echo -n "your-secret-value" | base64
```

#### Windows (PowerShell):
```powershell
[Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes("your-secret-value"))
```

### Decoding to Verify:

#### Linux / macOS:
```bash
echo "Q0hBTkdFX01F" | base64 -d
```

#### Windows (PowerShell):
```powershell
[System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String("Q0hBTkdFX01F"))
```

### Alternative: Generating Secrets Directly via `kubectl`:
```bash
kubectl create secret generic cloudops-secrets -n cloudops \
  --from-literal=DB_USER=cloudops_user \
  --from-literal=DB_PASSWORD=my_strong_db_password \
  --from-literal=POSTGRES_DB=cloudops_db \
  --from-literal=POSTGRES_USER=cloudops_user \
  --from-literal=POSTGRES_PASSWORD=my_strong_db_password \
  --from-literal=AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE \
  --from-literal=AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY \
  --dry-run=client -o yaml > secret.yaml
```

---

## Deployment Order

Kubernetes manifests must be deployed in dependency order to prevent race conditions during startup:

```
Step 1: Namespace
   ↓
Step 2: ConfigMap & Secret
   ↓
Step 3: PostgreSQL Deployment & PVC
   ↓
Step 4: PostgreSQL Service
   ↓
Step 5: CloudOps API Deployment
   ↓
Step 6: CloudOps API Service
   ↓
Step 7: Ingress Routing
```

### Step-by-Step Commands:

```bash
# 1. Create the dedicated namespace
kubectl apply -f k8s/namespace.yaml

# 2. Apply runtime configuration and credentials
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml

# 3. Deploy PostgreSQL PVC and Deployment
kubectl apply -f k8s/postgres-deployment.yaml

# 4. Deploy PostgreSQL internal ClusterIP service
kubectl apply -f k8s/postgres-service.yaml

# 5. Deploy CloudOps Enterprise API application (2 replicas)
kubectl apply -f k8s/deployment.yaml

# 6. Expose CloudOps API internally via ClusterIP
kubectl apply -f k8s/service.yaml

# 7. Apply NGINX Ingress rules
kubectl apply -f k8s/ingress.yaml
```

### One-Command Batch Deployment:

```bash
kubectl apply -f k8s/
```

---

## Verification & Health Checking

### 1. Check Pod Status
Verify all pods are in the `Running` state and ready:
```bash
kubectl get pods -n cloudops -o wide
```
*Expected output:*
- `cloudops-api-XXXXX-XXXXX` (2 pods, READY `1/1`, STATUS `Running`)
- `postgres-XXXXX-XXXXX` (1 pod, READY `1/1`, STATUS `Running`)

### 2. Verify Persistent Volume Claim
```bash
kubectl get pvc -n cloudops
```
*Expected output:* `postgres-pvc` with STATUS `Bound` and capacity `5Gi`.

### 3. Verify Services & Endpoints
```bash
kubectl get svc -n cloudops
kubectl get endpoints -n cloudops
```
*Expected output:*
- `cloudops-api-service`: Port 80 -> TargetPort 8000
- `postgres-service`: Port 5432 -> TargetPort 5432

### 4. Check Ingress Configuration
```bash
kubectl get ingress -n cloudops
```
*Expected output:*
- Host: `cloudops.example.com`
- Backend: `cloudops-api-service:80`

### 5. Inspect Application Logs
```bash
# Check CloudOps API logs
kubectl logs -n cloudops -l app=cloudops-api --tail=50 -f

# Check PostgreSQL logs
kubectl logs -n cloudops -l app=postgres --tail=50 -f
```

### 6. Test Endpoints Locally via Port-Forwarding
To test without configuring local DNS or Ingress:
```bash
kubectl port-forward svc/cloudops-api-service 8000:80 -n cloudops
```
In another terminal, test the endpoints:
```bash
# Liveness probe
curl -i http://localhost:8000/health/live

# Readiness probe
curl -i http://localhost:8000/health/ready

# Root API documentation
curl -i http://localhost:8000/docs
```

### 7. Access via Ingress Host
Add an entry in your local `hosts` file (`/etc/hosts` or `C:\Windows\System32\drivers\etc\hosts`):
```text
<INGRESS_CONTROLLER_IP> cloudops.example.com
```
Then navigate to:
```text
http://cloudops.example.com/
```

---

## Clean Up / Teardown

To delete all resources created by these manifests:

```bash
# Delete all resources in the k8s folder
kubectl delete -f k8s/

# Or delete the entire namespace (cascades deletion to all resources inside)
kubectl delete namespace cloudops
```
