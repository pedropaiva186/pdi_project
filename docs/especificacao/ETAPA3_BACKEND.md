# Etapa 3 — Especificação de implementação do Backend (esqueleto)

> Documento de tarefa para o agente responsável pelo backend. Complementa (não substitui) [BACKEND.md](BACKEND.md), [API.md](API.md) e [PROCESSOS.md](PROCESSOS.md). **API.md é o contrato**: qualquer divergência com ele é um bug. Em detalhes de implementação, **este documento prevalece** sobre BACKEND.md.

## 0. Regras do trabalho

- **Escopo de escrita:** `backend/`, `run.py` (raiz), `README.md` (raiz) e `.gitignore` (raiz, só para **acrescentar** entradas). **Não** altere `shared/`, `docs/`, `frontend/` nem `pyproject.toml`. Se achar um problema no catálogo ou na especificação, **pare e reporte** ao líder.
- **Não faça commits.**
- **Regra de ouro:** nenhum código de PDI. Os handlers em `backend/app/processing/` são **stubs** (assinatura + docstring + `raise NotImplementedError`). Também é proibido, **na infraestrutura**, calcular histograma, converter cores (fora as conversões de modo do Pillow descritas em §4), convoluir, aplicar FFT ou gerar ruído.
- **Bibliotecas:** `fastapi`, `uvicorn[standard]`, `pydantic` v2, `numpy`, `pillow`, `python-multipart`; testes: `pytest`, `httpx`. **Proibido:** OpenCV, scikit-image, SciPy.
- **Python:** código compatível com 3.11+. Na máquina local há `python3.14` (`/opt/homebrew/bin/python3.14`) e `python3` = 3.15. Crie o venv com **python3.14** em `backend/.venv` (wheels mais maduros); se der problema, use o 3.15 e reporte.
- **Idioma:** mensagens de erro para o usuário em português do Brasil; código e logs em inglês.
- Tipagem: anotações de tipo em todas as funções públicas. Estilo PEP 8; linhas com até 100 colunas.

## 1. Estrutura final

```
run.py                              # raiz: build do front (se preciso) + Uvicorn
README.md                           # raiz: instruções para o avaliador (ver §11)
backend/
├── requirements.txt
├── requirements-dev.txt            # -r requirements.txt + pytest + httpx
├── pytest.ini                      # testpaths = tests ; pythonpath = .
├── run.py                          # dev: uvicorn com --reload
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── logging_config.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py                 # acesso a catalog/implemented em app.state
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── health.py
│   │       ├── processes.py
│   │       ├── images.py
│   │       └── process.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── responses.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── catalog.py
│   │   ├── validation.py
│   │   └── errors.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── image_io.py
│   │   ├── uploads.py              # leitura do UploadFile com limite de tamanho
│   │   ├── implemented.py          # detecção de handlers implementados
│   │   └── runner.py
│   └── processing/                 # ◄── ÁREA DO GRUPO (só stubs)
│       ├── __init__.py
│       ├── types.py
│       ├── registry.py
│       ├── color.py
│       ├── intensity.py
│       ├── spatial.py
│       ├── frequency.py
│       └── noise.py
└── tests/
    ├── __init__.py
    ├── conftest.py                 # fixtures: client, fábrica de PNGs em memória, fake handlers
    ├── test_catalog.py
    ├── test_validation.py
    ├── test_image_io.py
    ├── test_runner.py
    └── test_api.py
```

**Não** crie `processing/utils.py` (é do grupo, se quiser).

### `requirements.txt`

```
fastapi>=0.115
uvicorn[standard]>=0.30
pydantic>=2.7
numpy>=2.0
pillow>=10.4
python-multipart>=0.0.9
```

`requirements-dev.txt`: `-r requirements.txt`, `pytest>=8`, `httpx>=0.27`.

`.gitignore` da raiz: o arquivo atual tem `docs/`, `.*` e `!.gitignore`; **mantenha essas linhas** e acrescente `__pycache__/`, `*.pyc`, `node_modules/`, `frontend/dist/`.

## 2. `app/config.py`

