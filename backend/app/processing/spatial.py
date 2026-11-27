"""Processos da categoria Filtros espaciais (Etapa 4 — a implementar pelo grupo).

Os corpos das funções são stubs: apenas assinatura, contrato e ``NotImplementedError``.
"""

from __future__ import annotations

import numpy as np

from .types import OutputImage, ProcessResult


def gaussian_blur(image: np.ndarray, params: dict) -> ProcessResult:
    """Filtro de média gaussiana.

    Suaviza a imagem por convolução com um kernel gaussiano.

    Entrada:
        Cinza ``(H, W)`` e RGB ``(H, W, 3)``, ``uint8``. Em RGB, aplique por canal.

    Parâmetros:
        - ``kernel_size`` (int **ímpar**, 3–31, default 5): tamanho da janela.
        - ``sigma`` (float, 0.1–20, default 1.0): desvio padrão do kernel.

    Saídas:
        - ``result`` "Imagem suavizada" — ``main``, ``uint8``, mesmo shape.
        Sem histogramas e sem métricas.

    Dicas teóricas:
        Kernel 2D separável: ``G(x, y) = exp(-(x² + y²) / (2σ²))``, normalizado
        para soma 1. Faça padding (refletir ou replicar) para manter o tamanho.
        Prefira duas passadas 1D (linha/coluna) por eficiência. Arredonde e
        sature ao voltar para ``uint8``. Não use OpenCV/scikit-image/SciPy.
        Referência: Gonzalez & Woods, cap. 3.
    """
    raise NotImplementedError


def median_filter(image: np.ndarray, params: dict) -> ProcessResult:
    """Filtro de mediana.

    Troca cada pixel pela mediana da vizinhança; funciona bem contra ruído sal e
    pimenta.

    Entrada:
        Cinza ``(H, W)`` e RGB ``(H, W, 3)``, ``uint8``. Em RGB, mediana por canal.

    Parâmetros:
        - ``kernel_size`` (int **ímpar**, 3–31, default 3): tamanho da janela.

    Saídas:
        - ``result`` "Filtro de mediana" — ``main``, ``uint8``, mesmo shape.
        Sem histogramas e sem métricas.

    Dicas teóricas:
        Use ``np.lib.stride_tricks.sliding_window_view`` para extrair as janelas e
        calcule a mediana (``np.median`` ou ``np.partition``) no eixo da janela;
        padding de borda para manter o shape. Custo O(H·W·k²) — aceitável para
        4096×4096? Meça. Referência: Gonzalez & Woods, cap. 5 (order-statistics
        filters).
    """
    raise NotImplementedError


def min_filter(image: np.ndarray, params: dict) -> ProcessResult:
    """Filtro de mínimo (erosão).

    Troca cada pixel pelo mínimo da vizinhança; remove ruído do tipo sal.

    Entrada:
        Cinza ``(H, W)`` e RGB ``(H, W, 3)``, ``uint8``. Em RGB, por canal.

    Parâmetros:
        - ``kernel_size`` (int **ímpar**, 3–31, default 3): tamanho da janela.

    Saídas:
        - ``result`` "Filtro de mínimo" — ``main``, ``uint8``, mesmo shape.
        Sem histogramas e sem métricas.

    Dicas teóricas:
        Filtro de ordem (estatística de ordem): mínimo das janelas de
        ``kernel_size × kernel_size``. Com ``sliding_window_view``, use
        ``windows.min(axis=(-2, -1))``. Padding de borda obrigatório para manter
        o shape. Referência: Gonzalez & Woods, cap. 5.
    """
    raise NotImplementedError


def max_filter(image: np.ndarray, params: dict) -> ProcessResult:
    """Filtro de máximo (dilatação).

    Troca cada pixel pelo máximo da vizinhança; remove ruído do tipo pimenta.

    Entrada:
        Cinza ``(H, W)`` e RGB ``(H, W, 3)``, ``uint8``. Em RGB, por canal.

    Parâmetros:
        - ``kernel_size`` (int **ímpar**, 3–31, default 3): tamanho da janela.

    Saídas:
        - ``result`` "Filtro de máximo" — ``main``, ``uint8``, mesmo shape.
        Sem histogramas e sem métricas.

    Dicas teóricas:
        Análogo ao filtro de mínimo, com ``windows.max(axis=(-2, -1))``. Padding
        de borda para manter o shape. Referência: Gonzalez & Woods, cap. 5.
    """
    raise NotImplementedError


