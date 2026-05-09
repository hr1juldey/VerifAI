from __future__ import annotations

import logging
import re

import dspy
from dspy import Image as DspyImage

from app.application.ports import ExplainerPort

logger = logging.getLogger(__name__)

OLLAMA_MODEL = "ollama_chat/gemma4:e4b"
OLLAMA_BASE = "http://localhost:11434"


class ExplainRejection(dspy.Signature):
    catalog_image: DspyImage = dspy.InputField(
        desc="Original catalog product photo",
    )
    return_image: DspyImage = dspy.InputField(
        desc="Returned item with red overlay on flagged regions",
    )
    product_description: str = dspy.InputField(
        desc="Product name and details for context",
    )
    explanation: str = dspy.OutputField(
        desc="Factual description of red-highlighted regions only. "
        "No preamble. 1-3 sentences.",
    )


class GemmaExplainer(ExplainerPort):
    def __init__(self) -> None:
        lm = dspy.LM(
            model=OLLAMA_MODEL,
            api_base=OLLAMA_BASE,
            api_key="",
            cache=False,
            temperature=0.3,
            num_retries=3,
        )
        dspy.configure(lm=lm)
        self._predictor = dspy.Predict(ExplainRejection)
        logger.info("DSPy explainer initialized with %s", OLLAMA_MODEL)

    async def explain(
        self,
        catalog_image_path: str,
        annotated_return_path: str,
        product_description: str,
    ) -> str:
        result = self._predictor(
            catalog_image=DspyImage(url=catalog_image_path),
            return_image=DspyImage(url=annotated_return_path),
            product_description=product_description,
        )
        raw = result.explanation
        return _clean(raw)


def _clean(text: str) -> str:
    text = text.strip()
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"^(Here is|Based on|The)[^.]*\.\s*", "", text, count=1)
    return text.strip()
