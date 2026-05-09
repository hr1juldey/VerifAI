from __future__ import annotations

from fastapi import APIRouter, File, Form, Request, UploadFile
from PIL import Image

from app.presentation.schemas import CatalogResponse, ErrorResponse

router = APIRouter(tags=["catalog"])


@router.post(
    "/catalog",
    response_model=CatalogResponse,
    responses={201: {"model": CatalogResponse}},
    status_code=201,
)
async def catalog_product(
    request: Request,
    product_id: str = Form(...),
    image: UploadFile = File(...),
) -> CatalogResponse | ErrorResponse:
    pil_image = Image.open(image.file).convert("RGB")
    use_case = request.app.state.ingest_catalog_use_case
    result = await use_case.execute(product_id, pil_image)
    request.app.state.catalog_images[product_id] = pil_image
    return CatalogResponse(**result)
