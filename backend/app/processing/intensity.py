"""Processos da categoria Intensidade (Etapa 4 — a implementar pelo grupo).

Os corpos das funções são stubs: apenas assinatura, contrato e ``NotImplementedError``.
"""

from __future__ import annotations

import numpy as np

from .types import Histogram, OutputImage, ProcessResult


def threshold(image: np.ndarray, params: dict) -> ProcessResult:
    """Limiarização.

    Binariza a imagem: pixels com intensidade acima do limiar ``k`` viram branco
    (255) e os demais, preto (0).

    Entrada:
        Cinza ``(H, W)`` e RGB ``(H, W, 3)``, ``uint8``. Em RGB, a forma de
        aplicar (por canal ou sobre uma conversão para cinza) é decisão do grupo;
        mantenha o shape da entrada na saída.

    Parâmetros:
        - ``k`` (int, 0–255, default 128): limiar. A comparação é
          ``pixel > k`` (estritamente maior), conforme a descrição do catálogo.

    Saídas:
        - ``result`` "Imagem limiarizada" — ``main``, ``uint8``, mesmo shape da
          entrada, com valores apenas 0 e 255.
        Sem histogramas e sem métricas.

    Dicas teóricas:
        Transformação de intensidade pontual, sem vizinhança: basta comparar o
        array. Em RGB, se optar por canal, aplique o mesmo ``k`` a cada banda.
        Referência: Gonzalez & Woods, cap. 3 (Intensity Transformations).
    """
    raise NotImplementedError


def log_transform(image: np.ndarray, params: dict) -> ProcessResult:
    """Transformação logarítmica.

    Aplica ``s = c · log(1 + r)``, expandindo os tons escuros e comprimindo os
    claros.

    Entrada:
        Cinza ``(H, W)`` e RGB ``(H, W, 3)``, ``uint8``. Em RGB, aplique por canal
        (decisão do grupo), mantendo o shape.

    Parâmetros:
        - ``c`` (float, 0.01–100, default 45.99): ganho. Com ``r`` em [0, 255],
          ``c = 255 / ln(256) ≈ 45.99`` faz a saída ocupar exatamente [0, 255].

    Saídas:
        - ``result`` "Transformação logarítmica" — ``main``, ``uint8``.
        Sem histogramas e sem métricas.

    Dicas teóricas:
        Use logaritmo natural (``np.log(1 + r)``) sobre ``float``. Para voltar a
        ``uint8``, **sature** com ``np.clip(..., 0, 255)`` e ``astype`` (não
        normalize, senão ``c`` deixa de ter o efeito descrito). Referência:
        Gonzalez & Woods, cap. 3.
    """
    raise NotImplementedError


def power_transform(image: np.ndarray, params: dict) -> ProcessResult:
    """Transformação de potência (gama).

    Aplica ``s = c · r^γ``, com ``r`` normalizado em [0, 1].

    Entrada:
        Cinza ``(H, W)`` e RGB ``(H, W, 3)``, ``uint8``.

    Parâmetros:
        - ``c`` (float, 0.01–10, default 1.0): ganho multiplicativo.
        - ``gamma`` (float, 0.01–10, default 1.0): expoente. γ < 1 clareia;
          γ > 1 escurece.

    Saídas:
        - ``result`` "Transformação de potência" — ``main``, ``uint8``.
        Sem histogramas e sem métricas.

    Dicas teóricas:
        Normalize ``r / 255``, aplique ``c * r ** gamma``, volte a multiplicar por
        255 e sature para ``uint8``. Evite ``inf``/``nan`` (γ positivo e r ≥ 0 já
        garantem valores finitos). Em RGB, por canal. Referência: Gonzalez &
        Woods, cap. 3.
    """
    raise NotImplementedError


def histogram_equalization(image: np.ndarray, params: dict) -> ProcessResult:
    """Equalização de histograma.

    Redistribui as intensidades usando a CDF e devolve os histogramas antes e
    depois da equalização.

    Entrada:
        Somente cinza ``(H, W)``, ``uint8`` — o catálogo aceita apenas o modo
        ``gray`` (equalizar imagens coloridas não é um processo relevante, como
        pede o PDF). Imagens RGB são recusadas com ``422 unsupported_mode``.

    Parâmetros:
        Nenhum.

    Saídas:
        - ``equalized`` "Imagem equalizada" — ``main``, cinza, ``uint8``.
        - Histograma ``before`` "Histograma original", channel ``gray``, 256
          contagens inteiras da imagem de entrada.
        - Histograma ``after`` "Histograma equalizado", channel ``gray``, 256
          contagens inteiras da imagem de saída.

    Dicas teóricas:
        ``h = np.bincount(image.ravel(), minlength=256)``; CDF cumulativa;
        mapeie ``s = round(255 * cdf[r] / total)`` (ou ``(L-1) * cdf / (M·N)``).
        Trate o caso de imagem constante para não dividir por zero. Os
        histogramas são **contagens**, não probabilidades, e devem vir na ordem
        ``before``, ``after``. Referência: Gonzalez & Woods, cap. 3.
    """
    raise NotImplementedError


def intensity_slicing(image: np.ndarray, params: dict) -> ProcessResult:
    """Fatiamento por intensidade.

    Destaca com o valor fixo 255 os pixels cuja intensidade está na faixa
    [A, B]; o fundo pode ser preservado ou zerado.

    Entrada:
        Cinza ``(H, W)`` e RGB ``(H, W, 3)``, ``uint8``. Em RGB, aplique a mesma
        máscara a todos os canais (ou o critério que o grupo documentar).

    Parâmetros:
        - ``a`` (int, 0–255, default 100): início da faixa (inclusivo).
        - ``b`` (int, 0–255, default 180): fim da faixa (inclusivo). O backend
          garante ``a <= b`` pela constraint ``less_equal``.
        - ``preserve_background`` (bool, default ``true``): ligado, os pixels
          fora de [A, B] ficam como estão; desligado, vão para 0.

    Saídas:
        - ``result`` "Imagem fatiada" — ``main``, ``uint8``. O valor de destaque é
          **fixo em 255** (não é um parâmetro do catálogo).

    Dicas teóricas:
        Monte a máscara ``(image >= a) & (image <= b)`` e use ``np.where``. Não
        confunda com limiarização: aqui a faixa é fechada nos dois extremos.
        Referência: Gonzalez & Woods, cap. 3.
    """
    raise NotImplementedError
