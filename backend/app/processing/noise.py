"""Processos da categoria Ruído (Etapa 4 — a implementar pelo grupo).

Os corpos das funções são stubs: apenas assinatura, contrato e ``NotImplementedError``.
"""

from __future__ import annotations

import numpy as np

from .types import OutputImage, ProcessResult

#: Densidade fixa usada quando o ruído é só sal **ou** só pimenta (o catálogo só
#: expõe ``salt_probability``/``pepper_probability`` para o tipo "salt_and_pepper").
SINGLE_NOISE_PROBABILITY = 0.05


def gaussian_noise(image: np.ndarray, params: dict) -> ProcessResult:
    """Ruído gaussiano aditivo.

    Soma a cada pixel uma amostra de ruído gaussiano, com saturação em [0, 255].

    Entrada:
        Cinza ``(H, W)`` e RGB ``(H, W, 3)``, ``uint8``.

    Parâmetros:
        - ``intensity`` (float, 0–100, default 20): desvio padrão σ do ruído.
        - ``distribution`` (float, −100–100, default 0): média μ do ruído.

    Saídas:
        - ``result`` "Imagem com ruído gaussiano" — ``main``, ``uint8``, mesmo
          shape.
        Sem histogramas e sem métricas.

    Dicas teóricas:
        Use ``rng = np.random.default_rng()`` (não o gerador global) e
        ``rng.normal(mu, sigma, image.shape)``. Some em ``float`` e sature com
        ``np.clip``. Em RGB, o ruído pode ser gerado com o shape completo (ruído
        independente por canal) ou um valor por pixel (ruído correlacionado) —
        decida e documente. ``σ = 0`` devolve a entrada. Referência: Gonzalez &
        Woods, cap. 5 (Image Restoration).
    """
    raise NotImplementedError


def salt_pepper_noise(image: np.ndarray, params: dict) -> ProcessResult:
    """Ruído sal / pimenta.

    Troca pixels por 255 (sal) e/ou 0 (pimenta).

    Entrada:
        Cinza ``(H, W)`` e RGB ``(H, W, 3)``, ``uint8``.

    Parâmetros:
        - ``noise_type`` (select: ``"salt"`` | ``"pepper"`` |
          ``"salt_and_pepper"``, default ``"salt_and_pepper"``): tipo de ruído.
        - ``salt_probability`` (float, 0–0.5, default 0.025): probabilidade de
          sal. **Só chega ao handler quando** ``noise_type == "salt_and_pepper"``
          (``visible_if`` no catálogo); nos outros tipos a chave não existe em
          ``params``.
        - ``pepper_probability`` (float, 0–0.5, default 0.025): idem para
          pimenta.
        - Quando o tipo é só sal ou só pimenta, use a densidade fixa
          ``SINGLE_NOISE_PROBABILITY = 0.05`` (constante deste módulo), pois o
          catálogo não expõe probabilidade nesses casos.

    Saídas:
        - ``result`` "Imagem com ruído" — ``main``, ``uint8``, mesmo shape.
        Sem histogramas e sem métricas.

    Dicas teóricas:
        Sorteie máscaras booleanas com ``rng.random(shape) < p`` e aplique 255/0.
        Em RGB, decida entre trocar o pixel inteiro (três canais) ou canal a
        canal e documente. Garanta que sal e pimenta não disputem o mesmo pixel
        (máscaras disjuntas). Referência: Gonzalez & Woods, cap. 5.
    """
    raise NotImplementedError
