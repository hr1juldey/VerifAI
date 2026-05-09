from __future__ import annotations

import logging

import cv2
import numpy as np
import torch
from transformers import pipeline

from app.application.ports import EncoderPort
from app.domain.value_objects import ImageData

logger = logging.getLogger(__name__)


def normalize_clahe(image: ImageData) -> np.ndarray:
    if not isinstance(image, np.ndarray):
        image = np.array(image)
    if image.dtype != np.uint8:
        image = (image * 255).clip(0, 255).astype(np.uint8)
    if len(image.shape) == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    if image.shape[2] == 4:
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l_ch, a_ch, b_ch = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_ch = clahe.apply(l_ch)
    lab = cv2.merge([l_ch, a_ch, b_ch])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


class IjepaEncoder(EncoderPort):
    def __init__(
        self, device: str = "cuda", model_id: str = "facebook/ijepa_vith14_22k"
    ) -> None:
        self._device = device
        device_id = 0 if (device == "cuda" and torch.cuda.is_available()) else -1
        self._pipe = pipeline(
            "image-feature-extraction",
            model=model_id,
            device=device_id,
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
        from PIL import Image as PILImage

        import numpy as np

        pil_images = []
        for img in images:
            if isinstance(img, np.ndarray):
                img = PILImage.fromarray(img)
            pil_images.append(img)

        inputs = self._processor(pil_images, return_tensors="pt", padding=True)
        inputs = {k: v.to(self._device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = self._model(**inputs)
        hidden = outputs.last_hidden_state
        if self._device == "cuda":
            hidden = hidden.float()

        batch_size = hidden.shape[0]
        tokens_all = hidden.reshape(batch_size, -1, hidden.shape[-1])
        pooled_all = tokens_all.mean(dim=1)

        if return_tokens:
            return pooled_all.cpu(), tokens_all.cpu()
        return pooled_all.cpu()
