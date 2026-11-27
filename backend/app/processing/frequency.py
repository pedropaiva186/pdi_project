"""Processos da categoria Filtros na frequência (Etapa 4 — a implementar pelo grupo).

Os corpos das funções são stubs: apenas assinatura, contrato e ``NotImplementedError``.
"""

from __future__ import annotations

import numpy as np

from .types import OutputImage, ProcessResult


def gaussian_frequency_filter(image: np.ndarray, params: dict) -> ProcessResult:
    """Filtro gaussiano na frequência.

    Passa-baixa ``H = exp(-D² / (2·D₀²))``; passa-alta ``1 - H``. A filtragem é
    feita no domínio da frequência (DFT).

    Entrada:
        Cinza ``(H, W)`` e RGB ``(H, W, 3)``, ``uint8``. Em RGB, aplique por canal.

    Parâmetros:
        - ``filter_type`` (select: ``"lowpass"`` | ``"highpass"``, default
          ``"lowpass"``): tipo de filtro.
        - ``cutoff`` (float, 1–500, default 30): frequência de corte ``D₀``,
          medida em pixels do espectro a partir do centro.

    Saídas:
        - ``result`` "Imagem filtrada" — ``main``, ``uint8``, mesmo shape.
        Sem histogramas e sem métricas.

    Dicas teóricas:
        ``F = np.fft.fft2(f)``; centralize com ``np.fft.fftshift`` (ou multiplique
        ``f`` por ``(-1)^(x+y)`` antes); monte ``D(u, v)`` como a distância de cada
        ponto ao centro; aplique ``F * H``; volte com ``ifft2``/``ifftshift`` e
        pegue a parte real. A saída é ``float`` (pode ter ringing/valores fora de
        [0, 255]): normalize ou sature para ``uint8`` e documente. Referência:
        Gonzalez & Woods, cap. 4 (Filtering in the Frequency Domain).
    """
    raise NotImplementedError


def butterworth_filter(image: np.ndarray, params: dict) -> ProcessResult:
    """Filtro de Butterworth na frequência.

    Passa-baixa ``H = 1 / (1 + (D/D₀)^(2n))``; passa-alta
    ``H = 1 / (1 + (D₀/D)^(2n))``.

    Entrada:
        Cinza ``(H, W)`` e RGB ``(H, W, 3)``, ``uint8``. Em RGB, por canal.

    Parâmetros:
        - ``filter_type`` (select: ``"lowpass"`` | ``"highpass"``, default
          ``"lowpass"``).
        - ``cutoff`` (float, 1–500, default 30): ``D₀`` em pixels do espectro.
        - ``order`` (int, 1–10, default 2): ordem ``n``; quanto maior, mais
          abrupta a transição.

    Saídas:
        - ``result`` "Imagem filtrada" — ``main``, ``uint8``, mesmo shape.
        Sem histogramas e sem métricas.

    Dicas teóricas:
        Mesmo pipeline de DFT do filtro gaussiano. No passa-alta, trate ``D = 0``
        (o centro do espectro) para não dividir por zero — normalmente
        ``H(0, 0) = 0`` no passa-alta (ou 1 para preservar a média; documente).
        ``n`` alto aproxima o filtro ideal (cuidado com ringing). Normalize a
        saída para ``uint8``. Referência: Gonzalez & Woods, cap. 4.
    """
    raise NotImplementedError
