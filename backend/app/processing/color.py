"""Processos da categoria Cor (Etapa 4 — a implementar pelo grupo).

Os corpos das funções são stubs: apenas assinatura, contrato e ``NotImplementedError``.
"""

from __future__ import annotations

import numpy as np

from .types import OutputImage, ProcessResult


def rgb_split(image: np.ndarray, params: dict) -> ProcessResult:
    """Decomposição RGB.

    Separa a imagem colorida em três imagens em escala de cinza, uma por canal
    R, G e B.

    Entrada:
        Somente RGB ``(H, W, 3)``, ``uint8`` — o catálogo aceita apenas o modo
        ``rgb``. Imagens em cinza são recusadas antes de chegar ao handler.

    Parâmetros:
        Nenhum.

    Saídas (todas ``main``, em cinza ``(H, W)``, ``uint8``):
        - ``r`` "Canal R" — intensidade do canal vermelho.
        - ``g`` "Canal G" — intensidade do canal verde.
        - ``b`` "Canal B" — intensidade do canal azul.
        Sem histogramas e sem métricas.

    Dicas teóricas:
        Cada canal é ``image[:, :, 0]``, ``image[:, :, 1]`` e ``image[:, :, 2]``
        (a ordem do Pillow é R, G, B). Não converta para cinza: o objetivo é
        mostrar cada banda separadamente. Referência: Gonzalez & Woods, cap. 6
        (Color Image Processing).
    """
    raise NotImplementedError


def hsv_split(image: np.ndarray, params: dict) -> ProcessResult:
    """Decomposição HSV.

    Converte a imagem RGB para HSV e mostra os canais H, S e V como imagens em
    escala de cinza.

    Entrada:
        Somente RGB ``(H, W, 3)``, ``uint8`` — o catálogo aceita apenas ``rgb``.

    Parâmetros:
        Nenhum.

    Saídas (todas ``main``, em cinza ``(H, W)``, ``uint8``):
        - ``h`` "Canal H" — matiz **escalado para 0–255** (H é um ângulo em
          [0, 360); multiplique por ``255 / 360`` e arredonde).
        - ``s`` "Canal S" — saturação (já em [0, 1] → multiplique por 255).
        - ``v`` "Canal V" — valor/brilho (idem).
        Sem histogramas e sem métricas.

    Dicas teóricas:
        Implemente a conversão RGB→HSV com NumPy puro (não há OpenCV). Calcule
        ``max`` e ``min`` por pixel, ``delta = max - min``; S = delta/max e
        V = max. Para H: se delta == 0, H = 0 (pixel acromático); senão use as
        fórmulas por canal dominante (60° · ...). Cuidado com divisão por zero
        (pixels pretos). Trabalhe em float e só no final converta para ``uint8``
        com ``np.rint``/``astype``. Referência: Gonzalez & Woods, cap. 6.
    """
    raise NotImplementedError
