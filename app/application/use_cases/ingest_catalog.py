from __future__ import annotations

import logging

from app.application.ports import EmbeddingStorePort, EncoderPort
from app.application.use_cases.verify_helpers import compute_baseline
from app.domain.value_objects import ImageData

logger = logging.getLogger(__name__)


class IngestCatalogUseCase:
    def __init__(
        self,
        encoder: EncoderPort,
        store: EmbeddingStorePort,
    ) -> None:
        self._encoder = encoder
        self._store = store

    async def execute(
        self,
        product_id: str,
        image: ImageData,
    ) -> dict[str, str | int]:
        embedding = self._encoder.encode_image(image, return_tokens=False)
        self._store.put(product_id, embedding)

        baseline = compute_baseline(self._encoder, embedding.numpy(), image)
        self._store.put_baseline(product_id, baseline.model_dump())

        self._store.save()
        logger.info("cataloged product %s (%d dims)", product_id, embedding.shape[0])
        return {
            "product_id": product_id,
            "embedding_dims": embedding.shape[0],
        }
