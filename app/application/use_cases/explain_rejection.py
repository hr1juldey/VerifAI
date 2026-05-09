from __future__ import annotations

import re

from app.application.ports import ExplainerPort


class ExplainRejectionUseCase:
    def __init__(self, explainer: ExplainerPort) -> None:
        self._explainer = explainer

    async def execute(
        self,
        catalog_image_path: str,
        annotated_return_path: str,
        product_description: str,
    ) -> tuple[str, str]:
        try:
            verdict, raw = await self._explainer.explain(
                catalog_image_path,
                annotated_return_path,
                product_description,
            )
        except Exception:
            return "CONTENT_DIFF", "Explanation unavailable (Ollama timeout)"
        return verdict, _clean_explanation(raw)


def _clean_explanation(text: str) -> str:
    text = text.strip()
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"^(Here is|Based on|The)[^.]*\.\s*", "", text, count=1)
    return text.strip()
