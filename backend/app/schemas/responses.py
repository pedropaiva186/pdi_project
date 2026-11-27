"""Modelos Pydantic que documentam as respostas da API no OpenAPI."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Resposta de ``GET /api/health``."""

    status: Literal["ok"] = "ok"


class InspectResponse(BaseModel):
    """Resposta de ``POST /api/images/inspect``."""

    mode: Literal["gray", "rgb"]
    width: int
    height: int
    source_mode: str
    filename: str | None = None


class OutputImageOut(BaseModel):
    """Uma imagem de saída (principal ou acessória)."""

    id: str
    label: str
    role: Literal["main", "aux"]
    mode: Literal["gray", "rgb"]
    width: int
    height: int
    image: str = Field(description="PNG em data URL (base64)")


class HistogramOut(BaseModel):
    """Histograma de 256 contagens."""

    id: str
    label: str
    channel: Literal["gray", "r", "g", "b"]
    values: list[int]


class MetricOut(BaseModel):
    """Métrica escalar exibida junto com as saídas."""

    label: str
    value: float | int | str
    unit: str | None = None


class ProcessInputOut(BaseModel):
    """Resumo da imagem de entrada."""

    mode: Literal["gray", "rgb"]
    width: int
    height: int


class ProcessResponse(BaseModel):
    """Resposta de ``POST /api/process/{process_id}``."""

    process_id: str
    params: dict[str, int | float | bool | str]
    input: ProcessInputOut
    outputs: list[OutputImageOut]
    histograms: list[HistogramOut]
    metrics: list[MetricOut]
    elapsed_ms: float


class ErrorBody(BaseModel):
    """Corpo do erro no formato único da API."""

    code: str
    message: str
    details: dict[str, Any]


class ErrorResponse(BaseModel):
    """Envelope de erro: ``{"error": {...}}``."""

    error: ErrorBody
