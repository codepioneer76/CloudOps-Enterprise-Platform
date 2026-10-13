"""System and architecture schemas."""

from typing import Dict, List, Any
from pydantic import BaseModel, Field


class SystemMetricsResponse(BaseModel):
    """Runtime system environment metrics."""
    os_name: str
    python_version: str
    pid: int
    environment: str
    container_ready: bool = True
    active_threads: int


class ArchitectureComparisonItem(BaseModel):
    """Comparison matrix entry between Virtualization and Containerization."""
    dimension: str
    virtual_machine: str
    container_docker: str
    enterprise_recommendation: str


class VirtualizationComparisonResponse(BaseModel):
    """Module 1 comparison between IaaS virtualization and Docker containers."""
    title: str = "Virtualization vs Containerization Architecture Comparison"
    matrix: List[ArchitectureComparisonItem]
    summary: str


class ModuleStatusItem(BaseModel):
    """Status entry for each of the 8 CloudOps Capstone modules."""
    module_number: int
    module_name: str
    status: str
    description: str


class CloudOpsOverviewResponse(BaseModel):
    """High-level status of all 8 CloudOps enterprise modules."""
    project_title: str
    deadline: str
    total_modules: int = 8
    modules: List[ModuleStatusItem]