def unsharp_mask(image: np.ndarray, params: dict) -> ProcessResult:
    """Máscara de aguçamento.

    Aplica ``g = f + k · (f − f_borrada)``: ``k = 1`` é a máscara de nitidez
    clássica; ``k > 1`` é o high-boost.

    Entrada:
        Cinza ``(H, W)`` e RGB ``(H, W, 3)``, ``uint8``. Em RGB, por canal.

    Parâmetros:
        - ``kernel_size`` (int **ímpar**, 3–31, default 5): janela da suavização.
        - ``gain`` (float, 0–10, default 1.0): ganho ``k``.

    Saídas:
        - ``result`` "Imagem aguçada" — ``main``, ``uint8``, mesmo shape.
        Sem histogramas e sem métricas.

    Dicas teóricas:
        ``f_borrada`` é uma média gaussiana com o mesmo ``kernel_size`` (defina o
        σ, por exemplo ``kernel_size / 6``). Calcule em ``float``, some a máscara
        e sature com ``np.clip``. ``k = 0`` devolve a entrada. Referência:
        Gonzalez & Woods, cap. 3.
    """
    raise NotImplementedError


def laplacian_sharpen(image: np.ndarray, params: dict) -> ProcessResult:
    """Realce por Laplaciano.

    Aplica ``g = f − c · ∇²f`` e devolve também o Laplaciano ajustado como imagem
    acessória.

    Entrada:
        Cinza ``(H, W)`` e RGB ``(H, W, 3)``, ``uint8``. Em RGB, por canal (ou
        sobre a luminância — decisão do grupo).

    Parâmetros:
        - ``kernel_size`` (int **ímpar**, 3–15, default 3): tamanho da janela da
          aproximação do Laplaciano (o 3×3 é o clássico).

    Saídas:
        - ``result`` "Imagem realçada" — ``main``, ``uint8``, mesmo shape.
        - ``laplacian`` "Laplaciano ajustado" — **``aux``**, imagem ``uint8`` com
          o Laplaciano normalizado para exibição (não é histograma).
        Sem histogramas e sem métricas.

    Dicas teóricas:
        Kernel 3×3 ``[[0, 1, 0], [1, -4, 1], [0, 1, 0]]`` (ou
        ``[[1, 1, 1], [1, -8, 1], [1, 1, 1]]``); ``c = 1`` no caso clássico.
        Padding para manter o tamanho. O Laplaciano tem valores negativos: para
        exibir em ``uint8``, normalize (``(lap - min) / (max - min) * 255``) ou
        use ``|lap|`` — documente a escolha. Referência: Gonzalez & Woods, cap. 3.
    """
    raise NotImplementedError


def sobel(image: np.ndarray, params: dict) -> ProcessResult:
    """Gradiente de Sobel.

    Calcula a magnitude do gradiente (``|Gx| + |Gy|`` ou ``√(Gx² + Gy²)``), que
    realça as bordas.

    Entrada:
        Cinza ``(H, W)`` e RGB ``(H, W, 3)``, ``uint8``. Em RGB, por canal ou
        sobre o cinza — decisão do grupo.

    Parâmetros:
        - ``kernel_size`` (int **ímpar**, 3–7, default 3): tamanho dos kernels de
          derivada (3×3 é o clássico; para 5 e 7 defina/derive os kernels).

    Saídas:
        - ``magnitude`` "Magnitude do gradiente" — ``main``, ``uint8``, mesmo
          shape.
        Sem histogramas e sem métricas.

    Dicas teóricas:
        ``Gx = [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]`` e ``Gy`` transposto; calcule
        em ``float``, padding de borda, magnitude e **normalize para exibição**
        (o máximo teórico de ``|Gx| + |Gy|`` é ~4·255; normalizar pelo máximo
        observado ou por fator fixo — documente). Referência: Gonzalez & Woods,
        cap. 3.
    """
    raise NotImplementedError


def adaptive_median(image: np.ndarray, params: dict) -> ProcessResult:
    """Filtro adaptativo de mediana.

    Usa a mediana com janela que cresce de 3×3 até o tamanho máximo, preservando
    detalhes melhor que a mediana fixa.

    Entrada:
        Cinza ``(H, W)`` e RGB ``(H, W, 3)``, ``uint8``. Em RGB, por canal.

    Parâmetros:
        - ``max_window`` (int **ímpar**, 3–21, default 7): tamanho máximo da
          janela (o mínimo é sempre 3).

    Saídas:
        - ``result`` "Mediana adaptativa" — ``main``, ``uint8``, mesmo shape.
        Sem histogramas e sem métricas.

    Dicas teóricas:
        Algoritmo clássico (Gonzalez & Woods, cap. 5.3.2): para cada pixel, na
        janela atual calcule ``z_min``, ``z_max`` e ``z_med``. Se
        ``z_min < z_med < z_max``, teste o pixel: se ``z_min < z < z_max``,
        mantenha ``z``; senão use ``z_med``. Se a mediana for um impulso (igual a
        ``z_min`` ou ``z_max``), aumente a janela e repita; no limite
        ``max_window``, use ``z_med``. Padding de borda. Custo alto: priorize a
        clareza do código. Referência: Gonzalez & Woods, cap. 5.
    """
    raise NotImplementedError
