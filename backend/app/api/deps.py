"""Dependências do FastAPI: acesso ao estado carregado no ``lifespan``."""

from __future__ import annotations

from fastapi import Request

from ..core.catalog import Catalog
from ..processing.registry import Handler


def get_catalog(request: Request) -> Catalog:
    """Catálogo validado (``app.state.catalog``)."""
    return request.app.state.catalog


def get_handlers(request: Request) -> dict[str, Handler]:
    """Registro de handlers ativo (``app.state.handlers``)."""
    return request.app.state.handlers


def get_implemented(request: Request) -> dict[str, bool]:
    """Mapa de processos implementados (``app.state.implemented``)."""
    return request.app.state.implemented
