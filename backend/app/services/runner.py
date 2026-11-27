"""Orquestração de ``POST /api/process/{process_id}``.

Fluxo obrigatório: catálogo → decode → modo → params → handler → validação da
saída → serialização. Cada etapa falha com o ``AppError`` correspondente do
contrato (``API.md``) e toda requisição gera uma linha de log.
"""

from __future__ import annotations

import logging
import math
from time import perf_counter
from typing import Any

import numpy as np

from ..core.catalog import Catalog, ProcessSpec
from ..core.errors import (
    AppError,
    invalid_output,
    not_implemented,
    processing_error,
    unsupported_mode,
)
from ..core.validation import parse_params
from ..processing.registry import Handler
from ..processing.types import Metric, ProcessResult
from .image_io import DecodedImage, decode_png, encode_png_data_url, mode_of

logger = logging.getLogger(__name__)

VALID_ROLES = ("main", "aux")
VALID_CHANNELS = ("gray", "r", "g", "b")
TIMING_METRIC_LABEL = "Tempo de processamento"


def log_request(
    process_id: str,
    mode: str,
    width: int,
    height: int,
    elapsed_ms: float,
    status: int,
) -> None:
    """Registra uma linha por requisição do endpoint de processamento."""
    logger.info(
        "process id=%s mode=%s size=%dx%d elapsed_ms=%.2f status=%d",
        process_id,
        mode,
        width,
        height,
        elapsed_ms,
        status,
    )


def _validate_histograms(result: ProcessResult) -> None:
    for histogram in result.histograms:
        if histogram.channel not in VALID_CHANNELS:
            raise invalid_output(
                f"O histograma '{histogram.id}' tem channel '{histogram.channel}'; "
                "use 'gray', 'r', 'g' ou 'b'."
            )
        try:
            length = len(histogram.values)
        except TypeError:
            raise invalid_output(
                f"O histograma '{histogram.id}' deve ter uma lista com 256 valores."
            ) from None
        if length != 256:
            raise invalid_output(
                f"O histograma '{histogram.id}' deve ter exatamente 256 valores "
                f"(recebeu {length})."
            )
        for position, value in enumerate(histogram.values):
            if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
                raise invalid_output(
                    f"O histograma '{histogram.id}' tem um valor não inteiro na posição "
                    f"{position}; use inteiros."
                )
            if value < 0:
                raise invalid_output(
                    f"O histograma '{histogram.id}' tem um valor negativo na posição "
                    f"{position}; use inteiros não negativos."
                )


def _validate_metrics(result: ProcessResult) -> None:
    for metric in result.metrics:
        value = metric.value
        if isinstance(value, np.generic):
            value = value.item()
        if isinstance(value, float) and not math.isfinite(value):
            raise invalid_output(
                f"A métrica '{metric.label}' tem valor não finito; use um número finito."
            )
        if not isinstance(value, (int, float, str)):
            raise invalid_output(
                f"A métrica '{metric.label}' tem valor do tipo "
                f"{type(metric.value).__name__}; use número ou texto."
            )


def validate_result(result: Any) -> ProcessResult:
    """Valida a saída do handler contra o contrato de ``types.py``."""
    if not isinstance(result, ProcessResult):
        raise invalid_output("O handler deve retornar um ProcessResult.")
    if not result.outputs:
        raise invalid_output(
            "O handler deve retornar ao menos uma saída (outputs está vazio)."
        )

    seen_ids: set[str] = set()
    main_count = 0
    for output in result.outputs:
        if output.role not in VALID_ROLES:
            raise invalid_output(
                f"A saída '{output.id}' tem role '{output.role}'; use 'main' ou 'aux'."
            )
        if output.id in seen_ids:
            raise invalid_output(
                f"A saída '{output.id}' está duplicada; use ids únicos por processo."
            )
        seen_ids.add(output.id)
        if output.role == "main":
            main_count += 1

        data = output.data
        if not isinstance(data, np.ndarray):
            raise invalid_output(f"A saída '{output.id}' deve ser um numpy.ndarray.")
        if data.dtype != np.uint8:
            raise invalid_output(
                f"A saída '{output.id}' tem dtype {data.dtype}; converta para uint8 "
                "(np.clip + astype ou normalização)."
            )
        if data.ndim == 3 and data.shape[2] != 3:
            raise invalid_output(
                f"A saída '{output.id}' tem shape {data.shape}; "
                "esperado (H, W) ou (H, W, 3)."
            )
        if data.ndim not in (2, 3):
            raise invalid_output(
                f"A saída '{output.id}' tem shape {data.shape}; "
                "esperado (H, W) ou (H, W, 3)."
            )

    if main_count == 0:
        raise invalid_output(
            "O handler deve retornar ao menos uma saída com role 'main'."
        )

    _validate_histograms(result)
    _validate_metrics(result)
    return result


def _metric_to_dict(metric: Metric) -> dict[str, Any]:
    value = metric.value.item() if isinstance(metric.value, np.generic) else metric.value
    payload: dict[str, Any] = {"label": metric.label, "value": value}
    if metric.unit is not None:
        payload["unit"] = metric.unit
    return payload


def _build_response(
    process: ProcessSpec,
    image: DecodedImage,
    params: dict[str, Any],
    result: ProcessResult,
    elapsed_ms: float,
) -> dict[str, Any]:
    ordered = [output for output in result.outputs if output.role == "main"]
    ordered += [output for output in result.outputs if output.role == "aux"]

    outputs = [
        {
            "id": output.id,
            "label": output.label,
            "role": output.role,
            "mode": mode_of(output.data),
            "width": int(output.data.shape[1]),
            "height": int(output.data.shape[0]),
            "image": encode_png_data_url(output.data),
        }
        for output in ordered
    ]

    histograms = [
        {
            "id": histogram.id,
            "label": histogram.label,
            "channel": histogram.channel,
            "values": [int(value) for value in histogram.values],
        }
        for histogram in result.histograms
    ]

    metrics = [_metric_to_dict(metric) for metric in result.metrics]
    metrics.append(
        {"label": TIMING_METRIC_LABEL, "value": elapsed_ms, "unit": "ms"}
    )

    return {
        "process_id": process.id,
        "params": params,
        "input": {
            "mode": image.mode,
            "width": image.width,
            "height": image.height,
        },
        "outputs": outputs,
        "histograms": histograms,
        "metrics": metrics,
        "elapsed_ms": elapsed_ms,
    }


def run_process(
    catalog: Catalog,
    handlers: dict[str, Handler],
    process_id: str,
    file_bytes: bytes,
    params_raw: str | None,
) -> dict[str, Any]:
    """Executa um processo e devolve o payload no formato de ``API.md``."""
    mode = "?"
    width = height = 0
    elapsed_ms = 0.0
    status = 500

    try:
        process = catalog.get(process_id)
        image = decode_png(file_bytes)
        mode, width, height = image.mode, image.width, image.height

        if image.mode not in process.modes:
            raise unsupported_mode(process.label, image.mode, process.modes)

        params = parse_params(process, params_raw)

        started = perf_counter()
        try:
            result = handlers[process_id](image.array.copy(), dict(params))
        except NotImplementedError:
            raise not_implemented(process.label) from None
        except Exception as exc:
            logger.exception("handler failed: process id=%s", process_id)
            raise processing_error(exc) from exc
        elapsed_ms = round((perf_counter() - started) * 1000, 2)

        validate_result(result)
        payload = _build_response(process, image, params, result, elapsed_ms)
        status = 200
        return payload
    except AppError as exc:
        status = exc.status
        raise
    finally:
        log_request(process_id, mode, width, height, elapsed_ms, status)
