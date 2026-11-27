# Especificação do Backend

**Stack:** Python 3.11+, FastAPI, Uvicorn, Pydantic v2, NumPy, Pillow (**só para I/O**), python-multipart, pytest + httpx (testes).
**Não usar OpenCV/scikit-image/SciPy na infraestrutura.** Nos handlers de PDI, a escolha das bibliotecas é do grupo (recomendado: só NumPy).

## 1. Estrutura

```
backend/
├── requirements.txt
├── run.py                      # uvicorn app.main:app --host 127.0.0.1 --port 8000 (--reload em dev)
├── app/
│   ├── main.py                 # cria o app, CORS, handlers de erro, routers, serve frontend/dist em "/"
│   ├── config.py               # caminhos (shared/processes.json, frontend/dist), limites de tamanho
│   ├── api/
│   │   └── routes/
│   │       ├── health.py       # GET  /api/health
│   │       ├── processes.py    # GET  /api/processes
│   │       ├── images.py       # POST /api/images/inspect
│   │       └── process.py      # POST /api/process/{process_id}
│   ├── schemas/
│   │   └── responses.py        # modelos Pydantic das respostas (API.md)
│   ├── core/
│   │   ├── catalog.py          # carrega e valida processes.json; consulta por id
│   │   ├── validation.py       # valida/converte params (tipo, faixa, odd, options, visible_if, constraints)
│   │   └── errors.py           # AppError(code, message, status, details) + handlers → formato único
│   ├── services/
│   │   ├── image_io.py         # bytes PNG → ndarray uint8 normalizado (+ mode); ndarray → data URL PNG
│   │   └── runner.py           # orquestra: valida o modo, chama o handler, mede o tempo, valida e serializa a saída
│   └── processing/             # ◄── ÁREA DO GRUPO
│       ├── __init__.py
│       ├── types.py            # ProcessResult, OutputImage, Histogram, Metric (dataclasses)
│       ├── registry.py         # PROCESS_HANDLERS: dict[str, Callable] (id do catálogo → função)
│       ├── color.py            # rgb_split, hsv_split
│       ├── intensity.py        # threshold, log_transform, power_transform, histogram_equalization, intensity_slicing
│       ├── spatial.py          # gaussian_blur, median_filter, min_filter, max_filter, unsharp_mask,
│       │                       # laplacian_sharpen, sobel, adaptive_median
│       ├── frequency.py        # gaussian_frequency_filter, butterworth_filter
│       └── noise.py            # gaussian_noise, salt_pepper_noise
└── tests/
    ├── test_catalog.py         # JSON válido; todo id do catálogo tem handler e vice-versa
    ├── test_validation.py      # tipos, faixas, odd, visible_if, constraints, defaults
    ├── test_image_io.py        # normalização de modos (L, LA, RGB, RGBA, P, 1, 16 bits → erro)
    └── test_api.py             # health, catálogo, inspect, 404/422/501, formato de erro
```

## 2. Contrato dos handlers (para o grupo)

```python
# processing/types.py
from dataclasses import dataclass, field
from typing import Literal
import numpy as np

@dataclass
class OutputImage:
    id: str                       # ex.: "result", "r", "laplacian"
    label: str                    # ex.: "Imagem filtrada"
    data: np.ndarray              # uint8, (H, W) ou (H, W, 3)
    role: Literal["main", "aux"] = "main"

@dataclass
class Histogram:
    id: str
    label: str
    values: list[int]             # 256 contagens
    channel: Literal["gray", "r", "g", "b"] = "gray"

@dataclass
class Metric:
    label: str
    value: float | int | str
    unit: str | None = None

@dataclass
class ProcessResult:
    outputs: list[OutputImage]
    histograms: list[Histogram] = field(default_factory=list)
    metrics: list[Metric] = field(default_factory=list)
```

Assinatura de **todo** handler:
```python
def nome_do_processo(image: np.ndarray, params: dict) -> ProcessResult: ...
```
- `image`: `uint8`, `(H, W)` se cinza ou `(H, W, 3)` se RGB. É uma **cópia**, pode ser alterada à vontade.
- `params`: **já validados e convertidos** (int, float, bool, str), com os defaults preenchidos. Ex.: `params["kernel_size"]` é sempre um `int` ímpar dentro da faixa.
- O handler é chamado **só** para os modos listados em `modes`.
- Retorno: pelo menos uma saída `main`. Cálculos podem usar `float`, mas **a saída tem que voltar a `uint8`** (o grupo decide entre saturar com clip ou normalizar). Se não voltar, o runner devolve `500 invalid_output` explicando o motivo.

## 3. Regra dos stubs (Etapa 3)

Os handlers em `processing/*.py` **não devem conter nenhuma lógica de PDI**. Cada um tem só:
1. a assinatura;
2. uma docstring com a descrição do processo, os parâmetros recebidos (tipo e faixa), as saídas esperadas (ids, roles, histogramas) e dicas de onde aparecem os conceitos teóricos;
3. `raise NotImplementedError`.

Exemplo:
```python
def threshold(image: np.ndarray, params: dict) -> ProcessResult:
    """Limiarização.

    Entrada: imagem em escala de cinza (H, W), uint8.
    Parâmetros:
        k (int, 0–255): limiar. Pixels > k → 255; caso contrário → 0.
    Saídas:
        main "result" — imagem binarizada (uint8).
    """
    raise NotImplementedError
```

**Fica de fora dos stubs** (é PDI e é responsabilidade do grupo): cálculo de histograma, conversão RGB→HSV/cinza, convolução, padding, FFT, geração de ruído, normalização para exibição. Se o grupo quiser funções auxiliares compartilhadas (ex.: `convolve`, `pad`, `histogram`), crie um `processing/utils.py`.

**Já vem implementado** (infraestrutura): decodificar e codificar PNG, normalizar o modo, validar parâmetros e modo, medir o tempo, serializar a resposta, tratar erros, descobrir `implemented` e servir o frontend.

## 4. Fluxo de `POST /api/process/{id}` (runner)

1. `catalog.get(id)` → `404 process_not_found`.
2. `image_io.decode(file)` → `(ndarray, mode)`, ou `400`/`413`.
3. `mode not in process.modes` → `422 unsupported_mode`.
4. `validation.parse(process, params_json)` → `dict` tipado, ou `422 invalid_params`.
5. `handler = registry.PROCESS_HANDLERS[id]`; chama com `image.copy()` e mede o tempo com `time.perf_counter`.
   - `NotImplementedError` → `501 not_implemented`;
   - qualquer outra exceção → `500 processing_error` (com o traceback no log).
6. Valida cada `OutputImage.data` (`uint8`, `ndim` 2, ou 3 com 3 canais) → `500 invalid_output`.
7. Codifica as saídas em PNG base64, acrescenta a métrica de tempo e monta a resposta (API.md).

**Detecção de `implemented`** (na inicialização): chama cada handler com uma imagem 8×8 de zeros no primeiro modo aceito e os parâmetros default. Se lançar `NotImplementedError`, marca `false`; qualquer outro resultado marca `true`. Processos são rápidos em 8×8, então isso não pesa.

## 5. Considerações

- Handlers síncronos: as rotas de processamento são `def` (não `async`), e o FastAPI as roda em uma threadpool.
- Logs: uma linha por requisição de processo (`id`, modo, dimensões, tempo, status).
- `run.py` na raiz do repositório: se `frontend/dist` não existir e houver `npm`, roda `npm install && npm run build`; depois sobe o Uvicorn. Se não houver `npm`, avisa e sobe só a API.
