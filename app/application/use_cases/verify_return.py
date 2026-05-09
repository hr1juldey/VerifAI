from __future__ import annotations

import base64
import logging
import tempfile
import time

import cv2
import numpy as np
from torch.nn.functional import cosine_similarity

from app.application.ports import (
    EmbeddingStorePort,
    EncoderPort,
    ExplainerPort,
    SpatialDiffPort,
)
from app.application.use_cases.explain_rejection import ExplainRejectionUseCase
from app.application.use_cases.verify_helpers import make_error_result, to_numpy
from app.domain.entities import VerificationResult
from app.domain.value_objects import ImageData
from app.infrastructure.ijepa_encoder import normalize_clahe
from app.infrastructure.spatial_diff import compute_patch_deltas

logger = logging.getLogger(__name__)

DEFAULT_THRESHOLD = 0.7
DEFAULT_REGIONAL_THRESHOLD = 0.25
DEFAULT_DELTA_THRESHOLD = 0.15


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
            return make_error_result(product_id)

        baseline = self._store.get_baseline(product_id)
        product_threshold = baseline["threshold"] if baseline else self._threshold
        regional_threshold = (
            baseline["regional_threshold"] if baseline else DEFAULT_REGIONAL_THRESHOLD
        )
        delta_threshold = (
            baseline["delta_threshold"] if baseline else DEFAULT_DELTA_THRESHOLD
        )

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

        # --- MATCH path ---
        if score < product_threshold:
            return await self._reject(
                product_id,
                score,
                elapsed,
                catalog_image,
                return_image,
                catalog_tokens,
                return_tokens,
            )

        # --- Check regional spatial diff ---
        diff_map, flagged_count, contiguous_regions = (
            self._spatial.compute_regional_stats(
                catalog_tokens,
                return_tokens,
                regional_threshold=regional_threshold,
            )
        )

        if contiguous_regions >= 2:
            return await self._suspect(
                product_id,
                score,
                elapsed,
                baseline,
                product_threshold,
                delta_threshold,
                catalog_image,
                return_image,
                catalog_tokens,
                return_tokens,
                diff_map,
            )

        # --- Clean MATCH ---
        return VerificationResult(
            decision="MATCH",
            confidence=score,
            product_id=product_id,
            latency_ms=elapsed,
            baseline_threshold=product_threshold,
        )

    async def _suspect(
        self,
        product_id: str,
        score: float,
        elapsed_start: float,
        baseline: dict | None,
        product_threshold: float,
        delta_threshold: float,
        catalog_image: ImageData,
        return_image: ImageData,
        catalog_tokens,
        return_tokens,
        diff_map,
    ) -> VerificationResult:
        # Augmentation consistency test: CLAHE normalize + re-encode
        norm_img = normalize_clahe(return_image)
        _, norm_tokens = self._encoder.encode_image(norm_img, return_tokens=True)
        deltas = compute_patch_deltas(return_tokens, norm_tokens, catalog_tokens)

        max_delta = float(np.max(deltas))
        t_now = (time.perf_counter() - elapsed_start / 1000) * 1000

        if max_delta > delta_threshold:
            # Lighting artifact → resolve to MATCH
            return VerificationResult(
                decision="MATCH",
                confidence=score,
                product_id=product_id,
                latency_ms=t_now,
                suspect_reason="LIGHTING_ARTIFACT",
                baseline_threshold=product_threshold,
            )

        if max_delta < delta_threshold * 0.33:
            # Content diff → escalate to REJECT
            return await self._reject(
                product_id,
                score,
                elapsed_start,
                catalog_image,
                return_image,
                catalog_tokens,
                return_tokens,
                suspect_reason="CONTENT_DIFF",
            )

        # Ambiguous → keep SUSPECT, ask Gemma
        diff_map = self._spatial.render_overlay(return_image, diff_map)
        diff_map = self._spatial.create_composite(catalog_image, diff_map)
        verdict, explanation = await self._get_explanation(
            catalog_image,
            diff_map.annotated_image,
            product_id,
        )

        _, buf = cv2.imencode(".png", diff_map.annotated_image)
        b64 = base64.b64encode(buf).decode()

        if verdict == "LIGHTING_ARTIFACT":
            decision = "MATCH"
        else:
            decision = "REJECT"

        return VerificationResult(
            decision=decision,
            confidence=score,
            product_id=product_id,
            latency_ms=(time.perf_counter() - elapsed_start / 1000) * 1000,
            spatial_diff_image=b64,
            explanation=explanation,
            suspect_reason="LIGHTING_ARTIFACT"
            if decision == "MATCH"
            else "CONTENT_DIFF",
            baseline_threshold=product_threshold,
        )

    async def _reject(
        self,
        product_id: str,
        score: float,
        elapsed_start: float,
        catalog_image: ImageData,
        return_image: ImageData,
        catalog_tokens,
        return_tokens,
        suspect_reason: str | None = None,
    ) -> VerificationResult:
        diff_map = self._spatial.compute_diff(catalog_tokens, return_tokens)
        diff_map = self._spatial.render_overlay(return_image, diff_map)
        diff_map = self._spatial.create_composite(catalog_image, diff_map)

        _, explanation = await self._get_explanation(
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
            latency_ms=(time.perf_counter() - elapsed_start / 1000) * 1000,
            spatial_diff_image=b64,
            explanation=explanation,
            suspect_reason=suspect_reason,
        )

    async def _get_explanation(
        self,
        catalog_img: ImageData,
        annotated: ImageData,
        product_id: str,
    ) -> tuple[str, str]:
        with (
            tempfile.NamedTemporaryFile(suffix=".png") as cat_f,
            tempfile.NamedTemporaryFile(suffix=".png") as ret_f,
        ):
            cv2.imwrite(cat_f.name, to_numpy(catalog_img))
            cv2.imwrite(ret_f.name, to_numpy(annotated))
            return await self._explain.execute(
                cat_f.name,
                ret_f.name,
                product_id,
            )
