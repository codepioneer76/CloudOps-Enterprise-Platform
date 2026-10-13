"""Machine Learning inference and model catalog endpoints."""

from typing import List
from fastapi import APIRouter, Depends, status

from app.schemas.ml import (
    MLBackendInfo,
    MLModelCatalogItem,
    MLPredictionResponse,
    WorkloadMetricsInput,
)
from app.services.ml_service import MLService, get_ml_service

router = APIRouter(prefix="/ml", tags=["Machine Learning Inference"])


@router.get(
    "/info",
    response_model=MLBackendInfo,
    status_code=status.HTTP_200_OK,
    summary="ML Inference Backend Status",
)
def get_ml_info(
    ml: MLService = Depends(get_ml_service),
) -> MLBackendInfo:
    return ml.get_backend_info()


@router.get(
    "/models",
    response_model=List[MLModelCatalogItem],
    status_code=status.HTTP_200_OK,
    summary="List Registered Models",
)
def list_models(
    ml: MLService = Depends(get_ml_service),
) -> List[MLModelCatalogItem]:
    return ml.list_models()


@router.post(
    "/predict",
    response_model=MLPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Run Workload Anomaly Inference",
    description="Evaluates workload telemetry to detect anomalies, capacity bottlenecks, or normal operations.",
)
def predict_workload(
    metrics: WorkloadMetricsInput,
    ml: MLService = Depends(get_ml_service),
) -> MLPredictionResponse:
    return ml.predict(metrics)
