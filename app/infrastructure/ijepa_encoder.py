from __future__ import annotations

import logging

import torch
from transformers import pipeline

from app.application.ports import EncoderPort
from app.domain.value_objects import ImageData

logger = logging.getLogger(__name__)

MODEL_ID = "facebook/ijepa_vith14_22k"


class IjepaEncoder(EncoderPort):
    def __init__(self, device: str = "cuda") -> None:
        self._device = device
        device_id = 0 if (device == "cuda" and torch.cuda.is_available()) else -1
        self._pipe = pipeline(
            "image-feature-extraction", model=MODEL_ID, device=device_id,
        )
        self._model = self._pipe.model
        self._processor = self._pipe.image_processor
        self._model.eval()
        if device_id >= 0:
            vram = torch.cuda.memory_allocated() / 1e9
            logger.info("I-JEPA loaded on GPU, %.1f GB VRAM", vram)
        else:
            logger.warning("I-JEPA running on CPU - degraded performance")

    def encode_image(
        self,
        image: ImageData,
        return_tokens: bool = False,
    ) -> torch.Tensor | tuple[torch.Tensor, torch.Tensor]:
        from PIL import Image as PILImage

        import numpy as np

        if isinstance(image, np.ndarray):
            image = PILImage.fromarray(image)
        inputs = self._processor(image, return_tensors="pt").to(self._device)
        with torch.no_grad():
            outputs = self._model(**inputs)
        hidden = outputs.last_hidden_state
        if self._device == "cuda":
            hidden = hidden.float()
        tokens = hidden.squeeze(0)
        pooled = tokens.mean(dim=0)
        if return_tokens:
            return pooled.cpu(), tokens.cpu()
        return pooled.cpu()

    def encode_batch(
        self,
        images: list[ImageData],
        return_tokens: bool = False,
    ) -> torch.Tensor | tuple[torch.Tensor, torch.Tensor]:
        results = [self.encode_image(img, return_tokens) for img in images]
        if return_tokens:
            pooled = torch.stack([r[0] for r in results])
            tokens = torch.stack([r[1] for r in results])
            return pooled, tokens
        return torch.stack(results)