```python
from pathlib import Path
import os

ROOT_DIR = Path(__file__).resolve().parents[2]          # pdi_project/
CATALOG_PATH = Path(os.getenv("PDI_CATALOG_PATH", ROOT_DIR / "shared" / "processes.json"))
FRONTEND_DIST = Path(os.getenv("PDI_FRONTEND_DIST", ROOT_DIR / "frontend" / "dist"))
MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_IMAGE_SIDE = 4096
CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
DETECTION_IMAGE_SIZE = 8
```

## 3. `core/errors.py`

```python
class AppError(Exception):
    def __init__(self, code: str, message: str, status: int, details: dict | None = None): ...
```

Fábricas (funções ou `classmethod`), uma por código de API.md: `invalid_image(msg)`, `unsupported_image(msg)`, `image_too_large(msg, details)`, `process_not_found(pid)`, `invalid_params(msg, param=None, **details)`, `unsupported_mode(process_label, mode, allowed)`, `not_implemented(process_label)`, `invalid_output(msg)`, `processing_error(exc)`.

`register_exception_handlers(app)` registra:

| Exceção | Resposta |
|---|---|
| `AppError` | `status` + `{"error": {"code", "message", "details"}}` |
| `RequestValidationError` (FastAPI) | `422 invalid_params`, mensagem "Requisição inválida.", `details.errors` = lista simplificada (`loc`, `msg`) |
| `StarletteHTTPException` | mesmo status; `404` → `code="not_found"`, "Recurso não encontrado."; `405` → `code="method_not_allowed"`; outros → `code="http_error"` |
| `Exception` (qualquer outra) | `500 internal_error`, "Erro interno do servidor." (com o traceback no log) |

Sempre `details` presente (objeto vazio se não houver).

Mensagens padrão (use estes textos):

| Código | Mensagem |
|---|---|
| `invalid_image` (ausente) | "Nenhum arquivo foi enviado." |
| `invalid_image` (não PNG/corrompido) | "O arquivo enviado não é um PNG válido." |
| `unsupported_image` | "Formato de PNG não suportado ({source_mode}). Use imagens em escala de cinza de 8 bits ou RGB de 24 bits." |
| `image_too_large` (bytes) | "O arquivo excede o limite de 20 MB." |
| `image_too_large` (lado) | "A imagem excede o limite de 4096 pixels por lado ({w}×{h})." |
| `process_not_found` | "Processo '{id}' não encontrado." |
| `unsupported_mode` | "O processo '{label}' não está disponível para imagens {em escala de cinza / coloridas (RGB)}." |
| `not_implemented` | "O processo '{label}' ainda não foi implementado." |
| `processing_error` | "Erro ao executar o processo: {TipoDaExceção}: {mensagem}" |
| `invalid_output` | ver §7 |

## 4. `core/catalog.py`

```python
@dataclass(frozen=True)
class ParamSpec: id, label, type, default, min=None, max=None, step=None, odd=False,
                 options: tuple[str, ...] = (), visible_if: dict | None = None, help=None
@dataclass(frozen=True)
class ProcessSpec: id, label, category, description, modes: tuple[str, ...],
                   params: tuple[ParamSpec, ...], constraints: tuple[dict, ...], raw: dict
class Catalog:
    raw: dict
    categories: list[dict]
    processes: dict[str, ProcessSpec]     # mantém a ordem do JSON
    def get(self, process_id: str) -> ProcessSpec   # AppError process_not_found
    def to_public(self, implemented: dict[str, bool]) -> dict
def load_catalog(path: Path) -> Catalog
class CatalogError(Exception)
```

`load_catalog` faz uma **validação estrita** e falha na inicialização (`CatalogError` com uma mensagem clara) se:
- o JSON for inválido, ou faltarem `version`, `categories` ou `processes`;
- houver ids de categoria ou processo duplicados, ou um processo referenciar uma categoria inexistente;
- `modes` estiver vazio ou contiver algo diferente de `gray`/`rgb`;
- houver param com `type` desconhecido, id duplicado no processo, `int`/`float` sem `min`/`max`, `min > max`, `default` fora da faixa ou do tipo, `odd` com default par (ou `min`/`max` pares), `select` sem `options` ou com default fora delas, ou `bool` com default não booleano;
- `visible_if` referenciar um param inexistente, ou `equals` não for uma opção válida desse param;
- uma constraint tiver regra diferente de `less_equal` ou referenciar params inexistentes.

