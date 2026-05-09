from __future__ import annotations

import asyncio

from fastapi import APIRouter, File, Form, Request, UploadFile
from PIL import Image

from app.presentation.schemas import ErrorResponse, VerifyResponse

router = APIRouter(tags=["verify"])

_semaphore = asyncio.Semaphore(2)


@router.post(
    "/verify",
    response_model=VerifyResponse,
    responses={404: {"model": ErrorResponse}},
)
async def verify_return(
    request: Request,
    product_id: str = Form(...),
    image: UploadFile = File(...),
) -> VerifyResponse | ErrorResponse:
    pil_image = Image.open(image.file).convert("RGB")
    use_case = request.app.state.verify_return_use_case
    store = request.app.state.embedding_store

    catalog_emb = store.get(product_id)
    if catalog_emb is None:
        return ErrorResponse(
            error="not_found",
            detail=f"Product {product_id} not registered in catalog",
        )

    catalog_image = request.app.state.catalog_images.get(product_id)
    async with _semaphore:
        result = await use_case.execute(product_id, pil_image, catalog_image)

    return VerifyResponse(**result.model_dump())
