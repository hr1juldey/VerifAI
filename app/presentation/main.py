from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.infrastructure.embedding_store import EmbeddingStore
from app.infrastructure.gemma_explainer import GemmaExplainer
from app.infrastructure.ijepa_encoder import IjepaEncoder
from app.infrastructure.spatial_diff import SpatialDiff
from app.application.use_cases.ingest_catalog import IngestCatalogUseCase
from app.application.use_cases.verify_return import VerifyReturnUseCase
from app.presentation.routes import catalog, health, verify

load_dotenv()

logger = logging.getLogger(__name__)

THRESHOLD_ENV = "VERIFICATION_THRESHOLD"
DEFAULT_THRESHOLD = 0.7


@asynccontextmanager
async def lifespan(app: FastAPI):
    device = "cuda" if _cuda_available() else "cpu"
    model_id = os.environ.get("IJEPA_MODEL_ID", "facebook/ijepa_vith14_22k")
    encoder = IjepaEncoder(device=device, model_id=model_id)
    store = EmbeddingStore(
        persist_path=os.environ.get("EMBEDDINGS_PATH", "data/embeddings.pt"),
    )
    store.load()
    spatial = SpatialDiff(
        alpha=float(os.environ.get("SPATIAL_ALPHA", "0.4")),
        diff_threshold=float(os.environ.get("SPATIAL_DIFF_THRESHOLD", "0.5")),
    )
    explainer = GemmaExplainer(
        model=os.environ.get("OLLAMA_MODEL", "ollama_chat/gemma4:e4b"),
        base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=float(os.environ.get("OLLAMA_TEMPERATURE", "0.3")),
        max_retries=int(os.environ.get("OLLAMA_RETRIES", "3")),
    )
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
    cors_origins = os.environ.get("CORS_ORIGINS", "*").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(catalog.router)
    app.include_router(verify.router)
    return app


app = create_app()