`to_public` devolve o **JSON original** (preservando todos os campos e a ordem) com `"implemented": bool` acrescentado a cada processo. Não altere o `raw`: faça uma cópia profunda.

## 5. `core/validation.py`

```python
def parse_params(process: ProcessSpec, raw: str | None) -> dict[str, int | float | bool | str]
```

Algoritmo:

1. `raw` `None` ou só espaços → `{}`. `json.loads` falhou → `invalid_params("Os parâmetros não estão em JSON válido.")`. Resultado diferente de `dict` → `invalid_params("Os parâmetros devem ser um objeto JSON.")`.
2. Chave que não existe em `process.params` → `invalid_params("Parâmetro desconhecido: '{k}'.", param=k)`.
3. Para cada param, **na ordem do catálogo**, converte e valida o valor recebido (ou usa o default se estiver ausente ou for `null`):
   - `int`: aceita `int` (não `bool`) ou `float` com valor inteiro (`5.0` → `5`); qualquer outro → "'{label}' deve ser um número inteiro.". Fora de `[min, max]` → "'{label}' deve estar entre {min} e {max}.". `odd` e par → "'{label}' deve ser um número ímpar.".
   - `float`: aceita `int`/`float` (não `bool`), finito (`math.isfinite`) → `float(v)`; senão "'{label}' deve ser um número.". Faixa como no `int`.
   - `bool`: só `True`/`False` → senão "'{label}' deve ser verdadeiro ou falso.".
   - `select`: `str` em `options` → senão "'{label}' deve ser uma das opções: {opções}.".
   - Em todos os erros: `details = {"param": id, "value": valor_recebido}` (+ `min`/`max`/`options` quando fizer sentido).
4. **Visibilidade:** depois de resolver todos, remove do resultado os params cujo `visible_if` for falso (avaliado sobre os valores **resolvidos**). Param invisível enviado pelo cliente é **ignorado** (não é erro).
5. **Constraints:** `less_equal [a, b]`, avaliada só se `a` e `b` estiverem no resultado; violada → `invalid_params(constraint["message"], param=b, params=[a, b])`.
6. Retorna o dict final (ordem do catálogo). É ele que vai para o handler e para o campo `params` da resposta.

## 6. `services/image_io.py` e `services/uploads.py`

```python
@dataclass
class DecodedImage:
    array: np.ndarray        # uint8, C-contíguo; (H, W) gray ou (H, W, 3) rgb
    mode: Literal["gray", "rgb"]
    source_mode: str         # modo original do Pillow
    width: int
    height: int

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
def decode_png(data: bytes) -> DecodedImage
def encode_png_data_url(array: np.ndarray) -> str
def mode_of(array: np.ndarray) -> Literal["gray", "rgb"]
```

`uploads.read_upload(file: UploadFile | None) -> bytes`: `None` ou nome vazio → `invalid_image` (ausente); lê `file.file.read(MAX_UPLOAD_BYTES + 1)`; se passar do limite → `413 image_too_large`; bytes vazios → `invalid_image`.

`decode_png`:
1. Não começa com `PNG_SIGNATURE` → `invalid_image`.
2. `Image.open(BytesIO(data))`; confere `img.format == "PNG"`; verifica `img.size` **antes** de `load()`: lado > `MAX_IMAGE_SIDE` → `413` com `details={"width", "height", "max_side"}`.
3. `img.load()` dentro de `try` (qualquer exceção do Pillow → `invalid_image`). Desative o aviso de *decompression bomb* do Pillow só dentro desse contexto, se necessário (o limite de lado já protege).
4. Normalização por `img.mode`:

| `img.mode` | Ação | `mode` |
|---|---|---|
| `L` | — | gray |
| `LA` | `img.getchannel("L")` | gray |
| `1` | `img.convert("L")` | gray |
| `RGB` | — | rgb |
| `RGBA` | `img.convert("RGB")` (descarta o alfa, sem composição) | rgb |
| `P`, `PA` | `img.convert("RGBA").convert("RGB")`; se os 3 canais forem idênticos em todo pixel → usa só um canal (gray) | rgb ou gray |
| outros (`I;16*`, `I`, `F`, `CMYK`, `YCbCr`, `LAB`, `HSV`…) | `unsupported_image` | — |

   > Observação: a comparação "canais idênticos" no caso `P` é uma conversão de **modo de arquivo**, não PDI; está permitida.
