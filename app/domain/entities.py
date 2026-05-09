from __future__ import annotations

import numpy as np
import torch
from pydantic import BaseModel, Field


class Embedding(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    product_id: str
    tensor: torch.Tensor


class SpatialDiffMap(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    heatmap: np.ndarray
    annotated_image: np.ndarray
    composite_image: np.ndarray | None = Field(default=None)


class VerificationResult(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    decision: str
    confidence: float
    latency_ms: float
    product_id: str
    spatial_diff_image: str | None = Field(default=None)
    explanation: str | None = Field(default=None)
