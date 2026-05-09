from __future__ import annotations

import base64
import logging
import tempfile
import time

import cv2
from torch.nn.functional import cosine_similarity

from app.application.ports import (
    EmbeddingStorePort,
    EncoderPort,
    ExplainerPort,
    SpatialDiffPort,
)
from app.application.use_cases.explain_rejection import ExplainRejectionUseCase
from app.domain.entities import VerificationResult
from app.domain.value_objects import ImageData

logger = logging.getLogger(__name__)

DEFAULT_THRESHOLD = 0.7


class VerifyReturnUseCase:
    def __init__(
        self,
        encoder: EncoderPort,
        store: EmbeddingStorePort,
        spatial: SpatialDiffPort,
        explainer: ExplainerPort,
        threshold: float = DEFAULT_THRESHOLD,
    ) -> None:
        self._encoder = encoder
        self._store = store
        self._spatial = spatial
        self._threshold = threshold
        self._explain = ExplainRejectionUseCase(explainer)

    async def execute(
        self,
        product_id: str,
        return_image: ImageData,
        catalog_image: ImageData,
    ) -> VerificationResult:
        t0 = time.perf_counter()
        catalog_emb = self._store.get(product_id)
        if catalog_emb is None:
            return _error_result(product_id)

        return_emb, return_tokens = self._encoder.encode_image(
            return_image,
            return_tokens=True,
        )
        _, catalog_tokens = self._encoder.encode_image(
            catalog_image,
            return_tokens=True,
        )
        score = cosine_similarity(
            catalog_emb.unsqueeze(0),
            return_emb.unsqueeze(0),
        ).item()
        elapsed = (time.perf_counter() - t0) * 1000

        if score >= self._threshold:
            return VerificationResult(
                decision="MATCH",
                confidence=score,
                product_id=product_id,
                latency_ms=elapsed,
            )

        diff_map = self._spatial.compute_diff(catalog_tokens, return_tokens)
        diff_map = self._spatial.render_overlay(return_image, diff_map)
        diff_map = self._spatial.create_composite(catalog_image, diff_map)

        explanation = await self._get_explanation(
            catalog_image,
            diff_map.annotated_image,
            product_id,
        )
        _, buf = cv2.imencode(".png", diff_map.annotated_image)
        b64 = base64.b64encode(buf).decode()

        return VerificationResult(
            decision="REJECT",
            confidence=score,
            product_id=product_id,
            latency_ms=elapsed,
            spatial_diff_image=b64,
            explanation=explanation,
        )

    async def _get_explanation(
        self,
        catalog_img: ImageData,
        annotated: ImageData,
        product_id: str,
    ) -> str:
        with (
            tempfile.NamedTemporaryFile(suffix=".png") as cat_f,
            tempfile.NamedTemporaryFile(suffix=".png") as ret_f,
        ):
            cv2.imwrite(cat_f.name, _to_numpy(catalog_img))
            cv2.imwrite(ret_f.name, _to_numpy(annotated))
            return await self._explain.execute(
                cat_f.name,
                ret_f.name,
                product_id,
            )


def _error_result(product_id: str) -> VerificationResult:
    return VerificationResult(
        decision="ERROR",
        confidence=0.0,
        product_id=product_id,
        latency_ms=0,
        explanation=f"Product {product_id} not registered",
    )


def _to_numpy(image: ImageData):
    import numpy as np

    if isinstance(image, np.ndarray):
        return image
    return np.array(image)
