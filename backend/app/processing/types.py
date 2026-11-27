"""Contrato dos handlers de PDI (Etapa 4 — implementação manual pelo grupo).

Cada processo do catálogo tem uma função em ``processing/*.py`` com a assinatura::

    def nome_do_processo(image: np.ndarray, params: dict) -> ProcessResult: ...

Regras do contrato:

* ``image`` é sempre ``uint8``, C-contíguo, com shape ``(H, W)`` (cinza) ou
  ``(H, W, 3)`` (RGB). É uma **cópia**: o handler pode alterá-la à vontade.
* ``params`` chega **já validado e convertido** (``int``, ``float``, ``bool`` ou
  ``str``), com os defaults do catálogo preenchidos e sem os parâmetros ocultos
  por ``visible_if``.
* O handler é chamado apenas para os modos listados em ``modes`` no catálogo.
* O retorno é um :class:`ProcessResult` com **pelo menos uma saída ``main``**.
  Cálculos internos podem usar ``float``, mas toda imagem devolvida em
  :class:`OutputImage` precisa ser ``uint8`` (``np.clip`` + ``astype`` ou
  normalização) com shape ``(H, W)`` ou ``(H, W, 3)``.
* Histogramas têm sempre 256 contagens inteiras não negativas; métricas têm valor
  escalar (número ou texto) e unidade opcional.

Se a saída violar o contrato, o runner responde ``500 invalid_output`` com uma
mensagem dizendo o que corrigir; exceções inesperadas viram ``500 processing_error``
e ``NotImplementedError`` (o estado atual dos stubs) vira ``501 not_implemented``.

Enquanto o handler lançar ``NotImplementedError``, o processo aparece como
``"implemented": false`` em ``GET /api/processes``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np


@dataclass
class OutputImage:
    """Imagem de saída de um processo (principal ou acessória)."""

    id: str  # ex.: "result", "r", "laplacian"
    label: str  # ex.: "Imagem filtrada"
    data: np.ndarray  # uint8, (H, W) ou (H, W, 3)
    role: Literal["main", "aux"] = "main"


@dataclass
class Histogram:
    """Histograma de 256 posições exibido nos dados acessórios."""

    id: str
    label: str
    values: list[int]  # 256 contagens
    channel: Literal["gray", "r", "g", "b"] = "gray"


@dataclass
class Metric:
    """Métrica escalar exibida junto com as saídas (ex.: PSNR, tempo)."""

    label: str
    value: float | int | str
    unit: str | None = None


@dataclass
class ProcessResult:
    """Resultado completo de um handler."""

    outputs: list[OutputImage]
    histograms: list[Histogram] = field(default_factory=list)
    metrics: list[Metric] = field(default_factory=list)
