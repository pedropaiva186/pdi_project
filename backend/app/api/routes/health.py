"""Rota de verificação de saúde."""

from __future__ import annotations

from fastapi import APIRouter

from ...schemas.responses import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="Verificação de saúde")
def health() -> HealthResponse:
    """Responde ``{"status": "ok"}`` quando o servidor está de pé."""
    return HealthResponse()
