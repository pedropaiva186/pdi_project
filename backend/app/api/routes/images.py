"""Rota de inspeção de imagens (``POST /api/images/inspect``)."""

from __future__ import annotations

from fastapi import APIRouter, File, UploadFile

from ...schemas.responses import ErrorResponse, InspectResponse
from ...services.image_io import decode_png
from ...services.uploads import read_upload

router = APIRouter()

ERROR_RESPONSES = {
    400: {"model": ErrorResponse, "description": "PNG ausente, corrompido ou não suportado"},
    413: {"model": ErrorResponse, "description": "Arquivo acima do limite de tamanho"},
}


@router.post(
    "/images/inspect",
    response_model=InspectResponse,
    responses=ERROR_RESPONSES,
    summary="Inspeciona um PNG (modo e dimensões)",
)
def inspect_image(file: UploadFile | None = File(None)) -> InspectResponse:
    """Decodifica o PNG e informa o modo normalizado (cinza/RGB) e as dimensões."""
    data = read_upload(file)
    image = decode_png(data)
    return InspectResponse(
        mode=image.mode,
        width=image.width,
        height=image.height,
        source_mode=image.source_mode,
        filename=file.filename if file is not None else None,
    )