5. `array = np.ascontiguousarray(np.asarray(img, dtype=np.uint8))`; retorna `DecodedImage`.

`encode_png_data_url(array)`: `Image.fromarray(array, mode="L" | "RGB")` → `save(buf, format="PNG", compress_level=1)` (prioriza a velocidade) → `"data:image/png;base64," + b64`.

## 7. `processing/` — contrato, registro e stubs

### 7.1 `types.py`

Exatamente como BACKEND.md §2 (`OutputImage`, `Histogram`, `Metric`, `ProcessResult`). Acrescente, no topo do módulo, uma docstring explicando o contrato para o grupo, em português.

### 7.2 `registry.py`

```python
Handler = Callable[[np.ndarray, dict], ProcessResult]
PROCESS_HANDLERS: dict[str, Handler] = {  # os 19 ids do catálogo, na ordem do catálogo
    "rgb_split": color.rgb_split, ...
}
```

### 7.3 Stubs — saídas fixadas (contrato que a docstring deve declarar)

| Módulo | Função | Saídas (`id` — `label` — role) | Extras |
|---|---|---|---|
| color | `rgb_split` | `r` "Canal R", `g` "Canal G", `b` "Canal B" — main (gray) | — |
| color | `hsv_split` | `h` "Canal H", `s` "Canal S", `v` "Canal V" — main (gray) | H escalado para 0–255 (docstring explica) |
| intensity | `threshold` | `result` "Imagem limiarizada" — main | — |
| intensity | `log_transform` | `result` "Transformação logarítmica" — main | — |
| intensity | `power_transform` | `result` "Transformação de potência" — main | — |
| intensity | `histogram_equalization` | `equalized` "Imagem equalizada" — main | histogramas `before` "Histograma original", `after` "Histograma equalizado" (channel `gray`) |
| intensity | `intensity_slicing` | `result` "Imagem fatiada" — main | valor de destaque 255 fixo |
| spatial | `gaussian_blur` | `result` "Imagem suavizada" — main | — |
| spatial | `median_filter` | `result` "Filtro de mediana" — main | — |
| spatial | `min_filter` | `result` "Filtro de mínimo" — main | — |
| spatial | `max_filter` | `result` "Filtro de máximo" — main | — |
| spatial | `unsharp_mask` | `result` "Imagem aguçada" — main | — |
| spatial | `laplacian_sharpen` | `result` "Imagem realçada" — main; `laplacian` "Laplaciano ajustado" — aux | — |
| spatial | `sobel` | `magnitude` "Magnitude do gradiente" — main | — |
| spatial | `adaptive_median` | `result` "Mediana adaptativa" — main | — |
| frequency | `gaussian_frequency_filter` | `result` "Imagem filtrada" — main | — |
| frequency | `butterworth_filter` | `result` "Imagem filtrada" — main | — |
| noise | `gaussian_noise` | `result` "Imagem com ruído gaussiano" — main | — |
| noise | `salt_pepper_noise` | `result` "Imagem com ruído" — main | constante de módulo `SINGLE_NOISE_PROBABILITY = 0.05` (densidade quando o tipo é só sal ou só pimenta) |

Cada docstring (em português) deve conter, nesta ordem:
1. nome do processo e uma frase sobre o que ele faz;
2. **Entrada:** formatos aceitos (consulte `modes` no catálogo) — cinza `(H, W)` e/ou RGB `(H, W, 3)`, `uint8`; para RGB, lembrete de que a forma de aplicar (por canal, em V do HSV, etc.) é decisão do grupo;
3. **Parâmetros:** cada chave de `params` com tipo, faixa e significado (copiar do catálogo; mencionar `visible_if` quando houver: ex. no `salt_pepper_noise`, `salt_probability`/`pepper_probability` só chegam quando `noise_type == "salt_and_pepper"`);
4. **Saídas:** exatamente as da tabela acima (ids, labels, roles, histogramas);
5. **Dicas teóricas:** fórmula e pontos de atenção (ex.: tratamento de bordas/padding, normalização para exibição do Laplaciano e do Sobel, centralização do espectro com `(-1)^(x+y)` ou `fftshift`, `D(u, v)` medido a partir do centro, divisão por zero no Butterworth passa-alta em `D = 0`, saturação vs. normalização para voltar a `uint8`, referência ao capítulo correspondente de Gonzalez & Woods);
6. `raise NotImplementedError`.

