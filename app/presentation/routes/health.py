from __future__ import annotations

import os

import httpx
from fastapi import APIRouter, Request

from app.presentation.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request) -> HealthResponse:
    gpu = _check_gpu(request)
    ollama_base = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_ok = await _check_ollama(ollama_base)
    ollama_model = os.environ.get("OLLAMA_MODEL", "ollama_chat/gemma4:e4b")
    return HealthResponse(
        status="ok" if gpu["model_loaded"] else "degraded",
        gpu_available=gpu["gpu_available"],
        model_loaded=gpu["model_loaded"],
        cache_size=gpu["cache_size"],
        ollama_provider=ollama_model,
        ollama_connected=ollama_ok,
    )


def _check_gpu(request: Request) -> dict:
    import torch

    store = request.app.state.embedding_store
    return {
        "gpu_available": torch.cuda.is_available(),
        "model_loaded": hasattr(request.app.state, "encoder"),
        "cache_size": store.size() if store else 0,
    }


async def _check_ollama(ollama_base: str) -> bool:
    ollama_url = f"{ollama_base}/api/tags"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(ollama_url)
            return resp.status_code == 200
    except (httpx.HTTPError, OSError):
        return False
