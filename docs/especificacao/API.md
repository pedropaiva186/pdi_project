# Contrato da API

Base: `/api`. Respostas em JSON (UTF-8). Em desenvolvimento, o Vite redireciona `/api` para `http://127.0.0.1:8000`, então **não há CORS** em produção. Mesmo assim, o backend libera `http://localhost:5173` para quem chamar a API direto.

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/health` | Verificação de saúde |
| `GET` | `/api/processes` | Catálogo de processos e categorias |
| `POST` | `/api/images/inspect` | Lê um PNG e informa o modo (cinza/RGB) e as dimensões |
| `POST` | `/api/process/{process_id}` | Executa um processo sobre o PNG enviado |

---

### `GET /api/health`
```json
{ "status": "ok" }
```

### `GET /api/processes`
Devolve o conteúdo de `shared/processes.json` (formato em [PROCESSOS.md](PROCESSOS.md#formato-do-catálogo)), acrescido de `implemented` em cada processo:
```json
{
  "version": 1,
  "categories": [{ "id": "intensity", "label": "Intensidade" }],
  "processes": [
    {
      "id": "threshold",
      "label": "Limiarização",
      "category": "intensity",
      "modes": ["gray", "rgb"],
      "implemented": false,
      "params": [{ "id": "k", "label": "Limiar k", "type": "int", "min": 0, "max": 255, "step": 1, "default": 128 }]
    }
  ]
}
```
> `implemented` é `false` enquanto o handler lançar `NotImplementedError`. O backend descobre isso testando o handler na inicialização. O frontend pode mostrar um selo "não implementado", mas **não deve desabilitar** o processo por causa disso.

### `POST /api/images/inspect`
`multipart/form-data`: campo `file` (PNG).

**200**
```json
{ "mode": "rgb", "width": 512, "height": 384, "source_mode": "RGBA", "filename": "lena.png" }
```
- `mode`: `"gray"` | `"rgb"`. É o que define quais processos ficam habilitados.
- `source_mode`: modo original do Pillow (informativo).

Normalização do modo:

| Modo do PNG (Pillow) | `mode` | Tratamento |
|---|---|---|
| `L` | `gray` | — |
| `LA` | `gray` | descarta o canal alfa |
| `RGB` | `rgb` | — |
| `RGBA` | `rgb` | descarta o canal alfa |
| `P` (paleta) | `rgb` ou `gray` | converte para RGB; se a paleta for só de cinza, trata como `L` |
| `1` (binária) | `gray` | converte para `L` (0/255) |
| `I;16`, `I`, `F` e outros | — | **400** `unsupported_image` |

### `POST /api/process/{process_id}`
`multipart/form-data`:

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `file` | PNG | sim | Imagem de entrada |
| `params` | string JSON | não | Ex.: `{"k": 100}`. Parâmetros que faltarem recebem o `default` do catálogo |

O backend: (1) decodifica e normaliza a imagem, (2) confere se o `mode` está em `process.modes`, (3) valida e converte os parâmetros, (4) chama o handler, (5) valida e codifica a saída.

**200**
```json
{
  "process_id": "histogram_equalization",
  "params": { },
  "input": { "mode": "gray", "width": 512, "height": 512 },
  "outputs": [
    { "id": "equalized", "label": "Imagem equalizada", "role": "main",
      "mode": "gray", "width": 512, "height": 512,
      "image": "data:image/png;base64,iVBORw0KG..." }
  ],
  "histograms": [
    { "id": "before", "label": "Histograma original", "channel": "gray", "values": [0, 3, 12, "... 256 valores"] },
    { "id": "after",  "label": "Histograma equalizado", "channel": "gray", "values": ["... 256 valores"] }
  ],
  "metrics": [
    { "label": "Tempo de processamento", "value": 12.4, "unit": "ms" }
  ],
  "elapsed_ms": 12.4
}
```
- `params`: os parâmetros **efetivamente usados**, já com os defaults preenchidos.
- `outputs[].role`:
  - `"main"`: aparece no painel **Imagem de saída**. Se houver mais de uma (ex.: R, G, B), o painel mostra abas.
  - `"aux"`: aparece no painel **Dados/Imagens acessórias** (ex.: Laplaciano ajustado, espectro, máscara do filtro).
- `histograms[].channel`: `"gray"` | `"r"` | `"g"` | `"b"`; `values` tem sempre 256 inteiros.
- `metrics`: lista ordenada; `value` é número ou string; `unit` é opcional. O backend sempre acrescenta "Tempo de processamento".
- Toda saída pode ser salva e usada como nova entrada.

---

## Erros

Formato único para qualquer erro (inclusive validação):
```json
{ "error": { "code": "invalid_params", "message": "Mensagem legível em português", "details": { } } }
```

| HTTP | `code` | Quando |
|---|---|---|
| 400 | `invalid_image` | Arquivo ausente, corrompido ou que não é PNG |
| 400 | `unsupported_image` | PNG com profundidade ou modo não suportado |
| 413 | `image_too_large` | Arquivo > 20 MB ou lado > 4096 px |
| 404 | `process_not_found` | `process_id` fora do catálogo |
| 422 | `invalid_params` | JSON inválido, tipo errado, fora do intervalo, `odd` violado, opção inexistente, restrição violada. `details.param` indica o parâmetro |
| 422 | `unsupported_mode` | Processo não aceita o modo da imagem (ex.: equalização em RGB) |
| 501 | `not_implemented` | O handler ainda lança `NotImplementedError` |
| 500 | `invalid_output` | O handler devolveu um array fora do contrato (dtype ≠ uint8, shape inválido). A mensagem diz o que corrigir |
| 500 | `processing_error` | Exceção inesperada no handler. `message` traz o tipo e o texto da exceção (é um projeto acadêmico, então isso ajuda a depurar) |

## Nomes de arquivo ao salvar (frontend)
`{nome_original_sem_ext}_{process_id}_{output_id}.png`, por exemplo `lena_gaussian_blur_result.png`.
