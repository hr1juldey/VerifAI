from __future__ import annotations

import httpx
from fastapi import APIRouter, Request

from app.presentation.schemas import HealthResponse

router = APIRouter(tags=["health"])

OLLAMA_URL = "http://localhost:11434/api/tags"


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request) -> HealthResponse:
    gpu = _check_gpu(request)
    ollama_ok = await _check_ollama()
    return HealthResponse(
        status="ok" if gpu["model_loaded"] else "degraded",
        gpu_available=gpu["gpu_available"],
        model_loaded=gpu["model_loaded"],
        cache_size=gpu["cache_size"],
        ollama_provider="ollama_chat/gemma4:e4b",
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


async def _check_ollama() -> bool:
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(OLLAMA_URL)
            return resp.status_code == 200
    except (httpx.HTTPError, OSError):
        return False
