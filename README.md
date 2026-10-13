# CloudOps Enterprise Platform

> **Cloud Infrastructure, Automation & Deployment Ecosystem**  
> *Unlox Major Capstone Project*  
> **Target Completion Date:** 13 October 2026, 11:59 PM IST

---

## 1. Overview & Modules Alignment

The **CloudOps Enterprise Platform** is an industry-grade cloud infrastructure and DevOps automation system simulating production ecosystems operated by modern cloud organizations (e.g., Netflix, Uber, Swiggy, Zomato, Slack).

The platform addresses all **8 Core Capstone Modules**:
1. **Cloud Infrastructure Provisioning & Virtualization Layer** — IaaS architecture, EC2 compute sizing, networking & security groups, Virtualization vs. Containerization matrix (`/api/v1/system/architecture`).
2. **Cloud Networking, Storage & Data Layer** — VPC (`10.0.0.0/16`), public subnet (`10.0.1.0/24`), Internet Gateway, route tables, PostgreSQL persistent storage (`cloudops_postgres_data`), S3/MinIO-compatible object storage service (`S3StorageService`).
3. **Serverless Architecture & Microservices Design** — FastAPI microservices backend, non-root multi-stage Docker container (`UID 10001`), Kubernetes manifests (Deployments, Services, ConfigMap, Secrets, Ingress, probes).
4. **Cloud Security, IAM, Encryption & Monitoring** — Defense-in-depth model, least-privilege IAM design, restricted SSH access (`trusted_ssh_cidr`), container security context, Kubernetes readiness/liveness diagnostic probes (`/health/live`, `/health/ready`).
5. **Automation & Infrastructure as Code (IaC)** — Complete modular Terraform AWS configuration (`terraform/`) provisioning VPC, Subnet, IGW, Route Table, Security Group, and EC2 Docker host.
6. **CI/CD Pipeline Engineering for Cloud-Native Apps** — Automated GitHub Actions workflow (`.github/workflows/ci-cd.yml`) executing 4 jobs: automated testing, Docker build & Trivy security scanning, Terraform validation, and Kubernetes manifest validation.
7. **Big Data, AI & Stream Processing on Cloud** — Workload telemetry ingestion, deterministic anomaly detection ML inference engine (`/api/v1/ml/predict`), and cloud SageMaker integration design.
8. **No-Code Cloud App Deployment & Final Integration** — OpenAPI/Swagger interactive UI (`/docs`, `/redoc`), RESTful data connectors, and no-code platform integration architecture.

---

## 2. Repository Structure

