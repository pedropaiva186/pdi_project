"""Rota do catálogo de processos."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from ...core.catalog import Catalog
from ..deps import get_catalog, get_implemented

router = APIRouter()


@router.get("/processes", summary="Catálogo de processos e categorias")
def list_processes(
    catalog: Catalog = Depends(get_catalog),
    implemented: dict[str, bool] = Depends(get_implemented),
) -> dict[str, Any]:
    """Devolve o ``processes.json`` original com ``implemented`` em cada processo."""
    return catalog.to_public(implemented)
