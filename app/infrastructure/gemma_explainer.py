from __future__ import annotations

import logging
import re

import dspy
from dspy import Image as DspyImage

from app.application.ports import ExplainerPort

logger = logging.getLogger(__name__)


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
    verdict: str = dspy.OutputField(
        desc="One of: LIGHTING_ARTIFACT or CONTENT_DIFF",
    )
    explanation: str = dspy.OutputField(
        desc="Factual description of red-highlighted regions only. "
        "No preamble. 1-3 sentences.",
    )


class GemmaExplainer(ExplainerPort):
    def __init__(
        self,
        model: str = "ollama_chat/gemma4:e4b",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.3,
        max_retries: int = 3,
    ) -> None:
        lm = dspy.LM(
            model=model,
            api_base=base_url,
            api_key="",
            cache=False,
            temperature=temperature,
            num_retries=max_retries,
        )
        dspy.configure(lm=lm)
        self._predictor = dspy.Predict(ExplainRejection)
        logger.info("DSPy explainer initialized with %s", model)

    async def explain(
        self,
        catalog_image_path: str,
        annotated_return_path: str,
        product_description: str,
    ) -> tuple[str, str]:
        result = self._predictor(
            catalog_image=DspyImage(url=catalog_image_path),
            return_image=DspyImage(url=annotated_return_path),
            product_description=product_description,
        )
        verdict = result.verdict.strip().upper()
        if verdict not in ("LIGHTING_ARTIFACT", "CONTENT_DIFF"):
            verdict = "CONTENT_DIFF"
        return verdict, _clean(result.explanation)


def _clean(text: str) -> str:
    text = text.strip()
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"^(Here is|Based on|The)[^.]*\.\s*", "", text, count=1)
    return text.strip()