```text
CloudOps-Enterprise-Platform/
├── .github/
│   └── workflows/
│       └── ci-cd.yml         # GitHub Actions 4-job CI/CD pipeline
├── .dockerignore             # Docker build exclusions (venv, git, secrets, tests)
├── .env.example              # Environment variables template
├── .gitignore                # Git exclusions (virtualenvs, secrets, caches)
├── Dockerfile                # Multi-stage production container image (non-root)
├── docker-compose.yml        # Multi-service stack (API + PostgreSQL + persistent volumes)
├── pytest.ini                # Pytest configuration
├── README.md                 # Project documentation and quickstart
├── requirements.txt          # Production and testing Python dependencies
├── docs/
│   └── architecture.md       # Comprehensive Architecture Document (Mermaid diagrams)
├── k8s/                      # Kubernetes Manifests (Production Ready)
│   ├── namespace.yaml        # Namespace: cloudops
│   ├── configmap.yaml        # Environment configuration
│   ├── secret.yaml           # Secrets template (base64 placeholder)
│   ├── deployment.yaml       # API deployment (2 replicas, resource limits, probes)
│   ├── service.yaml          # ClusterIP service (:80 -> :8000)
│   ├── postgres-deployment.yaml # PostgreSQL deployment + 5Gi PVC
│   ├── postgres-service.yaml # Internal PostgreSQL ClusterIP service (:5432)
│   ├── ingress.yaml          # NGINX Ingress controller configuration
│   └── README.md             # Kubernetes deployment guide
├── terraform/                # Infrastructure as Code (AWS)
│   ├── main.tf               # VPC, Subnet, IGW, Route Table, SG, EC2
│   ├── variables.tf          # Input variables (CIDR, instance type, sensitive db)
│   ├── outputs.tf            # Public IP, VPC ID, Subnet ID, App URL
│   ├── terraform.tfvars.example # Safe example variables template
│   └── README.md             # Terraform execution and security guide
├── src/
│   └── app/
│       ├── __init__.py
│       ├── main.py           # Application factory (create_app) & root routes
│       ├── config.py         # Application settings & environment loader
│       ├── schemas/          # Pydantic v2 schemas
│       │   ├── database.py   # Database backend & audit record schemas
│       │   ├── health.py     # Liveness, readiness, dependency schemas
│       │   ├── system.py     # System metrics & virtualization comparison schemas
│       │   ├── storage.py    # Object storage and bucket schemas
│       │   └── ml.py         # Model catalog and inference schemas
│       ├── services/         # Pluggable backend service interfaces
│       │   ├── db_service.py      # Database abstraction + PostgreSQL / Mock
│       │   ├── storage_service.py # Storage abstraction + S3/MinIO / In-Memory
│       │   └── ml_service.py      # ML abstraction + baseline heuristic classifier
│       └── api/              # API router hierarchy
│           ├── router.py     # Main /api aggregator
│           └── v1/
│               ├── router.py # /api/v1 aggregator
│               ├── database.py# /api/v1/database (CRUD, audit logs, backend info)
│               ├── health.py # /health/live, /health/ready, /health
│               ├── system.py # /api/v1/system (metrics, architecture, modules)
│               ├── storage.py# /api/v1/storage (CRUD, buckets, backend info)
│               └── ml.py     # /api/v1/ml (predict, models, backend info)
└── tests/
    ├── conftest.py           # Pytest fixtures and isolated dependency overrides
    ├── test_database.py      # Database subsystem CRUD & schema validation tests
    ├── test_health.py        # Health, liveness, and readiness probe tests
    ├── test_integration.py   # Multi-service storage and PostgreSQL integration tests
    ├── test_system.py        # System metrics & architecture comparison tests
    ├── test_storage.py       # Object storage lifecycle & error handling tests
    └── test_ml.py            # ML inference & validation tests
```

---

## 3. Local Setup & Testing

### Prerequisites
- Python 3.10+ (Tested on Python 3.14)
- Docker Desktop (Windows / WSL2 or Linux)

### Activate Virtual Environment (PowerShell)
```powershell
.\.venv\Scripts\Activate.ps1
```

### Run Automated Tests (28 Tests)
```powershell
& ".\.venv\Scripts\pytest.exe" -v
```

### Run Standalone FastAPI Development Server
```powershell
& ".\.venv\Scripts\uvicorn.exe" src.app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 4. Docker & Persistent Storage

### Multi-Stage Hardened Dockerfile
- **Builder Stage**: Python 3.12 slim compiling wheels into `/opt/venv`.
- **Runtime Stage**: Python 3.12 slim, dedicated non-root user (`appuser`, UID `10001`), total image content size `~87.7 MB`.
- **Healthcheck**: Embedded Python HTTP probe checking `/health/live`.

```powershell
docker build -t cloudops-enterprise-platform:latest .
```

### Docker Compose Stack
Orchestrates the FastAPI service and PostgreSQL with persistent volume:
```powershell
# Start services in background
docker compose up -d

# Inspect health status
docker compose ps

# Graceful shutdown (preserves volume data)
docker compose down

# Full cleanup (removes persistent volumes)
docker compose down -v
```

---

## 5. Kubernetes Deployment (`k8s/`)

The platform includes production-ready Kubernetes manifests:
1. `namespace.yaml` — Dedicated `cloudops` namespace
2. `configmap.yaml` & `secret.yaml` — Declarative runtime configuration
3. `postgres-deployment.yaml` & `postgres-service.yaml` — 5Gi PVC backed database
4. `deployment.yaml` & `service.yaml` — 2-replica API deployment with probes and limits
5. `ingress.yaml` — NGINX Ingress controller routing

### Deployment Commands
```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/postgres-service.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```

---

## 6. Infrastructure as Code (`terraform/`)

Modular Terraform configuration defining AWS infrastructure:
- **VPC & Subnets**: Custom CIDR `10.0.0.0/16`, public subnet `10.0.1.0/24`
- **Internet Gateway & Routes**: Automated outbound internet routing
- **Security Groups**: SSH restricted to operator's trusted IP (`trusted_ssh_cidr`), HTTP 8000 open, PostgreSQL 5432 kept internal
- **EC2 Compute**: `t2.micro` running Amazon Linux 2023 with automated Docker bootstrap

### Terraform Workflow
```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your IP and key pair
terraform init
terraform validate
terraform plan
# terraform apply (Requires explicit approval - do not execute without review)
```

---

## 7. CI/CD Pipeline (`.github/workflows/ci-cd.yml`)

Automated pipeline with 4 discrete jobs:
- **Job 1 (`test`)**: Python 3.12 setup, installs dependencies, executes pytest suite.
- **Job 2 (`build`)**: Builds Docker image, executes Trivy container vulnerability scanner.
- **Job 3 (`validate-infra`)**: Runs `terraform init` and `terraform validate`.
- **Job 4 (`validate-k8s`)**: Validates Kubernetes manifests with `kubectl dry-run`.

---

## 8. API Endpoints Reference

### Documentation
- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`
- **OpenAPI JSON**: `http://127.0.0.1:8000/openapi.json`

