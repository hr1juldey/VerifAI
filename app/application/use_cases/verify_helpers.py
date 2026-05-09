from __future__ import annotations

import numpy as np

from app.domain.entities import VerificationResult
from app.domain.value_objects import ImageData


def make_error_result(product_id: str) -> VerificationResult:
    return VerificationResult(
        decision="ERROR",
        confidence=0.0,
        product_id=product_id,
        latency_ms=0,
        explanation=f"Product {product_id} not registered",
    )


def to_numpy(image: ImageData) -> np.ndarray:
    if isinstance(image, np.ndarray):
        return image
    return np.array(image)
