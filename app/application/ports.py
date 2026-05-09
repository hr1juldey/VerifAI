from __future__ import annotations

import abc

import torch

from app.domain.entities import SpatialDiffMap
from app.domain.value_objects import ImageData, ProductId


class EncoderPort(abc.ABC):
    @abc.abstractmethod
    def encode_image(
        self,
        image: ImageData,
        return_tokens: bool = False,
    ) -> torch.Tensor | tuple[torch.Tensor, torch.Tensor]: ...

    @abc.abstractmethod
    def encode_batch(
        self,
        images: list[ImageData],
        return_tokens: bool = False,
    ) -> torch.Tensor | tuple[torch.Tensor, torch.Tensor]: ...


class EmbeddingStorePort(abc.ABC):
    @abc.abstractmethod
    def get(self, product_id: ProductId) -> torch.Tensor | None: ...

    @abc.abstractmethod
    def put(self, product_id: ProductId, embedding: torch.Tensor) -> None: ...

    @abc.abstractmethod
    def get_baseline(self, product_id: ProductId) -> dict | None: ...

    @abc.abstractmethod
    def put_baseline(self, product_id: ProductId, baseline: dict) -> None: ...

    @abc.abstractmethod
    def save(self) -> None: ...

    @abc.abstractmethod
    def load(self) -> None: ...

    @abc.abstractmethod
    def size(self) -> int: ...


class SpatialDiffPort(abc.ABC):
    @abc.abstractmethod
    def compute_diff(
        self,
        tokens_a: torch.Tensor,
        tokens_b: torch.Tensor,
    ) -> SpatialDiffMap: ...

    @abc.abstractmethod
    def render_overlay(
        self,
        image: ImageData,
        diff_map: SpatialDiffMap,
    ) -> SpatialDiffMap: ...

    @abc.abstractmethod
    def create_composite(
        self,
        catalog_image: ImageData,
        annotated_return: ImageData,
    ) -> SpatialDiffMap: ...


class ExplainerPort(abc.ABC):
    @abc.abstractmethod
    async def explain(
        self,
        catalog_image_path: str,
        annotated_return_path: str,
        product_description: str,
    ) -> tuple[str, str]: ...