Os imports nos módulos de processing se limitam a `numpy as np` e `from .types import ...`.

## 8. `services/implemented.py`

```python
def detect_implemented(catalog: Catalog, handlers: dict[str, Handler]) -> dict[str, bool]
```

Para cada processo: imagem de zeros `uint8` 8×8 (`(8, 8)` se o primeiro modo for `gray`, `(8, 8, 3)` se for `rgb`), `params = parse_params(process, None)`; chama o handler; `NotImplementedError` → `False`; qualquer outro retorno ou exceção → `True` (exceção → `logger.warning`). Executado no `lifespan` do app; o resultado fica em `app.state.implemented`.

Na inicialização, verifique também que `set(catalog.processes) == set(PROCESS_HANDLERS)`; se não bater, levante um erro claro, listando os ids que sobram e os que faltam.

## 9. `services/runner.py`

```python
def run_process(catalog: Catalog, handlers: dict[str, Handler],
                process_id: str, file_bytes: bytes, params_raw: str | None) -> dict
```

Fluxo (ordem obrigatória, igual a BACKEND.md §4):
1. `process = catalog.get(process_id)` → 404.
2. `img = decode_png(file_bytes)` → 400/413.
3. `img.mode not in process.modes` → 422 `unsupported_mode` (`details={"mode", "allowed_modes"}`).
4. `params = parse_params(process, params_raw)` → 422.
5. `t0 = perf_counter()`; `result = handler(img.array.copy(), dict(params))`; `elapsed_ms = round((perf_counter() - t0) * 1000, 2)`.
   - `NotImplementedError` → 501; outra exceção → `logger.exception` + 500 `processing_error`.
6. **Validação da saída** (cada falha → 500 `invalid_output`, com uma mensagem específica em português que diga o que corrigir):
   - `result` não é `ProcessResult` → "O handler deve retornar um ProcessResult.";
   - `outputs` vazio ou sem nenhum `role == "main"`;
   - `id` de saída duplicado; `role` fora de `main`/`aux`;
   - `data` não é `np.ndarray`; `dtype != uint8` → "A saída '{id}' tem dtype {dtype}; converta para uint8 (np.clip + astype ou normalização)."; `ndim` não for 2 nem 3 com `shape[2] == 3` → "A saída '{id}' tem shape {shape}; esperado (H, W) ou (H, W, 3).";
   - histograma: `len(values) != 256`, valor não inteiro ou negativo, ou `channel` inválido;
   - métrica com `value` que não seja `int`/`float`/`str` (aceite tipos escalares do NumPy e converta com `.item()`).
7. Montagem (formato de API.md):
   - `outputs`: `{id, label, role, mode: mode_of(data), width, height, image: encode_png_data_url(data)}` (as saídas `main` primeiro, depois as `aux`, mantendo a ordem relativa);
   - `histograms`: `values` convertidos para `int` nativo;
   - `metrics`: as do handler + `{"label": "Tempo de processamento", "value": elapsed_ms, "unit": "ms"}` no **final**;
   - `elapsed_ms`: tempo só do handler (sem codificação);
   - `input`: `{mode, width, height}`; `params`: o dict validado.
8. Log em nível INFO, uma linha: `process id=%s mode=%s size=%dx%d elapsed_ms=%.2f status=%d` (também nos erros 4xx/5xx desse endpoint).

## 10. API — `main.py`, rotas e schemas

### 10.1 `main.py`

```python
def create_app(catalog_path: Path = CATALOG_PATH, frontend_dist: Path = FRONTEND_DIST,
               handlers: dict | None = None) -> FastAPI
app = create_app()
```