### Health & Monitoring
| Method | Endpoint | Description |
|:---|:---|:---|
| `GET` | `/health/live` | Kubernetes Liveness Probe (`status: "live"`) |
| `GET` | `/health/ready` | Kubernetes Readiness Probe (Storage, ML, DB checks) |
| `GET` | `/health` | Consolidated diagnostic health report |

### Database Subsystem (Module 2)
| Method | Endpoint | Description |
|:---|:---|:---|
| `GET` | `/api/v1/database/info` | PostgreSQL backend connectivity status |
| `POST` | `/api/v1/database/records` | Insert operational audit record |
| `GET` | `/api/v1/database/records` | Query audit log records |

### Storage Subsystem (Module 2)
| Method | Endpoint | Description |
|:---|:---|:---|
| `GET` | `/api/v1/storage/info` | Storage backend status & provider info |
| `GET` | `/api/v1/storage/buckets` | List storage buckets |
| `POST` | `/api/v1/storage/objects` | Store / upload object |
| `GET` | `/api/v1/storage/objects` | List objects in bucket |
| `GET` | `/api/v1/storage/objects/{key}` | Retrieve stored object |
| `DELETE` | `/api/v1/storage/objects/{key}` | Delete object |

### Machine Learning Inference (Module 7)
| Method | Endpoint | Description |
|:---|:---|:---|
| `GET` | `/api/v1/ml/info` | ML model metadata & task description |
| `GET` | `/api/v1/ml/models` | List registered models in catalog |
| `POST` | `/api/v1/ml/predict` | Workload anomaly classification |

### System & Architecture (Module 1)
| Method | Endpoint | Description |
|:---|:---|:---|
| `GET` | `/api/v1/system/metrics` | Host OS, runtime, PID, thread metrics |
| `GET` | `/api/v1/system/architecture` | Virtualization vs Containerization matrix |
| `GET` | `/api/v1/system/modules` | 8-module ecosystem status |

---

## 9. Deliverables Tracking & Verification Status

| Deliverable | Status | Verification Evidence |
|:---|:---|:---|
| **D1: Core FastAPI App & APIs** | ✅ **Completed & Verified** | 28 automated tests passing; Swagger UI operational |
| **D2: Docker & Persistent Storage** | ✅ **Completed & Verified** | Multi-stage image built (87.7 MB, non-root UID 10001); PostgreSQL volume persistence tested |
| **D3: Architecture Documentation** | ✅ **Completed & Verified** | Comprehensive `docs/architecture.md` with Mermaid diagrams & spec mapping |
| **D4: Infrastructure as Code (IaC)** | 📋 **Configuration Ready** | Modular `terraform/` (VPC, Subnet, IGW, SG, EC2, UserData, README) |
| **D5: Kubernetes Manifests** | 📋 **Configuration Ready** | 8 validated YAML manifests in `k8s/` + deployment guide |
| **D6: CI/CD Pipeline** | 📋 **Configuration Ready** | Syntax-validated GitHub Actions workflow (`.github/workflows/ci-cd.yml`) |
| **D7: Security, IAM & Monitoring** | ✅ **Completed & Documented** | Security model in `docs/architecture.md`, probes in app, restricted SG in Terraform |
| **D8: Big Data & ML Pipeline** | ✅ **Completed & Tested** | Telemetry schema, deterministic classifier, 7 passing ML tests |
| **D9: No-Code Integration** | ✅ **Completed & Documented** | OpenAPI/Swagger interactive UI ready for low-code platform connectors |
