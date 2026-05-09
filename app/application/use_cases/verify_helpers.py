from __future__ import annotations

import logging

import cv2
import numpy as np
from torch.nn.functional import cosine_similarity

from app.application.ports import EncoderPort
from app.domain.entities import ProductBaseline, VerificationResult
from app.domain.value_objects import ImageData

logger = logging.getLogger(__name__)


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


def _augment_brightness(image: np.ndarray) -> np.ndarray:
    factor = np.random.uniform(0.7, 1.3)
    return np.clip(image.astype(np.float32) * factor, 0, 255).astype(np.uint8)


def _augment_blur(image: np.ndarray) -> np.ndarray:
    k = np.random.choice([3, 5])
    return cv2.GaussianBlur(image, (k, k), 0)


def _augment_shadow(image: np.ndarray) -> np.ndarray:
    h, w = image.shape[:2]
    mask = np.ones((h, w), dtype=np.float32) * 0.5
    cx, cy = np.random.randint(0, w), np.random.randint(0, h)
    yy, xx = np.ogrid[:h, :w]
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    radius = min(h, w) // 2
    mask[dist < radius] = 1.0
    return np.clip(image.astype(np.float32) * mask[..., None], 0, 255).astype(
        np.uint8,
    )


def _augment_color_shift(image: np.ndarray) -> np.ndarray:
    shift = np.random.randint(-20, 20, size=3).astype(np.int16)
    img = image.astype(np.int16) + shift
    return np.clip(img, 0, 255).astype(np.uint8)


def _augment_rotation(image: np.ndarray) -> np.ndarray:
    angle = np.random.uniform(-5, 5)
    h, w = image.shape[:2]
    matrix = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    return cv2.warpAffine(image, matrix, (w, h), borderMode=cv2.BORDER_REFLECT)


_AUGMENTATIONS = [
    _augment_brightness,
    _augment_blur,
    _augment_shadow,
    _augment_color_shift,
    _augment_rotation,
]


def compute_baseline(
    encoder: EncoderPort,
    catalog_embedding: np.ndarray,
    image: ImageData,
) -> ProductBaseline:
    import torch

    img = to_numpy(image)
    augmented = [aug(img) for aug in _AUGMENTATIONS]
    embeddings = encoder.encode_batch(augmented)

    catalog_t = torch.from_numpy(catalog_embedding).unsqueeze(0)
    sims = cosine_similarity(catalog_t, embeddings, dim=-1).numpy()

    mean = float(sims.mean())
    std = float(sims.std())
    mn = float(sims.min())

    threshold = mean - 2 * std
    regional_threshold = mn - 0.05
    delta_threshold = 0.15

    logger.info(
        "baseline: mean=%.3f std=%.3f min=%.3f threshold=%.3f",
        mean,
        std,
        mn,
        threshold,
    )
    return ProductBaseline(
        mean=mean,
        std=std,
        min=mn,
        threshold=threshold,
        regional_threshold=regional_threshold,
        delta_threshold=delta_threshold,
    )
