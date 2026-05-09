from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.infrastructure.embedding_store import EmbeddingStore
from app.infrastructure.gemma_explainer import GemmaExplainer
from app.infrastructure.ijepa_encoder import IjepaEncoder
from app.infrastructure.spatial_diff import SpatialDiff
from app.application.use_cases.ingest_catalog import IngestCatalogUseCase
from app.application.use_cases.verify_return import VerifyReturnUseCase
from app.presentation.routes import catalog, health, verify

logger = logging.getLogger(__name__)

THRESHOLD_ENV = "VERIFICATION_THRESHOLD"
DEFAULT_THRESHOLD = 0.7


@asynccontextmanager
async def lifespan(app: FastAPI):
    device = "cuda" if _cuda_available() else "cpu"
    encoder = IjepaEncoder(device=device)
    store = EmbeddingStore()
    store.load()
    spatial = SpatialDiff()
    explainer = GemmaExplainer()
    threshold = float(os.environ.get(THRESHOLD_ENV, DEFAULT_THRESHOLD))

    ingest = IngestCatalogUseCase(encoder, store)
    verify_uc = VerifyReturnUseCase(encoder, store, spatial, explainer, threshold)

    app.state.encoder = encoder
    app.state.embedding_store = store
    app.state.catalog_images = {}
    app.state.ingest_catalog_use_case = ingest
    app.state.verify_return_use_case = verify_uc
    logger.info("VerifAI ready (device=%s, threshold=%.2f)", device, threshold)
    yield


def _cuda_available() -> bool:
    import torch

    return torch.cuda.is_available()


def create_app() -> FastAPI:
    app = FastAPI(
        title="VerifAI",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(catalog.router)
    app.include_router(verify.router)
    return app


app = create_app()