- `lifespan`: carrega o catálogo, confere a paridade catálogo ↔ handlers, detecta os implementados e guarda tudo em `app.state` (`catalog`, `handlers`, `implemented`). O parâmetro `handlers` permite que os testes injetem handlers falsos.
- `FastAPI(title="Processador de Imagens — PDI", version="0.1.0")`.
- `CORSMiddleware(allow_origins=CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"])`.
- `register_exception_handlers(app)`.
- Routers com `prefix="/api"`.
- **Frontend:** se `frontend_dist / "index.html"` existir → `app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")`, **depois** dos routers. Se não existir → `GET /` devolve um HTML simples: "Frontend não compilado. Rode `npm run build` em `frontend/` ou use `python run.py`.".
- Garanta que `/api/rota-inexistente` devolve **JSON 404** (`not_found`), e não o `index.html`. Se o mount em `/` interceptar, crie um catch-all `@router.api_route("/api/{path:path}")` que levanta 404 antes do mount.

### 10.2 Rotas (todas `def`, síncronas)

| Rota | Implementação |
|---|---|
| `GET /api/health` | `{"status": "ok"}` |
| `GET /api/processes` | `catalog.to_public(app.state.implemented)` |
| `POST /api/images/inspect` | `file: UploadFile | None = File(None)` → `read_upload` → `decode_png` → `{mode, width, height, source_mode, filename: file.filename}` |
| `POST /api/process/{process_id}` | `file: UploadFile | None = File(None)`, `params: str | None = Form(None)` → `run_process(...)` |

> O arquivo ausente deve virar `400 invalid_image` (não o `422` do FastAPI); por isso `File(None)` com checagem manual.

### 10.3 `schemas/responses.py`

Modelos Pydantic para documentar o OpenAPI: `HealthResponse`, `InspectResponse`, `OutputImageOut`, `HistogramOut`, `MetricOut`, `ProcessResponse`, `ErrorBody`, `ErrorResponse`. Use-os em `response_model` e `responses={400: {"model": ErrorResponse}, ...}`. O catálogo (`/api/processes`) pode ser `dict` livre.

## 11. `run.py` (raiz) e `backend/run.py`

**`backend/run.py`** (dev): `uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)`, com `app_dir` sendo a pasta do próprio arquivo.

**`run.py` (raiz)**, para a apresentação. Usa só a biblioteca padrão + uvicorn:

```
python run.py [--host 127.0.0.1] [--port 8000] [--dev] [--rebuild] [--no-build] [--no-browser]
```

1. Confere a versão do Python (≥ 3.11) e se `fastapi`, `uvicorn`, `numpy`, `PIL` e `multipart` são importáveis; se faltar algo, mostra a mensagem `pip install -r backend/requirements.txt` e sai com código 1.
2. Frontend: se `--no-build`, pula. Senão, se `frontend/dist/index.html` não existir (ou com `--rebuild`): se `frontend/package.json` não existir → aviso "frontend/ não encontrado; subindo só a API". Se `shutil.which("npm")` → `npm install` (se faltar `node_modules`) e `npm run build`, com `cwd=frontend` e saída no terminal; se falhar, mostra um aviso e continua só com a API. Sem `npm` → aviso equivalente.
3. Mostra `Servidor em http://{host}:{port}`; abre o navegador (`webbrowser.open`, numa thread com ~1,5 s de atraso) a menos que `--no-browser`.
4. `uvicorn.run("app.main:app", app_dir=str(ROOT / "backend"), host, port, reload=--dev)`.

## 12. Testes (`pytest`)

Gere as imagens **em memória** com Pillow (fixture `make_png(mode, size=(16, 12), color=...) -> bytes`); não grave arquivos binários no repositório.

`conftest.py`: fixture `client` (`TestClient(create_app())` dentro de `with`, para rodar o lifespan); fixture `fake_client(handlers_override)` que cria o app com handlers falsos (ex.: um `threshold` falso que devolve `ProcessResult` válido, um que devolve `float64`, um que levanta `ValueError`).

Cobertura mínima:

- **test_catalog:** o `shared/processes.json` real carrega; paridade de ids com `PROCESS_HANDLERS`; `to_public` preserva campos e ordem e acrescenta `implemented`; cada regra de validação do §4 rejeita um catálogo inválido (use `tmp_path`).
- **test_validation:** defaults; `int` aceita `5.0` e rejeita `5.5`, `"5"` e `true`; faixa; `odd`; `float` rejeita `NaN`/`bool`; `select` inválido; chave desconhecida; JSON malformado e não-objeto; `visible_if` (param invisível enviado é ignorado e não aparece no resultado; visível sem valor recebe o default); constraint `a > b` → erro com `details.param == "b"`.
- **test_image_io:** `L`, `LA`, `RGB`, `RGBA`, `P` colorido → rgb, `P` com paleta cinza → gray, `1` → gray com valores {0, 255}, `I;16` → `unsupported_image`; bytes que não são PNG (ex.: um JPEG gerado pelo Pillow) → `invalid_image`; PNG truncado → `invalid_image`; lado > 4096 → 413 (pode usar `monkeypatch` em `MAX_IMAGE_SIDE` para não gerar uma imagem enorme); `encode_png_data_url` faz *round-trip* exato com `decode_png`.
- **test_runner:** sucesso com handler falso (formato completo; "Tempo de processamento" por último; `main` antes de `aux`); `invalid_output` para `float64`, shape `(H, W, 4)`, sem `main`, ids duplicados, histograma com 255 valores; `processing_error` com `ValueError`; `not_implemented`; os params validados chegam ao handler.
- **test_api:** `/api/health`; `/api/processes` com os 19 processos, todos `implemented: false` com os stubs reais; `inspect` OK, sem arquivo (400) e não PNG (400); `process` com id inexistente (404), equalização em RGB (422 `unsupported_mode`), params inválidos (422 com `details.param`), stub real (501 `not_implemented`), JSON de erro no formato único; `/api/xyz` → 404 JSON; `GET /` sem o dist → HTML de aviso, e com um dist falso em `tmp_path` → serve o `index.html`.

`pytest -q` deve passar **sem falhas nem avisos de depreciação** do próprio código.

## 13. `README.md` (raiz)

Em português, para o avaliador e para o grupo:
1. Título e uma frase sobre o projeto (disciplina, UFPB).
2. **Requisitos:** Python 3.11+ e Node.js 20+ (Node só é necessário para compilar a interface).
3. **Execução rápida:** criar o venv, `pip install -r backend/requirements.txt` e `python run.py`; abre em `http://127.0.0.1:8000`.
4. **Desenvolvimento:** os dois terminais (backend `python backend/run.py`; frontend `npm run dev`), e o mock `VITE_USE_MOCK=true npm run dev`.
5. **Testes:** `pip install -r backend/requirements-dev.txt` e `cd backend && pytest`.
6. **Implementando os processos:** aponta para `backend/app/processing/`, o contrato (`ProcessResult`), a regra de saída `uint8`, a detecção automática de `implemented` e o significado do erro `501`.
7. Estrutura de pastas resumida e link para `docs/especificacao/` (atenção: `docs/` está no `.gitignore`; mencione que a especificação fica local).

## 14. Critérios de aceite (verificar antes de reportar)

1. `cd backend && python3.14 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt` funciona.
2. `.venv/bin/pytest -q` → tudo verde.
3. `python run.py --no-build --no-browser` sobe o servidor, e:
   - `curl -s localhost:8000/api/health` → `{"status":"ok"}`;
   - `curl -s localhost:8000/api/processes` → 19 processos, `implemented: false`;
   - `curl -s -F file=@<png> localhost:8000/api/images/inspect` → modo correto;
   - `curl -s -F file=@<png> -F 'params={"k":100}' localhost:8000/api/process/threshold` → `501 not_implemented` no formato único;
   - `curl -s -F file=@<png_rgb> localhost:8000/api/process/histogram_equalization` → `422 unsupported_mode`;
   - `curl -s localhost:8000/docs` → OpenAPI disponível.
4. Nenhum stub contém lógica de PDI (cada corpo é só docstring + `raise NotImplementedError`).
5. `grep -rE "cv2|skimage|scipy" backend/` não encontra nada.

## 15. Relatório final

Ao terminar, reporte ao líder: o que foi feito, os comandos usados, a saída resumida do `pytest`, o resultado de cada critério de aceite (✅/❌), desvios desta especificação (com o motivo) e pendências.
