"""Rota de execução de processos (``POST /api/process/{process_id}``)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, File, Form, UploadFile

from ...core.catalog import Catalog
from ...core.errors import AppError
from ...processing.registry import Handler
from ...schemas.responses import ErrorResponse, ProcessResponse
from ...services.runner import log_request, run_process
from ...services.uploads import read_upload
from ..deps import get_catalog, get_handlers

router = APIRouter()

ERROR_RESPONSES = {
    400: {"model": ErrorResponse, "description": "PNG ausente, corrompido ou não suportado"},
    404: {"model": ErrorResponse, "description": "Processo inexistente"},
    413: {"model": ErrorResponse, "description": "Arquivo acima do limite de tamanho"},
    422: {"model": ErrorResponse, "description": "Parâmetros ou modo inválidos"},
    500: {"model": ErrorResponse, "description": "Saída inválida ou falha no handler"},
    501: {"model": ErrorResponse, "description": "Processo ainda não implementado"},
}


@router.post(
    "/process/{process_id}",
    response_model=ProcessResponse,
    response_model_exclude_none=True,
    responses=ERROR_RESPONSES,
    summary="Executa um processo sobre o PNG enviado",
)
def process_image(
    process_id: str,
    file: UploadFile | None = File(None),
    params: str | None = Form(None),
    catalog: Catalog = Depends(get_catalog),
    handlers: dict[str, Handler] = Depends(get_handlers),
) -> dict[str, Any]:
    """Valida entrada/modo/parâmetros, chama o handler e serializa o resultado."""
    try:
        # Processo inexistente tem prioridade (404) sobre a validação do arquivo.
        catalog.get(process_id)
        data = read_upload(file)
    except AppError as exc:
        # Erros anteriores ao runner (arquivo ausente/grande) também entram no log.
        log_request(process_id, "?", 0, 0, 0.0, exc.status)
        raise
    return run_process(catalog, handlers, process_id, data, params)
