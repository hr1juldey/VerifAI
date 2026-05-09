from __future__ import annotations

from pydantic import BaseModel, Field


class CatalogResponse(BaseModel):
    product_id: str
    embedding_dims: int


class VerifyResponse(BaseModel):
    decision: str
    confidence: float
    latency_ms: float
    product_id: str
    spatial_diff_image: str | None = Field(default=None)
    explanation: str | None = Field(default=None)
    suspect_reason: str | None = Field(default=None)
    baseline_threshold: float | None = Field(default=None)


class HealthResponse(BaseModel):
    status: str
    gpu_available: bool
    model_loaded: bool
    cache_size: int
    ollama_provider: str
    ollama_connected: bool


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = Field(default=None)


class CalibrateRequest(BaseModel):
    product_id: str
    category: str
    decision: str
    human_label: str
    cosine_sim: float


class CalibrateResponse(BaseModel):
    status: str


class CalibrationStatsResponse(BaseModel):
    categories: dict[str, dict] | None = Field(default=None)
    status: str | None = Field(default=None)
