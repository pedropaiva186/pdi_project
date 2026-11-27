"""Detecção automática de quais processos já foram implementados.

Um processo é considerado implementado quando o handler **não** lança
``NotImplementedError`` ao ser chamado com uma imagem 8×8 de zeros e os
parâmetros default do catálogo. Qualquer outro resultado ou exceção marca o
processo como implementado (a exceção é registrada no log para depuração).
"""

from __future__ import annotations

import logging

import numpy as np

from ..config import DETECTION_IMAGE_SIZE
from ..core.catalog import Catalog
from ..core.validation import parse_params
from ..processing.registry import Handler

logger = logging.getLogger(__name__)


def check_handler_parity(catalog: Catalog, handlers: dict[str, Handler]) -> None:
    """Garante que catálogo e registro têm exatamente os mesmos ids de processo."""
    catalog_ids = set(catalog.processes)
    handler_ids = set(handlers)
    if catalog_ids == handler_ids:
        return
    missing = sorted(catalog_ids - handler_ids)
    extra = sorted(handler_ids - catalog_ids)
    parts = []
    if missing:
        parts.append(f"missing handlers for: {', '.join(missing)}")
    if extra:
        parts.append(f"handlers without catalog entry: {', '.join(extra)}")
    raise RuntimeError("catalog/handler mismatch — " + "; ".join(parts))


def detect_implemented(catalog: Catalog, handlers: dict[str, Handler]) -> dict[str, bool]:
    """Testa cada handler e devolve ``{process_id: implemented}``."""
    implemented: dict[str, bool] = {}
    size = DETECTION_IMAGE_SIZE
    for process_id, process in catalog.processes.items():
        handler = handlers[process_id]
        shape = (size, size) if process.modes[0] == "gray" else (size, size, 3)
        image = np.zeros(shape, dtype=np.uint8)
        params = parse_params(process, None)
        try:
            handler(image, params)
        except NotImplementedError:
            implemented[process_id] = False
        except Exception:  # noqa: BLE001 - qualquer falha indica handler "vivo"
            logger.warning(
                "detection: handler %s raised an exception; marking as implemented",
                process_id,
                exc_info=True,
            )
            implemented[process_id] = True
        else:
            implemented[process_id] = True
    return implemented
