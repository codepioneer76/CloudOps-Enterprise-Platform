"""System metrics and CloudOps architecture endpoints."""

import os
import platform
import threading
from fastapi import APIRouter, Depends, status

from app.config import Settings, get_settings
from app.schemas.system import (
    ArchitectureComparisonItem,
    CloudOpsOverviewResponse,
    ModuleStatusItem,
    SystemMetricsResponse,
    VirtualizationComparisonResponse,
)

router = APIRouter(prefix="/system", tags=["System & Architecture"])


@router.get(
    "/metrics",
    response_model=SystemMetricsResponse,
    status_code=status.HTTP_200_OK,
    summary="Host & Runtime Metrics",
)
def get_system_metrics(
    settings: Settings = Depends(get_settings),
) -> SystemMetricsResponse:
    return SystemMetricsResponse(
        os_name=platform.platform(),
        python_version=platform.python_version(),
        pid=os.getpid(),
        environment=settings.app_env,
        container_ready=True,
        active_threads=threading.active_count(),
    )


@router.get(
    "/architecture",
    response_model=VirtualizationComparisonResponse,
    status_code=status.HTTP_200_OK,
    summary="Module 1: Virtualization vs Containerization Comparison",
)
def get_virtualization_comparison() -> VirtualizationComparisonResponse:
    matrix = [
        ArchitectureComparisonItem(
            dimension="Architecture Abstraction",
            virtual_machine="Hardware-level virtualization via Hypervisor (Type 1/Type 2). Emulates entire guest OS kernel.",
            container_docker="OS-level virtualization sharing host OS kernel via namespaces (pid, net, mnt) and cgroups.",
            enterprise_recommendation="Use Containers for microservices density and rapid scaling; use VMs for strong multi-tenant kernel isolation.",
        ),
        ArchitectureComparisonItem(
            dimension="Startup Time",
            virtual_machine="Minutes (full OS boot, init system, driver loading).",
            container_docker="Milliseconds to seconds (process launch within existing kernel).",
            enterprise_recommendation="Containers optimize autoscaling responsiveness and blue-green zero-downtime cutovers.",
        ),
        ArchitectureComparisonItem(
            dimension="Resource Overhead",
            virtual_machine="High: requires dedicated memory, disk, and CPU allocated per guest OS.",
            container_docker="Minimal: shares host OS memory buffers and kernel memory structures.",
            enterprise_recommendation="Containers maximize compute density on cloud nodes (EC2/EKS).",
        ),
        ArchitectureComparisonItem(
            dimension="Portability & Packaging",
            virtual_machine="AMIs / VMDK / VHD - gigabytes in size, hypervisor-dependent formats.",
            container_docker="OCI Container Images - layered, immutable, registry-backed, run anywhere Docker/containerd runs.",
            enterprise_recommendation="OCI standard images provide immutable CI/CD promotion across Dev, Staging, and Prod.",
        ),
        ArchitectureComparisonItem(
            dimension="Security & Isolation",
            virtual_machine="Hardware-enforced boundary. Hypervisor security ring isolation.",
            container_docker="Process-level isolation. Shared kernel requires Seccomp, AppArmor/SELinux, and non-root users.",
            enterprise_recommendation="Pair hardened container distros (Distroless/Alpine) with dedicated node pools.",
        ),
    ]

    return VirtualizationComparisonResponse(
        title="Virtualization (IaaS) vs Containerization (Docker) Technical Analysis",
        matrix=matrix,
        summary=(
            "The CloudOps Enterprise Platform employs Docker containerization orchestrated via "
            "Kubernetes for microservices, deployed atop resilient cloud infrastructure (IaaS / managed nodes)."
        ),
    )


@router.get(
    "/modules",
    response_model=CloudOpsOverviewResponse,
    status_code=status.HTTP_200_OK,
    summary="CloudOps Platform 8-Module Ecosystem Status",
)
def get_modules_status() -> CloudOpsOverviewResponse:
    modules = [
        ModuleStatusItem(
            module_number=1,
            module_name="Cloud Infrastructure Provisioning & Virtualization Layer",
            status="in_progress",
            description="IaaS architecture blueprint, virtualization vs containerization analysis, foundational web server.",
        ),
        ModuleStatusItem(
            module_number=2,
            module_name="Cloud Networking, Storage & Data Layer",
            status="pending",
            description="VPC, subnets, route tables, IGW/NAT, S3 lifecycle policies, and RDS/database connectivity.",
        ),
        ModuleStatusItem(
            module_number=3,
            module_name="Serverless Architecture & Microservices Design",
            status="in_progress",
            description="FastAPI microservices, Docker containerization, Kubernetes manifests, and serverless triggers.",
        ),
        ModuleStatusItem(
            module_number=4,
            module_name="Cloud Security, IAM, Encryption & Monitoring",
            status="pending",
            description="Least privilege IAM policies, KMS encryption at rest/transit, CloudWatch dashboards & alerts.",
        ),
        ModuleStatusItem(
            module_number=5,
            module_name="Automation & Infrastructure as Code (IaC)",
            status="pending",
            description="Terraform configurations for end-to-end cloud environment provisioning.",
        ),
        ModuleStatusItem(
            module_number=6,
            module_name="CI/CD Pipeline Engineering for Cloud-Native Apps",
            status="pending",
            description="GitHub Actions automated lint, test, docker build, image scanning, and deploy workflows.",
        ),
        ModuleStatusItem(
            module_number=7,
            module_name="Big Data, AI & Stream Processing on Cloud",
            status="pending",
            description="Telemetry streaming ingestion, analytics warehouse schema, and ML inference service.",
        ),
        ModuleStatusItem(
            module_number=8,
            module_name="No-Code Cloud App Deployment & Final Integration",
            status="pending",
            description="No-code operational portal connecting to backend cloud APIs, complete with demo artifacts.",
        ),
    ]

    return CloudOpsOverviewResponse(
        project_title="CloudOps Enterprise Platform: Cloud Infrastructure, Automation & Deployment Ecosystem",
        deadline="2026-10-13 23:59:00 IST",
        total_modules=8,
        modules=modules,
    )
