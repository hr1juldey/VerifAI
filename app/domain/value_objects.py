from __future__ import annotations

import enum

import numpy as np
from numpy.typing import NDArray
from PIL import Image
from pydantic import BaseModel

ProductId = str


class Decision(str, enum.Enum):
    MATCH = "MATCH"
    SUSPECT = "SUSPECT"
    REJECT = "REJECT"


class SuspectReason(str, enum.Enum):
    LIGHTING_ARTIFACT = "LIGHTING_ARTIFACT"
    CONTENT_DIFF = "CONTENT_DIFF"


class MatchScore(BaseModel):
    value: float
    threshold: float = 0.7

    @property
    def is_match(self) -> bool:
        return self.value >= self.threshold


ImageData = Image.Image | NDArray[np.float32]
