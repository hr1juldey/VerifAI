from __future__ import annotations

import numpy as np
import torch

from app.infrastructure.spatial_diff import SpatialDiff


def test_compute_diff_identical(random_tokens):
    sd = SpatialDiff()
    result = sd.compute_diff(random_tokens, random_tokens)
    assert result.heatmap.shape == (16, 16)
    assert np.allclose(result.heatmap, 0.0, atol=1e-5)


def test_compute_diff_different(random_tokens):
    sd = SpatialDiff()
    other = torch.randn_like(random_tokens)
    result = sd.compute_diff(random_tokens, other)
    assert result.heatmap.shape == (16, 16)
    assert result.heatmap.max() > 0.0


def test_render_overlay(random_image, random_tokens):
    sd = SpatialDiff()
    diff_map = sd.compute_diff(random_tokens, torch.randn_like(random_tokens))
    rendered = sd.render_overlay(np.array(random_image), diff_map)
    assert rendered.annotated_image.shape == (224, 224, 3)
    assert rendered.annotated_image.dtype == np.uint8


def test_create_composite(random_image, random_tokens):
    sd = SpatialDiff()
    diff_map = sd.compute_diff(random_tokens, torch.randn_like(random_tokens))
    rendered = sd.render_overlay(np.array(random_image), diff_map)
    composite = sd.create_composite(np.array(random_image), rendered)
    assert composite.composite_image is not None
    assert composite.composite_image.shape[1] == 224 * 2
