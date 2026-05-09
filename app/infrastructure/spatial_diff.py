from __future__ import annotations

import cv2
import numpy as np
import torch
from torch.nn.functional import cosine_similarity

from app.application.ports import SpatialDiffPort
from app.domain.entities import SpatialDiffMap
from app.domain.value_objects import ImageData

DEFAULT_ALPHA = 0.4
DEFAULT_DIFF_THRESHOLD = 0.5
HEATMAP_PATCH_SIZE = 14
HEATMAP_GRID = 16


class SpatialDiff(SpatialDiffPort):
    def __init__(
        self,
        alpha: float = DEFAULT_ALPHA,
        diff_threshold: float = DEFAULT_DIFF_THRESHOLD,
    ) -> None:
        self._alpha = alpha
        self._diff_threshold = diff_threshold

    def compute_diff(
        self,
        tokens_a: torch.Tensor,
        tokens_b: torch.Tensor,
        regional_threshold: float | None = None,
    ) -> SpatialDiffMap:
        sims = cosine_similarity(tokens_a, tokens_b, dim=-1)
        diff_scores = 1.0 - sims.numpy()
        heatmap = diff_scores.reshape(HEATMAP_GRID, HEATMAP_GRID)
        return SpatialDiffMap(heatmap=heatmap, annotated_image=np.array([]))

    def compute_regional_stats(
        self,
        tokens_a: torch.Tensor,
        tokens_b: torch.Tensor,
        regional_threshold: float,
    ) -> tuple[SpatialDiffMap, int, int]:
        diff_map = self.compute_diff(tokens_a, tokens_b)
        flagged = diff_map.heatmap > regional_threshold
        flagged_count = int(flagged.sum())
        contiguous_regions = _count_contiguous(flagged)
        return diff_map, flagged_count, contiguous_regions

    def render_overlay(
        self,
        image: ImageData,
        diff_map: SpatialDiffMap,
    ) -> SpatialDiffMap:
        img = _to_bgr_uint8(image)
        h, w = img.shape[:2]
        heatmap_up = cv2.resize(
            diff_map.heatmap.astype(np.float32),
            (w, h),
            interpolation=cv2.INTER_LINEAR,
        )
        heatmap_norm = np.clip(heatmap_up * 2.0, 0, 1)
        colored = cv2.applyColorMap(
            (heatmap_norm * 255).astype(np.uint8),
            cv2.COLORMAP_JET,
        )
        mask = diff_map.heatmap.reshape(
            HEATMAP_GRID,
            HEATMAP_GRID,
        )
        mask_up = cv2.resize(
            mask.astype(np.float32),
            (w, h),
            interpolation=cv2.INTER_LINEAR,
        )
        overlay = np.where(mask_up[..., None] > self._diff_threshold, colored, img)
        blended = cv2.addWeighted(overlay, self._alpha, img, 1 - self._alpha, 0)
        return SpatialDiffMap(
            heatmap=diff_map.heatmap,
            annotated_image=blended,
        )

    def create_composite(
        self,
        catalog_image: ImageData,
        diff_map: SpatialDiffMap,
    ) -> SpatialDiffMap:
        cat = _to_bgr_uint8(catalog_image)
        ret = diff_map.annotated_image
        h = max(cat.shape[0], ret.shape[0])
        cat_r = cv2.resize(cat, (cat.shape[1], h))
        ret_r = cv2.resize(ret, (ret.shape[1], h))
        composite = np.hstack([cat_r, ret_r])
        return SpatialDiffMap(
            heatmap=diff_map.heatmap,
            annotated_image=diff_map.annotated_image,
            composite_image=composite,
        )


def _to_bgr_uint8(image: ImageData) -> np.ndarray:
    from PIL import Image as PILImage

    if isinstance(image, PILImage.Image):
        image = np.array(image)
    if image.dtype != np.uint8:
        image = (image * 255).clip(0, 255).astype(np.uint8)
    if len(image.shape) == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    if image.shape[2] == 4:
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    return image


def compute_patch_deltas(
    raw_tokens: torch.Tensor,
    norm_tokens: torch.Tensor,
    catalog_tokens: torch.Tensor,
) -> np.ndarray:
    raw_sims = cosine_similarity(raw_tokens, catalog_tokens, dim=-1)
    norm_sims = cosine_similarity(norm_tokens, catalog_tokens, dim=-1)
    deltas = (norm_sims - raw_sims).numpy()
    return deltas.reshape(HEATMAP_GRID, HEATMAP_GRID)


def _count_contiguous(flagged: np.ndarray) -> int:
    visited = np.zeros_like(flagged, dtype=bool)
    regions = 0
    for i in range(flagged.shape[0]):
        for j in range(flagged.shape[1]):
            if flagged[i, j] and not visited[i, j]:
                _flood_fill(flagged, visited, i, j)
                regions += 1
    return regions


def _flood_fill(grid: np.ndarray, visited: np.ndarray, i: int, j: int) -> None:
    stack = [(i, j)]
    while stack:
        ci, cj = stack.pop()
        if ci < 0 or ci >= grid.shape[0] or cj < 0 or cj >= grid.shape[1]:
            continue
        if visited[ci, cj] or not grid[ci, cj]:
            continue
        visited[ci, cj] = True
        stack.extend([(ci - 1, cj), (ci + 1, cj), (ci, cj - 1), (ci, cj + 1)])
